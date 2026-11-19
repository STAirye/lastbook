r"""fork: builds the meaning check's three files (engine/meaning_red.py, docs/FORK.md 3m) from the fp32 bge-small-en-v1.5 that
hybrid search uses, and prints their sizes and SHA-256.

  set LASTBOOK_DATA=D:\LastbookData-fork-test      (its library's words are what typos.correct uses on the examples)
  python -X utf8 tools/meaning_red_model.py [--src DIR] [--out DIR] [--write-manifest] [--cv] [--compare NPZ]

  --src             the fp32 model folder (model.onnx, tokenizer.json). Default DATA/derived/models/bge-small-en-v1.5
  --out             default derived/models/meaning-red in this checkout (git-ignored); the builds bundle that folder
  --write-manifest  put the files' sizes and SHA-256 in engine/data/meaning_red_manifest.json (the repo, revision unchanged)
  --cv              also recompute the thresholds out of fold, as the prototype did (5-fold x 3, stratified by category; needs
                    scikit-learn), and print them beside the fixed ones. The fixed ones are kept either way.
  --compare NPZ     print how far the centroids are from another centroid file (the prototype's model_int8.npz)

model_int8.onnx: onnxruntime.quantization.quantize_dynamic, weights QInt8, nothing else (with onnx 1.23.2 and onnxruntime
1.32.0 the same bytes as the prototype's copy). centroids.npz: the examples after typos.correct, embedded with that exact
file (no query prefix, batches of 64 as retrieval.Embedder), one unit mean per category: red (20) and non-red (yellow and
10 look-alike green categories), float16, with the thresholds. Written with fixed zip times, so the same inputs give the
same bytes.
"""
import argparse
import io
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import engine.paths as lastbook_paths  # noqa: E402
from engine import meaning_red, typos  # noqa: E402

EXAMPLES = ROOT / 'engine' / 'data' / 'meaning_red_examples.jsonl'
# The prototype's thresholds for the int8 model (.claude/drafts/meaning/model_int8.json): the out-of-fold score above which
# 5% (strict) / 10% (wide) of the green examples fall. Set on the examples only; the app uses wide.
THRESHOLDS = {'strict': 0.024351298809051514, 'wide': 0.006628692150115967}


def read_examples():
    with open(EXAMPLES, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def embed_all(model, texts):
    return np.vstack([model.embed(texts[i:i + 64]) for i in range(0, len(texts), 64)])


def centroids(X, lab, cat):
    def cents(mask):
        names = sorted(set(cat[mask]))
        c = np.vstack([X[mask & (cat == k)].mean(0) for k in names])
        return c / np.linalg.norm(c, axis=1, keepdims=True), names
    return cents(lab == 'red'), cents(lab != 'red')


def score(Q, R, N):
    return (Q @ R.T).max(1) - (Q @ N.T).max(1)


def cv_thresholds(X, lab, cat):
    from sklearn.model_selection import StratifiedKFold
    tot = np.zeros(len(X))
    for rep in range(3):
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=rep).split(X, cat):
            (R, _), (N, _) = centroids(X[tr], lab[tr], cat[tr])
            tot[te] += score(X[te], R, N)
    s = tot / 3
    g = np.sort(s[lab == 'green'])[::-1]
    return {k: float(g[int(np.floor(b * len(g)))]) for k, b in (('strict', 0.05), ('wide', 0.10))}


def save_npz(path, arrays):
    """np.savez with fixed zip entry times, so the file's SHA-256 depends only on the arrays."""
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as z:
        for name, a in arrays.items():
            buf = io.BytesIO()
            np.lib.format.write_array(buf, np.asanyarray(a), allow_pickle=False)
            info = zipfile.ZipInfo(name + '.npy', date_time=(1980, 1, 1, 0, 0, 0))
            z.writestr(info, buf.getvalue())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=str(lastbook_paths.DATA / 'derived' / 'models' / 'bge-small-en-v1.5'))
    ap.add_argument('--out', default=str(ROOT / meaning_red.SUBDIR))
    ap.add_argument('--write-manifest', action='store_true')
    ap.add_argument('--cv', action='store_true')
    ap.add_argument('--compare')
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    from onnxruntime.quantization import QuantType, quantize_dynamic
    with tempfile.TemporaryDirectory() as tmp:
        q = Path(tmp) / 'model_int8.onnx'
        quantize_dynamic(str(src / 'model.onnx'), str(q), weight_type=QuantType.QInt8)
        shutil.copyfile(q, out / 'model_int8.onnx')
    shutil.copyfile(src / 'tokenizer.json', out / 'tokenizer.json')

    ex = read_examples()
    lab = np.array([r['label'] for r in ex])
    cat = np.array([r['cat'] for r in ex])
    texts = [typos.correct(r['text']) or r['text'] for r in ex]
    model = meaning_red.Model(out)          # the exact file just written; no centroids yet
    X = embed_all(model, texts)
    (R, red_names), (N, non_names) = centroids(X, lab, cat)
    save_npz(out / 'centroids.npz', {
        'red': R.astype(np.float16), 'nonred': N.astype(np.float16),
        'red_categories': np.array(red_names), 'nonred_categories': np.array(non_names),
        'strict': np.float64(THRESHOLDS['strict']), 'wide': np.float64(THRESHOLDS['wide'])})
    print(f'{len(ex)} examples, {len(red_names)} red and {len(non_names)} non-red centroids; thresholds {THRESHOLDS}')

    s = score(X, R.astype(np.float16).astype(np.float32), N.astype(np.float16).astype(np.float32))
    for l in ('red', 'yellow', 'green'):
        print(f'  in-sample {l}: {int((s[lab == l] > THRESHOLDS["wide"]).sum())}/{int((lab == l).sum())} over wide')
    if a.cv:
        print('  out of fold, recomputed:', cv_thresholds(X, lab, cat), '(fixed:', THRESHOLDS, ')')
    if a.compare:
        with np.load(a.compare) as z:
            for k, mine in (('red', R), ('nonred', N)):
                theirs = z[k].astype(np.float32)
                cos = (mine * theirs).sum(1) / np.linalg.norm(theirs, axis=1)
                print(f'  {k} centroids vs {a.compare}: max |diff| {np.abs(mine - theirs).max():.5f}, min cosine {cos.min():.6f}')

    files = []
    for name in ('model_int8.onnx', 'tokenizer.json', 'centroids.npz'):
        p = out / name
        files.append({'name': name, 'size': p.stat().st_size, 'sha256': meaning_red.sha256_of(p)})
        print(f'{files[-1]["sha256"]}  {files[-1]["size"]:>10}  {p}')
    if a.write_manifest:
        m = meaning_red.manifest()
        m['files'] = files
        with open(meaning_red.MANIFEST, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(m, f, indent=1)
            f.write('\n')
        print('wrote', meaning_red.MANIFEST)


if __name__ == '__main__':
    main()
