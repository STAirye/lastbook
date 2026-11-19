"""fork: whether a build bundles the meaning check's files (engine/meaning_red.py, docs/FORK.md 3m).

  python -I -B packaging/meaning_red_files.py        prints the folder to bundle, or nothing

derived/models/meaning-red/ (made by tools/meaning_red_model.py, or downloaded) is bundled when it holds every file of
engine/data/meaning_red_manifest.json with its size and SHA-256. Missing: the app is built without it, and says so here;
setup can still download them with the local AI model. Present but different: the build stops."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'derived' / 'models' / 'meaning-red'
MANIFEST = ROOT / 'engine' / 'data' / 'meaning_red_manifest.json'


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    files = json.loads(MANIFEST.read_text(encoding='utf-8'))['files']
    if not files or not all((FOLDER / f['name']).is_file() for f in files):
        print(f'meaning check: no files in {FOLDER}; the app is built without them (tools/meaning_red_model.py makes them)', file=sys.stderr)
        return 0
    bad = [f['name'] for f in files if (FOLDER / f['name']).stat().st_size != f['size'] or sha256_of(FOLDER / f['name']) != f['sha256']]
    if bad:
        print(f'meaning check: {", ".join(bad)} in {FOLDER} do not match {MANIFEST.name}', file=sys.stderr)
        return 1
    print(FOLDER)
    return 0


if __name__ == '__main__':
    sys.exit(main())
