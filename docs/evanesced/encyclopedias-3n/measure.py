"""Do encyclopedia articles need the fork's long-page sections? Measures length and where the useful words sit."""
import json, re, sys, time, statistics as st
from pathlib import Path
sys.path.insert(0, r'D:\git\lastbook'); sys.path.insert(0, r'D:\git\lastbook\.claude\drafts\triage')
from engine import encyclopedias as E
import cases as C
ROOT = r'D:\LastbookData\library-data'
rows = [c for c in C.cases() if c['typo_of'] is None and c['colour'] in ('red', 'yellow', 'green')]
out, t0 = [], time.time()
for c in rows:
    pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
    t = time.time()
    hits = E.search(c['q'][:300], limit=E.INITIAL_LIMIT, excerpt=0, read_text=False, root=ROOT)
    for rank, h in enumerate(hits):
        arc = E._open_archive(E.zim_path(h['zim'], ROOT))
        got = E.entry_text(arc, h['article'], cap=None)
        if not got:
            continue
        title, text = got
        m = pat.search(text)
        out.append({'id': c['id'], 'colour': c['colour'], 'q': c['q'], 'rank': rank, 'zim': h['zim'][:9], 'title': title,
                    'len': len(text), 'any': bool(m), 'first_at': m.start() if m else None,
                    'head2000': bool(pat.search(text[:E.INITIAL_CHARS])),
                    'pick2000': bool(pat.search(E.pick_section(text, c['q'], E.INITIAL_CHARS))),
                    'ms': round((time.time() - t) * 1000)})
Path(r'D:\git\lastbook\.claude\drafts\encyclopedia\measure.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
L = [r['len'] for r in out]
print('questions', len(rows), 'articles', len(out), 'secs', round(time.time() - t0))
print('len median', st.median(L), 'p90', sorted(L)[int(.9 * len(L))], 'max', max(L))
for cut in (2000, 5000, 20000, 100000):
    print(f'  > {cut}:', sum(l > cut for l in L))
print('need words anywhere', sum(r['any'] for r in out), '| first 2000 (now)', sum(r['head2000'] for r in out),
      '| pick_section 2000', sum(r['pick2000'] for r in out))
for col in ('red', 'yellow', 'green'):
    R = [r for r in out if r['colour'] == col]
    print(col, len(R), 'any', sum(r['any'] for r in R), 'head', sum(r['head2000'] for r in R), 'pick', sum(r['pick2000'] for r in R))
print('longest top-1 hits:')
for r in sorted([r for r in out if r['rank'] == 0], key=lambda r: -r['len'])[:12]:
    print(f"  {r['len']:>8} {r['zim']} {r['title'][:60]!r} <- {r['q'][:50]!r}")
