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
sys.path[:0] = [str(ROOT), str(ROOT / 'app' / 'tests')]
import fixture  # noqa: E402
os.environ['LASTBOOK_DATA'] = str(fixture.ensure())   # engine.paths reads it once: the made-up library every test module uses
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

    # fork: each of these was bent into another word one edit away, so the negation went ("hasnt" -> hasn)
    CV = dict(V, hasn=50, haven=300, shouldn=40, wouldn=40, weren=30, hadn=20, shoulder=900, head=3000, here=9000,
              whose=900, wave=700, young=900, im=1078, id=1477, were=13643, well=21467, shell=959, hell=67, its=26804,
              lets=572, ill=1361, wed=45, shed=345, moved=800, all=50000, day=9000, vomiting=900, green=800)

    def test_contractions_typed_without_the_apostrophe(self):
        W = typos.Words(self.CV, E)
        for q, want in [('baby hasnt moved all day', "baby hasn't moved all day"),
                        ('i havent pooed in days', "i haven't pooed in days"),
                        ('you shouldnt swim after eating', "you shouldn't swim after eating"),
                        ('they werent breathing', "they weren't breathing"), ('it wouldnt stop', "it wouldn't stop"),
                        ('i shouldve called', "i should've called"), ('he is bleeding from the hed', 'he is bleeding from the head'),
                        ('heres what happened', "here's what happened"), ('whos there', "who's there"),
                        ('weve tried', "we've tried"), ('youve got to', "you've got to"), ('ive been sick', "i've been sick"),
                        ('kid aint breathing', "kid ain't breathing"), ('Hasnt moved', "Hasn't moved"),
                        ('HE HASNT MOVED', "HE HASN'T MOVED")]:
            self.assertEqual(typos.correct_with(q, W), want, q)
        for q in ('we were there', 'not well', 'a sea shell', 'bloody hell', 'its leg', 'lets go', 'he is ill',
                  'they wed in may', 'the shed', 'photo id', 'id card'):          # words of their own: left as typed
            self.assertEqual(typos.correct_with(q, W), q, q)

    def test_im_by_the_words_around_it(self):
        W = typos.Words(self.CV, E)
        for q, want in [('im vomiting green', "i'm vomiting green"), ('Im 17', "I'm 17"), ('IM DYING', "I'M DYING"),
                        ('and im bleeding', "and i'm bleeding")]:
            self.assertEqual(typos.correct_with(q, W), want, q)
        for q in ('give im adrenaline', 'im injection into the thigh', 'iv or im', 'give IM adrenaline', 'the IM route'):
            self.assertEqual(typos.correct_with(q, W), q, q)

    def test_negation_reaches_the_checks(self):
        from engine import confidence
        W = typos.Words(self.CV, E)
        for q in ('he isnt breathing', 'she hasnt peed all day', 'mum cant move her arm'):
            self.assertTrue(confidence.urgent(typos.correct_with(q, W)), q)
            self.assertNotRegex(typos.correct_with(q, W), r"\b(hasn|isn|can)\b(?!')", q)

    def test_names_with_capitals_inside_and_slang_stay(self):
        W = typos.Words(dict(self.CV, oring=30, unlike=900, fortunate=300, stiffly=20), E)
        for q in ('my brother is ODing', 'my iPhone', 'unalive myself', 'fortnite all night', 'sniffly nose'):
            self.assertEqual(typos.correct_with(q, W), q, q)

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


# fork: words typed with no spaces (split_word). Page counts and emergency-book counts from the real library, rounded.
GV = {
    'and': 130010, 'the': 119546, 'a': 116101, 'to': 114554, 'in': 111293, 'is': 103375, 'on': 80883, 'this': 76621,
    'it': 70581, 'can': 67601, 'not': 63310, 'so': 36241, 'do': 33303, 'how': 31207, 'i': 29030, 'water': 22274,
    'help': 14680, 'note': 13685, 'he': 7091, 'his': 5942, 'stop': 5500, 'cut': 5330, 'my': 4506, 'fire': 3433,
    'store': 3010, 'baby': 2229, 'blue': 2133, 'breathing': 2036, 'bleeding': 1853, 'rice': 1567, 'burn': 1508,
    'ion': 1433, 'son': 845, 'king': 545, 'kitchen': 408, 'craft': 363, 'ate': 352, 'hypothermia': 294, 'electro': 172,
    'choking': 137, 'cho': 123, 'electrocution': 94, 'purify': 74, 'hyper': 71, 'gutenberg': 53, 'hypo': 42, 'elk': 27,
    'hes': 21, 'chunking': 10, 'firecraft': 3, 'she': 6000, 'make': 9000, 'soap': 400,
}
GE = {'not': 4452, 'breathing': 1292, 'choking': 117, 'help': 1609, 'baby': 645, 'blue': 52, 'kitchen': 15, 'fire': 1496,
      'can': 3401, 'stop': 391, 'bleeding': 762, 'hypothermia': 101, 'electrocution': 4, 'the': 29784, 'his': 419,
      'this': 2472, 'cut': 144, 'burn': 393, 'water': 2475, 'how': 1018, 'store': 59, 'rice': 39}
GLUED = typos.Words(GV, GE)


class Glued(unittest.TestCase):
    """Words typed with no spaces, split into the library's words (split_word)."""

    def setUp(self):
        self.addCleanup(os.environ.pop, 'LASTBOOK_TYPO_SPLIT', None)
        os.environ.pop('LASTBOOK_TYPO_SPLIT', None)

    def fix(self, q):
        return typos.correct_with(q, GLUED)

    def test_glued_questions(self):
        for q, want in [('heschuokinghelkp', "he's choking help"),          # the owner's test: two slips and an apostrophe
                        ('hesnotbreathing', "he's not breathing"), ('mybabyisblue', 'my baby is blue'),
                        ('kitchenonfire', 'kitchen on fire'), ('cantstopbleeding', "can't stop bleeding"),
                        ('howtopurifywater', 'how to purify water'), ('Kitchenonfire', 'Kitchen on fire'),
                        ('MYBABYISBLUE', 'MY BABY IS BLUE'), ('help kitchenonfire now', 'help kitchen on fire now')]:
            self.assertEqual(self.fix(q), want, q)

    def test_real_long_words_and_names_stay(self):
        for q in ('hypothermia', 'electrocution', 'firecraft', 'Gutenberg', 'how do i treat hypothermia',
                  'what is electrocution', 'chunking'):
            self.assertEqual(self.fix(q), q, q)
        self.assertIsNone(typos.split_word('firecraft', GLUED))      # on 3 pages: a word of the library, never split
        self.assertEqual(self.fix('hypothermai'), 'hypothermia')    # a slip in one long word: corrected whole, not split

    def test_mash_and_short_words_stay(self):
        for q in ('asdfghjkl', 'qwertyuiop', 'jdjdk', 'zxcvbnm', 'sdfsdfsdf', 'hjkhjkhjk'):
            self.assertEqual(self.fix(q), q, q)
        self.assertIsNone(typos.split_word('mybaby', GLUED))           # fewer than 8 letters: never split

    def test_clean_questions_unchanged(self):
        for q in ('my baby is blue', "he's not breathing", 'how to purify water', 'kitchen on fire'):
            self.assertEqual(self.fix(q), q, q)

    def test_glued_with_an_apostrophe_inside(self):
        # fork: the apostrophe kept the run one token that was never split ("he'snotbreathingwhatdoido" found no pages)
        for q, want in [("he'snotbreathing", "he's not breathing"), ("she'sbleeding", "she's bleeding"),
                        ("i'mchoking", "i'm choking"), ("i’mchoking", "i'm choking"), ("He'snotbreathing", "He's not breathing"),
                        ("mybabyisn'tbreathing", "my baby isn't breathing"), ('help-hesnotbreathing', "help-he's not breathing"),
                        ("he's choking", "he's choking"), ("she's", "she's"), ("o'clock", "o'clock"), ('first-aid', 'first-aid')]:
            self.assertEqual(self.fix(q), want, q)
        os.environ['LASTBOOK_TYPO_SPLIT'] = '0'
        self.assertEqual(self.fix("he'snotbreathing"), "he'snotbreathing")

    def test_neighbours_found_as_edits1_finds_them(self):
        for s in ('chuoking', 'helkp', 'bleeeding', 'hypothermai', 'brething', 'kitchne', 'waterr', 'xqzv'):
            want = {x: how for x, how in typos._edits1(s).items() if x in GLUED.common}
            self.assertEqual(typos._near(s, GLUED), want, s)

    def test_switch(self):
        os.environ['LASTBOOK_TYPO_SPLIT'] = '0'
        self.assertEqual(self.fix('kitchenonfire'), 'kitchenonfire')
        self.assertEqual(self.fix('kitchne on fire'), 'kitchen on fire')     # the rest of the correction stays on


class BodyWords(unittest.TestCase):
    """fork: body words one slip away that fix_word leaves because the library has the slip as a word ("puls", on 24 pages),
    and glued runs with a body word that could not be split (typos.body_fix, engine/confidence.BODY_WORDS)."""
    BV = dict(GV, puls=24, pulse=1577, pulses=560, bloom=259, breeding=581, chore=16, choke=193, chose=359, blood=4372,
              breath=635, cook=2000, flowers=900, chicken=700, household=800, list=3000, has=50000, no=40000, what=31234)
    WORDS = typos.Words(BV, dict(GE, pulse=206, blood=955, breath=152, choke=5))

    def setUp(self):
        for k in ('LASTBOOK_BODY_FIX', 'LASTBOOK_BODY_SIGNS'):
            self.addCleanup(os.environ.pop, k, None)
            os.environ.pop(k, None)

    def fix(self, q):
        return typos.correct_with(q, self.WORDS)

    def test_real_word_slips_for_body_words(self):
        self.assertEqual(typos.fix_word('puls', self.WORDS), 'puls')        # 24 pages: a real word to fix_word
        self.assertEqual(self.fix('he has no puls what do i do'), 'he has no pulse what do i do')
        self.assertEqual(self.fix('He has no Puls'), 'He has no Pulse')

    def test_glued_body_words_that_could_not_be_split(self):
        self.assertIsNone(typos.split_word('mybbyisntbreathing', self.WORDS))
        self.assertEqual(self.fix('mybbyisntbreathing'), 'not breathing')
        self.assertEqual(self.fix('hesnotbreathing'), "he's not breathing")   # split as before

    def test_other_words_unchanged(self):
        for q in ('how to cook pulses', 'how to make flowers bloom', 'chicken breeding', 'household chore list',
                  'she chose', 'he has no pulse', "she can't breath", 'my baby is blue', 'kitchenonfire', 'firecraft'):
            self.assertEqual(self.fix(q), q.replace('kitchenonfire', 'kitchen on fire'), q)

    def test_switches(self):
        os.environ['LASTBOOK_BODY_FIX'] = '0'
        self.assertEqual(self.fix('he has no puls'), 'he has no puls')
        self.assertEqual(self.fix('mybbyisntbreathing'), 'mybbyisntbreathing')
        os.environ.pop('LASTBOOK_BODY_FIX')
        os.environ['LASTBOOK_BODY_SIGNS'] = '0'                                 # the body signs off: their correction too
        self.assertEqual(self.fix('he has no puls'), 'he has no puls')


class EnglishWords(unittest.TestCase):
    """fork: ordinary English words (engine/english_words.txt.gz) are never "corrected" into a library word; a short explicit
    list of real-word slips for emergency words is (SLIPS, PHRASE_SLIPS); letters typed again and again are cut first."""
    EV = dict(V, peeled=300, poking=40, sewing=500, blocked=900, gaps=700, sizes=900, tested=900, stock=2000, poised=60,
              crust=200, camp=900, brand=800, breathe=900, bleeding=1800, passed=2000, heart=3000, drooping=40, weak=900,
              blood=4000, help=9000, please=3000, so=20000, much=9000, no=40000, leak=800, gas=3000, hemorrhage=150,
              unconscious=800, tourniquet=200, poisoned=300, man=5000, my=30000, son=900, having=8000, he=40000, she=30000,
              was=50000, the=90000, a=90000, lot=3000, car=4000, properly=900, face=2000, arm=1500, **{'from': 60000, 'is': 90000})
    WORDS = typos.Words(EV, dict(E, breathe=300, bleeding=600, heart=400, blood=900, help=800, leak=40, gas=300))

    def setUp(self):
        self.addCleanup(os.environ.pop, 'LASTBOOK_TYPO_ENGLISH', None)
        os.environ.pop('LASTBOOK_TYPO_ENGLISH', None)

    def fix(self, q):
        return typos.correct_with(q, self.WORDS)

    def test_the_list_ships_and_reads_fast(self):
        typos._ENGLISH['words'] = None
        words = typos.english_words()
        self.assertIs(typos.english_words(), words)     # read once: later questions pay nothing (no clock: a busy machine is slow)
        self.assertGreater(len(words), 50000)
        self.assertTrue({'keeled', 'puking', 'gasps', 'seizes', 'breathing'} <= words)
        self.assertFalse({'strock', 'poisend', 'siezing', 'bleding', 'hlep', 'breating'} & words)
        self.assertTrue((ROOT / 'engine' / 'english_words.LICENSE.txt').is_file())

    def test_everyday_words_stay(self):
        for q in ('she keeled over', 'he keeps puking', 'spewing everywhere', 'he blacked out', 'short gasps', 'he seizes',
                  'she texted me', 'crusty eyes', 'leg cramp', 'colour of the rash', 'the dog is breeding'):
            self.assertEqual(self.fix(q), q, q)
        for w in ('keeled', 'colour', 'haemorrhage', 'paracetamol', 'mum'):
            self.assertTrue(typos.is_english(w), w)
        self.assertIsNone(typos.split_word('dribbling', self.WORDS))       # a long English word is never split

    def test_typos_are_still_fixed(self):
        for q, want in [('strock', 'stroke'), ('poisend', 'poisoned'), ('hemmorage', 'hemorrhage'), ('unconshus man', 'unconscious man'),
                        ('hlep', 'help'), ('brething', 'breathing'), ('chocking', 'choking'), ('brunt', 'burnt')]:
            self.assertEqual(self.fix(q), want, q)

    def test_real_word_slips(self):
        for q, want in [('he cant breed', 'he can\'t breathe'), ("hes not braking", "he's not breathing"),
                        ('she is not breaking', 'she is not breathing'), ('she is breeding a lot from the leg', 'she is bleeding a lot from the leg'),
                        ('my son is having a sea sure', 'my son is having a seizure'), ('he past out', 'he passed out'),
                        ('cheat pain', 'chest pain'), ('chest pane', 'chest pain'), ('dad having a hart attack', 'dad having a heart attack'),
                        ('gas leek', 'gas leak'), ('his face is dropping', 'his face is drooping'), ('my arm feels week', 'my arm feels weak')]:
            self.assertEqual(self.fix(q), want, q)
        for q in ('the car is not braking properly', 'we are not breeding the dogs', 'in the past out of the way'):
            self.assertEqual(self.fix(q), q, q)                              # a machine, an animal, the past

    def test_letters_typed_again_and_again(self):
        self.assertEqual(self.fix('sooo much bloooood'), 'so much blood')
        self.assertEqual(self.fix('pleaseeee helpppp my son'), 'please help my son')
        self.assertEqual(self.fix('kkkkk'), 'kkkkk')                         # mash stays mash
        self.assertEqual(typos.unstretch('breathing', self.WORDS.V), 'breathing')

    def test_switch(self):
        os.environ['LASTBOOK_TYPO_ENGLISH'] = '0'
        self.assertFalse(typos.is_english('keeled'))
        self.assertNotIn('breathe', self.fix('he cant breed'))              # no real-word slips either
        self.assertEqual(self.fix('gasps'), 'gaps')                         # as before: bent into the library's word


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
        self.addCleanup(typos._state.update, key=None, words=None, memo={})   # also when a check fails
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


if __name__ == '__main__':
    unittest.main()
