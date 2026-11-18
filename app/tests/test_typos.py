#!/usr/bin/env python3
"""fork: spelling mistakes in search questions (engine/typos.py) against a small made-up vocabulary: no library, no server.

  python3 -B -m unittest app.tests.test_typos [-v]

The page counts (V) and emergency-book counts (E) below are rounded from the real library, so each trap is the one the
real words set: "checking" is on more pages than "choking", "showed" on 13 times as many as "shocked".
"""
import os, sys, unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine import typos  # noqa: E402

V = {  # pages per word
    'breathing': 2036, 'breaking': 1500, 'bleating': 12, 'treating': 900, 'creating': 1100, 'berthing': 13, 'husband': 400,
    'collapsed': 300, 'collapse': 500, 'stopped': 1200, 'choking': 137, 'checking': 1718, 'cooking': 1500,
    'shocking': 40, 'shooting': 248, 'showing': 2736, 'shouting': 100, 'shorting': 20, 'shocked': 93, 'showed': 1236,
    'smoked': 200, 'stoked': 15, 'stabbed': 17, 'stated': 1592, 'stayed': 150, 'staged': 300, 'asthma': 416, 'asia': 533,
    'riots': 15, 'roots': 1558, 'diner': 6, 'dinner': 161, 'finer': 321, 'seizure': 405, 'fire': 5000, 'fiber': 300,
    'bleach': 400, 'breech': 50, 'beech': 60, 'brunt': 5, 'burnt': 178, 'blunt': 293, 'baby': 3000, 'buy': 900, 'boy': 600,
    'pain': 3110, 'pan': 900, 'pin': 700, 'piano': 30, 'stroke': 900, 'stork': 12, 'snake': 800, 'snack': 60, 'soak': 700,
    'earthquake': 900, 'earthquakes': 400, 'diarrhea': 900, 'pneumonia': 400, 'agua': 192, 'aqua': 35, 'hervir': 12,
    'nino': 19, 'eu': 200, 'mt': 306, 'chain': 800, 'start': 4000, 'water': 9000, 'boil': 600, 'injection': 500,
    'adrenaline': 200, 'leg': 2000, 'chest': 1500, 'food': 6000, 'talk': 800, 'attack': 900, 'inhaler': 100, 'what': 31234,
    'wire': 1500, 'watts': 300, 'city': 2000, 'during': 8000,
}
E = {  # times the first-aid and emergency books use it
    'breathing': 1292, 'breaking': 50, 'treating': 100, 'creating': 10, 'choking': 117, 'checking': 37, 'cooking': 20,
    'shocking': 3, 'shooting': 19, 'showing': 53, 'shouting': 7, 'shocked': 4, 'showed': 159, 'smoked': 3, 'stated': 8,
    'asthma': 149, 'asia': 15, 'riots': 3, 'seizure': 136, 'fire': 1496, 'fiber': 13, 'bleach': 42, 'breech': 6,
    'burnt': 15, 'blunt': 37, 'baby': 645, 'buy': 36, 'boy': 22, 'pain': 1019, 'stroke': 242, 'snake': 66, 'soak': 29,
    'earthquake': 50, 'diarrhea': 400, 'pneumonia': 60, 'leg': 300, 'chest': 400, 'food': 200, 'what': 780,
}
WORDS = typos.Words(V, E)


def fix(q):
    return typos.correct_with(q, WORDS)


class Corrections(unittest.TestCase):
    def test_known_fixes(self):
        for q, want in [('my husbnd colapsed and isnt breating', "my husband collapsed and isn't breathing"),
                        ('hes chocking on food cant talk', "he's choking on food can't talk"),
                        ('some one is shoting', 'some one is shooting'), ('shoked by a wire', 'shocked by a wire'),
                        ('stabed in the chest', 'stabbed in the chest'), ('asma attack no inhaler', 'asthma attack no inhaler'),
                        ('chest pian', 'chest pain'), ('bleech', 'bleach'), ('brething', 'breathing'), ('strok', 'stroke'),
                        ('snak bit my leg', 'snake bit my leg'), ('bby', 'baby'), ('earthqauk', 'earthquake'),
                        ('diarea', 'diarrhea'), ('nemonia', 'pneumonia'), ('fier', 'fire')]:
            self.assertEqual(fix(q), want, q)

    def test_traps(self):
        self.assertEqual(fix('what to do during riots in the city'), 'what to do during riots in the city')  # the emergency books use it
        self.assertEqual(fix('chocking'), 'choking')       # not checking: a letter dropped beside its double (ck)
        self.assertEqual(fix('shoting'), 'shooting')       # not showing: t and w are not neighbouring keys
        self.assertEqual(fix('shoked'), 'shocked')         # not showed
        self.assertEqual(fix('stabed'), 'stabbed')         # not stated, nor staged
        self.assertEqual(fix('asma'), 'asthma')            # not asia
        self.assertEqual(fix('brunt'), 'burnt')            # a real word, but not one of the emergency books: swapped, not blunt
        self.assertEqual(fix('at diner'), 'at diner')      # a real word; neither dinner nor finer is in the emergency books

    def test_breath_and_breathe_stay(self):
        for q in ('she cant breath', 'cant breathe'):
            self.assertNotIn('breathing', fix(q), q)

    def test_apostrophes(self):
        self.assertEqual(fix('isnt'), "isn't")
        self.assertEqual(fix('Hes not breathing'), "He's not breathing")
        self.assertEqual(fix('it doesnt fade'), "it doesn't fade")
        self.assertEqual(fix("he isn't breating"), "he isn't breathing")      # typed with the apostrophe: left alone
        self.assertEqual(fix('give im injection'), 'give im injection')        # intramuscular, not "i'm"

    def test_short_words_numbers_and_models(self):
        for q in ('ot', 'eu', 'mt', 'EU2200i wont start', 'MT07 chain', '2200 watts', '12v', 'CPR', 'give IM adrenaline'):
            self.assertEqual(fix(q).replace("won't", 'wont'), q, q)
        self.assertEqual(fix('EU2200i wont start'), "EU2200i won't start")

    def test_capitals_kept(self):
        self.assertEqual(fix('Breating'), 'Breathing')
        self.assertEqual(fix('MY BABY ISNT BREATING'), "MY BABY ISN'T BREATHING")   # all in capitals: still corrected

    def test_other_languages_untouched(self):
        for q in ('niño', 'niño no respira', 'agua', 'hervir', 'hervir agua', 'como hervir agua', 'nino', 'água fervida',
                  'ñino con fiebre'):
            self.assertEqual(fix(q), q, q)

    def test_common_and_stop_words_untouched(self):
        for q in ('what', 'the water', 'roots', 'stated', 'checking the chain'):
            self.assertEqual(fix(q), q, q)


class Switch(unittest.TestCase):
    def setUp(self):
        self.real = typos.words_for
        typos.words_for = lambda path=None: WORDS
        typos._state['memo'] = {}
        self.env = os.environ.pop('LASTBOOK_TYPO_FIX', None)

    def tearDown(self):
        typos.words_for = self.real
        typos._state['memo'] = {}
        os.environ.pop('LASTBOOK_TYPO_FIX', None)
        if self.env is not None:
            os.environ['LASTBOOK_TYPO_FIX'] = self.env

    def test_on_by_default_and_shown(self):
        self.assertEqual(typos.correct('baby chokeing'), 'baby choking')
        self.assertEqual(typos.shown('baby chokeing'), {'corrected': 'baby choking'})
        self.assertEqual(typos.shown('baby choking'), {})

    def test_off_switch(self):
        os.environ['LASTBOOK_TYPO_FIX'] = '0'
        self.assertEqual(typos.correct('baby chokeing'), 'baby chokeing')
        self.assertEqual(typos.shown('baby chokeing'), {})

    def test_no_library(self):
        typos.words_for = lambda path=None: None
        self.assertEqual(typos.correct('baby chokeing'), 'baby chokeing')


class FromDatabase(unittest.TestCase):
    """The vocabulary read from a search database with the app's own table, read-only; too small a library changes nothing."""

    def test_small_library_changes_nothing_and_rebuilds_on_change(self):
        import sqlite3, tempfile
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / 'search.sqlite'
            con = sqlite3.connect(db)
            con.execute('CREATE VIRTUAL TABLE pages USING fts5(doc_id UNINDEXED,title,collection,category,path UNINDEXED,'
                        'page UNINDEXED,body,tokenize="unicode61")')
            rows = [('fa', 'First Aid Manual', '', '', '', i, 'choking breathing airway') for i in range(5)]
            rows += [('cook', 'Cooking', '', '', '', i, 'cooking checking food') for i in range(5)]
            con.executemany('INSERT INTO pages VALUES (?,?,?,?,?,?,?)', rows)
            con.commit()
            con.close()
            w = typos.Words.from_db(db)
            self.assertEqual(w.V['choking'], 5)
            self.assertEqual(w.E['choking'], 5)
            self.assertNotIn('cooking', w.E)
            self.assertIsNone(typos.words_for(db))      # 9 terms: far too few to tell a typo from a rare word
            before = typos._state['key']
            con = sqlite3.connect(db)
            con.execute("INSERT INTO pages VALUES ('x','x','','','',1,'more words here')")
            con.commit()
            con.close()
            typos.words_for(db)
            self.assertNotEqual(typos._state['key'], before)
            typos._state.update(key=None, words=None, memo={})


if __name__ == '__main__':
    unittest.main()
