# Search as triage: measurements and candidate changes, for discussion

This is a summary of measurements made in a fork (`STAirye/lastbook`), offered for discussion and as input for the
test-only PR asked for on #154. It is not a competing design, and nothing here has been tried by hand in the app window
yet. Where an emergency rule is needed, the intent is to use #167's `urgent` field,
as the maintainers asked. All questions and conversations are invented.

## The idea

Someone searching Lastbook in a hurry is often scared, typing fast, and naming the setting more than the emergency. So
we treated search as triage:

- Each question has an urgency: **red** (life at risk now), **yellow** (needs care soon), **green** (how-to, planning).
- **The most urgent need wins.** "He burned his hand and now he isn't breathing" should lead with breathing.
- **Don't bury the emergency page** under pages about the setting (the flood, the pool, the camp stove).
- **Don't flood the top 8 with one topic or one book.**

There are two layers. Meaning-based search (bge-small vectors, or the local model rewriting the question) helps a lot
where it exists. But the shipped desktop app is keyword-only, so the no-model keyword path has to hold up on its own.
Every number below is given for both.

## How it was tested

- **362 invented questions over 159 topics:** 253 clean ones coloured red / yellow / green (131 red), of which 22 are
  counterexamples that use emergency words in their everyday sense ("brake bleed", a dead battery, drowning tomato
  plants), plus 109 versions typed with panicky typos.
- **52 invented conversations**, scored on the last message: follow-ups, additions, corrections, new emergencies, some
  with a noise message in between.
- **Scorer:** the top 8 of `/api/retrieve`. Each question lists the words a useful page must have, most urgent need
  first, and a page that must not come first. "First result right" means the first hit's title or excerpt matches the
  most urgent need. It is a strict text match, so a first-aid page whose excerpt lacks the words counts as a miss.
- **Baseline:** upstream `main` at `256d52f`, full library.

## What we found

- **Whole-book saved web pages.** 353 saved HTML pages are over 20,000 characters (up to 4.4 MB) and match almost any
  question: *Modern Machine-Shop Practice* came up for 26 of the 362. Cutting those pages into sections of about 5,000
  characters (the stored text has no headings) brought that to 4, raised every score a little, and made hybrid search on those pages faster (4.95 s → 0.68 s). A
  score penalty for long pages was tried first and only fixed the keyword side (26 → 19 on hybrid).
- **Typos.** Keyword search needs whole words, so "breating" matches nothing and the emergency drops out of the query.
  Correcting unknown words against the library's own vocabulary, weighted toward words in emergency books, changed 99 of
  the 109 typo questions and none of the clean ones. Useful pages in the top 8 for typo questions: **2.23 → 4.72**
  keyword-only, 3.39 → 5.57 hybrid.
- **Conversations.** Searching only the newest message loses the context; carrying the previous pages over loses new
  emergencies ("THE KITCHEN IS ON FIRE" after a water question got water pages). Classifying the newest message without
  a model (noise / correction / a new danger sign / follow-up) fixed most of that. Hybrid, first result right:
  corrections 29% → 57%, new emergencies 0% → 80%, follow-ups unchanged at 86%. Additions got worse (68% → 47%), and so
  did messages after noise (75% → 58%).
- **Keyword-only vs hybrid, all changes together** (first result right, before → after):

  | | keyword-only | hybrid |
  |---|---|---|
  | Red questions | 44% → 44% | 67% → 70% |
  | All clean questions | 58% → 59% | 73% → 76% |
  | Red questions with no useful page | 28 → 27 of 131 | 5 → 8 of 131 |
  | Conversations | 48% → 54% | 56% → 64% |

  Red is the weakest colour on both, which is where it matters most.
- **How sure the search is.** A small logistic regression on signals search already has (how many of the question's
  words the first page carries, keyword match strength for how rare the words are, first-aid book or not; with vectors,
  the best cosine and how far the two searches agree) predicts whether the first page is right. Cross-validated by
  topic: AUC 0.78 keyword-only, 0.74 hybrid, and calibrated within a few points in each band. Below 0.60 the chat
  offers buttons; below 0.25 it asks the person to say more. A question that may be urgent always gets its pages
  anyway, so red questions never lose them. One result we didn't expect: predicting "one of the first 3 pages is right"
  sounds kinder but works worse. That outcome is so common (78% keyword-only, 90% hybrid) that the model is nearly
  always sure, and it lets 2–4 times as many all-wrong searches through with no buttons.

## Caveats

- The test set and the conversation classifier were written together, so the numbers are optimistic. New wording will
  do worse.
- Not yet tested by hand in the app window; checked by unit tests and the event stream.
- The "may be urgent" list used for the confidence rule is the fork's own; upstream it should come from #167's
  `urgent` phrases instead.
- The buttons offered are the emergency set ("Not breathing", "Heavy bleeding" … "Something else"), even on everyday
  questions; whether people tap them is not measured.
- Confidence inside a conversation predicts poorly (AUC 0.45–0.65), so there it only offers buttons.
- Red questions with no useful page at all: still 8 of 131 with hybrid, and 27 of 131 keyword-only.

## Proposed next steps, as separate small PRs

1. **The test-only PR asked for on #154:** the question set with expected first results, the counterexamples, the
   scorer, and the baseline on `256d52f`. Nothing else.
2. **Long pages in sections**, scored against that baseline.
3. **Typo correction**, scored the same way.
4. **Conversation handling and the confidence estimate**, using #167's `urgent` field for the urgency check.

## References

- Fork record, `docs/FORK.md`:
  [3g. 10-turn stress test](https://github.com/STAirye/lastbook/blob/fork/lightweight-gemma-no-us-maps/docs/FORK.md#3g-a-10-turn-stress-test-a-confused-user),
  [3h. Keyword search misses everyday wording](https://github.com/STAirye/lastbook/blob/fork/lightweight-gemma-no-us-maps/docs/FORK.md#3h-keyword-search-misses-everyday-wording-upstream),
  [3k. Search as triage](https://github.com/STAirye/lastbook/blob/fork/lightweight-gemma-no-us-maps/docs/FORK.md#3k-search-as-triage-long-pages-typos-conversations),
  [3l. How sure the search is](https://github.com/STAirye/lastbook/blob/fork/lightweight-gemma-no-us-maps/docs/FORK.md#3l-how-sure-the-search-is)
- Fork commits:
  [a5d2d4e conversations](https://github.com/STAirye/lastbook/commit/a5d2d4e),
  [0da7c33 typos](https://github.com/STAirye/lastbook/commit/0da7c33),
  [40a393a sections](https://github.com/STAirye/lastbook/commit/40a393a),
  [c66b9ad](https://github.com/STAirye/lastbook/commit/c66b9ad) and
  [f4eb142](https://github.com/STAirye/lastbook/commit/f4eb142) confidence
- Upstream: [#154](https://github.com/Immortal-Protocols/lastbook/issues/154),
  [#167](https://github.com/Immortal-Protocols/lastbook/pull/167),
  [#168](https://github.com/Immortal-Protocols/lastbook/pull/168)
- To be attached with the test-only PR (currently local): `RESULTS.md`, `COMPARE_long_pages.md`, `COMPARE_rewrite.md`,
  `MULTITURN.md`, `CONFIDENCE.md`, and the test set and scorer (`cases.py`, `convos.py`, `score.py`).
