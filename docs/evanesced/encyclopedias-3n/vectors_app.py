"""The app's first_wiki with LASTBOOK_WIKI_VECTORS=1 vs 0 on the real library and indexes; time, RAM, useful."""
import json, os, re, sys, time, statistics as st
sys.path[:0] = [r'D:\git\lastbook', r'D:\git\lastbook\.claude\drafts\triage']
import psutil
import assistant as A
from engine import meaning_red, wiki_vectors, typos
import cases as C
ROOT = r'D:\LastbookData\library-data'
proc = psutil.Process()
print('meaning runner ready', meaning_red.wait(120), flush=True)
rss0 = proc.memory_info().rss
os.environ['LASTBOOK_WIKI_VECTORS'] = '1'
t = time.perf_counter(); first = A.first_wiki('how do i cool a burn', root=ROOT); load = time.perf_counter() - t
print(f'first question (loads the indexes): {load:.1f} s, RSS +{(proc.memory_info().rss - rss0) / 2**20:.0f} MB, '
      f'source {"vectors" if first and "score" in first[0] and first[0]["score"] < 1.01 and wiki_vectors._loaded else "?"}', flush=True)
res = {}
for mode in ('1', '0'):
    os.environ['LASTBOOK_WIKI_VECTORS'] = mode
    for col in ('nonred', 'red'):
        cs = [c for c in C.cases() if c['typo_of'] is None and (c['colour'] == 'red') == (col == 'red')]
        ms, top1, any3, none = [], 0, 0, 0
        for c in cs:
            pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
            q = typos.correct(c['q']) or c['q']
            t = time.perf_counter(); hits = A.first_wiki(q, root=ROOT); ms.append((time.perf_counter() - t) * 1000)
            ok = [bool(pat.search(h['excerpt'] + ' ' + h['title'])) for h in hits]
            top1 += bool(ok and ok[0]); any3 += any(ok); none += not hits
        res[(mode, col)] = (len(cs), top1, any3, none, round(st.median(ms)), round(sorted(ms)[int(.9 * len(ms))]))
        print('vectors' if mode == '1' else 'keyword', col, 'n, first useful, any3, none, ms median, p90 =', res[(mode, col)], flush=True)
print(f'RSS after: +{(proc.memory_info().rss - rss0) / 2**20:.0f} MB')
meaning_red.stop()
