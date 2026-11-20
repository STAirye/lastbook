"""fork: engine/wiki_vectors, encyclopedia articles by meaning from a vector index per file (dev toggle). Tiny fake
indexes, a fake question embedding and fake articles: no model, no libzim."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine import encyclopedias, sections, wiki_vectors as WV   # noqa: E402

FILL = 'Notes on other matters entirely. ' * 200       # ~6,600 characters: the article has 2 sections


def unit(*xs):
    v = np.zeros(WV.DIM, dtype=np.float32)
    for i, x in enumerate(xs):
        v[i] = x
    return v / np.linalg.norm(v)


class Vectors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.zims = {}
        self.texts = {'Burns': FILL + 'Burns: cool the burn under running water for twenty minutes.',
                      'Knots': 'Tie a bowline like this.', 'Fever': 'A fever is a high temperature.'}
        # file a: Burns (2 sections, the 2nd about burns), Knots; file b: Fever
        self.make('a.zim', ['Burns', 'Knots'], [unit(0, 1), unit(1, 0.2), unit(0, 0, 1)])
        self.make('b.zim', ['Fever'], [unit(0.6, 0.8)])
        for p in (mock.patch.object(encyclopedias, 'list_files', lambda root=None: sorted(self.zims)),
                  mock.patch.object(encyclopedias, 'zim_path', lambda name, root=None: self.zims.get(name)),
                  mock.patch.object(encyclopedias, 'entry_text', lambda arc, a, cap=None: (a, self.texts[a])),
                  mock.patch.dict(os.environ, {'LASTBOOK_WIKI_VECTORS': '1'})):
            p.start()
            self.addCleanup(p.stop)
        WV._reset_for_tests()
        self.addCleanup(WV._reset_for_tests)

    def make(self, name, articles, vecs, stale=False):
        z = self.dir / name
        z.write_bytes(b'x' * (10 + len(name)))
        self.zims[name] = z
        st = z.stat()
        stem = f'vec-{name}-{st.st_size + (1 if stale else 0)}-{st.st_mtime_ns}'
        art, start = [], []
        for ai, a in enumerate(articles):
            for s, _ in sections.cut(sections.norm_ws(self.texts[a]), sections.SECTION):
                art.append(ai)
                start.append(s)
        self.assertEqual(len(art), len(vecs))
        np.save(self.dir / f'{stem}.f16.npy', np.array(vecs, dtype=np.float16))
        (self.dir / f'{stem}.rows.json').write_text(json.dumps({'paths': articles, 'titles': articles, 'art': art,
                                                                'start': start}), encoding='utf-8')

    def pick(self, qv, **k):
        return WV.pick('how to cool a burn', folder=self.dir, embed=lambda texts: [qv], opener=lambda p: object(), **k)

    def test_off_unless_the_toggle(self):
        with mock.patch.dict(os.environ, {'LASTBOOK_WIKI_VECTORS': '0'}):
            self.assertIsNone(self.pick(unit(1, 0)))

    def test_best_section_across_files(self):
        got = self.pick(unit(1, 0))
        self.assertEqual([h['article'] for h in got], ['Burns', 'Fever', 'Knots'])
        self.assertIn('cool the burn under running water', got[0]['excerpt'])     # its 2nd section, not its start
        self.assertEqual(got[0]['zim'], 'a.zim')
        self.assertGreater(got[0]['score'], got[1]['score'])
        self.assertEqual(len(self.pick(unit(1, 0), limit=1)), 1)

    def test_no_index_or_a_stale_one_falls_back(self):
        self.zims.clear()
        self.make('c.zim', ['Fever'], [unit(1, 0)], stale=True)         # built for another edition of the file
        self.assertIsNone(self.pick(unit(1, 0)))

    def test_a_broken_index_is_skipped_once(self):
        name = 'a.zim'
        stem = WV._stem_for(name, self.zims[name], self.dir)
        (self.dir / f'{stem}.rows.json').write_text('{"paths": []}', encoding='utf-8')
        got = self.pick(unit(1, 0))
        self.assertEqual([h['article'] for h in got], ['Fever'])          # the other file still answers
        self.assertIn(stem, WV._failed)

    def test_runner_not_ready_falls_back(self):
        with mock.patch.object(WV.meaning_red, '_model', None):
            self.assertIsNone(WV.pick('burn', folder=self.dir))

    def test_an_embedding_error_falls_back(self):
        def boom(texts):
            raise RuntimeError('runner ended')
        self.assertIsNone(WV.pick('burn', folder=self.dir, embed=boom))


if __name__ == '__main__':
    unittest.main()
