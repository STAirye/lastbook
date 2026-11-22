"""Shared helpers: load the repo's engine read-only, embed with bge-small (same Embedder as retrieval.py), cache vectors."""
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('LASTBOOK_DATA', r'D:\LastbookData-fork-test')
REPO = Path(r'D:\git\lastbook')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402

import retrieval  # noqa: E402
from engine import typos, confidence  # noqa: E402

CACHE = HERE / 'cache'
CACHE.mkdir(exist_ok=True)
_emb = None


def embedder():
    global _emb
    if _emb is None:
        if os.environ.get('MEANING_MODEL_DIR'):     # e.g. the int8 copy in cache/int8 (Phase D)
            retrieval.MODEL = Path(os.environ['MEANING_MODEL_DIR'])
        _emb = retrieval.Embedder()
    return _emb


def read_jsonl(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]


def corrected(texts):
    return [typos.correct(t) or t for t in texts]


def embed(texts, prefix=False, tag='x'):
    """Unit vectors, cached on disk by content hash."""
    pre = retrieval.QUERY_PREFIX if prefix else ''
    h = hashlib.sha1(('\n'.join(texts) + '|' + pre).encode('utf-8')).hexdigest()[:16]
    tag += '-int8' if 'int8' in os.environ.get('MEANING_MODEL_DIR', '') else ''
    p = CACHE / f'{tag}-{int(prefix)}-{h}.npy'
    if p.exists():
        return np.load(p)
    e = embedder()
    out = np.vstack([e.embed([pre + t for t in texts[i:i + 64]]) for i in range(0, len(texts), 64)])
    np.save(p, out)
    return out


def words_flag(text):
    """The current word rule as assistant.is_danger calls urgent(): as typed and corrected (no english words here)."""
    return bool(confidence.urgent(text, typos.correct(text)))
