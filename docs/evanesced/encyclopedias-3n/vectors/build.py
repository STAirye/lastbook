"""Build a per-ZIM meaning (vector) index: one bge-small-en-v1.5 vector per ~5,000-char section of every article.

  python build.py --zim <file.zim> [--limit N] [--out DIR] [--device cuda|cpu] [--cpu-sample N]

Walk: every entry id, redirects skipped, only text/html, print versions and articles over MAX_BYTES skipped (as
engine/wiki_pick.pick does, so the comparison is fair). Text: encyclopedias.entry_text + sections.norm_ws, cut with
sections.cut (SECTION=5000). Embedding: [CLS], unit vectors, max 320 tokens (as retrieval.Embedder).
Sidecar (never inside the ZIM / library): <out>/vec-<zim name>-<size>-<mtime_ns>.{meta.json,rows.npz,f16.npy,i8.npy}
"""
import argparse, json, os, re, sys, time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, r'D:\git\lastbook')
import numpy as np
from engine import encyclopedias as E, sections as S, wiki_pick as W

MAX_TOKENS = 320
BGE = os.environ.get('BGE_DIR', r'<scratchpad>\bge')
_arc = None
LANG = re.compile(r'/[a-z]{2,3}$')


def _init(zim):
    global _arc
    from libzim.reader import Archive
    _arc = Archive(zim)


def work(ids):
    """(path, title, [(start, text)]) for each non-redirect article among the entry ids; plus counts."""
    out, redir, skipped = [], 0, 0
    for i in ids:
        try:
            e = _arc._get_entry_by_id(i)
        except Exception:
            skipped += 1
            continue
        if e.is_redirect:
            redir += 1
            continue
        if LANG.search(e.path):     # Appropedia's translations (Article/es): the picker's prefer_primary drops them too
            skipped += 1
            continue
        try:
            it = e.get_item()
            if 'html' not in (it.mimetype or '').lower():
                skipped += 1
                continue
            if it.size > W.MAX_BYTES or W.PRINT.search(e.path) or W.PRINT.search(e.title or ''):
                skipped += 1
                continue
        except Exception:
            skipped += 1
            continue
        got = E.entry_text(_arc, e.path, cap=None)
        if not got or not got[1]:
            skipped += 1
            continue
        title, text = got
        secs = S.cut(S.norm_ws(text), S.SECTION)
        if secs:
            out.append((e.path, title, secs))
        else:
            skipped += 1
    return out, redir, skipped


class GpuEmbedder:
    def __init__(self, device):
        import torch
        from transformers import AutoTokenizer, AutoModel
        self.torch, self.device = torch, device
        self.tok = AutoTokenizer.from_pretrained(BGE)
        self.model = AutoModel.from_pretrained(BGE).to(device).eval()
        if device == 'cuda':
            self.model.half()

    def embed(self, texts, bs=128):
        torch = self.torch
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        out = np.zeros((len(texts), 384), dtype=np.float32)
        with torch.inference_mode():
            for b in range(0, len(order), bs):
                idx = order[b:b + bs]
                enc = self.tok([texts[i] for i in idx], padding=True, truncation=True, max_length=MAX_TOKENS,
                               return_tensors='pt').to(self.device)
                h = self.model(**enc).last_hidden_state[:, 0].float()
                h = torch.nn.functional.normalize(h, dim=1)
                out[idx] = h.cpu().numpy()
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zim', default=r'D:\LastbookData\library-data\collections\mdwiki_en_all_maxi_2025-11.zim')
    ap.add_argument('--limit', type=int, default=0, help='stop after this many articles (smoke test)')
    ap.add_argument('--out', default=r'D:\LastbookData\derived\index')
    ap.add_argument('--device', default='cuda')
    ap.add_argument('--workers', type=int, default=10)
    ap.add_argument('--cpu-sample', type=int, default=0, help='also time the CPU on this many sections')
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    from libzim.reader import Archive
    zim = Path(a.zim)
    st = zim.stat()
    n = Archive(zim).all_entry_count
    print('entries', n, flush=True)
    emb = GpuEmbedder(a.device)
    emb.embed(['warm up'] * 8)

    paths, titles, art_idx, starts, vecs = [], [], [], [], []
    redir = skipped = 0
    t_emb = 0.0
    t0 = time.time()
    CH = 100
    chunks = [range(i, min(n, i + CH)) for i in range(0, n, CH)]
    buf_t, buf_meta = [], []

    def flush():
        nonlocal t_emb
        if not buf_t:
            return
        t = time.time()
        v = emb.embed(buf_t)
        t_emb += time.time() - t
        vecs.append(v.astype(np.float16))
        for ai, s in buf_meta:
            art_idx.append(ai)
            starts.append(s)
        buf_t.clear(); buf_meta.clear()

    done = False
    last = 0
    with Pool(a.workers, _init, (str(zim),)) as pool:
        for res, r, s in pool.imap(work, chunks):
            redir += r; skipped += s
            for path, title, secs in res:
                ai = len(paths)
                paths.append(path); titles.append(title)
                for st_, tx in secs:
                    buf_t.append(tx); buf_meta.append((ai, st_))
                if a.limit and len(paths) >= a.limit:
                    done = True
                    break
            if len(buf_t) >= 4096:
                flush()
            if len(paths) - last >= 5000:
                last = len(paths)
                print(f'{len(paths)} articles, {sum(len(v) for v in vecs) + len(buf_t)} sections, {time.time() - t0:.0f} s', flush=True)
            if done:
                pool.terminate()
                break
    flush()
    total = time.time() - t0
    V = np.concatenate(vecs)
    nsec = len(V)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = f'vec-{zim.name}-{st.st_size}-{st.st_mtime_ns}{a.tag}'
    np.save(out / f'{stem}.f16.npy', V)
    np.save(out / f'{stem}.i8.npy', np.rint(V.astype(np.float32) * 127).astype(np.int8))
    np.savez(out / f'{stem}.rows.npz', paths=np.array(paths, dtype=object), titles=np.array(titles, dtype=object),
             art=np.array(art_idx, dtype=np.int32), start=np.array(starts, dtype=np.int32))
    meta = dict(zim=zim.name, size=st.st_size, mtime_ns=st.st_mtime_ns, entries=n, redirects=redir, skipped=skipped,
                articles=len(paths), sections=nsec, model='bge-small-en-v1.5', dim=384, device=a.device,
                build_s=round(total, 1), embed_s=round(t_emb, 1), limit=a.limit)
    (out / f'{stem}.meta.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print(json.dumps(meta), flush=True)
    for ext in ('f16.npy', 'i8.npy', 'rows.npz'):
        print(ext, (out / f'{stem}.{ext}').stat().st_size)

    if a.cpu_sample:
        rng = np.random.default_rng(0)
        from libzim.reader import Archive as A
        arc = A(zim)
        pick = rng.choice(len(paths), size=min(len(paths), a.cpu_sample), replace=False)
        texts = []
        for i in pick:
            got = E.entry_text(arc, paths[i], cap=None)
            secs = S.cut(S.norm_ws(got[1]), S.SECTION)
            texts.append(secs[rng.integers(len(secs))][1])
        cpu = GpuEmbedder('cpu')
        cpu.embed(texts[:8])
        t = time.time(); cpu.embed(texts); dt = time.time() - t
        print(json.dumps(dict(cpu_sample=len(texts), cpu_s=round(dt, 1), cpu_ms_per_section=round(dt / len(texts) * 1000, 1),
                              est_cpu_full_h=round(dt / len(texts) * nsec / 3600, 2))), flush=True)


if __name__ == '__main__':
    main()
