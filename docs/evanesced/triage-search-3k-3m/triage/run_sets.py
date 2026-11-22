r"""Extra labelled sets (cases128.py, cases241.py) through one version of the code, in-process and read-only.

    set LASTBOOK_CODE=<worktree>  &  set LASTBOOK_DATA=<data folder>  [& set TH_KW=1]
    python -B -X utf8 run_sets.py OUT.json cases128 cases241

As run154.py / conf_eval.py: sections build refused, read-only index connections, vector file never truncated, no model.
Per case: the top 8 of assistant.hybrid (what /api/retrieve returns and the chat's first search uses), scored with
score.py's rules against the set's own P. On code with engine.confidence (the fork): also the chat's first search through
assistant.turn_hits([question]) -> route, is_danger, confidence (committed coefficients), and the chat's level after the
fork's everyday rule (assistant.chat: an everyday question gets buttons only below EVERYDAY_BUTTONS).
"""
import importlib.util, json, os, re, sqlite3, sys, time
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


SCORE = by_path('score')
SETS = {n: by_path(n) for n in sys.argv[2:]}

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

t0 = time.time()
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
assistant.init(server, server.INDEX)
state = server.INDEX.status.get('state')
print('code', ROOT, 'data', os.environ['LASTBOOK_DATA'], 'kw' if KW else 'hybrid', 'semantic', state, flush=True)
chat = confidence is not None and hasattr(assistant, 'turn_hits')

rows = []
for name, mod in SETS.items():
    SCORE.RX = {k: re.compile(v, re.I) for k, v in mod.P.items()}
    for c in mod.cases():
        rec = {'set': name, 'id': c['id'], 'q': c['q'], 'topic': c['topic'], 'colour': c['colour'], 'need': c['need'],
               'typo': bool(c.get('typo_of')), 'counter': bool(c['not_first'])}
        t1 = time.time()
        hits = assistant.hybrid(c['q'][:300], 8)
        rec['seconds'] = round(time.time() - t1, 3)
        s = SCORE.score(c, hits)
        s['top3_ok'] = any(any(SCORE.RX[k].search(SCORE.text(h)) for k in c['need']) for h in hits[:3])
        rec.update({k: s[k] for k in ('useful', 'first_ok', 'top3_ok', 'covered', 'context_share', 'wrong_sense_first', 'titles')})
        if chat:
            h2, info = assistant.turn_hits([{'role': 'user', 'content': c['q']}], None, True)
            conf = info.get('confidence') or {}
            p = conf.get('p')
            if p is None:
                level = None
            elif info['danger']:
                level = conf.get('level')
            else:
                level = confidence.everyday_level(p) if hasattr(confidence, 'everyday_level') else conf.get('level')
            rec.update(route=info['route'], danger=info['danger'], p=p, level=level,
                       same_hits=[(h['doc_id'], h.get('page')) for h in h2[:8]] == [(h['doc_id'], h.get('page')) for h in hits[:8]],
                       injury=confidence.injury(c['q']) if hasattr(confidence, 'injury') else None)
        rows.append(rec)
    print(name, 'done', round(time.time() - t0), 's', flush=True)
json.dump({'code': str(ROOT), 'data': os.environ['LASTBOOK_DATA'], 'mode': 'keyword' if KW else 'hybrid', 'semantic': state,
           'chat': chat, 'rows': rows, 'seconds': round(time.time() - t0, 1)},
          open(sys.argv[1], 'w', encoding='utf-8'), indent=0, ensure_ascii=False, default=str)
print('done', round(time.time() - t0), 's', flush=True)
