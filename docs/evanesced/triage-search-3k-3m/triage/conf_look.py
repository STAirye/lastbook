import json, sys
import numpy as np
from conf_fit import oof, matrix
d = json.load(open(sys.argv[1], encoding='utf-8')); rows = d['rows']
names = sys.argv[2].split(',')
X = matrix(rows, names); y = np.array([r['first_ok'] for r in rows], int); g = np.array([r['topic'] for r in rows])
p, a = oof(X, y, g, 0.3, repeats=5)
print('AUC', a.mean())
o = np.argsort(p)
print('--- right but lowest')
for i in o:
    if y[i] and p[i] < .35: print(f"{p[i]:.2f} {rows[i]['colour']:6} {rows[i]['q'][:60]:60} | {rows[i]['titles'][0][:60]}")
print('--- wrong but highest')
for i in o[::-1]:
    if not y[i] and p[i] > .7: print(f"{p[i]:.2f} {rows[i]['colour']:6} {rows[i]['q'][:60]:60} | {rows[i]['titles'][0][:60]}")
