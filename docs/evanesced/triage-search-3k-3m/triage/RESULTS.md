# Triage test set: first run (2026-11-18)

Baseline: upstream `main` at 256d52f, full library (7,808 documents), top 8 of `/api/retrieve`.
Keyword-only = meaning-based search switched off (`kwserver.py`); hybrid = keyword + bge-small (337,016 passages).

## The set (`cases.py`)

- **159 topics, 362 questions:** 253 clean, of which 22 are counterexamples, plus 109 typo variants.
- **Colours:** 67 red topics, 36 yellow, 56 green. Red covers ABCDE emergencies, poisoning, birth, fire, gas,
  disasters happening now, and a little security (active shooter, intruder, explosion).
- **Green includes firefighting how-tos:** extinguisher, smoke and CO alarms, escape plan, defensible space, generator.
- **Counterexamples** use emergency words in their everyday sense: an engine that chokes, bleeding brakes, a dead
  battery, shock absorbers, an electric fence, smoking fish, a burn barrel, drowning tomato plants.
- Each question lists what it **needs** (most urgent first) and its **context**, the setting words such as the flood
  around the wire. All situations are invented.

## Scores (`score.py`)

| | Keyword-only | Hybrid |
|---|---|---|
| **Red:** first result matches the urgent need | 44% | 67% |
| **Red:** useful pages in the top 8 (mean) | 3.9 | 5.1 |
| **Red:** questions with no useful page | **27 of 131** | 5 of 131 |
| **Red:** every need covered (two-part questions) | 68% | 87% |
| Yellow: first result right | 70% | 73% |
| Green: first result right | 82% | 84% |
| Counterexamples: first result right | 64% | 73% |
| Counterexamples: first result in the wrong (emergency) sense | 4 | 2 |
| Topic cap broken (over half the top 8 are setting only) | 4 | 3 |

What it shows:
- **Red is the worst colour, not the best.** Search does worst exactly where it matters most. Without the model (what
  most installs have), 1 in 5 red questions finds nothing useful at all.
- **The scorer is strict.** About 13 red "misses" on each setup have a first-aid book first (*Basic Emergency Care*,
  *First Aid*) whose excerpt doesn't contain the matched words. So the real red rates are a few points higher. The
  ranking, not the scorer, is the main problem.
- **One document matches everything.** *Modern Machine-Shop Practice* (p.None) is in the top 8 of 25 questions on
  keyword-only and 26 on hybrid, all unrelated: amputation, stroke, grease fire, birth. It looks like a whole-book page
  that matches any word. Worth its own fix.

## Typos

Typos were typed the way a panicking person types: dropped and doubled letters, missing apostrophes, sound-alikes.

| | Keyword-only | Hybrid |
|---|---|---|
| Clean questions, same topics: useful / first right | 4.13 / 50% | 5.34 / 71% |
| **With typos** | 2.23 / 28% | 3.39 / 45% |
| Typo questions with no useful page | **54 of 109** | 23 of 109 |
| **Typos corrected first (`typofix.py`)** | **4.16 / 53%** | **5.23 / 72%** |
| Typo questions with no useful page, corrected | 25 of 109 | 8 of 109 |

Why typos fail:
- **Keyword search:** a misspelled word matches nothing, because FTS5 needs whole words. The search then falls back to
  "any word", so the misspelled word, often the emergency itself ("breating", "chokeing", "siezure"), simply drops out
  and the remaining words decide.
- **The model** splits words into pieces, so it keeps some of the meaning, but it still loses about a third.

The no-model fix (`typofix.py`), with no new download:
- **Vocabulary:** the words of the library itself (99,450 terms found in 3+ pages).
- **Candidates:** words 1 or 2 edits away, taken only if at least 50 times more common.
- **Choice:** prefer keeping the first letter, then words used in the library's first-aid and emergency books, then
  how common the word is.
- **Result:** it brings typo questions back to clean-question level on both setups, and it changed only 1 of the 253
  clean questions.

Its remaining mistakes are the case for a real word list, the next layer up:
- **Rare real words get "corrected":** "riots" → "roots". The library alone can't tell that "riots" is a word.
- **Some misspellings land on a common word:** "chocking" → "checking", "shoting" → "showing", "shoked" → "showed",
  "stabed" → "stated", "asma" → "asia".
- Not reinventing the wheel: an English dictionary (hunspell / SCOWL) for "is this already a word", plus a
  common-misspellings list for the emergency words. The E4B layer would fix the rest by rewriting the question.

## Files

- `cases.py`: topics, patterns, counterexamples, typos.
- `score.py`: the scorer.
- `typofix.py`: typo correction and its rescoring.
- `kwserver.py`: runs a server with meaning-based search off.
- `results_main_256d52f.json`, `results_typofix.json`: every question with its top 8 titles and excerpts.

Run:

    python -I score.py OUT.json keyword=http://127.0.0.1:8894 hybrid=http://127.0.0.1:8897
