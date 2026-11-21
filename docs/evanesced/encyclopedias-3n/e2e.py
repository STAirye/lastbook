"""End to end on the real library: urgent label first, encyclopedias in parallel, the merge. Keyword-only, no AI model."""
import json, os, re, sqlite3, sys, time, statistics as st
sys.path[:0] = [r'D:\git\lastbook', r'D:\git\lastbook\.claude\drafts\triage']
os.environ.pop('LASTBOOK_LOCAL_AI', None)
import retrieval
retrieval.AVAILABLE = False
from engine import sections as _s
from engine.paths import ro_uri
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None, check_same_thread=False)
_load = retrieval.Index._load
retrieval.Index._load = lambda self, truncate=True, db=None: _load(self, False, db)
import server, assistant as A
from engine import meaning_red
import cases as C
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
A.init(server, server.INDEX)
print('meaning check ready', meaning_red.wait(120), flush=True)
ROOT = r'D:\LastbookData\library-data'
wt = {}
_fw = A.first_wiki
def timed(q, root=None):
    t = time.perf_counter(); r = _fw(q, root=ROOT); wt[q] = (time.perf_counter() - t) * 1000; return r
A.first_wiki = timed
rows = []
for c in [c for c in C.cases() if c['typo_of'] is None]:
    q = c['q']; msgs = [{'role': 'user', 'content': q}]
    pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
    t0 = time.perf_counter(); job = A.WikiJob(q); t1 = time.perf_counter()
    hits, turn = A.turn_hits(msgs, None, True); t2 = time.perf_counter()
    wiki = job.result(q, turn); t3 = time.perf_counter()
    lib = [(h, A.excerpt_body(h), f'L{i}') for i, h in enumerate(hits)]
    art = [(h, f'W{i}') for i, h in enumerate(wiki)]
    order = A.merge_first(lib, art, A.wiki_q(q, turn))
    first_w = next((i for i, b in enumerate(order) if b.startswith('W')), None)
    rows.append({'q': q, 'colour': c['colour'], 'urgent': job.urgent or bool(turn.get('danger')), 'label_ms': (t1 - t0) * 1000,
                 'lib_ms': (t2 - t1) * 1000, 'wait_ms': (t3 - t2) * 1000, 'wiki_ms': wt.get(job.q, 0) if not job.urgent else 0,
                 'n_wiki': len(wiki), 'useful': [bool(pat.search(h['excerpt'] + ' ' + h['title'])) for h in wiki],
                 'first_wiki_pos': first_w, 'n_lib': len(hits), 'order': order})
json.dump(rows, open(r'D:\git\lastbook\.claude\drafts\encyclopedia\e2e.json', 'w', encoding='utf-8'), indent=1)
for col in ('red', 'yellow', 'green'):
    R = [r for r in rows if r['colour'] == col]
    print(col, len(R), 'labelled urgent', sum(r['urgent'] for r in R), 'with articles', sum(r['n_wiki'] > 0 for r in R),
          'articles', sum(r['n_wiki'] for r in R), 'useful', sum(sum(r['useful']) for r in R))
N = [r for r in rows if not r['urgent']]
print('label ms median', round(st.median(r['label_ms'] for r in rows), 1))
print('library ms median', round(st.median(r['lib_ms'] for r in rows)), '| encyclopedia ms median (not urgent)', round(st.median(r['wiki_ms'] for r in N)))
print('serial (lib + wiki) median', round(st.median(r['lib_ms'] + r['wiki_ms'] for r in N)),
      '| parallel (lib + wait) median', round(st.median(r['lib_ms'] + r['wait_ms'] for r in N)))
print('an article above some library page', sum(1 for r in N if r['first_wiki_pos'] is not None and r['first_wiki_pos'] < r['n_lib']), 'of', sum(r['n_wiki'] > 0 for r in N))
meaning_red.stop()
