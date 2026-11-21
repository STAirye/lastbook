"""Score of each picked article vs whether it is useful, to set a floor. Also: library search time (what parallel saves)."""
import json, re, sys, time, statistics as st
from pathlib import Path
sys.path.insert(0, r'D:\git\lastbook'); sys.path.insert(0, r'D:\git\lastbook\.claude\drafts\triage')
import os
os.environ.setdefault('LASTBOOK_LIBRARY', r'D:\LastbookData\library-data'); os.environ.setdefault('LASTBOOK_DATA', r'D:\LastbookData')
from engine import wiki_pick as W
import cases as C
ROOT = r'D:\LastbookData\library-data'
rows = []
for c in [c for c in C.cases() if c['typo_of'] is None]:
    pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
    for i, h in enumerate(W.pick(c['q'], root=ROOT)):
        rows.append({'q': c['q'], 'colour': c['colour'], 'rank': i, 'title': h['title'], 'score': h['score'], 'share': h['share'],
                     'useful': bool(pat.search(h['excerpt'] + ' ' + h['title']))})
Path(r'D:\git\lastbook\.claude\drafts\encyclopedia\floor.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
print('articles', len(rows), 'useful', sum(r['useful'] for r in rows))
for f in (0, .34, .5, .6, .67, .75, .85, 1.0):
    k = [r for r in rows if r['score'] >= f]
    print(f'floor {f:.2f}: kept {len(k):3d} useful {sum(r["useful"] for r in k):3d} useless {sum(not r["useful"] for r in k):3d}'
          f' | precision {sum(r["useful"] for r in k) / max(1, len(k)):.2f}')
