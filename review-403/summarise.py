"""Markdown tables from before.json / after.json (capture.py): one row per step and search, repeats collapsed."""
import json, sys
from pathlib import Path

Q = ['grease fire in a pan', 'kitchen fires', 'lathe chuck']
out = []
for f in sys.argv[1:]:
    d = json.loads(Path(f).read_text(encoding='utf-8'))
    out += [f"\n**{d['code']}**\n", '| step | t (s) | search | answer (s) | results | top 2: title [cited pages] | long page opened: page / pages |',
            '|---|---|---|---|---|---|---|']
    prev, reps = None, 0
    for s in d['log']:
        if 'long_rows' in s:
            continue
        sig = json.dumps({q: s[q].get('top') for q in Q})
        if sig == prev:
            reps += 1
            continue
        if reps:
            out.append(f'| (same answers {reps} more times, every 2 s) | | | | | | |')
        prev, reps = sig, 0
        for q in Q:
            r = s[q]
            top = '; '.join(f"{t['title'][:40]} {[h['page'] for h in t['hits']]}" for t in r.get('top', [])[:2]) or '(nothing)'
            o = r.get('opened') or {}
            op = f"{o.get('page')} / {o.get('pages')}" if o else '-'
            out.append(f"| {s['step']} | {s['t']} | {q} | {r.get('seconds')} | {r.get('n')} | {top} | {op} |")
    if reps:
        out.append(f'| (same answers {reps} more times, every 2 s, until the 60 s limit) | | | | | | |')
print('\n'.join(out))
