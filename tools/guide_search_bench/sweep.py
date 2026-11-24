#!/usr/bin/env python3
"""The variant sweep that chose the rule's weights, on the development sets only (never the held-out set).

    python3 -B tools/guide_search_bench/sweep.py [--remote origin] [--base origin/main]

Each variant is this branch's web/words.js with other constants (PART: a start-of-word match for the last word of
the search; PART_ANY: for the other words; ENDINGS on or off; STEMS; JOIN), run through bench.py --dev --units
against the base. Prints, per variant, the right first results on the primary and secondary sets and the searches
that fail a test. The variant in web/words.js (every word 0.5) was picked from this table before the held-out run.
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORDS = HERE.parents[1] / 'web' / 'words.js'
VARIANTS = {   # name: (PART, PART_ANY, STEMS, JOIN, ENDINGS)
    'last word only, 0.5 (C1)': ('0.5', '0', 'false', 'true', True),
    'others 0.25, last 0.5': ('0.5', '0.25', 'false', 'true', True),
    'last word only, 0.75': ('0.75', '0', 'false', 'true', True),
    'last word only, 1': ('1', '0', 'false', 'true', True),
    'C1 without endings': ('0.5', '0', 'false', 'true', False),
    'C1 with stems': ('0.5', '0', 'true', 'true', True),
    'C1 without joining': ('0.5', '0', 'false', 'false', True),
    'every word 0.5 (the rule)': ('0.5', '0.5', 'false', 'true', True),
}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    remote = a[a.index('--remote') + 1] if '--remote' in a else 'origin'
    base = a[a.index('--base') + 1] if '--base' in a else 'origin/main'
    src = WORDS.read_text(encoding='utf-8')
    line = re.search(r'const PART = [^;]*;', src).group(0)
    endings = re.search(r'const ENDINGS = new Set\(\[[^\]]*\]\);', src).group(0)
    with tempfile.TemporaryDirectory() as d:
        for name, (part, any_, stems, join, ends) in VARIANTS.items():
            v = src.replace(line, f'const PART = {part}, PART_ANY = {any_}, STEMS = {stems}, JOIN = {join};')
            if not ends:
                v = v.replace(endings, 'const ENDINGS = new Set();')
            f, out = Path(d) / 'words.js', Path(d) / 'out.json'
            f.write_text(v, encoding='utf-8')
            r = subprocess.run([sys.executable, '-B', str(HERE / 'bench.py'), '--remote', remote, '--dev', '--units',
                                '--out', str(out), f'A={base}', f'C={base}@{f}'], capture_output=True, text=True, encoding='utf-8')
            if r.returncode:
                sys.exit(r.stderr[-2000:])
            res = json.loads(out.read_text(encoding='utf-8'))
            fails = sorted({x.split(': ', 1)[1] for x in res['units']['C, baseline suite']['failing']})
            print(f"{name:28} primary {res['sets']['primary']['right']['C']:2}/17  secondary "
                  f"{res['sets']['secondary']['right']['C']:2}/24  failing searches {len(fails)}: {', '.join(fails)}", flush=True)


if __name__ == '__main__':
    main()
