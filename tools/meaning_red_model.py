r"""fork: builds the meaning check's two files (engine/meaning_red.py, docs/FORK.md 3m) from the fp32 bge-small-en-v1.5 (a
Hugging Face folder) and prints their sizes and SHA-256.

  set LASTBOOK_DATA=D:\LastbookData-fork-test      (its library's words are what typos.correct uses on the examples)
  python -X utf8 tools/meaning_red_model.py [--src DIR] [--llama-cpp DIR] [--runner EXE] [--out DIR] [--write-manifest]
                                            [--cv] [--compare NPZ]

  --src             the Hugging Face model folder (model.safetensors, config.json, tokenizer.json, 1_Pooling/).
                    Default DATA/derived/models/bge-small-en-v1.5-hf
  --llama-cpp       a llama.cpp checkout at the tag the runner is built from (packaging/llm/build_llm_windows.sh: b12032,
                    dde879bc), for its convert_hf_to_gguf.py and gguf-py. Default $LASTBOOK_LLAMA_CPP, else
                    D:\buildtools\lastbook-llm\work\llama.cpp
  --runner          the local AI program, with --embed (packaging/llm/lastbook_llm.cpp). Default: the app's own, as found
                    by llm_local.runner_path
  --out             default derived/models/meaning-red in this checkout (git-ignored); the builds bundle that folder
  --write-manifest  put the files' sizes and SHA-256 in engine/data/meaning_red_manifest.json (the repo, revision unchanged)
  --cv              also recompute the thresholds out of fold, as the prototype did (5-fold x 3, stratified by category; needs
                    scikit-learn), and print them beside the fixed ones. The fixed ones are kept either way.
  --compare NPZ     print how far the centroids are from another centroid file (the prototype's model_gguf.npz)

bge-small-en-v1.5-q8_0.gguf: convert_hf_to_gguf.py --outtype q8_0 (the converter quantizes to q8_0 itself; no llama-quantize
program is needed), about 37 MB, [CLS] pooling read from 1_Pooling. centroids.npz: the examples after typos.correct, embedded with
that exact file through the runner (no query prefix, 64 to a request), one unit mean per category: red (20) and non-red (yellow and
10 look-alike green categories), float32, with the thresholds. Written with fixed zip times, so the same inputs give the same bytes.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import engine.paths as lastbook_paths  # noqa: E402
from engine import meaning_red, typos  # noqa: E402

EXAMPLES = ROOT / 'engine' / 'data' / 'meaning_red_examples.jsonl'
# The GGUF prototype's thresholds (.claude/drafts/meaning/model_gguf.npz): the out-of-fold score above which 5% (strict) /
# 10% (wide) of the green examples fall. Set on the examples only; the app uses wide.
THRESHOLDS = {'strict': 0.03168658415476481, 'wide': 0.00836634635925293}
LLAMA_CPP = r'D:\buildtools\lastbook-llm\work\llama.cpp'


def read_examples():
    with open(EXAMPLES, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def convert(src, llama_cpp, out):
    """Hugging Face folder to a q8_0 GGUF with the pinned llama.cpp's own converter."""
    script = Path(llama_cpp) / 'convert_hf_to_gguf.py'
    if not script.is_file():
        raise SystemExit(f'no convert_hf_to_gguf.py in {llama_cpp}: give --llama-cpp a checkout of the runner\'s llama.cpp tag')
    env = dict(os.environ, PYTHONPATH=str(Path(llama_cpp) / 'gguf-py'), PYTHONUTF8='1')
    r = subprocess.run([sys.executable, '-X', 'utf8', str(script), str(src), '--outfile', str(out), '--outtype', 'q8_0'],
                       capture_output=True, text=True, encoding='utf-8', env=env)
    if r.returncode or not out.is_file():
        raise SystemExit(f'convert_hf_to_gguf.py failed ({r.returncode}):\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}')


def embed_all(emb, texts):
    return np.array([v for i in range(0, len(texts), 64) for v in emb.embed(texts[i:i + 64])], dtype=np.float32)


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
    ap.add_argument('--src', default=str(lastbook_paths.DATA / 'derived' / 'models' / 'bge-small-en-v1.5-hf'))
    ap.add_argument('--llama-cpp', default=os.environ.get('LASTBOOK_LLAMA_CPP', LLAMA_CPP))
    ap.add_argument('--runner')
    ap.add_argument('--out', default=str(ROOT / meaning_red.SUBDIR))
    ap.add_argument('--write-manifest', action='store_true')
    ap.add_argument('--cv', action='store_true')
    ap.add_argument('--compare')
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    exe = Path(a.runner) if a.runner else meaning_red.runner()
    if exe is None or not exe.is_file():
        raise SystemExit('no local AI program (lastbook-llm) to embed with: build it (packaging/llm/build_llm_*.sh) or give --runner')

    gguf = out / meaning_red.GGUF
    convert(src, a.llama_cpp, gguf)

    ex = read_examples()
    lab = np.array([r['label'] for r in ex])
    cat = np.array([r['cat'] for r in ex])
    texts = [typos.correct(r['text']) or r['text'] for r in ex]
    emb = meaning_red.Embedder(exe, gguf)          # the exact file just written
    try:
        X = embed_all(emb, texts)
    finally:
        emb.close()
    (R, red_names), (N, non_names) = centroids(X, lab, cat)
    save_npz(out / meaning_red.CENTROIDS, {
        'red': R.astype(np.float32), 'nonred': N.astype(np.float32),
        'red_categories': np.array(red_names), 'nonred_categories': np.array(non_names),
        'strict': np.float64(THRESHOLDS['strict']), 'wide': np.float64(THRESHOLDS['wide'])})
    print(f'{len(ex)} examples, {len(red_names)} red and {len(non_names)} non-red centroids; thresholds {THRESHOLDS}')

    s = score(X, R, N)
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
    for name in (meaning_red.GGUF, meaning_red.CENTROIDS):
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
