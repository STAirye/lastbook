"""Final model per mode: chosen signals, grouped CV (20 x 5 folds by topic), calibration, threshold tables, coefficients.

    python -B -X utf8 conf_final.py conf_kw.json conf_hy.json > conf_final.txt
"""
import json, math, sys
import numpy as np
from sklearn.metrics import roc_auc_score
from conf_fit import oof, fit_all, raw, calib, table, matrix

SETS = {
    'keyword': ['cover1', 'title1', 'kw_top_per_idf', 'idf_mean', 'strict', 'emerg1'],
    'hybrid': ['cos1', 'cos_drop', 'overlap', 'all1', 'title1', 'docs', 'strict', 'emerg1'],
}
C = 0.3
if len(sys.argv) > 3:
    C = float(sys.argv[3])


def pr(p):
    return 1 / (1 + math.exp(-p))


out = {}
for path in sys.argv[1:3]:
    d = json.load(open(path, encoding='utf-8'))
    mode, rows = d['mode'], d['rows']
    names = SETS[mode]
    X = matrix(rows, names)
    y = np.array([r['first_ok'] for r in rows], int)
    yu = np.array([r['useful'] > 0 for r in rows], int)
    g = np.array([r['topic'] for r in rows])
    red = np.array([r['colour'] == 'red' and not r['counter'] for r in rows])
    typo = np.array([r['typo'] for r in rows])
    p, aucs = oof(X, y, g, C)
    pu, aucu = oof(X, yu, g, C)
    print(f'\n==================== {mode}: {len(rows)} questions, first right {y.mean():.0%}, a useful page in top 8 {yu.mean():.0%}')
    print(f'signals: {names}, L2 C={C}')
    print(f'grouped-CV AUC, first right: {aucs.mean():.3f} (sd over repeats {aucs.std():.3f}); on averaged OOF {roc_auc_score(y, p):.3f}')
    print(f'  red only: {roc_auc_score(y[red], p[red]):.3f} (n={red.sum()}); clean: {roc_auc_score(y[~typo], p[~typo]):.3f}; typos: {roc_auc_score(y[typo], p[typo]):.3f}')
    print(f'same model against "a useful page in top 8": AUC {roc_auc_score(yu, p):.3f}; a model fitted for it: {aucu.mean():.3f}')
    print(f'Brier {np.mean((p - y) ** 2):.3f} (always the base rate: {np.mean((y.mean() - y) ** 2):.3f})')
    print('\ncalibration (out-of-fold): band | n | mean predicted | actual first right')
    for band, n, mp, act in calib(p, y):
        print(f'  {band} | {n} | {mp if mp is None else round(mp, 2)} | {act if act is None else round(act, 2)}')
    print('deciles:')
    for band, n, mp, act in calib(p, y, edges=tuple(np.quantile(p, np.linspace(0, 1, 11))[:-1]) + (1.0001,)):
        print(f'  {band} | {n} | {mp if mp is None else round(mp, 2)} | {act if act is None else round(act, 2)}')
    print('\nthreshold table (out-of-fold probabilities; red = red topics, counterexamples out; danger = assistant.danger_signs)')
    print(table(p, rows))
    sc, m = fit_all(X, y, C)
    print('\nstandardised coefficients (fit on all; size = weight per standard deviation):')
    for n, w in sorted(zip(names, m.coef_[0]), key=lambda x: -abs(x[1])):
        print(f'  {n:16} {w:+.3f}')
    coef = raw(sc, m, names)
    print('raw coefficients:', json.dumps(coef))
    # plain fit (in-sample) for comparison
    pin = m.predict_proba(sc.transform(X))[:, 1]
    print(f'in-sample AUC (overstates): {roc_auc_score(y, pin):.3f}')
    # check the raw dict reproduces sklearn
    z = np.array([coef['bias'] + sum(coef[n] * r['f'].get(n, 0.0) for n in names) for r in rows])
    assert np.allclose(1 / (1 + np.exp(-z)), pin, atol=1e-3)
    out[mode] = coef
    # conversations: own search (first traced call) vs joined (last), and the better of them
    cv = [c for c in d['convos'] if c['calls']]
    yc = np.array([c['first_ok'] for c in cv], int)
    P = lambda f: 1 / (1 + math.exp(-(coef['bias'] + sum(coef[n] * f.get(n, 0.0) for n in names))))
    own = np.array([P(c['calls'][0]['f']) for c in cv])
    best = np.array([max(P(c['calls'][0]['f']), P(c['calls'][-1]['f'])) for c in cv])     # as turn_hits: own and joined
    last = np.array([P(c['calls'][-1]['f']) for c in cv])
    print(f'\nconversations (n={len(cv)}, last message first right {yc.mean():.0%}), in-sample coefficients:')
    for name, v in (('own search', own), ('joined search', last), ('better of the two', best)):
        print(f'  {name:18} AUC {roc_auc_score(yc, v):.3f}; below .25: {(v < .25).sum()} (right {((v < .25) & (yc == 1)).sum()}); below .75: {(v < .75).sum()} (right {((v < .75) & (yc == 1)).sum()})')
    json.dump({'mode': mode, 'p': p.tolist(), 'ids': [r['id'] for r in rows]}, open(f'conf_oof_{mode}.json', 'w', encoding='utf-8'))
print('\nMODELS =', json.dumps(out, indent=1))
