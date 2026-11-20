r"""fork, dev tool: rewrite a prototype vector index's rows.npz (object arrays, which need pickle to load) as rows.json,
the format engine/wiki_vectors.py reads. Only run on files you built yourself.

    python tools/wiki_vectors_rows.py D:\LastbookData\derived\index
"""
import json, sys
from pathlib import Path

import numpy as np

for p in sorted(Path(sys.argv[1]).glob('vec-*.rows.npz')):
    out = p.with_name(p.name[:-len('.rows.npz')] + '.rows.json')
    z = np.load(p, allow_pickle=True)
    rows = {'paths': [str(x) for x in z['paths']], 'titles': [str(x) for x in z['titles']],
            'art': [int(x) for x in z['art']], 'start': [int(x) for x in z['start']]}
    out.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    print(out.name, len(rows['paths']), 'articles', len(rows['art']), 'sections', round(out.stat().st_size / 2**20, 1), 'MB')
