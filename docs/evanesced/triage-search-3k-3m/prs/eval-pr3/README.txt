PR 3 (triage/3-typos) measurements. Data: D:\LastbookData-fork-test, read only (snap-before/after.json equal).
Sections file: built by score.py --sections into the session scratchpad (not kept: it is a library-derived binary).
kw-before.json: score.py --mode keyword --sections <scratch> --rows on triage-2 (cf12898); equals PR 2's eval/kw-after.json.
kw-after.json / hy-after.json: same on triage-3. Hybrid "before" = ../eval/hy-after.json (PR 2's run, not rerun).
Compare: python -B ../eval/compare.py kw-before.json kw-after.json keyword
words_measure.py -> words.json: corrector changes on triage/#154 questions and English words bent on lists 1-4,
  English guard on and off.
tests-after.txt: every app/tests file run one at a time (before the looks_foreign fix; test_typos, test_bridge,
  test_what_ships, test_topic_search, test_long_pages rerun after it, all OK).
