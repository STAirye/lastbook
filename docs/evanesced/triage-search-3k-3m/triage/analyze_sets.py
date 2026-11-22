r"""Score run_sets.py's outputs (r128/{main,new}_{kw,hy}.json) -> LESSONS_154.json (+ prints the tables).

    python -B -X utf8 analyze_sets.py
"""
import importlib.util, json, re
from collections import Counter
from pathlib import Path

T = Path(__file__).resolve().parent
R = T / 'r128'


def by_path(name):
    spec = importlib.util.spec_from_file_location(name, T / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C241 = by_path('cases241')
CASES = by_path('cases')
C154 = by_path('cases154')
VERS = [('main', 'upstream main 4fd221e, D:\\LastbookData'), ('new', 'fork/phrase-injury fe635e7, D:\\LastbookData-fork-test')]
MODES = ['kw', 'hy']


def agg(rs):
    n = len(rs)
    return {'n': n, 'first_ok': sum(r['first_ok'] for r in rs), 'top3_ok': sum(r['top3_ok'] for r in rs),
            'any_useful': sum(r['useful'] > 0 for r in rs), 'useful_sum': sum(r['useful'] for r in rs),
            'covered': sum(r['covered'] for r in rs), 'wrong_sense_first': sum(r['wrong_sense_first'] for r in rs),
            'cap_broken': sum(r['context_share'] > 0.5 for r in rs)}


def auc(p, y):
    pos = [a for a, b in zip(p, y) if b]
    neg = [a for a, b in zip(p, y) if not b]
    if not pos or not neg:
        return None
    return round(sum((a > b) + 0.5 * (a == b) for a in pos for b in neg) / (len(pos) * len(neg)), 3)


D = {f'{v}_{m}': json.load(open(R / f'{v}_{m}.json', encoding='utf-8')) for v, _ in VERS for m in MODES}
out = {'versions': dict(VERS), 'tables': {}, 'per_question': {}}

# aggregates per set, version, mode, subset
tab = {}
for s in ('cases128', 'cases241'):
    for key, d in D.items():
        rows = [r for r in d['rows'] if r['set'] == s]
        sub = {'clean': [r for r in rows if not r['typo']], 'typo': [r for r in rows if r['typo']]}
        if s == 'cases128':
            cl = sub['clean']
            sub |= {'red': [r for r in cl if r['colour'] == 'red' and not r['counter']],
                    'yellow': [r for r in cl if r['colour'] == 'yellow' and not r['counter']],
                    'green': [r for r in cl if r['colour'] == 'green' and not r['counter']],
                    'counter': [r for r in cl if r['counter']]}
            # the typos' clean partners (first phrasing of the same topic)
            first = {r['topic']: r for r in cl if r['id'].endswith('.0')}
            sub['typo_partners'] = [first[r['topic']] for r in sub['typo']]
        else:
            sub |= {'emergency': [r for r in rows if r['id'] in {f'241.{i:02d}' for i, c in enumerate(C241.CASES) if c['group'] == 'emergency'}],
                    'counter241': [r for r in rows if r['id'] in {f'241.{i:02d}' for i, c in enumerate(C241.CASES) if c['group'] == 'counter'}]}
        tab[f'{s}:{key}'] = {k: agg(v) for k, v in sub.items() if v}
out['tables']['aggregates'] = tab
for k, v in tab.items():
    print(k, {x: (y['n'], y['first_ok'], y['top3_ok'], y['any_useful'], y['useful_sum'], y['wrong_sense_first']) for x, y in v.items()})

# per question: first_ok / useful / first title for each version-mode, + confidence on new
for s in ('cases128', 'cases241'):
    pq = []
    ids = [r['id'] for r in D['main_kw']['rows'] if r['set'] == s]
    for i in ids:
        row = None
        for key, d in D.items():
            r = next(x for x in d['rows'] if x['id'] == i)
            if row is None:
                row = {'id': i, 'q': r['q'], 'colour': r['colour'], 'need': r['need'], 'typo': r['typo'], 'counter': r['counter']}
            row[key] = {'first': int(r['first_ok']), 'top3': int(r['top3_ok']), 'useful': r['useful'],
                        'wrong_sense': int(r['wrong_sense_first']), 'title1': r['titles'][0] if r['titles'] else ''}
            if key.startswith('new'):
                row[key] |= {'p': r.get('p'), 'level': r.get('level'), 'danger': r.get('danger'), 'injury': r.get('injury'),
                             'route': r.get('route'), 'same_hits': r.get('same_hits')}
        pq.append(row)
    out['per_question'][s] = pq

# confidence on the new fork: AUC (first right) and the chat's level, per set and mode
conf = {}
for m in MODES:
    for s in ('cases128', 'cases241'):
        rows = [r for r in D[f'new_{m}']['rows'] if r['set'] == s and r.get('p') is not None]
        p, y1, y3 = [r['p'] for r in rows], [r['first_ok'] for r in rows], [r['top3_ok'] for r in rows]
        lv = Counter((('urgent' if r['danger'] else 'everyday'), r['level']) for r in rows)
        conf[f'{s}:{m}'] = {
            'n': len(rows), 'first_ok': sum(y1), 'auc_first': auc(p, y1), 'auc_top3': auc(p, y3),
            'brier': round(sum((a - b) ** 2 for a, b in zip(p, y1)) / len(p), 3), 'mean_p': round(sum(p) / len(p), 3),
            'levels': {f'{a}/{b}': n for (a, b), n in sorted(lv.items())},
            'wrong_first_but_sure': [(r['q'], r['p']) for r in rows if not r['first_ok'] and r['level'] == 'sure'],
            'right_first_but_not_sure': [(r['q'], r['p'], r['level']) for r in rows if r['first_ok'] and r['level'] != 'sure'],
            'red_not_urgent': [r['q'] for r in rows if r['colour'] == 'red' and not r['danger']],
            'green_urgent': [r['q'] for r in rows if r['colour'] == 'green' and r['danger']],
        }
out['tables']['confidence_new'] = conf
print(json.dumps(conf, indent=1))

# label agreement: cases241 vs cases.py / cases154.py for the same text (written blind, compared after)
lab = {c['q']: ('cases.py', c['colour'], c['need']) for c in CASES.cases() if not c['typo_of']}
lab |= {c['q']: ('cases154', c['colour'], c['need']) for c in C154.CASES if c['q'] not in lab}
alt = {"someone fell in the rainwater pool and is not breathing": "someone fell in the rainwater pool and isn't breathing"}
ag = []
for c in C241.CASES:
    k = lab.get(c['q']) or lab.get(alt.get(c['q'], ''))
    if k:
        ag.append({'q': c['q'], 'mine': (c['colour'], c['need']), 'earlier': k,
                   'same_colour': c['colour'] == k[1], 'same_need0': c['need'][0] == k[2][0]})
out['tables']['label_agreement_241'] = {'n': len(ag), 'same_colour': sum(a['same_colour'] for a in ag),
                                        'same_need0': sum(a['same_need0'] for a in ag),
                                        'differ': [a for a in ag if not (a['same_colour'] and a['same_need0'])]}
print(json.dumps(out['tables']['label_agreement_241'], indent=1))
json.dump(out, open(T / 'LESSONS_154.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
