r"""fork/contractions: before (19c2db2) vs after, line by line.  python -B -X utf8 diff.py BEFORE AFTER [heldout|insample]
Prints every line whose searched text, urgency, body signs, action or first page changed. Measurement only."""
import json, sys

load = lambda p: json.load(open(p, encoding='utf-8'))['rows']
B, A = load(sys.argv[1]), load(sys.argv[2])
ins = len(sys.argv) > 3 and sys.argv[3] == 'insample'
first = lambda r: (r['top3'][0]['title'] if r.get('top3') else None) if not ins else r.get('first')
n = 0
for b, a in zip(B, A):
    if ins:
        keys = ('searched', 'danger', 'body', 'action', 'first_ok', 'top3_ok', 'level')
        tag = f"[{b.get('set')}]"
        text = b['q']
    else:
        keys = ('corrected', 'is_danger', 'urgent', 'body', 'action', 'n_hits')
        tag = f"[{b['triage']}|{','.join(b['kind'])}]"
        text = b['text']
    ch = {k: (b.get(k), a.get(k)) for k in keys if b.get(k) != a.get(k)}
    if first(b) != first(a):
        ch['first'] = (first(b), first(a))
    if ch:
        n += 1
        print(f'{text!r} {tag}')
        for k, (x, y) in ch.items():
            print(f'    {k}: {x!r} -> {y!r}')
print(n, 'lines changed of', len(B))
