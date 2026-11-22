r"""First page right vs one of the first 3 pages right: base rates, fits, cross-checks and the chat policy at 0.60 / 0.25.

    set LASTBOOK_DATA=D:\LastbookData-fork-test  &  set LASTBOOK_CODE=<worktree>
    python -B -X utf8 conf_top3.py conf_kw.json conf_hy.json > conf_top3.txt

Labels from the stored hits with score.py's per-hit rule (a hit is useful when it matches any need; the same rule that
counts `useful`): top3_ok = one of hits 1-3 is useful. first_ok as stored (hit 1 matches need[0], not the wrong sense).
Same model family as conf_final.py: standardised L2 logistic (C = 0.3), grouped CV by topic, 5 folds x 20 shuffles.
Feature sets: (a) the committed signals; (b) (a) plus top-3 versions computed here from the stored hits and trace.
Read-only: reads the JSON files and the library's word counts (engine.typos) only.
"""
import json, os, sys
import numpy as np
from sklearn.metrics import roc_auc_score
sys.path[:0] = [os.environ['LASTBOOK_CODE']]
from engine import confidence as C  # noqa: E402
from conf_fit import oof, fit_all, raw, calib  # noqa: E402
SETS = {   # as conf_final.py (not imported: it runs its fit at import)
    'keyword': ['cover1', 'title1', 'kw_top_per_idf', 'idf_mean', 'strict', 'emerg1'],
    'hybrid': ['cos1', 'cos_drop', 'overlap', 'all1', 'title1', 'docs', 'strict', 'emerg1'],
}
import score as SCORE  # noqa: E402
from cases import cases  # noqa: E402

CASES = {c['id']: c for c in cases()}
B, U = 0.60, 0.25
EXTRA = ['cover_best3', 'cover_mean3', 'title_best3', 'all3', 'emerg3']


def useful_hit(c, h):
    return any(SCORE.RX[k].search(SCORE.text(h)) for k in c['need'])


def extras(r):
    groups = r['trace'].get('groups') or []
    hs = r['hits'][:3]
    cov = lambda t: sum(C._has(t, g) for g in groups) / len(groups) if groups else 0.0
    full = [cov(((h.get('title') or '') + ' ' + (h.get('excerpt') or '')).lower()) for h in hs] or [0.0]
    title = [cov((h.get('title') or '').lower()) for h in hs] or [0.0]
    return {'cover_best3': max(full), 'cover_mean3': sum(full) / 3, 'title_best3': max(title),
            'all3': float(bool(groups) and max(full) == 1.0), 'emerg3': float(any(C._emergency_book(h) for h in hs))}


def pct(x):
    return f'{x:.0%}'


def main():
    report = {}
    for path in sys.argv[1:3]:
        d = json.load(open(path, encoding='utf-8'))
        mode, rows = d['mode'], d['rows']
        for r in rows:
            c = CASES[r['id']]
            u = [useful_hit(c, h) for h in r['hits']]
            assert sum(u) == r['useful'], (r['id'], sum(u), r['useful'])      # same rule as the stored labels
            r['top3_ok'] = any(u[:3])
            r['f'] = dict(r['f'], **extras(r))
        y1 = np.array([r['first_ok'] for r in rows], int)
        y3 = np.array([r['top3_ok'] for r in rows], int)
        assert not np.any(y1 & ~y3.astype(bool))                                 # first right implies top-3 right
        g = np.array([r['topic'] for r in rows])
        red = np.array([r['colour'] == 'red' and not r['counter'] for r in rows])
        urg = np.array([C.urgent(r['q'], r['corrected']) for r in rows])
        print(f'\n==================== {mode}: {len(rows)} questions')
        print(f'base rates: first right {y1.mean():.1%} ({y1.sum()}), one of first 3 right {y3.mean():.1%} ({y3.sum()}), '
              f'useful in top 8 {np.mean([r["useful"] > 0 for r in rows]):.1%}')
        print(f'  red: first {y1[red].mean():.1%}, top3 {y3[red].mean():.1%} (n={red.sum()}); '
              f'first wrong but 2 or 3 right: {(y3 & (1 - y1)).sum()}')
        sets = {'a': SETS[mode], 'b': SETS[mode] + EXTRA}
        P = {}
        for tname, y in (('first', y1), ('top3', y3)):
            for sname, names in sets.items():
                X = np.array([[r['f'].get(n, 0.0) for n in names] for r in rows], float)
                p, aucs = oof(X, y, g, 0.3)
                other = y3 if tname == 'first' else y1
                key = f'{tname}-{sname}'
                P[key] = p
                sc, m = fit_all(X, y, 0.3)
                coef = raw(sc, m, names)
                report.setdefault(mode, {})[key] = {'coef': coef, 'std': dict(zip(names, m.coef_[0].round(3).tolist()))}
                print(f'\n-- {key} ({len(names)} signals): CV AUC own target {aucs.mean():.3f} (sd {aucs.std():.3f}); '
                      f'on other target ({"top3" if tname == "first" else "first"}) {roc_auc_score(other, p):.3f}; '
                      f'red own {roc_auc_score(y[red], p[red]):.3f}; Brier {np.mean((p - y) ** 2):.3f} '
                      f'(base {np.mean((y.mean() - y) ** 2):.3f})')
                print('   calibration own target: ' + '; '.join(f'{b} n={n} pred={mp:.2f} act={a:.2f}' if n else f'{b} n=0'
                                                            for b, n, mp, a in calib(p, y)))
                print('   standardised:', ', '.join(f'{k} {v:+.2f}' for k, v in sorted(zip(names, m.coef_[0]), key=lambda x: -abs(x[1]))))
                print('   raw:', json.dumps(coef))
        print(f'\n   policy at buttons {B} / unsure {U} (out-of-fold). FA = label true but below {B}; slip = label false but at/above')
        hdr = ('| model | sure / buttons / unsure | FA first (red) | slips first (red) | FA top3 (red) | slips top3 = none of 3 right '
               'but sure (red) | first right but unsure (red) | unsure & not urgent |')
        print(hdr + '\n|' + '---|' * 8)
        for key, p in P.items():
            s, b, u = p >= B, (p >= U) & (p < B), p < U
            fa = lambda y: f'{((p < B) & (y == 1)).sum()} ({((p < B) & (y == 1) & red).sum()})'
            sl = lambda y: f'{((p >= B) & (y == 0)).sum()} ({((p >= B) & (y == 0) & red).sum()})'
            print(f'| {key} | {s.sum()} ({pct(s.mean())}) / {b.sum()} ({pct(b.mean())}) / {u.sum()} ({pct(u.mean())}) | '
                  f'{fa(y1)} | {sl(y1)} | {fa(y3)} | {sl(y3)} | {(u & (y1 == 1)).sum()} ({(u & (y1 == 1) & red).sum()}) | '
                  f'{(u & ~urg).sum()} |')
        # same share of buttons as the first-page model at 0.60: who misses fewer "none of 3 right"?
        base_share = (P['first-a'] < B).mean()
        print(f'\n   at the same share below the buttons cut as first-a at {B} ({base_share:.0%}):')
        for key, p in P.items():
            cut = np.quantile(p, base_share)
            print(f'     {key}: cut {cut:.2f}, none of 3 right but sure {((p >= cut) & (y3 == 0)).sum()}, '
                  f'first right but buttons {((p < cut) & (y1 == 1)).sum()}')
        json.dump({'mode': mode, 'ids': [r['id'] for r in rows], 'p': {k: v.tolist() for k, v in P.items()},
                   'top3_ok': y3.tolist()}, open(f'conf_top3_oof_{mode}.json', 'w', encoding='utf-8'))
    json.dump(report, open('conf_top3_coef.json', 'w', encoding='utf-8'), indent=1)


if __name__ == '__main__':
    main()
