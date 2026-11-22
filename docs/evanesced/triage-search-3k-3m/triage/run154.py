r"""#154's 32 questions (cases154.py), clean and typo, through one version of the code, in-process and read-only.

    set LASTBOOK_CODE=<worktree>  &  set LASTBOOK_DATA=<data folder>  [& set TH_KW=1]
    python -B -X utf8 run154.py OUT.json

As conf_eval.py: sections build refused, read-only index connections, vector file never truncated, no model.
Per query: top 8 of assistant.hybrid (what /api/retrieve returns). On code with engine.confidence (the new fork), the
chat's first search instead: assistant.turn_hits([question]) -> hits (same search, route 'first'), its confidence
estimate (committed coefficients and cuts) and is_danger; also the trace.
"""
import importlib.util, inspect, json, os, sqlite3, sys, time
from pathlib import Path

ROOT = Path(os.environ['LASTBOOK_CODE'])
KW = os.environ.get('TH_KW') == '1'
TRIAGE = Path(__file__).resolve().parent
if not os.environ.get('LASTBOOK_DATA'):
    raise SystemExit('set LASTBOOK_DATA')
os.environ.pop('LASTBOOK_LOCAL_AI', None)
sys.path[:0] = [str(ROOT)]

spec = importlib.util.spec_from_file_location('cases154', TRIAGE / 'cases154.py')
C154 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C154)

import retrieval  # noqa: E402
if KW:
    retrieval.AVAILABLE = False
try:
    from engine import sections as _sections  # noqa: E402

    def _no_build(*a, **k):
        raise OSError('triage: sections build refused (read-only run)')
    _sections.build = _no_build
except ImportError:
    _sections = None
from engine.paths import ro_uri  # noqa: E402
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None,
                                                    check_same_thread=False)
_load = retrieval.Index._load
retrieval.Index._load = lambda self, truncate=True, db=None: _load(self, False, db)

import server, assistant  # noqa: E402
try:
    from engine import confidence  # noqa: E402
except ImportError:
    confidence = None
try:
    from engine import typos  # noqa: E402
except ImportError:
    typos = None

t0 = time.time()
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
assistant.init(server, server.INDEX)
state = server.INDEX.status.get('state')
print('code', ROOT, 'data', os.environ['LASTBOOK_DATA'], 'kw' if KW else 'hybrid', 'semantic', state,
      server.INDEX.status.get('chunks'), flush=True)
traced = 'trace' in inspect.signature(assistant.hybrid).parameters
chat = confidence is not None and hasattr(assistant, 'turn_hits')

rows = []
for i, c in enumerate(C154.CASES):
    for typo, q in ((False, c['q']), (True, c['typo'])):
        tr, rec = {}, {'i': i, 'q': q, 'typo': typo}
        t1 = time.time()
        if chat:
            hits, info = assistant.turn_hits([{'role': 'user', 'content': q}], None, True)
            # the same search again with a trace, to keep its signals (turn_hits keeps none)
            hits2 = assistant.hybrid(q[:300], 8, trace=tr)
            rec.update(route=info['route'], danger=info['danger'], confidence=info['confidence'],
                       same_as_traced=[(h['doc_id'], h.get('page')) for h in hits] == [(h['doc_id'], h.get('page')) for h in hits2],
                       urgent=confidence.urgent(q, typos.correct(q) if typos else None),
                       danger_signs=sorted(assistant.danger_signs(q)) if hasattr(assistant, 'danger_signs') else None,
                       corrected=typos.correct(q) if typos else None,
                       features=confidence.features(hits2[:8], tr) if 'groups' in tr else None)
        elif traced:
            hits = assistant.hybrid(q[:200], 8, trace=tr)
        else:
            hits = assistant.hybrid(q[:200], 8)
        rec['seconds'] = round(time.time() - t1, 3)
        rec['hits'] = [{x: h.get(x) for x in ('doc_id', 'page', 'kind', 'title', 'excerpt', 'found_by', 'score')} for h in hits[:8]]
        rec['trace'] = tr
        rows.append(rec)
    print(f'{i + 1}/{len(C154.CASES)}', flush=True)
json.dump({'code': str(ROOT), 'data': os.environ['LASTBOOK_DATA'], 'mode': 'keyword' if KW else 'hybrid', 'semantic': state,
           'chat': chat, 'rows': rows, 'seconds': round(time.time() - t0, 1)},
          open(sys.argv[1], 'w', encoding='utf-8'), indent=0, ensure_ascii=False, default=str)
print('done', round(time.time() - t0), 's', flush=True)
