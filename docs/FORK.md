# Fork: custom lightweight Gemma 4, no US maps

This is an unofficial fork of [Immortal-Protocols/lastbook](https://github.com/Immortal-Protocols/lastbook), kept at
[STAirye/lastbook](https://github.com/STAirye/lastbook) on the branch `fork/lightweight-gemma-no-us-maps` (that repository's
default branch). It is based on upstream Lastbook 1.1.11 and is not signed or published on lastbook.org. The library,
guides, search, the no-network rules and the bridge are upstream's. This file records what the fork changes and why, what
was measured, and what is still open.

| | Upstream | This fork |
|---|---|---|
| State map step in setup | Required: pick a US state, which downloads its map and address search | Gone. No state picker, no state map or address download |
| The map inside a pack (Medium: California, All: the whole US) | Kept | Kept by default. Optional: replace it with the world base map |
| Local AI model | Only the published Gemma 4 26B A4B file (exact name, size and SHA-256) | That file, or **your own Gemma 4 GGUF** (E2B, E4B, any quant), used from where it is |
| How your own model answers | — | It thinks first, and the thinking is hidden. Its context is cleared before each answer (see 3) |

## 1. No US maps

Two switches, both `False` in this fork:

- `MAPS` in `web/setup.js` hides the state picker in setup and the "Choose state" row in Library and local AI.
- `MAPS` in `engine/setup/api.py` stops setup adding a state's address index on its own. A map or address zip you pick
  yourself with "Choose a library zip or AI model file" still installs.

Set both to `True` to get the upstream behaviour back. The upstream tests run with `MAPS = True`: `AddressIndexes` in
`app/tests/test_setup.py` switches it on.

**Why:** upstream only has US state maps, built from US federal data (terrain from USGS, water from USACE and NHD, crops
from USDA, addresses from US Overture data), and setup wouldn't start until you picked a state. Outside the US the step is
useless. Only the world base map stays, which shows other countries at country scale.

### Removing the map a pack brings (optional)

Medium's zip has California's detailed map built in, and All's has the whole US. You download it either way, because it's
part of the pack's checked zip. Setup's choose screen shows a checkbox, unticked by default:
**Remove the bundled … map after unpacking**. Library and local AI has the same option as **Remove it** on the map row,
for a library that is already installed.

You can't just delete those files. The world base map lives in the same SQLite files (`national`, `water`, `terrain`,
`places`), and Check and repair would see them as damaged and download the whole pack again. So the fork rebuilds the base
map from them:

- `install.thin_to_base(src, dest)` (in `engine/setup/install.py`) follows the same rules as `base_set()` in
  `packaging/build_packs.py`: roads at zoom 8 and below, water at zoom 9 and below, relief to zoom 7, places not from
  OpenStreetMap, an empty street map, and no buildings, crops or atlas. A state set is the base set plus the rows inside
  the state's box, so this gives the base set back. The source files are only read.
- The result gets a `map-set.json` named `base`. Check and repair then checks the map files against it instead of
  `pack-manifest.tsv`, as it already does for state maps.
- During a pack install it runs in the staged library before the switch, as a job item `kind: "thin"`. In Library and
  local AI it's staged the same way a state map is and switched in when Lastbook restarts. If the result doesn't open, the
  old map is put back.
- It needs about 1.5 GB free while it runs. It saves about 3 GB on Medium, and much more on All.
- Not yet tried on a real library. The tests run it on small SQLite fixtures shaped like the real files.

## 2. Your own Gemma 4 GGUF

Pick the file with **Choose a library zip or AI model file** on the setup screen, or **Use your own Gemma 4 file** in
Library and local AI. You can also set `LASTBOOK_MODEL_FILE=/path/to/model.gguf`, which overrides both.

- The file is used from where it is and is not copied. Any folder works. An SSD loads it faster, so the same disk as
  `LastbookData` (or `LastbookData/models/`) is a good place.
- It must be a **Gemma 4** model (E2B, E4B, 26B A4B, 31B, any quantization), because Lastbook builds Gemma 4's own prompt
  format (`llm_local.render`). Other model families will load but answer badly or not at all.
- What's checked: the file exists, ends in `.gguf` and starts with the GGUF signature. There is no published SHA-256 for
  your own file, so its contents aren't checked. Get it from a source you trust.
- llama.cpp still measures whether it fits (`lastbook-llm --measure`). The memory estimate uses your file's real size
  (`llm_local.judge(fit, model_bytes)`).
- Where it's saved: `custom_model` in `LastbookData/derived/llm/state.json`. A file chosen during first-run setup waits in
  the app's `setup.json` until the new library opens (`api.opened()`).
- While your own file is chosen, setup never offers the published model, and Check and repair never downloads it.
  **Use the published model** switches back.
- The runner is upstream's `lastbook-llm` (llama.cpp b12032) and was not rebuilt. See 3 for a runner bug this works
  around.

**Measured on the fork's first test machine** (RTX 3080 Ti, 32 GB RAM): Gemma 4 E4B Q4_K_M from Hugging Face, 4.98 GB. All
43 layers on the GPU (about 3.9 GB of VRAM plus 2.4 GB of RAM), loaded in about 3 s, and an answer with hidden thinking
takes about 8 s.

## 3. Making a small Gemma 4 answer well

The published 26B was evaluated by upstream with thinking off. E4B behaved differently. Each step below fixed a problem
found by testing, in this order.

### 3a. Thinking text in the answer (first fix, later replaced)

Upstream tells the model to skip thinking by ending the prompt with an empty thought block,
`<|turn>model\n<|channel>thought\n<channel|>`, which matches the 26B's template. E4B's own chat template (stored in the
GGUF as `tokenizer.chat_template`) starts the model's turn with `<|turn>model\n` alone. Given the empty block, E4B thought
anyway, in plain text ("Here's a thinking process…"), and Chat showed it.

First fix: start the answer the way the file's own template does (`llm_local.answer_start`, which reads the template with
`gguf_chat_template`). That hid the thinking, but showed the next problem.

### 3b. Follow-up questions lost their sources

With thinking off, E4B's first answers cited sources correctly (`[S2]`). Follow-up questions didn't. Measured on one
follow-up repeated 6 times: 2 of 6 answers cited correctly. The others cited as "(Title, p. 29)", which Chat can't link
and marks as "This answer has no linked sources", or came back as a stray fragment.

Why: before a follow-up, `web/chat.js` (`history_()`) rewrites earlier answers' `[S2]` into "(Title, p. 29)". That's
upstream's design, because keys are numbered per question. Lastbook puts the instructions and the new search results at
the top of the prompt, then the conversation, so the nearest example E4B sees before it writes is its own earlier answer in
that style. The 26B follows the rule anyway; E4B copies the example. Two prompt-only fixes were tried and didn't help:
removing old citations from history (2 of 6 correct), and a reminder added to the question (0 of 6).

### 3c. Let it think, and hide the thinking

Before 3a, E4B was really thinking, just visibly, and its sources were cited correctly. So for your own file the fork now
switches thinking **on**, the way the file's template does it, and hides the thinking:

- `llm_local.thinks(path)`: on when the file's template supports thinking (contains `<|think|>`). `LASTBOOK_AI_THINK=0`
  turns it off.
- `render(..., think=True)` puts `<|think|>` at the top of the system turn and starts the answer with `<|turn>model\n`.
  After tool results it reopens the thought channel, as the template does.
- `llm_local.hide_thinking()` removes the thought channel from what Chat shows, while it streams and in the final text.
  An unclosed block hides everything after it.
- Each round gets `THINK_TOKENS` (1500) extra tokens of room for the thinking, in `assistant._local_round` and
  `_fit_prompt`.
- The published 26B is unchanged (thinking off, upstream's ending).

With this, follow-ups cited correctly, but some answers still showed thinking. See 3d.

### 3d. A runner bug: reusing context with Gemma 4's sliding window

With `LASTBOOK_AI_DEBUG=1`, the log showed that in the bad answers the model's output **began in the middle of its
previous answer's thinking**: no opening `<|channel>`, only the closing `<channel|>`. Nothing was lost in transit: the
runner's generated-token count matched what Lastbook received.

Cause: `packaging/llm/lastbook_llm.cpp` reuses the longest shared start of the previous prompt and removes the rest with
`llama_memory_seq_rm`, starting over only if that call fails. Gemma 4's sliding-window layers keep only about the last
1024 positions (E4B's log shows a 1024-cell SWA cache). After a long answer, the window no longer holds what comes just
before the shared start, but the call can still succeed. The model then reads a damaged context and carries on from its old
thinking. llama.cpp's own server checks `llama_memory_seq_pos_min` and reprocesses the prompt when the window is incomplete;
this runner doesn't. The bug is upstream's too, and probably affects the 26B in long chats.

Workaround, with no rebuild (`Local._forget_context`): before each request, for your own file only, Lastbook sends a
one-token request whose first token differs from any prompt's (`\n` against `<|turn>`). The real request then reuses
nothing, so the runner clears the context and reads the prompt from the start. The real prompt isn't changed. It costs
rereading the prompt (about 3,000 tokens) every round; on the 3080 Ti a whole answer still takes about 8 s.
`LASTBOOK_AI_REUSE=1` turns the workaround off.

Result (E4B, through the real chat pipeline, `server.py` with the local AI on): the same follow-up 6 times out of 6 cited
correctly; 3 new first questions cited correctly (14, 13 and 22 keys); every round had an intact, hidden thought block
(10 of 10).

**The real fix, in the runner (2026-11-17).** Before reusing, `lastbook_llm.cpp` now makes llama-server's check
(`tools/server/server-context.cpp`, `pos_min_thold`). The first token read next, at position `keep`, looks back `n_swa`
positions (`llama_model_n_swa`, 512 for E4B; the cache holds 1024 cells). If `llama_memory_seq_pos_min` is at or past
`keep - n_swa + 2`, the window no longer reaches that far, so the runner clears the context and reads the prompt from the
start. Otherwise it reuses as before. The fixed runner says `"swa_check": true` in its ready event, and then Lastbook skips
the workaround (`Local.needs_forget`). An older runner (the release's) still gets the workaround.

Measured with E4B, three-turn chat (3e), 6 runs of the last question plus the two turns before it: 9 of 9 rounds began with
an intact thought block. 8 rounds started over because the window was too short (`n_reused: 0`). One round reused the whole
prompt (`n_reused: 4326`): the answer before it was short (494 tokens), so the window still covered it, and that answer came
out right too. The check and its wording would make a good pull request upstream: the release runner has the bug, and it
probably affects the 26B in long chats.

### 3e. From the third turn on, citations as "(Title, p. N)" again

Found by hand: the third question of a chat came back citing "(Water and Health, p. 12)", and Chat said "This answer has no
linked sources". The tests in 3b–3d only covered two turns. Reproduced through the chat pipeline: 3 turns, the last one
asked 4 times, **0 of 4** cited with keys. With two earlier answers in "(Title, p. N)" style just before its own, E4B copies
them even while thinking.

Fix (`assistant.rekey_history`, your own file only, after the first search of the turn): in the earlier answers the model
sees, a citation of a page (or a video moment) that this turn's sources hold again becomes this turn's key, `[S1]`. Every
other citation is removed. That includes a known title alone, since the catalogue's titles are matched. Other parentheses
stay. Every example before the new answer then cites the way it must. The browser's own history is unchanged.
`LASTBOOK_AI_REKEY=0` turns it off.

Result: the same chat, 6 of 6 with keys only and no "(Title, p. N)". The same 6 of 6 with the fixed runner and no
workaround, and again with default settings.

### 3f. Building the runner on Windows

`packaging/llm/build_llm_windows.sh` needs portable tools in one folder (`TOOLS`). On the fork's test machine they are in
`D:\buildtools\lastbook-llm\`, downloaded 2026-11-17:

| Tool | From | Checked |
|---|---|---|
| `llvm-mingw-20261020-ucrt-x86_64\` | github.com/mstorsjo/llvm-mingw release 20261020 | SHA-256 matches GitHub's and the script's |
| `cmake-4.4.0-windows-x86_64\` | github.com/Kitware/CMake v4.4.0 | same |
| `ninja.exe` | github.com/ninja-build/ninja v1.13.2, `ninja-win.zip` | same |
| `msys\ucrt64\` | repo.msys2.org/mingw/ucrt64: shaderc 2026.3-1, glslang 16.3.0-1, spirv-tools **3~**1.4.350.1-1 (the name has an epoch), gcc-libs 16.2.0-3 | HTTPS only (signatures downloaded but not checked: no MSYS2 keyring here) |
| `vulkan-headers\`, `spirv-headers\` | git clones at tag `vulkan-sdk-1.4.350.1` | commits `8864cdc8`, `ad9184e7`, as the script says |

The `.pkg.tar.zst` files unpack with Python 3.14's own `compression.zstd` and `tarfile`. Then, in Git Bash:

```bash
TOOLS='D:\buildtools\lastbook-llm' W='D:\buildtools\lastbook-llm\work' bash packaging/llm/build_llm_windows.sh
```

Set `W` outside the repo: by default it's `derived/llm`, and the script empties `W/bin-win` first, which is where the app
runs the runner from. A first build takes about 3 minutes on the 5800X3D, and a rebuild after changing only
`lastbook_llm.cpp` takes seconds. The script's own checks (no network imports, no folder of this machine inside) passed.
Copy `W/bin-win` to `derived/llm/bin-win`. The release's runner is kept beside it as `derived/llm/bin-win.release`.
Smart App Control (see the script's note) is not on this machine.

### 3g. A 10-turn stress test: a confused user

`tools/fork_chat_test.py`: 10 questions about stored water, run through the chat pipeline as the browser runs them. They
include typos, a unit correction at turn 5 ("wait sorry i meant 2500 meters not feet"), and a **mistake** at turn 6: the
person says the assistant told them boiling removes chemicals and the water smells of bleach. Turn 7 is "im confused now",
and turn 10 is "give me the short steps again". Two conversations per arm, 20 answers. "Good" means it has `[Sn]` keys, no
citation written with a title, and no thinking shown.

| Arm | What's on | Good |
|---|---|---|
| B | Fixed runner, no history rewrite (`LASTBOOK_AI_REKEY=0`) | **4 of 20** |
| A | + history rewrite (3e) | 14 of 20 |
| A2 | + answer repair and follow-up search (below) | 14 of 20 |
| A3 | + previous answer's pages carried over (below) | **20 of 20** |

What each run showed:
- **B:** one conversation switched to "(Title, p. N)" from turn 3 on, and the other to `(S4)`, `(S2, S3)` from turn 2 on.
  Whatever style slips in once stays, because the history carries it.
- **A:** no title citations, but turns like 5, 7, 9 and 10 had nothing to cite. The first search uses only the latest
  message, and "wait sorry i meant 2500 meters" finds little. Turn 5 even said the library didn't cover altitude, although
  turn 4 had cited the 3-minute rule. One answer cited as `[CERT Basic Training Participant Manual (2019), p. 27]`. That
  title holds parentheses, so 3e's pattern hadn't matched it in the history.
- **A2:** turn 5's content was right (3 minutes), but it was cited from memory, once with a made-up title and page.
- **A3:** every answer cited with keys. Content checked by hand in both conversations: turn 5 says 3 minutes at 2500 m,
  cited. Turn 6 corrects the person plainly ("No, that is incorrect … Boiling does NOT get rid of toxic chemicals"), cited.
  Turn 8 gives the library's dose (40 drops, or ½ teaspoon, for 5 gallons). Turn 9 says the library has no child-specific
  guidance, under "Not found in the library". Answers took 4–12 s.

The three additions, all for your own file only:
- `assistant.repair_cites`: in the final answer, `(S4)` / `(S2, S3)` become `[S4]` / `[S2][S3]`. "[Title, p. 12]" or
  "(Title, p. 12)" becomes the key when that page is among this turn's sources. Otherwise it stays as written, and Chat shows
  it as not linked. The keys are then validated as usual. In the history, keys left in parentheses are removed, because
  they were numbered for another question. Off with `LASTBOOK_AI_REKEY=0`, together with 3e.
- `assistant.followup_hits`: for a follow-up, a second search runs on the previous question with this one. This message's
  best hits come first, then the joined search's new ones, then the rest, 8 in all.
- `assistant.cited_before`: the PDF pages the previous answer cited (up to 3, taken from its "(Title, p. N)" and looked up in
  the catalogue) go first among this turn's sources, with their full page text. Then a clarification has the page it's
  about, with a key. Off with `LASTBOOK_AI_FOLLOWUP=0`, together with the follow-up search.

3e's pattern now matches the catalogue's known titles first, with an optional page or time, so titles holding parentheses
are handled.

## 4. Running from source on Windows

Running from source needs two things from an upstream release, copied in (both folders are ignored by git):

- The AI runner: the release's `_internal\llm\` to `derived\llm\bin-win\`.
- The WebView2 SDK DLLs (`Microsoft.Web.WebView2.Core.dll`, `Microsoft.Web.WebView2.WinForms.dll`, `WebView2Loader.dll`):
  the release's `_internal\webview2\` to `app\webview2\`. Without them the window says "Lastbook could not load the files
  it needs to show its window".

Then `python app/main.py --data <path to LastbookData>`. The packages are in `packaging/requirements_app.txt`.

## 5. Diagnostics

| Setting | What it does |
|---|---|
| `LASTBOOK_MODEL_FILE` | Use this GGUF, whatever setup saved |
| `LASTBOOK_AI_THINK=0` | Your own file answers with thinking off (3a's behaviour) |
| `LASTBOOK_AI_REUSE=1` | With an older runner, skip the workaround and let it reuse context (upstream's behaviour; see 3d). The fork's runner checks the window itself |
| `LASTBOOK_AI_REKEY=0` | Send earlier answers' citations as the browser wrote them, "(Title, p. N)", and don't repair the answer's citations (3e, 3g) |
| `LASTBOOK_AI_FOLLOWUP=0` | Search only the latest message, with no pages carried over from the previous answer (3g) |
| `LASTBOOK_AI_DEBUG=1` | Log each round's raw output (thinking and markup included) and the runner's token counts, as `local AI raw:` and `local AI done:` |

The app log is `LastbookData\derived\logs\lastbook.log`, and the runner's is `local-ai.log` beside it. For your own file the
log says `local AI: your own model file; it thinks (hidden) before answering`.

To test through the chat pipeline without the window: `LASTBOOK_DATA=… LASTBOOK_LOCAL_AI=1 python server.py --port 8899`,
then POST `{"messages": [...]}` to `/api/chat`. It answers as server-sent events (`delta` events carry the text).

## 6. Other fixes in this fork

- `app/tests/test_chat_steps.py` (upstream's) read Node's output in Windows' default cp1252 and failed. It now reads UTF-8.
  The same fix would work upstream.

## Tests

Run the suite from [CONTRIBUTING.md](../CONTRIBUTING.md). The fork's own cases are in `app/tests/test_setup.py`:
`ForkNoMaps` (no state step, thinning the map), `ForkCustomModel` (choosing, saving and clearing your own file) and
`ForkLocalAI` (template reading, answer start, thinking, hiding thinking, clearing context unless the runner checks the
window, history citations rekeyed, answer citations repaired, follow-up hits and carried-over pages, memory estimate). The
model-level stress test is `tools/fork_chat_test.py` (3g), which needs the model and a test server.

## Open

- Thinning a real pack's map (1) and the setup screens with no state picker have only been tested by the automated tests,
  not by hand.
- The runner fix (3d) is built and tested on this machine only. A release of the fork would ship it from
  `build_llm_windows.sh` (and the Mac and Linux scripts, not yet rebuilt). It's also a candidate pull request upstream.
- 3g was measured on one topic (stored water), 2 conversations per arm. Other topics, video citations (carry-over handles
  PDF pages only), and the published 26B with these changes (they're off for it) haven't been measured.
- The follow-up search and carry-over add a little prompt (up to 3 full pages). On a slower computer that's slower reading.
- Thinking makes answers slower than thinking off. On a slower computer, `LASTBOOK_AI_THINK=0` trades citation reliability
  in follow-ups for speed.
- Showing the hidden thinking in a collapsible section of the answer (as Chat's "How it searched" does) was suggested; not
  built.
- **Maps outside the US.** Every detailed layer is built from US data (see [MAPS.md](MAPS.md)). A street map for another
  country from an OpenStreetMap extract, using `tools/build_map.py`, would be a separate piece of work.
