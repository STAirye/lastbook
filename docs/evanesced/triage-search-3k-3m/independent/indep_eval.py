r"""Held-out check: the emergency-detection checks on the independent phrase list (phrases.jsonl), read-only, no tuning.

    set LASTBOOK_CODE=D:\git\lastbook  &  set LASTBOOK_DATA=D:\LastbookData-fork-test  [& set TH_KW=1]
    python -B -X utf8 indep_eval.py OUT.json

As ../triage/body_eval.py: sections build refused, read-only index connections, vector file never truncated, no model.
Per line: typos.correct (and what it split / fixed / body-fixed), body_signs, urgent, is_danger, danger_signs,
unknown_words; then assistant.turn_hits as a first message, its confidence, and chat_level's action.
"""
import json, os, re, sqlite3, sys, time
from pathlib import Path

ROOT = Path(os.environ['LASTBOOK_CODE'])
KW = os.environ.get('TH_KW') == '1'
HERE = Path(__file__).resolve().parent
if not os.environ.get('LASTBOOK_DATA'):
    raise SystemExit('set LASTBOOK_DATA')
os.environ.pop('LASTBOOK_LOCAL_AI', None)
sys.path[:0] = [str(ROOT)]

import retrieval  # noqa: E402
if KW:
    retrieval.AVAILABLE = False
from engine import sections as _sections  # noqa: E402
def _no_build(*a, **k):
    raise OSError('independent: sections build refused (read-only run)')
_sections.build = _no_build
from engine.paths import ro_uri  # noqa: E402
retrieval.Index._db = lambda self: sqlite3.connect(ro_uri(self.db_path), uri=True, timeout=60, isolation_level=None,
                                                    check_same_thread=False)
_load = retrieval.Index._load
retrieval.Index._load = lambda self, truncate=True, db=None: _load(self, False, db)

import server, assistant  # noqa: E402
from engine import confidence, typos  # noqa: E402


def action(turn, n_hits):
    level, conf, everyday = assistant.chat_level(turn, True, 1)
    if level == 'unsure':
        if turn.get('danger'):
            return level, everyday, ('ask+pages' if n_hits else 'ask (danger, nothing found)')
        return level, everyday, 'ask'
    if turn['buttons'] or level != 'sure':
        return level, everyday, ('compact buttons' if everyday else 'buttons')
    return level, everyday, 'answer'


def word_changes(q, words):
    """[(as typed, how: split|fix|body, result)] for each word typos.correct_with changes (same order of tries)."""
    out = []
    if not q or typos.looks_foreign(q):
        return out
    toks = typos.TOKEN.findall(q)
    shouting = sum(t.isupper() for t in toks) > len(toks) / 2
    for t in toks:
        if not re.fullmatch(r'[A-Za-z]+', t) or (t.isupper() and len(t) > 1 and not shouting):
            continue
        parts = typos.split_word(t.lower(), words) if typos.split_on() else None
        if parts:
            out.append((t, 'split', ' '.join(parts)))
            continue
        f = typos.fix_word(t.lower(), words)
        if f != t.lower():
            out.append((t, 'fix', f))
            continue
        b = typos.body_fix(f, words) if typos.body_fix_on() else f
        if b != t.lower():
            out.append((t, 'body', b))
    return out


rows_in = [json.loads(l) for l in open(HERE / 'phrases.jsonl', encoding='utf-8') if l.strip()]
t0 = time.time()
server.catalog()
server.INDEX = retrieval.Index(server.catalog, server.trust, server.library.DB)
assistant.init(server, server.INDEX)
W = typos.words_for()
assistant._vocab()
print('code', ROOT, 'kw' if KW else 'hybrid', 'semantic', server.INDEX.status.get('state'), len(rows_in), flush=True)
out = []
for i, r in enumerate(rows_in):
    q = r['text']
    corrected = typos.correct(q)
    hits, turn = assistant.turn_hits([{'role': 'user', 'content': q}], None, True)
    conf = turn.get('confidence') or {}
    level, everyday, act = action(turn, len(hits))
    shown = act not in ('ask', 'ask (danger, nothing found)') and bool(hits)
    out.append(dict(
        i=i, text=q, meaning=r['meaning'], triage=r['triage'], signs=r['signs'], kind=r['kind'], source=r['source'],
        corrected=corrected, changed=corrected != q, changes=word_changes(q, W),
        body=sorted(confidence.body_signs(q, corrected)), urgent=confidence.urgent(q, corrected),
        urgent_words=sorted({m.group(0).lower() for m in confidence.URGENT.finditer((q + ' ' + corrected).replace('’', "'"))}),
        is_danger=assistant.is_danger(q), danger_signs=sorted(assistant.danger_signs(q + ' ' + corrected)),
        unknown_words=confidence.unknown_words(corrected), conf_unknown=bool(conf.get('unknown_words')),
        route=turn['route'], turn_danger=bool(turn.get('danger')), turn_body=turn.get('body'),
        p=conf.get('p'), p_fitted=conf.get('p_fitted'), conf_level=conf.get('level'), chat_level=level,
        everyday=everyday, action=act, pages_shown=shown, n_hits=len(hits),
        top3=[{'title': h.get('title'), 'page': h.get('page'), 'kind': h.get('kind'), 'doc_id': h.get('doc_id'),
               'emergency_book': confidence._emergency_book(h)} for h in hits[:3]],
        first_emergency=bool(hits) and confidence._emergency_book(hits[0]),
        top3_emergency=any(confidence._emergency_book(h) for h in hits[:3])))
    if i % 100 == 99:
        print(i + 1, round(time.time() - t0), 's', flush=True)
json.dump({'code': str(ROOT), 'data': os.environ['LASTBOOK_DATA'], 'mode': 'keyword' if KW else 'hybrid',
           'semantic': server.INDEX.status.get('state'), 'rows': out, 'seconds': round(time.time() - t0, 1)},
          open(sys.argv[1], 'w', encoding='utf-8'), indent=0, ensure_ascii=False, default=str)
print('done', round(time.time() - t0), 's', flush=True)
