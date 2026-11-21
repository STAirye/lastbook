"""Query timing, runner-vs-GPU vector check, and keyword / vector / hybrid benchmark on MDWiki.

  python bench.py [--stem vec-...]   (writes bench.json beside this file)
"""
import argparse, json, os, re, statistics as st, sys, time
from pathlib import Path

sys.path.insert(0, r'D:\git\lastbook'); sys.path.insert(0, r'D:\git\lastbook\.claude\drafts\triage')
import numpy as np
from engine import encyclopedias as E, sections as S, wiki_pick as W, meaning_red as MR
import cases as C

HERE = Path(__file__).resolve().parent
ZIMNAME = 'mdwiki_en_all_maxi_2025-11.zim'
ZIM = Path(r'D:\LastbookData\library-data\collections') / ZIMNAME
TMP_ROOT = Path(r'D:\LastbookData\tmp-mdwiki-only')   # a library root holding only MDWiki (hard link), so wiki_pick is limited to it
MODEL_DIR = Path(r'D:\git\lastbook\derived\models\meaning-red')
HYB_W = 0.3       # hybrid2: weight of the keyword picker's score next to the cosine
TOPK_VEC = 10     # hybrid: vector candidates


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


class Index:
    def __init__(self, stem, d=Path(r'D:\LastbookData\derived\index')):
        z = np.load(d / f'{stem}.rows.npz', allow_pickle=True)
        self.paths, self.titles = list(z['paths']), list(z['titles'])
        self.art, self.start = z['art'], z['start']
        self.f16 = np.load(d / f'{stem}.f16.npy')
        self.i8 = np.load(d / f'{stem}.i8.npy')
        self.V = self.f16.astype(np.float32)
        self.first = np.searchsorted(self.art, np.arange(len(self.paths)))   # rows are in article order
        self.by_path = {p: i for i, p in enumerate(self.paths)}

    def scores(self, qv):
        return self.V @ qv

    def scores_i8(self, qv, chunk=100_000):
        out = np.empty(len(self.i8), dtype=np.float32)
        for a in range(0, len(self.i8), chunk):
            out[a:a + chunk] = self.i8[a:a + chunk].astype(np.float32) @ qv / 127.0
        return out

    def per_article(self, s):
        mx = np.maximum.reduceat(s, self.first)
        return mx

    def top(self, s, k=3):
        mx = self.per_article(s)
        idx = np.argpartition(-mx, k)[:k]
        idx = idx[np.argsort(-mx[idx])]
        return idx, mx

    def best_row(self, ai, s):
        a = self.first[ai]
        b = self.first[ai + 1] if ai + 1 < len(self.first) else len(s)
        return a + int(np.argmax(s[a:b]))


def excerpt_for(arc, idx, ai, row, query):
    got = E.entry_text(arc, idx.paths[ai], cap=None)
    if not got:
        return ''
    secs = S.cut(S.norm_ws(got[1]), S.SECTION)
    st_ = int(idx.start[row])
    sec = next((t for s0, t in secs if s0 == st_), secs[0][1] if secs else '')
    return E.pick_section(sec, query, E.INITIAL_CHARS)


def hit(arc, idx, ai, row, query):
    return {'title': idx.titles[ai], 'article': idx.paths[ai], 'excerpt': excerpt_for(arc, idx, ai, row, query)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stem', default='')
    a = ap.parse_args()
    d = Path(r'D:\LastbookData\derived\index')
    stem = a.stem or next(p.name[:-len('.meta.json')] for p in d.glob('vec-mdwiki*.meta.json') if 'smoke' not in p.name)
    print('index', stem, flush=True)
    idx = Index(stem)
    print('articles', len(idx.paths), 'sections', len(idx.V), flush=True)
    from libzim.reader import Archive
    arc = Archive(ZIM)
    (TMP_ROOT / 'collections').mkdir(parents=True, exist_ok=True)
    link = TMP_ROOT / 'collections' / ZIMNAME
    if not link.exists():
        os.link(ZIM, link)

    model = MR.Model(MODEL_DIR)
    model.embed(['warm up'])
    res = {'index': stem}

    # 1. the runner's vectors against the GPU build's, on a sample of the stored sections
    rng = np.random.default_rng(1)
    rows = rng.choice(len(idx.V), size=150, replace=False)
    texts, cache = [], {}
    for r in rows:
        ai = int(idx.art[r])
        if ai not in cache:
            got = E.entry_text(arc, idx.paths[ai], cap=None)
            cache[ai] = dict(S.cut(S.norm_ws(got[1]), S.SECTION))
        texts.append(cache[ai][int(idx.start[r])])
    t = time.time()
    rv = np.concatenate([model.embed([x]) for x in texts])
    dt = time.time() - t
    cos = (rv * idx.V[rows]).sum(1)
    res['runner_vs_gpu'] = {'n': len(rows), 'cos_min': float(cos.min()), 'cos_median': float(np.median(cos)), 'cos_mean': float(cos.mean()),
                            'under_0.99': int((cos < 0.99).sum()), 'runner_ms_per_section': round(dt / len(rows) * 1000, 1)}
    print(res['runner_vs_gpu'], flush=True)

    # 2. cases
    allc = C.cases()
    sets = {'nonred': [c for c in allc if c['typo_of'] is None and c['colour'] != 'red'],
            'red': [c for c in allc if c['typo_of'] is None and c['colour'] == 'red']}
    rows_out, summ = [], {}
    qt_embed, qt_scan, qt_scan_i8, qt_total = [], [], [], []
    agree_i8 = n_i8 = 0
    for name, cs in sets.items():
        tally = {m: [0, 0, 0] for m in ('keyword', 'vector', 'hybrid', 'hybrid2')}   # n_first, n_any3, none
        tkw = []
        for c in cs:
            pat = re.compile('|'.join(C.P[k] for k in c['need']), re.I)
            q = c['q']
            words = W.words_of(q)
            query = ' '.join(words)
            # keyword
            t = time.time(); kw = W.pick(q, limit=12, root=str(TMP_ROOT)); tkw.append((time.time() - t) * 1000)
            kw3 = kw[:3]
            # vector
            t0 = time.perf_counter()
            qv = model.embed([q])[0]
            t1 = time.perf_counter()
            s = idx.scores(qv)
            top, mx = idx.top(s, TOPK_VEC)
            t2 = time.perf_counter()
            qt_embed.append((t1 - t0) * 1000); qt_scan.append((t2 - t1) * 1000); qt_total.append((t2 - t0) * 1000)
            if name == 'nonred' and len(qt_scan_i8) < 40:
                t = time.perf_counter(); s8 = idx.scores_i8(qv); top8, _ = idx.top(s8, 3)
                qt_scan_i8.append((time.perf_counter() - t) * 1000)
                agree_i8 += int(set(top8.tolist()) == set(top[:3].tolist())); n_i8 += 1
            vec3 = [hit(arc, idx, int(ai), idx.best_row(int(ai), s), query) for ai in top[:3]]
            # hybrid: vector top-K union keyword candidates, ranked by cosine
            cand = {int(ai) for ai in top}
            for h in kw:
                ai = idx.by_path.get(h['article'])
                if ai is not None:
                    cand.add(ai)
            ranked = sorted(cand, key=lambda ai: -mx[ai])[:3]
            hyb3 = [hit(arc, idx, ai, idx.best_row(ai, s), query) for ai in ranked]
            # hybrid2: cosine + keyword share score (W.pick's score, 0 when the keyword search did not return it)
            kws = {idx.by_path.get(h['article']): h['score'] for h in kw}
            ranked2 = sorted(cand, key=lambda ai: -(mx[ai] + HYB_W * kws.get(ai, 0.0)))[:3]
            hyb3b = [hit(arc, idx, ai, idx.best_row(ai, s), query) for ai in ranked2]
            for m, hs in (('keyword', kw3), ('vector', vec3), ('hybrid', hyb3), ('hybrid2', hyb3b)):
                ok = [bool(pat.search(h['excerpt'] + ' ' + h['title'])) for h in hs]
                tally[m][0] += bool(ok and ok[0]); tally[m][1] += any(ok); tally[m][2] += not hs
                rows_out.append({'set': name, 'how': m, 'q': q, 'topic': c['topic'], 'titles': [h['title'] for h in hs], 'ok': ok})
        summ[name] = {'n': len(cs), **{m: {'first_useful': v[0], 'any3_useful': v[1], 'none': v[2]} for m, v in tally.items()},
                      'keyword_ms_median': round(st.median(tkw)), 'keyword_ms_p90': round(pct(tkw, .9))}
        print(name, json.dumps(summ[name]), flush=True)
    res['summary'] = summ
    res['query_ms'] = {'n': len(qt_total), 'embed_runner_median': round(st.median(qt_embed), 1), 'embed_runner_p90': round(pct(qt_embed, .9), 1),
                       'scan_f32_median': round(st.median(qt_scan), 1), 'scan_f32_p90': round(pct(qt_scan, .9), 1),
                       'total_median': round(st.median(qt_total), 1), 'total_p90': round(pct(qt_total, .9), 1),
                       'scan_i8_chunked_median': round(st.median(qt_scan_i8), 1), 'scan_i8_chunked_p90': round(pct(qt_scan_i8, .9), 1),
                       'i8_top3_same_as_f16': f'{agree_i8}/{n_i8}'}
    print(res['query_ms'], flush=True)
    (HERE / 'bench.json').write_text(json.dumps({**res, 'rows': rows_out}, indent=1), encoding='utf-8')
    model.close()


if __name__ == '__main__':
    main()
