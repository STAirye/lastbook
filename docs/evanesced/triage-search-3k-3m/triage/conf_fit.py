"""Fit and judge the search-confidence model on conf_eval.py's output.

    python -B -X utf8 conf_fit.py conf_kw.json conf_hy.json  > conf_fit.txt

Logistic regression (standardised, L2), cross-validated grouped by topic (a topic's clean and typo questions stay in
the same fold), 20 repeats of 5 folds. Prints AUC, calibration, coefficients, threshold tables, and the coefficients on
the raw signals as a Python dict for engine/confidence.py.
"""
import json, sys
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

REPEATS, FOLDS = 20, 5


def matrix(rows, names):
    return np.array([[r['f'].get(n, 0.0) for n in names] for r in rows], dtype=float)


def oof(X, y, groups, C, repeats=REPEATS):
    """Out-of-fold probabilities, averaged over repeats; and the AUC of each repeat."""
    P = np.zeros((repeats, len(y)))
    aucs = []
    for rep in range(repeats):
        for tr, te in GroupKFold(FOLDS, shuffle=True, random_state=rep).split(X, y, groups):
            sc = StandardScaler().fit(X[tr])
            m = LogisticRegression(C=C, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
            P[rep, te] = m.predict_proba(sc.transform(X[te]))[:, 1]
        aucs.append(roc_auc_score(y, P[rep]))
    return P.mean(0), np.array(aucs)


def fit_all(X, y, C):
    sc = StandardScaler().fit(X)
    m = LogisticRegression(C=C, max_iter=2000).fit(sc.transform(X), y)
    return sc, m


def raw(sc, m, names):
    w = m.coef_[0] / sc.scale_
    b = m.intercept_[0] - float(np.sum(m.coef_[0] * sc.mean_ / sc.scale_))
    return {'bias': round(b, 4), **{n: round(float(x), 4) for n, x in zip(names, w)}}


def calib(p, y, edges=(0, .25, .5, .75, 1.0001)):
    out = []
    for a, b in zip(edges, edges[1:]):
        s = (p >= a) & (p < b)
        out.append((f'{a:.2f}-{min(b, 1):.2f}', int(s.sum()), float(p[s].mean()) if s.any() else None,
                    float(y[s].mean()) if s.any() else None))
    return out


def greedy(X, y, groups, names, C, k=10):
    chosen, best_hist = [], []
    left = list(range(len(names)))
    while left and len(chosen) < k:
        scores = []
        for j in left:
            _, a = oof(X[:, chosen + [j]], y, groups, C, repeats=4)
            scores.append((a.mean(), j))
        a, j = max(scores)
        chosen.append(j)
        left.remove(j)
        best_hist.append((names[j], round(a, 3)))
    return best_hist


def table(p, rows, cuts=(.1, .15, .2, .25, .3, .35, .4, .5, .6, .7, .75, .8, .85)):
    ok = np.array([r['first_ok'] for r in rows])
    use = np.array([r['useful'] > 0 for r in rows])
    red = np.array([r['colour'] == 'red' and not r['counter'] for r in rows])
    dg = np.array([r['danger'] for r in rows])
    lines = ['| cut | below | first right but below (false alarm) | first wrong but at/above (slip) | useful>0 but below | '
             'red below | red right but below | red wrong at/above | danger-sign right but below |', '|' + '---|' * 9]
    for c in cuts:
        b = p < c
        lines.append(f'| {c:.2f} | {b.sum()} ({b.mean():.0%}) | {(b & ok).sum()} of {ok.sum()} | {(~b & ~ok).sum()} of {(~ok).sum()} | '
                     f'{(b & use).sum()} of {use.sum()} | {(b & red).sum()} of {red.sum()} | {(b & red & ok).sum()} of {(red & ok).sum()} | '
                     f'{(~b & red & ~ok).sum()} of {(red & ~ok).sum()} | {(b & dg & ok).sum()} of {(dg & ok).sum()} |')
    return '\n'.join(lines)


def main():
    for path in sys.argv[1:]:
        d = json.load(open(path, encoding='utf-8'))
        rows = d['rows']
        names = list(rows[0]['f'].keys())
        X = matrix(rows, names)
        y = np.array([r['first_ok'] for r in rows], dtype=int)
        yu = np.array([r['useful'] > 0 for r in rows], dtype=int)
        groups = np.array([r['topic'] for r in rows])
        print(f'\n\n==================== {d["mode"]}  ({len(rows)} questions, first right {y.mean():.0%}, useful>0 {yu.mean():.0%})')
        print('mean search time', round(np.mean([r['seconds'] for r in rows]), 3), 's')
        print('\nsingle-signal AUC (first_ok), sign: + higher signal = more likely right')
        for j, n in enumerate(names):
            if np.std(X[:, j]) == 0:
                continue
            a = roc_auc_score(y, X[:, j])
            print(f'  {n:16} {max(a, 1 - a):.3f} {"+" if a >= .5 else "-"}')
        for C in (0.03, 0.1, 0.3, 1.0, 3.0):
            _, a = oof(X, y, groups, C, repeats=5)
            print(f'all signals, C={C}: grouped-CV AUC {a.mean():.3f} (+-{a.std():.3f})')
        print('\ngreedy forward selection (CV AUC after adding each, 4 repeats; optimistic):')
        for n, a in greedy(X, y, groups, names, 0.3):
            print(f'  + {n:16} {a}')
        yield_ = (d, rows, names, X, y, yu, groups)
        globals().setdefault('_runs', []).append(yield_)


if __name__ == '__main__':
    main()
