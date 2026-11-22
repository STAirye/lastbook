r"""Score ab_phrases_run.py's outputs (rab/ab_kw.json, rab/ab_hy.json) -> rab/ab_phrases.json and printed tables.

    python -B -X utf8 ab_phrases_analyze.py
"""
import importlib.util, json, re
from pathlib import Path

T = Path(__file__).resolve().parent
R = T / 'rab'


def by_path(name):
    spec = importlib.util.spec_from_file_location(name, T / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CM = by_path('cases')
CASES = {c['id']: c for c in CM.cases()}
C154M = by_path('cases154')
C154 = C154M.CASES
RX = {k: re.compile(v, re.I) for k, v in C154M.P.items()}       # cases.P plus two keys
BUT, UNS, EVERY = 0.60, 0.25, 0.30
ARMS = ('base', 'A', 'B', 'AB')
MODES = [mo for mo in ('kw', 'hy') if (R / f'ab_{mo}.json').exists()]
INJ_PHRASE = ['treat water in the lungs after drowning', 'light a fire to keep him warm with hypothermia',
              'carbon monoxide from making a fire in the tent']
HOWTO = ['how do i light a campfire', 'i need to start a fire but i have no matches and no gas',
         'how do i make the water safe to drink', 'how do i purify water from a creek',
         'how do i treat water damage on the floor', "how to make the water safe for a baby's formula"]


def text(h):
    return (h.get('title') or '') + ' ' + (h.get('excerpt') or '')


def m(keys, t):
    return any(RX[k].search(t) for k in keys)


def score(c, hits, pat154=None):
    ts = [text(h) for h in hits]
    first = ts[0] if ts else ''
    wrong = bool(ts) and bool(c['not_first']) and m(c['not_first'], first) and not m(c['need'], first)
    s = {'useful': sum(1 for t in ts if m(c['need'], t)),
         'first_ok': bool(ts) and bool(RX[c['need'][0]].search(first)) and not wrong,
         'top3_ok': any(m(c['need'], t) for t in ts[:3]),
         'covered': all(any(RX[k].search(t) for t in ts) for k in c['need']),
         'wrong_sense': wrong, 'title1': (hits[0].get('title') if hits else '')}
    if pat154:
        s['u154'] = sum(1 for t in ts if re.search(pat154, t, re.I))
    return s


def action(urg, p):
    if p is None:
        return 'sure'
    if urg:
        return 'reply+pages' if p < UNS else 'buttons' if p < BUT else 'sure'
    return 'reply, pages hidden' if p < min(UNS, EVERY) else 'buttons (compact)' if p < EVERY else 'sure'


def agg(rs):
    n = len(rs) or 1
    return {'n': len(rs), 'first_ok': sum(r['first_ok'] for r in rs), 'top3_ok': sum(r['top3_ok'] for r in rs),
            'useful_mean': round(sum(r['useful'] for r in rs) / n, 2), 'useful_sum': sum(r['useful'] for r in rs),
            'zero_useful': sum(r['useful'] == 0 for r in rs), 'covered': sum(r['covered'] for r in rs),
            'wrong_sense': sum(r['wrong_sense'] for r in rs)} | (
        {'u154': sum(r['u154'] for r in rs)} if rs and 'u154' in rs[0] else {})


def conf(rs):
    return {'confident_miss': [r['q'] for r in rs if not r['top3_ok'] and r['action'] == 'sure'],
            'first_right_but_buttons_or_reply': [r['q'] for r in rs if r['first_ok'] and r['action'] != 'sure'],
            'urgent_pages_lost': [r['q'] for r in rs if r['colour'] in ('red', 'yellow') and r['action'] == 'reply, pages hidden'],
            'actions': {a: sum(r['action'] == a for r in rs) for a in ('sure', 'buttons', 'buttons (compact)', 'reply+pages', 'reply, pages hidden')}}


res = {'tables': {}, 'scored': {}, 'changed': {}}
for mo in MODES:
    d = json.load(open(R / f'ab_{mo}.json', encoding='utf-8'))
    for arm in ARMS:
        scored = []
        for r in d['arms'][arm]:
            if r['src'] == 'cases':
                c = CASES[r['id']]
                s = score(c, r['hits'])
                s.update(colour=c['colour'], typo=bool(c['typo_of']), counter=bool(c['not_first']), topic=c['topic'])
            else:
                i = int(r['id'].rstrip('t'))
                c = C154[i]
                s = score(c, r['hits'], c['pat154'])
                s.update(colour=c['colour'], typo=r['id'].endswith('t'), counter=bool(c['not_first']), group=c['group'])
            p = (r['confidence'] or {}).get('p')
            s.update(src=r['src'], id=r['id'], q=r['q'], p=p, danger=r['danger'], action=action(r['danger'], p),
                     helper=bool(r['helpers']), retry=r['retry'], groups=[g[0] for g in r['groups']],
                     titles=[h['title'] for h in r['hits'][:3]])
            scored.append(s)
        res['scored'][f'{mo}_{arm}'] = scored
        cs = [x for x in scored if x['src'] == 'cases']
        clean = [x for x in cs if not x['typo']]
        c1 = [x for x in scored if x['src'] == 'c154']
        t = {'cases_clean': agg(clean), 'cases_typo': agg([x for x in cs if x['typo']]),
             'cases_counter': agg([x for x in clean if x['counter']])}
        for col in ('red', 'yellow', 'green'):
            t[f'cases_{col}'] = agg([x for x in clean if x['colour'] == col and not x['counter']])
        t['c154_clean'] = agg([x for x in c1 if not x['typo']])
        t['c154_typo'] = agg([x for x in c1 if x['typo']])
        for col in ('red', 'yellow', 'green'):
            t[f'c154_{col}'] = agg([x for x in c1 if not x['typo'] and x['colour'] == col])
        t['conf_cases'] = conf(cs)
        t['conf_c154'] = conf(c1)
        res['tables'][f'{mo}_{arm}'] = t

# changes against base, per arm and mode
for mo in MODES:
    base = {(x['src'], x['id']): x for x in res['scored'][f'{mo}_base']}
    for arm in ARMS[1:]:
        ch = []
        for x in res['scored'][f'{mo}_{arm}']:
            b = base[(x['src'], x['id'])]
            if (b['first_ok'], b['top3_ok'], b['useful'], b['titles'], b['action']) != (x['first_ok'], x['top3_ok'], x['useful'], x['titles'], x['action']):
                verdict = ('better' if (x['first_ok'], x['top3_ok'], x['useful']) > (b['first_ok'], b['top3_ok'], b['useful']) and
                           x['first_ok'] >= b['first_ok'] and x['top3_ok'] >= b['top3_ok'] and x['useful'] >= b['useful'] else
                           'worse' if x['first_ok'] <= b['first_ok'] and x['top3_ok'] <= b['top3_ok'] and x['useful'] <= b['useful']
                           and (x['first_ok'], x['top3_ok'], x['useful']) != (b['first_ok'], b['top3_ok'], b['useful']) else
                           'same' if (x['first_ok'], x['top3_ok'], x['useful']) == (b['first_ok'], b['top3_ok'], b['useful']) else 'mixed')
                ch.append({'src': x['src'], 'id': x['id'], 'q': x['q'], 'colour': x['colour'], 'verdict': verdict,
                           'first': [int(b['first_ok']), int(x['first_ok'])], 'top3': [int(b['top3_ok']), int(x['top3_ok'])],
                           'useful': [b['useful'], x['useful']], 'u154': [b.get('u154'), x.get('u154')],
                           'action': [b['action'], x['action']], 'p': [b['p'], x['p']],
                           'title1': [b['title1'], x['title1']]})
        res['changed'][f'{mo}_{arm}'] = ch

# key questions
key = {}
for mo in MODES:
    for arm in ARMS:
        for x in res['scored'][f'{mo}_{arm}']:
            if x['src'] == 'c154' and not x['typo'] and (x['q'] in INJ_PHRASE or x['q'] in HOWTO):
                key.setdefault(x['q'], {})[f'{mo}_{arm}'] = f"{x['u154']}{'F' if x['first_ok'] else ''}{'' if x['top3_ok'] else ' (none in 3)'}"
res['tables']['key'] = key
json.dump(res, open(R / 'ab_phrases.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

cols = ('first_ok', 'top3_ok', 'useful_mean', 'zero_useful', 'covered')
for mo in MODES:
    print(f'\n### {mo}')
    for part in ('cases_clean', 'cases_red', 'cases_yellow', 'cases_green', 'cases_counter', 'cases_typo', 'c154_clean', 'c154_typo',
                 'c154_red', 'c154_yellow', 'c154_green'):
        print(part.ljust(14), ' | '.join(f"{a}: " + ' '.join(str(res['tables'][f'{mo}_{a}'][part].get(k)) for k in cols + ('u154',) if k in res['tables'][f'{mo}_{a}'][part]) for a in ARMS))
    for a in ARMS:
        for s in ('conf_cases', 'conf_c154'):
            cf = res['tables'][f'{mo}_{a}'][s]
            print(a, s, 'miss', len(cf['confident_miss']), 'firstright-not-sure', len(cf['first_right_but_buttons_or_reply']),
                  'lost', len(cf['urgent_pages_lost']), cf['actions'])
print('\nkey')
for q, v in key.items():
    print(q, v)
for k, ch in res['changed'].items():
    print('\n', k, len(ch), {v: sum(c['verdict'] == v for c in ch) for v in ('better', 'worse', 'mixed', 'same')})
