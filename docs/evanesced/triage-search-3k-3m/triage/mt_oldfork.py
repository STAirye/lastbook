"""Old fork multi-turn over HTTP: only the 'latest' and 'fork' strategies of multiturn.py.
    python -I -X utf8 mt_oldfork.py OUT.json NAME=URL [...]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import multiturn as M  # noqa: E402
from convos import CONVOS  # noqa: E402
import typofix  # noqa: E402

V = typofix.vocab('D:/LastbookData/library-data/search.sqlite',
                  '<scratchpad>/vocab.json')
KINDS = ('follow', 'add', 'correct', 'new', 'after_noise', 'all')
res = {}
for a in sys.argv[2:]:
    name, base = a.split('=', 1)
    for strat in ('latest', 'fork'):
        rows = []
        for c in CONVOS:
            hits, _, _ = M.run(base, c['turns'], strat, V)
            r = M.score(c, hits)
            r['kind'] = c['turns'][-1][1]
            r['has_noise'] = any(k == 'noise' for _, k in c['turns'][1:])
            rows.append(r)
        by = {k: M.agg([r for r in rows if r['kind'] == k]) for k in KINDS[:4]}
        by['after_noise'] = M.agg([r for r in rows if r['has_noise']])
        by['all'] = M.agg(rows)
        res[f'{name} {strat}'] = by
        print(f'{name} {strat:8}' + ''.join(f'{k}={round(by[k]["first_ok"]*100)}({by[k]["n"]}) ' for k in KINDS), flush=True)
json.dump(res, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
