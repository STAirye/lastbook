"""Three encyclopedia files together: one question embed through the runner, a scan of each file's matrix, merge of
the top 3 articles by best-section cosine; against wiki_pick.pick over the real library root. Writes bench_all.json."""
import json, re, statistics as st, sys, time, collections
from pathlib import Path

sys.path.insert(0, r'D:\git\lastbook'); sys.path.insert(0, r'D:\git\lastbook\.claude\drafts\triage')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from engine import encyclopedias as E, wiki_pick as W, meaning_red as MR
import cases as C
import bench as B

HERE = Path(__file__).resolve().parent
ROOT = r'D:\LastbookData\library-data'
D = Path(r'D:\LastbookData\derived\index')
CHUNK = 50_000
NAMES = ['mdwiki_en_all_maxi_2025-11.zim', 'appropedia_en_all_maxi_2026-02.zim', 'wikibooks_en_all_maxi_2026-04.zim']


def scan_f16(V16, qv, chunk=CHUNK):
    out = np.empty(len(V16), dtype=np.float32)
    for a in range(0, len(V16), chunk):
        out[a:a + chunk] = V16[a:a + chunk].astype(np.float32) @ qv
    return out


def main():
    from libzim.reader import Archive
    idxs, arcs = {}, {}
    for n in NAMES:
        stem = next(p.name[:-len('.meta.json')] for p in D.glob(f'vec-{n}-*.meta.json') if 'smoke' not in p.name)
        idxs[n] = B.Index(stem)
        arcs[n] = Archive(Path(ROOT) / 'collections' / n)
    mb = lambda x: round(x / 2**20, 1)
    res = {'counts': {n: {'articles': len(i.paths), 'sections': len(i.V)} for n, i in idxs.items()},
           'ram_MB': {'f32_total': mb(sum(i.V.nbytes for i in idxs.values())),
                      'f16_total': mb(sum(i.f16.nbytes for i in idxs.values())),
                      'f16_chunk_buffer': mb(CHUNK * 384 * 4),
                      'f32_each': {n: mb(i.V.nbytes) for n, i in idxs.items()}}}
    print(res, flush=True)
    for i in idxs.values():     # the f32 copies are only kept while timing the f32 scan; the f16 timing below uses f16
        pass
    model = MR.Model(B.MODEL_DIR)
    model.embed(['warm up'])

    def vec_pick(q, mode, k=3):
        t0 = time.perf_counter()
        qv = model.embed([q])[0]
        t1 = time.perf_counter()
        cand = []
        for n, i in idxs.items():
            s = i.scores(qv) if mode == 'f32' else scan_f16(i.f16, qv)
            top, mx = i.top(s, k)
            for ai in top:
                cand.append((float(mx[ai]), n, int(ai), i.best_row(int(ai), s)))
        cand.sort(key=lambda t: -t[0])
        t2 = time.perf_counter()
        return cand[:k], (t1 - t0) * 1000, (t2 - t1) * 1000

    allc = C.cases()
    sets = {'nonred': [c for c in allc if c['typo_of'] is None and c['colour'] != 'red'],
            'red': [c for c in allc if c['typo_of'] is None and c['colour'] == 'red']}
    timing = {'f32': [], 'f16': []}
    summ, rows_out = {}, []
    for name, cs in sets.items():
        tally = {m: [0, 0, 0] for m in ('keyword', 'vector')}
        files = {m: collections.Counter() for m in tally}
        tk, tv = [], []
        for c in cs:
            pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
            q = c['q']
            query = ' '.join(W.words_of(q))
            t = time.time(); kw = W.pick(q, root=ROOT); tk.append((time.time() - t) * 1000)
            cand, te, ts = vec_pick(q, 'f32')
            timing['f32'].append((te, ts))
            if len(timing['f16']) < 100:
                timing['f16'].append(vec_pick(q, 'f16')[1:])
            tv.append(te + ts)
            vec = [dict(B.hit(arcs[n], idxs[n], ai, row, query), zim=n) for _, n, ai, row in cand]
            for m, hs in (('keyword', kw), ('vector', vec)):
                ok = [bool(pat.search(h['excerpt'] + ' ' + h['title'])) for h in hs]
                tally[m][0] += bool(ok and ok[0]); tally[m][1] += any(ok); tally[m][2] += not hs
                if hs:
                    files[m][hs[0]['zim'].split('_')[0]] += 1
                rows_out.append({'set': name, 'how': m, 'q': q, 'titles': [h['title'] for h in hs],
                                 'zims': [h['zim'].split('_')[0] for h in hs], 'ok': ok})
        summ[name] = {'n': len(cs), **{m: {'first_useful': v[0], 'any3_useful': v[1], 'none': v[2],
                                           'top_article_from': dict(files[m])} for m, v in tally.items()},
                      'keyword_ms_median': round(st.median(tk)), 'keyword_ms_p90': round(B.pct(tk, .9)),
                      'vector_f32_ms_median': round(st.median(tv), 1), 'vector_f32_ms_p90': round(B.pct(tv, .9), 1)}
        print(name, json.dumps(summ[name]), flush=True)
    res['summary'] = summ
    f = lambda k, j: [t[j] for t in timing[k]]
    res['query_ms'] = {'embed_median': round(st.median(f('f32', 0)), 1),
                       'scan3_f32_median': round(st.median(f('f32', 1)), 1), 'scan3_f32_p90': round(B.pct(f('f32', 1), .9), 1),
                       'scan3_f16_chunked_median': round(st.median(f('f16', 1)), 1), 'scan3_f16_chunked_p90': round(B.pct(f('f16', 1), .9), 1),
                       'n_f16': len(timing['f16'])}
    print(res['query_ms'], flush=True)
    (HERE / 'bench_all.json').write_text(json.dumps({**res, 'rows': rows_out}, indent=1), encoding='utf-8')
    model.close()


if __name__ == '__main__':
    main()
