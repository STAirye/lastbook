from collections import Counter
from common import HERE, read_jsonl, words_flag
EX = read_jsonl(HERE / 'examples.jsonl')
c = Counter(); n = Counter()
for r in EX:
    f = words_flag(r['text']); n[r['label']] += 1; c[r['label']] += f
    if r['label'] == 'red' and not f: print('MISS', r['text'])
print({k: f"{c[k]}/{n[k]}" for k in n})
gc = Counter(r['cat'] for r in EX if r['label']=='green' and words_flag(r['text']))
print(gc)
