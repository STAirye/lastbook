r"""Blind list 4, step 1: the English search words the chat would make for each message (assistant.english_query, the fork's
3i), made once with the person's own local model, so every run uses the same ones. Prints counts only.

    set LASTBOOK_DATA=D:\LastbookData  &  set LASTBOOK_LOCAL_AI=1
    python -B .claude\drafts\independent4\english4.py

Writes english.json: {"<line index>": "words" | null}, only for lines needs_english() calls non-English (as the chat).
"""
import json, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT)]
os.environ['LASTBOOK_LOCAL_AI'] = '1'
import server, assistant  # noqa: E402

rows = [json.loads(l) for l in open(HERE / 'phrases_mixed.jsonl', encoding='utf-8') if l.strip()]
assistant.init(server, None)
L = assistant.LOCAL
t0 = time.time()
while L.status()['state'] in ('absent', 'checking', 'measuring') and time.time() - t0 < 180:   # the background file check
    time.sleep(0.5)
print('model file check:', L.status()['state'], round(time.time() - t0, 1), 's', flush=True)
why = L.ensure_running(None, lambda: False)
assert not why and getattr(L, 'custom', False), (why, L.status() if hasattr(L, 'status') else None)
print('model ready in', round(time.time() - t0, 1), 's', flush=True)
out, t0 = {}, time.time()
for i, r in enumerate(rows):
    if assistant.needs_english(r['text']):
        out[str(i)] = assistant.english_query(r['text'], '', lambda: False)
    if i % 50 == 49:
        print(i + 1, round(time.time() - t0), 's', flush=True)
json.dump(out, open(HERE / 'english.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(json.dumps({'lines': len(rows), 'non-English by needs_english': len(out),
                  'got English words': sum(1 for v in out.values() if v), 'seconds': round(time.time() - t0)}))
L.stop('list 4 done')
