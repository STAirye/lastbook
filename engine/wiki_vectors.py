"""fork, dev toggle: the encyclopedia articles for Chat's first results, by meaning, from a vector index per file.

Off unless LASTBOOK_WIKI_VECTORS=1. The prototype (docs/evanesced/encyclopedias-3n/vectors/RESULTS.md) embedded every ~5,000-
character section (engine/sections.cut) of MDWiki, Appropedia and Wikibooks with bge-small-en-v1.5 on a GPU, once: 430,000
sections, 11.6 min, 330 MB as f16. On the 253 test questions over all three files the first article was useful for 84%
of everyday questions (wiki_pick, the keyword picker: 70%) and 70% of urgent ones (47%), in about 36 ms (wiki_pick: about
450 ms).

Files, beside the library's other indexes (derived/index/), one set per encyclopedia file:
  vec-<zim name>-<size>-<mtime_ns>.f16.npy     float16 [sections, 384], unit vectors, rows in article order
  vec-<zim name>-<size>-<mtime_ns>.rows.json   {"paths": [...], "titles": [...], "art": [...], "start": [...]}:
                                               each section's article index and start offset in sections.norm_ws(text)
  vec-<zim name>-<size>-<mtime_ns>.meta.json   model, dim, counts
A file whose size or modification time no longer matches its encyclopedia file is ignored (a new edition needs a new
index). Nothing is loaded with pickle.

The question is embedded by the meaning check's runner (engine/meaning_red, the same bge-small through lastbook-llm
--embed): the desktop process loads no model. Its vectors match the GPU build's (cosine 0.9996 or more on 150 sections).
The matrices are loaded as float32 on the first question that reaches the encyclopedias (about 630 MB for the three
files; f16 converted chunk by chunk was 15 times slower). pick returns None when it cannot answer (switched off, no
index, runner not ready, any error), and the caller uses wiki_pick.
"""
import json
import os
import threading
import time
from pathlib import Path

import engine.paths as lastbook_paths
from engine import encyclopedias, meaning_red, sections

DIM = 384
# bge's instruction for search questions (as retrieval.QUERY_PREFIX: the sections are embedded without it). Without it a
# short question matched texts of its own kind: "he is not breathing" -> a lateral-thinking puzzle, a Latin primer.
QUERY_PREFIX = 'Represent this sentence for searching relevant passages: '
_lock = threading.Lock()
_loaded = {}        # zim name -> Index, for the files as they are now
_failed = {}        # zim name -> why, so a broken file is not read again on every question


def on():
    return os.environ.get('LASTBOOK_WIKI_VECTORS') == '1'


def prefix():
    return os.environ.get('LASTBOOK_WIKI_VECTORS_PREFIX') != '0'


def index_dir():
    return lastbook_paths.DATA / 'derived' / 'index'


class Index:
    def __init__(self, stem, folder):
        import numpy as np
        rows = json.loads((folder / f'{stem}.rows.json').read_text(encoding='utf-8'))
        self.paths, self.titles = rows['paths'], rows['titles']
        self.art = np.asarray(rows['art'], dtype=np.int32)
        self.start = np.asarray(rows['start'], dtype=np.int32)
        self.V = np.load(folder / f'{stem}.f16.npy', allow_pickle=False).astype(np.float32)
        if self.V.ndim != 2 or self.V.shape[1] != DIM or len(self.V) != len(self.art) or not len(self.paths):
            raise ValueError('index rows and vectors do not match')
        self.first = np.searchsorted(self.art, np.arange(len(self.paths)))     # first row of each article

    def top(self, qv, k):
        """[(cosine, article index, best row)] for the k articles whose best section is closest to qv."""
        import numpy as np
        s = self.V @ qv
        best = np.maximum.reduceat(s, self.first)
        k = min(k, len(best))
        idx = np.argpartition(-best, k - 1)[:k]
        out = []
        for ai in idx[np.argsort(-best[idx])]:
            a = self.first[ai]
            b = self.first[ai + 1] if ai + 1 < len(self.first) else len(s)
            out.append((float(best[ai]), int(ai), int(a + np.argmax(s[a:b]))))
        return out


def _stem_for(name, path, folder):
    st = path.stat()
    stem = f'vec-{name}-{st.st_size}-{st.st_mtime_ns}'
    return stem if (folder / f'{stem}.f16.npy').is_file() and (folder / f'{stem}.rows.json').is_file() else None


def indexes(root=None, folder=None):
    """{zim name: Index} for the encyclopedia files present that have a matching index; loads each once."""
    folder = Path(folder) if folder is not None else index_dir()
    out = {}
    for name in encyclopedias.list_files(root):
        path = encyclopedias.zim_path(name, root)
        if path is None:
            continue
        try:
            stem = _stem_for(name, path, folder)
        except OSError:
            continue
        if stem is None:
            continue
        with _lock:
            got = _loaded.get(stem)
            if got is None and stem not in _failed:
                t = time.perf_counter()
                try:
                    got = _loaded[stem] = Index(stem, folder)
                    print(f'encyclopedia vectors: {name} loaded in {time.perf_counter() - t:.1f} s '
                          f'({len(got.paths)} articles, {len(got.V)} sections)', flush=True)
                except Exception as e:
                    _failed[stem] = f'{type(e).__name__}: {e}'[:200]
                    print(f'encyclopedia vectors: {name} skipped ({_failed[stem]})', flush=True)
        if got is not None:
            out[name] = got
    return out


def _excerpt(arc, article, start, query, cap):
    got = encyclopedias.entry_text(arc, article, cap=None)
    if not got or not got[1]:
        return None
    for s, sec in sections.cut(sections.norm_ws(got[1]), sections.SECTION):
        if s == start:
            return got[0], encyclopedias.pick_section(sec, query, cap)
    return got[0], encyclopedias.pick_section(got[1], query, cap)      # the article changed: its best part by words


def pick(q, limit=encyclopedias.INITIAL_LIMIT, excerpt=encyclopedias.INITIAL_CHARS, root=None, folder=None,
         embed=None, opener=None):
    """Up to `limit` hits (the dicts of encyclopedias.search, plus 'score': the cosine) for q, by meaning; None when the
    vector index cannot answer, so the caller falls back. embed and opener are for tests."""
    if not on() or not (q or '').strip():
        return None
    try:
        idx = indexes(root, folder)
        if not idx:
            return None
        if embed is None:
            m = meaning_red._model
            if m is None:
                return None
            embed = m.embed
        qv = embed([(QUERY_PREFIX if prefix() else '') + q[:2000]])[0]
        cand = sorted(((c, name, ai, row) for name, ix in idx.items() for c, ai, row in ix.top(qv, limit)),
                      key=lambda t: -t[0])
        opener = opener or encyclopedias._open_archive
        hits = []
        for c, name, ai, row in cand:
            ix = idx[name]
            article = ix.paths[ai]
            got = _excerpt(opener(encyclopedias.zim_path(name, root)), article, int(ix.start[row]), q, excerpt)
            if not got:
                continue
            title, text = got
            hits.append({'title': title or ix.titles[ai], 'collection': Path(name).stem, 'zim': name, 'article': article,
                         'zim_key': encyclopedias.zim_key(name, article), 'path': encyclopedias.ui_path(name, article),
                         'publisher': encyclopedias.publisher(name), 'year': encyclopedias.year_of(name),
                         'trust': encyclopedias.TRUST, 'kind': 'zim', 'excerpt': text, 'score': round(c, 4)})
            if len(hits) >= limit:
                break
        return hits
    except Exception as e:
        print(f'encyclopedia vectors: {type(e).__name__}: {e}'[:300], flush=True)
        return None


def _reset_for_tests():
    with _lock:
        _loaded.clear()
        _failed.clear()
