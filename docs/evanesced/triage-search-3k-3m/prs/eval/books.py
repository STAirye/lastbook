"""Count questions whose top 8 hold a whole-book page. argv: sections file, catalog.json, rows json files..."""
import json, sqlite3, sys
from collections import Counter

sec, catf, files = sys.argv[1], sys.argv[2], sys.argv[3:]
con = sqlite3.connect(f'file:{sec}?mode=ro', uri=True)
long_ids = {d for (d,) in con.execute('SELECT doc_id FROM long')}
with open(catf, encoding='utf-8') as fh:
    cat = json.load(fh)
items = cat['items'] if isinstance(cat, dict) and 'items' in cat else cat
long_titles = {r['title'] for r in items if r.get('id') in long_ids}
MSP = 'Modern Machine-Shop Practice'
print('long titles', len(long_titles), 'machine-shop titles:', [t for t in long_titles if 'Machine-Shop' in t])


def title_of(s):
    return s.rsplit(' p.', 1)[0]


for f in files:
    with open(f, encoding='utf-8') as fh:
        d = json.load(fh)
    rows = d['rows']
    out = {}
    for name, sel in (('triage (362)', lambda r: r['set'] == 'triage'),
                      ('triage clean (253)', lambda r: r['set'] == 'triage' and not r.get('typo')),
                      ('all scored questions', lambda r: True)):
        rs = [r for r in rows if sel(r) and 'titles' in r]
        msp = sum(any(title_of(t).startswith(MSP) for t in r['titles'][:8]) for r in rs)
        anyl = sum(any(title_of(t) in long_titles for t in r['titles'][:8]) for r in rs)
        slots = sum(sum(title_of(t) in long_titles for t in r['titles'][:8]) for r in rs)
        out[name] = {'n': len(rs), 'machine_shop_in_top8': msp, 'any_whole_book_in_top8': anyl, 'whole_book_slots': slots}
    top = Counter(title_of(t) for r in rows if r['set'] == 'triage' for t in r['titles'][:8] if title_of(t) in long_titles)
    print(f, json.dumps(out, indent=1))
    print('  most frequent whole books (triage):', top.most_common(5))
