"""fork: a meaning-based check for questions that may be urgent (docs/FORK.md 3m).

The word rule (engine/confidence.urgent and assistant.is_danger) misses urgent questions worded in ways it has no word for
("his throat is closing after peanuts", "my son says voices are telling him to jump"). This adds a second opinion from
meaning: the question, after typos.correct and with no query prefix, is embedded with an int8 copy of bge-small-en-v1.5
(the model hybrid search uses) and compared with 31 centroids, one per category of the invented examples in
engine/data/meaning_red_examples.jsonl (20 red categories, 10 look-alike green ones and yellow).

  score = max cosine to a red centroid - max cosine to a non-red centroid;  fired = score > the "wide" threshold

It is used only as `urgent = words OR meaning`: it can add an urgent flag, never remove one. A false flag only means a
question's pages are never held back.

Files (model_int8.onnx, tokenizer.json, centroids.npz; MANIFEST lists their sizes and SHA-256), looked for in order:
  1. APP/derived/models/meaning-red/   the source tree (tools/meaning_red_model.py writes them there), or the packaged app,
                                       whose build copies that folder in when it is there
  2. DATA/derived/models/meaning-red/  where setup downloads them (fetch(), from Hugging Face, next to the local AI model)
Each file is checked against MANIFEST before use. Loading runs on a background thread (start(), from server.init) and
never blocks a question: until it has loaded, or when anything fails (a missing or changed file, no onnxruntime), the
words alone decide, as before, and the log says so once. LASTBOOK_MEANING_RED=0 turns it off.
"""
import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

import engine.paths as lastbook_paths

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'data' / 'meaning_red_manifest.json'
SUBDIR = Path('derived') / 'models' / 'meaning-red'
MAX_TOKENS = 320            # as retrieval.Embedder
THREADS = 2                 # 2.6 ms a question on a Ryzen 7 5800X3D; leaves the CPU to the search and the AI

_lock = threading.Lock()    # guards the state below
_run_lock = threading.Lock()    # one embedding at a time (tokenizer and session together)
_thread = None
_model = None
_status = {'state': 'not started', 'why': None, 'folder': None, 'load_s': None}


def on():
    return os.environ.get('LASTBOOK_MEANING_RED', '1') != '0'


def manifest():
    with open(MANIFEST, encoding='utf-8') as f:
        return json.load(f)


def folders():
    """Where the files may be, in the order they are tried."""
    out = [lastbook_paths.APP / SUBDIR, lastbook_paths.DATA / SUBDIR]
    return list(dict.fromkeys(out))


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def find(check=True):
    """The first folder holding every file of the manifest with its size (and SHA-256, when check), or None, with why."""
    files = manifest()['files']
    why = 'no meaning-red files in ' + ' or '.join(str(d) for d in folders())
    for d in folders():
        if not all((d / f['name']).is_file() for f in files):
            continue
        bad = [f['name'] for f in files if (d / f['name']).stat().st_size != f['size']
               or (check and sha256_of(d / f['name']) != f['sha256'])]
        if not bad:
            return d, None
        why = f'{", ".join(bad)} in {d} not the files of {MANIFEST.name}'
    return None, why


def _import_runtime():
    """onnxruntime and tokenizers, with telemetry off as retrieval.py does it (engine/quiet_onnx.py on Windows)."""
    if 'onnxruntime' in sys.modules and sys.modules['onnxruntime'] is None:
        raise ImportError('onnxruntime is blocked in this process')     # the tests that run with no model; quiet_onnx would still load its DLL
    os.environ['ORT_DISABLE_TELEMETRY'] = '1'
    if os.name == 'nt':
        from engine import quiet_onnx
        quiet_onnx.silence()      # before the import, which already writes usage events to Windows. If this fails, no import.
    import numpy as np
    import onnxruntime as ort
    from tokenizers import Tokenizer
    if hasattr(ort, 'disable_telemetry_events'):
        ort.disable_telemetry_events()
    return np, ort, Tokenizer


class Model:
    """The int8 bge-small, its tokenizer and the centroids, from one folder."""

    def __init__(self, folder, threads=THREADS):
        np, ort, Tokenizer = _import_runtime()
        self.np = np
        so = ort.SessionOptions()
        so.intra_op_num_threads = max(1, min(threads, os.cpu_count() or 1))
        so.inter_op_num_threads = 1
        self.sess = ort.InferenceSession(str(folder / 'model_int8.onnx'), so, providers=['CPUExecutionProvider'])
        self.tok = Tokenizer.from_file(str(folder / 'tokenizer.json'))
        self.tok.enable_truncation(max_length=MAX_TOKENS)
        self.tok.enable_padding()
        self.inputs = {i.name for i in self.sess.get_inputs()}
        c = folder / 'centroids.npz'
        if c.is_file():
            with np.load(c) as z:
                self.R, self.N = z['red'].astype(np.float32), z['nonred'].astype(np.float32)
                self.threshold = float(z['wide'])
                self.strict = float(z['strict'])

    def embed(self, texts):
        """Unit [CLS] vectors, as retrieval.Embedder.embed."""
        np = self.np
        with _run_lock:
            enc = self.tok.encode_batch(list(texts))
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feed = {'input_ids': ids, 'attention_mask': mask}
            if 'token_type_ids' in self.inputs:
                feed['token_type_ids'] = np.zeros_like(ids)
            out = self.sess.run(None, feed)[0]
        v = out[:, 0, :]
        v = v / np.linalg.norm(v, axis=1, keepdims=True).clip(1e-9)
        return v.astype(np.float32)

    def score(self, text):
        v = self.embed([text])[0]
        return float((self.R @ v).max() - (self.N @ v).max())


def _load():
    global _model
    t = time.perf_counter()
    try:
        folder, why = find()
        if folder is None:
            raise FileNotFoundError(why)
        m = Model(folder)
        m.score('warm up')
        with _lock:
            _model = m
            _status.update(state='ready', why=None, folder=str(folder), load_s=round(time.perf_counter() - t, 2))
        print(f'meaning check: ready in {_status["load_s"]} s from {folder}', flush=True)
    except Exception as e:      # the words alone decide, as before
        with _lock:
            _status.update(state='off', why=f'{type(e).__name__}: {e}'[:300], load_s=round(time.perf_counter() - t, 2))
        print(f'meaning check: off, the urgent words alone decide ({_status["why"]})', flush=True)


def start():
    """Load in the background, once. Returns at once."""
    global _thread
    if not on():
        return
    with _lock:
        if _thread is not None:
            return
        _status['state'] = 'loading'
        _thread = threading.Thread(target=_load, name='meaning-red', daemon=True)
        _thread.start()


def wait(timeout=None):
    """For tools and tests: start, and wait for the load to end. True when ready."""
    start()
    t = _thread
    if t is not None:
        t.join(timeout)
    return _model is not None


def status():
    with _lock:
        return dict(_status, on=on())


def check(text):
    """{'score': float or None, 'fired': bool, 'state'} for a question already put through typos.correct. Never blocks on
    the load and never starts it: before it is ready (or when it is off) score is None and fired False, so the words alone
    decide."""
    if not on():
        return {'score': None, 'fired': False, 'state': 'switched off'}
    m = _model
    if m is None:       # loading, off, or never started (server.init starts it; tools and tests call start or wait)
        return {'score': None, 'fired': False, 'state': _status['state']}
    if not (text or '').strip():
        return {'score': None, 'fired': False, 'state': 'ready'}
    try:
        s = m.score(text[:2000])
    except Exception as e:
        return {'score': None, 'fired': False, 'state': f'error: {type(e).__name__}'}
    return {'score': round(s, 4), 'fired': s > m.threshold, 'state': 'ready'}


def _reset_for_tests():
    global _thread, _model
    with _lock:
        _thread, _model = None, None
        _status.update(state='not started', why=None, folder=None, load_s=None)


# ------------------------------------------------------------------ download (setup) --
def urls():
    """[(name, url, size, sha256)] on Hugging Face, or None while the manifest names no published revision."""
    m = manifest()
    rev = m.get('revision') or ''
    if len(rev) != 40 or any(c not in '0123456789abcdef' for c in rev):
        return None
    return [(f['name'], f"https://huggingface.co/{m['repo']}/resolve/{rev}/{f['name']}", f['size'], f['sha256'])
            for f in m['files']]


def fetch(control=None, allowed=None, context=None, dest=None):
    """Downloads the files into DATA/derived/models/meaning-red (or dest) through engine/setup/download.py, as setup gets the
    local AI model: HTTPS to Hugging Face only, each file's SHA-256 checked. Called by setup after the person's own download
    of the local AI model, never on its own. Returns 'present', 'fetched', or 'unpublished' (no revision in the manifest yet).
    Raises what download.Download raises; the caller goes on without it."""
    folder, _ = find(check=False)
    if folder is not None:
        return 'present'
    todo = urls()
    if todo is None:
        return 'unpublished'
    from engine.setup import download
    dest = Path(dest or (lastbook_paths.DATA / SUBDIR))
    control = control or download.Control()
    for name, url, size, sha in todo:
        if (dest / name).is_file() and (dest / name).stat().st_size == size and sha256_of(dest / name) == sha:
            continue
        download.Download(url, dest / name, size, sha, control, allowed=allowed, context=context, connections=1).run()
    return 'fetched'
