# Working on this fork

This is an unofficial fork of upstream Lastbook (`origin` = Immortal-Protocols/lastbook, `fork` = STAirye/lastbook,
branch `fork/lightweight-gemma-no-us-maps`). Read [docs/FORK.md](docs/FORK.md) first: it records what the fork changes,
why, what was measured and what is open. Upstream's rules in [CONTRIBUTING.md](CONTRIBUTING.md) apply here too.

- **Merging upstream:** when a conflict touches search (`server.py`, `retrieval.py`, `assistant.py`, `engine/`), the
  fork's search engine wins. Carry upstream's fix into it where it is a real fix, and record that in FORK.md.
- **Text the project keeps as UTF-8 is read and written as UTF-8.** On Windows, Python uses the system's locale
  encoding for text unless told otherwise (often cp1252), and code that works on a Mac or Linux stops there with
  `UnicodeDecodeError: 'charmap' codec ...`.
  - For the project's own text files (Python, `web/`, `content/`, JSON, Markdown), pass `encoding='utf-8'` to `open()`,
    `Path.read_text()` and `Path.write_text()`. Binary reads (`'rb'`, `read_bytes()`) take no encoding.
  - For a subprocess known to print UTF-8, such as Node in the tests, pass `encoding='utf-8'` with `text=True`. Other
    programs may use another encoding: check what yours prints first.
  - Don't rely on `PYTHONUTF8=1` or `python -X utf8`: other computers don't have them.
  - Suspect this first on any `UnicodeDecodeError` or `'charmap'` error. To check a fix, run the test with
    `PYTHONUTF8=0`.
- **Working scripts are archived when their work is done.** Repro scripts, measuring harnesses and notes live in the
  untracked `.claude/drafts/` (or a session's scratchpad) while the work is open. When the branch, worktree or session
  that made them is finished, copy them as they were into `docs/evanesced/<batch>/` and write the batch's section in
  [docs/evanesced/README.md](docs/evanesced/README.md), which has the rules (no binaries or models, personal paths
  replaced, never deleted). Pending batches are listed at the end of `.claude/drafts/TODO.md`.
- **Tests on Windows:** run the test files one at a time (`python -B -m unittest app.tests.<file>`). Run all at
  once, some files change shared state and others then fail. `test_battery` and `test_run_source_linux` only pass on Linux.
