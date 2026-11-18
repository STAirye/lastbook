#!/usr/bin/env python3
"""fork: long saved web pages are searched in sections (engine/sections.py), against a small made-up library.

  python -B -m unittest app.tests.test_long_pages [-v]

A whole book saved as one web page holds nearly every word, so it matched almost any question. The library here has one
such book (about 70,000 characters of machine-shop sentences, with "grease", "fire" and "pan" far apart and one passage
about a tourniquet), a short kitchen-fire page and a PDF page. The engine is run in its own process with LASTBOOK_DATA
pointing at it (paths are read when it is imported), and that process reports what it found as JSON. No model, no
server, no port. Never packaged."""
import json, os, random, sqlite3, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BOOK, KITCHEN, PDF = 'book-machine-shop', 'kitchen-fires', 'water-pdf'
TQ = 'In the shop, a tourniquet is tied above the wound on the limb when bleeding from the limb will not stop.'
KITCHEN_TEXT = ('Grease fire in a pan: turn off the heat and slide a lid over the pan. Never put water on a grease fire. '
                'Leave the lid on the pan until it is cool.')


def book_text():
    rnd = random.Random(7)
    nouns = 'lathe tool spindle chuck carriage gear shaft bearing bolt file drill bit vise cutter collet bench gauge'.split()
    verbs = 'set turn hold cut clamp measure check oil grind true'.split()
    out, n = [], 0
    while n < 70000:
        s = f'The {rnd.choice(nouns)} must be {rnd.choice(verbs)} with care before the {rnd.choice(nouns)} is used on the work, and the {rnd.choice(nouns)} should be kept clean.'
        out.append(s)
        n += len(s) + 1
    for at, extra in ((40, 'Wipe the grease from the ways each evening.'), (300, 'Keep a bucket of sand in case of fire.'),
                      (560, 'Chips fall into the drip pan under the bed.'), (230, TQ)):
        out.insert(at, extra)
    return '\n'.join(out)


def make_library(data):
    lib = data / 'library-data'
    (lib / 'pages').mkdir(parents=True)
    (lib / 'text').mkdir()
    cat = [{'id': BOOK, 'kind': 'html', 'title': 'Modern Shop Practice', 'collection': 'Books', 'category': 'tools', 'path': 'pages/book.html', 'publisher': 'Gutenberg'},
           {'id': KITCHEN, 'kind': 'html', 'title': 'Kitchen fires', 'collection': 'Safety', 'category': 'fire', 'path': 'pages/kitchen.html', 'publisher': 'Fire service'},
           {'id': PDF, 'kind': 'pdf', 'pages': 61, 'title': 'Safe water', 'collection': 'Water', 'category': 'water', 'path': 'documents/w.pdf', 'publisher': 'Health'}]
    (lib / 'catalog.json').write_text(json.dumps(cat), encoding='utf-8')
    (lib / 'pages' / 'book.html').write_text('<p>' + book_text().replace('\n', '</p><p>') + '</p>', encoding='utf-8')
    (lib / 'pages' / 'kitchen.html').write_text('<p>' + KITCHEN_TEXT + '</p>', encoding='utf-8')
    con = sqlite3.connect(lib / 'search.sqlite')
    con.execute('CREATE VIRTUAL TABLE pages USING fts5(doc_id UNINDEXED,title,collection,category,path UNINDEXED,page UNINDEXED,body,tokenize="unicode61")')
    for r, body in ((cat[0], book_text()), (cat[1], KITCHEN_TEXT), (cat[2], 'Bring water to a rolling boil for one minute.')):
        con.execute('INSERT INTO pages VALUES (?,?,?,?,?,?,?)', (r['id'], r['title'], r['collection'], r['category'], r['path'], 1, body))
    for n in range(2, 61):  # more pages, so word weights (bm25) are like a real library's: rare words count most
        con.execute('INSERT INTO pages VALUES (?,?,?,?,?,?,?)', (PDF, 'Safe water', 'Water', 'water', 'documents/w.pdf', n,
                                                                  f'Water page {n}: keep the water container covered and clean.'))
    con.commit()
    con.close()


def probe(data):
    """Run in the child process: the engine with LASTBOOK_DATA=data. Prints one JSON object."""
    os.environ['LASTBOOK_DATA'] = str(data)
    sys.path.insert(0, str(ROOT))
    import server, assistant, retrieval
    from engine import sections
    assistant.S = server          # keyword side only: no meaning-based index in this library
    out = {}
    main = sqlite3.connect(server.library.DB)
    out['plain_fire'] = [d for (d,) in main.execute("SELECT doc_id FROM pages WHERE pages MATCH 'grease AND fire AND pan'")]
    main.close()
    out['find_fire'] = [r['id'] for r in server.find('grease fire pan')['results']]
    out['fts_fire'] = [list(r[:2]) for r in assistant._fts('grease fire pan')]
    out['find_tq'] = [(r['id'], [h['page'] for h in r['hits']]) for r in server.find('tourniquet limb')['results']]
    out['fts_tq'] = [list(r[:2]) for r in assistant._fts('tourniquet limb')]
    out['hybrid_tq'] = [(h['doc_id'], h['page']) for h in assistant.hybrid('tourniquet limb')]
    out['hybrid_fire'] = [(h['doc_id'], h['page']) for h in assistant.hybrid('grease fire pan')]
    out['status'] = {k: str(v) for k, v in sections.status().items()}
    out['nsections'] = sections.sectioned(BOOK)
    out['kitchen_sectioned'] = sections.sectioned(KITCHEN)
    texts = server.doc_texts(server.catalog()['by_id'][BOOK])
    out['tq_section'] = next(i for i, t in enumerate(texts, 1) if 'tourniquet' in t)
    out['texts_rejoin'] = ' '.join(texts) == retrieval.norm_ws(book_text())
    out['files'] = sorted(p.name for p in (data / 'derived' / 'index').glob('sections-*.sqlite'))

    # meaning-based index: passages stored with the whole page's number, relabelled by section without re-embedding
    ix = retrieval.Index(server.catalog, server.trust, server.library.DB)
    db = ix._db()
    spans = retrieval.chunk_spans(retrieval.norm_ws(book_text()))
    rows = [(i + 1, BOOK, 1, None, c, 1) for i, (_, c) in enumerate(spans)]
    rows.append((len(rows) + 1, KITCHEN, 1, None, KITCHEN_TEXT, 1))
    rows.append((len(rows) + 1, BOOK, 1, None, 'a passage that is in no chunk of the book at all, kept as it was', 1))
    db.executemany('INSERT INTO chunk(id,doc_id,page,t,text,active) VALUES (?,?,?,?,?,?)', rows)
    db.executemany('INSERT INTO docstate VALUES (?,?,?,?)', [(BOOK, 'sig-1', len(spans) + 1, 0), (KITCHEN, 'sig-k', 1, 0)])
    first = ix.relabel_sections(db)
    again = ix.relabel_sections(db)
    path = sections.ensure(server.library.DB, server.kind_of)
    starts = sections.starts(path, BOOK)
    want = [sections.section_of(starts, s) for s, _ in spans]
    got = [p for (p,) in db.execute('SELECT page FROM chunk WHERE doc_id=? ORDER BY id', (BOOK,))]
    out['relabel'] = {'first': first, 'again': again, 'pages_right': got[:-1] == want, 'unmatched_kept': got[-1],
                      'kitchen': db.execute('SELECT page FROM chunk WHERE doc_id=?', (KITCHEN,)).fetchone()[0],
                      'max_page': max(got), 'tq_page': got[next(i for i, (_, c) in enumerate(spans) if 'tourniquet' in c)]}
    db.close()
    parts = ix._texts(BOOK, ('pages', server.catalog()['by_id'][BOOK]))
    out['texts_pages'] = sorted({p for p, _, _ in parts})
    out['texts_tq_page'] = next(p for p, _, c in parts if 'tourniquet' in c)
    out['texts_kitchen'] = sorted({p for p, _, _ in ix._texts(KITCHEN, ('pages', server.catalog()['by_id'][KITCHEN]))})

    # the library index changes: a new sections file on the next search, the old one removed
    old = sections.ensure(server.library.DB, server.kind_of)
    main = sqlite3.connect(server.library.DB)
    main.execute('INSERT INTO pages VALUES (?,?,?,?,?,?,?)', (PDF, 'Safe water', 'Water', 'water', 'documents/w.pdf', 61, 'Store boiled water covered.'))
    main.commit()
    main.close()
    os.utime(server.library.DB, ns=(os.stat(server.library.DB).st_atime_ns, os.stat(server.library.DB).st_mtime_ns + 10**9))
    server.find('store boiled water')
    new = sections.ensure(server.library.DB, server.kind_of)
    out['rebuild'] = {'changed': old != new, 'old_gone': not old.exists(), 'new_there': new.exists(),
                      'files': sorted(p.name for p in (data / 'derived' / 'index').glob('sections-*.sqlite')),
                      'same_again': sections.ensure(server.library.DB, server.kind_of) == new}
    print('PROBE ' + json.dumps(out))


class LongPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        data = Path(cls.dir.name) / 'Lastbook Data #1'
        make_library(data)
        e = {k: v for k, v in os.environ.items() if k not in ('LASTBOOK_DATA', 'LASTBOOK_LOCAL_AI')}
        r = subprocess.run([sys.executable, '-B', '-X', 'utf8', __file__, '--probe', str(data)], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', env=e, cwd=cls.dir.name)
        line = next((l for l in r.stdout.splitlines() if l.startswith('PROBE ')), None)
        if r.returncode or not line:
            raise AssertionError(f'probe failed ({r.returncode}):\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}')
        cls.o = json.loads(line[6:])

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def test_sections_built(self):
        self.assertGreaterEqual(self.o['nsections'], 12)
        self.assertEqual(self.o['kitchen_sectioned'], 0)               # short pages stay whole
        self.assertTrue(self.o['texts_rejoin'])                        # nothing lost between sections
        self.assertEqual(len(self.o['files']), 1)

    def test_scattered_words_no_longer_find_the_book(self):
        self.assertIn(BOOK, self.o['plain_fire'])                       # the problem: the whole page has all three words
        self.assertEqual(self.o['find_fire'][0], KITCHEN)
        self.assertEqual(self.o['fts_fire'][0][0], KITCHEN)
        self.assertEqual(self.o['hybrid_fire'][0][0], KITCHEN)
        self.assertNotIn(BOOK, self.o['find_fire'][:1])

    def test_one_section_is_found_as_its_section(self):
        sec = self.o['tq_section']
        self.assertGreater(sec, 1)
        self.assertEqual(self.o['find_tq'][0], [BOOK, [sec]])           # Library search: the hit names the section
        self.assertEqual(self.o['fts_tq'][0], [BOOK, sec])              # the assistant's keyword side
        self.assertEqual(self.o['hybrid_tq'][0], [BOOK, sec])           # hybrid keeps the section for html

    def test_semantic_relabel(self):
        rl = self.o['relabel']
        self.assertTrue(rl['pages_right'])
        self.assertIn(rl['tq_page'], (self.o['tq_section'] - 1, self.o['tq_section']))   # labelled by where the passage starts
        self.assertEqual(rl['unmatched_kept'], 1)
        self.assertEqual(rl['kitchen'], 1)
        self.assertGreater(rl['max_page'], 10)
        self.assertEqual(rl['first']['documents'], 1)
        self.assertEqual(rl['first']['unmatched'], 1)
        self.assertEqual(rl['again']['documents'], 0)                   # once per document and signature

    def test_new_passages_are_chunked_by_section(self):
        self.assertEqual(self.o['texts_pages'], list(range(1, self.o['nsections'] + 1)))
        self.assertEqual(self.o['texts_tq_page'], self.o['tq_section'])
        self.assertEqual(self.o['texts_kitchen'], [1])

    def test_rebuilt_when_the_library_index_changes(self):
        rb = self.o['rebuild']
        self.assertTrue(rb['changed'])
        self.assertTrue(rb['old_gone'])
        self.assertTrue(rb['new_there'])
        self.assertEqual(len(rb['files']), 1)
        self.assertTrue(rb['same_again'])


class Cut(unittest.TestCase):
    def test_cut_after_sentences(self):
        sys.path.insert(0, str(ROOT))
        from engine import sections
        text = ' '.join(f'Sentence number {i} is here.' for i in range(1500))
        secs = sections.cut(text)
        self.assertTrue(all(t.endswith('.') for _, t in secs))
        self.assertTrue(all(len(t) <= sections.SECTION for _, t in secs))
        self.assertTrue(all(len(t) >= sections.SECTION // 2 - 1 for _, t in secs[:-1]))
        starts = [s for s, _ in secs]
        self.assertEqual([sections.section_of(starts, s) for s in starts], list(range(1, len(secs) + 1)))
        self.assertEqual(sections.section_of(starts, starts[3] + 5), 4)
        self.assertEqual(sections.cut('x' * 12000)[0][1], 'x' * 5000)   # no space at all: a hard cut


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--probe':
        probe(Path(sys.argv[2]))
    else:
        unittest.main()
