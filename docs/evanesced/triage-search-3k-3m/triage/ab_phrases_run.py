r"""A/B of the phrase fixes (docs/FORK.md 3h): four arms in one process, in-process and read-only.

    set LASTBOOK_CODE=D:\git\lastbook\.claude\worktrees\phrase-injury  &  set LASTBOOK_DATA=D:\LastbookData-fork-test
    python -B -X utf8 ab_phrases_run.py OUT.json        (TH_KW=1: keyword-only, as the desktop app ships)

Arms: base (LASTBOOK_PHRASE_INJURY=0, LASTBOOK_PHRASE_RETRY=0), A (injury exception), B (retry without the helpers), AB.
Per question of cases.py (362) and cases154.py (32 + typos): the chat's first search, assistant.turn_hits([question])
(hits, danger, confidence with the committed coefficients), the groups and helpers of server.query_groups, and the
keyword trace. As run154.py: sections build refused, read-only index connections, no model.
"""
import importlib.util, json, os, sqlite3, sys, time
from pathlib import Path

ROOT = Path(os.environ['LASTBOOK_CODE'])
KW = os.environ.get('TH_KW') == '1'
T = Path(__file__).resolve().parent
if not os.environ.get('LASTBOOK_DATA'):
    raise SystemExit('set LASTBOOK_DATA')
os.environ.pop('LASTBOOK_LOCAL_AI', None)
sys.path[:0] = [str(ROOT)]


def by_path(name):
    spec = importlib.util.spec_from_file_location(name, T / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = by_path('cases').cases()
C154 = by_path('cases154').CASES

import retrieval  # noqa: E402
if KW:
    retrieval.AVAILABLE = False
from engine import sections as _sections  # noqa: E402


def _no_build(*a, **k):
    raise OSError('triage: sections build refused (read-only run)')


_sections.build = _no_build
from engine.paths import ro_uri  # noqa: E402
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None,
                                                    check_same_thread=False)
_load = retrieval.Index._load
retrieval.Index._load = lambda self, truncate=True, db=None: _load(self, False, db)

import server, assistant  # noqa: E402

t0 = time.time()
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
assistant.init(server, server.INDEX)
state = server.INDEX.status.get('state')
print('code', ROOT, 'kw' if KW else 'hybrid', 'semantic', state, flush=True)

ARMS = {'base': ('0', '0'), 'A': ('1', '0'), 'B': ('0', '1'), 'AB': ('1', '1')}
QS = [('cases', c['id'], c['q']) for c in CASES] + \
     [('c154', f'{i}' + ('t' if typo else ''), q) for i, c in enumerate(C154) for typo, q in ((False, c['q']), (True, c['typo']))]

out = {'mode': 'keyword' if KW else 'hybrid', 'semantic': state, 'arms': {}}
_traced = assistant._traced
for arm, (inj, rty) in ARMS.items():
    os.environ['LASTBOOK_PHRASE_INJURY'], os.environ['LASTBOOK_PHRASE_RETRY'] = inj, rty
    server.find.cache_clear()
    t1, rows = time.time(), []
    for src, qid, q in QS:
        traces = []

        def spy(q2, k=8, tr=None):
            hs = _traced(q2, k, tr)
            traces.append(dict(tr) if tr is not None else {})
            return hs
        assistant._traced = spy
        try:
            hits, info = assistant.turn_hits([{'role': 'user', 'content': q}], None, True)
        finally:
            assistant._traced = _traced
        qi = {}
        content, groups = server.query_groups(q, qi)
        tr = traces[0] if traces else {}
        rows.append({'src': src, 'id': qid, 'q': q, 'groups': groups, 'helpers': qi['helpers'], 'route': info['route'],
                     'danger': info['danger'], 'confidence': info['confidence'],
                     'strict': tr.get('strict'), 'retry': tr.get('retry'), 'any_word': tr.get('any_word'),
                     'hits': [{x: h.get(x) for x in ('doc_id', 'page', 'kind', 'title', 'excerpt')} for h in hits[:8]]})
    out['arms'][arm] = rows
    print(arm, len(rows), round(time.time() - t1), 's', flush=True)
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=0, ensure_ascii=False, default=str)
print('done', round(time.time() - t0), 's', flush=True)
