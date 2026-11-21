"""wiki_vectors with and without bge's query instruction, on the 253 questions (real indexes and runner)."""
import os, re, sys, time, statistics as st
sys.path[:0] = [r'D:\git\lastbook', r'D:\git\lastbook\.claude\drafts\triage']
os.environ['LASTBOOK_WIKI_VECTORS'] = '1'
from engine import meaning_red, wiki_vectors as WV, typos
import cases as C
ROOT = r'D:\LastbookData\library-data'
meaning_red.wait(120)
for pre in ('1', '0'):
    os.environ['LASTBOOK_WIKI_VECTORS_PREFIX'] = pre
    for col in ('nonred', 'red'):
        cs = [c for c in C.cases() if c['typo_of'] is None and (c['colour'] == 'red') == (col == 'red')]
        top1 = any3 = 0; files = {}
        for c in cs:
            pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
            hits = WV.pick(typos.correct(c['q']) or c['q'], root=ROOT) or []
            ok = [bool(pat.search(h['excerpt'] + ' ' + h['title'])) for h in hits]
            top1 += bool(ok and ok[0]); any3 += any(ok)
            if hits: files[hits[0]['zim'][:6]] = files.get(hits[0]['zim'][:6], 0) + 1
        print('prefix' if pre == '1' else 'bare  ', col, len(cs), 'first useful', top1, 'any3', any3, 'first from', files, flush=True)
meaning_red.stop()
