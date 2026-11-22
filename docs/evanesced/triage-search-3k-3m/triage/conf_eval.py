r"""Signals and labels for search confidence, in-process (no servers, no model). Read-only on the data folder.

    set LASTBOOK_DATA=D:\LastbookData-fork-test
    set LASTBOOK_CODE=D:\git\lastbook\.claude\worktrees\search-confidence
    python -B -X utf8 conf_eval.py OUT.json          (TH_KW=1: keyword-only, as the desktop app ships)

Per labelled question: the top 8 of assistant.hybrid (as /api/retrieve and the chat's first search), engine.confidence
features from its trace, and score.py's labels. Plus the conversations (convos.py): turn_hits on the last message with
cited replies, and the features of its own and joined searches.
"""
import importlib.util, json, os, sqlite3, sys, time
from pathlib import Path

ROOT = Path(os.environ['LASTBOOK_CODE'])
KW = os.environ.get('TH_KW') == '1'
TRIAGE = Path(__file__).resolve().parent
if not os.environ.get('LASTBOOK_DATA'):
    raise SystemExit('set LASTBOOK_DATA')
os.environ.pop('LASTBOOK_LOCAL_AI', None)
sys.path[:0] = [str(ROOT)]


def by_path(name):
    spec = importlib.util.spec_from_file_location(name, TRIAGE / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = by_path('cases')
SCORE = by_path('score')
CONVOS = by_path('convos').CONVOS

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
from engine import confidence  # noqa: E402

t0 = time.time()
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
assistant.init(server, server.INDEX)
print('code', ROOT, 'semantic', server.INDEX.status.get('state'), server.INDEX.status.get('chunks'), flush=True)

rows = []
for c in CASES.cases():
    tr = {}
    t1 = time.time()
    hits = assistant.hybrid(c['q'][:300], 8, trace=tr)
    dt = time.time() - t1
    s = SCORE.score(c, hits)
    danger = bool(assistant.danger_signs(c['q'] + ' ' + tr.get('q', '')))
    f = confidence.features(hits, tr, danger)
    rows.append({'id': c['id'], 'q': c['q'], 'corrected': tr.get('q'), 'topic': c['topic'], 'colour': c['colour'],
                 'typo': bool(c['typo_of']), 'counter': bool(c['not_first']), 'danger': danger, 'seconds': round(dt, 3),
                 'first_ok': s['first_ok'], 'useful': s['useful'], 'covered': s['covered'], 'f': f,
                 'titles': s['titles'][:3], 'trace': tr,
                 'hits': [{x: h.get(x) for x in ('doc_id', 'page', 'kind', 'title', 'excerpt', 'found_by', 'score')} for h in hits]})
print(f'{len(rows)} cases in {time.time() - t0:.0f}s', flush=True)

# conversations: last message, cited replies (as turnhits_eval.py), features of own and joined searches
def cite(hits):
    pdf = [h for h in hits if h.get('kind') == 'pdf' and h.get('page')][:3]
    return 'From the library: ' + ' '.join(f'Step {n + 1} ({h["title"]}, p. {h["page"]}).' for n, h in enumerate(pdf))

conv = []
_h = assistant.hybrid
for c in CONVOS:
    msgs, hits = [], []
    for msg, _ in c['turns']:
        if msgs:
            msgs.append({'role': 'assistant', 'content': cite(hits)})
        msgs.append({'role': 'user', 'content': msg})
        calls = []
        def spy(q, k=8, kind='any', doc=None, trace=None):
            tr = trace if trace is not None else {}
            hs = _h(q, k, kind, doc, trace=tr)
            calls.append((q, hs, tr))
            return hs
        assistant.hybrid = spy
        try:
            hits, info = assistant.turn_hits(msgs, None, True)
        finally:
            assistant.hybrid = _h
    s = SCORE.score(c, hits)
    last = c['turns'][-1][0]
    danger = bool(assistant.danger_signs(last))
    fs = [{'q': q, 'f': confidence.features(hs, tr, danger)} for q, hs, tr in calls]
    conv.append({'name': c.get('name') or c['turns'][0][0][:40], 'kind': c['turns'][-1][1], 'route': info['route'],
                 'first_ok': s['first_ok'], 'useful': s['useful'], 'calls': fs, 'colour': c.get('colour')})
json.dump({'mode': 'keyword' if KW else 'hybrid', 'rows': rows, 'convos': conv}, open(sys.argv[1], 'w', encoding='utf-8'),
          indent=0, ensure_ascii=False)
print('done', time.time() - t0, flush=True)
