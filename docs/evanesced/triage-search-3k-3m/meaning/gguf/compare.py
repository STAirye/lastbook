"""Smoke test: bge-small GGUF via the runner's libllama (probe.exe, or lastbook-llm --embed) vs ONNX fp32 / int8.
python -X utf8 compare.py [runner_exe_dir]"""
import json, os, random, subprocess, sys, time
from pathlib import Path
import numpy as np
import psutil

HERE = Path(__file__).resolve().parent
WT = Path(r'D:\git\lastbook\.claude\worktrees\meaning-check')
sys.path.insert(0, str(WT))
from engine import meaning_red  # noqa: E402

BIN = r'D:\git\lastbook\derived\llm\bin-win'
FP32 = Path(r'D:\LastbookData\derived\models\bge-small-en-v1.5\model.onnx')

rows = [json.loads(l) for l in open(HERE.parent / 'examples.jsonl', encoding='utf-8')]
random.seed(7)
picked = random.sample(rows, 20)
invented = [
    'my wife colapsed and wont wake up', 'he swalowed a batery', 'kid drank bleach a minute ago',
    'theres smoke in the kitchen and the alarm is going', 'how do i store rice for 10 years',
    'best way to purify creek water', 'chest pain going down my left arm', 'i cut my hand deep and it wont stop bleding',
    'how to make a solar oven', 'my dog ate chocolate', 'snake bit my leg its swelling',
    'how long does canned food last', 'I feel like ending it all tonight', 'grandpa face drooping and slurred speach',
    'can i eat dandelions', 'water in the basement after the storm', 'baby has a fever of 104 and is floppy',
    'how do i tie a bowline knot', 'allergic reaction throat feels tight', 'what is the capital of france',
]
edge = ['', ' ', 'word ' * 700, '🔥🔥 help 😱 my house is on fire 🔥', 'mi hijo no respira', '我的孩子不呼吸了',
        'он не дышит', 'a\\nb\\nc', '\u200b', '%s %d {} "quotes" \\ backslash']
texts = [r['text'] for r in picked] + invented


def onnx_embed(path, items):
    import onnxruntime as ort
    from tokenizers import Tokenizer
    so = ort.SessionOptions(); so.intra_op_num_threads = 2
    s = ort.InferenceSession(str(path), so, providers=['CPUExecutionProvider'])
    tok = Tokenizer.from_file(str(WT / 'derived/models/meaning-red/tokenizer.json'))
    tok.enable_truncation(max_length=meaning_red.MAX_TOKENS)
    out, n = [], []
    names = {i.name for i in s.get_inputs()}
    for t in items:
        e = tok.encode(t)
        ids = np.array([e.ids], dtype=np.int64)
        feed = {'input_ids': ids, 'attention_mask': np.ones_like(ids)}
        if 'token_type_ids' in names:
            feed['token_type_ids'] = np.zeros_like(ids)
        v = s.run(None, feed)[0][0, 0]
        out.append(v / max(np.linalg.norm(v), 1e-9)); n.append(len(e.ids))
    return np.array(out, dtype=np.float32), n


def probe(model, mode, items):
    """Returns vectors (None for errors), n_tokens, ms each, load_s, peak working set MB, stderr tail."""
    env = dict(os.environ, PATH=BIN + os.pathsep + os.environ['PATH'])
    t = time.perf_counter()
    p = subprocess.Popen([str(HERE / 'probe.exe'), str(model), BIN, mode, str(meaning_red.MAX_TOKENS)],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                         text=True, encoding='utf-8')
    out, err = p.communicate(''.join(x.replace('\n', ' ') + '\n' for x in items), timeout=300)
    wall = time.perf_counter() - t
    lines = out.splitlines()
    vecs, ns, ms = [], [], []
    for l in lines:
        if l.startswith('ERR'):
            vecs.append(None); ns.append(l); ms.append(None); continue
        f = l.split()
        ns.append(int(f[0])); ms.append(float(f[1])); vecs.append(np.array(f[2:], dtype=np.float32))
    load = [l for l in err.splitlines() if l.startswith('LOADED')]
    return dict(vecs=vecs, n=ns, ms=ms, wall=wall, rc=p.returncode, load=load, err=err[-400:])


def peak_mem(model, mode):
    env = dict(os.environ, PATH=BIN + os.pathsep + os.environ['PATH'])
    p = subprocess.Popen([str(HERE / 'probe.exe'), str(model), BIN, mode, '320'], stdin=subprocess.PIPE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, text=True, encoding='utf-8')
    for x in texts * 3:
        p.stdin.write(x + '\n'); p.stdin.flush()
    time.sleep(2)
    m = psutil.Process(p.pid).memory_info()
    p.stdin.close(); p.wait(60)
    return round(m.peak_wset / 2**20), round(m.private / 2**20)


def main():
    m8 = meaning_red.Model(WT / 'derived/models/meaning-red')
    R, N, thr = m8.R, m8.N, m8.threshold
    score = lambda v: float((R @ v).max() - (N @ v).max())
    ref32, n32 = onnx_embed(FP32, texts)
    ref8 = m8.embed(texts)
    res = {'threshold': thr, 'runs': {}}
    print(f'threshold {thr:.4f}')
    for name in ['f32', 'f16', 'q8_0']:
        for mode in ['cpu', 'gpu']:
            model = HERE / f'bge-small-en-v1.5-{name}.gguf'
            r = probe(model, mode, texts)
            V = np.array(r['vecs'])
            c32 = (V * ref32).sum(1); c8 = (V * ref8).sum(1)
            s_g = [score(v) for v in V]; s_32 = [score(v) for v in ref32]; s_8 = [score(v) for v in ref8]
            dis32 = [texts[i] for i in range(len(texts)) if (s_g[i] > thr) != (s_32[i] > thr)]
            dis8 = [texts[i] for i in range(len(texts)) if (s_g[i] > thr) != (s_8[i] > thr)]
            tokmis = [texts[i] for i in range(len(texts)) if r['n'][i] != n32[i]]
            pk = peak_mem(model, mode)
            row = dict(cos32_min=float(c32.min()), cos32_mean=float(c32.mean()), cos8_min=float(c8.min()),
                       cos8_mean=float(c8.mean()), score_maxdiff32=float(np.abs(np.array(s_g) - s_32).max()),
                       dis32=dis32, dis8=dis8, tokmis=tokmis, ms_median=float(np.median(r['ms'][1:])),
                       ms_max=float(max(r['ms'][1:])), load=r['load'], wall=round(r['wall'], 2), peak_mb=pk,
                       fired=sum(s > thr for s in s_g), fired32=sum(s > thr for s in s_32), fired8=sum(s > thr for s in s_8))
            res['runs'][f'{name}/{mode}'] = row
            print(f'{name}/{mode}: cos32 min {row["cos32_min"]:.5f} mean {row["cos32_mean"]:.5f} | cos8 min {row["cos8_min"]:.5f} '
                  f'mean {row["cos8_mean"]:.5f} | score diff {row["score_maxdiff32"]:.4f} | dis32 {dis32} dis8 {dis8} | '
                  f'tokmis {tokmis} | ms med {row["ms_median"]:.2f} max {row["ms_max"]:.2f} | {r["load"]} wall {r["wall"]:.2f}s | '
                  f'peak/private MB {pk} | fired {row["fired"]}/{row["fired32"]}/{row["fired8"]}')
    # int8 vs fp32 for scale
    c = (ref8 * ref32).sum(1)
    print(f'onnx int8 vs fp32: min {c.min():.5f} mean {c.mean():.5f}')
    res['int8_vs_fp32'] = [float(c.min()), float(c.mean())]
    # edge cases
    e32, en = onnx_embed(FP32, [x.replace('\\n', '\n') for x in edge])
    for name, mode in [('q8_0', 'cpu'), ('f16', 'gpu')]:
        r = probe(HERE / f'bge-small-en-v1.5-{name}.gguf', mode, edge)
        print(f'edge {name}/{mode}: rc {r["rc"]}, {len(r["vecs"])} answers for {len(edge)}')
        res['edge_' + name + mode] = []
        for i, x in enumerate(edge):
            v = r['vecs'][i] if i < len(r['vecs']) else 'missing'
            cs = None if v is None or isinstance(v, str) else float(v @ e32[i])
            sc = None if cs is None else score(v)
            print(f'   {x[:40]!r}: n {r["n"][i] if i < len(r["n"]) else "-"} (onnx {en[i]}) cos {cs} score {sc}')
            res['edge_' + name + mode].append([x[:40], r['n'][i] if i < len(r['n']) else None, en[i], cs])
        if r['rc']:
            print(r['err'])
    json.dump(res, open(HERE / 'compare_results.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
