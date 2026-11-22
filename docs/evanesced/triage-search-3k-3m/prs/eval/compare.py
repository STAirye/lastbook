"""Before/after table rows from two score.py outputs. argv: before.json after.json label"""
import json, sys
b = json.load(open(sys.argv[1], encoding='utf-8'))['summary']
a = json.load(open(sys.argv[2], encoding='utf-8'))['summary']
mode = sys.argv[3]
KEYS = ('useful_mean', 'first_ok', 'top3_ok', 'covered', 'zero_useful', 'cap_broken', 'wrong_sense_first')
ROWS = [('Triage, red', 'triage', 'red'), ('Triage, yellow', 'triage', 'yellow'), ('Triage, green', 'triage', 'green'),
        ('Triage, counterexamples', 'triage', 'counterexamples'), ('Triage, typo versions', 'triage', 'typos'),
        ('#128, clean', 'issue128', 'all_clean'), ('#128, typos', 'issue128', 'typos'),
        ('#154, clean', 'issue154', 'all_clean'), ('#154, typos', 'issue154', 'typos'), ('#241', 'issue241', None)]


def get(s, st, sub):
    x = s.get(st, {})
    if sub:
        x = x.get(sub, {})
    return x


def cell(x, y, k):
    if x.get(k) is None:
        return 'n/a'
    return f"{x[k]}" if x[k] == y.get(k) else f"{x[k]} → {y.get(k)}"


for name, st, sub in ROWS:
    x, y = get(b, st, sub), get(a, st, sub)
    if not x:
        print('missing', name, list(b.get(st, {}).keys())[:10])
        continue
    print(f"| {name} | {mode} | {x.get('n')} | " + ' | '.join(cell(x, y, k) for k in KEYS) + ' |')
for k in ('conversations', 'glued'):
    print(k, json.dumps(b.get(k))[:400])
    print(k, json.dumps(a.get(k))[:400])
for n in (1, 2, 3, 4):
    print('list', n, json.dumps(b['lists'].get(f'list{n}'))[:300])
    print('list', n, json.dumps(a['lists'].get(f'list{n}'))[:300])
print('154 useful', b.get('issue154', {}).get('useful154'), a.get('issue154', {}).get('useful154'))
