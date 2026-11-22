r"""Body signs and the fire/water phrase exceptions (fork/body-signs), before vs after, in-process and read-only.

    set LASTBOOK_CODE=<worktree>  &  set LASTBOOK_DATA=D:\LastbookData-fork-test  [& set TH_KW=1]
    python -B -X utf8 body_eval.py OUT.json

As run_sets.py / glued_eval.py / turnhits_eval.py: sections build refused, read-only index connections, vector file never
truncated, no model. Every set: cases.py (362), cases154.py (32 + typos), cases128.py, cases241.py, cases_glued.py, and the
52 conversations (convos.py, last message, replies that cite the previous turn's top 3 PDF pages). Per question: the chat's
first search (assistant.turn_hits), scored with score.py against the set's own P, and what the chat does with it
(assistant.chat_level when the code has it, else the same steps as 9712522's chat()): answer / buttons / ask (the bare
"help me help you") / ask+pages (UNSURE_DANGER). Also: what was searched, is_danger, the URGENT words and DANGER signs that
matched, and (after) the body signs.
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
CASES, C154, C128, C241 = by_path('cases'), by_path('cases154'), by_path('cases128'), by_path('cases241')
GLUED = by_path('cases_glued').CASES
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
from engine import confidence, typos  # noqa: E402

AFTER = hasattr(assistant, 'chat_level')


def level_before(turn, followup=True, asked=1):
    """9712522's chat(): the same steps, for code without chat_level."""
    conf = turn.get('confidence')
    level = conf['level'] if conf and turn['route'] != 'noise' else 'sure'
    if not turn.get('danger') and conf and turn['route'] != 'noise':
        level = confidence.everyday_level(conf['p'])
    if level == 'unsure' and (turn['route'] not in ('first', 'danger') or (not followup and asked > 1)):
        level = 'buttons'
    if turn['route'] == 'noise' and not turn.get('still'):
        level = 'unsure'
    return level


def action(turn, asked=1):
    level = assistant.chat_level(turn, True, asked)[0] if AFTER else level_before(turn, True, asked)
    if level == 'unsure':
        return 'ask+pages' if turn.get('danger') else 'ask'
    return 'buttons' if (turn['buttons'] or level != 'sure') else 'answer'


_cache = {}
_hybrid = assistant.hybrid
def cached(q, k=8, kind='any', doc=None, trace=None):
    if kind != 'any' or doc:
        return _hybrid(q, k, kind, doc)
    if (q, k) not in _cache:
        tr = {}
        _cache[(q, k)] = (_hybrid(q, k, trace=tr), tr)
    hits, tr = _cache[(q, k)]
    if trace is not None:
        trace.update(tr)
    return [dict(h) for h in hits]
assistant.hybrid = cached


def facts(q, turn, hits, c, scorable):
    corrected = typos.correct(q)
    t = (q + ' ' + corrected).lower().replace('’', "'")
    rec = {'q': q, 'searched': corrected, 'danger': bool(turn.get('danger')), 'route': turn['route'],
           'p': (turn.get('confidence') or {}).get('p'), 'level': (turn.get('confidence') or {}).get('level'),
           'unknown_words': bool((turn.get('confidence') or {}).get('unknown_words')),
           'urgent_words': sorted({m.group(0).lower() for m in confidence.URGENT.finditer(t)}),
           'danger_signs': sorted(assistant.danger_signs(q)), 'body': turn.get('body'),
           'n_hits': len(hits), 'first': (hits[0]['title'][:70] + ' p.' + str(hits[0].get('page'))) if hits else None,
           'keys': [[h['doc_id'], h.get('page')] for h in hits[:8]]}
    if scorable:
        s = SCORE.score(c, hits)
        s['top3_ok'] = any(any(SCORE.RX[k].search(SCORE.text(h)) for k in c['need']) for h in hits[:3])
        rec.update({k: s[k] for k in ('useful', 'first_ok', 'top3_ok', 'wrong_sense_first')})
    else:
        rec.update(useful=None, first_ok=None, top3_ok=None, wrong_sense_first=None)
    return rec


def sets():
    yield 'cases', CASES.P, [dict(c) for c in CASES.cases()]
    cs = []
    for i, c in enumerate(C154.CASES):
        cs.append(dict(c, id=f'154.{i}', typo_of=None))
        cs.append(dict(c, q=c['typo'], id=f'154.{i}t', typo_of=c['q']))
    yield 'cases154', C154.P, cs
    yield 'cases128', C128.P, C128.cases()
    yield 'cases241', C241.P, C241.cases()
    yield 'cases_glued', C154.P, [{'q': g['q'], 'id': f'g.{i:02d}', 'need': g['need'], 'not_first': [], 'context': [],
                                   'colour': 'red' if g['red'] else 'green', 'kind': g['kind'], 'typo_of': None}
                                  for i, g in enumerate(GLUED)]


def cite(hits):
    pdf = [h for h in hits if h.get('kind') == 'pdf' and h.get('page')][:3]
    return 'From the library: ' + ' '.join(f'Step {n + 1} ({h["title"]}, p. {h["page"]}).' for n, h in enumerate(pdf))


t0 = time.time()
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
assistant.init(server, server.INDEX)
typos.words_for()
assistant._vocab()
print('code', ROOT, 'after' if AFTER else 'before', 'kw' if KW else 'hybrid', 'semantic', server.INDEX.status.get('state'),
      flush=True)
rows = []
for name, P, cases in sets():
    SCORE.RX = {k: re.compile(v, re.I) for k, v in P.items()}
    for c in cases:
        q = c['q']
        hits, turn = assistant.turn_hits([{'role': 'user', 'content': q}], None, True)
        rec = facts(q, turn, hits, c, bool(c['need']))
        rec.update(set=name, id=c['id'], colour=c.get('colour'), need=c['need'], typo=bool(c.get('typo_of')),
                   counter=bool(c.get('not_first')), action=action(turn))
        rows.append(rec)
    print(name, len(cases), round(time.time() - t0), 's', flush=True)
SCORE.RX = {k: re.compile(v, re.I) for k, v in CASES.P.items()}
for i, c in enumerate(CONVOS):
    msgs, hits = [], []
    for msg, _ in c['turns']:
        if msgs:
            msgs.append({'role': 'assistant', 'content': cite(hits)})
        msgs.append({'role': 'user', 'content': msg})
        hits, turn = assistant.turn_hits(msgs, None, True)
    q = c['turns'][-1][0]
    rec = facts(q, turn, hits, c, True)
    rec.update(set='convos', id=f'c.{i:02d}', colour=c['colour'], need=c['need'], typo=False, counter=False,
               kind=c['turns'][-1][1], turns=[m for m, _ in c['turns']], action=action(turn, len(c['turns'])))
    rows.append(rec)
print('convos', len(CONVOS), round(time.time() - t0), 's', flush=True)
json.dump({'code': str(ROOT), 'after': AFTER, 'data': os.environ['LASTBOOK_DATA'], 'mode': 'keyword' if KW else 'hybrid',
           'semantic': server.INDEX.status.get('state'), 'rows': rows, 'seconds': round(time.time() - t0, 1)},
          open(sys.argv[1], 'w', encoding='utf-8'), indent=0, ensure_ascii=False, default=str)
print('done', round(time.time() - t0), 's', flush=True)
