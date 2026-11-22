# Blind list 4 (Qwen3.5-9B, run locally, 2026-11-21): results

Measurement only: no code, word list, example or threshold changed; nothing committed or pushed. The messages were
read only after all four runs were done.

## The list

Generated overnight with Qwen3.5-9B run locally (not Claude; nobody on this side saw it) from `PROMPTS.md`; the output came back as one log
(`raw/phrases local.txt`: the model's output saved as an escaped string, part of it HTML-escaped again), recovered by
`recover.py` into `phrases_mixed.jsonl`: **832 messages**, 115 red / 153 yellow / 564 green (467 counterexamples).

| | Lines | Red / yellow / green | Note |
|---|---|---|---|
| English | 300 | 65 / 133 / 102 | 147 of them are one template ("ive been feeling like my sense of X is all wrong…"); only 7 counterexamples |
| Spanish (321 Chilean, 204 Mexican) | 525 | 45 / 18 / 462 | mostly idioms: "me muero de / por…" 132, "estoy muerto…" 120, "quiero matar el…" 25 |
| Unclear | 7 | 5 / 2 / 0 | fragments of the log, e.g. `Real-word typo "rappd` |

So it is narrow: it tests Spanish idioms (false alarms) and a small set of Spanish and English emergencies well, and
little else. Its labels are Qwen3.5-9B's: several "red" English lines are doubtful (see Misses).

## How it was run

`eval4.py` = `../independent3/eval3.py` reading this list, in-process, read-only, `LASTBOOK_DATA=D:\LastbookData-fork-test`,
fork at bc4c782, meaning check ready in every run (threshold 0.00837). Four runs:

- **typed:** each message as typed (what the desktop does with no local AI).
- **english:** each non-English message also with the English search words the chat makes for it (3i,
  `assistant.english_query`), made once by `english4.py` with the local Gemma 4 E4B: 520 lines needed them, 518 got them,
  61 s in all. `is_danger` and `turn_hits` get them as in the chat.
- each keyword-only and hybrid. Urgency is the same in both (text checks); only the pages differ.

`analyze4.py` → `results.json`, `runs/report.txt` (every miss and every flagged counterexample in full).

## Results

| | English, typed | Spanish, typed | Spanish, with English words |
|---|---|---|---|
| Red urgent (words OR meaning) | **58/65 (89%)** | 12/45 (27%) | **43/45 (96%)** |
| Red urgent, words alone | 54/65 | 7/45 | 42/45 |
| Red added by the meaning check | 4 | 5 | 1 |
| Yellow urgent | 63/133 (47%) | 1/18 | 13/18 (72%) |
| Counterexamples urgent | 6/7 | 31/460 (7%) | **89/460 (19%)** |
| Red: pages shown | 65/65 | 45/45 | 45/45 |
| Red: first page from an emergency book (keyword / hybrid) | 29% / 34% | 0% / 2% | 49% / 49% |
| Red: an emergency book in the top 3 (keyword / hybrid) | 45% / 58% | 2% / 4% | 73% / 82% |

- **No red line was left without pages** in any run (115/115 shown, none with nothing found).
- **Spanish needs the English words.** As typed, the English-only rules catch 27% of Spanish red lines and find almost
  no emergency pages; with the chat's English search words, 96% and an emergency book in the top 3 for 82%. The desktop
  without a local AI has no way to do this.
- **The English words also carry the idioms over:** Spanish counterexamples flagged rose from 7% to 19%. "Estoy muerto
  después de bailar", "mi notebook está muerto", "mate el fuego" become "dead", "kill fire" in English. A false alarm only
  means the pages are always shown and buttons are offered.

## Misses (red, with English words, hybrid)

- **2 Spanish, both untranslated:** "No puedo respirar después de inhalar humo en el incendio" → `respirar humo incendio`,
  "Mi hijo está respirando con mucho esfuerzo y se le hunden las costillas" → `respirando esfuerzo costillas`. Gemma
  returned Spanish words, and `english_words` accepted them because they hold none of `OTHER_WORDS`' function words. Of 518
  translations, 15 have half or more words outside the English word list (2 red). A fix (not made): check the words
  against `engine/english_words.txt.gz` and ask again or fall back.
- **7 English:** "im still feeling like i want to just lay down and die after all that work today lol" (an idiom labelled
  red) and 6 lines of the one template ("…my sense of hope / reality / self / past / truth is all wrong… rn", "can't
  remember anything from this week"). These are doubtful as red; the label is Qwen3.5-9B's.
- 1 fragment of the log ("Real-word typo "rappd"), not a message.

## What it adds to lists 1–3

- First measurement of **Spanish** through the chat's path: red 96% with English words vs 27% as typed.
- A real fault found: untranslated "English" words pass `english_words`.
- English red 89% is lower than list 3's 94.5%, but 6 of the 7 misses are one doubtful template, so it says little.
- Not usable for: serious or messy English (the prompts' other two parts barely came through), yellow precision, or
  page quality beyond "emergency book in the top 3".

## After the fix (2026-11-21)

`assistant.english_words` now also needs half or more of the words to be English words (`_mostly_english`,
`engine/english_words.txt.gz`), and `english_query` asks once more ("Write the words in English") when the reply isn't.
`english4.py` rerun (`english_before_fix.json` kept): both red lines now come back in English ("smoke inhalation
breathing difficulty", "respiratory effort ribs"); only two dish names stay untranslated and are searched as typed.
`english_kw` rerun (`runs/english_kw_before_fix.json` kept): Spanish red urgent 43/45 → **44/45**, an emergency book in
the top 3 33 → 35, counterexamples flagged 89 → 91 of 460 (the retranslation varies run to run: 118 of 520 changed). The
one red line left ("se le hunden las costillas" → "respiratory effort ribs") is a gap in the urgent words (chest
retractions), not the translation.
