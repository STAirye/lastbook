r"""Score run154.py's outputs: #154's own count, the triage labels (cases154.py), typos, and the confidence model.

    python -B -X utf8 analyze154.py          -> r154/analysis.json (+ prints the tables used in RESULTS_154.md)
"""
import importlib.util, json, random, re, sqlite3, sys
from collections import Counter
from pathlib import Path

T = Path(__file__).resolve().parent
R = T / 'r154'
spec = importlib.util.spec_from_file_location('cases154', T / 'cases154.py')
C154 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C154)
spec = importlib.util.spec_from_file_location('cases', T / 'cases.py')
CASES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CASES)
RX = {k: re.compile(v, re.I) for k, v in C154.P.items()}
QS = C154.CASES
VERSIONS = [('main', 'upstream main 256d52f'), ('old', 'old fork 8e201db'), ('new', 'new fork 9366f16')]
MODES = [('kw', 'keyword'), ('hy', 'hybrid')]
BUT, UNS, EVERY = 0.60, 0.25, 0.30

con = sqlite3.connect('file:D:/LastbookData/library-data/search.sqlite?mode=ro', uri=True)
LT = {t for (t,) in con.execute('SELECT DISTINCT title FROM pages WHERE length(body) > 20000')}


def text(h):
    return (h.get('title') or '') + ' ' + (h.get('excerpt') or '')


def m(keys, t):
    return any(RX[k].search(t) for k in keys)


def score(c, hits):
    ts = [text(h) for h in hits]
    first = ts[0] if ts else ''
    wrong_sense = bool(ts) and bool(c['not_first']) and m(c['not_first'], first) and not m(c['need'], first)
    return {
        'u154': sum(1 for t in ts if re.search(c['pat154'], t, re.I)),
        'useful': sum(1 for t in ts if m(c['need'], t)),
        'first_ok': bool(ts) and bool(RX[c['need'][0]].search(first)) and not wrong_sense,
        'top3_ok': any(m(c['need'], t) for t in ts[:3]),
        'covered': all(any(RX[k].search(t) for t in ts) for k in c['need']),
        'context': sum(1 for t in ts if c['context'] and m(c['context'], t) and not m(c['need'], t)),
        'whole_book': sum(1 for h in hits if (h.get('title') or '') in LT),
        'wrong_sense': wrong_sense,
        'titles': [f"{h.get('title')} p.{h.get('page')}" for h in hits],
    }


def agg(rs):
    n = len(rs)
    return {'n': n, 'first_ok': sum(r['first_ok'] for r in rs), 'top3_ok': sum(r['top3_ok'] for r in rs),
            'any_useful': sum(r['useful'] > 0 for r in rs), 'useful_sum': sum(r['useful'] for r in rs),
            'covered': sum(r['covered'] for r in rs), 'whole_book_slots': sum(r['whole_book'] for r in rs),
            'whole_book_qs': sum(r['whole_book'] > 0 for r in rs), 'context_over_half': sum(r['context'] > 4 for r in rs),
            'u154': sum(r['u154'] for r in rs)}


def auc(p, y):
    pos = [a for a, b in zip(p, y) if b]
    neg = [a for a, b in zip(p, y) if not b]
    if not pos or not neg:
        return None
    s = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    return s / (len(pos) * len(neg))


def auc_ci(p, y, n=4000, seed=7):
    rnd, out = random.Random(seed), []
    idx = list(range(len(p)))
    for _ in range(n):
        b = [rnd.choice(idx) for _ in idx]
        a = auc([p[i] for i in b], [y[i] for i in b])
        if a is not None:
            out.append(a)
    out.sort()
    return round(out[int(0.025 * len(out))], 3), round(out[int(0.975 * len(out)) - 1], 3)


res = {'scored': {}, 'tables': {}}
for v, _ in VERSIONS:
    for mo, _ in MODES:
        d = json.load(open(R / f'{v}_{mo}.json', encoding='utf-8'))
        rows = []
        for r in d['rows']:
            c = QS[r['i']]
            s = score(c, r['hits'])
            s.update(i=r['i'], q=r['q'], typo=r['typo'], colour=c['colour'], group=c['group'])
            for k in ('confidence', 'danger', 'urgent', 'danger_signs', 'corrected', 'features', 'route', 'same_as_traced'):
                if k in r:
                    s[k] = r[k]
            rows.append(s)
        res['scored'][f'{v}_{mo}'] = rows

# 1. #154's own count, clean questions, against the earlier runs
old = {'kw': json.load(open(T.parent / 'check_search_tiers_results.json', encoding='utf-8')),
       'hy': json.load(open(T.parent / 'check_search_tiers_results_hybrid.json', encoding='utf-8'))}
t1 = {}
for mo, _ in MODES:
    prev = {r['q']: r for r in old[mo]}
    t1[mo] = {'earlier_before_256d52f': sum(r['before'] for r in old[mo]), 'earlier_after_128': sum(r['after'] for r in old[mo])}
    for v, _ in VERSIONS:
        rs = [r for r in res['scored'][f'{v}_{mo}'] if not r['typo']]
        t1[mo][v] = sum(r['u154'] for r in rs)
        t1[mo][v + '_typo'] = sum(r['u154'] for r in res['scored'][f'{v}_{mo}'] if r['typo'])
    t1[mo]['main_vs_earlier_before_diffs'] = [(r['q'], prev[r['q']]['before'], r['u154'])
                                              for r in res['scored'][f'main_{mo}'] if not r['typo'] and prev[r['q']]['before'] != r['u154']]
res['tables']['t154'] = t1
print('#154 count', json.dumps(t1, indent=1))

# per question #154 count
perq = []
for i, c in enumerate(QS):
    row = {'q': c['q'], 'colour': c['colour']}
    for v, _ in VERSIONS:
        for mo, _ in MODES:
            r = next(x for x in res['scored'][f'{v}_{mo}'] if x['i'] == i and not x['typo'])
            row[f'{v}_{mo}'] = r['u154']
            row[f'{v}_{mo}_first'] = r['first_ok']
            row[f'{v}_{mo}_top3'] = r['top3_ok']
            row[f'{v}_{mo}_title1'] = r['titles'][0] if r['titles'] else ''
    perq.append(row)
res['tables']['per_question'] = perq

# 2-3. triage, per colour, clean and typo
t2 = {}
for key, rows in res['scored'].items():
    for typo in (False, True):
        rs = [r for r in rows if r['typo'] == typo]
        t2[f'{key}_{"typo" if typo else "clean"}'] = {col: agg([r for r in rs if r['colour'] == col]) for col in ('red', 'yellow', 'green')} | {'all': agg(rs)}
res['tables']['triage'] = t2
for k, v in t2.items():
    print(k, {c: (x['first_ok'], x['top3_ok'], x['any_useful'], x['covered'], x['whole_book_slots']) for c, x in v.items()})

# typo pairs on old vs new
tp = {}
for mo, _ in MODES:
    for v, _ in VERSIONS:
        rows = res['scored'][f'{v}_{mo}']
        cl = {r['i']: r for r in rows if not r['typo']}
        ty = {r['i']: r for r in rows if r['typo']}
        tp[f'{v}_{mo}'] = {'first_lost': [cl[i]['q'] for i in cl if cl[i]['first_ok'] and not ty[i]['first_ok']],
                           'first_gained': [cl[i]['q'] for i in cl if not cl[i]['first_ok'] and ty[i]['first_ok']],
                           'useful_drop_ge3': [(ty[i]['q'], cl[i]['useful'], ty[i]['useful']) for i in cl if cl[i]['useful'] - ty[i]['useful'] >= 3],
                           'zero_useful_typo': [ty[i]['q'] for i in ty if ty[i]['useful'] == 0]}
res['tables']['typo_pairs'] = tp

# 4. confidence, new fork
def action(urg, p):
    if urg:
        return 'reply+pages' if p < UNS else 'buttons' if p < BUT else 'sure'
    return 'reply, pages hidden' if p < min(UNS, EVERY) else 'buttons (compact)' if p < EVERY else 'sure'


oofq = {}
for mode in ('keyword', 'hybrid'):
    oof = json.load(open(T / f'conf_oof_{mode}.json', encoding='utf-8'))
    oofq[mode] = dict(zip(oof['ids'], oof['p']))
idq = {c['q']: c['id'] for c in CASES.cases()}
cases_by_q = {c['q']: c for c in CASES.cases()}

t4 = {}
for mo, mode in MODES:
    rows = res['scored'][f'new_{mo}']
    out = {}
    for subset, rs in (('clean', [r for r in rows if not r['typo']]), ('typo', [r for r in rows if r['typo']]),
                       ('all64', rows)):
        p = [r['confidence']['p'] for r in rs]
        y1 = [r['first_ok'] for r in rs]
        y3 = [r['top3_ok'] for r in rs]
        bands = []
        for lo, hi in ((0, .25), (.25, .5), (.5, .75), (.75, 1.01)):
            b = [r for r in rs if lo <= r['confidence']['p'] < hi]
            bands.append({'band': f'{lo:.2f}-{min(hi, 1):.2f}', 'n': len(b),
                          'mean_p': round(sum(r['confidence']['p'] for r in b) / len(b), 2) if b else None,
                          'first_ok': sum(r['first_ok'] for r in b), 'top3_ok': sum(r['top3_ok'] for r in b)})
        brier = sum((a - b) ** 2 for a, b in zip(p, y1)) / len(p)
        base = sum(y1) / len(y1)
        acts = Counter()
        detail = []
        for r in rs:
            a = action(r['danger'], r['confidence']['p'])
            r['action'] = a
            acts[a] += 1
            detail.append(a)
        out[subset] = {
            'n': len(rs), 'first_ok': sum(y1), 'top3_ok': sum(y3),
            'auc_first': round(auc(p, y1), 3) if auc(p, y1) is not None else None, 'auc_first_ci': auc_ci(p, y1),
            'auc_top3': round(auc(p, y3), 3) if auc(p, y3) is not None else None, 'auc_top3_ci': auc_ci(p, y3),
            'brier': round(brier, 3), 'brier_base': round(base * (1 - base), 3), 'mean_p': round(sum(p) / len(p), 3),
            'bands': bands, 'actions': dict(acts),
            'first_right_but_buttons_or_reply': [r['q'] for r in rs if r['first_ok'] and r['action'] != 'sure'],
            'top3_right_but_reply': [r['q'] for r in rs if r['top3_ok'] and r['action'].startswith('reply')],
            'none_of_3_and_sure': [r['q'] for r in rs if not r['top3_ok'] and r['action'] == 'sure'],
            'first_wrong_and_sure': [r['q'] for r in rs if not r['first_ok'] and r['action'] == 'sure'],
            'pages_hidden': [(r['q'], r['colour']) for r in rs if r['action'] == 'reply, pages hidden'],
            'urgent_pages_lost': [r['q'] for r in rs if r['colour'] in ('red', 'yellow') and r['action'] == 'reply, pages hidden'],
            'urgent_by_colour': {col: [sum(1 for r in rs if r['colour'] == col and r['danger']), sum(1 for r in rs if r['colour'] == col)]
                                 for col in ('red', 'yellow', 'green')},
            'not_urgent': [(r['q'], r['colour']) for r in rs if not r['danger']],
            'danger_sign': [(r['q'], r['danger_signs']) for r in rs if r.get('danger_signs')],
        }
        # the stored out-of-fold p (grouped CV in conf_fit, cases.py fit) for the same text, where cases.py has it
        o = [(oofq[mode][idq[r['q']]], r) for r in rs if r['q'] in idq]
        if o:
            po, ro = [a for a, _ in o], [b for _, b in o]
            out[subset]['oof_overlap'] = {'n': len(o), 'auc_first': round(auc(po, [r['first_ok'] for r in ro]) or 0, 3),
                                          'auc_first_ci': auc_ci(po, [r['first_ok'] for r in ro]),
                                          'auc_first_committed_same_qs': round(auc([r['confidence']['p'] for r in ro], [r['first_ok'] for r in ro]) or 0, 3),
                                          'auc_top3': round(auc(po, [r['top3_ok'] for r in ro]) or 0, 3)}
        # lowest p
        out[subset]['by_p'] = [(round(r['confidence']['p'], 3), int(r['first_ok']), int(r['top3_ok']), r['colour'], int(r['danger']),
                                r['action'], r['q'], r['titles'][0] if r['titles'] else '') for r in sorted(rs, key=lambda r: r['confidence']['p'])]
    t4[mode] = out
    print(mode, json.dumps({k: {x: out[k][x] for x in ('n', 'first_ok', 'top3_ok', 'auc_first', 'auc_first_ci', 'auc_top3', 'auc_top3_ci', 'brier', 'brier_base', 'actions')} for k in out}, indent=0))
res['tables']['confidence'] = t4

# label agreement with cases.py (checked after the blind labels were written)
agree = []
for c in QS:
    k = cases_by_q.get(c['q'])
    if k:
        agree.append({'q': c['q'], 'mine': (c['colour'], c['need']), 'cases': (k['colour'], k['need']),
                      'same_colour': c['colour'] == k['colour'], 'same_need0': c['need'][0] == k['need'][0]})
res['tables']['label_agreement'] = {'n': len(agree), 'same_colour': sum(a['same_colour'] for a in agree),
                                    'same_need0': sum(a['same_need0'] for a in agree),
                                    'differ': [a for a in agree if not (a['same_colour'] and a['same_need0'])]}
res['tables']['typos_in_cases_py'] = [c['typo'] for c in QS if c['typo'] in idq]
print('agreement', json.dumps(res['tables']['label_agreement'], indent=0))
json.dump(res, open(R / 'analysis.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
