# Fork: custom lightweight Gemma 4, no US maps

This is an unofficial fork of Lastbook. It changes two things and leaves the rest (the library, guides, search, the
no-network rules, the bridge) as upstream has them. It is not signed and is not published on lastbook.org.

| | Upstream | This fork |
|---|---|---|
| State map step in setup | Required: pick a US state, which downloads its map and address search | Gone. No state picker, no state map or address download |
| The map that comes inside a pack (Medium: California, All: the whole US) | Kept | Kept by default. You can choose to remove it and keep only the world base map |
| Local AI model | Only the published Gemma 4 26B A4B file (exact name, size and SHA-256) | That file, or **your own Gemma 4 GGUF** (for example E2B or E4B), used from where it is |

## 1. No US maps

Two switches, both `False` in this fork:

- `MAPS` in `web/setup.js` hides the state picker in setup and the "Choose state" row in Library and local AI.
- `MAPS` in `engine/setup/api.py` stops setup adding a state's address index on its own. A map or address zip you pick
  yourself with "Choose a library zip or AI model file" still installs.

Set both to `True` to get the upstream behaviour back. With `MAPS = True` the upstream tests run as before
(`AddressIndexes` in `app/tests/test_setup.py` patches it on).

### Removing the map a pack brings (optional)

Medium's zip has California's detailed map built in, and All's has the whole US. You download it either way, because it is
part of the pack's checked zip. Setup's choose screen then shows a checkbox, unticked by default:
**Remove the bundled … map after unpacking**. Library and local AI has the same option as **Remove it** on the map row,
for a library that is already installed.

You can't just delete those files. The world base map is stored in the same SQLite files (`national`, `water`,
`terrain`, `places`), and Check and repair would see the files as damaged and download the whole pack again. So the fork
rebuilds the base map from them instead:

- `install.thin_to_base(src, dest)` (in `engine/setup/install.py`) follows the same rules as `base_set()` in
  `packaging/build_packs.py`: roads at zoom 8 and below, water at zoom 9 and below, relief to zoom 7, places not from
  OpenStreetMap, an empty street map, and no buildings, crops or atlas. A state set is the base set plus the rows inside
  the state's box, so this gives the base set back. The source files are only read.
- The result gets a `map-set.json` named `base`. Check and repair then checks the map files against it instead of
  `pack-manifest.tsv`, as it already does for state maps.
- During a pack install it runs in the staged library before the switch, as a job item `kind: "thin"`. In Library and
  local AI it is staged the same way a state map is and switched in when Lastbook restarts. If the result doesn't open, the
  old map is put back.
- It needs about 1.5 GB free while it runs. It saves about 3 GB on Medium, and much more on All.

## 2. Your own Gemma 4 GGUF

Pick the file with **Choose a library zip or AI model file** on the setup screen, or **Use your own Gemma 4 file** in
Library and local AI. You can also set `LASTBOOK_MODEL_FILE=/path/to/model.gguf`, which overrides both.

- The file is used from where it is and is not copied. Any folder works. An SSD loads it faster, so the same disk as
  `LastbookData` (or `LastbookData/models/`) is a good place.
- It must be a **Gemma 4** model (E2B, E4B, 26B A4B, 31B, any quantization), because Lastbook builds Gemma 4's own prompt
  format (`llm_local.py`). Other model families will load but answer badly or not at all.
- What is checked: the file exists, ends in `.gguf` and starts with the GGUF signature. There is no published SHA-256
  for your own file, so its contents are not checked. Get it from a source you trust.
- **Thinking off, the file's own way.** Lastbook asks Gemma 4 to answer without thinking. The published 26B A4B gets an
  empty thought block after `<|turn>model\n`, as upstream tested. A file of your own instead gets whatever its built-in
  chat template (`tokenizer.chat_template` in the GGUF) puts there. For E2B and E4B that's `<|turn>model\n` alone. With the
  empty thought block, E4B writes its reasoning out as plain text ("Here's a thinking process…") and Chat shows it
  (`llm_local.answer_start`). The log says which one is used: `local AI: your own model file; its answers start with …`.
- llama.cpp still measures whether it fits (`lastbook-llm --measure`), and the memory estimate uses your file's real
  size (`llm_local.judge(fit, model_bytes)`).
- Where it is saved: `custom_model` in `LastbookData/derived/llm/state.json`. A file chosen during first-run setup waits
  in the app's `setup.json` until the new library opens (`api.opened()`).
- While your own file is chosen, setup never offers the published model, and Check and repair never downloads it.
  **Use the published model** switches back.
- The runner is unchanged: llama.cpp b12032, the build the project's small-model evaluation used. No rebuild is needed.

## Tests

Run the suite from [CONTRIBUTING.md](../CONTRIBUTING.md). The fork's own cases are in `app/tests/test_setup.py`:
`ForkNoMaps`, `ForkCustomModel` and `ForkLocalAI`.

## Not in this fork

- **Maps outside the US.** Every detailed layer is built from US data (see [MAPS.md](MAPS.md)). A street map for
  another country from an OpenStreetMap extract, using `tools/build_map.py`, would be a separate piece of work.
