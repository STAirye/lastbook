"""Cheap test: how long the --embed runner takes for a question plus ~18 encyclopedia excerpts of 2,000 characters."""
import sys, time, statistics as st
sys.path.insert(0, r'D:\git\lastbook'); sys.path.insert(0, r'D:\git\lastbook\.claude\drafts\triage')
from engine import encyclopedias as E, wiki_pick as W, meaning_red as M, sections
import cases as C
ROOT = r'D:\LastbookData\library-data'
t = time.time(); ok = M.wait(120); print('runner ready', ok, round(time.time() - t, 2), M.status()['state'], flush=True)
m = M._model
qs = [c['q'] for c in C.cases() if c['typo_of'] is None][::12][:20]
one, batch, n_ex = [], [], []
for q in qs:
    words = W.words_of(q); pats = [W._pattern(w) for w in words]
    cands = E.search(' '.join(words), per_file=W.PER_FILE, limit=E.SEARCH_LIMIT, root=ROOT, read_text=False, excerpt=0)
    ex = []
    for h in cands:
        if W.PRINT.search(h['article']):
            continue
        arc = E._open_archive(E.zim_path(h['zim'], ROOT))
        got = E.entry_text(arc, h['article'], cap=None)
        if got and got[1]:
            ex.append(E.pick_section(W.best_section(got[1], pats)[1], q, 2000))
    n_ex.append(len(ex))
    t = time.perf_counter(); m.embed([q]); one.append((time.perf_counter() - t) * 1000)
    t = time.perf_counter(); m.embed([q] + ex); batch.append((time.perf_counter() - t) * 1000)
print('excerpts per question median', st.median(n_ex), 'max', max(n_ex))
print('question alone ms median', round(st.median(one), 1))
print('question + excerpts ms median', round(st.median(batch)), 'p90', round(sorted(batch)[int(.9 * len(batch))]), 'max', round(max(batch)))
print('per excerpt ms', round(st.median([b / max(1, n + 1) for b, n in zip(batch, n_ex)]), 1))
M.stop()
