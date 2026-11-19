#!/usr/bin/env python3
"""Compare an installed library's file list with a new release's: which files would be added, changed, removed or kept.

  python3 tools/compare_packs.py OLD/pack-manifest.tsv NEW/pack-manifest.tsv [--list]
  python3 tools/compare_packs.py --data /path/to/LastbookData NEW/pack-manifest.tsv [--list]

With --data, the installed list is that library's own pack-manifest.tsv. Only the two lists are compared (path, size and
SHA-256 of each file); no file in the library is opened, nothing is downloaded and no port is used. This is a first step
toward upgrades that fetch only what changed (issue #144); setup does not use it yet.
"""
import argparse, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from engine.setup import install  # noqa: E402


def files(n):
    return f'{n} file' if n == 1 else f'{n} files'


def size(n):
    for unit in ('bytes', 'KB', 'MB', 'GB'):
        if n < 1000 or unit == 'GB':
            return f'{n} bytes' if unit == 'bytes' else f'{n:.1f} {unit}'
        n /= 1000


def main(args):
    ap = argparse.ArgumentParser(description="Compare an installed library's pack-manifest.tsv with a new release's.")
    ap.add_argument('--data', help='the installed library, the folder that holds pack-manifest.tsv (instead of OLD)')
    ap.add_argument('--list', action='store_true', help='also list each path, under its heading')
    ap.add_argument('manifests', nargs='+', type=Path, help='OLD and NEW pack-manifest.tsv, or only NEW with --data')
    a = ap.parse_args(args)
    if a.data:
        a.manifests.insert(0, Path(a.data) / 'pack-manifest.tsv')
    if len(a.manifests) != 2:
        ap.error('give the installed and the new pack-manifest.tsv, or --data and the new one')
    try:
        old, new = (install.read_pack_manifest(p) for p in a.manifests)
    except OSError as e:
        sys.exit(f'Cannot read {e.filename}: {e.strerror}.')
    except ValueError as e:
        sys.exit(f'Cannot use this list: {e}.')
    d = install.compare_pack_manifests(old, new)
    for k, what in (('added', 'new in this release'), ('changed', 'differ in size or SHA-256'),
                    ('unchanged', 'already here, kept as they are'), ('removed', 'no longer in the release')):
        print(f'{k:<10} {files(len(d[k])):>12}  {size(d["bytes"][k]):>12}  {what}')
    if d['unsafe']:
        print(f'{"unsafe":<10} {files(len(d["unsafe"])):>12}  {"":>12}  paths outside the library, never used')
    print(f'\nTo fetch: {size(d["fetch_bytes"])} (added and changed). Already here: {size(d["reuse_bytes"])}.')
    if a.list:
        for k in ('added', 'changed', 'removed', 'unsafe', 'unchanged'):
            if d[k]:
                print(f'\n{k}:')
                for rel in d[k]:
                    print('  ' + rel)


if __name__ == '__main__':
    sys.stdout.reconfigure(errors='backslashreplace')     # a console or file that cannot show a path's letters must not stop the list
    main(sys.argv[1:])
