import os, sys, sqlite3, time, numpy as np
sys.path.insert(0, r'D:\git\lastbook-pr\eval-pr1-ortgpu') if False else None
sys.path.insert(0, r'D:\git\lastbook\.claude\drafts\prs\eval-pr1-main\ortgpu')
sys.path.insert(1, r'D:\git\lastbook-pr\gpu-builder')
import retrieval  # no preload_dlls here: retrieval.Embedder must do it
print(retrieval.ort.__file__, retrieval.ort.__version__, retrieval.ort.get_available_providers())
N=int(sys.argv[1]) if len(sys.argv)>1 else 500
c=sqlite3.connect('file:D:/LastbookData-main-index/derived/index/semantic.sqlite?mode=ro&immutable=1',uri=True)
T=[t for (t,) in c.execute(f'select text from chunk where active=1 order by id limit {N}')]
def run(gpu):
    e=retrieval.Embedder(gpu=gpu); e.embed(T[:48]); t0=time.time()
    v=np.vstack([e.embed(T[i:i+48]) for i in range(0,N,48)]); dt=time.time()-t0
    print(e.provider, f'{N/dt:.0f} passages/s'); return v
g=run(True); 
os.environ['LASTBOOK_EMBED_DEVICE']='cpu'; c2=run(True)
print('opt-out provider ok')
cos=(g*c2).sum(1); print('min cosine',cos.min(),'max abs diff',np.abs(g-c2).max())
# vs stored index vectors
st=np.fromfile(r'D:\LastbookData-main-index\derived\index\vectors.f16',dtype=np.float16,count=N*384).reshape(N,384).astype(np.float32)
print('cuda vs stored cos min',(g*st).sum(1).min(),'cpu vs stored',(c2*st).sum(1).min())
