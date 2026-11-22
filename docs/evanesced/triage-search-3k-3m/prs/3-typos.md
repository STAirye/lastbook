Put misspelled words right before searching the library (triage search, part 3 of 8)

## What changes

Keyword search needs whole words. "my husbnd colapsed and isnt breating" matches nothing as typed, the search falls
back to any of the words, and the word that was the emergency drops out. This puts each misspelled word back to a word
the library uses, before the search sees the question.

- New `engine/typos.py`. `typos.correct(q)` runs first in `server.query_groups` (the Library tab's search and the
  assistant's keyword search) and in `assistant.hybrid` (keyword and meaning search). `/api/find` and `/api/retrieve`
  add `corrected`, what was searched, when it differs from the question. The page does not show it yet.
- **The words are the library's own.** The keyword index's terms and how many pages hold each (`fts5vocab`, read-only,
  about 1.3 s, kept until the search database changes). The library's first-aid and emergency books, found by title,
  count extra: "chokeing" becomes choking, not cooking. No dictionary is downloaded. A library of fewer than 5,000
  terms (a test library, a first install) changes nothing.
- **Only words that look like typos change**: plain a-z, 3+ letters, not a stop word, on fewer than 20 pages. The
  replacement is one edit away (two for words of 5+ letters the index lacks) and on many more pages. A changed letter
  must be a neighbouring key or a vowel for a vowel ("bleech" → bleach); a doubled or undoubled letter counts extra
  ("chocking" → choking, not checking; "stabed" → stabbed). A word the emergency books use themselves stays ("riots"
  is never "roots"). A short list of well-known misspellings that edits cannot reach ("asma", "hemmorage", "unconshus").
- **Ordinary English is never "corrected".** The corrector knows only the library, so it bent everyday words into
  library words: "keeled" → peeled, "puking" → poking, "gasps" → gaps. A word of the new `engine/english_words.txt.gz`
  (every form of the hunspell en_US words as Chromium ships them, 78,238 words, 205 KB) is left alone, and so are
  British spellings of them and a few chat words and medicine names. `tools/english_words.py` builds the list; the
  licence is `engine/english_words.LICENSE.txt`, the copyright section of the dictionary's README, verbatim. A short,
  explicit list of real-word slips is put right: "chocking", "overdoes", "brunt", and by the words around them
  "he cant breed" → breathe, "sea sure" → seizure, "chest pane", "hart attack", "gas leek". Letters typed again and
  again are cut first ("bloooood" → blood).
- **Contractions typed without the apostrophe keep their negation.** "hasnt", "isnt", "shouldve" and the rest of the
  common ones are put back first, so they are not bent into hasn, shoulder or whose. "im" is I'm unless a medicine
  word is beside it ("give im adrenaline" stays). `server.STOP` now also drops "i'm", "he's", "there's" and the like;
  "isn't" and "can't" stay searched.
- **Words typed with no spaces are split**: "heschuokinghelkp" → "he's choking help", "kitchenonfire" → "kitchen on
  fire". Only words of 8+ letters the index does not hold, so "hypothermia", "firecraft" and "Gutenberg" stay.
- **Questions in another language are left as typed.** A question with letters beyond a-z, or with more Spanish,
  Portuguese or French function words than English ones, is not corrected. "a", "me" and "no" count for neither
  language: before that, "Me muero de ganas de ir a la playa" became "Me mere de gaas de ir a la play" (test list 4).
- Switches: `LASTBOOK_TYPO_FIX=0` (all of it), `LASTBOOK_TYPO_SPLIT=0`, `LASTBOOK_TYPO_ENGLISH=0`.
- The word list and its licence ship in the Windows build, the macOS spec and the Linux build, and the three package
  scans require them. `engine.typos` added to the macOS hidden imports and the Linux build's copied files.
- `docs/TRIAGE-SEARCH.md` section 3 says what is in this pull request and what comes later.

No web files change.

## Why

Issue #154 asked for search that treats a question as triage: an urgent question must get a useful first page.
Proposal: #{ISSUE}. People in a hurry type fast, on a phone, scared. In the triage test set, typo versions of the
questions got 2.2 useful pages of 8 against 4.8 for the same questions typed right, and half of them got no useful
page at all.

## How it was tested

Measured with PR 1's scorer, read-only, against the same copy of the Medium library pack as PR 1 and PR 2, with
`--sections <scratch folder>` (the sections file built by PR 2's code into a scratch folder outside the data folder).
"Before" is PR 2's tip (cf12898); it reproduces PR 2's "after" numbers exactly. Nothing in the data folder was written
(file sizes and times compared before and after).

**Useful pages, keyword-only** (`n` questions; before → after, one number when unchanged):

| Set | n | useful of 8 (mean) | first useful | any of top 3 | covered | no useful page | topic cap broken | wrong sense first |
|---|---|---|---|---|---|---|---|---|
| Triage, red | 131 | 4.18 | 59 | 97 | 89 | 26 | 4 | 0 |
| Triage, yellow | 56 | 5.21 | 40 | 47 | 47 | 8 | 0 | 0 |
| Triage, green | 44 | 6.05 | 37 | 41 | 41 | 2 | 0 | 0 |
| Triage, counterexamples | 22 | 4.82 | 14 | 17 | 19 | 3 | 0 | 5 |
| **Triage, typo versions** | 109 | **2.21 → 4.76** | 30 → 65 | 47 → 86 | 41 → 82 | 54 → 19 | 3 → 2 | 0 |
| #128, clean | 27 | 4.37 | 17 | 22 | 23 | 3 | 0 | 0 |
| #128, typos | 25 | 3.52 → 4.32 | 13 → 15 | 16 → 21 | 16 → 20 | 7 → 4 | 0 | 2 → 0 |
| #154, clean | 32 | 4.62 | 19 | 27 | 27 | 3 | 2 | 0 |
| **#154, typos** | 32 | **2.88 → 4.75** | 13 → 21 | 19 → 27 | 14 → 27 | 13 → 2 | 2 | 1 → 0 |
| #241 | 21 | 5.0 | 11 | 20 | 19 | 0 | 1 | 2 |

#154's own useful count: 144 → 145 of 256 clean, 101 → 150 of 256 typos.
The author's fork measured 2.23 → 4.72 for the triage typo versions keyword-only.

**Useful pages, hybrid** (keyword + meaning search). "Before" is PR 2's recorded hybrid "after" run on the same
data, not rerun here (the keyword "before" reproduced PR 2's exactly):

| Set | n | useful of 8 (mean) | first useful | any of top 3 | covered | no useful page | topic cap broken | wrong sense first |
|---|---|---|---|---|---|---|---|---|
| Triage, red | 131 | 5.27 | 91 | 112 | 112 | 8 | 3 | 0 |
| Triage, yellow | 56 | 6.0 | 43 | 51 | 55 | 0 | 0 | 0 |
| Triage, green | 44 | 6.98 | 38 | 44 | 44 | 0 | 0 | 0 |
| Triage, counterexamples | 22 | 6.05 | 17 | 21 | 22 | 0 | 0 | 2 |
| **Triage, typo versions** | 109 | **3.44 → 5.62** | 49 → 86 | 75 → 99 | 71 → 96 | 23 → 6 | 2 → 1 | 0 |
| #128, clean | 27 | 6.0 | 23 | 26 | 27 | 0 | 0 | 0 |
| #128, typos | 25 | 4.72 → 5.92 | 15 → 20 | 19 → 22 | 20 → 24 | 4 → 1 | 0 | 2 → 0 |
| #154, clean | 32 | 5.47 | 21 | 29 → 28 | 28 | 2 | 1 | 0 |
| **#154, typos** | 32 | **4.22 → 5.41** | 14 → 20 | 24 → 27 | 25 → 27 | 2 | 1 | 1 → 0 |
| #241 | 21 | 5.62 | 16 | 21 | 19 | 0 | 0 | 0 |

#154's own useful count (hybrid): 177 → 179 of 256 clean, 144 → 176 of 256 typos. The author's fork measured
3.39 → 5.57 for the triage typo versions in hybrid. In hybrid, glued urgent messages with a useful first page:
1 → 14 of 18; conversations 4.15 → 4.17.

**Clean questions are not changed.** The corrector changes 0 of the 253 clean triage questions and 0 of #154's 32,
and 100 of the 109 triage typo versions and all 32 of #154's. The clean triage, #128 and #241 questions get exactly
the same 8 results as before. One clean #154 question changed its results, through the new stop words ("he's"): the same useful count, though in hybrid its useful page moved out of the top 3.

**Glued words** (`data/glued.json`): of 18 urgent messages typed with no spaces, 18 found no page before; after, 11
have a useful first page and 15 one in the top 3. Of 6 everyday ones, 0 → 4 in the top 3. Keyboard mash still finds
nothing (6 of 7), as it should.

**Conversations** (last message): useful 3.35 → 3.46, no useful page 15 → 13.

**Independent lists 1-4** (pages shown): every line now finds pages; before, 25 red lines of list 1, 11 of list 2 and
5 of list 3 found none.

**English words bent** (a typed word in the English list that the corrector changed, not by a split or an apostrophe):

| List | English guard off (`LASTBOOK_TYPO_ENGLISH=0`) | on |
|---|---|---|
| 1 (690 lines) | 40 lines | 3 |
| 2 (606) | 49 | 1 |
| 3 (531) | 47 | 0 |
| 4 (832) | 6 | 0 |

The 4 left are the explicit slips list on purpose ("chocking" → choking, "overdoes" → overdose). Every other English
word stays. The author's fork measured 35 → 0 and 46 → 0 on lists 1 and 2 against its older corrector.
Of list 4's 532 lines in Spanish, the corrector changed 50 before the "a"/"me"/"no" fix and none after; none of 2,926
English test questions and lines is taken for another language.

**Where typo versions lost pages** (15 of 109 got fewer useful pages): each one was corrected right except
"tooth nocked out" (→ nicked). Searching the right words brings other pages: "is it safe to put watr on a burn" found 8
burn pages when "watr" matched nothing and the search used the other words; "water on a burn" brings water pages.

Tests:

- New `app/tests/test_typos.py` (30 tests), on made-up vocabularies with page counts rounded from the real library,
  so each trap is the real one ("checking" is on more pages than "choking"): known fixes and traps, contractions and
  "im", names with capitals inside, numbers and models, other languages, glued words, English words and the slips list,
  repeated letters, the switches, and the vocabulary read from a small search database. Passes with `PYTHONUTF8=0`.
- `app/tests/test_bridge.py`: the correction reaches `query_groups`, `/api/find` and `/api/retrieve` (with
  `corrected`), and pronoun contractions are not searched.
- `app/tests/test_what_ships.py`: the word list and its licence are in every build and every package scan.
- Every test file run one at a time on Windows. All pass except `test_battery` (fails before and after: Linux only)
  and `test_setup` (the same 3 failures before and after: map space and the first-run job, as in PR 2).
  `test_run_source_linux` skips on Windows.

## How it relates to #287

#287 (`web/words.js`) lets the guide search try other forms of a word (-s, -es, -ies, -ed, -ing) when a search finds
nothing. The corrector does not touch endings: an English word is never changed, so "tourniquets", "fainting",
"choked" and "batteries" are searched as typed. It only fixes forms that are not words ("chokeing" → choking,
"bleedin" → bleeding). The library search already had its own form rule (a word of 5+ letters ending in -s is also
searched without it). The two searches are separate (the corrector runs on the server, #287 in the page), so nothing
needed aligning; making the library search's forms as wide as #287's would be a change of its own, measured on its own.

## What it doesn't do

- Body words one slip away that the library also has as words ("puls", on 24 pages) are not put right here, nor
  glued runs around a body word that could not be split. That needs the body words of `engine/confidence.py`, which
  comes in PR 5 with `typos.body_fix` and `LASTBOOK_BODY_FIX`.
- The urgency check (`assistant.is_danger`, PR 7) and the encyclopedia search (PR 4) will also use the corrected text;
  they are not here yet.
- The page does not show "Searched for: ..." yet; the API returns it.
- English only. Other languages are left as typed.
- The constants were set on named failures and on the glued-word runs described in `docs/TRIAGE-SEARCH.md`; most were
  not swept. The 15 slang and brand words added to the English list came from independent list 2, so its typo numbers
  are in-sample.

Part 3 of 8 of the triage-based search engine (proposal: #{ISSUE}); builds on #{PR2}. Until that one is merged, GitHub shows its changes here too; this part's own changes alone: [triage/2-sections...triage/3-typos](https://github.com/STAirye/lastbook/compare/triage/2-sections...triage/3-typos).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
