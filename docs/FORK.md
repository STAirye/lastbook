# Fork: custom lightweight Gemma 4, no US maps

This is an unofficial fork of [Immortal-Protocols/lastbook](https://github.com/Immortal-Protocols/lastbook), kept at
[STAirye/lastbook](https://github.com/STAirye/lastbook) on the branch `fork/lightweight-gemma-no-us-maps` (that repository's
default branch). It is based on upstream Lastbook 1.1.13 and is not signed or published on lastbook.org. The library,
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

### 3h. Keyword search misses everyday wording (upstream)

Found by hand: "i need to start a fire but i have no matches and no gas" was answered with "the library does not contain
detailed instructions", and "that looks like a... concerning oversight" got an apology. Four manuals in the library cover
it: ATP 3-50.21 (p. 121–129), FM 21-76 (p. 66–70) and the USMC Summer and Winter handbooks (p. 34–36).

- **Not the model, and not the fork's changes:** the first search (`assistant.hybrid`) returned one useful page. The others
  were about fireplaces in earthquakes, wind turbines and trail steps. The desktop app searches by keyword only, and every
  word is required. Fire-*safety* pages mention start, fire, matches and gas, so they win; the survival manuals say
  tinder, kindling, ignition. Reproduce with `/api/retrieve?q=…`.
- **Tried and dropped:**
  - A guard that sent "not found in the library" answers back once to search again: 2 of 8 answers named a method,
    against 3 of 8 without it. E4B ignored the nudge or searched with poor words.
  - Searching without the things the person lacks ("no matches", "ran out of formula"): 99 → 88 useful hits on 16
    prompts. It broke "ran out of baby formula" (7 → 0) and "ran out of insulin" (5 → 1), where the lacked thing is the
    topic, and didn't help the fire question, because the pages with every word are the fire-safety ones.
- **Fix (`server.PHRASES`, upstream's own mechanism for everyday wording):**
  - "start / make / light / build a (camp)fire" searches as fire AND (tinder OR kindling OR firecraft). Not "building
    fire", which is a building on fire. "ignition" was tried too: it brought welding and hazmat pages back.
  - "make / keep the water safe", "purify water", "treat water" search as water AND (disinfect OR purify OR treatment OR
    chlorine). Not "make it safe", which can be about anything.
- **Measured** with `tools/fork_search_check.py`: 20 everyday prompts, most saying what the person lacks, plus controls
  (a building fire, a kitchen fire, "no pulse", "no running water"). It counts the top 8 hits whose title or excerpt has a
  word a useful page would have, before (the committed code, served from a worktree) and after. **109 → 121 of 160**:
  fire without matches 2 → 7, light a campfire 2 → 8, purify creek water 6 → 7, and every other prompt is unchanged,
  controls included.
- **End to end with E4B:** the fire question plus "concerning oversight", 4 runs: 3 of 8 → 6 of 8 answers naming a method
  with citations (7 of 8 counting one that wrote "Bow & Drill"; the eighth asked what was missing). All four first answers
  name flint and steel, bow drill or hand drill, with 12–24 keys. The 10-turn test (3g) stays at 20 of 20. Eight single
  questions (campfire, creek water, no fuel, cooking without power, baby formula, building fire, kitchen fire, no pulse)
  are all cited and on topic.

This is a change to search, so it applies to every model, the published 26B too. `test_bridge.ForkSearchWords` covers
the phrases and the controls.

**Later bug: the phrases inside injury questions** (found by tracing #154's questions). "treat water in the lungs after
drowning" was searched as water AND (disinfect OR … chlorine) AND lungs AND drowning. No page has all of them, so the
search relaxed to any of the words, and the six helper words and the title bonus put water-treatment manuals first: 0
useful of 8 (keyword-only). The same for "light a fire to keep him warm with hypothermia" (0 of 8) and "carbon monoxide
from making a fire in the tent" (3). Upstream, with no phrases, did better on these.

- **Fix:** the two how-to phrases (making fire, making water safe) are not used when the question names an injury:
  `engine/confidence.INJURY`, the injury words of the urgent list (breathing, drowning, burned, scald, shock, poison,
  hypothermia, frostbite, injured, fell, caught fire …) plus lungs, monoxide, inhaled, blisters, electrocuted, coughing.
  Not the whole urgent list: its fire, smoke, gas, baby and cut would also stop "how do i light a campfire" and "make the
  water safe for a baby's formula". A bare "burns" or "smoke" doesn't count ("wood that burns longer"). The other phrases
  (power cut, heart attack, can't breathe …) are unchanged. `LASTBOOK_PHRASE_INJURY=0` turns it off.
- **Tried and left off:** when every word finds too few pages, search every word again without the phrase's helper words
  before relaxing (`LASTBOOK_PHRASE_RETRY=1`). It fixes the same questions, but "start a fire with no matches and no gas"
  fell 7 → 2 useful: without tinder and kindling, fire + matches + gas finds the fire-safety pages again.
- **Measured** in-process on the 362 labelled questions and #154's 32 (+ typos), four arms, keyword-only and hybrid
  (`.claude/drafts/triage/AB_PHRASES.md`). Keyword-only, with the fix: first page right 150 → 153 and a right page in the
  top 3 199 → 204 of 253; #154's count 144 → 168 of 256 (typos 152 → 169). Drowning 0 → 4 useful (first right),
  hypothermia 0 → 4, carbon monoxide 3 → 8. No question worse. The how-to questions are as before: campfire 8, no matches
  7, water safe to drink 8, formula 8. Hybrid moves a page or two either way (#154 186 → 189). The confidence buttons:
  confident misses 18 → 17 and 6 → 4, urgent pages hidden unchanged (none from the phrases).

**Later: the phrases on safety and medical questions** (#128's review, #154). "how do i prevent a generator from starting
a fire" was searched as firecraft (first page a winter survival handbook), "make a fire escape plan for my family" too
(the Army survival manual), and "how do i treat water intoxication" as drinking water (wastewater manuals).

- **Fix:** the fire-making phrase is also not used when the question has prevent, avoid, stop, risk, hazard, cause,
  escape, spread, safety or drill (a fire drill; a bow drill still makes fire). The water-safe phrase is not used for
  intoxication, poisoning, lungs or overdose. `test_bridge.ForkSearchWords` pairs each how-to with its safety or medical
  counterpart (start a fire / prevent a generator from starting one, make a fire / a fire escape plan, make the water
  safe / water intoxication …), as #128's review asked: the how-to keeps the manuals' words, the counterpart its own.
- **Measured** in-process on every triage set (`.claude/drafts/triage/BODY_SIGNS.md`): only the target questions move.
  Keyword-only: generator (clean and typo) first page right 0 → 1 (an aircraft manual's fire-prevention page, 2 → 3
  useful); escape plan ×4 4 → 6–8 useful ("Make a Family Emergency Plan" first instead of the Army manual); water
  intoxication still has no right page, but its confidence falls 0.66 → 0.28, so it gets buttons instead of a sure
  answer. On all 599 questions first right 351 → 353 from these, useful +12, nothing worse. Hybrid: water intoxication
  0 → 1 first right ("Food and Water in an Emergency", clean and typo), the generator question gets the Honda manual
  first, and the escape plan ×4 scores 1 → 0: "Make A Plan" (a family-plan page) instead of "Mult-Family Home escape
  routes", which the scorer's escape pattern doesn't count. Nothing else moved.

### 3i. Questions in Spanish (and other languages)

Gemma 4 reads and writes Spanish, but the library is in English, and so is its keyword search: "¿cómo purifico agua de un
estero?" searched as typed finds Spanish FEMA leaflets ("Prepárese", "Ciclones Tropicales") and nothing about purifying
water. The model's own searches were in Spanish too ("primeros auxilios torniquete") and found the same leaflets.

- **English search words first** (`assistant.english_query`). When a question looks non-English (`needs_english`: words
  with letters beyond a–z, like ñ, á or 水, and common Spanish, Portuguese and French words outweigh English function
  words; text is composed (NFC) first, since a phone or Mac may send "niño" as n plus a combining tilde), the local model
  writes the question as English search words: one short call, thinking off, at most 32 tokens. The first search uses
  those, falling back to the original wording if they find nothing. For a follow-up, the earlier question goes along so
  "¿y si el agua está turbia?" becomes "chlorine dosage turbid water", and the joined search (3g) uses the earlier
  question's English words. English questions skip all of this.
- The search runs before the model starts. For a non-English question the model now starts first, since it's needed for
  the answer anyway. Only for your own file (like 3g); off with `LASTBOOK_AI_ENGLISH_SEARCH=0`.
- **The answer** gets one note: the library was searched in English with these words, search again in English, answer
  in the question's language. Asking it also to keep the three special headings in English ("Not found in the library:"…)
  made E4B write its other headings in English too ("Direct Answer"), so that was dropped. Instead `web/chat.js` also
  knows the headings in Spanish ("No encontrado en la biblioteca", "Las fuentes no coinciden", "Mi propio razonamiento"),
  only as headings, and starts a sentence at ¿, ¡ and capitals like É or Ñ when it marks uncited sentences.
- **Measured** with E4B on 8 Spanish questions (fire without matches, creek water, tourniquet, fridge after a 2-day
  outage, scald, gas leak after an earthquake, bleach for 20 litres, then "¿y si el agua está turbia?"): **8 of 8** answers
  cited and on topic (survival manuals' fire pages, WHO water notes, tourniquet guides), against **5 of 8** with
  `LASTBOOK_AI_ENGLISH_SEARCH=0`, whose cited pages were mostly the generic Spanish leaflets. All 16 answers were in
  Spanish. About 2–3 s more per question (mean 12.6 s against 10.0 s).
- **The rewrite prompt, tuned** (`assistant.REWRITE`). Keyword search needs every word on the page, and the first
  prompt ("key things, at most 8 words") gave words no manual uses: "Disinfecting non-potable water **methods**",
  "Earthquake gas leak check **procedure manual**", and after a question about caustic soda, "Sodium hypochlorite **vs**
  caustic soda **comparison**". None of them finds Hesperian's bleach table. The prompt now says the search needs every
  word, asks for 2 to 5 words a page with the answer would contain (things, symptoms, products, amounts with units, the
  product rather than the brand), names the words to leave out, says to search for what the person needs now, and gives
  three examples. On 14 Spanish questions (the 8 above, a follow-up about boiling time, a baby's diarrhoea in Chilean
  Spanish, a recluse spider bite, water for 4 people, insulin run out), counting the first search's top 8 hits whose title
  or excerpt fits the question: **0** searched as typed, **74** with the first prompt, **97.5** with this one, of 112
  (2 rounds; a rerun gave 95). "¿cuánto cloro le echo a 20 litros?" now searches "bleach 20 liters" and finds the table
  first. Each rewrite takes 0.1–0.4 s with E4B; the 2–3 s measured above was mostly starting the model sooner.
  Tried and dropped: a rule and example for carrying an amount from the earlier question ("tengo clorox al 5%" after
  "5 galones" still gave "sodium hypochlorite 5%"); no measurable change.
- **Not fixed:** the Spanish documents in the library are no longer what the first search finds for Spanish questions
  (they rarely answered them). "estero" was rendered "estuarine" (in Chile it's a creek); the results were still right.
  One answer misread a dose table; that is 3j.

`ForkLocalAI.test_english_search_for_other_languages` and `test_chat_steps.SpanishAnswers` cover it, with ñ, ü, ¿, ¡,
accented capitals and decomposed letters.

### 3j. Tables read row by row (upstream)

Found by hand: "¿cuánto cloro le echo a 20 litros de agua?" got **5 teaspoons** of 5% bleach, 3 runs of 3, citing
Hesperian's "Water and Sanitation: Keys to Staying Healthy" p. 23 and "Protecting Community Water" p. 36. Both say
**1/2 teaspoon for 20 litres**; 5 teaspoons is the 200-litre barrel. Ten times the dose.

- **Not the model, and not the library text.** The text is `pdftotext -layout`, so tables keep their columns as runs of
  spaces. `assistant.py` squashed every run to one before the model read a page (`read_pages`, the first search's best
  pages, "ask about this page"; upstream code). That reads a page line by line, and when a row's label takes two lines
  with its amount between them, or prose runs beside the table, the rows interleave:
  `For 5 gallons or / 1/2 teaspoon / 20 liters / For a 200 liter / 5 teaspoons / barrel`. It applies to every model,
  the published 26B too.
- **How common:** of 136,796 PDF pages, 783 have a column of amounts (a number and a unit) beside labels; on 617 of
  them the old reading runs rows together (2,878 of 6,264 rows; judged from the rebuilt table, so an estimate). 174 of
  those pages are in health and water documents (40 documents: Hesperian, MSF, WHO, ICRC). Sized with
  `engine/page_tables.tables` over the library, no model.
- **Fix (`engine/page_tables.py`, used through `assistant.page_body`):**
  - Find columns of amounts that stand apart, take the columns beside them (a column of prose beside a table is
    recognised and left as prose), let each amount start a row and attach each label line to the nearest amount. The
    table is written one row per line: `For 5 gallons or 20 liters | 1/2 teaspoon`.
  - Only when that is clearly right: few empty cells, no cell over 3 lines, no row taking a label line that doesn't touch
    it, no unrecognised value between rows, no cell holding two amounts. Otherwise, if the old reading ran its rows
    together, the table is kept **as printed** (blank columns dropped, so columns still line up). A table laid across
    (weights as columns, as MSF prints nebulised epinephrine) is also given read down each column: "Column 4: 4 to,
    6 months, 7 kg, 3.5 mg, 3.5 mL, 1 mL". Pages with no such table read exactly as before.
  - Page caps (3,200 / 3,500 / 4,000 characters) count the text as the old squash would, so kept spaces don't push
    content out.
  - A search excerpt (FTS snippet) of a table page runs rows together too: it's followed by the table, one row per line,
    or a pointer to `read_pages` (`assistant.excerpt_body`).
  - One line in the system prompt: tables come as `|` rows or as printed; take an amount only from the matching row or
    column, say which, and don't work out a new amount. Measured neutral (below), kept as a statement of rule 2 for
    tables.
  - `LASTBOOK_AI_TABLES=0` gives the old reading, and no prompt line.
- **Considered, not built** (not measured with the model): keeping every page's spaces (no squash at all) still leaves
  the bleach table's amount between its two label lines, the same ambiguity, on every table page. Re-extracting the PDFs wasn't needed: the
  layout is already in the shipped text. An answer check (an amount not next to the asked quantity in the cited text)
  wasn't built: after the fix the remaining misses are in one table, and such a check would need the quantity parsed
  from the question.
- **Measured** with `tools/fork_table_test.py`, E4B, 14 questions whose answer is one table row (bleach for 1, 4, 20
  and 200 litres; ferrous sulfate for a 5-year-old; vitamin D for 6 months; nebulised epinephrine for 7 kg; each in
  English and Spanish), 3 runs each:

  | | Right | Wrong | Other |
  |---|---|---|---|
  | Old reading (`LASTBOOK_AI_TABLES=0`) | 32 of 42 | 9 | 1 |
  | Rows only | 39 | 2 | 1 |
  | Rows, printed tables completed, excerpts | 36 | 1 | 5 |
  | + prompt line | 37 | 2 | 3 |
  | + read down each column (final) | **41** | **0** | 1 |

  Bleach for 20 litres: **1 of 6 → 6 of 6** in every arm with the fix (the old reading said 5 teaspoons, or 8 drops).
  "Other" is mostly answers giving the right amount with other rows beside it (bleach per litre from the US Army water
  manual's table, which lists several volumes) or an amount from elsewhere on the page (vitamin D's after-treatment
  dose). Ferrous sulfate and vitamin D (a table the old reading already got right) stayed right. Nebulised epinephrine
  for 7 kg, a table laid across: 1 of 6 right with the old reading, 2–4 of 6 with rows only, **5 of 6** with read down
  each column; the sixth gave 3.5 mL from one MSF printing and 3 mL (the 6 kg column) from the other. Each arm is one
  set of 3 runs, so differences of one or two answers between the middle arms are noise.

`ForkLocalAI.test_tables_are_read_by_row`, `test_tables_that_cannot_be_split_stay_as_printed` and
`test_page_body_caps_and_switch` cover it, with both printings of the bleach table.

### 3k. Search as triage: long pages, typos, conversations

Measured on a test set of 362 invented questions over 159 topics (emergency medicine, firefighting, disasters, a little
security, everyday tasks): 253 clean questions coloured red / yellow / green by urgency, 22 counterexamples ("brake
bleed" is not bleeding), 109 typed with panicky typos. Each lists the words a useful page must have, and a page that
must not come first. Plus 52 invented conversations, scored on the last message. The set and scorer live outside the
repo for now (upstream issue #154 asked for a test-only pull request of them).

- **Long saved web pages in sections** (`engine/sections.py`). 353 saved HTML pages are whole books (over 20,000
  characters, up to 4.4 MB) and match nearly any question: *Modern Machine-Shop Practice* came up for 26 of the 362.
  Each is cut into sections of about 5,000 characters, after a sentence where possible (the stored text has no
  headings; 351 pages → 7,623 sections, 4 s, stored in
  `derived/index/sections-<hash>.sqlite`, since the pack's `search.sqlite` is checksummed and stays as shipped). The
  meaning-based passages are relabelled to their section. Search returns the section; the reader opens the page at it
  and shows "Section N of M". Machine-Shop questions: 26 → 4. Hybrid search on the long pages: 4.95 s → 0.68 s.
  Tried and dropped: a score penalty for long pages (26 → 19).
- **Typos** (`engine/typos.py`). Keyword search needs whole words, so "breating" matches nothing. A word not in the
  library is replaced by the closest library word (edit distance, weighted to words in emergency books, first letter
  kept, keyboard-neighbour swaps and doubled letters cheaper), before both searches. "my husbnd colapsed and isnt
  breating" → "my husband collapsed and isn't breathing". 99 of the 109 typo questions changed, 0 of the 253 clean
  ones. The corrected question is returned as `corrected` by `/api/find` and `/api/retrieve`. `LASTBOOK_TYPO_FIX=0`
  turns it off.
- **Words typed with no spaces** (`typos.split_word`). In a live test the first message "heschuokinghelkp" ("he's
  choking help") got no buttons and was answered as plain "help": the correction works word by word, so a 16-letter
  blob was never corrected, and `urgent()` never saw "choking". Now a word of 8 or more letters that the index doesn't
  hold is cut into the library's words where that is clearly better than leaving it. Every way of cutting it is weighed
  at once (dynamic programming over where the spaces go): each piece costs how rare its word is in the library (log of
  the commonest word's pages over its own), plus 5 when the piece is a slip for its word (the same slips as above: one
  edit, first letter kept, a doubled letter cheaper; 8 for a changed letter that isn't a neighbouring key), plus 1 for a
  missing apostrophe ("hes" → he's); each space costs 3. Pieces of one or two letters only from a short list ("a", "my",
  "is", …), not the index's "jd" or "ed". The cut is used when it costs at most −4 + 1.5 per letter + 4 per space, and 4
  less than the word corrected whole (that one a little cheaper for a word of the emergency books: "overdoes" is
  overdose, not "over does"). A word on 3+ pages ("firecraft", "gutenberg") is never cut.

  The costs were chosen on data: 2,729 runs of 2–6 words glued from the test questions (clean) and 1,157 from their
  typo versions, against 800 long words with one or two typos (they must be corrected, not cut) and 800 real rare words
  of the index treated as unknown. Chosen setting: clean runs cut at the right places 94% (wrong 3.5%, mostly "in to"
  for "into" and "can not"), typo runs 79% (wrong 8%), long words with typos cut 1%. Real rare words are cut 35% of
  the time ("pilocarpine" → pilot car pine), but only words the index doesn't hold are ever tried, and those find
  nothing as typed anyway. It costs nothing for a question without such a word, and a few milliseconds for one with it
  (the slips are looked up through the index of words with a letter dropped that the two-edit correction already
  builds). `LASTBOOK_TYPO_SPLIT=0` turns the splitting off.
- **Ordinary English is left alone** (`typos.is_english`). The correction only knows the library's words, so on a
  held-out list (3l) it bent everyday words into other words: "keeled" → peeled, "puking" → poking, "spewing" →
  sewing, "blacked" → blocked, "gasps" → gaps, "seizes" → sizes, "texted" → tested, about 40 lines in 690. Now a word
  of a general English word list is never corrected, split or made a body word. The list is
  `engine/english_words.txt.gz` (78,238 lower-case words, 210 KB, read in about 20 ms): every form of the hunspell
  en_US dictionary, made from SCOWL, with its affixes applied, taken by `tools/english_words.py` from the copy Chrome
  keeps for spell checking. Its licence is SCOWL's, permissive (use, change and share, also commercially, with the
  copyright notices): `engine/english_words.LICENSE.txt`, whose notices still have to be replaced by the verbatim
  README before a release. British spellings count through the American one ("colour", "haemorrhage"), and a few chat
  words and medicine names are added ("lol", "mum", "paracetamol").

  A few real words are nearly always a slip for an emergency word here, and those are kept in two short, explicit
  lists: one word alone (`SLIPS`: "chocking" → choking, "brunt" → burnt, "overdoes" → overdose, and "wile" → while, which two typo questions of 3k needed), and by the words
  around them (`PHRASE_SLIPS`): "he cant breed", "hes not braking", "she is not breaking" → breathe/breathing (not when
  the question names a car, brakes, an animal, bread …), "breeding a lot from the leg" → bleeding, "sea sure" →
  seizure, "past out" → passed out, "cheat pain" / "chest pane" → chest pain, "hart attack", "gas leek", "face is
  dropping" → drooping, "pulse is week" → weak. Some misspellings too far from their word, or one edit from another
  real word, were added to the known list ("hemmorage", "unconshus", "tournaquet", "strock", "poisend", "hlep"). Letters
  typed again and again are cut to one or two first, to whichever is a word ("bloooood" → blood, "helpppp" → help,
  "hesss" → he's; "kkkkk" stays mash). `LASTBOOK_TYPO_ENGLISH=0` turns all of this off. Speed on the 690 lines: 0.26 ms
  a question on average (0.33 before), at most 10 ms.
- **Contractions without the apostrophe** (fork/contractions, found by the second held-out list). Only 14 were known,
  so the rest were "corrected" one edit away and the negation went: "baby hasnt moved" → "hasn moved", "havent" →
  haven, "shouldnt" → shouldn, "shouldve" → shoulder, "whos" → whose. All the common n't, 's, 're, 'll, 've and 'd
  forms are now put back before any other correction (`typos.APOSTROPHES`); real words stay ("were", "well", "ill",
  "its", "lets", "shell", "hell", "wed", "shed", "id"), and so does "hed" (typed for head on the lists). "im" becomes
  I'm unless a medicine word is beside it ("give im adrenaline", "iv or im"; IM in capitals stays). The search drops
  a pronoun with its ending ("i'm", "he's", "there's": `server.STOP`) as it drops the pronoun; the negations stay.
  A glued run with an apostrophe inside is split too ("he'snotbreathingwhatdoido" → "he's not breathing what do i
  do", which found no pages; "i'mchoking", "she'sbleedingalot"), from 6 letters and without the "corrected whole"
  margin; "he's", "grandma's", "o'clock" stay. A hyphenated word is split part by part, never corrected. A word with
  capitals inside ("ODing", "iPhone") is left as typed, and a few slang, brand and medical words joined the English
  words ("unalive", "fortnite", "sniffly", "redback", "rennie", "konked", "gouching", "fluey", "doms", "stooling":
  all from list 2, which is no longer blind for them). Measured against 19c2db2, in-process and read-only. Neither
  held-out list is blind any more. Urgent, body signs and pages withheld didn't change on any set. On list 2, 7 lines
  get their negation back and the glued line finds pages (0 → 8, the resuscitation guidelines first). The typo lines
  went from 18 fixed / 6 wrong to 19 / 5. Red+yellow lines whose first page looks like health: list 1 272 → 278
  keyword-only and 285 → 284 hybrid; list 2 214 → 213 and 227 → 229. Mixed line by line: "hes blue" now opens a
  statistics book, while "hes not breathing" opens the resuscitation guidelines instead of the CERT manual.
  In-sample, right first pages went 354 → 356 keyword-only and 436 → 438 hybrid, of 599. Hybrid top 3 went 524 → 522:
  "he swallowed pool water and now he's coughing" and its typo version.

  On 48 invented glued and gibberish questions (with 3l's unknown-word rule): 20 of 24 glued questions are split right
  (all 6 everyday ones, 14 of 18 emergencies; missed "mysonatebleach" → "my so nate bleach", "hescolapsednotbreathin"
  → "… breath in", and "snakebitmyleg" and "mybbyisntbreathing" stay whole). `urgent()` is now true for 17 of the 18
  emergencies (3 before), and the first page is right for 10 (keyword-only; 0 before) and 13 (hybrid; 1 before). The
  owner's question now finds the choking pages first, p 0.91 hybrid. The 11 long real words and names stay whole. On the
  362 test questions and #154's 32 with their typo versions nothing changed, keyword-only or hybrid (the words
  searched, the route, the first page, what the chat does), nor on the 52 conversations.
- **Conversations** (`assistant.turn_hits`). The newest message is classified without a model: noise ("jdjdk", "sorry
  wrong chat") → no search, and the chat shows buttons (a `suggest` event); a correction ("no no I mean…") → the
  correction words are dropped and pages already shown go last, none carried over; a danger sign the conversation
  didn't have yet → this message's own search first, none carried over; otherwise 3g's follow-up search, joined with
  the last message that wasn't noise.

| First result right | keyword only, before → after | hybrid, before → after |
|---|---|---|
| Red questions | 44% → 44% | 67% → 70% |
| All clean questions | 58% → 59% | 73% → 76% |
| Typo questions, useful pages in top 8 | 2.23 → 4.72 | 3.39 → 5.57 |
| Conversations (with cited replies) | 48% → 54% | 56% → 64% |

On conversations, hybrid: corrections 29% → 57%, new emergencies 0% → 80%, follow-ups 86% → 86%, but additions
68% → 47% and messages after noise 75% → 58%. 19 single questions got better and 2 worse (hybrid).

`app/tests/test_long_pages.py`, `test_typos.py` and `test_turn_hits.py` cover it.

### 3l. How sure the search is

Without a model, `engine/confidence.py` estimates the chance that the first page is right, from signals the search
already has: how many of the question's words (or synonyms) the first page and its title carry, how strong the keyword
match is for how rare the words are, whether the page is from a first-aid book; with meaning-based search also the best
cosine, how fast the cosines fall, how far the two searches agree, and how many different books the top 8 come from.
It is a logistic regression stored as plain numbers, one set for keyword-only search and one for hybrid.

- **How well:** on the 362 test questions of 3k, cross-validated by topic (a topic's clean and typo versions in the
  same fold), AUC 0.78 keyword-only and 0.74 hybrid, and calibrated: in each 25-point band the predicted and actual
  rates are within a few points.
- **What the chat does** with a question that may be urgent (below): below 0.60 it offers buttons; below 0.25, on a
  new question, it asks the person to say more instead of answering from bad pages. Keyword-only, buttons on 43% of the test questions and the request on 7%; 5 of
  216 right first pages get the request. Hybrid: buttons on 18%, the request under 1%. 14 of 362 keyword-only
  questions (21 hybrid) get no buttons although none of the first 3 pages is right.
- **A question that may be urgent always gets its pages,** with the buttons and the request. The danger signs alone
  caught 81 of the 218 red questions ("my son isn't breathing" slipped), so `confidence.urgent()` adds a wide list of
  urgent words, matched before and after typo correction: 218 of 218. A false match only means pages are shown.
- **Everyday questions** (not urgent by the same rule: no danger sign, no danger button, no urgent word) get buttons only
  below 0.30, and the same buttons drawn smaller (`'style': 'compact'` in the `suggest` event: a row of small chips).
  Below 0.25 they also get the request to say more, as before; that cut never sits above the everyday buttons cut
  (with `LASTBOOK_CONF_BUTTONS_EVERYDAY` under 0.25, the request moves down with it). Before this, an everyday question
  under 0.60 got the full-size emergency buttons. On the test set's 51 everyday questions, out of fold:

  | cut | keyword-only: buttons | first page right, buttons anyway | none of first 3 right, no buttons | hybrid: buttons |
  |---|---|---|---|---|
  | 0.15–0.25 | 0 | 0 | 7 (all) | 0 |
  | **0.30** | 2 (4%) | 0 | 6 | 0 |
  | 0.35–0.40 | 5 (10%) | 2 | 5 | 0 |
  | 0.60 (before) | 16 (31%) | 9 | 1 | 5 (10%) |

  0.30 is the lowest cut that catches anything: "how to build a root cellar" (first page from a winter survival
  handbook) and "tooth nocked out" (a trail notebook), neither with a right first page. 0.35 adds two right first pages.
  Hybrid never goes that low on an everyday question (lowest 0.46). 51 questions is a small sample: the wide urgent
  list takes most of the test set.
- **Words the library doesn't have.** The fitted model has no signal for "the question's words aren't real words" (one
  was tried while fitting and dropped: it was 0 on every test question), and a search for keyboard mash can look fine:
  keyword-only, "jdjdk" finds nothing and gets p 0.38, which is over the everyday cut, so it was answered; "qwertyuiop"
  got 0.94. Now, after typo correction and splitting, if the question has no content word (only search stop words, such
  as "help" or "how do i") or most of its content words are on fewer than 3 pages, p is capped under both unsure cuts
  (`unknown_words` in the estimate, with the fitted p as `p_fitted`), whatever the model says. The chat then asks for
  more words, with buttons, also on a first message, and still gives the pages if the question may be urgent. A
  question in another language and words with digits ("EU2200i") are left to the model. `LASTBOOK_CONF_UNKNOWN=0`
  turns the rule off. The coefficients were not refitted. All 7 keyboard-mash questions of 3k's glued set and 2 of its 3
  unknown words ("blorft" is corrected to "blot") now get the request, keyword-only and hybrid, where all were answered
  before; it never fires on the 426 test questions.
- **Noise as a first message.** Later in a conversation, noise ("ok", "sorry wrong chat") brings back the last sensible
  message's results with buttons. A first message has nothing to fall back on: a stock phrase or one with no letters
  now gets its own search, the buttons and the request to say more, as an unsure search does (before: answered from
  whatever its search found). Mash as a first message ("jdjdk") gets the same through the rule above. A message whose
  words are mash as typed but the library's words once split ("heschuokinghelkp") is not noise.
- **Body signs: the answer is never withheld.** "he has no puls what do i do" got p 0.22 and was not urgent ("puls" is on
  24 pages of the library, so the typo correction leaves it, and the urgent list has "pulse"): the chat gave only "help
  me help you", to someone with no pulse. "mybbyisntbreathing" (glued, could not be split) the same, with no pages at
  all. Now `confidence.body_signs` looks for a body sign in the question as typed and as searched: pulse or heartbeat,
  breathing, blue lips or skin, unconscious (unresponsive, collapsed, passed out, won't wake), choking, bleeding or
  blood, a seizure (convulsions, having a fit), chest pain, not moving (limp, floppy), cold and clammy (or wet). A word
  counts one slip away too, or two for a long word, with the first letter kept, but only a word the library has on fewer
  than 50 pages: "puls" is pulse, while "pulses", "bloom", "breeding" and "chose" are words of their own, and a one-slip
  match must be a plausible slip (a key next to it, a vowel, a letter dropped, added or swapped), so "chore" is not
  choke. Inside a glued run the library doesn't hold, a short list of stems is looked for ("breath", "isntbreath",
  "bleed", "chok", "pulse", …). A question with a body sign counts as urgent, is never noise, and when the search is
  very unsure the chat answers from its pages with the buttons instead of asking (before, an urgent one got the pages
  without an answer, `UNSURE_DANGER`). The search gets the body word too (`typos.body_fix`): "puls" → pulse, and the
  unsplittable glued run → its stem's words ("not breathing"), which finds the CPR pages instead of nothing.
  `LASTBOOK_BODY_SIGNS=0` turns it all off, `LASTBOOK_BODY_FIX=0` only the search's part.

  Measured on every triage set, keyword-only and hybrid, 9712522 against this (`.claude/drafts/triage/BODY_SIGNS.md`):
  107 of the 599 questions (cases, #154's with typos, #128's, #241's, the glued set, the 52 conversations' last
  messages) name a body sign. Those that got only "help me help you": 2 → 0 keyword-only ("no puls", the glued one), 1
  → 0 hybrid; those that got the pages without an answer: 9 → 0 keyword-only. No question that showed pages before
  shows fewer now, none urgent before is not now, and the only two newly urgent are those two red ones.
  "mybbyisntbreathing" now finds resuscitation pages first (0 → 8 useful keyword-only, 0 → 5 hybrid); "he has no
  puls" is searched as "pulse" (hybrid first right, 0 → 2 useful; keyword-only First Aid p. 7, as the clean question).
  No clean question's search words changed. Narrowing `urgent()` with this list was measured and not done: the
  everyday questions it catches are caught by fire, gas, baby, bleach and generator, not by body words, and dropping
  any of those loses red questions (fire alone 15, for 28 green ones relieved).
- **A held-out check, and what it changed.** All the numbers above were measured on questions written together with
  the code. A list of 690 new lines written by someone who never saw it (343 red, 104 yellow, 243 green, 128 of those
  counterexamples; `.claude/drafts/independent/`) found the gaps: urgent on 85% of red lines (218 of 218 in-sample),
  18 red lines keyword-only (4 hybrid) given only "help me help you" with no pages ("took 20 of her sleeping tablets",
  "he's out cold on the pavement", "911", "worst headache of my life"), 36 more given the pages without an answer, and
  urgent on 80% of the counterexamples. Three changes followed; **that list is no longer held out**, since they were
  made against it (a second, unseen list is the next check).
  - **The pages are never withheld.** The request to say more now always comes with the pages the search found, as
    pages to open ("Pages the library found"), and with the buttons, urgent or not (`UNSURE_PAGES` for an everyday
    question). Only a search that found nothing says so.
  - **An urgent question is answered.** A question that may be urgent whose search is very unsure is answered from its
    pages, with the buttons, as a body sign's is, instead of the pages without an answer (`UNSURE_DANGER`); not when
    its words aren't the library's (mash). Measured both ways: on the in-sample sets, of the 35 questions that move
    (23 red), the first page is right for only 4 but one of the first 3 is right for 23 (66%), and the model reads the
    first 4 whole and is told to say "Not found in the library" when they don't fit; on the held-out list 58 of the 83
    red lines in that band have a health page in their first 3. Pages without an answer leave a frightened person to
    read them alone, so the answer was chosen. `LASTBOOK_CONF_URGENT_ANSWER=0` brings back the pages only.
  - **A bare plea** as a first message ("911", "help", "hlep", "HELP ME", "emergency", "sos") gets the emergency
    buttons first, larger, under "What is happening?", a line saying to call the local emergency number if someone may
    die, and the pages (`assistant.plea`; `'style': 'urgent'` in the `suggest` event). Before, "911" (no letters) was
    noise and got the bare request.
  - **Everyday wordings** were added to the urgent words and the body signs: unconsciousness (slumped, out cold, won't
    answer or respond, hard to rouse, keeled over, dropped like a stone, face down, on the floor), bleeding without the
    word (pouring, gushing, soaking pads, a cut that won't stop), the chest and heart (an elephant on the chest, a tight
    chest, a heart racing, pounding or too slow), stroke (a crooked smile, can't lift an arm, slurring, can't feel one
    side, words coming out wrong, the worst or a thunderclap headache), overdose (tablets, a whole box or packet,
    medicine names, sleeping it off), seizures (fitting, eyes rolling, shaking that won't stop, foam at the mouth),
    snoring or gurgling in someone collapsed, CPR named (a body sign: what to do for no pulse), suicide in other words
    (killing myself, wants to die, saying goodbye), and a few yellow ones (can't pee, something in the eye, a broken
    nose). Written as general patterns, not the list's sentences.
  - **Everyday idioms** are cut out before the urgent words and the danger signs look (`confidence.NOT_URGENT`):
    "bleed the brakes", "blood orange", "a breath of fresh air", "stroke of luck", "drowning in emails", "collapsed
    into laughter", "my phone is dead", "the engine is choking", "doesn't fit", "CPR certification", "painting" (no
    longer "pain"). Only the phrase goes: "bad breath and now he can't breathe" is still urgent.
  - With 3k's English words, in numbers (keyword-only; hybrid is the same where it is a text check):

  | held-out list 1 | 4ea2d9f | now |
  |---|---|---|
  | urgent: red / yellow | 293/343 (85%) / 79/104 (76%) | 340/343 (99%) / 98/104 (94%) |
  | urgent: green / counterexamples / mild | 64% / 80% / 45% | 31% / 17% / 47% |
  | body sign found, lines with a covered sign (red) | 67% (65%) | 85% (84%) |
  | body sign on counterexamples | 34% | 7% |
  | red: bare "help me help you", pages withheld (keyword / hybrid) | 18 / 4 | 0 / 0 |
  | red: pages without an answer (keyword / hybrid) | 36 / 1 | 0 / 0 |
  | all lines: pages withheld (keyword / hybrid) | 37 / 5 | 0 / 0 |
  | typo lines (84) with the meaning word right | 45 fixed, 15 wrong word, 19 left | 71 fixed, 6 wrong, 2 left |
  | clean lines with an English word bent | 35 | 0 |

  The three red lines still not urgent: "911" (a plea, so it gets the buttons anyway), "myboyiscoking" (split into
  "cooking") and one in French. In-sample (all six sets, both modes), nothing urgent before stopped being urgent
  except green ones ("how to bleed the brakes", "the car battery is dead"), the first page changed for one question
  (better: "dad having a hart attack"), and the pages are now withheld for none (4 keyword-only, 10 hybrid before: glued mash).
  Right first pages: 354 → 354 keyword-only, 435 → 436 hybrid, of 599.
- **Inside a conversation** it only offers buttons: there the confidence predicts poorly (AUC 0.45–0.65), since the
  first page is often one the previous answer cited.
- **Tried and dropped:** buttons below 0.75 (68% of keyword-only questions, 116 false alarms against 70); predicting
  "one of the first 3 pages is right" instead of the first. Top-3 right is far more common (78% keyword-only, 90%
  hybrid), so that model is sure almost always and lets 2–4 times as many all-wrong searches through without buttons,
  and it ranks them no better.
- `/api/retrieve` returns `confidence` (the urgent cuts). Settings: `LASTBOOK_CONF=0`, `LASTBOOK_CONF_BUTTONS`,
  `LASTBOOK_CONF_UNSURE`, `LASTBOOK_CONF_BUTTONS_EVERYDAY`, `LASTBOOK_CONF_UNKNOWN=0`, `LASTBOOK_BODY_SIGNS=0`,
  `LASTBOOK_BODY_FIX=0`, `LASTBOOK_CONF_URGENT_ANSWER=0`.

`app/tests/test_confidence.py` covers it (`BodySigns` and the body-sign chat and turn tests too; the pages with every
request to say more, the urgent answer, the plea, the everyday wordings and idioms); `test_typos.BodyWords` the search's
part, `test_typos.EnglishWords` the English words and the slips, `test_what_ships` that the word list ships.

### 3m. A meaning-based second opinion on urgent questions

The urgent words of 3l miss urgent questions worded in a way they have no word for ("his throat is closing after
peanuts", "my son says voices are telling him to jump"). `engine/meaning_red.py` adds a check by meaning, from the
prototype in `.claude/drafts/meaning/` (its `RESULTS.md` has the method and how it was chosen; `LLAMACPP_SMOKE.md` and
`LLAMACPP_STATS.md` the move to the runner):

- **How:** the question, after `typos.correct` and with no query prefix, is embedded with bge-small-en-v1.5 (the model
  hybrid search uses, here a q8_0 GGUF of 37 MB) and compared with 31 centroids, one per category of 689 invented
  examples (`engine/data/meaning_red_examples.jsonl`: 20 red categories; yellow and 10 look-alike green ones). Score =
  closest red centroid minus closest non-red one; it fires above the "wide" threshold (0.0084, set on the examples only:
  10% of green examples out of fold; the "strict" one, 0.0317, is stored but not used).
- **Where the embedding happens: the runner, not the desktop.** An earlier version ran an int8 ONNX copy inside the
  desktop process with onnxruntime. That broke upstream's rule that the desktop loads no model and no onnxruntime
  (`test_bridge.WholeProcess.test_no_listening_socket_and_no_model`), needed onnxruntime and tokenizers in the Mac and
  Linux builds, and a changed test. This version keeps every one of those rules: the embedding is done by the app's own
  local-AI program, `lastbook-llm`, started a second time as `lastbook-llm --model bge-small-en-v1.5-q8_0.gguf --embed
  --cpu-only --threads 2` (`packaging/llm/lastbook_llm.cpp`: `--embed` loads an embedding model with [CLS] pooling and
  answers `{"op":"embed","id":1,"texts":[...],"max_tokens":320}` with `{"ev":"embedding","id":1,"vectors":[[...]],...}`,
  unit vectors; it refuses `gen`, and chat mode refuses `embed`; its ready line says `"embed":true`). The pipes are the
  same as the chat runner's: no socket, no port. The desktop imports neither onnxruntime nor tokenizers for this; it only
  does the two small matrix products (numpy, already a dependency) with the centroids. The runner uses the llama.cpp
  tag already shipped (b12032): only the runner program grew (+97 lines), the library's DLLs are the same sources.
- **Only adds:** `assistant.is_danger` is the words (danger signs, buttons, `confidence.urgent`) **or** the meaning
  check. It can make a question urgent, never take that away; an urgent question's pages are never held back, so a
  false flag costs little. `turn_hits` puts `info['meaning']` (`score`, `fired`, `state`, and what the words said) in
  the turn, and the `local AI confidence:` log line (`LASTBOOK_AI_DEBUG=1`) carries it.
- **The runner process:** `server.init` calls `meaning_red.start()`, which starts a thread and returns at once (0.2 ms).
  The thread checks the files' SHA-256, starts the runner (`llm_local.runner_path()`, tied to the app with the same job
  object on Windows; on a Mac or Linux it leaves when its input closes), waits for `ready` (it must say `"embed":true`:
  an older runner refuses `--embed` and ends, which counts as a failure), warms it with one question, and keeps it for
  the rest of the run: one long-lived process, one question per request (batching gains nothing: 5.3 ms a question at
  8, 32 or 128 to a request), one request at a time under a lock. It loads in 0.2 s and stays at 66 MB private memory,
  no video memory (`--cpu-only`: Vulkan is slower per question and stalls for seconds the first time a size is seen).
  It is asked from the thread of the question, with a 10 s limit. Until it is ready, or after any failure (runner
  missing, an old runner, the GGUF or centroids missing or changed, the process ended, an answer that does not come), the
  words alone decide, as before, and the log says once `meaning check: off, ...`. A runner that ended or stopped
  answering is closed and started again, at most 3 times in all (`MAX_RESTARTS`), then the words alone for the rest of
  the run. `atexit` stops it (`{"op":"quit"}`, then a kill after 3 s). It runs beside the chat runner (Gemma) without
  either noticing: the chat runner is unchanged in chat mode (`swa_check` and all).
- **Files:** `bge-small-en-v1.5-q8_0.gguf` and `centroids.npz` (31 x 384 float32 and the thresholds). They are not in
  git: `tools/meaning_red_model.py` makes them from the Hugging Face copy of the model (`DATA/derived/models/
  bge-small-en-v1.5-hf`) with the runner's own llama.cpp tag (`convert_hf_to_gguf.py --outtype q8_0`; pass `--llama-cpp`
  a checkout of tag b12032), then embeds the examples through the runner (with `LASTBOOK_DATA` set: they go through that
  library's `typos.correct`) to make the centroids, into `derived/models/meaning-red/` (ignored by git), prints their
  SHA-256 and, with `--write-manifest`, writes their sizes and SHA-256 into `engine/data/meaning_red_manifest.json`, the
  one list every copy is checked against. The GGUF and the centroids come out byte-identical to the prototype's
  (`LLAMACPP_STATS`), and the out-of-fold thresholds recomputed with `--cv` equal the fixed ones.
- **Where the app finds them:** `APP/derived/models/meaning-red/` (the source tree), `<runner folder>/meaning-red/` (a
  packaged app: the Windows, Mac and Linux builds copy `derived/models/meaning-red` in next to the runner, `llm/meaning-red`,
  when `packaging/meaning_red_files.py` finds it complete and matching the manifest, and stop if it is there but
  different; the Linux package scan lets through exactly that one GGUF), then `DATA/derived/models/meaning-red/`, where
  setup downloads them: after the person's own download of the local AI model, `engine/setup/api.py` fetches the files
  from the Hugging Face repo in the manifest through `engine/setup/download.py` (HTTPS to huggingface.co only,
  SHA-256 checked), unless the app already has them. A failure leaves the words alone; the model's install goes on.
  While the manifest has no `revision` (a commit id), nothing is downloaded at all. The manifest and the licence text
  (`engine/data/meaning_red_LICENSE.txt`: MIT, BAAI) ship in every build; `THIRD_PARTY_NOTICES.md` lists the model as a
  GGUF file used by the runner.
- **Upstream's rules are kept:** `test_bridge` is as upstream's (its WholeProcess test is byte-identical to origin/main's
  and passes: the desktop process has no model file open, no onnxruntime, no listening socket; the runner is a child
  process). The Mac and Linux builds do not gain onnxruntime or tokenizers (requirements, the Mac spec's excludes and
  both scans are as before; only the Linux scan allows that one GGUF by name), search stays keyword-only on the
  desktop, and the chat runner's behaviour is unchanged. `test_meaning_red.WholeProcess` checks, in a process of its own,
  that no socket listens, that none of onnxruntime, tokenizers, onnx or retrieval is imported, and that the runner is
  gone after the app exits.

Measured with this code (in-process, read-only, `LASTBOOK_DATA=D:\LastbookData-fork-test`, sections build refused; the
words are 9bd116e's). Urgent counts, red / yellow / green (the green lines are counterexamples and mild ones):

| | list 1 (343/104/243) | list 2 (249/111/246) | list 3 (199/78/254) |
|---|---|---|---|
| words only | 340 / 98 / 76 | 230 / 85 / 127 | 173 / 55 / 154 |
| meaning only | 297 / 56 / 60 | 210 / 53 / 62 | 162 / 35 / 75 |
| **words OR meaning (this branch)** | **341 / 100 / 104** | **243 / 93 / 147** | **188 / 62 / 173** |
| the int8 ONNX version, for reference | 341 / 101 / 106 | 245 / 93 / 147 | 186 / 65 / 171 |

Red caught only by the meaning: 1, 13 and 15. Out-of-fold on the examples (5 folds x 3): red recall 80.3% at 5% green
false flags and 89.5% at 10% (the int8 version: 81% and 90%). In-sample triage sets (273 red, 94 yellow, 148 green): words
OR meaning 272 / 79 / 67 against the words alone 272 / 75 / 63, and `is_danger` 273 red as before: no question urgent by the
words stops being urgent, on any list. The GGUF and the int8 model disagree on about 25 to 30 lines a list, both ways, all
near the threshold, so the centroids were refit on the GGUF's vectors (they are not the int8 ones).

Cost on this PC (Ryzen 7 5800X3D, 2 runner threads): a question takes 5 to 11 ms through the pipe (5.2 ms median on a quiet
machine, `LLAMACPP_STATS.md`; 9 ms median, 13 ms p95 and 29 ms max over the 2,342 lines measured later on a busier one, of
which 4 to 6 ms is the runner computing; the int8 ONNX version took 2.2 ms in process), `is_danger` 9.7 ms median with it
against 0.3 ms without; the runner adds 66 MB private (68 MB peak) as a second process and the desktop 2 MB; the server's
start is not slowed (`start()` returns in 0.2 ms; the runner is ready 0.2 s later on its thread). The check runs once per
message.

`LASTBOOK_MEANING_RED=0` turns it off. `app/tests/test_meaning_red.py` covers it (fires on clear urgent wordings,
quiet on clear everyday ones, only adds, falls back on a missing or changed file, a missing or old runner, a runner that
ends (started again, then given up) or stops answering, the switch, threads, a real runner killed and restarted, the
manifest and no download while unpublished, the runner's arguments, a process of its own that opens no socket, loads no
onnxruntime and leaves no runner behind); `test_what_ships` that every build and scan carries it and that the Mac and
Linux builds still have no onnxruntime.

### 3n. Encyclopedia articles in the first results, by their best section

Upstream 1.1.13 adds the top 3 encyclopedia hits (MDWiki, Appropedia, Wikibooks, Wikipedia when present) to Chat's first
results: the raw question goes to the encyclopedias' own search, and the first 2,000 characters of each article go to the
model. When 1.1.13 was merged, the fork's first search (`turn_hits`) won the conflict, and the articles were left out, while
upstream's SYSTEM prompt still says they are there. They are back now, but picked the way §3k picks long pages, because
the same problem shows up there and is worse (`.claude/drafts/encyclopedia/`, the 253 clean test questions over the
three installed files):

- The median article is 28,000 characters; 723 of 752 are over 5,000 and 136 over 100,000. Whole books stored as one
  article came first: "Mirad Grammar/print version" (1.35 MB) for "my toddler drank bleach", "US History/Print version"
  for "my eyes sting from wildfire smoke", "Richard Nixon" for "he is pale cold and sweaty after the accident".
- The words a useful answer needs were in the first 2,000 characters for 259 of the 622 articles that held them.

`engine/wiki_pick.py`: the question's content words only go to the encyclopedias' search ("my" and "has" matched every
book). Print and printable versions are skipped, since each chapter is its own article too, and so is anything over
800 KB. Each candidate (6 per file) is cut into ~5,000-character sections (`sections.cut`). An article scores by the share
of the question's words in its best section (plural and past-tense endings dropped, so "burns" finds "burned"), plus a
little for words in its title; ties keep the encyclopedia's order. The excerpt is the part of that section where the
words are. The words are the ones `turn_hits` searched with (a follow-up's joined words, the earlier message's after
noise), with typos fixed (`assistant.wiki_q`). Any failure falls back to upstream's way; `LASTBOOK_WIKI_PICK=0` turns it off.

| 253 clean questions | Upstream's way | Best section |
|---|---|---|
| First article useful (holds the needed words) | 92 (36%) | **146 (58%)** |
| Any of the 3 useful | 163 | **197** |
| Red / yellow / green, first useful | 34 / 25 / 33 | 61 / 40 / 45 |
| No article at all | 1 | 5 |
| Time, median / p90 | 92 / 512 ms | 578 / 962 ms |

The excerpt is chosen for the question's words, so "holds the needed words" favours it a little where those overlap.
The encyclopedias still hold little first aid, so wrong first articles remain ("Doom/Complete list of enemies" for a
chainsaw cut). Typo questions were measured raw (4 → 7 useful of 109); Chat fixes typos first.
**Urgent first, then side by side, then shown apart** (`assistant.WikiJob`, `assistant.chat`, `web/chat.js`):

- The newest message is labelled before anything is searched (`is_danger`, 11 ms). Urgent: no encyclopedia search at
  all, so the manuals have the first results to themselves. All 131 red test questions skip it. The label is the broad
  one that never holds pages back, so it also drops the articles for 48 of 58 yellow and 38 of 64 green questions ("how to
  use a fire extinguisher"). So the chat then shows **"Not an emergency? Add the encyclopedias"**, which asks again with
  `wiki: true`: the articles come back, and nothing else about the urgent label changes (manual first, pages never
  held back, emergency buttons). The precise label (danger signs or the meaning check) would drop them for only 9 green
  questions, but it misses 14 red ones, including "splashed bleach in my eye" and "downed power line in the yard".
- Otherwise the encyclopedia search runs on a thread of its own while `turn_hits` searches the library, from its own
  pool of candidates, with its own limit (3 beside the library's 8): the encyclopedias' size cannot take the library's
  places. Median 806 ms one after the other → 433 ms side by side (library 115 ms, encyclopedias 383 ms).
- The two searches stay apart, to the model and on screen. The model gets the library's results as before (the triage
  order, untouched) and, in a second message, the articles, marked as community-written background from a separate
  search. The chat shows the library's sources, then "From the encyclopedias" with the articles, whether the answer
  used them or not (the cited ones first). A merge was tried first: a plain comparison of word-share scores put articles
  2nd to 4th, above useful manual pages, for 76 of 108 articles (a short web excerpt holds fewer of the question's words
  than a 2,000-character article only because it is shorter), and a strict rule (an article above a page only when it
  holds every word of the question and the page fewer than half) kept the library's order but pushed most articles to
  the end. Apart, neither search's order changes and no article is held back for being short.
- Ranking the candidates by meaning (bge-small through the `--embed` runner) was timed and dropped for now: 60–200 ms per
  2,000-character excerpt on 2 threads, the runner taking one text at a time, so 0.4–2.4 s a question.

**Dev toggle: a vector index of the encyclopedias** (`LASTBOOK_WIKI_VECTORS=1`, off by default; `engine/wiki_vectors.py`).
A prototype embedded every ~5,000-character section of MDWiki, Appropedia and Wikibooks with bge-small-en-v1.5 on the GPU,
once (`.claude/drafts/encyclopedia/vectors/` in the wiki-vectors worktree): 185,702 articles, 429,964 sections, 11.6 min
on an RTX 3080 Ti (about 6 h on a CPU), 330 MB as f16, files `derived/index/vec-<zim>-<size>-<mtime_ns>.{f16.npy,rows.json,meta.json}`
(the prototype's `rows.npz` needs pickle; `tools/wiki_vectors_rows.py` rewrites it as JSON). With the toggle, `first_wiki`
asks it first: the question (with bge's search instruction, as `retrieval.QUERY_PREFIX`) is embedded by the meaning check's
runner, each file's matrix is scanned, the 3 articles with the closest section win, and the excerpt is that section's best
part. No index, a stale one (size or time changed), the runner not ready, or any error: `wiki_pick` as before.

| Through `first_wiki`, 253 questions | Keyword (`wiki_pick`) | Vectors |
|---|---|---|
| Everyday (122): first useful / any of 3 | 85 / 108 | **98 / 114** |
| Urgent (131): first useful / any of 3 | 61 / 89 | **92 / 111** |
| Time median / p90 | 583 / 885 ms | **76 / 170 ms** (urgent 140 / 331) |
| First load / memory | – | 1.4 s once / **+690 MB** (f32) |

The time includes reading the 3 articles for their excerpts. The scorer only checks that topic words appear, and spot checks
show weak articles it cannot see: "he is not breathing" got a lateral-thinking puzzle's solution and (before the search
instruction) a Latin primer from Wikibooks, beside a good "Medical Emergencies" chapter. A likely cause: the model reads
320 tokens (about 1,300 characters), so each vector stands for the first quarter of its 5,000-character section. Smaller
sections mean a bigger index (about 4 times the rows); with the two searches shown apart this was not pursued.

**Setting (chat sidebar): "Encyclopedias on urgent questions too", on by default** (`sg.wikiUrgent` in the browser's
storage; the chat then sends `wiki: true` with every question). With a vector index of the encyclopedias a search takes
~36 ms (Open), so speed is no reason to skip them; the articles are shown apart from the manuals. Off: urgent
questions use the manuals alone, with the "Not an emergency?" button. A client that sends no `wiki` (the server's own
default) still skips them. With today's keyword picker the urgent articles are often weak ("he is not breathing":
"Philips Breath Counter", "Conscious breathing"). `LASTBOOK_WIKI_URGENT=1` keeps them server-side for every client. `app/tests/test_wiki_pick.py` and
`test_confidence.ChatConfidence` (`test_encyclopedia_articles_come_apart_from_the_library`)
cover it.

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
| `LASTBOOK_AI_ENGLISH_SEARCH=0` | Search a non-English question as typed, without the model's English search words (3i) |
| `LASTBOOK_AI_TABLES=0` | Give the model pages with every run of spaces squashed, tables line by line, as upstream does (3j) |
| `LASTBOOK_PHRASE_INJURY=0` | Use the fire and water-safe phrases even when the question names an injury (3h) |
| `LASTBOOK_PHRASE_RETRY=1` | When every word finds too little, search again without a phrase's helper words before relaxing (3h; off: it lost "no matches and no gas") |
| `LASTBOOK_TYPO_FIX=0` | Search questions as typed, without correcting misspelled words (3k) |
| `LASTBOOK_TYPO_SPLIT=0` | Don't split words typed with no spaces ("kitchenonfire"); the rest of the correction stays on (3k) |
| `LASTBOOK_TYPO_ENGLISH=0` | Correct ordinary English words into library words again ("keeled" → peeled), without the real-word slips ("he cant breed") or the cutting of repeated letters (3k) |
| `LASTBOOK_CONF=0` | No confidence estimate: no buttons or request to say more from it (3l). `LASTBOOK_CONF_BUTTONS` / `LASTBOOK_CONF_UNSURE` move the cuts (0.60 / 0.25); `LASTBOOK_CONF_BUTTONS_EVERYDAY` the everyday questions' buttons cut (0.30) |
| `LASTBOOK_CONF_UNKNOWN=0` | Trust the confidence model even when the question's words aren't the library's (3l) |
| `LASTBOOK_CONF_URGENT_ANSWER=0` | A very unsure search for a question that may be urgent gets the pages and the request to say more, without an answer, as before (3l). A body sign is still answered |
| `LASTBOOK_BODY_SIGNS=0` | Don't look for body signs ("no puls", "mybbyisntbreathing"): a very unsure search with one may again get only the request to say more (3l). Turns `LASTBOOK_BODY_FIX` off too |
| `LASTBOOK_BODY_FIX=0` | Search a body word's slip ("puls") or a glued run with one as typed; the body signs still count (3l) |
| `LASTBOOK_MEANING_RED=0` | No meaning check: the urgent words alone decide whether a question may be urgent (3m) |
| `LASTBOOK_AI_DEBUG=1` | Log each round's raw output (thinking and markup included) and the runner's token counts, as `local AI raw:` and `local AI done:`, and each question's English search words as `local AI english search:` |

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
window, history citations rekeyed, answer citations repaired, follow-up hits and carried-over pages, memory estimate,
English search words for other languages, tables read by row, as printed and down columns, page caps and the
`LASTBOOK_AI_TABLES` switch). `app/tests/test_chat_steps.py` has `SpanishAnswers` (3i). The
model-level stress test is `tools/fork_chat_test.py` (3g), which needs the model and a test server.
`app/tests/test_bridge.py` has `ForkSearchWords` (3h). `tools/fork_search_check.py` compares the first search on 20
everyday prompts between two servers (3h); it needs no model. `tools/fork_table_test.py` asks 14 table questions against
a test server and checks the amount (3j); it needs the model.

## Open

- **Encyclopedias (3n):** shown apart from the library, by the keyword picker. The vector index stays a dev toggle and is
  not pursued (690 MB of memory for 3 files, growing with every pack, a GPU build per file). The encyclopedia group
  under the answer has been seen in the window once ("how do i purify water"); real answers still need reading by a person.
- **Meaning check (3m):** the Hugging Face repo is not uploaded (the manifest's `revision` is empty, so setup downloads
  nothing yet; upload the two files of `derived/models/meaning-red`, put the commit id in the manifest). The runner's
  `--embed` mode is built and run on this Windows machine only: the Mac and Linux runner builds (same
  `lastbook_llm.cpp`, no script change expected) are untested, and so are the three packaged builds with the files
  bundled in `llm/meaning-red` and the Linux scan's allowance for the GGUF. The check adds one runner process of 66 MB
  beside the chat one. The threshold was set on the examples only; list 2's and 3's false flags (children's and old people's
  everyday questions, idioms the examples lack) show where the examples are thin, and adding examples for them now would be
  tuning on the test lists, so a fresh list is needed before the numbers are trusted further. English only (a question's
  English search words, 3i, are not checked). In hybrid mode the loaded fp32 `Embedder` is not reused (the runner's
  `--embed` could serve it too: same model, same 320-token limit, but that is not done).
- Thinning a real pack's map (1) and the setup screens with no state picker have only been tested by the automated tests,
  not by hand.
- The runner fix (3d) is built and tested on this machine only. A release of the fork would ship it from
  `build_llm_windows.sh` (and the Mac and Linux scripts, not yet rebuilt). It's also a candidate pull request upstream.
- 3g was measured on one topic (stored water), 2 conversations per arm. Other topics, video citations (carry-over handles
  PDF pages only), and the published 26B with these changes (they're off for it) haven't been measured.
- **Search in the desktop app is keyword-only** (upstream's design: `test_bridge` checks no embedding model is loaded in the
  desktop process; the meaning check's one is in the runner's process, 3m). Its
  vocabulary gaps (3h) are where it fails. The fork adds two phrases; more gaps surely exist. "he has no pulse" got a thin
  answer that points to a "No Heartbeat" section without the steps, the same before and after 3h.
- "we have no fuel to boil water, how else can i make it safe" still finds nothing useful in the first search (0 of 8);
  the model searches again and answers well (bleach, cited).
- The follow-up search and carry-over add a little prompt (up to 3 full pages). On a slower computer that's slower reading.
- Thinking makes answers slower than thinking off. On a slower computer, `LASTBOOK_AI_THINK=0` trades citation reliability
  in follow-ups for speed.
- Showing the hidden thinking in a collapsible section of the answer (as Chat's "How it searched" does) was suggested; not
  built.
- **Tables (3j).** Tables laid across are still the weakest: 1 of 6 epinephrine answers also gave the neighbouring
  column's 3 mL. About 560 tables can only be shown as printed; a small model may still misread
  columns there. Tables without a recognised unit (bare numbers, "kcal" rows without one), scanned (OCR) pages and
  tables split across pages aren't handled. The rebuilt tables were checked by eye on a sample of health documents, not
  all 226. 3j was measured on E4B only, 3 runs of 14 questions, and only for the questions' first answer. A candidate
  pull request upstream (the squash is upstream's): reported as upstream issue #148, and sent as PR #178
  (branch `table-rows`, without the excerpt rows and the prompt line). From its review: a label wholly above its amount
  was paired one row off and called sure; such tables are now kept as printed (19 of 226 sure tables, each one flawed).
  Rotated tables: `pdftotext -layout` turns a rotated page upright; a rotated table on a page of upright text comes out
  as a "staircase" (amounts in one block, labels in another) that isn't rebuilt, but the library has only 2 with
  amounts, neither a dose. **Tables that are pictures are a separate problem**: they have no text, so neither this nor
  the local model (text only, no view_page) can read them. 3,474 PDF pages have no text at all and 108 documents are
  almost all scanned (none in health); pictures of tables on pages that do have text haven't been counted. Options:
  OCR when a pack is built, or page images for a local model that accepts them (not checked for E4B or the runner).
- 3i was measured once per arm on 8 questions. Portuguese and French are detected but not measured. The UI itself is
  still English (upstream issue #54).
- **Triage search (3k).** The sections file is built in the background when the server starts (about 4 s); only a test
  copy of the library has been through it. The conversation buttons and the reader opening a section haven't been seen in the window. Additions and
  messages after noise are weaker than 3g alone. 8 red questions still get no useful page (a severed finger, someone
  trapped under a wall, a mudslide). The iPad port has no typo correction. `packaging/linux/build_app_linux.sh` now
  copies `page_tables.py`, `sections.py` and `typos.py` (the first was missing since 3j); the Linux build hasn't been
  run. The classifier and the test set were written together, so its scores are
  optimistic. The confidence buttons (3l), their smaller everyday style and the request to say more haven't been seen in the
  window; everyday questions get the emergency set ("Not breathing", "Heavy bleeding" …), only smaller and only below
  0.30, and the wide urgent-word list
  shows some everyday questions' pages "in case this is urgent".
- **Held-out fixes (3k, 3l).** The first held-out list was used to make them, so its numbers are now in-sample; the
  second list is the real check. `engine/english_words.LICENSE.txt` gives SCOWL's notices from memory: replace them
  with the verbatim README of Chromium's hunspell en_US before a release. The plea buttons and the "Pages the library
  found" heading haven't been seen in the window. The wider urgent words make more everyday questions urgent where
  they name a symptom (mild lines 45% → 47%); the cost is buttons and an answer, never pages withheld.
- **Maps outside the US.** Every detailed layer is built from US data (see [MAPS.md](MAPS.md)). A street map for another
  country from an OpenStreetMap extract, using `tools/build_map.py`, would be a separate piece of work.
