#!/usr/bin/env python3
"""Paired benchmark of guide-search changes (#333): several arms side by side, scored against frozen answers.

    python3 -B tools/guide_search_bench/bench.py [--remote origin] [--dev] [--units] [--out FILE] NAME=ARM ...

An ARM is BASE[+N+N...][@WORDS]:
  BASE     a git ref of this repository (origin/main, a branch, a commit)
  +N       upstream pull request N, fetched from --remote as pull/N/head and merged onto BASE in a temporary
           worktree (merges must be clean). Fetched heads are kept as refs/guide-search-bench/pr-N
  @WORDS   a words.js file to use instead of the arm's own web/words.js (a path, relative to the current folder)
The first arm is the baseline the controls are compared with (normally plain main).

Sets, all public and in this folder:
  primary     #430's 17 false matches (right answers from #430 where it has them, reference.json's own otherwise)
  secondary   the other #333 and #432 searches; exploratory
  held-out    heldout.json: 67 short-word traps and 59 useful prefix searches, written before any arm ran
  controls    every search in app/tests/test_topic_search*.py of every arm, plus #430's KEEP rows (read from
              pull/430/head at run time); outcome = the same first result as the baseline arm
reference.json and heldout.json are checked against FROZEN.sha256 before anything runs.

--dev      leave the held-out set out (for tuning; the held-out set is meant to be run once, on a fixed rule)
--units    also run the topic-search tests (with #430's) in each arm: the baseline arm's suite on every arm, and
           the arm's own suite where it merges pull requests; lists every failing search by name
--out      write every row and table as JSON

Statistics: exact two-sided McNemar on the discordant pairs, and the clustered McNemar of Durkalski, Palesch,
Lipsitz and Rust (2003, Stat Med 22:2417-2428), clustered by the short word a row is about, with its exact
sign-flip p. Needs git, node and Python 3.9+; no data folder, no network beyond the git fetches.
"""
import hashlib, io, json, math, re, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNNER = 'app/tests/topic_search_emergency.mjs'
SUITES = ['app.tests.test_topic_search', 'app.tests.test_topic_search_emergency', 'app.tests.test_topic_search_prefix']


def git(*a, binary=False, cwd=ROOT):
    r = subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                       **({} if binary else {'text': True, 'encoding': 'utf-8'}))
    if r.returncode:
        err = r.stderr.decode('utf-8', 'replace') if binary else r.stderr
        sys.exit(f'git {" ".join(a)} failed: {err}')
    return r.stdout


def pr_ref(remote, n):
    git('fetch', '-q', remote, f'+pull/{n}/head:refs/guide-search-bench/pr-{n}')
    return f'refs/guide-search-bench/pr-{n}'


def extract(ref, paths, into):
    with tarfile.open(fileobj=io.BytesIO(git('archive', '--format=tar', ref, *paths, binary=True))) as t:
        if sys.version_info >= (3, 12):
            t.extractall(into, filter='data')
        else:
            t.extractall(into)


class Arm:
    """One arm, built into a folder: its guides, web/, app/tests (its own suite) and the words.js it runs."""

    def __init__(self, name, spec, remote, tmp):
        self.name, self.spec = name, spec
        base, _, words = spec.partition('@')
        base, *prs = base.split('+')
        self.dir = Path(tmp) / name
        ref = base
        if prs:
            wt = Path(tmp) / f'{name}-merge'
            git('worktree', 'add', '-q', '--detach', str(wt), base)
            try:
                for n in prs:
                    r = subprocess.run(['git', '-C', str(wt), '-c', 'user.name=bench', '-c', 'user.email=bench@localhost',
                                        'merge', '-q', '--no-edit', pr_ref(remote, n)], capture_output=True, text=True, encoding='utf-8')
                    if r.returncode:
                        sys.exit(f'arm {name}: #{n} does not merge cleanly onto {base}:\n{r.stdout}{r.stderr}')
                ref = git('rev-parse', 'HEAD', cwd=wt).strip()
            finally:
                git('worktree', 'remove', '--force', str(wt))
        self.sha = git('rev-parse', '--short', ref).strip()
        extract(ref, ['content/topics', 'web', 'app/tests'], self.dir)
        if words:
            (self.dir / 'web' / 'words.js').write_bytes(Path(words).read_bytes())
        self.words = Path(words).name if words else None
        self.topics = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((self.dir / 'content' / 'topics').glob('*.json'))]
        self.stop = re.search(r"const QSTOP = new Set\('([^']*)'\.split", (self.dir / 'web' / 'app.js').read_text(encoding='utf-8')).group(1).split(' ')

    def label(self):
        return f'{self.spec} ({self.sha}{", words=" + self.words if self.words else ""})'

    def first(self, queries):
        """First result of each search, as 'guide/choice' ('guide/' with no choice, 'NONE' with no guide)."""
        cases = self.dir / 'cases.json'
        cases.write_text(json.dumps({'stop': self.stop, 'topics': self.topics, 'questions': queries}, ensure_ascii=False), encoding='utf-8')
        p = subprocess.run([shutil.which('node') or sys.exit('needs node on PATH'), str(self.dir / RUNNER),
                            str(self.dir / 'web' / 'words.js'), str(cases)], capture_output=True, text=True, encoding='utf-8', timeout=300)
        if p.returncode:
            sys.exit(p.stderr[-1500:])
        return ['NONE' if not r else f'{r[0][0]}/{r[0][1] or ""}' for r in json.loads(p.stdout)]


def load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def frozen():
    for line in (HERE / 'FROZEN.sha256').read_text(encoding='utf-8').splitlines():
        sha, name = line.split(' *')
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != sha:
            sys.exit(f'{name} does not match FROZEN.sha256: the frozen answers were changed')


def controls(arms, prefix_file):
    """Every search the topic-search tests of every arm run, with the first suite that has it, and #430's KEEP."""
    out = {}
    for a in arms:
        t = load(f'tts_{a.name}', a.dir / 'app' / 'tests' / 'test_topic_search.py')
        e = load(f'tte_{a.name}', a.dir / 'app' / 'tests' / 'test_topic_search_emergency.py')
        for q in [*t.ENGLISH, *t.TOPS]:
            out.setdefault(q, f'test_topic_search ({a.name})')
        for q in e.CASES['questions']:
            out.setdefault(q, f'test_topic_search_emergency ({a.name})')
    for q, _, _ in load('ttp', prefix_file).KEEP:
        out[q] = '#430 KEEP'
    return out


# Statistics (the same formulas as the library search's tools/search_eval/stats.py)
def mcnemar_p(b, c):
    """Exact two-sided McNemar: binomial(b + c, 1/2), probability of a split at least this uneven."""
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def sign_flip_p(d):
    """Exact two-sided p for sum(d) when each cluster's difference is equally likely to be + or -."""
    mags, obs, dist = [abs(x) for x in d if x], abs(sum(d)), {0: 1}
    for m in mags:
        nxt = {}
        for s, c in dist.items():
            nxt[s + m] = nxt.get(s + m, 0) + c
            nxt[s - m] = nxt.get(s - m, 0) + c
        dist = nxt
    return min(1.0, sum(c for s, c in dist.items() if abs(s) >= obs) / 2 ** len(mags))


def durkalski(d):
    """Clustered McNemar: d[i] = (wrong -> right) - (right -> wrong) in cluster i; chi2 = (sum d)^2 / sum d^2.
    Returns (chi2, exact sign-flip p, clusters with d != 0)."""
    s, ss = sum(d), sum(x * x for x in d)
    return (0.0, 1.0, 0) if ss == 0 else (s * s / ss, sign_flip_p(d), sum(1 for x in d if x))


def table(rows, a, b):
    """2x2 of arm a against arm b on rows (q, short, right answers, {arm: first}), row and clustered McNemar."""
    n, d, moved = {(x, y): 0 for x in (1, 0) for y in (1, 0)}, {}, []
    for q, short, right, got in rows:
        ra, rb = got[a] in right, got[b] in right
        n[(ra, rb)] += 1
        d[short] = d.get(short, 0) + (rb and not ra) - (ra and not rb)
        if ra != rb:
            moved.append([q, 'gained' if rb else 'lost', got[a], got[b]])
    chi, p_cl, disc = durkalski(list(d.values()))
    return {'a': a, 'b': b, 'n': len(rows), 'both': n[(1, 1)], 'a_only': n[(1, 0)], 'b_only': n[(0, 1)],
            'neither': n[(0, 0)], 'mcnemar_p': mcnemar_p(n[(1, 0)], n[(0, 1)]), 'clusters': len(d),
            'clusters_moved': disc, 'durkalski_chi2': chi, 'durkalski_p_exact': p_cl, 'moved': moved}


def units(arm, suite_dir, label, prefix_file, tmp):
    """Run SUITES (test files from suite_dir) on an arm's guides and words.js; failing searches by name."""
    d = Path(tmp) / f'units-{arm.name}-{label}'
    shutil.copytree(arm.dir, d)
    for f in (d / 'app' / 'tests').glob('test_topic_search*.py'):
        f.unlink()
    for f in suite_dir.glob('test_topic_search*.py'):
        shutil.copy(f, d / 'app' / 'tests' / f.name)
    shutil.copy(prefix_file, d / 'app' / 'tests' / 'test_topic_search_prefix.py')
    t = subprocess.run([sys.executable, '-B', '-m', 'unittest', *SUITES], cwd=d, capture_output=True, text=True, encoding='utf-8')
    named = {f'{m[0]}: {m[1]}' for m in re.findall(r"^FAIL: (\w+) \(.*?\) \(\w+=('(?:[^'\\]|\\.)*'|\"[^\"]*\")", t.stderr, re.M)}
    unnamed = {f'{m}: (no search named)' for m in re.findall(r"^(?:FAIL|ERROR): (\w+) \([^)]*\)$", t.stderr, re.M)}
    return t.stderr.strip().splitlines()[-1], sorted(named | unnamed)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]

    def opt(name, default=None):
        if name in a:
            i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
        return default

    def flag(name):
        if name in a:
            a.remove(name); return True
        return False
    remote, outfile, dev, run_units = opt('--remote', 'origin'), opt('--out'), flag('--dev'), flag('--units')
    if not a or any('=' not in x for x in a):
        sys.exit(__doc__)
    frozen()
    ref = json.loads((HERE / 'reference.json').read_text(encoding='utf-8'))
    held = json.loads((HERE / 'heldout.json').read_text(encoding='utf-8'))
    sets = {'primary': ref['primary'], 'secondary': ref['secondary']}
    if not dev:
        sets.update({'held-out trap': held['trap'], 'held-out keep': held['keep']})
    with tempfile.TemporaryDirectory() as tmp:
        arms = [Arm(n, s, remote, tmp) for n, s in (x.split('=', 1) for x in a)]
        # #430's file, read from its pull request head, placed where it finds the baseline arm's guides
        prefix_file = arms[0].dir / 'app' / 'tests' / 'test_topic_search_prefix.py'
        prefix_file.write_text(git('show', f'{pr_ref(remote, 430)}:app/tests/test_topic_search_prefix.py'), encoding='utf-8')
        ctrl = controls(arms, prefix_file)
        queries = list(dict.fromkeys([r['q'] for rows in sets.values() for r in rows] + list(ctrl)))
        got = {q: {} for q in queries}
        for arm in arms:
            for q, f in zip(queries, arm.first(queries)):
                got[q][arm.name] = f
        names, base = [x.name for x in arms], arms[0].name
        res = {'arms': {x.name: x.label() for x in arms}, 'sets': {}, 'controls': {}}
        for sname, rows in sets.items():
            rr = [(r['q'], r['short'], set(r['right']), got[r['q']]) for r in rows]
            res['sets'][sname] = {
                'n': len(rr), 'right': {n: sum(g[n] in right for _, _, right, g in rr) for n in names},
                'rows': [{'q': q, 'short': s, 'right': sorted(right), **g} for q, s, right, g in rr],
                'pairs': [table(rr, x, y) for i, x in enumerate(names) for y in names[i + 1:]]}
        for n in names[1:]:
            res['controls'][n] = {'n': len(ctrl), 'changed': [[q, src, got[q][base], got[q][n]] for q, src in ctrl.items()
                                                              if got[q][base] != got[q][n]]}
        if run_units:
            res['units'] = {}
            main_suite = arms[0].dir / 'app' / 'tests'
            for arm in arms:
                for label, suite in (('baseline', main_suite), ('own', arm.dir / 'app' / 'tests')):
                    if label == 'own' and '+' not in arm.spec:      # same tests as the baseline's
                        continue
                    line, fails = units(arm, suite, label, prefix_file, tmp)
                    res['units'][f'{arm.name}, {label} suite'] = {'result': line, 'failing': fails}
    if outfile:
        Path(outfile).write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for n, label in res['arms'].items():
        print(f'{n} = {label}')
    for sname, s in res['sets'].items():
        print(f"\n== {sname} (n={s['n']}): right first result " + ', '.join(f"{n} {s['right'][n]}" for n in names))
        for t in s['pairs']:
            print(f"  {t['a']} vs {t['b']}: both {t['both']}, {t['a']} only {t['a_only']}, {t['b']} only {t['b_only']}, "
                  f"neither {t['neither']} | McNemar exact p={t['mcnemar_p']:.4g} | clustered by short word: "
                  f"{t['clusters_moved']}/{t['clusters']} moved, chi2={t['durkalski_chi2']:.2f}, exact p={t['durkalski_p_exact']:.4g}")
            for q, how, x, y in t['moved']:
                print(f'      {how:6} {q!r}: {x} -> {y}')
    for n, c in res['controls'].items():
        print(f"\n== controls: {n} vs {base}: {len(c['changed'])} of {c['n']} searches change their first result")
    for k, u in res.get('units', {}).items():
        print(f"\n== tests, arm {k}: {u['result']}")
        for f in u['failing']:
            print('    ', f)


if __name__ == '__main__':
    main()
