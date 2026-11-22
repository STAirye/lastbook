"""Score assistant.turn_hits on the invented conversations, in-process: no HTTP server, no model, no background indexer.

    set LASTBOOK_DATA=D:\\LastbookData
    python -B -X utf8 .claude/drafts/turnhits_eval.py [TRIAGE_DIR]

TRIAGE_DIR (default D:\\git\\lastbook\\.claude\\drafts\\triage) holds convos.py and score.py. Read-only on the data folder:
the semantic index is opened with read-only connections and its vector file is never truncated.
Two runs: assistant replies empty (nothing for cited_before to carry), and replies that cite the previous turn's top 3
PDF pages as "(Title, p. N)", as web/chat.js history_() sends a real answer. Plus `latest` (the last message alone).
"""
import importlib.util, json, os, sqlite3, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(os.environ.get('LASTBOOK_CODE') or Path(__file__).resolve().parents[2])   # triage copy: code root from LASTBOOK_CODE
KW = os.environ.get('TH_KW') == '1'   # triage copy: keyword-only (meaning-based search off)
TRIAGE = Path(sys.argv[1] if len(sys.argv) > 1 else r'D:\git\lastbook\.claude\drafts\triage')
if not os.environ.get('LASTBOOK_DATA'):
    raise SystemExit('set LASTBOOK_DATA')
os.environ.pop('LASTBOOK_LOCAL_AI', None)       # no model
sys.path[:0] = [str(ROOT)]


def by_path(name):
    spec = importlib.util.spec_from_file_location(name, TRIAGE / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CONVOS = by_path('convos').CONVOS
SCORE = by_path('score')

import retrieval  # noqa: E402
if KW:
    retrieval.AVAILABLE = False
from engine import sections as _sections  # noqa: E402
def _no_build(*a, **k):
    raise OSError('triage: sections build refused (read-only run)')
_sections.build = _no_build
from engine.paths import ro_uri  # noqa: E402

# read-only: the writer connection becomes a read-only one, and the vector file is not truncated
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None,
                                                    check_same_thread=False)
_load = retrieval.Index._load
retrieval.Index._load = lambda self, truncate=True, db=None: _load(self, False, db)

import server, assistant  # noqa: E402

t0 = time.time()
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)     # as server.init, without its threads
assistant.init(server, server.INDEX)
print('code', ROOT, 'sections', _sections.ensure(server.library.DB, server.kind_of) if hasattr(server, 'kind_of') else 'n/a', flush=True)
print(f'init {time.time() - t0:.1f}s, semantic {server.INDEX.status.get("state")}, {server.INDEX.status.get("chunks")} chunks',
      flush=True)
t0 = time.time()
assistant._vocab()
print(f'vocab {len(assistant._VOCAB["words"])} words in {assistant._VOCAB["seconds"]}s', flush=True)

_cache = {}
_hybrid = assistant.hybrid
def cached(q, k=8, kind='any', doc=None):     # the same search gives the same pages: each runs once
    if kind != 'any' or doc:
        return _hybrid(q, k, kind, doc)
    if (q, k) not in _cache:
        _cache[(q, k)] = _hybrid(q, k)
    return _cache[(q, k)]


assistant.hybrid = cached


def cite(hits):
    pdf = [h for h in hits if h.get('kind') == 'pdf' and h.get('page')][:3]
    return 'From the library: ' + ' '.join(f'Step {n + 1} ({h["title"]}, p. {h["page"]}).' for n, h in enumerate(pdf))


def run(c, cited):
    msgs, hits, routes = [], [], []
    for msg, _ in c['turns']:
        if msgs:
            msgs.append({'role': 'assistant', 'content': cite(hits) if cited else ''})
        msgs.append({'role': 'user', 'content': msg})
        if cited or len(msgs) == 2 * len(c['turns']) - 1:      # empty replies: only the last turn matters
            hits, info = assistant.turn_hits(msgs, None, True)
            routes.append(info['route'])
    return hits, info, routes


KINDS = ('follow', 'add', 'correct', 'new', 'after_noise', 'all')
table, route_count = {}, Counter()
for name in ('latest', 'turn_hits (empty replies)', 'turn_hits (cited replies)'):
    rows = []
    for c in CONVOS:
        if name == 'latest':
            hits = assistant.hybrid(c['turns'][-1][0][:300], 8)
        else:
            hits, info, routes = run(c, 'cited' in name)
            if 'cited' in name:
                route_count[(c['turns'][-1][1], routes[-1])] += 1
        r = SCORE.score(c, hits)
        r['kind'] = c['turns'][-1][1]
        r['has_noise'] = any(k == 'noise' for _, k in c['turns'][1:])
        rows.append(r)
    by = {k: SCORE.agg([r for r in rows if r['kind'] == k]) for k in KINDS[:4]}
    by['after_noise'] = SCORE.agg([r for r in rows if r['has_noise']])
    by['all'] = SCORE.agg(rows)
    table[name] = by

print(f'\nsearches {len(_cache)}, {time.time() - t0:.0f}s\n')
print('First result right (%), ' + ('KEYWORD-ONLY' if KW else 'hybrid') + ', in-process  [n: ' + ', '.join(f'{k} {table["latest"][k]["n"]}' for k in KINDS) + ']')
print(f'{"":28}' + ''.join(f'{k:>12}' for k in KINDS))
for name, by in table.items():
    print(f'{name:28}' + ''.join(f'{round(by[k]["first_ok"] * 100):>12}' for k in KINDS))
print('\nUseful pages in the top 8 (mean)')
for name, by in table.items():
    print(f'{name:28}' + ''.join(f'{by[k]["useful_mean"]:>12}' for k in KINDS))
print('\nroute of the last message (label -> route), cited replies:', json.dumps({f'{a}->{b}': n for (a, b), n in sorted(route_count.items())}))
