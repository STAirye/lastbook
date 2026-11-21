"""Through assistant.chat (model stood in for): where the articles land among the library pages, and which are useful."""
import json, os, re, sqlite3, sys
sys.path[:0] = [r'D:\git\lastbook', r'D:\git\lastbook\.claude\drafts\triage']
os.environ.pop('LASTBOOK_LOCAL_AI', None)
import retrieval; retrieval.AVAILABLE = False
from engine.paths import ro_uri
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None, check_same_thread=False)
_load = retrieval.Index._load; retrieval.Index._load = lambda self, truncate=True, db=None: _load(self, False, db)
import server, assistant as A
from engine import meaning_red
import cases as C
server.catalog(); server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB); A.init(server, server.INDEX)
meaning_red.wait(120)
ROOT = r'D:\LastbookData\library-data'
_fw = A.first_wiki; A.first_wiki = lambda q, root=None: _fw(q, root=ROOT)
seen = []
A._http_round = lambda msgs, tools, c, wrote, ss: (seen.append(msgs) or ('(answer)', {}))
pos, rows = [], []
for c in [c for c in C.cases() if c['typo_of'] is None and c['colour'] != 'red']:
    seen.clear(); pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
    A.chat([{'role': 'user', 'content': c['q']}], None, lambda e: None, lambda: False)
    if not seen:
        continue
    first = next((m['content'] for m in seen[0] if m['content'].startswith('Initial library search')), '')
    blocks = re.findall(r'<<SOURCE (S\d+).*?\n(.*?)<<END', first, re.S)
    kinds = [('W' if '(Encyclopedia article:' in b else 'L', bool(pat.search(b))) for _, b in blocks]
    if any(k == 'W' for k, _ in kinds):
        rows.append({'q': c['q'], 'order': ''.join(k + ('+' if u else '-') for k, u in kinds)})
json.dump(rows, open(r'D:\git\lastbook\.claude\drafts\encyclopedia\merge_chat.json', 'w', encoding='utf-8'), indent=1)
for r in rows: print(r['order'], '|', r['q'][:60])
meaning_red.stop()
