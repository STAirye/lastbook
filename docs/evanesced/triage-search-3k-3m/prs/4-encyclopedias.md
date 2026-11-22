Pick encyclopedia articles by their best section, and show them apart from the library (triage search, part 4 of 8)

## What changes

Chat's first results add the top 3 encyclopedia articles for the question. Each article goes to the model as its first
2,000 characters. Encyclopedia articles are long, and the useful part is often not at the start. Whole books saved as
one article come first for questions they have nothing to do with. This picks the part of each article that is about the
question, and shows the articles apart from the library's pages.

- New `engine/wiki_pick.py`. `pick(q)`:
  - Searches the encyclopedias with the question's content words only. The library's stop words are dropped, plus a few
    small words every book holds ("my" and "has" matched every book). It asks for 6 candidates per file.
  - Skips print and printable versions of whole books (each chapter is its own article too), and articles over 800,000
    bytes.
  - Cuts each candidate into sections of about 5,000 characters (`sections.cut`, from PR 2). An article scores by its
    best section's share of the question's words, plus a little for words in its title. A word matches by its first 5
    letters, so "burns" finds "burned". Ties keep the encyclopedia's own order.
  - Sends the part of that best section where the words are (`encyclopedias.pick_section`), not the start of the article.
- `assistant.first_wiki(q)` runs `wiki_pick.pick` on the question after `typos.correct` (PR 3), in place of the plain
  `encyclopedia_hits` call in the chat turn. If the pick raises, or `LASTBOOK_WIKI_PICK=0`, it uses `encyclopedia_hits`
  as before. It never raises into Chat.
- **The library's results and the encyclopedia articles go to the model as two system messages**, not one
  (`assistant.initial_messages`). On `main` they are merged into one "Initial library search results..." message. The
  two searches score on different scales (a short web excerpt holds fewer of the question's words than a 2,000-character
  article, only because it is shorter), so each keeps its own order. The articles' message says they are
  community-written background and that the library results above are the ones to prefer for safety-critical steps. If
  only one search finds something, only that message is sent. If neither does, the "found nothing" message is
  unchanged.
- `web/chat.js`: under the answer, the encyclopedia articles are their own group, "From the encyclopedias (n)", apart
  from "Sources". It is shown whether the answer cited them or not (the cited ones first, then the rest; "not used in
  this answer" when none was cited). Library sources that were looked at but not used stay under "Also looked at". While
  the answer is being written, the pages found so far are split the same way. The helpers are `isWiki` and `byShelf`.
  Chat's labels are plain English in `chat.js` on `main` (not in the i18n catalogs), so the new label is too.
- `engine/wiki_pick.py` added to the Linux build's copied files and the macOS spec's hidden imports (the Windows build
  finds it through `assistant`). `web/index.html` (`chat.js?v=16`) and `web/sw.js` (`sg-shell-v14`) bumped.
- `docs/TRIAGE-SEARCH.md` section 2 says what is in this pull request and what comes later.

`LASTBOOK_WIKI_PICK=0` turns the picker off (the plain encyclopedia search, still shown apart).

## Why

Issue #154 asked for search that treats a question as triage: an urgent question must get a useful first page.
Proposal: #{ISSUE}. The same thing that hurt library search (PR 2) is worse in the encyclopedias, which hold whole books
and long articles:

- The median article is about 28,000 characters, and 136 of 752 are over 100,000.
- Whole books saved as one article came first. "Mirad Grammar/print version" (1.35 MB) came first for "my toddler
  drank bleach". "US History/Print version" came first for "my eyes sting from wildfire smoke".
- The words a useful answer needs were in the first 2,000 characters for only 259 of the 622 articles that held them.

Apart from the ranking, the merged message also meant one search's scores were compared with the other's, and the
person could not tell which sources were the library's and which were community-written.

## How it was tested

Measured on the author's fork, which has the same code (`engine/wiki_pick.py` is unchanged here apart from its comment),
on the 253 clean triage questions, with the three encyclopedia files that ship with the Medium pack (MDWiki, Appropedia,
Wikibooks; 752 candidate articles). "Useful" means the article's excerpt and title contain the words the question's
case needs (the same `need` patterns as PR 1's test set). The scorer from PR 1 does not measure the encyclopedias, so I
did not rerun these numbers on this branch.

| 253 clean questions | before (raw question, first 2,000 characters) | best section |
|---|---|---|
| First article useful | 92 (36%) | **146 (58%)** |
| Any of the 3 useful | 163 | **197** |
| First useful, red / yellow / green | 34 / 25 / 33 | 61 / 40 / 45 |
| No article at all | 1 | 5 |
| Time, median / p90 | 92 / 512 ms | 578 / 962 ms |

The excerpt is chosen for the question's words, so "useful" favours it a little where the two overlap. The
encyclopedias hold little first aid, so wrong first articles remain ("Doom/Complete list of enemies" for a chainsaw
cut). Typo questions, measured on the raw words, went from 4 to 7 useful of 109; Chat now fixes typos first.

On the same 253 questions, the keyword picker's first article was useful for 70% of the everyday ones (85 of 122) and
47% of the urgent ones (61 of 131).

Tests:

- New `app/tests/test_wiki_pick.py` (6 tests, fake articles, no libzim): stop words are not sent, print versions and
  huge articles are skipped, the excerpt is the best section and not the start, more of the words beats the search
  order, word endings match, a question with no content words does not search.
- `app/tests/test_encyclopedias.py` (4 new): `first_wiki` uses the pick on the corrected question, falls back when the
  pick raises and with `LASTBOOK_WIKI_PICK=0`; the initial results are two system messages, each holding only its own
  sources; one block alone, and neither.
- `app/tests/test_chat_steps.py` (1 new, Node): `byShelf` splits library and encyclopedia sources and keeps each order.
- Run one file at a time on Windows, also with `PYTHONUTF8=0`: `test_wiki_pick`, `test_encyclopedias`,
  `test_encyclopedias_real` (skipped without the files), `test_wiki_routes`, `test_chat_steps`, `test_chat_tables`,
  `test_typos`, `test_long_pages`, `test_i18n_catalogs`, `test_bridge`, `test_what_ships`, `test_retrieval`,
  `test_topic_search`: all pass. `test_battery` and `test_run_source_linux` only pass on Linux (fail or skip on Windows
  before and after this change).
- Not run: the page in a browser with a real model.

## What it doesn't do

- **No urgent skip.** The encyclopedias are searched for every question. Leaving them out for questions labelled urgent,
  so the manuals have the first results to themselves, needs `assistant.is_danger` and comes in PR 7.
- **No vector index.** The author's fork also tried a meaning index of the encyclopedias. It found the useful article more often, but it needs about 690 MB of memory for three files, grows with every pack, and needs a GPU build for each file. It was dropped.
- **The question is not translated.** A question in another language is searched as typed. English search words for
  such questions are a later part of this series.
- The encyclopedia search still runs after the library search in the chat turn. Running them side by side was a speed
  change on the fork and is left out here to keep this small.
- The constants (6 candidates per file, 800,000 bytes, 5 letters of stem, the 0.25 title weight) were not swept. A
  minimum score was tried on the fork and dropped.

Part 4 of 8 of the triage-based search engine (proposal: #{ISSUE}); builds on #{PR3}. Until that one is merged, GitHub shows its changes here too; this part's own changes alone: [triage/3-typos...triage/4-encyclopedias](https://github.com/STAirye/lastbook/compare/triage/3-typos...triage/4-encyclopedias).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
