#!/usr/bin/env python3
"""fork: the meaning check for urgent questions (engine/meaning_red.py, docs/FORK.md 3m), on the app's own llama.cpp runner.

  python -X utf8 -B -m unittest app.tests.test_meaning_red [-v]

Checked: it fires on clear urgent wordings and not on clear everyday ones (with the files built by tools/meaning_red_model.py in
derived/models/meaning-red and a runner with --embed; skipped without them), it only ever adds to the urgent words, it falls
back quietly when a file or the runner is missing or changed or old, when the runner ends (it is started again a few times) or
stops answering, LASTBOOK_MEANING_RED=0, several threads at once, the manifest, and the process that uses it opens no
listening socket, loads no model and no onnxruntime or tokenizers, and leaves no runner behind when it exits. The restart and
old-runner tests use a stand-in program, so they need no model. Never packaged."""
import json, os, re, shutil, subprocess, sys, tempfile, textwrap, threading, time, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT)]

from engine import meaning_red  # noqa: E402


def _have():
    folder = meaning_red.find(check=False)[0]
    exe = meaning_red.runner()
    return folder is not None and exe is not None


HAVE = _have()
URGENT = ['my husband collapsed and is not breathing', 'she swallowed a whole bottle of her pills an hour ago',
          'my baby went floppy and blue']
EVERYDAY = ['how do i bake sourdough bread', 'best way to store potatoes for winter', 'how to fix a squeaky door hinge']


def fresh():
    meaning_red._reset_for_tests()


class Manifest(unittest.TestCase):
    def test_names_sizes_and_hashes(self):
        m = meaning_red.manifest()
        self.assertRegex(m['repo'], r'^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$')
        self.assertEqual([f['name'] for f in m['files']], ['bge-small-en-v1.5-q8_0.gguf', 'centroids.npz'])
        for f in m['files']:
            self.assertRegex(f['sha256'], r'^[0-9a-f]{64}$')
            self.assertGreater(f['size'], 1000)
        self.assertTrue(m['revision'] == '' or re.fullmatch(r'[0-9a-f]{40}', m['revision']), m['revision'])

    def test_nothing_to_download_until_published(self):
        with mock.patch.object(meaning_red, 'manifest', lambda: {'repo': 'a/b', 'revision': '', 'files': []}):
            self.assertIsNone(meaning_red.urls())
        rev = 'a' * 40
        files = [{'name': 'x.gguf', 'size': 5, 'sha256': '0' * 64}]
        with mock.patch.object(meaning_red, 'manifest', lambda: {'repo': 'a/b', 'revision': rev, 'files': files}):
            self.assertEqual(meaning_red.urls(), [('x.gguf', f'https://huggingface.co/a/b/resolve/{rev}/x.gguf', 5, '0' * 64)])

    def test_unpublished_fetch_opens_nothing(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(meaning_red, 'folders', lambda: [Path(d) / 'none']), \
                mock.patch.object(meaning_red, 'urls', lambda: None):
            self.assertEqual(meaning_red.fetch(dest=Path(d) / 'got'), 'unpublished')
            self.assertFalse((Path(d) / 'got').exists())

    def test_the_examples_ship_in_the_repo(self):
        rows = [json.loads(x) for x in (ROOT / 'engine' / 'data' / 'meaning_red_examples.jsonl').read_text(encoding='utf-8').splitlines() if x]
        self.assertEqual(len(rows), 689)
        self.assertEqual(len({r['cat'] for r in rows if r['label'] == 'red'}), 20)
        self.assertEqual(len({r['cat'] for r in rows if r['label'] != 'red'}), 11)

    def test_no_onnxruntime_or_tokenizers_on_this_path(self):
        """Upstream's rule: the desktop loads no model and no onnxruntime. The embedding is the runner's."""
        src = (ROOT / 'engine' / 'meaning_red.py').read_text(encoding='utf-8')
        for line in src.splitlines():
            if re.match(r'\s*(import|from)\s', line):
                self.assertNotRegex(line, r'onnx|tokenizers|quiet_onnx|retrieval', line)


# A stand-in for lastbook-llm --embed: prints what the real one prints, answers every embed with one fixed unit vector.
FAKE = textwrap.dedent('''
    import json, sys, time
    mode = sys.argv[1]
    def out(o):
        sys.stdout.write(json.dumps(o) + "\\n"); sys.stdout.flush()
    if mode == "old":                      # a runner from before --embed: it refuses the option and ends
        out({"ev": "error", "code": "usage", "msg": "unknown option --embed"}); sys.exit(2)
    out({"ev": "ready", "n_ctx": 512, "embed": mode != "old-ready"})   # old-ready: it started, but is not an embedding runner
    die_after = int(mode.split("-")[2]) if mode.startswith("die-after-") else None
    n = 0
    for line in sys.stdin:
        req = json.loads(line)
        if req.get("op") == "quit":
            break
        n += 1
        if mode == "hang" and n > 1:
            time.sleep(60)
        if die_after is not None and n > die_after:
            sys.exit(3)
        out({"ev": "embedding", "id": req["id"], "vectors": [[1.0, 0.0, 0.0, 0.0] for _ in req["texts"]], "n_tokens": [3], "ms": 1})
''')


class Stand:
    """A folder with a stand-in for the runner, and tiny files in place of the GGUF and centroids."""

    def __init__(self, mode):
        import numpy as np
        self.mode = mode
        self.dir = tempfile.TemporaryDirectory()
        d = Path(self.dir.name)
        self.script = d / 'fake_runner.py'
        self.script.write_text(FAKE, encoding='utf-8')
        (d / meaning_red.GGUF).write_bytes(b'not a model')
        np.savez(d / meaning_red.CENTROIDS, red=np.array([[1, 0, 0, 0]], dtype=np.float32), nonred=np.array([[0, 1, 0, 0]], dtype=np.float32),
                 strict=np.float64(0.03), wide=np.float64(0.008))
        self.folder = d
        self.spawned = []
        real = subprocess.Popen

        def popen(argv, **kw):
            self.spawned.append(list(argv))
            return real([sys.executable, '-X', 'utf8', str(self.script), self.mode], **kw)
        self.patches = [mock.patch.object(meaning_red.subprocess, 'Popen', popen),
                        mock.patch.object(meaning_red, 'find', lambda check=True: (self.folder, None)),
                        mock.patch.object(meaning_red, 'runner', lambda: Path(sys.executable))]

    def __enter__(self):
        for p in self.patches:
            p.start()
        return self

    def __exit__(self, *a):
        for p in self.patches:
            p.stop()
        fresh()
        self.dir.cleanup()


class Fallback(unittest.TestCase):
    def setUp(self):
        fresh()

    def tearDown(self):
        fresh()

    def test_missing_files_leave_the_words(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(meaning_red, 'folders', lambda: [Path(d)]):
            self.assertFalse(meaning_red.wait(30))
            st = meaning_red.status()
            self.assertEqual(st['state'], 'off')
            self.assertIn('FileNotFoundError', st['why'])
            self.assertEqual(meaning_red.check('my husband is not breathing'), {'score': None, 'fired': False, 'state': 'off'})

    @unittest.skipUnless(HAVE, 'no meaning-red files or runner: run tools/meaning_red_model.py')
    def test_a_changed_file_is_refused(self):
        src = meaning_red.find(check=False)[0]
        with tempfile.TemporaryDirectory() as d:
            for f in meaning_red.manifest()['files']:
                shutil.copyfile(src / f['name'], Path(d) / f['name'])
            p = Path(d) / 'centroids.npz'
            b = bytearray(p.read_bytes())
            b[-100] ^= 1
            p.write_bytes(bytes(b))
            with mock.patch.object(meaning_red, 'folders', lambda: [Path(d)]):
                folder, why = meaning_red.find()
                self.assertIsNone(folder)
                self.assertIn('centroids.npz', why)
                self.assertFalse(meaning_red.wait(30))

    def test_no_runner_leaves_the_words(self):
        with Stand('good'), mock.patch.object(meaning_red, 'runner', lambda: None):
            self.assertFalse(meaning_red.wait(30))
            st = meaning_red.status()
            self.assertEqual(st['state'], 'off')
            self.assertIn('no local AI program', st['why'])

    def test_an_old_runner_that_refuses_embed_leaves_the_words(self):
        with Stand('old') as s:
            self.assertFalse(meaning_red.wait(30))
            st = meaning_red.status()
            self.assertEqual(st['state'], 'off')
            self.assertIn('usage', st['why'])
            self.assertEqual(len(s.spawned), 1)
            self.assertFalse(meaning_red.check('my husband is not breathing')['fired'])

    def test_an_old_runner_that_does_not_say_embed_leaves_the_words(self):
        with Stand('old-ready'):
            self.assertFalse(meaning_red.wait(30))
            self.assertIn('no --embed', meaning_red.status()['why'])

    def test_what_is_started_is_the_embed_runner_on_the_cpu(self):
        with Stand('good') as s:
            self.assertTrue(meaning_red.wait(30), meaning_red.status())
            argv = s.spawned[0]
            for a in ('--model', '--embed', '--cpu-only', '--threads'):
                self.assertIn(a, argv)
            self.assertTrue(argv[argv.index('--model') + 1].endswith(meaning_red.GGUF))
            self.assertEqual(argv[argv.index('--threads') + 1], str(meaning_red.THREADS))
            self.assertNotIn('--ctx', argv)

    def test_switch(self):
        with mock.patch.dict(os.environ, {'LASTBOOK_MEANING_RED': '0'}), Stand('good') as s:
            meaning_red.start()
            self.assertIsNone(meaning_red._thread)
            self.assertFalse(meaning_red.status()['on'])
            self.assertEqual(meaning_red.check('my husband is not breathing')['state'], 'switched off')
            self.assertEqual(s.spawned, [])

    def test_not_started_never_blocks(self):
        self.assertEqual(meaning_red.check('my husband is not breathing'), {'score': None, 'fired': False, 'state': 'not started'})


class Runner(unittest.TestCase):
    """The process handling, with a stand-in for the runner."""

    def setUp(self):
        fresh()

    def tearDown(self):
        fresh()

    def test_a_working_runner_scores_and_stops(self):
        with Stand('good'):
            self.assertTrue(meaning_red.wait(30), meaning_red.status())
            r = meaning_red.check('my husband is not breathing')
            self.assertEqual(r, {'score': 1.0, 'fired': True, 'state': 'ready'})
            self.assertEqual(meaning_red.check('   ')['score'], None)
            proc = meaning_red._model.emb.proc
            meaning_red.stop()
            self.assertIsNotNone(proc.poll())
            self.assertEqual(meaning_red.check('my husband is not breathing')['fired'], False)
            meaning_red.start()                      # nothing is started again after stop
            self.assertEqual(meaning_red.status()['state'], 'stopped')

    def test_a_runner_that_ends_is_started_again(self):
        with Stand('die-after-3') as s:             # the warm-up and two questions, then it ends on the third
            self.assertTrue(meaning_red.wait(30))
            self.assertTrue(meaning_red.check('a')['fired'])
            self.assertTrue(meaning_red.check('b')['fired'])
            r = meaning_red.check('c')               # this one finds it gone: the words alone, and a new runner starts
            self.assertEqual((r['fired'], r['score']), (False, None))
            self.assertTrue(r['state'].startswith('error'))
            self.assertEqual(meaning_red.status()['restarts'], 1)
            meaning_red._thread.join(30)
            self.assertEqual(len(s.spawned), 2)
            self.assertTrue(meaning_red.check('d')['fired'])     # the new one answers

    def test_restarts_stop_after_a_few(self):
        with Stand('die-after-1') as s:             # the warm-up works, every question after it ends the runner
            self.assertTrue(meaning_red.wait(30))
            for i in range(meaning_red.MAX_RESTARTS + 1):     # each question finds the runner gone; the last finds no restarts left
                meaning_red._thread.join(30)
                self.assertFalse(meaning_red.check(f'q{i}')['fired'])
            st = meaning_red.status()
            self.assertEqual(st['state'], 'off', st)
            self.assertEqual(st['restarts'], meaning_red.MAX_RESTARTS)
            self.assertEqual(len(s.spawned), 1 + meaning_red.MAX_RESTARTS)
            self.assertEqual(meaning_red.check('again'), {'score': None, 'fired': False, 'state': 'off'})
            self.assertEqual(len(s.spawned), 1 + meaning_red.MAX_RESTARTS)      # and no more

    def test_a_runner_that_stops_answering_is_given_up_on(self):
        with Stand('hang') as s, mock.patch.object(meaning_red, 'ASK_WAIT', 0.5):
            self.assertTrue(meaning_red.wait(30))
            proc = meaning_red._model.emb.proc
            t = time.time()
            r = meaning_red.check('my husband is not breathing')
            self.assertLess(time.time() - t, 5)
            self.assertEqual((r['fired'], r['state']), (False, 'error: TimeoutError'))
            time.sleep(0.5)
            self.assertIsNotNone(proc.poll())        # the stuck one was stopped

    def test_threads_with_a_stand_in(self):
        with Stand('good'):
            self.assertTrue(meaning_red.wait(30))
            got, errors = [], []

            def run():
                try:
                    for i in range(20):
                        got.append(meaning_red.check(f'question {i}')['score'])
                except Exception as e:
                    errors.append(e)
            ts = [threading.Thread(target=run) for _ in range(6)]
            for x in ts:
                x.start()
            for x in ts:
                x.join(60)
            self.assertEqual(errors, [])
            self.assertEqual(got, [1.0] * 120)


class OnlyAdds(unittest.TestCase):
    """is_danger = words OR meaning: the meaning check never takes an urgent flag away."""

    @classmethod
    def setUpClass(cls):
        import assistant
        cls.a = assistant

    def test_words_stay_urgent_when_meaning_says_no(self):
        no = lambda t: {'score': -0.5, 'fired': False, 'state': 'ready'}
        with mock.patch.object(meaning_red, 'check', no):
            info = {}
            self.assertTrue(self.a.is_danger('my son isnt breathing', meaning=info))
            self.assertEqual(info, {'score': -0.5, 'fired': False, 'state': 'ready', 'words': True})
            self.assertTrue(self.a.is_danger('Poison'))

    def test_meaning_adds(self):
        yes = lambda t: {'score': 0.05, 'fired': True, 'state': 'ready'}
        q = 'how do i bake sourdough bread'
        self.assertFalse(self.a.is_danger(q))
        with mock.patch.object(meaning_red, 'check', yes):
            info = {}
            self.assertTrue(self.a.is_danger(q, meaning=info))
            self.assertEqual(info['words'], False)

    def test_a_failing_runner_leaves_the_words(self):
        fresh()
        try:
            with Stand('die-after-1'):
                self.assertTrue(meaning_red.wait(30))
                self.assertTrue(self.a.is_danger('my son isnt breathing'))         # the words say so; the runner ends meanwhile
                self.assertFalse(self.a.is_danger('how do i bake sourdough bread'))
        finally:
            fresh()

    def test_turn_info_carries_it(self):
        yes = lambda t: {'score': 0.05, 'fired': True, 'state': 'ready'}
        with mock.patch.object(meaning_red, 'check', yes), mock.patch.object(self.a, 'hybrid', lambda q, k=8, trace=None: []):
            hits, info = self.a.turn_hits([{'role': 'user', 'content': 'how do i bake sourdough bread'}])
        self.assertTrue(info['danger'])
        self.assertEqual(info['meaning'], {'score': 0.05, 'fired': True, 'state': 'ready', 'words': False})


@unittest.skipUnless(HAVE, 'no meaning-red files or runner: run tools/meaning_red_model.py')
class Loaded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fresh()
        assert meaning_red.wait(120), meaning_red.status()

    @classmethod
    def tearDownClass(cls):
        fresh()

    def test_fires_on_clear_urgent_wordings(self):
        for q in URGENT:
            r = meaning_red.check(q)
            self.assertEqual(r['state'], 'ready')
            self.assertTrue(r['fired'], (q, r))

    def test_quiet_on_clear_everyday_ones(self):
        for q in EVERYDAY:
            self.assertFalse(meaning_red.check(q)['fired'], q)

    def test_it_is_a_process_of_its_own(self):
        pid = meaning_red._model.emb.proc.pid
        self.assertNotEqual(pid, os.getpid())
        self.assertIsNone(meaning_red._model.emb.proc.poll())

    def test_threads(self):
        want = {q: meaning_red.check(q)['score'] for q in URGENT + EVERYDAY}
        got, errors = [], []

        def run():
            try:
                for _ in range(5):
                    for q in URGENT + EVERYDAY:
                        got.append((q, meaning_red.check(q)['score']))
            except Exception as e:
                errors.append(e)
        ts = [threading.Thread(target=run) for _ in range(6)]
        for t in ts:
            t.start()
        for t in ts:
            t.join(60)
        self.assertEqual(errors, [])
        self.assertEqual(len(got), 6 * 5 * len(want))
        for q, s in got:
            self.assertAlmostEqual(s, want[q], places=3)

    def test_start_twice_loads_once(self):
        t = meaning_red._thread
        meaning_red.start()
        self.assertIs(meaning_red._thread, t)

    def test_a_real_runner_that_is_killed_is_started_again(self):
        m = meaning_red._model
        m.emb.proc.kill()
        m.emb.proc.wait(10)
        r = meaning_red.check(URGENT[0])
        self.assertFalse(r['fired'])
        meaning_red._thread.join(60)
        self.assertEqual(meaning_red.status()['state'], 'ready', meaning_red.status())
        self.assertTrue(meaning_red.check(URGENT[0])['fired'])


def _pid_alive(pid):
    if os.name == 'nt':
        out = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'], capture_output=True, text=True,
                             encoding='oem', errors='replace').stdout
        return f'"{pid}"' in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@unittest.skipUnless(HAVE, 'no meaning-red files or runner: run tools/meaning_red_model.py')
class WholeProcess(unittest.TestCase):
    def test_loads_no_model_listens_on_nothing_and_leaves_no_runner(self):
        code = r'''
import json, socket, sys
sys.path.insert(0, sys.argv[1])
listens = []
_l = socket.socket.listen
socket.socket.listen = lambda self, *a: (listens.append(1), _l(self, *a))[1]
from engine import meaning_red
ok = meaning_red.wait(120)
r = meaning_red.check('my husband collapsed and is not breathing')
bad = sorted(k for k in sys.modules if k.split('.')[0] in ('onnxruntime', 'tokenizers', 'retrieval', 'onnx'))
print(json.dumps({'ok': ok, 'listens': len(listens), 'modules': bad, 'fired': r['fired'], 'pid': meaning_red._model.emb.proc.pid,
                  'folder': meaning_red.status()['folder']}))
'''
        env = dict(os.environ)
        env.pop('LASTBOOK_MEANING_RED', None)
        r = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', code, str(ROOT)], capture_output=True, text=True,
                           encoding='utf-8', timeout=180, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertTrue(out['ok'], out)
        self.assertEqual(out['listens'], 0)
        self.assertEqual(out['modules'], [])          # no onnxruntime, no tokenizers, and hybrid search's model is not loaded
        self.assertTrue(out['fired'])
        self.assertTrue(out['folder'].replace('\\', '/').endswith('derived/models/meaning-red'), out)
        for _ in range(50):                           # the app exited: its runner went with it
            if not _pid_alive(out['pid']):
                break
            time.sleep(0.1)
        self.assertFalse(_pid_alive(out['pid']), 'the runner is still running after the app exited')


if __name__ == '__main__':
    unittest.main()
