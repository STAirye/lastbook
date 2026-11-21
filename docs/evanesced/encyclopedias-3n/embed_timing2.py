import sys, time, statistics as st
sys.path.insert(0, r'D:\git\lastbook')
from engine import meaning_red as M
from pathlib import Path
folder, _ = M.find()
text = ('The casualty should be kept warm and still while help is called. Check breathing and pulse often. ' * 40)
for threads in (2, 4):
    m = M.Model(folder, threads=threads); m.embed(['warm'])
    for chars in (600, 1000, 2000):
        for n in (6, 12):
            ms = []
            for _ in range(5):
                t = time.perf_counter(); m.embed(['question'] + [text[i:i + chars] for i in range(n)]); ms.append((time.perf_counter() - t) * 1000)
            print(f'threads {threads} chars {chars} n {n}: {round(st.median(ms))} ms', flush=True)
    m.close()
