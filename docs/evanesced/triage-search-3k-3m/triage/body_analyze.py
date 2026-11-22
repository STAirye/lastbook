r"""Score body_eval.py's outputs (body/{before,after}_{kw,hy}.json) -> BODY_SIGNS.json, and print the tables.

    python -B -X utf8 body_analyze.py
"""
import json
from collections import Counter
from pathlib import Path

T = Path(__file__).resolve().parent
B = T / 'body'
SETS = ['cases', 'cases154', 'cases128', 'cases241', 'cases_glued', 'convos']
ACTIONS = ['answer', 'buttons', 'ask', 'ask+pages']
SHOWS = {'answer', 'buttons', 'ask+pages'}      # the pages are shown as the answer's


def load(v, m):
    return {(r['set'], r['id']): r for r in json.load(open(B / f'{v}_{m}.json', encoding='utf-8'))['rows']}


def agg(rs):
    sc = [r for r in rs if r['first_ok'] is not None]
    a = Counter(r['action'] for r in rs)
    return {'n': len(rs), 'scored': len(sc), 'first_ok': sum(r['first_ok'] for r in sc), 'top3_ok': sum(r['top3_ok'] for r in sc),
            'useful': sum(r['useful'] for r in sc), 'no_useful': sum(r['useful'] == 0 for r in sc),
            'urgent': sum(r['danger'] for r in rs), **{x: a.get(x, 0) for x in ACTIONS}}


out = {'tables': {}, 'safety': {}, 'changed': {}}
for m in [x for x in ('kw', 'hy') if (B / f'after_{x}.json').exists() and (B / f'before_{x}.json').exists()]:
    be, af = load('before', m), load('after', m)
    assert be.keys() == af.keys()
    tab = {}
    for s in SETS:
        keys = [k for k in be if k[0] == s]
        tab[s] = {'before': agg([be[k] for k in keys]), 'after': agg([af[k] for k in keys])}
    tab['all'] = {'before': agg(list(be.values())), 'after': agg(list(af.values()))}
    out['tables'][m] = tab
    body = [k for k in af if af[k]['body']]
    out['safety'][m] = {
        'body_sign_questions': len(body),
        'body_bare_ask_before': [(k[0], be[k]['q']) for k in body if be[k]['action'] == 'ask'],
        'body_bare_ask_after': [(k[0], af[k]['q']) for k in body if af[k]['action'] == 'ask'],
        'body_ask_pages_before': [(k[0], be[k]['q']) for k in body if be[k]['action'] == 'ask+pages'],
        'body_ask_pages_after': [(k[0], af[k]['q']) for k in body if af[k]['action'] == 'ask+pages'],
        'urgent_pages_lost': [(k[0], af[k]['q'], be[k]['action'], af[k]['action']) for k in af
                              if be[k]['action'] in SHOWS and af[k]['action'] == 'ask'],
        'urgent_lost': [(k[0], af[k]['q']) for k in af if be[k]['danger'] and not af[k]['danger']],
        'urgent_gained': [(k[0], af[k]['q'], af[k]['colour']) for k in af if af[k]['danger'] and not be[k]['danger']],
        'red_not_urgent_after': [(k[0], af[k]['q']) for k in af if af[k]['colour'] == 'red' and not af[k]['counter']
                                 and not af[k]['danger']],
        'red_bare_ask_after': [(k[0], af[k]['q']) for k in af if af[k]['colour'] == 'red' and af[k]['action'] == 'ask'],
    }
    ch = []
    for k in be:
        b, a = be[k], af[k]
        diff = {f: (b[f], a[f]) for f in ('first_ok', 'top3_ok', 'useful', 'action', 'danger', 'searched', 'first', 'route')
                if b[f] != a[f]}
        if diff:
            ch.append({'set': k[0], 'id': k[1], 'q': a['q'], 'colour': a['colour'], 'body': a['body'], **diff})
    out['changed'][m] = ch

json.dump(out, open(T / 'BODY_SIGNS.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for m, tab in out['tables'].items():
    print(f'\n== {m}: set | first right | top-3 right | useful | no useful page | urgent | answer / buttons / ask / ask+pages')
    for s, d in tab.items():
        b, a = d['before'], d['after']
        f = lambda k: f"{b[k]}->{a[k]}" if b[k] != a[k] else str(b[k])
        print(f"{s:12} n={b['n']:3} ({b['scored']}) | {f('first_ok')} | {f('top3_ok')} | {f('useful')} | {f('no_useful')} | "
              f"{f('urgent')} | {' / '.join(f(x) for x in ACTIONS)}")
    sa = out['safety'][m]
    print('body-sign questions', sa['body_sign_questions'], '| bare ask before', len(sa['body_bare_ask_before']), 'after',
          len(sa['body_bare_ask_after']), '| ask+pages before', len(sa['body_ask_pages_before']), 'after',
          len(sa['body_ask_pages_after']), '| urgent pages lost', len(sa['urgent_pages_lost']), '| urgent lost',
          len(sa['urgent_lost']), '| urgent gained', len(sa['urgent_gained']), '| red bare ask after', sa['red_bare_ask_after'])
    print('  bare ask before:', sa['body_bare_ask_before'])
    print('  urgent gained:', sa['urgent_gained'])
    print(f'  changed ({len(out["changed"][m])}):')
    for c in out['changed'][m]:
        print('   ', {k: v for k, v in c.items() if k not in ('id',)})
