#!/usr/bin/env python3
"""fork: the meaning check for urgent questions (engine/meaning_red.py, docs/FORK.md 3m).

  python -X utf8 -B -m unittest app.tests.test_meaning_red [-v]

Checked: it fires on clear urgent wordings and not on clear everyday ones (with the model files built by
tools/meaning_red_model.py in derived/models/meaning-red; skipped without them), it only ever adds to the urgent words, it
falls back quietly when a file is missing or changed or onnxruntime is blocked, LASTBOOK_MEANING_RED=0, several threads at
once, the manifest, and a process that loads it opens no listening socket and loads no other model. Never packaged."""
import json, os, re, shutil, subprocess, sys, tempfile, threading, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT)]

from engine import meaning_red  # noqa: E402

HAVE = meaning_red.find(check=False)[0] is not None
URGENT = ['my husband collapsed and is not breathing', 'she swallowed a whole bottle of her pills an hour ago',
          'my baby went floppy and blue']
EVERYDAY = ['how do i bake sourdough bread', 'best way to store potatoes for winter', 'how to fix a squeaky door hinge']


def fresh():
    meaning_red._reset_for_tests()


class Manifest(unittest.TestCase):
    def test_names_sizes_and_hashes(self):
        m = meaning_red.manifest()
        self.assertRegex(m['repo'], r'^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$')
        self.assertEqual([f['name'] for f in m['files']], ['model_int8.onnx', 'tokenizer.json', 'centroids.npz'])
        for f in m['files']:
            self.assertRegex(f['sha256'], r'^[0-9a-f]{64}$')
            self.assertGreater(f['size'], 1000)
        self.assertTrue(m['revision'] == '' or re.fullmatch(r'[0-9a-f]{40}', m['revision']), m['revision'])

    def test_nothing_to_download_until_published(self):
        with mock.patch.object(meaning_red, 'manifest', lambda: {'repo': 'a/b', 'revision': '', 'files': []}):
            self.assertIsNone(meaning_red.urls())
        rev = 'a' * 40
        files = [{'name': 'x.onnx', 'size': 5, 'sha256': '0' * 64}]
        with mock.patch.object(meaning_red, 'manifest', lambda: {'repo': 'a/b', 'revision': rev, 'files': files}):
            self.assertEqual(meaning_red.urls(), [('x.onnx', f'https://huggingface.co/a/b/resolve/{rev}/x.onnx', 5, '0' * 64)])

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

    @unittest.skipUnless(HAVE, 'no meaning-red files: run tools/meaning_red_model.py')
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

    def test_blocked_runtime_loads_no_dll(self):
        with mock.patch.dict(sys.modules, {'onnxruntime': None}):
            with self.assertRaises(ImportError):
                meaning_red._import_runtime()

    def test_switch(self):
        with mock.patch.dict(os.environ, {'LASTBOOK_MEANING_RED': '0'}):
            meaning_red.start()
            self.assertIsNone(meaning_red._thread)
            self.assertFalse(meaning_red.status()['on'])
            self.assertEqual(meaning_red.check('my husband is not breathing')['state'], 'switched off')

    def test_not_started_never_blocks(self):
        self.assertEqual(meaning_red.check('my husband is not breathing'), {'score': None, 'fired': False, 'state': 'not started'})


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

    def test_turn_info_carries_it(self):
        yes = lambda t: {'score': 0.05, 'fired': True, 'state': 'ready'}
        with mock.patch.object(meaning_red, 'check', yes), mock.patch.object(self.a, 'hybrid', lambda q, k=8, trace=None: []):
            hits, info = self.a.turn_hits([{'role': 'user', 'content': 'how do i bake sourdough bread'}])
        self.assertTrue(info['danger'])
        self.assertEqual(info['meaning'], {'score': 0.05, 'fired': True, 'state': 'ready', 'words': False})


@unittest.skipUnless(HAVE, 'no meaning-red files: run tools/meaning_red_model.py')
class Loaded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fresh()
        if 'onnxruntime' in sys.modules and sys.modules['onnxruntime'] is None:
            del sys.modules['onnxruntime']
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


@unittest.skipUnless(HAVE, 'no meaning-red files: run tools/meaning_red_model.py')
class WholeProcess(unittest.TestCase):
    def test_loads_only_its_model_and_listens_on_nothing(self):
        code = r'''
import json, socket, sys
sys.path.insert(0, sys.argv[1])
listens = []
_l = socket.socket.listen
socket.socket.listen = lambda self, *a: (listens.append(1), _l(self, *a))[1]
from engine import meaning_red
ok = meaning_red.wait(120)
r = meaning_red.check('my husband collapsed and is not breathing')
print(json.dumps({'ok': ok, 'listens': len(listens), 'retrieval': 'retrieval' in sys.modules, 'fired': r['fired'],
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
        self.assertFalse(out['retrieval'])          # hybrid search's model is not loaded with it
        self.assertTrue(out['fired'])
        self.assertTrue(out['folder'].replace('\\', '/').endswith('derived/models/meaning-red'), out)


if __name__ == '__main__':
    unittest.main()
