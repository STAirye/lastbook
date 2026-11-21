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
out = {}
for c in [c for c in C.cases() if c['typo_of'] is None]:
    q = c['q']; fixed = typos.correct(q)
    sign = bool(A.danger_signs(q)); urg = bool(confidence.urgent(q, fixed, None)); s = m.score(fixed or q)
    d = out.setdefault(c['colour'], {'n': 0, 'sign': 0, 'urgent_words': 0, 'words': 0, 'meaning_wide': 0, 'meaning_strict': 0,
                                    'words_or_wide': 0, 'words_or_strict': 0, 'ex': []})
    w = sign or urg
    d['n'] += 1; d['sign'] += sign; d['urgent_words'] += urg; d['words'] += w
    d['meaning_wide'] += s > m.threshold; d['meaning_strict'] += s > m.strict
    d['words_or_wide'] += w or s > m.threshold; d['words_or_strict'] += w or s > m.strict
    if c['colour'] == 'green' and w and len(d['ex']) < 12:
        d['ex'].append((q, sorted(A.danger_signs(q)), urg))
print('thresholds wide', m.threshold, 'strict', m.strict)
for k, d in out.items():
    print(k, {x: y for x, y in d.items() if x != 'ex'})
for e in out['green']['ex']:
    print('  green, words fire:', e)
meaning_red.stop()
