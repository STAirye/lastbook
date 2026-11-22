"""Smoke test of lastbook-llm --embed (scratch build) and of it beside a loaded Gemma runner (the app's bin-win).
python -X utf8 runner_test.py"""
import json, subprocess, sys, threading, time
from pathlib import Path
import numpy as np
import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compare  # noqa: E402  (texts, edge, onnx_embed, meaning_red)

EMB = Path(r'D:\buildtools\lastbook-llm\work-meaning\bin-win\lastbook-llm.exe')
APP = Path(r'D:\git\lastbook\derived\llm\bin-win\lastbook-llm.exe')
GEMMA = Path(r'D:\LastbookData\models\gemma-4-E4B-it-Q4_K_M.gguf')


class Runner:
    def __init__(self, exe, args):
        self.t0 = time.perf_counter()
        self.p = subprocess.Popen([str(exe)] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, cwd=str(exe.parent))
        self.err = []
        threading.Thread(target=lambda: [self.err.append(l.decode('utf-8', 'replace')) for l in self.p.stderr], daemon=True).start()

    def read(self, want, timeout=180):
        while True:
            l = self.p.stdout.readline()
            if not l:
                return {'ev': 'EOF', 'rc': self.p.poll(), 'stderr': ''.join(self.err[-8:])}
            ev = json.loads(l)
            if ev.get('ev') in want:
                return ev

    def send(self, obj):
        self.p.stdin.write((json.dumps(obj, ensure_ascii=False) + '\n').encode('utf-8')); self.p.stdin.flush()

    def mem(self):
        m = psutil.Process(self.p.pid).memory_info()
        return round(m.peak_wset / 2**20), round(m.private / 2**20)

    def quit(self):
        try:
            self.send({'op': 'quit'}); self.p.wait(20)
        except Exception:
            self.p.kill()


def vram():
    try:
        return subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader'], capture_output=True,
                              text=True, encoding='utf-8').stdout.strip()
    except Exception:
        return '?'


def embed_runner(model, cpu=True):
    r = Runner(EMB, ['--model', str(model), '--embed'] + (['--cpu-only'] if cpu else []) + ['--threads', '2'])
    ready = r.read({'ready', 'error'})
    load_s = time.perf_counter() - r.t0
    return r, ready, load_s


def main():
    m8 = compare.meaning_red.Model(compare.WT / 'derived/models/meaning-red')
    score = lambda v: float((m8.R @ v).max() - (m8.N @ v).max())
    texts = compare.texts
    ref32, _ = compare.onnx_embed(compare.FP32, texts)
    model = HERE / 'bge-small-en-v1.5-q8_0.gguf'
    print('VRAM before', vram())
    r, ready, load_s = embed_runner(model)
    print('ready:', {k: v for k, v in ready.items() if k != 'desc'}, f'load {load_s:.2f}s')
    # one request per text, as the app would ask (one question at a time)
    V, ms = [], []
    for i, t in enumerate(texts):
        t1 = time.perf_counter()
        r.send({'op': 'embed', 'id': i, 'texts': [t], 'max_tokens': 320})
        ev = r.read({'embedding', 'error'})
        ms.append((time.perf_counter() - t1) * 1000)
        V.append(np.array(ev['vectors'][0], dtype=np.float32))
    V = np.array(V)
    c = (V * ref32).sum(1)
    dis = [t for t, v, w in zip(texts, V, ref32) if (score(v) > m8.threshold) != (score(w) > m8.threshold)]
    print(f'runner q8_0 cpu: cos vs fp32 min {c.min():.5f} mean {c.mean():.5f}; verdict disagreements vs fp32 {dis}; '
          f'round trip ms median {np.median(ms[1:]):.2f} max {max(ms[1:]):.2f}; mem peak/private MB {r.mem()}')
    # a batch request
    r.send({'op': 'embed', 'id': 'b', 'texts': texts, 'max_tokens': 320})
    ev = r.read({'embedding', 'error'})
    print('batch of', len(texts), 'ms', ev.get('ms'))
    # edge cases, each its own request, then bad requests
    for i, t in enumerate([x.replace('\\n', '\n') for x in compare.edge] + ['word ' * 700]):
        r.send({'op': 'embed', 'id': f'e{i}', 'texts': [t], 'max_tokens': 5000})
        ev = r.read({'embedding', 'error'})
        print('  edge', repr(t[:30]), ev.get('ev'), ev.get('n_tokens'), ev.get('code'))
    for bad in [{'op': 'embed', 'id': 'x', 'texts': [1, 2]}, {'op': 'embed', 'id': 'y'}, {'op': 'gen', 'id': 'z', 'prompt': 'hi'},
                {'op': 'embed', 'id': 'w', 'texts': ['ok'], 'max_tokens': -3}]:
        r.send(bad)
        r.send({'op': 'embed', 'id': 'after', 'texts': ['still alive?']})
        ev = r.read({'embedding', 'error'})
        print('  bad', json.dumps(bad), '->', ev.get('ev'), ev.get('code'), ev.get('msg'), ev.get('n_tokens'))
        if ev.get('id') != 'after':
            print('     then', r.read({'embedding', 'error'}).get('ev'))
    print('alive:', r.p.poll() is None, 'mem', r.mem())
    # beside Gemma: load the app's runner with E4B, then embed again with both resident
    g = Runner(APP, ['--model', str(GEMMA)])
    gready = g.read({'ready', 'error'})
    print('gemma:', gready.get('ev'), gready.get('n_ctx'), f'load {time.perf_counter() - g.t0:.1f}s', 'VRAM', vram(), 'gemma mem', g.mem())
    ms2 = []
    for t in texts[:10]:
        t1 = time.perf_counter()
        r.send({'op': 'embed', 'id': 1, 'texts': [t], 'max_tokens': 320}); r.read({'embedding', 'error'})
        ms2.append((time.perf_counter() - t1) * 1000)
    g.send({'op': 'gen', 'id': 9, 'segments': [['<|turn>user\n', True], ['Say OK.', False], ['<turn|>\n<|turn>model\n', True]],
            'max_tokens': 8})
    gd = g.read({'done', 'error'})
    print(f'embed beside gemma: median {np.median(ms2):.2f} ms; gemma gen -> {gd.get("ev")} {gd.get("reason")}; both alive',
          r.p.poll() is None, g.p.poll() is None)
    g.quit(); r.quit()
    # GPU embed runner for comparison
    r, ready, load_s = embed_runner(model, cpu=False)
    ms3 = []
    for t in texts:
        t1 = time.perf_counter()
        r.send({'op': 'embed', 'id': 1, 'texts': [t], 'max_tokens': 320}); r.read({'embedding', 'error'})
        ms3.append((time.perf_counter() - t1) * 1000)
    print(f'runner q8_0 Vulkan: load {load_s:.2f}s, ms median {np.median(ms3[1:]):.2f} max {max(ms3[1:]):.0f}, mem {r.mem()}, VRAM {vram()}')
    r.quit()


if __name__ == '__main__':
    main()
