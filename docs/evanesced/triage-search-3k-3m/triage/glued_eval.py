r"""Glued words and the unknown-word rule (engine/typos.py splitting, engine/confidence.unknown_words), in-process.

    set LASTBOOK_DATA=D:\LastbookData-fork-test
    set LASTBOOK_CODE=<worktree>              (before: fe635e7, after: fork/glued-words)
    python -B -X utf8 glued_eval.py OUT.json  (TH_KW=1: keyword-only, as the desktop app ships)

Read-only on the data folder (sections.build refused, the semantic index opened read-only, as conf_eval.py). Per question,
as the first message of a chat: what was searched (typos.correct), urgent (assistant.is_danger), turn_hits' route and
confidence, what the chat would do with it (chat_outcome: the same steps as assistant.chat), and whether the first page
matches need[0]. Sets: cases_glued.py, cases.py (362), cases154.py (32 + their typos).
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


CASES = by_path('cases')
C154 = by_path('cases154')
GLUED = by_path('cases_glued').CASES
SCORE = by_path('score')

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
from engine import confidence, typos  # noqa: E402

AFTER = hasattr(confidence, 'unknown_words')
RX = {k: re.compile(v, re.I) for k, v in C154.P.items()}


def chat_outcome(turn):
    """As assistant.chat for a first message: 'ask' (help me help you + buttons), 'buttons' (answer + buttons) or 'answer'."""
    conf, route = turn['confidence'], turn['route']
    level = conf['level'] if conf and route != 'noise' else 'sure'
    if not turn.get('danger') and conf and route != 'noise':
        level = confidence.everyday_level(conf['p'])
    if level == 'unsure' and route not in ('first', 'danger'):
        level = 'buttons'
    if AFTER and route == 'noise' and not turn.get('still'):
        level = 'unsure'
    return 'ask' if level == 'unsure' else 'buttons' if (turn['buttons'] or level != 'sure') else 'answer'


def one(q, need):
    t1 = time.perf_counter()
    searched = typos.correct(q)
    split_ms = (time.perf_counter() - t1) * 1000
    hits, turn = assistant.turn_hits([{'role': 'user', 'content': q}], None, True)
    first = (hits[0]['title'] + ' ' + (hits[0].get('excerpt') or '')) if hits else ''
    conf = turn.get('confidence') or {}
    return {'q': q, 'searched': searched, 'typo_ms': round(split_ms, 1), 'urgent': bool(turn.get('danger')),
            'route': turn['route'], 'p': conf.get('p'), 'p_fitted': conf.get('p_fitted', conf.get('p')),
            'unknown_words': bool(conf.get('unknown_words')), 'outcome': chat_outcome(turn),
            'first_ok': bool(need) and bool(hits) and bool(RX[need[0]].search(first)),
            'first': hits[0]['title'][:60] if hits else None}


t0 = time.time()
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
assistant.init(server, server.INDEX)
typos.words_for()
assistant._vocab()
print('code', ROOT, 'after' if AFTER else 'before', 'semantic', server.INDEX.status.get('state'), flush=True)

out = {'glued': [], 'cases': [], 'c154': []}
for c in GLUED:
    out['glued'].append(dict(one(c['q'], c['need']), kind=c['kind'], want=c['split'], red=c['red'], want_unsure=c['unsure']))
for c in CASES.cases():
    r = one(c['q'][:300], c['need'])
    s = None
    out['cases'].append(dict(r, id=c['id'], typo=bool(c['typo_of'])))
for i, c in enumerate(C154.CASES):
    for typo, q in ((False, c['q']), (True, c['typo'])):
        out['c154'].append(dict(one(q, c['need']), id=f'{i}{"t" if typo else ""}', typo=typo))
# speed of typos.correct on every question, memo cleared (the vocabulary stays cached)
qs = [r['q'] for k in out for r in out[k]]
typos._state['memo'].clear()
t1 = time.perf_counter()
for q in qs:
    typos.correct(q)
out['speed'] = {'questions': len(qs), 'ms_per_question': round((time.perf_counter() - t1) * 1000 / len(qs), 2)}
gl = [r['q'] for r in out['glued']]
typos._state['memo'].clear()
t1 = time.perf_counter()
for q in gl:
    typos.correct(q)
out['speed']['glued_ms_per_question'] = round((time.perf_counter() - t1) * 1000 / len(gl), 2)
out['speed']['max_ms'] = max(r['typo_ms'] for k in ('glued', 'cases', 'c154') for r in out[k])
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
print(f'done in {time.time() - t0:.0f}s', out['speed'], flush=True)
