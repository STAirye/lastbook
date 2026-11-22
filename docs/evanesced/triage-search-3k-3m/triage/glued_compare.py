"""Before/after of glued_eval.py runs: python -B -X utf8 glued_compare.py BEFORE.json AFTER.json"""
import json, sys
from collections import Counter

b, a = (json.load(open(p, encoding='utf-8')) for p in sys.argv[1:3])
print('speed before', b['speed'], '\nspeed after ', a['speed'])

print('\n== glued set')
for x, y in zip(b['glued'], a['glued']):
    ok = (y['searched'].lower() == y['want']) if y['want'] else (y['searched'] == y['q'] or y['kind'] not in ('long_word', 'mash'))
    print(f"{y['kind'][:10]:10} {y['q'][:27]:27} -> {y['searched'][:32]:32} {'split ok' if y['want'] and ok else 'SPLIT X ' if y['want'] else 'kept    ' if y['searched'] == y['q'] else 'changed '}"
          f" urgent {int(x['urgent'])}->{int(y['urgent'])}  p {x['p']}->{y['p']}{'*' if y['unknown_words'] else ' '}"
          f" {x['outcome']:7}->{y['outcome']:7} first {int(x['first_ok'])}->{int(y['first_ok'])}")
for kind in ('glued_red', 'glued_everyday', 'mash', 'autocorrect', 'unknown_word', 'long_word'):
    X = [r for r in b['glued'] if r['kind'] == kind]
    Y = [r for r in a['glued'] if r['kind'] == kind]
    split = sum(1 for r in Y if r['want'] and r['searched'].lower() == r['want'])
    print(f"{kind:15} n={len(Y):2}  split right {split:2}  urgent {sum(r['urgent'] for r in X):2}->{sum(r['urgent'] for r in Y):2}"
          f"  first right {sum(r['first_ok'] for r in X):2}->{sum(r['first_ok'] for r in Y):2}"
          f"  outcome {dict(Counter(r['outcome'] for r in X))} -> {dict(Counter(r['outcome'] for r in Y))}")

for key in ('cases', 'c154'):
    print(f'\n== {key}')
    X, Y = b[key], a[key]
    for typo in (False, True):
        xs = [r for r in X if r['typo'] == typo]
        ys = [r for r in Y if r['typo'] == typo]
        ch = [(x, y) for x, y in zip(xs, ys) if (x['searched'], x['outcome'], x['first_ok'], x['route'], x['urgent']) !=
              (y['searched'], y['outcome'], y['first_ok'], y['route'], y['urgent'])]
        print(f"{'typo' if typo else 'clean'}: n={len(ys)} first right {sum(r['first_ok'] for r in xs)}->{sum(r['first_ok'] for r in ys)}"
              f"  outcome {dict(Counter(r['outcome'] for r in xs))} -> {dict(Counter(r['outcome'] for r in ys))}"
              f"  unknown-word rule fired {sum(r['unknown_words'] for r in ys)}  changed {len(ch)}")
        for x, y in ch:
            print(f"   {y['id']:7} {y['q'][:50]!r}: searched {x['searched'][:40]!r}->{y['searched'][:40]!r} route {x['route']}->{y['route']}"
                  f" p {x['p']}->{y['p']}{'*' if y['unknown_words'] else ''} {x['outcome']}->{y['outcome']} first {int(x['first_ok'])}->{int(y['first_ok'])}")
