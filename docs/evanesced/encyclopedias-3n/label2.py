import json, os, sqlite3, sys
sys.path[:0] = [r'D:\git\lastbook', r'D:\git\lastbook\.claude\drafts\triage']
import retrieval; retrieval.AVAILABLE = False
from engine.paths import ro_uri
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None, check_same_thread=False)
_load = retrieval.Index._load; retrieval.Index._load = lambda self, truncate=True, db=None: _load(self, False, db)
import server, assistant as A
from engine import meaning_red, typos, confidence
import cases as C
server.catalog(); server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB); A.init(server, server.INDEX)
meaning_red.wait(120); m = meaning_red._model
res = {}; miss = []
for c in [c for c in C.cases() if c['typo_of'] is None]:
    q = c['q']; f = typos.correct(q); sign = bool(A.danger_signs(q + ' ' + A._search_words(q))); body = bool(confidence.body_signs(q, f, None))
    s = m.score(f or q)
    for name, v in (('sign|strict', sign or s > m.strict), ('sign|wide', sign or s > m.threshold),
                    ('sign|body|strict', sign or body or s > m.strict), ('sign|body|wide', sign or body or s > m.threshold)):
        res.setdefault(name, {}).setdefault(c['colour'], 0); res[name][c['colour']] += v
    if c['colour'] == 'red' and not (sign or body or s > m.threshold):
        miss.append(q)
for k, v in res.items(): print(k, v, '(of red 131, yellow 58, green 64)')
print('red missed by sign|body|wide:', miss)
meaning_red.stop()
