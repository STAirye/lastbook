import os, sys, json, sqlite3, time, subprocess, numpy as np
mode=sys.argv[1]; N=int(sys.argv[2]); SC=os.path.dirname(os.path.abspath(__file__))
c=sqlite3.connect('file:D:/LastbookData-main-index/derived/index/semantic.sqlite?mode=ro&immutable=1',uri=True)
tot=c.execute('select count(*) from chunk where active=1').fetchone()[0]
step=tot//N
ids=[r[0] for r in c.execute('select id from chunk where active=1 order by id')][::step][:N]
T=[c.execute('select text from chunk where id=?',(i,)).fetchone()[0] for i in ids]
print('passages',len(T),'of',tot, flush=True)
if mode in('ortcpu','ortcuda'):
    os.environ['LASTBOOK_EMBED_DEVICE']='cpu' if mode=='ortcpu' else ''
    if mode=='ortcuda': sys.path.insert(0, r'D:\git\lastbook\.claude\drafts\prs\eval-pr1-main\ortgpu')
    sys.path.insert(0, r'D:\git\lastbook-pr\gpu-builder')
    import retrieval
    if mode=='ortcuda': retrieval.ort.preload_dlls()
    e=retrieval.Embedder(gpu=True); e.embed(T[:48]); t0=time.time()
    v=np.vstack([e.embed(T[i:i+48]) for i in range(0,len(T),48)]); dt=time.time()-t0
else:
    args=['D:/git/lastbook/derived/llm/bin-win/lastbook-llm.exe','--model','D:/git/lastbook/derived/models/meaning-red/bge-small-en-v1.5-q8_0.gguf','--embed']
    if mode=='runcpu': args+=['--cpu-only','--threads',sys.argv[3] if len(sys.argv)>3 else '8']
    p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8')
    def rd():
        while True:
            l=p.stdout.readline()
            if not l: raise SystemExit('runner ended')
            if l.startswith('{'):
                d=json.loads(l)
                if d['ev'] in('ready','embedding','error'): return d
    r=rd(); print({k:v for k,v in r.items() if k!='vectors'}, flush=True)
    def req(tx,i):
        p.stdin.write(json.dumps({'op':'embed','id':i,'texts':tx,'max_tokens':320})+'\n'); p.stdin.flush(); return rd()
    req(T[:16],0); t0=time.time(); out=[]
    for k,i in enumerate(range(0,len(T),64)):
        d=req(T[i:i+64],k+1)
        assert d['ev']=='embedding',d
        out+=d['vectors']
    dt=time.time()-t0; v=np.array(out,dtype=np.float32)
    p.stdin.write('{"op":"quit"}\n'); p.stdin.flush(); p.wait(30)
print(mode, f'{len(T)/dt:.1f} passages/s ({dt:.1f}s)', flush=True)
np.save(f'{SC}/v_{mode}.npy',v); np.save(f'{SC}/ids.npy',np.array(ids))
