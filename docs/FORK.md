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

The real fix belongs in the runner: after `llama_memory_seq_rm`, check `llama_memory_seq_pos_min` against the window, as
llama-server does, and clear the context when it's too short. That needs a rebuild with the toolchain in
`packaging/llm/build_llm_windows.sh` (llvm-mingw, CMake, Ninja, glslc, Vulkan and SPIR-V headers), and it would make a good
pull request upstream.

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
| `LASTBOOK_AI_REUSE=1` | Let the runner reuse context (upstream's behaviour; see 3d) |
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
`ForkLocalAI` (template reading, answer start, thinking, hiding thinking, clearing context, memory estimate).

## Open

- Thinning a real pack's map (1) and the setup screens with no state picker have only been tested by the automated tests,
  not by hand.
- The runner fix for 3d, plus a rebuild.
- Thinking makes answers slower than thinking off. On a slower computer, `LASTBOOK_AI_THINK=0` trades citation reliability
  in follow-ups for speed.
- Showing the hidden thinking in a collapsible section of the answer (as Chat's "How it searched" does) was suggested; not
  built.
- **Maps outside the US.** Every detailed layer is built from US data (see [MAPS.md](MAPS.md)). A street map for another
  country from an OpenStreetMap extract, using `tools/build_map.py`, would be a separate piece of work.
