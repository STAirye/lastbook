import numpy as np, sqlite3, json, subprocess
ref=np.load('v_ortcpu.npy')
for n in ['ortcuda','runvk','runcpu']:
    v=np.load(f'v_{n}.npy'); c=(v*ref).sum(1)
    print(n,'min %.6f p1 %.6f median %.6f mean %.6f'%(c.min(),np.percentile(c,1),np.median(c),c.mean()),'<0.999:',int((c<0.999).sum()),'<0.99:',int((c<0.99).sum()))
a=np.load('v_runvk.npy'); b=np.load('v_runcpu.npy'); print('vk vs runcpu min %.6f'%(a*b).sum(1).min())
# neighbour agreement: for 300 queries (rows) among the 3000, top-10 overlap using ref vs runvk
S_ref=ref@ref.T; S_vk=a@a.T
np.fill_diagonal(S_ref,-1); np.fill_diagonal(S_vk,-1)
t_ref=np.argsort(-S_ref,1)[:,:10]; t_vk=np.argsort(-S_vk,1)[:,:10]
print('top10 overlap within sample %.4f'%np.mean([len(set(x)&set(y))/10 for x,y in zip(t_ref,t_vk)]), 'top1 same %.4f'%np.mean(t_ref[:,0]==t_vk[:,0]))
# tokenizer: token counts
import sys; sys.path.insert(0,r'D:\git\lastbook-pr\gpu-builder')
from tokenizers import Tokenizer
tok=Tokenizer.from_file(r'D:\LastbookData-main-index\derived\models\bge-small-en-v1.5\tokenizer.json'); tok.enable_truncation(max_length=320)
ids=np.load('ids.npy')[:400]
cn=sqlite3.connect('file:D:/LastbookData-main-index/derived/index/semantic.sqlite?mode=ro&immutable=1',uri=True)
T=[cn.execute('select text from chunk where id=?',(int(i),)).fetchone()[0] for i in ids]
hf=[len(e.ids) for e in tok.encode_batch(T)]
p=subprocess.Popen(['D:/git/lastbook/derived/llm/bin-win/lastbook-llm.exe','--model','D:/git/lastbook/derived/models/meaning-red/bge-small-en-v1.5-q8_0.gguf','--embed','--cpu-only','--threads','2'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8')
def rd():
    while True:
        l=p.stdout.readline()
        if l.startswith('{'):
            d=json.loads(l)
            if d['ev'] in('ready','embedding','error'): return d
rd(); nt=[]
for i in range(0,400,64):
    p.stdin.write(json.dumps({'op':'embed','id':i,'texts':T[i:i+64],'max_tokens':320})+'\n'); p.stdin.flush(); nt+=rd()['n_tokens']
p.stdin.write('{"op":"quit"}\n'); p.stdin.flush()
d=np.array(nt)-np.array(hf); print('token count differs on',int((d!=0).sum()),'of 400; max abs',int(abs(d).max()),'; truncated(320) HF:',sum(h==320 for h in hf))
