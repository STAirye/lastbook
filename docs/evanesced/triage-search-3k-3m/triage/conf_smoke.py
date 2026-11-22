"""In-process smoke test of the chat's confidence events on the real test library (keyword-only, read-only, no model)."""
import json, os, sqlite3, sys
sys.path[:0] = [os.environ['LASTBOOK_CODE']]
os.environ.pop('LASTBOOK_LOCAL_AI', None)
import retrieval
retrieval.AVAILABLE = False
from engine import sections as _s
_s.build = lambda *a, **k: (_ for _ in ()).throw(OSError('read-only run'))
from engine.paths import ro_uri
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None, check_same_thread=False)
_load = retrieval.Index._load
retrieval.Index._load = lambda self, truncate=True, db=None: _load(self, False, db)
import server, assistant
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
assistant.init(server, server.INDEX)
assistant._http_round = lambda msgs, tools, c, wrote, ss: ('(model answer)', {})
for q in ('how do i purify water from a creek', 'my sun isnt brething', 'build an electric fence for goats',
          'what to do during riots in the city', 'broken leg no ambulance'):
    ev = []
    assistant.chat([{'role': 'user', 'content': q}], None, ev.append, lambda: False)
    d = {e['type']: e for e in ev}
    s = d.get('suggest') or {}
    print(json.dumps({'q': q, 'confidence': s.get('confidence'), 'prompt': s.get('prompt'),
                      'buttons': [c['label'] for c in s.get('choices', [])], 'answer': d['done']['answer'][:70],
                      'unsure': d['done'].get('unsure'), 'cited': len(d['done']['sources']),
                      'consulted': len(d['done']['consulted'])}, ensure_ascii=False))
    tr = {}
    res = assistant.hybrid(q, 8, trace=tr)
    print('   /api/retrieve confidence:', assistant.search_confidence(res, tr))
