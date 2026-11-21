"""Upstream's first encyclopedia results (raw question, first 2,000 chars) vs engine/wiki_pick (best section)."""
import json, re, sys, time, statistics as st
from pathlib import Path
sys.path.insert(0, r'D:\git\lastbook'); sys.path.insert(0, r'D:\git\lastbook\.claude\drafts\triage')
from engine import encyclopedias as E, wiki_pick as W
import cases as C
ROOT = r'D:\LastbookData\library-data'
sets = {'clean': [c for c in C.cases() if c['typo_of'] is None], 'typo': [c for c in C.cases() if c['typo_of']]}
res, rows = {}, []
for name, cs in sets.items():
    for how in ('upstream', 'pick'):
        top1 = any3 = n = 0; ms = []; nothing = 0
        for c in cs:
            pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
            t = time.time()
            hits = E.search(c['q'][:300], limit=3, excerpt=2000, root=ROOT) if how == 'upstream' else W.pick(c['q'], root=ROOT)
            ms.append((time.time() - t) * 1000)
            n += 1
            ok = [bool(pat.search(h['excerpt'] + ' ' + h['title'])) for h in hits]
            top1 += bool(ok and ok[0]); any3 += any(ok); nothing += not hits
            rows.append({'set': name, 'how': how, 'q': c['q'], 'colour': c['colour'], 'titles': [h['title'] for h in hits], 'ok': ok})
        res[f'{name}/{how}'] = {'n': n, 'top1_useful': top1, 'any3_useful': any3, 'none': nothing,
                                'ms_median': round(st.median(ms)), 'ms_p90': round(sorted(ms)[int(.9 * len(ms))])}
        print(name, how, res[f'{name}/{how}'], flush=True)
Path(r'D:\git\lastbook\.claude\drafts\encyclopedia\compare.json').write_text(json.dumps({'summary': res, 'rows': rows}, indent=1), encoding='utf-8')
