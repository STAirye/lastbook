r"""What the chat would do with each labelled question, with engine/confidence.py as committed (thresholds from the
environment as the app reads them). Out-of-fold probabilities (conf_oof_<mode>.json) for the questions; the committed
coefficients on the conversations. Also checks the module reproduces the fitted model.

    set LASTBOOK_DATA=D:\LastbookData-fork-test  &  set LASTBOOK_CODE=<worktree>
    python -B -X utf8 conf_policy.py conf_kw.json conf_hy.json
"""
import json, os, sys
import numpy as np
from pathlib import Path
sys.path[:0] = [os.environ['LASTBOOK_CODE']]
from engine import confidence as C

B, U = C.thresholds()
print(f'thresholds: buttons < {B}, unsure < {U}')
for path in sys.argv[1:]:
    d = json.load(open(path, encoding='utf-8'))
    mode, rows = d['mode'], d['rows']
    oof = json.load(open(Path(path).with_name(f'conf_oof_{mode}.json'), encoding='utf-8'))
    p_oof = dict(zip(oof['ids'], oof['p']))
    mod = [C.estimate(r['hits'], r['trace'])['p'] for r in rows]
    insample = np.array([C.probability(r['f'], C.MODELS[mode]) for r in rows])
    print(f'\n== {mode}: module vs stored features, max |dp| {np.max(np.abs(np.array(mod) - insample)):.4f}')
    act = {}
    for r in rows:
        p = p_oof[r['id']]
        urg = C.urgent(r['q'], r['corrected'])
        a = 'answer' if p >= B else 'buttons' if p >= U else ('ask + pages' if urg else 'ask, pages hidden')
        act.setdefault(a, []).append(r)
    for a in ('answer', 'buttons', 'ask + pages', 'ask, pages hidden'):
        rs = act.get(a, [])
        red = [r for r in rs if r['colour'] == 'red' and not r['counter']]
        print(f'  {a:18} {len(rs):4} ({len(rs) / len(rows):.0%})  first right {sum(r["first_ok"] for r in rs):3}  '
              f'a useful page {sum(r["useful"] > 0 for r in rs):3}  red {len(red):3} (first right {sum(r["first_ok"] for r in red)})')
        if a == 'ask, pages hidden':
            for r in rs:
                print(f'      {p_oof[r["id"]]:.2f} ok={int(r["first_ok"])} useful={r["useful"]} {r["colour"]:6} {r["q"]}')
    cv = [c for c in d['convos'] if c['calls']]
    print(f'  conversations ({len(cv)}), committed coefficients, better of own and joined search:')
    for c in cv:
        fs = [c['calls'][0]['f'], c['calls'][-1]['f']]
        c['p'] = max(C.probability(f, C.MODELS[mode]) for f in fs)
    for a, test in (('answer', lambda p: p >= B), ('buttons', lambda p: U <= p < B), ('below unsure', lambda p: p < U)):
        rs = [c for c in cv if test(c['p'])]
        print(f'    {a:14} {len(rs):3}  first right {sum(c["first_ok"] for c in rs)}  routes {sorted(set(c["route"] for c in rs))}')
