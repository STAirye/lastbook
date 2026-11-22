# A triage-based search engine: methods, formulas and how to rerun every number

Companion to `upstream-search-summary.md` (the draft proposal). Every constant below was read from the code at
`c7795b5` (branch `fork/lightweight-gemma-no-us-maps`) or from a stored file, not from memory. Where `docs/FORK.md`
or the summary disagrees with the code, the code is used and the disagreement is listed in section 12.

Conventions: `<repo>` = the checkout, `<drafts>` = `<repo>/.claude/drafts` (untracked working folder),
`<LastbookData>` = a data folder (section 11), `path:function` = file and function. "kw" = keyword-only search (what
the desktop app ships), "hy" = hybrid (keyword + bge-small meaning search, server mode only). Several scripts have
absolute Windows paths for the repo and data folder written into them; edit those before running.

Checked again while writing this (all reproduced exactly): the meaning check's thresholds and centroids (6), the
confidence coefficients against `conf_final.txt` (5), the typo corrector on the 362 test questions (3), the
sections file's size (1), the examples file's counts (6), the manifest's sizes and SHA-256 (6). Nothing else was rerun;
the other numbers come from stored output files named in each section.

---

## 1. Long pages in sections

Code: `engine/sections.py` (`cut`, `norm_ws`, `build`, `query`, `ensure`, `section_of`), used by `server.find`,
`assistant._fts`, `retrieval.Index` (relabelling), the reader (`server.py` document endpoint).

Rule, with constants:

| Item | Value |
|---|---|
| Which pages | rows of the library's `pages` table with `length(body) > LONG` (LONG = 20,000 characters), whose catalog kind is `html`, and whose document has exactly one row (a document with pages of its own keeps its page numbers) |
| Cut size | `SECTION` = 5,000 characters |
| Text cut | `norm_ws(body)`: every whitespace run becomes one space, then strip |
| Boundary | for a piece starting at `i`: end `j = min(len, i + 5000)`. If `j < len`: take the last `". "` found between `i + 2500` and `j` and end just after the full stop (`j = k + 1`); if none, the last space between `i + 2500` and `j`; if none, cut at 5,000 exactly. Each piece is stripped and numbered 1..n; its start offset `i` is stored |
| So | a section is 2,500 to 5,000 characters (exactly 5,000 only when no boundary exists in the second half) |
| Storage | `derived/index/sections-<12 hex of sha256(sig)>.sqlite`, `sig = "<size>:<mtime_ns>:20000:5000:1"` of `search.sqlite` (`VERSION` = 1). Tables: `pages` (FTS5, same columns and `unicode61` tokenizer as the library's), `long` (which library rows they replace), `section` (doc, number, start offset, rowid), `meta`. The pack's checksummed `search.sqlite` is never written. A changed `search.sqlite` gives a new signature, a rebuild (a few seconds) and removal of older files |

Ranking in search (`sections.query`): the same SQL runs on the library index (rows of long pages excluded with
`rowid NOT IN (...)`) and on the sections file; each side is `ORDER BY bm25(pages,0,6,1,1,0,0,1) LIMIT n` (column weights:
doc_id 0, title 6, collection 1, category 1, path 0, page 0, body 1: the library's own). The two row lists are
concatenated and sorted by that bm25 (more negative is better), and the first `n` kept. bm25 values from two FTS5
tables use different corpus statistics, so the merge is approximate (documented in the code). A section's `page` is its
section number, so each section is an ordinary result; hybrid search fuses keyword and meaning lists with reciprocal rank
fusion, `score = sum over lists 1 / (60 + rank)` (`retrieval.rrf`, k = 60), on the key (doc, page). Meaning-search passages
embedded before the change are relabelled with their section by start offset (`sections.section_of`, no re-embedding).

How the constants were chosen: not by a sweep. 20,000 and 5,000 were set once; the stored text has no headings, so the cut
is by length. A score penalty for long pages was tried instead and dropped (`<drafts>/triage/COMPARE_long_pages.md`:
the book still came in through meaning search). No other sizes were measured (not recorded).

Numbers and where they come from:

| Claim | Source | Rerun |
|---|---|---|
| 353 whole-book pages (over 20,000 characters), 26 of 362 questions had *Modern Machine-Shop Practice* in the top 8 (hy); 26 → 1 with sections alone (hy), 25 → 6 (kw) | `triage/COMPARE_long_pages.md` (made with `triage/compare.py`) | `score.py` against a base server and a server with the sections file, then `compare.py` |
| 26 → 4 (both modes), typos 2.23 → 4.72 kw | `triage/COMPARE_rewrite.md`: base `256d52f` against the combined search rewrite (sections + typo correction + conversation) | same, `results_rewrite.json` |
| Build on the current data copy | 351 pages → 7,623 sections in 4.2 s, at most 1,890 sections in one page (read from the file's `meta` and `long` tables) | open `derived/index/sections-*.sqlite` read-only |

Not found in any stored output: "hybrid search on those pages 4.95 s → 0.68 s". The nearest stored figure is the mean
hybrid search time per question of 0.67 s (`triage/conf_hy.json`, 362 questions). Treat that line of the summary as
unsourced until it is re-measured.

---

## 2. Encyclopedia articles by best section

Code: `engine/wiki_pick.py` (`words_of`, `_pattern`, `best_section`, `score_text`, `pick`), `engine/encyclopedias.py`
(`search`, `entry_text`, `pick_section`; `INITIAL_LIMIT` = 3, `INITIAL_CHARS` = 2,000, `SEARCH_LIMIT` = 24), caller
`assistant.first_wiki`. Off with `LASTBOOK_WIKI_PICK=0`.

Constants: `PER_FILE` = 6 candidates per encyclopedia file, `SECTION` = 5,000 (= `sections.SECTION`), `MAX_BYTES` =
800,000, `STEM` = 5, `TITLE_WEIGHT` = 0.25.

Procedure for a question `q`:

1. `words_of(q)`: lower-case; tokens matching `[a-z0-9]+(?:'[a-z]+)?`; cut at the apostrophe; keep tokens of 3+ letters
   that are not in `STOP`; each word once, in order. `STOP` = `typos.STOP` (the library search's stop words, same as
   `server.STOP`) plus `am been were has had he she his her him hers it they just now very really about after before out
   all any one would could also than too much many off over`.
2. `_pattern(w)`: remove one ending, trying in order `ing`, `ed`, `es`, `s`, the first that fits and leaves 3+ letters; the
   pattern is `\b` + the first `STEM` (5) letters of what is left, case-insensitive ("burns" and "burned" both become `\bburn`).
3. Candidates = `encyclopedias.search(' '.join(words), per_file=6, limit=24, read_text=False)`, in the encyclopedia's own order (`rank`).
4. Skip a candidate whose path or title matches `PRINT` = `/(print(able)?[ _]version|print)$|[ _]\(print version\)$`, or whose
   archive item is larger than 800,000 bytes, or whose text cannot be read.
5. Read the whole text, `sections.cut(norm_ws(text), 5000)`. `share` = the best section's
   `(number of patterns found in the section) / (number of patterns)`; earlier sections win ties; stop early at 1.0.
   Skip the article if `share <= 0`.
6. `score = share + 0.25 * (patterns found in the title) / (number of patterns)`.
7. Sort by `(-score, rank)`; keep the first 3. Excerpt = `encyclopedias.pick_section(best section, query, 2000)`.

`score_text(text, title, pats) = (patterns found in text + 0.25 * patterns found in title) / number of patterns` is the same
score for any text (the library page case); `pick` itself uses the best section's share instead of the whole text's.

Constant choice: not swept. `floor.py` tried a minimum score (a floor) and dropped it. The 800 KB limit, the 6 candidates and
the 0.25 weight are not backed by a recorded comparison; the rationale in the code is that whole books saved as one article
(1.35 MB) and print versions came first.

"Useful" measure for this table: the case's `need` regexes (section 9) joined with `|`, searched case-insensitively in
`excerpt + ' ' + title` of each article. Table (253 clean questions, full library with the three encyclopedia files),
from `docs/evanesced/encyclopedias-3n/compare.json`:

| | upstream's way (raw question, first 2,000 characters) | `wiki_pick` |
|---|---|---|
| first article useful | 92 (36%) | 146 (58%) |
| any of the 3 useful | 163 | 197 |
| no article | 1 | 5 |
| time median / p90 | 92 / 512 ms | 578 / 962 ms |

The excerpt is chosen for the question's words, so "useful" favours it a little where the two overlap (FORK.md says so too).
Typo questions were measured raw: 4 → 7 of 109. Rerun: `docs/evanesced/encyclopedias-3n/compare.py` (hard-coded repo and
data paths and an import of `cases.py` from `<drafts>/triage`). `measure.py` there gives the length statistics (median article
28,000 characters; 136 of 752 over 100,000; the useful words inside the first 2,000 characters for 259 of 622 articles that hold them).

---

## 3. Typo correction

Code: `engine/typos.py`. Entry points `correct(q)` (memoised, 2,000 entries), `correct_with(q, words)`, `fix_word`,
`split_word`, `body_fix`. Switches: `LASTBOOK_TYPO_FIX=0` (all), `LASTBOOK_TYPO_SPLIT=0`, `LASTBOOK_TYPO_ENGLISH=0`,
`LASTBOOK_BODY_FIX=0`. Called first in `assistant.hybrid`, `server.query_groups` and `assistant.is_danger`.

**The library's words** (`Words.from_db`, read once per search database, kept until its size or time changes):

- `V[term]` = number of pages holding the term, from `fts5vocab`, only terms on 3 or more pages that are ASCII letters.
- `E[word]` = how many times the word occurs in the bodies of the first-aid and emergency books, found by title with
  `EMERGENCY_TITLES` (`"first aid" OR "emergency care" OR resuscitation OR "where there is no doctor" OR "emergency response
  guidebook" OR "fire safety" OR "are you ready" OR "cert basic"`, not `financial`); words of 3+ letters `[a-z]{3,}`, kept when
  they occur 3+ times. (`confidence._emergency_book` uses a slightly longer title regex, section 5.)
- Fewer than `MIN_VOCAB` = 5,000 terms: no correction at all. On the current data copy: 99,476 terms, 10,283 emergency words.

**Edits.** Not a numeric edit distance: candidates are strings one edit away (change a letter, drop one, add one, swap two
neighbours), or two edits away for words of 5+ letters that the library does not hold (`_edits2`, found through a table of every
common word with one letter dropped). Each edit carries a pair (plausible, bonus):

- changing a letter is plausible only if the new letter is a neighbouring key on a QWERTY layout (rows `qwertyuiop`, `asdfghjkl`,
  `zxcvbnm`, row r shifted r/2 keys; adjacent = same row 1 key apart, or neighbouring rows at most 0.5 apart), or vowel for vowel;
  dropping, adding and swapping are always plausible;
- bonus `DOUBLED` = 3.0 when the edit doubles or undoubles a letter (`ck` counts as a doubled k), else 0 (`e^3` is about 20, so it
  counts as if the word were on about 20 times as many pages); a two-edit pair is plausible only if both edits are, with the bonuses added.

**`fix_word(w)`** (w lower-case), in this order, first rule that applies wins:

1. `w` in `APOSTROPHES` (47 contractions typed without the apostrophe: `hasnt` → `hasn't`): that.
2. `w` in `KNOWN` (52 hand-listed misspellings that edits cannot reach) and `V[w] < 3` and the target is in `V`: the target.
3. `w` in `SLIPS` (5 real words that are slips for an emergency word: `chocking`, `chocked`, `overdoes`, `brunt`, `wile`) and the
   target is in `V` and `V[w] < RARE`: the target.
4. `is_english(w)` (section below): unchanged.
5. Unchanged if `w` is a stop word, shorter than 3, not plain a-z, or `V[w] >= RARE` (20).
6. `indexed = V[w] > 0` (the library holds it on 3+ pages). If `indexed` and `E[w] > 0` (the emergency books use it): unchanged.
7. `need = max(MIN_PAGES, V[w] * (GAIN_INDEXED if indexed else GAIN))` with `MIN_PAGES` = 10, `GAIN_INDEXED` = 20, `GAIN` = 50.
   A candidate `x` is allowed if `V[x] >= need`, `len(x) >= 3`, `x` not a stop word, and, when `w` is indexed, the edit is plausible
   and `E[x] >= EMERGENCY_MIN` (5).
8. Candidates: one edit; if none, and `len(w) >= 5` and `w` not indexed, two edits.
9. Choice: the maximum of the tuple `(x[0] == w[0], plausible, score(x) + bonus)` compared left to right, where
   `score(x) = 2 * ln(1 + E[x]) + ln(V[x])`. So: keep the first letter, then plausible slips, then emergency books' use of the word
   (weight 2 on the log) plus how common it is, with the doubled-letter bonus added to the last term.

**Word list guard** (`is_english`): `engine/english_words.txt.gz` (78,238 lower-case words: every form of the hunspell en_US
dictionary; licence in `engine/english_words.LICENSE.txt`) plus `EXTRA_ENGLISH` (chat words, medicine names, a few slang words)
plus British spellings mapped by suffix (`our`/`or`, `isation`/`ization`, `ise`/`ize`, `yse`/`yze`, `ae`/`e`, `oe`/`e`, `tre`/`ter`,
`ogue`/`og`, `ence`/`ense`, `lled`/`led`, `lling`/`ling`). An English word is never corrected, split or made a body word, except the
`SLIPS` and the 12 `PHRASE_SLIPS` regexes ("he cant breed" → breathe, "sea sure" → seizure, "chest pane", "hart attack", ...), which
are skipped when a machine, food or animal word is in the question. Letters typed three or more times running are cut first
(`unstretch`: "bloooood" → blood).

**Order in `correct_with(q)`:** a question that looks foreign (non-ASCII letters, or more Spanish/Portuguese/French function words
than English ones) is returned as typed; then `restore_im` ("im vomiting" → "i'm vomiting", unless a medicine word is beside it);
then `phrase_slips`; then each token: not plain letters or ALL CAPS (unless most of the question is capitals) or with inner capitals
("ODing", "iPhone"): kept (a run with an apostrophe or hyphen inside goes to `glued`); `unstretch`; `split_word`; `fix_word`;
`body_fix`; capitalisation restored.

**Glued words** (`split_word`, only for a word of 8+ letters, or 6+ with an apostrophe inside, that the index does not hold,
is not English and is plain a-z). Dynamic programming over where spaces go. Cost of one piece `s`:

```
rare(w)  = ln(max V) - ln(V.get(w, 3)) - 1 [if len(w) <= 2]
piece(s) = rare(s)                                  if V[s] >= SPLIT_PAGES (10)
         = rare(x) + 5 [plausible one-edit slip to x, first letter kept] or 8 [other slip] - 2 [doubled letter]   otherwise
         = rare(first word) + 1                     for a contraction typed without apostrophe ("hes" -> he's); "im" -> "i'm" as rare('i') + 1
total    = sum of piece costs + 3 per space
```

Pieces of 1-2 letters only from `SPLIT_SHORT_WORDS` (a, i, am, an, as, at, be, by, do, go, he, if, in, is, it, me, my, no, of, oh, ok,
on, or, so, to, up, us, we); at most 20 letters per piece. The split is used when
`total <= -4 + 1.5 * letters + 4 * spaces`, and, when `fix_word` could correct the word whole, also
`total + 4 < whole_cost`, with
`whole_cost = ln(max V) - ln(V[f]) - min(0.5 * ln(1 + E[f]), 3) + (5 | 8 | 10 for a non-single edit) - 2 [doubled]`.
Constants `SPLIT_*` (`SPLIT_COST` 3, `SPLIT_EDIT` 5, `SPLIT_EDIT_OTHER` 8, `SPLIT_DOUBLED` 2, `SPLIT_APOSTROPHE` 1, `SPLIT_EMERGENCY` 0.5 (max 3),
`SPLIT_SHORT` 1, `SPLIT_BASE` -4, `SPLIT_PER_LETTER` 1.5, `SPLIT_PER_SPACE` 4, `SPLIT_MARGIN` 4) were chosen on data (FORK.md 3k): 2,729 glued runs of 2-6 words from the
clean test questions and 1,157 from their typo versions, against 800 long words with one or two typos (must be corrected, not cut) and
800 real rare words of the index. Result at the chosen setting: clean runs cut right 94%, typo runs 79% (wrong 8%), long words with
typos cut 1%. The tuning scripts and their caches were in a session scratchpad and are not in `<drafts>` (not archived: not recorded).

How the other constants were chosen: `RARE` 20 and `GAIN` 50 come from the first prototype (`<drafts>/triage/typofix.py`: "a word on fewer than 20 pages,
a replacement at least 50 times as common"); `GAIN_INDEXED`, `EMERGENCY_MIN`, `MIN_PAGES`, `BODY_COMMON` (section 4): set while fixing
named failures ("riots" → "roots", "brunt" → "blunt", "puls"); no sweep is recorded.

Measured:

| Claim | Number | Source |
|---|---|---|
| Useful pages for typo questions, kw | 2.23 → 4.72 of 8 (hy 3.39 → 5.57); sections alone give 2.25 | `triage/COMPARE_rewrite.md`, `COMPARE_long_pages.md` |
| Clean questions changed | 0 of 253 (checked again at `c7795b5`: 0 of 253); typo questions changed: 100 of 109 now (FORK.md 3k says 99 at the time) | `<drafts>/triage/cases.py` through `typos.correct` |
| English words bent on independent lists | list 1: 35 → 0, list 2: 46 → 0 | `independent/RESULTS.md`, `independent2/RESULTS.md`; metric in `heldout-fixes/compare.py` (`bent`) |
| Typo lines "fixed" | list 1: 45 fixed / 15 wrong / 19 left → 71 / 6 / 2 (of 84) | `heldout-fixes/compare.py` (`typo_status`: the meaning restatement's content words, crude stem, against the typed and the corrected text; 6 lines settled by hand in `HAND`) |

---

## 4. Urgency by words

Code: `engine/confidence.py` (`URGENT`, `NOT_URGENT`, `urgent`, `not_urgent_text`, `BODY_WORDS`, `BODY_PHRASES`, `BODY_GLUED`,
`body_signs`, `body_match`) and `assistant.py` (`DANGER`, `danger_signs`, `is_danger`, `plea`).

```
not_urgent_text(t)   = t with every NOT_URGENT match (72 idiom alternatives) replaced by a space
urgent(*texts)       = any(URGENT.search(not_urgent_text(t)) for t in texts)  OR  body_signs(*texts) is non-empty
danger_signs(msg)    = {name of each of the 15 DANGER regexes found in not_urgent_text(msg).lower()}
is_danger(msg, english, meaning)
                     = danger_signs(msg + ' ' + english) non-empty
                       OR msg is one of the 5 danger-button labels (Not breathing, Heavy bleeding, Burn, Poison, Fire)
                       OR urgent(msg, typos.correct(msg), english)
                       OR meaning_red.check(typos.correct(msg) or msg)['fired']          (section 6)
turn_hits: info['danger'] = is_danger(...) OR plea(msg) [a bare "911"/"help"/"sos" as the first message]
```

- `URGENT`: one wide regex, about 275 top-level alternatives, whole-word stems (breath*, chok*, bleed*, fell, face, chest, pills,
  baby, car, help, ...), plus a second block of everyday wordings (out cold, keeled over, tablets, a whole box, crooked smile, can't
  lift an arm, worst headache, can't wake, ...). It is wide on purpose: a match only means the pages are never held back.
- `NOT_URGENT`: everyday idioms removed before the other rules look ("bleed the brakes", "blood orange", "a breath of fresh air",
  "drowning in emails", "heartbeat monitoring", "CPR certification"). Only the phrase goes: "bad breath and now he can't breathe" stays urgent.
- Body signs (`body_signs`): for each text, after idiom cutting, lower-cased: (a) any of the 9 `BODY_PHRASES` regexes (blue, unconscious,
  chest pain, not moving, seizure, cold and clammy, bleeding, pulse, breathing); (b) any alphabetic token that is one of the 23
  `BODY_WORDS`, or a slip for one (`body_match`: length 4+, the library has it on fewer than `BODY_COMMON` = 50 pages, not an English
  word unless itself a body word, same first letter, length within 1 (target of 6 letters or fewer) or 2 (longer), and either exactly one
  edit that is plausible, or two edits for a long target; the smallest edit count wins); (c) a glued run of 8+ letters the library does
  not hold that contains one of the 17 `BODY_GLUED` stems ("notbreath", "bleed", "chok", ...). Off with `LASTBOOK_BODY_SIGNS=0`.
- `assistant.DANGER` is the narrow list (15 signs: heart attack, passed out, not breathing, choking, unconscious, cpr, bleeding a lot,
  seizure, chest pain, on fire, smell gas, snake bit, poison, stuck in water, trapped). It decides conversation routing (section 7); the
  wide `URGENT` and the body signs decide whether pages may ever be withheld.

How they were chosen: written together with the 362-question set (`urgent` on 218 of 218 red questions, checked again at
`c7795b5`), the everyday-wording block and the idiom list added after independent list 1 as general patterns (not its sentences);
list 1 is therefore no longer blind. No fitted weights. The counts per category are in `<drafts>/urgent-mapping/RESULTS.md` section 1.

Measured (red recall, false flags): section 9, tables in section 10.

---

## 5. Confidence estimate

Code: `engine/confidence.py` (`MODELS`, `features`, `probability`, `estimate`, `unknown_words`, `thresholds`, `everyday_level`),
`assistant.py` (`search_confidence`, `chat_level`, `chat_reply`). Fit: `<drafts>/triage/` (`conf_eval.py`, `conf_fit.py`,
`conf_final.py`, outputs `conf_final.txt`, `conf_kw.json`, `conf_hy.json`; write-up `CONFIDENCE.md`).

Model: `p = 1 / (1 + exp(-(bias + sum_k w_k * x_k)))` on the raw (not standardised) signals; one set per mode.

| Signal | Definition (from `features`) | kw weight | hy weight |
|---|---|---|---|
| bias | | -3.6222 | -2.7284 |
| `cover1` | share of the query's word groups (a word with its synonyms) found as a whole word in the first hit's title + excerpt | 2.6573 | |
| `all1` | 1 if `cover1` is 1.0 | | 1.4529 |
| `title1` | the same share, in the first hit's title only | 2.3746 | 2.0129 |
| `kw_top_per_idf` | `-bm25 of the first keyword row / sum of the groups' idf`; `idf(group) = ln((N + 1) / (df + 1))`, `df` = pages of the group's commonest word, `N` = pages of the library's commonest term | 0.4326 | |
| `idf_mean` | mean of the groups' idf | 0.2656 | |
| `strict` | `ln(1 + rows that had every word)` | 0.0508 | 0.2002 |
| `emerg1` | 1 if the first hit's title matches `EMERGENCY_TITLE` (first aid, emergency care, resuscitation, where there is no doctor, emergency response guidebook, fire safety, are you ready, cert basic, emergency medic, life support, wilderness medic) and not `financial` | 0.8878 | 0.5764 |
| `cos1` | cosine of the best meaning passage | | 8.565 |
| `cos_drop` | `cos[0] - cos[min(7, n - 1)]` | | -12.2606 |
| `overlap` | keys shared by the keyword and meaning top 8, divided by 8 | | 1.1072 |
| `docs` | distinct documents in the top 8, divided by 8 | | -3.2324 |

Cuts (`confidence.py`, overridable by `LASTBOOK_CONF_BUTTONS`, `_UNSURE`, `_BUTTONS_EVERYDAY`; `LASTBOOK_CONF=0` turns all off):

```
level        = 'unsure' if p < UNSURE (0.25) ; 'buttons' if p < BUTTONS (0.60) ; else 'sure'
everyday q   = not is_danger(...):  'unsure' if p < min(0.25, 0.30) ; 'buttons' if p < EVERYDAY_BUTTONS (0.30) ; else 'sure'
unknown_words(q as searched): no content word, or more than half of the content words are neither on 3+ library pages nor English
             -> p = min(p, max(0, min(0.25, 0.30) - 0.05)) = min(p, 0.20), p_fitted kept, 'unknown_words': True
```

`assistant.chat_level` then adjusts: inside a conversation (route not first/danger) 'unsure' becomes 'buttons'; a body sign or an
urgent question (with words that are the library's) is never only asked, it is answered with buttons; a bare plea is asked what is happening.
Pages are never withheld (`chat_reply`: 'ask+pages', 'ask (nothing found)').

**How it was fit.** Data: `cases.py`, 362 questions (253 clean + 109 typo versions, 159 topics), top 8 of `assistant.hybrid`
(`conf_eval.py`, in-process, read-only), label `first_ok` from `score.py` (section 9). kw: `retrieval.AVAILABLE = False`; hy: 337,016
passages. Candidate signals were screened by single-signal AUC and greedy forward selection (`conf_fit.py`, 4 repeats, optimistic); the final
signal sets are fixed by hand in `conf_final.py` (`SETS`). Model: `StandardScaler` then `LogisticRegression(C=0.3, L2, max_iter=2000)`;
cross-validation: `GroupKFold(5, shuffle=True, random_state=rep)` grouped by topic (a topic's clean and typo questions in the same fold),
20 repeats. The final coefficients are a refit on all 362 questions, mapped back to raw signals (`raw()`: `w / scale`, `bias - sum(w * mean / scale)`),
and `conf_final.py` asserts they reproduce the scikit-learn probabilities to 1e-3. The values in `confidence.py` equal the printed
`raw coefficients` in `conf_final.txt` for both modes.

**AUC and how it is computed.** `roc_auc_score(first_ok, p)` where `p` is the out-of-fold probability of one repeat; reported as the mean over the
20 repeats, and also on the average of the 20 out-of-fold vectors:

| | kw | hy |
|---|---|---|
| base rate of first right | 60% | 76% |
| AUC, mean of 20 repeats (sd) | 0.775 (0.008) | 0.737 (0.016) |
| AUC, averaged out-of-fold | 0.778 | 0.743 |
| red only / clean / typos (averaged) | 0.754 / 0.770 / 0.795 | 0.697 / 0.764 / 0.702 |
| same model vs "a useful page in the top 8" | 0.720 | 0.815 |
| Brier (base rate alone) | 0.187 (0.241) | 0.159 (0.181) |
| in-sample AUC | 0.801 | 0.791 |

The summary's 0.78 / 0.74 are these rounded. Calibration, out-of-fold, bands 0-25 / 25-50 / 50-75 / 75-100 (n, mean predicted, actual first right):
kw 25, .21, .20 / 107, .37, .36 / 113, .62, .65 / 117, .87, .85; hy 1, .23, 1.0 / 26, .41, .46 / 139, .65, .62 / 196, .89, .90.
Inside conversations the same model ranks poorly (AUC 0.43-0.71 in `conf_final.txt`), which is why a conversation only gets buttons.

How the cuts were chosen: 0.60 buttons: first set at 0.75 (`CONFIDENCE.md`: buttons on 68% of kw questions, 116 false alarms against
17 slips) and moved to 0.60 by the project owner's decision (buttons on 43% of kw questions with the final model; 50%, 70 false alarms and 34 slips with the model of the time); 0.25 "help me help you": the value
asked for, at which kw has 7% of questions below and 5 of 216 right first pages (3 red) caught, and every red one still gets its pages; 0.30 everyday:
the lowest cut at which anything is caught among the 51 everyday questions (`conf_everyday.py`: "how to build a root cellar", "tooth nocked out"),
0.35 adds two right first pages. A model fitted for "one of the first 3 is right" was tried and dropped (`conf_top3.py`: it lets 2-4 times as many
searches whose first 3 pages are all wrong through at the same cut).

Rerun: `conf_eval.py OUT.json` (kw with `TH_KW=1`, hy without) then `conf_final.py conf_kw.json conf_hy.json > conf_final.txt`
(needs scikit-learn; `GroupKFold(shuffle=True)` needs a recent version, 1.9.1 was used to check). Caveat: `conf_eval.py` calls
`confidence.features(hits, tr, danger)` with three arguments, the signature of the code it was written for (worktree
`search-confidence`); at `c7795b5` `features(hits, trace)` takes two, so `conf_eval.py` must be run against that worktree's commit or edited.
`conf_final.py` itself only reads the stored JSON.

---

## 6. Meaning check

Code: `engine/meaning_red.py` (`Embedder`, `Model.score`, `check`, `find`, `fetch`), builder `tools/meaning_red_model.py`, examples
`engine/data/meaning_red_examples.jsonl`, manifest `engine/data/meaning_red_manifest.json`, runner mode `packaging/llm/lastbook_llm.cpp --embed`.

```
text   = typos.correct(question) or question          (cut at 2,000 characters)
v      = embedding of text: bge-small-en-v1.5, q8_0 GGUF, [CLS] pooling, unit length, max 320 tokens, NO query prefix
score  = max_r cos(v, c_r) - max_n cos(v, c_n)        r over 20 red centroids, n over 11 non-red centroids (v and c are unit vectors: cos = dot)
fired  = score > wide                                  wide = 0.00836634635925293 (about 0.00837); strict = 0.03168658415476481 is stored, not used
urgent = words OR fired                                (only adds; any failure leaves the words alone)
```

- Examples (`meaning_red_examples.jsonl`, 689 sentences, invented from general knowledge before any test list was opened):
  315 red in 20 categories, 144 yellow (one category), 230 green look-alikes in 10 categories. Red: anaphylaxis 12, bleeding 25, burns 15,
  chest_pain 16, child_baby_elderly 15, childbirth 12, choking 14, diabetic 7, drowning 10, head_spine 16, non_native_slang 16, not_breathing 27,
  overdose_poisoning 29, seizure 12, sepsis 7, stroke 15, suicide 18, temperature 11, trauma_other 18, unconscious 20. Green: cooking_home 25,
  course_question 30, everyday_howto 25, figurative_dark_humour 10, idiom 30, lookalike_words 30, mild_symptom 25, nonsense_noise 10,
  sport_game 20, tech 25. Non-red centroids = those 10 green categories plus yellow = 11.
- Centroids: each example goes through `typos.correct`, is embedded through the runner (64 to a request), and the unit mean per category
  is taken, then renormalised; stored as float32 `red` (20 x 384) and `nonred` (11 x 384) in `centroids.npz` with the two thresholds.
  Rebuilding gives identical arrays (checked: max difference 0.0 against the stored file), since the file is written with fixed zip times.
- Thresholds, defined on the examples only (`tools/meaning_red_model.py:cv_thresholds`): 5-fold stratified by category (`StratifiedKFold(5,
  shuffle=True, random_state=rep)`, labels = the category), 3 repeats (rep 0, 1, 2); in each fold the centroids come from the training part only and
  the held-out part is scored; an example's out-of-fold score is the mean of its 3 held-out scores. With `g` = the 230 green examples' scores sorted
  descending, `threshold(b) = g[floor(b * 230)]`: strict b = 0.05 (index 11), wide b = 0.10 (index 23). So "10% of green examples fall above wide" and "5% above
  strict". The values are written into `THRESHOLDS` (not recomputed by a normal build; `--cv` prints the recomputed ones). Checked again: `--cv`'s
  procedure returns exactly 0.03168658415476481 and 0.00836634635925293.
- Out-of-fold on the examples (rechecked): at wide, red recall 89.5%, green flagged 10.0%, yellow flagged 28.5%; at strict, red 80.3%, green 4.8%, yellow 16.0%
  (`LLAMACPP_STATS.md` section 1). In-sample: wide flags 301/315 red, 42/144 yellow, 18/230 green; strict 285 / 22 / 9.
- Choice of method (`<drafts>/meaning/cv.py`, `cv_results.json`, `RESULTS.md` Phase B): 12 scorers, each with and without bge's query prefix, same 5 x 3
  stratified cross-validation, red recall at 5% / 10% green false flags: kNN vote best 0.73 / 0.86; per-category centroids 0.81 / 0.90 (chosen);
  one red against one non-red centroid 0.65 / 0.82; logistic regression 0.64 / 0.84; every method with the prefix is 0.07-0.12 lower.
- Model file: `bge-small-en-v1.5-q8_0.gguf` made by `convert_hf_to_gguf.py --outtype q8_0` from the llama.cpp tag the runner is built from (b12032,
  dde879bc), 36,688,256 bytes; `centroids.npz` 51,434 bytes. Sizes and SHA-256 are in the manifest and were checked against the stored files again
  (match). Runner: `--embed --cpu-only --threads 2`; one JSON line per request (`{"op":"embed","id":n,"texts":[...],"max_tokens":320}`).
- Thresholds in older prototypes, for reading the old write-ups: ONNX fp32 prototype strict 0.0304 / wide 0.0080 (`meaning/RESULTS.md`); int8 ONNX
  branch (`51c7a4f`) wide 0.00663; the shipped GGUF 0.0317 / 0.00837. Lists 1-3 below use the shipped GGUF.

Held-out result (`meaning/LLAMACPP_STATS.md`, script `llamacpp_stats.py`, words = `confidence.urgent(q, typos.correct(q))` at `9bd116e`); counts red / yellow / green
flagged, green = counterexamples + mild lines:

| | list 1 (343/104/243) | list 2 (249/111/246) | list 3 (199/78/254) |
|---|---|---|---|
| words only | 340 / 98 / 76 | 230 / 85 / 127 | 173 / 55 / 154 |
| meaning only, wide | 297 / 56 / 60 | 210 / 53 / 62 | 162 / 35 / 75 |
| words OR meaning, wide (shipped) | 341 / 100 / 104 | 243 / 93 / 147 | 188 / 62 / 173 |
| red recall of words OR meaning | 99.4% | 97.6% | 94.5% |
| undertriage of words OR meaning | 0.6% | 2.4% | 5.5% |
| green flagged by words OR meaning | 42.8% | 59.8% | 68.1% |
| counterexamples flagged by words OR meaning | 39/128 (30%) | 95/135 (70%) | 110/147 (75%) |

Red caught only by meaning: 1, 13, 15. No red line the words flag stops being flagged (in-sample sets and lists). Speed through the pipe: median 5.2 ms,
p95 8.9 ms, max 24.5 ms over 2,342 lines (a busier run later: median 9 ms, p95 13 ms); the runner uses 66 MB private memory and loads in 0.2 s.

---

## 7. Conversation handling

Code: `assistant.turn_hits` (routes), `classify`, `is_noise`, `stock_noise`, `plea`, `danger_signs`, `followup_hits`, `cited_before`.
No model is used. The newest user message is classified against the earlier ones:

| Route | When | What is searched |
|---|---|---|
| `first` | one user message, or no earlier message that is not noise | its own search |
| `noise` | `is_noise(msg)` | no new search: the last sensible message's results again (`turn_hits` on the conversation up to it), plus buttons. With nothing sensible before it: its own search, buttons and a request for more words |
| `correct` | `CORRECT.search(msg)`: starts with "no" (repeated), or contains "i mean(t)", "not that", "that's not", "wrong one", "not me/him/her", "instead" | correction words stripped (`CORRECT_STRIP`); own search; the earlier message's search; pages shown last time (cited before, plus the earlier message's own search) go to the end; no carried pages |
| `danger` | `danger_signs(new message + English words)` has a sign none of the earlier non-noise messages had, or the message is a danger-button label | own best 5, then the joined search (earlier + new message), then the rest; no carried pages |
| `follow` | everything else | pages the previous answer cited (`cited_before`, up to 3), own best 4, the joined search, the rest, up to 8 (`followup_hits`) |

`is_noise(msg)`: true if `stock_noise` (a full-match of `NOISE_PHRASE`: sorry/wrong chat/ignore that/never mind/nvm/oops/lol/ok/k/wait/hm/test; or no
letters at all), or, unless the message is a danger button, needs English words, or names a body sign: fewer than half its words are known, both as typed and
after `typos.correct`. A word is known if it is in the short stop list, a contraction typed without apostrophe, ordinary English, on 20+ library pages, or
one edit from such a library word (words under 3 letters only from the stop list or the library).

How it was measured: 52 invented conversations (`triage/convos.py`: 14 follow-up, 19 addition, 14 correction, 5 new emergency; 12 contain a noise message),
scored on the last message with `score.py` (first result right). The "before" is the fork's earlier follow-up search (`mt_oldfork.py` over HTTP, `results_mt_oldfork.json`;
also `MULTITURN.md`): hy corrections 29% (4 of 14), new emergencies 0% (0 of 5). The "after" is `assistant.turn_hits` itself, in-process, with replies that cite the
previous turn's top 3 PDF pages (`turnhits_eval.py`, output `turnhits_hybrid.txt`): 57% (8 of 14) and 80% (4 of 5); overall 56% → 64%. The two paths differ (HTTP on the
full library against in-process on the test copy), and the group sizes are 14 and 5. The classifier was written alongside these cases (noise 11 of 12, corrections 14 of 14,
new emergencies found only through the danger-sign words, 5 of 5), so its accuracy there is optimistic.

---

## 8. Everyday phrases that hijack injury questions (summary's last problem row)

Code: `server.PHRASES` (how-to phrases "start/make/light a fire", "make the water safe", marked `HOWTO`), `server.query_groups`, `confidence.INJURY`,
`confidence.injury(q)`. A HOWTO phrase is skipped when the question matches `INJURY` (breathing, choking, unconscious, bleeding, wound, drowning, lungs,
inhaled, shock, burnt, scald, blisters, poison, swallowed, overdose, hypothermia, seizure, injured, hurt, fell, on fire, ...) or the phrase's own
exception regex. `LASTBOOK_PHRASE_INJURY=0` turns it off. A retry without the phrase's helper words was measured and left off by default
(`LASTBOOK_PHRASE_RETRY=1`): it lost "start a fire with no matches and no gas" (7 → 2 useful).

Measured (`triage/AB_PHRASES.md`, `ab_phrases_run.py`, kw): #154's useful count 144 → 168 of 256 (typos 152 → 169); "treat water in the lungs after drowning" 0 → 4 useful
pages of 8; `cases.py` first right 150 → 153, top 3 199 → 204. #154's count = for each of its 32 questions, the number of top-8 pages whose title + excerpt matches that
question's own topic regex (`cases154.py`), summed (32 x 8 = 256 possible).

---

## 9. Measures used in the summary

All scored on the first 8 results of `assistant.hybrid` (what `/api/retrieve` and the chat's first search return), as `title + ' ' + excerpt`,
case-insensitive, unless said.

| Measure | Definition | Computed by |
|---|---|---|
| need / useful page | each test case lists `need`, pattern keys into the table `P` of `cases.py` (regexes such as `CPR`, `CHOKE`, `BLEED`; the words a useful page must contain), most urgent first. A hit is useful if it matches any of the case's needs. `useful` = number of useful hits of 8 | `triage/score.py:score` |
| first useful (library) | `first_ok`: the first hit matches `need[0]` and is not a "wrong sense" (for a counterexample the first hit matches a `not_first` pattern and no need) | `score.py:score` |
| first useful (encyclopedias) | the first article's excerpt + title matches any of the case's needs (patterns joined with `|`) | `evanesced/encyclopedias-3n/compare.py` |
| any of top N | `top3_ok` = any of hits 1-3 matches any need (the per-hit rule that counts `useful`); encyclopedias: any of the 3 articles | `triage/conf_top3.py`, `run_sets.py`, `compare.py` (evanesced) |
| covered | every need appears somewhere in the top 8 | `score.py` |
| no useful page | `useful == 0` | `score.py` (`zero_useful`) |
| #154 useful count | section 8 | `triage/analyze154.py`, `ab_phrases_analyze.py` |
| topic cap broken | more than half the top 8 match only the question's setting (`context`) and no need | `score.py` |
| red recall | share of lines labelled red for which `assistant.is_danger` is true (words, or words OR meaning where stated) | `heldout-fixes/compare.py:heldout`; lists 3-4: `analyze3.py`, `analyze4.py` |
| undertriage | `1 - red recall` | derived |
| overtriage | share of green lines (counterexamples + mild + the rest of green) with `is_danger` true; counterexamples and mild reported separately; yellow reported on its own and not counted as green | `compare.py:heldout` |
| pages shown / withheld | `pages_shown = action not in {ask, ask (danger, nothing found), ask (nothing found)} and hits non-empty`; "bare ask" = action `ask` (no answer, pages only as consulted); "ask+pages" = pages but no answer. After the fixes the request to say more always comes with pages | `indep_eval.py`, `eval2.py`-`eval4.py` (field `pages_shown`, `action`) via `assistant.chat_reply` |
| emergency book | `confidence._emergency_book(hit)`: the title matches `EMERGENCY_TITLE` and not `financial`. Rough: many good health pages come from books it does not count | `confidence.py`, fields `first_emergency`, `top3_emergency` in the eval scripts |
| body sign found | `confidence.body_signs(text, corrected)` non-empty; "covered" lines are those whose labelled `signs` fall in the 10 categories of `compare.py:CAT` | `compare.py` |
| English word bent | the typed word is in the English list and the corrector changed it (not a split, not an apostrophe repair) | `compare.py:heldout` (`bent`) |
| AUC | `sklearn.metrics.roc_auc_score` of the label against the score: confidence (section 5, label `first_ok`); meaning score red vs green (prototype `meaning/evaluate.py`: 0.88 on lists 1 and 2; on the examples out of fold 0.96) | `conf_final.py`, `meaning/evaluate.py` |
| triage targets | undertriage under 5%; overtriage 25–35% acceptable, the American College of Surgeons Committee on Trauma's figures for trauma field triage [1]. Used as a reference, not a requirement: their overtriage ceiling exists because sending a patient to a trauma centre spends scarce, expensive hospital resources, while a false alarm here costs only pages shown anyway and a row of buttons, and the rules are cheap to change and remeasure. So undertriage is held to their target and overtriage may run higher | the summary, "Why" |
| #167 mapping | lines flagged by (a) the 5 phrases in the tree, (b) the 117 proposed phrases matched like `web/words.js` (a Python port checked against Node: 0 disagreements over 2,189 lines), (c) `danger_signs(t) or urgent(t, typos.correct(t))` (no meaning model), (d) b or c. The 2,189 lines = 690 + 606 + 531 (the three lists) + 362 (triage). Red 1,009 (343 + 249 + 199 + 218), yellow 367, green 813; rates 3% / 16% / 95% red, 0 / 2% / 81% yellow, 1% / 10% / 49% green | `urgent-mapping/measure.py` (needs the `regex` module), `measure_out.json` |

---

## 10. Test data

| Set | Size | Where | Labels |
|---|---|---|---|
| Triage set | 362 questions over 159 topics (67 red, 36 yellow, 56 green topics): 253 clean (131 red, 58 yellow, 44 green, of which 22 counterexamples: 20 green and 2 yellow), 109 typo versions (87 red, 16 yellow, 6 green) | `<drafts>/triage/cases.py` | colour by topic; `need`, `context`, `not_first` regexes written with the questions |
| #128's | 52 (including its reviewer's counterexamples) | `triage/cases128.py` | same format |
| #154's | 32 (+ 32 typo versions) | `triage/cases154.py` | blind labels written afterwards: 13 red, 11 yellow, 8 green; #154's own useful count |
| #241's | 21 | `triage/cases241.py` | same |
| Glued and gibberish | 48 | `triage/cases_glued.py` | the words each glued question was typed for |
| Conversations | 52 (14 follow-up, 19 addition, 14 correction, 5 new emergency) | `triage/convos.py` | what each last message is to the conversation |
| In-sample total used in `meaning/` | 273 red, 94 yellow, 148 green (the five case files above) | | |
| Independent list 1 | 690: 343 red / 104 yellow / 243 green; 128 counterexamples; 355 "web-inspired", 335 invented | `<drafts>/independent/phrases.jsonl` | `triage` (red/yellow/green), `meaning`, `signs`, `kind`, `persona`, `source` per line |
| Independent list 2 | 606: 249 / 111 / 246; 135 counterexamples, 109 mild; 126 web-inspired | `independent2/phrases.jsonl` | same |
| Independent list 3 | 531: 199 / 78 / 254; 147 counterexamples, 114 mild; 92 personas; 53 web-inspired | `independent3/phrases.jsonl` | same |
| Independent list 4 | 832: 115 red / 153 yellow / 564 green (467 counterexamples); 300 English, 525 Spanish, 7 unclear | `independent4/phrases_mixed.jsonl` (counts only used here) | Qwen3.5-9B's own labels (run locally) |
| Meaning examples | 689 (315 red, 144 yellow, 230 green) | `engine/data/meaning_red_examples.jsonl`, source `meaning/make_examples.py` | label and category |

How the lists were made. Lists 1-3: written by an AI agent in a fresh session told not to open any project file, asked for lines labelled by urgency as an emergency nurse
would on a phone triage line, with typos, glued words, slang, non-native English, voice dictation, emergencies buried in small talk, misconceptions, personas, and 128-147
counterexamples; list 3 was not read by anyone before both runs finished. The prompts for lists 1-3 were not saved (not recorded); `independent4/PROMPTS.md` holds three
prompts of the same design (serious and well-written / messy / multilingual), written to be given to a different model family. List 4 was generated from them by Qwen3.5-9B,
run locally (not the model family that wrote lists 1-3), over one night; how many of the three prompts were used is not recorded, and the output came back as a single log
(`independent4/raw/`, escaped and partly HTML-escaped), which `recover.py` turned into the 832 lines (`recover_report.json`, `rejected_mixed.txt`). It is narrow: 147 English lines
are one template, 525 are Spanish idioms; read `independent4/RESULTS.md` before using it. The results of lists 1-3 are in each folder's `RESULTS.md` and `results.json`.
The meaning examples were written first, from general knowledge, before any list was opened.

Which commits each list's numbers come from: list 1 before the held-out fixes `4ea2d9f`; after `19c2db2` (fork/heldout-fixes); list 2 before `4ea2d9f`, after `19c2db2`;
list 3 words `9bd116e`, words OR int8 meaning `51c7a4f`; lists 1-3 with the shipped GGUF meaning check: `meaning/llamacpp_stats.py` over the same texts; list 4 `bc4c782` (its `english_kw` run redone at `c7795b5`, after the English-words fix: Spanish red 43 → 44 of 45; `independent4/RESULTS.md`, "After the fix").
Each can be checked out with `git worktree add <dir> <commit>` and run with `LASTBOOK_CODE=<dir>`.

---

## 11. How to reproduce

**Data folder.** The runs read `<LastbookData>`, a local copy of upstream's Medium library pack (`pack.json`: `name` "medium", built 2026-11-12,
`setup-pack.json`: `Lastbook-Medium.zip`; 3 ZIM files for the encyclopedias, 138,547 rows in `library-data/search.sqlite`). It is read, never written: the scripts refuse the sections build
(`sections.build` replaced by a function that raises), open the index and the meaning vectors read-only and never truncate `vectors.f16`. The first search builds
`derived/index/sections-*.sqlite` if absent; in a copy that already has it nothing is written. `docs/FORK.md` does not say which pack the copy is; `pack.json` is the source for
"Medium". The "full library" runs of the first baseline (`triage/RESULTS.md`, `COMPARE_*`) used a second copy of the same pack with 337,016 meaning passages.

**Environment variables used by the scripts**

| Variable | Meaning |
|---|---|
| `LASTBOOK_DATA` | the data folder (required by every in-process script) |
| `LASTBOOK_CODE` | the code checkout or worktree under test (`conf_eval.py`, `run_sets.py`, `run154.py`, `eval*.py`, `heldout_eval.py`, `body_eval.py`, ...) |
| `TH_KW=1` | keyword-only (`retrieval.AVAILABLE = False`); absent = hybrid |
| `EN=1` | list 4 only: search and label each line with the English words of `independent4/english.json`; `EN=0` as typed |
| `LASTBOOK_LOCAL_AI` | removed by the eval scripts (no model); `english4.py` sets it to 1 to make the English words with the local model |
| `LASTBOOK_MEANING_RED=0` | meaning check off (words only); on by default when the files and the runner are present |
| `LASTBOOK_TYPO_FIX`, `_TYPO_SPLIT`, `_TYPO_ENGLISH`, `_BODY_FIX`, `_BODY_SIGNS` | `0` turns that part off (A/B arms) |
| `LASTBOOK_CONF`, `_CONF_BUTTONS`, `_CONF_UNSURE`, `_CONF_BUTTONS_EVERYDAY`, `_CONF_UNKNOWN`, `_CONF_URGENT_ANSWER` | confidence switches and cuts |
| `LASTBOOK_PHRASE_INJURY`, `LASTBOOK_PHRASE_RETRY` | section 8 arms |
| `LASTBOOK_WIKI_PICK=0` | encyclopedias as upstream; `LASTBOOK_WIKI_VECTORS=1` the dev vector index |

**Commands** (Windows, from `<repo>`; each script writes where its first argument says). The scripts in `<drafts>/triage/` import each other, so run them from or with
that folder on `sys.path`.

```
# triage set (362), top 8 + scoring, in process
set LASTBOOK_DATA=<LastbookData>  &  set LASTBOOK_CODE=<repo or worktree>  [& set TH_KW=1]
python -B -X utf8 <drafts>/triage/conf_eval.py OUT.json          # needs the commit of the 3-argument features() (section 5)
python -B -X utf8 <drafts>/triage/run_sets.py OUT.json cases128 cases241
python -B -X utf8 <drafts>/triage/run154.py OUT.json             # then analyze154.py
python -B -X utf8 <drafts>/triage/ab_phrases_run.py OUT.json     # then ab_phrases_analyze.py
python -B -X utf8 <drafts>/triage/turnhits_eval.py <drafts>/triage    # 52 conversations
python -I -X utf8 <drafts>/triage/compare.py SEARCH_DB OUT.md RESULTS.json:name=label,...
# over HTTP instead: kwserver.py serves keyword-only; then
python -I <drafts>/triage/score.py OUT.json keyword=http://127.0.0.1:PORT hybrid=http://127.0.0.1:PORT2

# confidence fit
python -B -X utf8 <drafts>/triage/conf_final.py conf_kw.json conf_hy.json > conf_final.txt

# independent lists (one run per mode, then the analyser)
python -B -X utf8 <drafts>/independent/indep_eval.py OUT.json    # list 1; analysis indep_analyze.py, indep_report.py
python -B -X utf8 <drafts>/independent2/eval2.py OUT.json        # analyze2.py   (before/after: two checkouts)
python -B -X utf8 <drafts>/independent3/eval3.py OUT.json        # analyze3.py   (words vs words OR meaning: two checkouts)
set EN=1 & python -B -X utf8 <drafts>/independent4/eval4.py OUT.json   # also EN=0; analyze4.py; english4.py makes english.json

# meaning check
python -X utf8 tools/meaning_red_model.py --cv --out <scratch folder>   # rebuilds the two files (default --out overwrites derived/models/meaning-red) and prints the recomputed thresholds
python -X utf8 <drafts>/meaning/llamacpp_stats.py                # GGUF against int8, lists 1-3, speed (paths to the scratch runner inside)
python -B <drafts>/urgent-mapping/measure.py                     # #167 mapping, writes measure_out.json

# encyclopedias
python docs/evanesced/encyclopedias-3n/compare.py                # also measure.py, floor.py
```

Traps: `heldout-fixes/compare.py` reads the English word list from a worktree path hard-coded in line 8 (use `engine/english_words.txt.gz`); the eval scripts
for lists 3-4 need the meaning files in `derived/models/meaning-red/` and the runner (`derived/llm/bin-*/lastbook-llm`) with `--embed`; `tools/meaning_red_model.py`
also needs the Hugging Face copy of bge-small-en-v1.5 and a llama.cpp checkout at tag b12032; the `LASTBOOK_DATA` library's words are what `typos.correct` uses,
so a different pack changes the corrected text slightly; the keyword results do not depend on a model, the hybrid ones need the pack's meaning index.

---

## 12. Where the summary or FORK.md disagree with the code or the stored output, and what is not recorded

Disagreements (the code or stored output is taken as right):

1. "353 saved web pages ... 26 → 4": 353 and 7,634 sections are `COMPARE_long_pages.md`'s figures from before the one-page-per-document rule; the code now builds 351 pages and 7,623 sections
   (FORK.md 3k says 351). "26 → 4" is `COMPARE_rewrite.md` (sections + typos + conversation); sections alone are 26 → 1 (hy) and 25 → 6 (kw).
2. "hybrid search on those pages 4.95 s → 0.68 s": no stored output has it (0.68 s is about the mean time per question over the whole 362-question set).
3. "Corrections first-right 29% → 57%, new emergencies 0% → 80%": the before and after come from two different measurement paths (section 7) and groups of 14 and 5.
4. "Fixes were built against list 1, checked on list 2": later changes (the slang and brand words in `EXTRA_ENGLISH`, the contraction list) came from list 2, which FORK.md 3k says is no
   longer blind; the 92% on list 2 is the `19c2db2` figure, before that.
5. "60-75% of counterexamples on lists 2 and 3 are flagged by words + meaning": the stored numbers are 70% (95 of 135) and 75% (110 of 147); 61% / 69% is the words alone.
6. "5-9 ms per question" (meaning check): `LLAMACPP_STATS.md` gives a median of 5.2 ms and p95 8.9 ms; FORK.md 3m says 5-11 ms (median 9 ms and p95 13 ms on a busier machine).
7. "the runner gained an --embed mode, about 90 lines": `git show --stat 8c782c5` is +101 / -13 (net +88); FORK.md says +97.
8. "A fourth list ... is being written": its results exist (`independent4/RESULTS.md`, 2026-11-21): Qwen3.5-9B's 832 lines, narrow (section 10), run at `bc4c782`, before the commit
   `c7795b5` ("English search words must be mostly English words, else asked once more"), which looks like the fix for the untranslated words its results list; its `english_*`
   runs have not been redone (not recorded).
9. "99 of 109 typo questions changed" (FORK.md 3k): 100 now. "AUC 0.45-0.65 inside a conversation" (FORK.md 3l): `conf_final.txt` has 0.43 to 0.71.
10. FORK.md says nothing about which pack the test data folder is; `pack.json` says Medium (section 11).
11. `CONFIDENCE.md`'s recommendation (75 / 25) is superseded in the same file by 0.60 / 0.25 and the everyday cut 0.30; the code has the latter.
12. `confidence.py`'s docstring points to `conf_final.py` for the fit: it is in `<drafts>/triage/` (untracked); `conf_eval.py` there no longer matches `features()` (section 5).

Not recorded or not determinable:

- The prompts and the exact instructions given to the agents that wrote lists 1-3.
- Any sweep for `LONG`, `SECTION`, `PER_FILE`, `MAX_BYTES`, `STEM`, `TITLE_WEIGHT`, `RARE`, `GAIN`, `GAIN_INDEXED`, `EMERGENCY_MIN`, `MIN_PAGES`, `BODY_COMMON`; and the scripts that tuned the `SPLIT_*` costs (session scratchpad, not archived).
- The 4.4 MB size of the largest saved web page (not re-measured; the largest single row over 20,000 characters in `search.sqlite` is 9.4 MB, which includes non-web pages).
- Timings of the "before" encyclopedia, library and meaning runs on a machine other than the author's PC (a Ryzen 7 5800X3D desktop) were not taken.
- The live tests with a local Gemma model: logs exist locally (`<drafts>/live-test*.log`) and are not meant to be shared; they are qualitative, with no counted outcome.

## 13. How the summary's preface counts were made (2026-11-22, the eight staged branches against `main` `9645686`)

Counted on what is proposed, part by part (`git diff --numstat` from each branch to the next, `triage/1-search-eval`
… `triage/8-conversation`), not on the fork, which also holds code that is not proposed.

| Part | Code (+/-) | Tests (+lines, `def test_`) | New modules |
|---|---|---|---|
| 1 test set and scorer | +347 | 0 | `tools/search_eval/score.py` |
| 2 sections | +438 / -55 | +231, 8 | `engine/sections.py` |
| 3 typos | +755 / -5 | +389, 33 | `engine/typos.py`, `tools/english_words.py` |
| 4 encyclopedias | +185 / -29 | +128, 12 | `engine/wiki_pick.py` |
| 5 confidence | +629 / -20 | +650, 43 | `engine/confidence.py` |
| 6 runner `--embed` | +104 / -12 | 0 | (C++ only) |
| 7 urgency | +806 / -27 | +871, 61 | `engine/meaning_red.py`, `engine/urgent_phrases.py`, `tools/meaning_red_model.py` |
| 8 conversation | +574 / -80 | +574, 48 | |
| **All** | **+3,838 / -228** | **+2,843, 205** | |

- **About 3,800 lines of code:** Python, JavaScript, CSS, C++, shell, the macOS spec and HTML outside `app/tests/`
  (HTML is only version bumps). Not counted: tests, docs (+877), data (+10,054: the test set's question files, the
  English word list's licence, the guides' `urgent` phrases, the meaning check's 689 example sentences).
- **6 sub-modules:** `engine/sections.py`, `typos.py`, `wiki_pick.py`, `confidence.py`, `meaning_red.py`,
  `urgent_phrases.py`, plus the runner's `--embed` mode and three tools (the scorer, the word-list builder, the meaning
  check's centroid builder).
- **About 200 tests:** 205 `def test_` functions added in `app/tests/` (some run Node checks of `web/chat.js` and
  `web/words.js`). Separate from the measured test sets (section 10).
- The earlier count (2026-11-21: about 3,500 lines, 6 sub-modules, about 150 tests) was made on the fork's merged
  changes and included `wiki_vectors.py`, which is not proposed.

## Sources

1. American College of Surgeons Committee on Trauma, *Resources for Optimal Care of the Injured Patient* (2014),
   chapter 3, p. 28. https://www.rumcsi.org/wp-content/uploads/2020/09/Resources-for-Optimal-Care-2014-v11-1.pdf
