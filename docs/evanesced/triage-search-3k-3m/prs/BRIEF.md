# Staging the triage-based search engine as upstream PRs: shared brief

Source of the code: the fork's branch `fork/lightweight-gemma-no-us-maps` in `D:\git\lastbook` (has upstream 1.1.14
merged; `origin` = Immortal-Protocols/lastbook, `fork` = STAirye/lastbook). Target: upstream `origin/main`.
The proposal text is `.claude/drafts/upstream-search-summary.md`; formulas and how numbers were measured:
`.claude/drafts/upstream-search-methods.md`; the fork's full record: `docs/FORK.md` (§3k–3n).

## The stack (each branch starts from the previous one's tip; PR N's diff = only its module)

| # | Branch | Contents | Starts from |
|---|---|---|---|
| 1 | `triage/1-search-eval` | Library-search test set and scorer (no app code): question sets, the three independent lists (+ list 4), scorer, recorded baseline on main; `docs/TRIAGE-SEARCH.md` (the methods doc, rewritten for the repo) | `origin/main` |
| 2 | `triage/2-sections` | Long saved pages cut into ~5,000-char sections in a separate index file; search scores sections; the reader opens the section | 1 |
| 3 | `triage/3-typos` | `engine/typos.py` + `english_words.txt.gz` + licence + `tools/english_words.py`: typo correction against library words, English guard, contractions, glued words. The body-sign parts that need `engine/confidence` wait for PR 5 (guard them so PR 3 runs alone) | 2 |
| 4 | `triage/4-encyclopedias` | `engine/wiki_pick.py`: encyclopedia articles by best section, searched beside the library and shown apart (chat.js group). No urgent skip yet (needs PR 7's `is_danger`); no vector index (`wiki_vectors.py` is fork-only, not proposed) | 3 |
| 5 | `triage/5-confidence` | `engine/confidence.py`: confidence estimate, buttons, never withhold pages, "help me help you", body signs (and typos' body-fix hooks) | 4 |
| 6 | `triage/6-runner-embed` | `packaging/llm/lastbook_llm.cpp` `--embed` mode (C++ only), aligned with upstream PR #168's embed op where possible | 5 |
| 7 | `triage/7-urgency` | Urgency on one source: `urgent` phrases for guide choices in `content/topics/*.json` (`.claude/drafts/urgent-mapping/proposed_urgent.json`), Python reading them, `assistant.is_danger`, `engine/meaning_red.py` (meaning check in the runner) + its manifest, the encyclopedia urgent skip and its setting; the injury guard on everyday phrases (`confidence.INJURY`/`injury()`, `server.py` `phrase_injury_on`, `LASTBOOK_PHRASE_INJURY`), left out of PR 5 | 6 |
| 8 | `triage/8-conversation` | `assistant.turn_hits` routes (noise / correction / new danger / follow-up) for the local AI chat | 7 |

Worktrees: `git -C D:\git\lastbook worktree add D:\git\lastbook-pr\triage-<N> -b <branch> <start>`.

## Rules for every PR

- **Only this PR's module.** Port from the fork the files and the hunks that belong to it; nothing from later PRs.
  Where code needs a later module, guard it or leave it out and say so in the PR text.
- **Strip fork-only parts:** the person's own Gemma file (`custom` model paths, rekey/repair citations, thinking-related
  changes in `llm_local.py`/`assistant.py`), no-US-maps changes, `docs/FORK.md`, `docs/evanesced/`, `CLAUDE.md`,
  `wiki_vectors.py`. Rewrite `# fork:` comments as plain comments (no "fork").
- **Upstream style** (CONTRIBUTING.md): small focused change, plain-English comments, regression tests, bump
  `web/index.html` / `web/sw.js` versions if web files change.
- **Tests:** port this module's tests from the fork; run upstream's test files that touch what you changed, one file at
  a time (`python -B -m unittest app.tests.<file>`; on Windows `test_battery` and `test_run_source_linux` fail before
  and after: say so). Everything else must pass.
- **Text files UTF-8:** `encoding='utf-8'` on every open/read_text/write_text; don't rely on PYTHONUTF8.
- **Edit with exact replacements, not sed, for anything with backslashes.**
- **Commit** on the branch, each commit message ending with the line
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. **Do not push. Do not open PRs. Post nothing.**
- **PR description draft:** write `D:\git\lastbook\.claude\drafts\prs\<N>-<name>.md`: title line, then What changes,
  Why (link the proposal issue as `#<issue>` placeholder and #154), How it was tested (numbers from the summary/methods
  doc for this module, and what you ran), What it doesn't do, and "Part N of 8 of the triage-based search engine;
  builds on #<previous PR> (placeholder)". End with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
  Plain English, short sentences. No personal data (no real names, emails, home paths; the author is STAirye).
- **Report back briefly:** branch tip, files changed (+/- lines), tests run and results, anything left out or guarded
  and why, anything you weren't sure about.
