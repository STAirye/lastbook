"""Compare scored variants: summaries, top-8 slots taken by whole-book HTML pages, and questions that got better or worse.

    python -I -X utf8 compare.py SEARCH_DB OUT.md RESULTS.json[:name=label,...] ...
"""
import json, re, sqlite3, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cases import P  # noqa: E402

LONG = 20000


def long_titles(db):
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    return {t for (t,) in con.execute('SELECT DISTINCT title FROM pages WHERE length(body) > ?', (LONG,))}


def main():
    db, out = sys.argv[1], sys.argv[2]
    LT = long_titles(db)
    variants = {}
    for arg in sys.argv[3:]:
        path, _, names = arg.partition(':')
        res = json.load(open(path, encoding='utf-8'))['by_server']
        for pair in names.split(','):
            name, label = pair.split('=')
            variants[label] = res[name]
    lines = ['| | ' + ' | '.join(variants) + ' |', '|---|' + '---|' * len(variants)]
    def row(label, f):
        lines.append(f'| {label} | ' + ' | '.join(f(v) for v in variants.values()) + ' |')
    S = lambda v, g, k: v['summary'][g][k]
    row('Red: first result right', lambda v: f"{S(v, 'red', 'first_ok'):.0%}")
    row('Red: useful in top 8', lambda v: f"{S(v, 'red', 'useful_mean'):.2f}")
    row('Red: no useful page', lambda v: str(S(v, 'red', 'zero_useful')))
    row('Yellow: first right', lambda v: f"{S(v, 'yellow', 'first_ok'):.0%}")
    row('Green: first right', lambda v: f"{S(v, 'green', 'first_ok'):.0%}")
    row('Counterexamples: first right', lambda v: f"{S(v, 'counterexamples', 'first_ok'):.0%}")
    row('All clean: useful in top 8', lambda v: f"{S(v, 'all_clean', 'useful_mean'):.2f}")
    row('All clean: first right', lambda v: f"{S(v, 'all_clean', 'first_ok'):.0%}")
    row('All clean: every need covered', lambda v: f"{S(v, 'all_clean', 'covered'):.0%}")
    row('Typos: useful in top 8', lambda v: f"{S(v, 'typos', 'useful_mean'):.2f}")

    def slots(v):
        n = q = 0
        for r in v['rows']:
            hit = False
            for t in r['titles']:
                if t.rsplit(' p.', 1)[0] in LT:
                    n += 1; hit = True
            q += hit
        return n, q
    row('Top-8 slots taken by whole-book pages (all 362 questions)', lambda v: str(slots(v)[0]))
    row('Questions with a whole-book page in the top 8', lambda v: str(slots(v)[1]))
    mm = lambda v: sum(any(t.startswith('Modern Machine-Shop') for t in r['titles']) for r in v['rows'])
    row('Questions with Modern Machine-Shop Practice', lambda v: str(mm(v)))

    labels = list(variants)
    text = ['# Variants', '', *lines, '']
    pairs =[(a, b) for a in labels for b in labels if a != b and a.split(' ')[-1] == b.split(' ')[-1] and a.startswith('base')]
    for a, b in pairs:
        ra = {r['q']: r for r in variants[a]['rows'] if not r['typo']}
        rb = {r['q']: r for r in variants[b]['rows'] if not r['typo']}
        diff = sorted(((rb[q]['useful'] - ra[q]['useful'], int(rb[q]['first_ok']) - int(ra[q]['first_ok']), q) for q in ra), key=lambda x: (x[1], x[0]))
        worse = [d for d in diff if d[1] < 0 or d[0] <= -2]
        better = [d for d in diff if d[1] > 0 or d[0] >= 2]
        text += [f'## {b} against {a}', '', f'Better: {len(better)} questions. Worse: {len(worse)}.', '']
        for title, ds in (('Worse', worse), ('Better', better[::-1])):
            text.append(f'{title}:')
            for du, df, q in ds[:15]:
                text.append(f"- {q} (useful {ra[q]['useful']}→{rb[q]['useful']}, first {'ok' if ra[q]['first_ok'] else 'wrong'}→{'ok' if rb[q]['first_ok'] else 'wrong'}): first now *{rb[q]['titles'][0] if rb[q]['titles'] else '-'}*")
            text.append('')
    Path(out).write_text('\n'.join(text), encoding='utf-8')
    print('\n'.join(text))


if __name__ == '__main__':
    main()
