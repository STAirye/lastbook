"""fork: a meaning-based check for questions that may be urgent (docs/FORK.md 3m).

The word rule (engine/confidence.urgent and assistant.is_danger) misses urgent questions worded in ways it has no word for
("his throat is closing after peanuts", "my son says voices are telling him to jump"). This adds a second opinion from
meaning: the question, after typos.correct and with no query prefix, is embedded with bge-small-en-v1.5 (the model hybrid
search uses; here a q8_0 GGUF file) and compared with 31 centroids, one per category of the invented examples in
engine/data/meaning_red_examples.jsonl (20 red categories, 10 look-alike green ones and yellow).

  score = max cosine to a red centroid - max cosine to a non-red centroid;  fired = score > the "wide" threshold

It is used only as `urgent = words OR meaning`: it can add an urgent flag, never remove one. A false flag only means a
question's pages are never held back.

The embedding is done by the app's own local-AI program (lastbook-llm, packaging/llm/lastbook_llm.cpp) started a second time
as `--embed --cpu-only`: a separate, long-lived process that reads one JSON line per question from its standard input and
answers one on its standard output (no socket, no port), as the chat one does. This process, the desktop, loads no model and
no onnxruntime for it, and opens nothing (upstream's rule, test_bridge's WholeProcess test). The runner is stopped when the
app exits (atexit; on Windows it also dies with the app's job object, on a Mac or Linux when its input closes).

Files (bge-small-en-v1.5-q8_0.gguf, centroids.npz; MANIFEST lists their sizes and SHA-256), looked for in order:
  1. APP/derived/models/meaning-red/    the source tree (tools/meaning_red_model.py writes them there)
  2. <the runner's folder>/meaning-red/ the packaged app, whose build copies that folder in next to the runner when it is there
  3. DATA/derived/models/meaning-red/   where setup downloads them (fetch(), from Hugging Face, next to the local AI model)
Each file is checked against MANIFEST before use. Starting runs on a background thread (start(), from server.init) and never
blocks a question: until the runner is ready, or when anything fails (a missing or changed file, no runner, a runner without
--embed, a runner that ends or stops answering), the words alone decide, as before, and the log says so once. A runner that
ended is started again, at most MAX_RESTARTS times in all. LASTBOOK_MEANING_RED=0 turns it off.
"""
import atexit
import collections
import hashlib
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

import engine.paths as lastbook_paths

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'data' / 'meaning_red_manifest.json'
SUBDIR = Path('derived') / 'models' / 'meaning-red'
GGUF = 'bge-small-en-v1.5-q8_0.gguf'
CENTROIDS = 'centroids.npz'
MAX_TOKENS = 320            # as retrieval.Embedder
THREADS = 2                 # about 5 ms a question on a Ryzen 7 5800X3D; leaves the CPU to the search and the AI
START_WAIT = 60             # seconds the runner has to say it is ready
ASK_WAIT = 10               # seconds it has to answer one question (about 0.005 s when well)
MAX_RESTARTS = 3            # a runner that ended is started again this many times, then the words alone for the rest of the run

_lock = threading.Lock()    # guards the state below
_thread = None
_model = None
_restarts = 0
_stopping = False
_registered = False
_status = {'state': 'not started', 'why': None, 'folder': None, 'load_s': None, 'restarts': 0}


def on():
    return os.environ.get('LASTBOOK_MEANING_RED', '1') != '0'


def manifest():
    with open(MANIFEST, encoding='utf-8') as f:
        return json.load(f)


def runner():
    """The local AI's program (llm_local finds it: APP/llm in the packaged app, derived/llm/bin-* in the source tree), or None."""
    import llm_local
    return llm_local.runner_path()


def folders():
    """Where the files may be, in the order they are tried."""
    out = [lastbook_paths.APP / SUBDIR]
    exe = runner()
    if exe is not None:
        out.append(exe.parent / 'meaning-red')
    out.append(lastbook_paths.DATA / SUBDIR)
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


class Embedder:
    """One lastbook-llm --embed process: start it, ask it for vectors, stop it. One question at a time."""

    def __init__(self, exe, gguf, threads=THREADS):
        import llm_local
        self.lock = threading.Lock()             # one request at a time: the answers come back in order on one pipe
        self.events = queue.Queue()
        self.err = collections.deque(maxlen=12)  # the runner's last lines on its error output, for the log
        self.next_id = 0
        self.proc = subprocess.Popen([str(exe), '--model', str(gguf), '--embed', '--cpu-only', '--threads', str(threads)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
                                     **llm_local._quiet())
        llm_local._tie_to_this_process(self.proc)
        threading.Thread(target=self._read, args=(self.proc, self.events), daemon=True, name='meaning-red-read').start()
        threading.Thread(target=self._drain, args=(self.proc, self.err), daemon=True, name='meaning-red-err').start()
        try:
            self.ready = self._wait_ready()
        except Exception:
            self.close()
            raise

    @staticmethod
    def _read(proc, events):
        try:
            for raw in proc.stdout:
                try:
                    events.put(json.loads(raw))
                except ValueError:
                    continue
        except (OSError, ValueError):
            pass
        events.put(None)        # the end of its output: it ended

    @staticmethod
    def _drain(proc, err):
        try:
            for raw in proc.stderr:
                err.append(raw.decode('utf-8', 'replace').rstrip())
        except (OSError, ValueError):
            pass

    def _tail(self):
        return ' | '.join(list(self.err)[-3:])[:300]

    def _wait_ready(self):
        end = time.time() + START_WAIT
        while True:
            try:
                ev = self.events.get(timeout=max(0.1, end - time.time()))
            except queue.Empty:
                raise TimeoutError(f'the runner was not ready in {START_WAIT} s') from None
            if ev is None:
                raise RuntimeError(f'the runner ended before it was ready (code {self.proc.poll()}) {self._tail()}')
            if ev.get('ev') == 'error':
                raise RuntimeError(f'the runner said {ev.get("code")}: {ev.get("msg")}')
            if ev.get('ev') == 'ready':
                if not ev.get('embed'):
                    raise RuntimeError('this runner has no --embed (an older runner)')
                return ev

    def embed(self, texts):
        """A list of unit vectors (lists of floats), one per text. Raises when the runner fails or does not answer."""
        with self.lock:
            self.next_id += 1
            rid = self.next_id
            line = json.dumps({'op': 'embed', 'id': rid, 'texts': list(texts), 'max_tokens': MAX_TOKENS}, ensure_ascii=False) + '\n'
            self.proc.stdin.write(line.encode('utf-8'))
            self.proc.stdin.flush()
            end = time.time() + ASK_WAIT
            while True:
                try:
                    ev = self.events.get(timeout=max(0.05, end - time.time()))
                except queue.Empty:
                    raise TimeoutError(f'no answer from the runner in {ASK_WAIT} s') from None
                if ev is None:
                    raise RuntimeError(f'the runner ended (code {self.proc.poll()}) {self._tail()}')
                if ev.get('id') != rid:
                    continue            # an answer to an earlier question that gave up
                if ev.get('ev') == 'embedding':
                    return ev['vectors']
                raise RuntimeError(f'the runner said {ev.get("code")}: {ev.get("msg")}')

    def close(self):
        proc = self.proc
        if proc.poll() is None:
            try:
                proc.stdin.write(b'{"op":"quit"}\n')
                proc.stdin.close()
                proc.wait(3)
            except (OSError, ValueError, subprocess.TimeoutExpired):
                proc.kill()
        for f in (proc.stdin, proc.stdout, proc.stderr):
            try:
                f.close()
            except (OSError, ValueError):
                pass


class Model:
    """The runner with the bge-small GGUF, and the centroids, from one folder."""

    def __init__(self, folder, exe=None, threads=THREADS):
        import numpy as np
        self.np = np
        exe = exe or runner()
        if exe is None:
            raise FileNotFoundError('no local AI program (lastbook-llm) to embed with')
        with np.load(folder / CENTROIDS) as z:
            self.R, self.N = z['red'].astype(np.float32), z['nonred'].astype(np.float32)
            self.threshold = float(z['wide'])
            self.strict = float(z['strict'])
        self.emb = Embedder(exe, folder / GGUF, threads)

    def embed(self, texts):
        """Unit [CLS] vectors, as retrieval.Embedder.embed."""
        return self.np.array(self.emb.embed(texts), dtype=self.np.float32)

    def score(self, text):
        v = self.embed([text])[0]
        return float((self.R @ v).max() - (self.N @ v).max())

    def close(self):
        self.emb.close()


def _load():
    global _model
    t = time.perf_counter()
    try:
        folder, why = find()
        if folder is None:
            raise FileNotFoundError(why)
        m = Model(folder)
        try:
            m.score('warm up')
        except Exception:
            m.close()
            raise
        with _lock:
            if _stopping:
                m.close()
                return
            _model = m
            _status.update(state='ready', why=None, folder=str(folder), load_s=round(time.perf_counter() - t, 2))
        print(f'meaning check: ready in {_status["load_s"]} s from {folder}', flush=True)
    except Exception as e:      # the words alone decide, as before
        with _lock:
            _status.update(state='off', why=f'{type(e).__name__}: {e}'[:300], load_s=round(time.perf_counter() - t, 2))
        print(f'meaning check: off, the urgent words alone decide ({_status["why"]})', flush=True)


def start():
    """Start the runner in the background, once. Returns at once."""
    global _thread, _registered
    if not on():
        return
    with _lock:
        if _thread is not None or _stopping:
            return
        _status['state'] = 'loading'
        _thread = threading.Thread(target=_load, name='meaning-red', daemon=True)
        _thread.start()
        if not _registered:
            _registered = True
            atexit.register(stop)


def stop():
    """Stop the runner (the app is leaving). Nothing is started again after this."""
    global _model, _stopping
    with _lock:
        m, _model, _stopping = _model, None, True
        _status.update(state='stopped')
    if m is not None:
        m.close()


def _lost(m, e):
    """The runner failed on a question (it ended, or did not answer): words alone for now, and start it again a few times."""
    global _model, _thread, _restarts
    with _lock:
        if _model is not m:     # another question already dealt with it
            return
        _model = None
        why = f'{type(e).__name__}: {e}'[:300]
        if _restarts < MAX_RESTARTS and not _stopping:
            _restarts += 1
            _status.update(state='loading', restarts=_restarts, why=why)
            print(f'meaning check: the runner failed ({why}); starting it again ({_restarts} of {MAX_RESTARTS})', flush=True)
            _thread = threading.Thread(target=_load, name='meaning-red', daemon=True)
            _thread.start()
        else:
            _status.update(state='off', why=why)
            print(f'meaning check: off, the urgent words alone decide ({why})', flush=True)
    m.close()


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
    """{'score': float or None, 'fired': bool, 'state'} for a question already put through typos.correct. Never waits for the
    runner to start and never starts it: before it is ready (or when it is off) score is None and fired False, so the words
    alone decide."""
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
        _lost(m, e)
        return {'score': None, 'fired': False, 'state': f'error: {type(e).__name__}'}
    return {'score': round(s, 4), 'fired': s > m.threshold, 'state': 'ready'}


def _reset_for_tests():
    global _thread, _model, _restarts, _stopping
    t = _thread
    if t is not None:
        t.join(90)
    with _lock:
        m, _thread, _model, _restarts, _stopping = _model, None, None, 0, False
        _status.update(state='not started', why=None, folder=None, load_s=None, restarts=0)
    if m is not None:
        m.close()


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
