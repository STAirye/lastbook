# Lastbook: custom lightweight Gemma 4, no US maps (fork)

> **This is an unofficial, unsigned fork** of [Immortal-Protocols/lastbook](https://github.com/Immortal-Protocols/lastbook).
> It has no builds or installers of its own: you run it from source. The releases, lastbook.org and its contact address
> belong to upstream Lastbook. Please don't send upstream reports about this fork.

## What this fork changes

| | Upstream Lastbook | This fork |
|---|---|---|
| US state map step in setup | Required | **Gone.** No state picker; no state map or address-search download |
| Detailed map inside a pack (Medium: California, All: whole US) | Kept | Kept by default. **Optional:** remove it after unpacking and keep only the world base map |
| Local AI model | Only the published Gemma 4 26B A4B file (exact SHA-256) | That file, or **your own Gemma 4 GGUF** (E2B, E4B, any quant), used from where it is |
| Chat and search | As released | Tuned so a small Gemma 4 answers well: hidden thinking, follow-up sources, tables read by row, everyday wording, typos, questions in Spanish, how sure the search is |

Everything else (library, guides, offline rules, the no-port bridge) is upstream as of Lastbook 1.1.12 (commit `4fd221e`).
Design notes, what is and isn't checked, and how to switch back: [docs/FORK.md](docs/FORK.md).

## Run this fork

1. Python 3.11 or later (the Windows build is pinned to 3.14), and the packages for your platform:
   ```bash
   python -m pip install -r packaging/requirements_app.txt      # Windows; packaging/requirements_macos.txt on a Mac
   ```
2. **The local AI runner** (`lastbook-llm`). This fork doesn't change it, so the one from an upstream release works.
   Copy the release's runner folder (on Windows `%LOCALAPPDATA%\Programs\Lastbook\_internal\llm\`) to
   `derived/llm/bin-win/` (`bin-mac/` or `bin-linux/` elsewhere). You can also build it with `packaging/llm/build_llm_*.sh`.
   Without it, Lastbook still works, but Chat only finds pages and doesn't write answers.
   **Windows also needs the WebView2 SDK DLLs** for its window. Copy `Microsoft.Web.WebView2.Core.dll`,
   `Microsoft.Web.WebView2.WinForms.dll` and `WebView2Loader.dll` from the release's `_internal\webview2\` to `app\webview2\`.
   Without them you get "Lastbook could not load the files it needs to show its window". git ignores both folders.
3. **A library** (data folder). Use one you already have, or let setup download one on first run.
4. **Your Gemma 4 GGUF** (optional). Download any Gemma 4 GGUF, for example a Q4_K_M quant of E4B or E2B from Hugging
   Face. An SSD makes it load faster.
5. Start it:
   ```bash
   python app/main.py --data /path/to/LastbookData
   ```
   Then pick the model in **Library and local AI → Use your own Gemma 4 file**, or set
   `LASTBOOK_MODEL_FILE=/path/to/model.gguf` before starting. Chat measures whether it fits, then uses it.

Tests: the command in [CONTRIBUTING.md](CONTRIBUTING.md). The fork's own tests (`ForkNoMaps`, `ForkCustomModel` and
`ForkLocalAI` in `app/tests/test_setup.py`, and others) are listed under Tests in [docs/FORK.md](docs/FORK.md#tests).
On Windows, run the test files one by one; `test_battery` and `test_run_source_linux` only pass on Linux.

## About Lastbook

Lastbook is an offline survival library for Mac, Windows and Linux: manuals, videos, encyclopedias, an offline map and
short practical guides on one computer, with a Chat that answers from the library and cites its pages. For everything
not specific to this fork (installers, Linux packages, privacy and network use, building the apps, packs, what's where in
the repository), see the [upstream README](https://github.com/Immortal-Protocols/lastbook/blob/main/README.md). Its
setup contract is in [docs/SETUP-API.md](docs/SETUP-API.md).

## Licence

Lastbook's original code and documentation use the [MIT License](LICENSE); this fork keeps it. Third-party software,
models, media and library content keep their own licenses, listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
and in each library pack.
