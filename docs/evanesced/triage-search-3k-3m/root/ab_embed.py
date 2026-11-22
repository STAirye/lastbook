"""A/B: bge-small vectors from onnxruntime (A, what the index was built with) against lastbook-llm --embed (B, llama.cpp).

    python -I ab_embed.py DATA_DIR RUNNER_EXE GGUF OUT.json [--sample N]

Checks, on the built index in DATA_DIR/derived/index:
  1. passages: N random stored passages re-embedded by A and by B; cosine of each against the stored vector
  2. questions: the questions below embedded by A and by B (with the index's query prefix); cosine A-B, and the top 10
     passages each finds in the whole index (same best passage? how many of the 10 shared?)
  3. speed: passages a second for A and B, and the time for one question
B runs twice: on the GPU (Vulkan, the runner's default) and with --cpu-only.
"""
import json, random, sqlite3, subprocess, sys, time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

DIM, MAXTOK = 384, 320
PREFIX = 'Represent this sentence for searching relevant passages: '
QUESTIONS = [
    'burned my hand trying to light a fire', 'i burnt my fingers lighting the campfire',
    'smoke inhalation from lighting a fire indoors', 'carbon monoxide from making a fire in the tent',
    'my clothes caught fire while starting the fire', 'my kid fell into the fire while we were making a fire',
    'treat water in the lungs after drowning', 'how do i treat water blisters on a burn', 'how do i treat water poisoning',
    'light a fire to keep him warm with hypothermia', 'my son nearly drowned in the rainwater pool',
    "someone fell in the rainwater pool and isn't breathing", "he swallowed pool water and now he's coughing",
    'drank creek water and now i have diarrhea', 'my child swallowed lamp oil', 'scorpion sting on my foot',
    'rash from poison ivy', 'snake bite while camping', 'hypothermia after falling in cold water',
    'someone got shocked by a wire in the flood water', 'is it safe to put water on a burn',
    'i burned my hand on the camp stove', 'how do i treat a burn from a campfire', 'how do i light a campfire',
    'i need to start a fire but i have no matches and no gas', 'how do i make the water safe to drink',
    'how do i purify water from a creek', "how to make the water safe for a baby's formula",
    'make a fire escape plan for my family', 'what could make a fire spread faster', 'pour water on a grease fire',
    'how do i treat water damage on the floor', 'how can i know if my can food has gone bad',
    'someone is full of blood, it does not stop', 'Honda EU2200i oil change', 'burn and not breathing',
]


class Onnx:
    def __init__(self, model_dir):
        so = ort.SessionOptions()
        self.sess = ort.InferenceSession(str(model_dir / 'model.onnx'), so, providers=['CPUExecutionProvider'])
        self.tok = Tokenizer.from_file(str(model_dir / 'tokenizer.json'))
        self.tok.enable_truncation(max_length=MAXTOK)
        self.tok.enable_padding()
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def embed(self, texts):
        enc = self.tok.encode_batch(texts)
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        feed = {'input_ids': ids, 'attention_mask': np.array([e.attention_mask for e in enc], dtype=np.int64)}
        if 'token_type_ids' in self.inputs:
            feed['token_type_ids'] = np.zeros_like(ids)
        v = self.sess.run(None, feed)[0][:, 0, :]
        return (v / np.linalg.norm(v, axis=1, keepdims=True).clip(1e-9)).astype(np.float32)


class Runner:
    def __init__(self, exe, gguf, cpu_only):
        argv = [exe, '--embed', '--model', gguf] + (['--cpu-only'] if cpu_only else [])
        self.p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        self.ready = self._wait('ready')

    def _wait(self, ev):
        for raw in self.p.stdout:
            j = json.loads(raw)
            if j.get('ev') == 'error':
                raise RuntimeError(j)
            if j.get('ev') == ev:
                return j
        raise RuntimeError('runner stopped')

    def embed(self, texts):
        self.p.stdin.write((json.dumps({'op': 'embed', 'id': 1, 'texts': list(texts), 'max_tokens': MAXTOK}) + '\n').encode('utf-8'))
        return np.array(self._wait('embedding')['vectors'], dtype=np.float32).reshape(-1, DIM)

    def close(self):
        try:
            self.p.stdin.write(b'{"op":"quit"}\n')
            self.p.wait(10)
        except Exception:
            self.p.kill()


def timed(fn, texts, batch=16):
    t = time.time()
    out = np.concatenate([fn(texts[i:i + batch]) for i in range(0, len(texts), batch)])
    return out, len(texts) / (time.time() - t)


def main():
    data, exe, gguf, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    n = int(sys.argv[sys.argv.index('--sample') + 1]) if '--sample' in sys.argv else 2000
    idx = data / 'derived' / 'index'
    db = sqlite3.connect(f'file:{idx / "semantic.sqlite"}?mode=ro', uri=True)
    raw = np.fromfile(idx / 'vectors.f16', dtype=np.float16)
    mat = raw[:len(raw) // DIM * DIM].reshape(-1, DIM)
    rows = min(len(mat), db.execute('SELECT MAX(id) FROM chunk').fetchone()[0] or 0)
    active = np.array([i - 1 for (i,) in db.execute('SELECT id FROM chunk WHERE active=1 AND id<=?', (rows,))])
    act = mat[active].astype(np.float32)
    rnd = random.Random(1)
    pick = sorted(rnd.sample(list(active), min(n, len(active))))
    texts = [db.execute('SELECT text FROM chunk WHERE id=?', (int(i) + 1,)).fetchone()[0] for i in pick]
    stored = mat[pick].astype(np.float32)
    res = {'index_rows': int(rows), 'active': int(len(active)), 'sample': len(pick)}

    a = Onnx(data / 'derived' / 'models' / 'bge-small-en-v1.5')
    va, rate_a = timed(a.embed, texts)
    qa = a.embed([PREFIX + q for q in QUESTIONS])
    t = time.time(); a.embed([PREFIX + QUESTIONS[0]]); qa_ms = (time.time() - t) * 1000
    res['A_onnx'] = {'passages_per_s': round(rate_a, 1), 'question_ms': round(qa_ms, 1),
                     'cos_vs_stored': summary((va * stored).sum(1))}

    def top10(qv):
        s = act @ qv
        return [int(active[i]) for i in np.argsort(-s)[:10]]

    for name, cpu in (('B_runner_gpu', False), ('B_runner_cpu', True)):
        t = time.time(); r = Runner(exe, gguf, cpu); start_s = time.time() - t
        vb, rate_b = timed(r.embed, texts)
        qb = r.embed([PREFIX + q for q in QUESTIONS])
        t = time.time(); r.embed([PREFIX + QUESTIONS[0]]); qb_ms = (time.time() - t) * 1000
        r.close()
        per_q = []
        for q, x, y in zip(QUESTIONS, qa, qb):
            ta, tb = top10(x), top10(y)
            per_q.append({'q': q, 'cos_A_B': round(float(x @ y), 5), 'same_best': ta[0] == tb[0], 'shared_of_10': len(set(ta) & set(tb))})
        res[name] = {'start_s': round(start_s, 2), 'passages_per_s': round(rate_b, 1), 'question_ms': round(qb_ms, 1),
                     'cos_vs_stored': summary((vb * stored).sum(1)), 'cos_vs_A_passages': summary((vb * va).sum(1)),
                     'questions_same_best': sum(p['same_best'] for p in per_q), 'questions': len(per_q),
                     'questions_shared_of_10_mean': round(sum(p['shared_of_10'] for p in per_q) / len(per_q), 2),
                     'questions_cos_min': min(p['cos_A_B'] for p in per_q), 'per_question': per_q,
                     'ready_event': r.ready}
        print(name, json.dumps({k: v for k, v in res[name].items() if k not in ('per_question', 'ready_event')}), flush=True)
    print('A_onnx', json.dumps(res['A_onnx']), flush=True)
    json.dump(res, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def summary(c):
    c = np.asarray(c)
    return {'min': round(float(c.min()), 5), 'p1': round(float(np.percentile(c, 1)), 5), 'median': round(float(np.median(c)), 5),
            'below_0.999': int((c < 0.999).sum())}


if __name__ == '__main__':
    main()
