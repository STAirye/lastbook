Search long saved web pages in sections (triage search, part 2 of 8)

## What changes

About 350 saved web pages in the library are whole books (mostly Project Gutenberg), each stored as one page of up
to millions of characters. A page that long holds nearly every word, so it matches almost any question.
*Modern Machine-Shop Practice* came in the top 8 for 25 of the 362 triage questions keyword-only.

- New `engine/sections.py`. Every saved web page over 20,000 characters (kind `html`, one row in the index) is cut
  into sections of about 5,000 characters, after a sentence where it can. Sections are numbered 1..n.
- The sections live in a file of their own: `derived/index/sections-<signature>.sqlite`. The pack's `search.sqlite`
  has a checksum in the pack manifest, so it is never written. The signature is the size and modification time of
  `search.sqlite`; when the library index changes, a new file is built and the old one removed.
- The file is built in a background thread when the server starts (`server.init`): 351 pages, 7,623 sections, about
  5 seconds on the test data. A search before it is ready waits for it.
- If the file cannot be built or read (a read-only data folder, say), search uses whole pages, exactly as before.
- Keyword search (`server.find`, `assistant._fts`) runs the same query on the library index, minus the long pages,
  and on the sections file, and merges the two by bm25. A section's `page` is its number, so each section is an
  ordinary result.
- Hybrid search keeps a long page's section number, so the sections of one book rank on their own. Short web pages
  are still cited without a page.
- The meaning index cuts new long pages by section. Passages embedded before this change are relabelled once with
  the section they start in, without re-embedding (`retrieval.Index.relabel_sections`, table `section_labels`).
- The reader: `/api/doc/<id>` says how many sections a long page has, and `/api/page/<id>/<n>` returns section n.
  A search result for a section opens the reader in Text only at that section, with Previous / Next and
  "Section n of N". Page still shows the whole saved page. "Open the original file" gets a `#:~:text=` fragment with
  the section's first words, which a browser tab scrolls to.
- The local AI's `read_pages` and "ask about this page" read a long page by section, as search cites it.
- The Library tab says "Section n:" on a hit; chat source cards say "section n".
- `tools/search_eval/score.py --sections <folder>` measures with the sections file kept in a folder you choose
  (built there if missing). Without it, long pages are searched whole, and the scorer never builds or removes a
  sections file in the data folder.
- `engine/sections.py` added to the Linux build's copied files and the macOS spec's hidden imports.
  `web/index.html` and `web/sw.js` versions bumped.

## Why

Issue #154 asked for search that treats a question as triage: an urgent question must get a useful first page.
Proposal: #{ISSUE}. Whole books saved as one page take places in the top 8 for questions they have nothing to do
with, because they contain every word somewhere. Cutting them into sections lets the one section that is about the
question compete on its own, and keeps the rest of the book out.

## How it was tested

Measured with PR 1's scorer (keyword about 4 minutes, hybrid about 25 per run), read-only, against the same copy of the Medium library pack as PR 1's baseline. "Before"
is PR 1's tip (`main` 9645686 plus the test sets); it reproduces `tools/search_eval/baseline-main.json` exactly.
"After" is this branch with `--sections <scratch folder>`. The sections file was built by this branch's code into a
scratch folder outside the data folder; nothing in the data folder was written (file sizes and times compared before
and after).

**Whole books in the top 8** (the 351 long pages; "after" counts a section of one):

| Questions | Mode | *Modern Machine-Shop Practice* in top 8 | any whole book in top 8 | places taken by whole books |
|---|---|---|---|---|
| Triage, all 362 | keyword | 25 → 4 | 106 → 87 | 286 → 146 |
| Triage, 253 clean | keyword | 23 → 3 | 99 → 60 | 273 → 104 |
| Triage, all 362 | hybrid | 26 → 3 | 77 → 58 | 145 → 93 |
| Triage, 253 clean | hybrid | 25 → 2 | 64 → 39 | 129 → 68 |

The author's fork measured 25 → 6 (keyword) and 26 → 1 (hybrid) for *Modern Machine-Shop Practice*.

After the change, the long pages that still come up are mostly the right section of a relevant book: the FAO animal
health manual's chapter on treating sick animals, the *Small Wind Guidebook*, *Canning*.

**Useful pages** (`n` questions; before → after, one number when unchanged):

| Set | Mode | n | useful of 8 (mean) | first useful | any of top 3 | covered | no useful page | topic cap broken | wrong sense first |
|---|---|---|---|---|---|---|---|---|---|
| Triage, red | keyword | 131 | 3.89 → 4.18 | 58 → 59 | 96 → 97 | 89 | 27 → 26 | 4 | 0 |
| Triage, yellow | keyword | 56 | 5.05 → 5.21 | 39 → 40 | 46 → 47 | 49 → 47 | 6 → 8 | 0 | 0 |
| Triage, green | keyword | 44 | 5.77 → 6.05 | 36 → 37 | 41 | 40 → 41 | 1 → 2 | 0 | 0 |
| Triage, counterexamples | keyword | 22 | 4.91 → 4.82 | 14 | 18 → 17 | 19 | 2 → 3 | 0 | 4 → 5 |
| Triage, typo versions | keyword | 109 | 2.23 → 2.21 | 30 | 47 | 42 → 41 | 54 | 3 | 0 |
| #128, clean | keyword | 27 | 4.44 → 4.37 | 16 → 17 | 23 → 22 | 23 | 3 | 0 | 0 |
| #128, typos | keyword | 25 | 3.6 → 3.52 | 13 | 16 | 16 | 7 | 0 | 2 |
| #154, clean | keyword | 32 | 4.47 → 4.62 | 20 → 19 | 27 | 27 | 3 | 2 | 0 |
| #154, typos | keyword | 32 | 2.91 → 2.88 | 13 | 19 | 15 → 14 | 12 → 13 | 2 | 1 |
| #241 | keyword | 21 | 4.81 → 5.0 | 12 → 11 | 20 | 19 | 0 | 1 | 2 |
| Triage, red | hybrid | 131 | 5.11 → 5.27 | 88 → 91 | 111 → 112 | 114 → 112 | 5 → 8 | 3 | 0 |
| Triage, yellow | hybrid | 56 | 5.86 → 6.0 | 42 → 43 | 51 | 54 → 55 | 1 → 0 | 0 | 0 |
| Triage, green | hybrid | 44 | 6.84 → 6.98 | 37 → 38 | 42 → 44 | 43 → 44 | 0 | 0 | 0 |
| Triage, counterexamples | hybrid | 22 | 5.73 → 6.05 | 17 | 20 → 21 | 22 | 0 | 0 | 2 |
| Triage, typo versions | hybrid | 109 | 3.39 → 3.44 | 49 | 74 → 75 | 71 | 23 | 2 | 0 |
| #128, clean | hybrid | 27 | 5.93 → 6.0 | 24 → 23 | 26 | 27 | 0 | 0 | 0 |
| #128, typos | hybrid | 25 | 4.72 | 15 | 19 | 20 | 4 | 0 | 2 |
| #154, clean | hybrid | 32 | 5.47 | 20 → 21 | 29 | 27 → 28 | 3 → 2 | 1 | 0 |
| #154, typos | hybrid | 32 | 4.16 → 4.22 | 14 | 25 → 24 | 25 | 2 | 1 | 1 |
| #241 | hybrid | 21 | 5.71 → 5.62 | 14 → 16 | 21 | 20 → 19 | 0 | 0 | 0 |

#154's own useful count (keyword): 141 → 144 of 256 clean, 101 → 101 of 256 typos.
#154's own useful count (hybrid): 177 → 177 of 256 clean, 143 → 144 of 256 typos.

Lists 1-4 (pages shown): unchanged in both modes. Conversations (last message): useful 3.23 → 3.35 keyword (no useful page 18 → 15), 3.98 → 4.15 hybrid.

Where a count went down, I looked at each question. Most "lost" useful pages were a whole book whose snippet
happened to contain the needed words: "kid not breathing and lips are blue" counted a calf-care chapter ("check that
the calf is breathing"); "splashed bleach in my eye" counted *Textiles and Clothing* (lime water and acid);
"bad toothache and swollen face" counted *Introduction to Philosophy*; "dust in my eye" counted a forum comment
("keep an eye on"). Two were real: a medicines page on poisoning and a prepping checklist with matches were pushed
just below the top 8 by sections of other pages. In hybrid, the 3 red questions that went to no useful page are the
same pattern: before, their one useful hit was a whole book (for "his finger got cut off" the top 3 were
*Modern Machine-Shop Practice*, *The Turner's Companion* and *The Principles of Leather Manufacture*).

Tests:

- New `app/tests/test_long_pages.py` (8 tests), on a small made-up library with one 70,000-character book: sections
  built and nothing lost between them; scattered words no longer find the book; a section is found as its section
  in `find`, `_fts` and `hybrid`; relabelling the meaning index (once per document); new passages chunked by
  section; a rebuild when the library index changes; and whole pages when the file cannot be built. Passes with
  `PYTHONUTF8=0`.
- Every test file run one at a time on Windows. All pass except `test_battery` (fails before and after: Linux only)
  and `test_setup` (3 failures in map space and the first-run job, the same before and after this change).
  `test_run_source_linux` skips on Windows.
- Checked by hand in the browser with the test library: the Library tab shows "Section 6:", the hit opens Text only
  at "Section 6 of 15" with the right text, and "Open the original file" carries the text fragment.

## What it doesn't do

- The cut is by length: saved pages have no headings in the index. 20,000 and 5,000 were set once, not tuned.
- bm25 scores from two FTS5 tables use different statistics, so the merge between the library index and the
  sections file is approximate. It measured well enough.
- In the reader's Page view the saved page opens at its top: it runs in a sandboxed frame, which the reader cannot
  scroll, and browsers do not apply text fragments inside a frame. That is why a section opens in Text only.
- Encyclopedia articles by best section (`engine/wiki_pick.py`) come in PR 4; typo correction in PR 3.
- PDFs and pages that already have their own page numbers are not changed.

Part 2 of 8 of the triage-based search engine (proposal: #{ISSUE}); builds on #{PR1}. Until that one is merged, GitHub shows its changes here too; this part's own changes alone: [triage/1-search-eval...triage/2-sections](https://github.com/STAirye/lastbook/compare/triage/1-search-eval...triage/2-sections).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
