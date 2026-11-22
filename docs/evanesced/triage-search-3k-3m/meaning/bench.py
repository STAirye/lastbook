"""Phase D: cost of the meaning check in a fresh process: import, model load, memory, ms per question (CPU).
Usage: python -X utf8 bench.py [threads] [model.onnx]"""
import json
import os
import sys
import time

t0 = time.perf_counter()
import psutil  # noqa: E402
P = psutil.Process()
rss0 = P.memory_info().rss
import numpy as np  # noqa: E402
sys.path.insert(0, r'D:\git\lastbook')
os.environ['ORT_DISABLE_TELEMETRY'] = '1'
t1 = time.perf_counter()
if os.name == 'nt':
    from engine import quiet_onnx
    quiet_onnx.silence()
import onnxruntime as ort  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402
t2 = time.perf_counter()
rss_import = P.memory_info().rss

MODEL_DIR = r'D:\LastbookData-fork-test\derived\models\bge-small-en-v1.5'
threads = int(sys.argv[1]) if len(sys.argv) > 1 else max(2, (os.cpu_count() or 4) // 2)
onnx_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(MODEL_DIR, 'model.onnx')
so = ort.SessionOptions()
so.intra_op_num_threads = threads
sess = ort.InferenceSession(onnx_path, so, providers=['CPUExecutionProvider'])
tok = Tokenizer.from_file(os.path.join(MODEL_DIR, 'tokenizer.json'))
tok.enable_truncation(max_length=320)
inputs = {i.name for i in sess.get_inputs()}
t3 = time.perf_counter()
rss_load = P.memory_info().rss
here = os.path.dirname(os.path.abspath(__file__))
m = np.load(os.path.join(here, 'model.npz'))
R, N = m['red'].astype(np.float32), m['nonred'].astype(np.float32)
th = json.load(open(os.path.join(here, 'model.json'), encoding='utf-8'))['thresholds']['wide']


def embed1(text):
    e = tok.encode(text)
    ids = np.array([e.ids], dtype=np.int64)
    feed = {'input_ids': ids, 'attention_mask': np.ones_like(ids)}
    if 'token_type_ids' in inputs:
        feed['token_type_ids'] = np.zeros_like(ids)
    v = sess.run(None, feed)[0][0, 0]
    return v / np.linalg.norm(v)


def red(text):
    v = embed1(text)
    return float((R @ v).max() - (N @ v).max()) > th


qs = [json.loads(l)['text'] for l in open(os.path.join(here, '..', 'independent2', 'phrases.jsonl'), encoding='utf-8')]
t4 = time.perf_counter()
red(qs[0])
t5 = time.perf_counter()
times = []
for q in qs[:300]:
    a = time.perf_counter()
    red(q)
    times.append((time.perf_counter() - a) * 1000)
rss_run = P.memory_info().rss
times.sort()
MB = 1 / 2 ** 20
print(json.dumps({
    'model': onnx_path, 'model_MB': round(os.path.getsize(onnx_path) * MB, 1), 'threads': threads,
    'import_numpy_s': round(t1 - t0, 3), 'import_onnxruntime_tokenizers_s': round(t2 - t1, 3),
    'session_and_tokenizer_load_s': round(t3 - t2, 3), 'first_question_ms': round((t5 - t4) * 1000, 1),
    'per_question_ms_median': round(times[len(times) // 2], 2), 'per_question_ms_p95': round(times[int(len(times) * .95)], 2),
    'per_question_ms_max': round(times[-1], 2),
    'rss_MB_start': round(rss0 * MB), 'rss_MB_after_import': round(rss_import * MB), 'rss_MB_after_load': round(rss_load * MB),
    'rss_MB_after_300': round(rss_run * MB), 'example_vectors_bytes': R.nbytes // 2 + N.nbytes // 2,
}, indent=1))
