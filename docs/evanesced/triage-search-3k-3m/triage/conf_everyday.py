"""Everyday (non-urgent) questions: buttons at cuts 0.15..0.40, out-of-fold first-page model."""
import json, os, sys
from pathlib import Path
T = Path(r'D:\git\lastbook\.claude\drafts\triage')
sys.path[:0] = [r'D:\git\lastbook\.claude\worktrees\everyday-buttons']
from engine import confidence as C
for name, mode in (('conf_kw.json', 'keyword'), ('conf_hy.json', 'hybrid')):
    d = json.load(open(T / name, encoding='utf-8'))
    oof = json.load(open(T / f'conf_oof_{mode}.json', encoding='utf-8'))
    p = dict(zip(oof['ids'], oof['p']))
    t3 = json.load(open(T / f'conf_top3_oof_{mode}.json', encoding='utf-8'))
    top3 = dict(zip(t3['ids'], t3['top3_ok']))
    rows = d['rows']
    ev = [r for r in rows if not (r['danger'] or C.urgent(r['q'], r['corrected']))]
    from collections import Counter
    print(f'\n== {mode}: {len(rows)} questions, everyday {len(ev)} ({Counter(r["colour"] for r in ev)}, counter {sum(r["counter"] for r in ev)})'
          f'; first right {sum(r["first_ok"] for r in ev)}, top3 right {sum(top3[r["id"]] for r in ev)}, none of 3 {sum(not top3[r["id"]] for r in ev)}')
    print('cut | buttons | first right but buttons | top3 right but buttons | none of 3 right, no buttons | p range')
    for cut in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.60):
        b = [r for r in ev if p[r['id']] < cut]
        print(f'{cut:.2f} | {len(b)} ({len(b)/len(ev):.0%}) | {sum(r["first_ok"] for r in b)} | {sum(top3[r["id"]] for r in b)} | '
              f'{sum(1 for r in ev if p[r["id"]] >= cut and not top3[r["id"]])}')
    print('lowest everyday:')
    for r in sorted(ev, key=lambda r: p[r['id']])[:14]:
        print(f'   {p[r["id"]]:.2f} first={int(r["first_ok"])} top3={int(top3[r["id"]])} {r["colour"]:6} {r["q"]}  | {r["titles"][:2]}')
