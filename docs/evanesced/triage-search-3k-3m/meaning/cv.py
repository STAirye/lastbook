"""Phase B: pick a classifier and its threshold by cross-validation on the examples only.
Positive = red. Negatives for the false-positive budget = green (look-alikes). Yellow is reported, not budgeted.
Writes cv_results.json and model.json (chosen method, threshold, settings)."""
import json
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from common import HERE, read_jsonl, corrected, embed

EX = read_jsonl(HERE / 'examples.jsonl')
LAB = np.array([r['label'] for r in EX])
CAT = np.array([r['cat'] for r in EX])
Y = (LAB == 'red').astype(int)
FPR_BUDGETS = (0.03, 0.05, 0.10)


def feats(S, ref_lab):
    """Per row of S (query x reference similarities): numbers describing closeness to red / yellow / green."""
    out = []
    for lab in ('red', 'yellow', 'green'):
        M = S[:, ref_lab == lab]
        srt = -np.sort(-M, axis=1)
        out += [srt[:, 0], srt[:, :3].mean(1)]
    F = np.stack(out, 1)
    nonred = np.maximum(F[:, 2], F[:, 4])
    return np.column_stack([F, F[:, 0] - nonred])


class Method:
    def fit(self, X, lab, cat): ...
    def score(self, Q): ...


class KNN(Method):
    def __init__(self, k, weighted=False):
        self.k, self.w, self.name = k, weighted, f'knn{k}{"w" if weighted else ""}'
    def fit(self, X, lab, cat):
        self.X, self.r = X, (lab == 'red').astype(float)
    def score(self, Q, S=None):
        S = Q @ self.X.T if S is None else S
        idx = np.argsort(-S, axis=1)[:, :self.k]
        r = self.r[idx]
        if not self.w:
            return r.mean(1)
        w = np.take_along_axis(S, idx, 1)
        w = np.exp(w / 0.05)
        return (r * w).sum(1) / w.sum(1)


class MaxDiff(Method):
    name = 'maxdiff'
    def fit(self, X, lab, cat):
        self.R, self.N = X[lab == 'red'], X[lab != 'red']
    def score(self, Q):
        return (Q @ self.R.T).max(1) - (Q @ self.N.T).max(1)


class MaxDiffGreen(Method):
    name = 'maxdiff_green'      # red vs green only: yellow neither pulls up nor down
    def fit(self, X, lab, cat):
        self.R, self.N = X[lab == 'red'], X[lab == 'green']
    def score(self, Q):
        return (Q @ self.R.T).max(1) - (Q @ self.N.T).max(1)


class Centroid(Method):
    def __init__(self, per_cat):
        self.per_cat, self.name = per_cat, 'centroid_cat' if per_cat else 'centroid'
    def fit(self, X, lab, cat):
        def cents(mask):
            if not self.per_cat:
                c = X[mask].mean(0, keepdims=True)
            else:
                c = np.vstack([X[mask & (cat == k)].mean(0) for k in sorted(set(cat[mask]))])
            return c / np.linalg.norm(c, axis=1, keepdims=True)
        self.R, self.N = cents(lab == 'red'), cents(lab != 'red')
    def score(self, Q):
        return (Q @ self.R.T).max(1) - (Q @ self.N.T).max(1)


class LR(Method):
    name = 'logreg'
    def fit(self, X, lab, cat):
        self.X, self.lab = X, lab
        # features for training rows from their similarity to the OTHER training rows (leave-self-out)
        S = X @ X.T
        np.fill_diagonal(S, -1)
        self.m = LogisticRegression(C=1.0, max_iter=1000).fit(feats(S, lab), (lab == 'red').astype(int))
    def score(self, Q):
        return self.m.predict_proba(feats(Q @ self.X.T, self.lab))[:, 1]


class LRCent(Method):
    """Logistic regression on the similarity to each category's centroid (red, yellow and green categories)."""
    name = 'logreg_cent'
    def __init__(self, C=1.0):
        self.C = C
    def _cents(self, X, cat):
        self.cats = sorted(set(cat))
        c = np.vstack([X[cat == k].mean(0) for k in self.cats])
        return c / np.linalg.norm(c, axis=1, keepdims=True)
    def fit(self, X, lab, cat):
        # inner 5-fold so each training row's features come from centroids that do not include it
        F = np.zeros((len(X), len(set(cat))))
        self.C_all = self._cents(X, cat)
        cats = self.cats
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=9).split(X, cat):
            sub = sorted(set(cat[tr]))
            c = np.vstack([X[tr][cat[tr] == k].mean(0) for k in sub]); c /= np.linalg.norm(c, axis=1, keepdims=True)
            F[np.ix_(te, [cats.index(k) for k in sub])] = X[te] @ c.T
        self.m = LogisticRegression(C=self.C, max_iter=2000).fit(F * 10, (lab == 'red').astype(int))
    def score(self, Q):
        return self.m.predict_proba((Q @ self.C_all.T) * 10)[:, 1]


def methods():
    return [KNN(k) for k in (1, 3, 5, 7, 11)] + [KNN(k, True) for k in (5, 11)] + \
           [MaxDiff(), MaxDiffGreen(), Centroid(False), Centroid(True), LR(), LRCent()]


def oof_scores(X, make, reps=3):
    """Out-of-fold scores, averaged over repeats of stratified 5-fold (stratified on category)."""
    tot = np.zeros(len(X))
    for rep in range(reps):
        skf = StratifiedKFold(5, shuffle=True, random_state=rep)
        for tr, te in skf.split(X, CAT):
            m = make()
            m.fit(X[tr], LAB[tr], CAT[tr])
            tot[te] += m.score(X[te])
    return tot / reps


def threshold_for(scores, budget):
    """Smallest threshold with green false-positive rate <= budget (red if score > t)."""
    g = np.sort(scores[LAB == 'green'])[::-1]
    n_allowed = int(np.floor(budget * len(g)))
    return g[n_allowed] if n_allowed < len(g) else -np.inf


def summarize(scores, t):
    flag = scores > t
    return {'red_recall': round(flag[LAB == 'red'].mean(), 3), 'yellow_flag': round(flag[LAB == 'yellow'].mean(), 3),
            'green_fp': round(flag[LAB == 'green'].mean(), 3)}


def main():
    res = {}
    for prefix in (False, True):
        X = embed(corrected([r['text'] for r in EX]), prefix=prefix, tag='ex')
        for mk in methods():
            name = f'{mk.name}{"+prefix" if prefix else ""}'
            s = oof_scores(X, lambda mk=mk: type(mk)(*(
                (mk.k, mk.w) if isinstance(mk, KNN) else (mk.per_cat,) if isinstance(mk, Centroid) else (mk.C,) if isinstance(mk, LRCent) else ())))
            row = {}
            for b in FPR_BUDGETS:
                t = threshold_for(s, b)
                row[f'fpr{int(b*100)}'] = dict(summarize(s, t), t=float(t))
            res[name] = row
            print(f'{name:22s}', '  '.join(f"@{k}: red {v['red_recall']:.3f} yel {v['yellow_flag']:.2f} fp {v['green_fp']:.3f}"
                                           for k, v in row.items()), flush=True)
    with open(HERE / 'cv_results.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1)


if __name__ == '__main__':
    main()
