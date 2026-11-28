"""DirectML (onnxruntime-directml, ./ortdml) on the same 3,000 passages as vk.py, against the onnxruntime CPU vectors.

    set LASTBOOK_DATA=D:\\LastbookData-main-index
    python -B dml.py [batch]
"""
import os, sys, sqlite3, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
B = int(sys.argv[1]) if len(sys.argv) > 1 else 48
sys.path.insert(0, os.path.join(HERE, 'ortdml'))
sys.path.insert(1, r'D:\git\lastbook-pr\gpu-builder')
os.environ['LASTBOOK_EMBED_DEVICE'] = 'cpu'
import retrieval  # noqa: E402

ort = retrieval.ort
print('onnxruntime', ort.__version__, ort.__file__, ort.get_available_providers(), flush=True)
ids = np.load(os.path.join(HERE, 'ids.npy'))
c = sqlite3.connect('file:D:/LastbookData-main-index/derived/index/semantic.sqlite?mode=ro&immutable=1', uri=True)
T = [c.execute('select text from chunk where id=?', (int(i),)).fetchone()[0] for i in ids]

e = retrieval.Embedder()  # CPU session, then the session is replaced with a DirectML one
so = ort.SessionOptions()
so.enable_mem_pattern = False  # required by the DirectML provider
so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
e.sess = ort.InferenceSession(str(retrieval.MODEL / 'model.onnx'), so, providers=['DmlExecutionProvider', 'CPUExecutionProvider'])
print('providers', e.sess.get_providers(), flush=True)
t0 = time.time(); e.embed(T[:B]); print(f'first batch {time.time() - t0:.1f}s', flush=True)
t0 = time.time()
v = np.vstack([e.embed(T[i:i + B]) for i in range(0, len(T), B)])
dt = time.time() - t0
print(f'dml batch {B}: {len(T) / dt:.1f} passages/s ({dt:.1f}s)', flush=True)
np.save(os.path.join(HERE, f'v_dml{B}.npy'), v)

ref = np.load(os.path.join(HERE, 'v_ortcpu.npy'))
cos = (v * ref).sum(1)
print('cosine vs ortcpu: min %.6f p1 %.6f median %.6f' % (cos.min(), np.percentile(cos, 1), np.median(cos)),
      '<0.999:', int((cos < 0.999).sum()), 'max abs diff %.6f' % np.abs(v - ref).max())
S_ref, S_v = ref @ ref.T, v @ v.T
np.fill_diagonal(S_ref, -1); np.fill_diagonal(S_v, -1)
a, b = np.argsort(-S_ref, 1)[:, :10], np.argsort(-S_v, 1)[:, :10]
print('top10 overlap %.4f top1 same %.4f' % (np.mean([len(set(x) & set(y)) / 10 for x, y in zip(a, b)]), np.mean(a[:, 0] == b[:, 0])))
