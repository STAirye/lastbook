"""Phase B final fit + Phase C evaluation.
Fits the chosen method (per-category centroids, no prefix) on all examples, threshold from the out-of-fold scores of cv.py,
writes model.npz (the vectors to ship) and model.json, then scores the held-out lists and the in-sample triage sets with
words only (confidence.urgent), meaning only, and words OR meaning. Writes eval_results.json."""
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

from common import HERE, read_jsonl, corrected, embed, words_flag
import cv

DRAFTS = HERE.parent
OPS = {'strict': 0.05, 'wide': 0.10}


def fit():
    X = embed(corrected([r['text'] for r in cv.EX]), prefix=False, tag='ex')
    s = cv.oof_scores(X, lambda: cv.Centroid(True))
    th = {k: float(cv.threshold_for(s, b)) for k, b in OPS.items()}
    m = cv.Centroid(True)
    m.fit(X, cv.LAB, cv.CAT)
    red_cats = sorted(set(cv.CAT[cv.LAB == 'red']))
    non_cats = sorted(set(cv.CAT[cv.LAB != 'red']))
    np.savez(HERE / f'model{OUTSUFFIX}.npz', red=m.R.astype(np.float16), nonred=m.N.astype(np.float16))
    json.dump({'method': 'centroid_cat: max cosine to a red category centroid minus max cosine to a non-red (yellow or '
                         'look-alike) category centroid; red when > threshold', 'prefix': False,
               'red_categories': red_cats, 'nonred_categories': non_cats, 'thresholds': th,
               'threshold_rule': 'out-of-fold (5-fold x3, examples only) score above which 5% / 10% of green examples fall'},
              open(HERE / f'model{OUTSUFFIX}.json', 'w', encoding='utf-8'), indent=1)
    return m, th


def load_triage():
    sys.path.insert(0, str(DRAFTS / 'triage'))
    out = []
    import cases, cases128, cases154, cases241, cases_glued
    for mod in (cases, cases128, cases154, cases241):
        for c in (mod.cases() if hasattr(mod, 'cases') else mod.CASES):
            out.append({'text': c['q'], 'triage': c['colour'], 'kind': [mod.__name__ + (':typo' if c.get('typo_of') or c.get('typo') else '')]})
    for c in cases_glued.CASES:
        out.append({'text': c['q'], 'triage': 'red' if c['red'] else 'green', 'kind': ['cases_glued:' + c['kind']]})
    return out


def run(rows, m, th, name):
    texts = [r['text'] for r in rows]
    Q = embed(corrected(texts), prefix=False, tag=name)
    score = m.score(Q)
    words = np.array([words_flag(t) for t in texts])
    res = {'n': len(rows), 'by_label': {}, 'by_kind': {}, 'red_misses': {}, 'new_fp': {}, 'lost_fp': {}}
    for op, t in th.items():
        mean = score > t
        either = words | mean
        sets = {'words': words, 'meaning': mean, 'both_or': either}
        lab = np.array([r['triage'] for r in rows])
        res['by_label'][op] = {k: {l: f'{int(v[lab == l].sum())}/{int((lab == l).sum())}' for l in ('red', 'yellow', 'green')}
                               for k, v in sets.items()}
        bk = defaultdict(dict)
        kinds = sorted({k for r in rows for k in r['kind']})
        for kd in kinds:
            idx = np.array([kd in r['kind'] for r in rows])
            for l in ('red', 'yellow', 'green'):
                sel = idx & (lab == l)
                if sel.sum():
                    bk[kd][l] = {k: f'{int(v[sel].sum())}/{int(sel.sum())}' for k, v in sets.items()}
        res['by_kind'][op] = bk
        res['red_misses'][op] = {
            'words': [texts[i] for i in np.where((lab == 'red') & ~words)[0]],
            'meaning': [texts[i] for i in np.where((lab == 'red') & ~mean)[0]],
            'both_or': [(texts[i], round(float(score[i]), 3)) for i in np.where((lab == 'red') & ~either)[0]],
            'caught_by_meaning_only': [texts[i] for i in np.where((lab == 'red') & ~words & mean)[0]],
        }
        res['new_fp'][op] = [(texts[i], rows[i]['kind'], rows[i]['triage'], round(float(score[i]), 3))
                             for i in np.where((lab != 'red') & mean & ~words)[0]]
    res['scores'] = [(texts[i], rows[i]['triage'], round(float(score[i]), 3), bool(words[i])) for i in range(len(rows))]
    return res


OUTSUFFIX = '_int8' if 'int8' in os.environ.get('MEANING_MODEL_DIR', '') else ''


def main():
    m, th = fit()
    print('thresholds', th)
    lists = {'independent': read_jsonl(DRAFTS / 'independent' / 'phrases.jsonl'),
             'independent2': read_jsonl(DRAFTS / 'independent2' / 'phrases.jsonl'),
             'triage_insample': load_triage()}
    out = {'thresholds': th}
    for name, rows in lists.items():
        out[name] = run(rows, m, th, name)
        print(name, json.dumps(out[name]['by_label'], indent=0))
    json.dump(out, open(HERE / f'eval_results{OUTSUFFIX}.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
