"""Runs the off-screen app in a child process and talks to it through files. Stops only that child, by PID. No sockets."""
import itertools, json, os, signal, subprocess, sys, time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
PY = ROOT / 'derived/app-only-proof/mac/venv/bin/python'
DATA = ROOT / 'derived/app-only-proof/mac/data'
_n = itertools.count(1)
HELP = r"""
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (f, ms = 15000) => { const t = performance.now(); while (performance.now() - t < ms) { try { const v = f(); if (v) return v } catch {} await sleep(50) } return null };
"""


class Run:
    def __init__(self, name, *args):
        self.name = name
        self.out = ROOT / 'derived/app-build/mac-run' / name
        self.ctl = self.out / 'ctl'
        self.ctl.mkdir(parents=True, exist_ok=True)
        (self.out / 'shots').mkdir(exist_ok=True)
        self.stdout = open(self.out / 'stdout.txt', 'ab')
        self.p = subprocess.Popen([str(PY), str(APP / 'tests/mac_offscreen.py'), '--run', name, '--data', str(DATA), *args], stdout=self.stdout, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                  env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        print('app pid', self.p.pid, flush=True)
        self.results = {}

    def cmd(self, kind, timeout=60, **k):
        i = f'{time.time_ns()}-{next(_n)}'
        t = self.ctl / f'{i}.tmp'
        t.write_text(json.dumps(dict(k, id=i, kind=kind)))
        t.replace(self.ctl / f'{i}.cmd')
        o = self.ctl / f'{i}.out'
        end = time.time() + timeout
        while time.time() < end:
            if self.p.poll() is not None:
                return {'error': f'app exited {self.p.returncode}', 'kind': kind}
            if o.exists():
                v = json.loads(o.read_text())
                o.unlink()
                return v
            time.sleep(0.02)
        return {'error': 'timeout', 'kind': kind}

    def js(self, code, timeout=60):
        v = self.cmd('js', timeout=timeout, code=HELP + code)
        if v.get('error'):
            return {'__error': v['error']}
        r = v.get('result')
        return json.loads(r) if r not in (None, 'None') else None

    def go(self, h, sel=None, wait=800, ms=15000):
        return self.js(f"location.hash={json.dumps(h)}; await sleep(100); " + (f"await until(()=>document.querySelector({json.dumps(sel)}),{ms}); " if sel else '') + f"await sleep({wait}); return location.href", timeout=ms / 1000 + wait / 1000 + 20)

    def shot(self, name):
        return self.cmd('shot', path=str(self.out / 'shots' / name))

    def wait_up(self, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            r = self.js("return document.readyState==='complete' && !!document.querySelector('#main h1')", timeout=5) if self.p.poll() is None else None
            if r is True:
                return True
            time.sleep(0.3)
        return False

    def rec(self, k, v):
        self.results[k] = v
        print(k, json.dumps(v, default=str)[:2500], flush=True)

    def log(self, name, since=0):
        out = []
        f = self.out / f'{name}.jsonl'
        if f.exists():
            for l in open(f):
                try:
                    r = json.loads(l)
                except ValueError:
                    continue
                if r.get('ts', r.get('t', 0)) >= since:
                    out.append(r)
        return out

    def mem(self):
        rows = self.log('mem')
        return {k: round(v / 1e6) for k, v in rows[-1].items() if k in ('app', 'WebContent', 'GPU', 'Networking') and v} if rows else {}

    def outside(self):
        """Sockets and model files, seen from outside the process."""
        pids = json.loads((self.out / 'pids.json').read_text())
        l = ','.join(str(p) for p in pids.values() if p)
        run = lambda *c: subprocess.run(c, capture_output=True, text=True, timeout=30).stdout
        listen = run('/usr/sbin/lsof', '-nP', '-a', '-p', l, '-iTCP', '-sTCP:LISTEN')
        inet = run('/usr/sbin/lsof', '-nP', '-a', '-p', l, '-i')
        files = run('/usr/sbin/lsof', '-nP', '-a', '-p', l)
        models = [x for x in files.splitlines() if any(s in x.lower() for s in ('onnx', 'bge-small', 'tokenizers', '/models/'))]
        real = [x for x in files.splitlines() if 'survival/library-data' in x or 'video-auth' in x]
        return {'pids': pids, 'listen': listen, 'inet': inet, 'model_files': models, 'real_library_files': real}

    def stop(self):
        if self.p.poll() is None:
            self.cmd('quit', timeout=3)
            try:
                self.p.wait(8)
            except subprocess.TimeoutExpired:
                os.kill(self.p.pid, signal.SIGTERM)
                self.p.wait(8)
        print('app exit', self.p.returncode, flush=True)
        (self.out / 'results.json').write_text(json.dumps(self.results, indent=1, default=str))
