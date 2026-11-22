"""Scratch: does widening the fork's fire/water phrase 'unless' fix #128's review counterexamples without losing how-to gains?
In-process, keyword-only and hybrid (TH_KW), read-only (as run_sets.py). Prints first_ok changes, base vs patched."""
import importlib.util, json, os, re, sqlite3, sys
TRI = r'D:\git\lastbook\.claude\drafts\triage'
ROOT = os.environ['LASTBOOK_CODE']; sys.path[:0] = [ROOT]
os.environ.pop('LASTBOOK_LOCAL_AI', None)
def by_path(n):
    s = importlib.util.spec_from_file_location(n, os.path.join(TRI, n + '.py')); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
SCORE = by_path('score')
import retrieval
if os.environ.get('TH_KW') == '1':
    retrieval.AVAILABLE = False
from engine import sections as _s
_s.build = lambda *a, **k: (_ for _ in ()).throw(OSError('ro'))
from engine.paths import ro_uri
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None, check_same_thread=False)
_l = retrieval.Index._load
retrieval.Index._load = lambda self, truncate=True, db=None: _l(self, False, db)
import server, assistant
server.catalog(); server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB); assistant.init(server, server.INDEX)

sets = []
for n in ('cases', 'cases128', 'cases241'):
    m = by_path(n); sets.append((n, m.P, m.cases()))
c154 = by_path('cases154')
cs = []
for i, c in enumerate(c154.CASES):
    cs.append(dict(c, id=f'154.{i}', typo_of=None)); cs.append(dict(c, q=c['typo'], id=f'154.{i}t', typo_of=c['q']))
sets.append(('cases154', c154.P, cs))

ORIG = list(server.PHRASES)
FIRE_UNLESS = r"|\b(prevent\w*|avoid\w*|stop\w*|risk\w*|hazard\w*|caus\w*|escape|spread\w*|safety|drill)\b"
WATER_UNLESS = r"|\b(intoxicat\w*|poison\w*|lungs?|overdos\w*)\b"
def patched():
    out = []
    for item in ORIG:
        rx = item[0]
        if 'tinder' in json.dumps(item[1]):
            item = (item[0], item[1], item[2] + FIRE_UNLESS) + tuple(item[3:])
        elif 'disinfect' in json.dumps(item[1]) and len(item) > 2:
            item = (item[0], item[1], item[2] + WATER_UNLESS) + tuple(item[3:])
        out.append(item)
    return out

res = {}
for arm, ph in (('base', ORIG), ('patched', patched())):
    server.PHRASES[:] = ph
    server.find.cache_clear()
    for n, P, cases in sets:
        SCORE.RX = {k: re.compile(v, re.I) for k, v in P.items()}
        for c in cases:
            hits = assistant.hybrid(c['q'][:300], 8)
            s = SCORE.score(c, hits)
            res.setdefault((n, c['id'], c['q']), {})[arm] = (int(s['first_ok']), s['useful'], s['titles'][0][:50] if s['titles'] else '')
ch = [(k, v) for k, v in res.items() if v["base"] != v["patched"]]
print('mode', 'kw' if os.environ.get('TH_KW') == '1' else 'hy', 'cases', len(res), 'changed', len(ch))
print('first_ok base', sum(v['base'][0] for v in res.values()), 'patched', sum(v['patched'][0] for v in res.values()))
print('useful base', sum(v['base'][1] for v in res.values()), 'patched', sum(v['patched'][1] for v in res.values()))
for k, v in ch:
    print(k[0], k[2][:60], v['base'], '->', v['patched'])
