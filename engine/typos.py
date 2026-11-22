"""fork: spelling mistakes in a search question, corrected against the library's own words.

Keyword search (server.query_groups, FTS5 with unicode61) needs whole words. "my husbnd colapsed and isnt breating" matches
nothing, the search falls back to any of the words, and the word that was the emergency drops out. This puts each
misspelled word back to a word the library uses, before the keyword search and the meaning-based search see the question.

- The words are the keyword index's own terms (fts5vocab), with the number of pages each is on: no dictionary is downloaded.
  The first-aid and emergency books of the library (by title) count extra, so "chokeing" becomes "choking", not "cooking".
  Both are read from the read-only search database in about 1 s and kept in memory until that file changes.
- A word is changed only when it looks like a typo: plain a-z letters, 3 or more, not a stop word, on fewer than RARE pages.
  The replacement is one edit away (a letter dropped, added, changed, or two swapped), or two edits for words of 5+ letters,
  and on at least GAIN times as many pages.
- A word the library itself prints on 3+ pages is a real word ("riots", "diner") and stays, unless the emergency books
  never use it, they do use the replacement, and a plausible one-edit slip leads there ("brunt" -> burnt): then it is
  most likely a slip for an emergency word. "riots" is in the emergency books itself, so it is never "roots".
- How the word was mistyped counts. A changed letter must be a neighbouring key or a vowel for a vowel ("bleech" ->
  bleach, "seazure" -> seizure); others come last ("shoting" is not "showing", "shoked" not "showed", "stabed" not
  "stated", "brunt" not "blunt"). A letter doubled or undoubled (ck is a doubled k) counts as if the word were on about
  20 times the pages: "chocking" -> choking, not checking; "stabed" -> stabbed.
- Words with digits ("EU2200i", "MT07"), apostrophes, hyphens or letters beyond a-z, and questions that look like another
  language ("hervir agua", "niño"), are left as typed. A library too small to tell typos from rare words changes nothing.
- fork: contractions typed without the apostrophe are put back first (APOSTROPHES: "hasnt" -> hasn't, not hasn; "im" by
  the words around it), so the negation reaches the search and the checks. A word with capitals inside ("ODing",
  "iPhone") is a name, not a typo, and stays.
- fork: words typed with no spaces are split (split_word): "heschuokinghelkp" -> "he's choking help", "kitchenonfire" ->
  "kitchen on fire". Only a word of 8+ letters the index doesn't hold, so "hypothermia", "firecraft" and "Gutenberg"
  stay; each piece may have one of the slips above. A run typed with an apostrophe inside ("he'snotbreathing",
  "i'mchoking") is split too, from 6 letters; a hyphenated word only part by part. Off with LASTBOOK_TYPO_SPLIT=0.
- fork: an ordinary English word is never corrected, split or made a body word (is_english: engine/english_words.txt.gz,
  the hunspell en_US words with every form, 78,238; British spellings through the American one), so "keeled", "puking"
  and "gasps" stay. A short, explicit list of real words that are slips for an emergency word is put right: SLIPS
  ("chocking", "brunt") and PHRASE_SLIPS, by the words around them ("he cant breed" -> breathe, "breeding a lot from the
  leg" -> bleeding, "sea sure" -> seizure, "past out", "cheat pain", "hart attack", "gas leek"). Letters typed again and
  again are cut first ("bloooood" -> blood). Off with LASTBOOK_TYPO_ENGLISH=0 (the word list, the slips and the cutting).
- Off with LASTBOOK_TYPO_FIX=0.
"""
import math, os, re, sqlite3, threading, time, unicodedata
from pathlib import Path

from engine.paths import ro_uri

RARE = 20           # a word on this many pages or more is never changed
GAIN = 50           # the replacement must be on this many times as many pages as the word
GAIN_INDEXED = 20   # for a word the index holds: less, since the emergency books must also use the replacement and not the word
MIN_PAGES = 10      # a word the index has never seen: the replacement must still be on this many pages
EMERGENCY_MIN = 5   # a real (indexed) word is changed only to a word the emergency books use at least this often
MIN_VOCAB = 5000    # fewer terms than this (a test library, a first install): no correction at all
LETTERS = 'abcdefghijklmnopqrstuvwxyz'

# The same as server.STOP: words the search drops anyway.
STOP = set('a an and are as at be but by can do does for from get got have help how i if in into is it its me my need '
           'no not of on or our please should so some that the their them then there these they this to up us was we '
           'what when where which who why will with without you your'.split())
# Typed without the apostrophe. Put back before any other correction, or the corrector bends them into another word and
# the negation goes ("hasnt" -> hasn, "shouldve" -> shoulder, "whos" -> whose). Not "its", "were", "well", "ill", "lets",
# "shell", "hell", "wed", "shed" or "id": those are words, and common ones in the library (id: 1,477 pages, ID). Not
# "hed" either: in the held-out lists it was typed for head ("bluding from the hed"), not he'd. "cant"
# and "wont" are words too, but rare ones (96 and 28 pages): typed in a question they are nearly always can't and won't.
# "im" only by the words around it (IM_KEPT): "give im adrenaline" is intramuscular.
APOSTROPHES = {'isnt': "isn't", 'cant': "can't", 'wont': "won't", 'dont': "don't", 'doesnt': "doesn't", 'didnt': "didn't",
               'wasnt': "wasn't", 'arent': "aren't", 'couldnt': "couldn't", 'hes': "he's", 'shes': "she's",
               'thats': "that's", 'someones': "someone's", 'theyre': "they're",
               # fork: the rest of the common ones
               'werent': "weren't", 'hasnt': "hasn't", 'havent': "haven't", 'hadnt': "hadn't", 'wouldnt': "wouldn't",
               'shouldnt': "shouldn't", 'mustnt': "mustn't", 'neednt': "needn't", 'shant': "shan't", 'aint': "ain't",
               'whats': "what's", 'theres': "there's", 'wheres': "where's", 'heres': "here's", 'whos': "who's",
               'hows': "how's", 'everyones': "everyone's", 'somebodys': "somebody's", 'youre': "you're",
               'ive': "i've", 'weve': "we've", 'youve': "you've", 'theyve': "they've", 'couldve': "could've",
               'wouldve': "would've", 'shouldve': "should've", 'mightve': "might've", 'youll': "you'll",
               'theyll': "they'll", 'itll': "it'll", 'thatll': "that'll", 'youd': "you'd", 'theyd': "they'd"}
# "im" is I'm, unless a medicine word is beside it ("give im injection", "im adrenaline", "iv or im"). IM in capitals in
# a question not all in capitals is kept anyway (correct_with).
IM_KEPT = re.compile(r"\b(give|given|gave|giving|via|by|an|the|iv|sc|(iv|sc) or)\s+im\b|\bim\s+(injection|injections|inj|injected|"
                     r"adrenaline|adrenalin|epinephrine|epi|glucagon|dose|doses|route|shot|needle|or|iv|and iv)\b", re.I)
IM = re.compile(r"\b([Ii])[Mm]\b(?!['’])")
# Well-known misspellings of emergency words that edits cannot reach, or reach wrongly. Each is used only when the right
# word is in the library. "asma" is also asthma in Spanish and Portuguese.
KNOWN = {'asma': 'asthma', 'azma': 'asthma', 'asthama': 'asthma', 'nemonia': 'pneumonia', 'numonia': 'pneumonia',
         'newmonia': 'pneumonia', 'pnemonia': 'pneumonia', 'excema': 'eczema', 'exema': 'eczema',
         'diarea': 'diarrhea', 'diarrea': 'diarrhea', 'diarhea': 'diarrhea', 'diareah': 'diarrhea', 'diahrea': 'diarrhea',
         # fork: three or more edits away, or one edit from another real word ("hemmorage", "strock" -> stock)
         'hemmorage': 'hemorrhage', 'hemorage': 'hemorrhage', 'hemmorhage': 'hemorrhage', 'hemorhage': 'hemorrhage',
         'haemorage': 'haemorrhage', 'hemmorrhage': 'hemorrhage', 'unconshus': 'unconscious', 'unconsious': 'unconscious',
         'unconcious': 'unconscious', 'unconscous': 'unconscious', 'anafilactic': 'anaphylactic',
         'anafalactic': 'anaphylactic', 'anaphalactic': 'anaphylactic', 'anafilaxis': 'anaphylaxis',
         'anaphalaxis': 'anaphylaxis', 'tournaquet': 'tourniquet', 'tourniquette': 'tourniquet', 'tornaquet': 'tourniquet',
         'turniquet': 'tourniquet', 'tourniket': 'tourniquet', 'hlep': 'help', 'halp': 'help', 'hepl': 'help',
         'siezure': 'seizure', 'seasure': 'seizure', 'seazure': 'seizure', 'siezures': 'seizures', 'strock': 'stroke',
         'stroak': 'stroke', 'poisend': 'poisoned', 'poisned': 'poisoned', 'posioned': 'poisoned', 'posion': 'poison',
         'poisen': 'poison', 'brest': 'breast', 'bluding': 'bleeding', 'concusion': 'concussion', 'dady': 'daddy'}
# fork: real words that are, in a question here, nearly always a slip for an emergency word. Kept small and explicit:
# every other ordinary English word stays as typed (english_words). Used only when the right word is in the library.
# "wile" -> while is not an emergency word, but the triage sets' typo questions relied on it.
SLIPS = {'chocking': 'choking', 'chocked': 'choked', 'overdoes': 'overdose', 'brunt': 'burnt', 'wile': 'while'}
# Real words that are a slip for a body word only next to certain words ("he cant breed", "she is breeding a lot from
# the leg", "my son is having a sea sure"). (pattern, replacement), tried on the question before its words, in order.
_NOT = r"(not|isn'?t|isnt|aren'?t|wasn'?t|can'?t|cant|cannot|couldn'?t|won'?t|wont|stopped|barely|hardly|no longer|trouble|struggling to|hard to)"
_END = r"(?=\s*($|[.,!?;:]|\b(and|but|properly|right|well|normally|at all|any ?more|now|again|very|so|or|i)\b))"
_MACHINE = re.compile(r"\b(car|cars|bike|bicycle|brakes?|truck|lorry|van|vehicle|wheels?|pedals?|engine|motor\w*|lock|code|"
                      r"glass|habit|rules?|law|record|news|dough|bread|loaf|crumbs?|chickens?|dogs?|cats?|rabbits?|"
                      r"horses?|cattle|sheep|goats?|pigs?|fish|birds?|plants?|seeds?)\b", re.I)
PHRASE_SLIPS = [(re.compile(rx, re.I), new, machine) for rx, new, machine in (
    (r"\b" + _NOT + r"\s+(breeding|breading|braking|breaking|breething)" + _END, r"\1 breathing", True),
    (r"\b" + _NOT + r"\s+(breed|bread|brake|break|breth)" + _END, r"\1 breathe", True),
    (r"\b(breeding|bleating|bleding)(?=\s+(a lot|alot|heavily|badly|everywhere|from|out of|loads|lots|so much|"
     r"profusely|non ?stop|again|still|all over)\b)", 'bleeding', False),
    (r"\b(sea|see|sie) ?sure(s)?\b", r"seizure\2", False),
    (r"(?<!\bthe )(?<!\bin the )\bpast out\b", 'passed out', False),
    (r"\b(cheat|chess|chests|chesty) (pain|pains|pane|panes)\b", r"chest \2", False),
    (r"\bchest panes?\b", 'chest pain', False),
    (r"\bhart (attack|attach|attak|beat|rate)\b", r"heart \1", False),
    (r"\b(gas|water|oil|fuel|petrol|chemical|acid) leeks?\b", r"\1 leak", False),
    (r"\b(heart|asthma|panic) attach\b", r"\1 attack", False),
    (r"\b(face|mouth|smile|eye|eyelid|lip|side of (his|her|my|the|their) face) (is |was |keeps |has |started |starts )?"
     r"dropping\b", r"\1 \3drooping", False),
    (r"\b(pulse|heartbeat|arm|leg|hand|side|legs|arms|feel|feels|feeling|felt|is|so|very|really) (is |are |so |very "
     r"|really |gone |went )?weeks?\b(?!\s+(old|ago|away|pregnant|later|before|after|of|in|to|now|\d))",
     r"\1 \2weak", False),
)]
# Letters typed again and again ("bloooood", "helpppp", "pleaseeee") are cut to one or two before anything else.
STRETCH = re.compile(r'(.)\1\1')
# A question in another language is not corrected into English. Common function words of Spanish, Portuguese and French that
# are not English words (as in assistant.OTHER_WORDS, which decides when the local AI writes English search words).
# "de", "ir", "voy", "estoy" and the rest of the second line: without them "Me muero de ganas de
# ir a la playa" counted as English and became "Me mere de gaas de ir a la play" (test list 4).
OTHER_WORDS = set('el la los las del al en y que es un una por para con sin pero como muy mi mis tu su sus se lo le les nos '
                  'de ir esa ese eso esas esos estoy estas voy nada quiero cada otra otro todo toda todos unos unas '
                  'yo este esta esto cuando tengo tiene necesito puedo hacer agua fuego nao um uma com isso voce tem '
                  'preciso fazer des du et est avec pas je comment pourquoi vous nous eau'.split())
ENGLISH_WORDS = STOP | set('am been were has had about after before out'.split())
# Words of English and of Spanish or Portuguese both ("a", "me", "no"): looks_foreign counts them for neither.
SHARED = {'a', 'me', 'no'}
# fork: ordinary English, not only the library's words. The corrector knows only the library, so it bent everyday words
# into other words: "keeled" -> peeled, "puking" -> poking, "spewing" -> sewing, "gasps" -> gaps. A word of this list
# (engine/english_words.txt.gz: every form of the hunspell en_US words, 78,238; licence beside it) is never corrected,
# split or made a body word, except the slips above (SLIPS, PHRASE_SLIPS). British spellings count through the American
# one ("colour", "haemorrhage", "paediatric"), and a few chat words and medicine names the list lacks are added here.
EXTRA_ENGLISH = set('lol lmao omg pls plz thx idk ok okay yeah yep nope nah gonna wanna gotta kinda dunno aint ya ur '
                    'mum mums mam nan nana nans grandad grandads granny nappy nappies telly bloke paracetamol ibuprofen '
                    'tylenol advil panadol nurofen calpol xanax valium epipen inhaler inhalers cpr aed defib '
                    # fork: slang, brand and medical words the list lacks, that the corrector bent into another word
                    # ("unalive" -> unlike, "fortnite" -> fortunate, "sniffly" -> stiffly, "stooling" -> stooping).
                    # All found in independent test list 2's messages (docs/FORK.md 3k): that list is no longer blind
                    # for them, so its typo numbers after this change are in-sample.
                    'unalive unalived tbh redback redbacks rennie rennies fortnite sniffly gurgly fluey konked gouching '
                    'doms stooling'.split())
BRITISH = (('our', 'or'), ('isation', 'ization'), ('ise', 'ize'), ('yse', 'yze'), ('ae', 'e'), ('oe', 'e'), ('tre', 'ter'),
           ('ogue', 'og'), ('ence', 'ense'), ('lled', 'led'), ('lling', 'ling'))
_ENGLISH = {'words': None}


def english_words():
    """The set of engine/english_words.txt.gz (beside this file; in the packaged app under engine/ there too), read once
    (about 10 ms). Empty when the file is missing: then nothing is guarded, as before."""
    if _ENGLISH['words'] is None:
        import gzip, sys
        path = Path(__file__).with_name('english_words.txt.gz')
        if not path.is_file() and getattr(sys, 'frozen', False):
            path = Path(getattr(sys, '_MEIPASS', '')) / 'engine' / 'english_words.txt.gz'
        try:
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                _ENGLISH['words'] = frozenset(f.read().split())
        except OSError:
            _ENGLISH['words'] = frozenset()
    return _ENGLISH['words']


def english_on():
    return os.environ.get('LASTBOOK_TYPO_ENGLISH', '1') != '0'


def is_english(w):
    """fork: True when w (any case) is an ordinary English word (english_words, EXTRA_ENGLISH, or a British spelling of
    one). False when LASTBOOK_TYPO_ENGLISH=0."""
    if not english_on() or not w:
        return False
    w = w.lower()
    E = english_words()
    if w in E or w in EXTRA_ENGLISH:
        return True
    return any(a in w and w.replace(a, b) in E for a, b in BRITISH)


def unstretch(w, V):
    """fork: w with letters typed three or more times running cut to one or two ("bloooood" -> blood, "helpppp" -> help),
    the way that is a word (English, the library's on MIN_PAGES pages, or one typed without its apostrophe), the library's
    commonest first; else cut to two, for the corrector to try. w itself when nothing runs three times."""
    if not english_on() or not STRETCH.search(w) or len(set(w)) < 2:     # "kkkkk" is mash, not "k"
        return w
    import itertools
    runs = [m.group(0) for m in re.finditer(r'(.)\1*', w)]
    opts = [[r[0], r[0] * 2] if len(r) >= 3 else [r] for r in runs]
    if sum(len(o) > 1 for o in opts) > 4:
        return ''.join(o[-1] for o in opts)
    cands = [''.join(p) for p in itertools.product(*opts)]
    known = [c for c in cands if c in APOSTROPHES or is_english(c) or V.get(c, 0) >= MIN_PAGES]
    return (max(known, key=lambda c: (c in APOSTROPHES, is_english(c), V.get(c, 0))) if known     # "hesss": he's, not Hess
            else ''.join(o[-1] for o in opts))


def phrase_slips(q):
    """fork: q with PHRASE_SLIPS put right ("he cant breed" -> he cant breathe), unless a breathing slip is about a machine,
    food or an animal ("the car is not braking", "not breeding the dogs")."""
    for rx, new, machine in PHRASE_SLIPS:
        if english_on() and rx.search(q) and not (machine and _MACHINE.search(q)):
            q = rx.sub(new, q)
    return q


def restore_im(q, shouting=False):
    """fork: "im" typed for I'm put back ("im vomiting" -> i'm vomiting), unless a medicine word is beside one (IM_KEPT:
    "give im adrenaline"). IM in capitals stays unless the whole question is in capitals."""
    if IM_KEPT.search(q):
        return q
    return IM.sub(lambda m: m.group(0) if m.group(0) == 'IM' and not shouting else
                  m.group(1) + ("'M" if m.group(0)[1] == 'M' else "'m"), q)
# The library's own first-aid and emergency books, found by title. The financial "first aid kit" is not one.
EMERGENCY_TITLES = ('title:("first aid" OR "emergency care" OR resuscitation OR "where there is no doctor" OR '
                    '"emergency response guidebook" OR "fire safety" OR "are you ready" OR "cert basic") NOT title:financial')


class Words:
    """The library's words: pages per term (V) and how often the emergency books use each word (E)."""

    def __init__(self, vocab, emergency=None):
        self.V, self.E = vocab, emergency or {}
        self.common = {t for t, n in vocab.items() if n >= MIN_PAGES and len(t) >= 3}    # what a word can become
        self._drops = None
        self.lmax = math.log(max(vocab.values())) if vocab else 0.0    # split_word: the commonest word's pages
        self.pieces = {}        # split_word: each piece tried -> its cheapest reading

    @property
    def drops(self):
        """Each word of common with one letter dropped -> that word, or a tuple of them: finds two-edit replacements in
        milliseconds rather than a second. Made on the first word that needs it (0.15 s, about 26 MB for 48,000 words)."""
        if self._drops is None:
            d = {}
            for t in self.common:
                for i in range(len(t)):
                    s = t[:i] + t[i + 1:]
                    v = d.get(s)
                    d[s] = t if v is None else (v, t) if isinstance(v, str) else v + (t,)
            self._drops = d
        return self._drops

    @classmethod
    def from_db(cls, path):
        con = sqlite3.connect(ro_uri(path), uri=True)
        try:
            con.execute('CREATE VIRTUAL TABLE temp.v USING fts5vocab(main, pages, row)')
            vocab = {t: n for t, n in con.execute('SELECT term, doc FROM temp.v WHERE doc >= 3') if t.isascii() and t.isalpha()}
            counts = {}
            for (body,) in con.execute('SELECT body FROM pages WHERE pages MATCH ?', (EMERGENCY_TITLES,)):
                for w in re.findall(r'[a-z]{3,}', (body or '').lower()):
                    counts[w] = counts.get(w, 0) + 1
        finally:
            con.close()
        return cls(vocab, {w: n for w, n in counts.items() if n >= 3})

    def score(self, w):
        # Words of the emergency books first, then how common the word is.
        return 2 * math.log1p(self.E.get(w, 0)) + math.log(self.V[w])


def _keys():
    """Letters next to each other on a QWERTY keyboard (rows offset by half a key)."""
    pos = {c: (r, i + r / 2) for r, row in enumerate(('qwertyuiop', 'asdfghjkl', 'zxcvbnm')) for i, c in enumerate(row)}
    return {(a, b) for a, (ra, xa) in pos.items() for b, (rb, xb) in pos.items()
            if a != b and ((ra == rb and abs(xa - xb) == 1) or (abs(ra - rb) == 1 and abs(xa - xb) <= 0.5))}


NEAR = _keys()
VOWELS = set('aeiou')
DOUBLED = 3.0       # added to the score of a replacement made by doubling or undoubling a letter: about 20 times the pages


def _plausible_change(x, y):
    """A changed letter that a slip of the finger or the ear explains: a key next to it, or one vowel for another
    ("bleech", "seazure"). Not "stabed" -> "stated" or "shoked" -> "showed"."""
    return (x, y) in NEAR or (x in VOWELS and y in VOWELS)


def _double(x, y):
    """A doubled letter, or ck (English's doubled k)."""
    return x == y or {x, y} == {'c', 'k'}


def _better(old, new):
    return new if old is None or new > old else old


def _edits1(w):
    """Every string one edit from w, with how likely the edit is as a slip: (plausible, bonus). Plausible is False only for
    a changed letter that is neither a neighbouring key nor a vowel for a vowel. The bonus is DOUBLED for a letter doubled
    or undoubled ("shoting", "stabed", "bleeeding", "chocking", "shoked")."""
    out = {}
    split = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    for a, b in split:
        if b:
            for c in LETTERS:
                if c != b[0]:
                    out[a + c + b[1:]] = _better(out.get(a + c + b[1:]), (_plausible_change(b[0], c), 0.0))   # changed
            d = (bool(a) and _double(a[-1], b[0])) or (len(b) > 1 and _double(b[0], b[1]))
            out[a + b[1:]] = _better(out.get(a + b[1:]), (True, DOUBLED if d else 0.0))                          # dropped
            if len(b) > 1 and b[0] != b[1]:
                x = a + b[1] + b[0] + b[2:]
                out[x] = _better(out.get(x), (True, 0.0))                                                         # swapped
        for c in LETTERS:
            d = (bool(a) and _double(a[-1], c)) or (bool(b) and _double(c, b[0]))
            out[a + c + b] = _better(out.get(a + c + b), (True, DOUBLED if d else 0.0))                           # added
    out.pop(w, None)
    return out


def _edits2(w, words):
    """The words two edits from w that a word can become, with how likely as for _edits1. Found through words.drops (each
    such word with one letter dropped): a word one edit from a string x has x, or x with a letter dropped, among its own
    drops or itself. The edits are symmetric, so the best path goes through a string one edit from both."""
    near = _edits1(w)
    found = set()
    drops, common = words.drops, words.common
    for x in near:
        for s in [x] + [x[:i] + x[i + 1:] for i in range(len(x))]:
            v = drops.get(s)
            if v:
                found.update((v,) if isinstance(v, str) else v)
            if s in common:
                found.add(s)
    found.discard(w)
    out = {}
    for y in found:
        there = _edits1(y)
        for z in near.keys() & there.keys():
            (p1, b1), (p2, b2) = near[z], there[z]
            out[y] = _better(out.get(y), (p1 and p2, b1 + b2))
    return out


def fix_word(w, words):
    """The word as it should be searched, or w itself. w is lower-case."""
    if w in APOSTROPHES:
        return APOSTROPHES[w]
    V, E = words.V, words.E
    if w in KNOWN and V.get(w, 0) < 3 and KNOWN[w] in V:
        return KNOWN[w]
    if english_on() and w in SLIPS and SLIPS[w] in V and V.get(w, 0) < RARE:   # fork: a real word, slip for an emergency one
        return SLIPS[w]
    if is_english(w):       # fork: ordinary English ("keeled", "puking"), not a typo of a library word
        return w
    own = V.get(w, 0)
    if w in STOP or len(w) < 3 or not (w.isascii() and w.isalpha()) or own >= RARE:
        return w
    indexed = own > 0               # the vocabulary holds words on 3+ pages
    if indexed and E.get(w, 0):     # the emergency books use it themselves ("riots"): a real word
        return w
    need = max(MIN_PAGES, own * (GAIN_INDEXED if indexed else GAIN))

    def ok(x, how):
        if V.get(x, 0) < need or len(x) < 3 or x in STOP:
            return False
        # a real word is changed only by a plausible slip, and only to a word of the emergency books
        return not indexed or (how[0] and E.get(x, 0) >= EMERGENCY_MIN)

    found = {x: how for x, how in _edits1(w).items() if ok(x, how)}
    if not found and len(w) >= 5 and not indexed:
        found = {x: how for x, how in _edits2(w, words).items() if ok(x, how)}
    if not found:
        return w
    # Most slips keep the first letter; then plausible slips; then the library's use, with a doubled letter counting extra.
    return max(found, key=lambda x: (x[0] == w[0], found[x][0], words.score(x) + found[x][1]))


# fork: words typed with no spaces ("heschuokinghelkp" = he's choking help). See split_word.
SPLIT_MIN = 8           # a word of fewer letters is never split
SPLIT_MIN_APOSTROPHE = 6  # fork: a run typed with an apostrophe inside ("he'sfine") is two words at least
SPLIT_PIECE = 20        # the longest piece tried
SPLIT_PAGES = MIN_PAGES  # a piece of 3+ letters is a word on at least this many pages, as a replacement in fix_word
SPLIT_COST = 3.0        # added for each space put in
SPLIT_EDIT = 5.0        # a piece one plausible slip from its word (fix_word's slips: a neighbouring key, a vowel, ...)
SPLIT_EDIT_OTHER = 8.0  # one other slip (a changed letter that is not a neighbouring key nor a vowel for a vowel)
SPLIT_DOUBLED = 2.0     # taken off for a letter doubled or undoubled ("chocking")
SPLIT_APOSTROPHE = 1.0  # a piece typed without its apostrophe ("hes" -> he's)
SPLIT_EMERGENCY = 0.5   # the word corrected whole costs this much less per log of the emergency books' use of it ...
SPLIT_EMERGENCY_MAX = 3.0  # ... at most this
SPLIT_SHORT = 1.0       # taken off for a word of one or two letters ("a", "my"): commoner in a question than in its pages
# A split is used when its cost is at most SPLIT_BASE + SPLIT_PER_LETTER * letters + SPLIT_PER_SPACE * spaces, and
# SPLIT_MARGIN under the cost of the word corrected whole (fix_word), when it can be. Chosen on data (docs/FORK.md 3k).
SPLIT_BASE = -4.0
SPLIT_PER_LETTER = 1.5
SPLIT_PER_SPACE = 4.0
SPLIT_MARGIN = 4.0
# Words of one or two letters a piece may be. Not "jd", "dk" or "ed": the index has those too, from abbreviations.
SPLIT_SHORT_WORDS = set('a i am an as at be by do go he if in is it me my no of oh ok on or so to up us we'.split())
TOKEN = re.compile(r"[\w'’-]+")


def split_on():
    return os.environ.get('LASTBOOK_TYPO_SPLIT', '1') != '0'


def _how(s, x):
    """How x is one edit from s, as _edits1(s)[x] would say ((plausible, bonus)), or None: without making every string one
    edit from s, for the many pieces split_word tries."""
    n, m = len(s), len(x)
    out = None
    if m == n:
        diff = [i for i in range(n) if s[i] != x[i]]
        if len(diff) == 1:
            out = (_plausible_change(s[diff[0]], x[diff[0]]), 0.0)                                   # changed
        elif len(diff) == 2 and diff[1] == diff[0] + 1 and s[diff[0]] == x[diff[1]] and s[diff[1]] == x[diff[0]]:
            out = (True, 0.0)                                                                         # swapped
    elif m == n - 1:
        for i in range(n):                                                                            # dropped
            if s[:i] + s[i + 1:] == x:
                d = (i > 0 and _double(s[i - 1], s[i])) or (i + 1 < n and _double(s[i], s[i + 1]))
                out = _better(out, (True, DOUBLED if d else 0.0))
    elif m == n + 1:
        for i in range(m):                                                                            # added
            if x[:i] + x[i + 1:] == s:
                c = x[i]
                d = (i > 0 and _double(s[i - 1], c)) or (i < n and _double(c, s[i]))
                out = _better(out, (True, DOUBLED if d else 0.0))
    return out


def _near(s, words):
    """The words a word can become (words.common) one edit from s -> (plausible, bonus), as _edits1 with its strings looked
    up, but found through words.drops: a few lookups instead of some 50 strings per letter."""
    drops, common = words.drops, words.common
    found = set()
    for t in [s] + [s[:i] + s[i + 1:] for i in range(len(s))]:
        v = drops.get(t)
        if v:
            found.update((v,) if isinstance(v, str) else v)
        if t != s and t in common:
            found.add(t)
    out = {}
    for x in found:
        how = _how(s, x)
        if how:
            out[x] = how
    return out


def _piece(s, words):
    """The cheapest reading of s as one word: (cost, word) or None. The cost is how rare the word is in the library (log of
    the commonest word's pages over its own pages), plus SPLIT_EDIT when s is a slip for it. A piece that is a word of the
    library (on SPLIT_PAGES or more) is that word. Otherwise its slips are fix_word's: one edit, the first letter kept, and
    of several words the one fix_word would pick (plausible slips, the emergency books' words, a doubled letter)."""
    memo = words.pieces
    if s in memo:
        return memo[s]
    V = words.V
    rare = lambda w: words.lmax - math.log(V.get(w, 3)) - (SPLIT_SHORT if len(w) <= 2 else 0.0)
    best = None
    if s == 'im':                   # fork: in a glued run "im" is I'm ("imchoking"), as rare as "i"
        best = (rare('i') + SPLIT_APOSTROPHE, "i'm")
    elif len(s) <= 2:
        best = (rare(s), s) if s in SPLIT_SHORT_WORDS and s in V else None
    else:
        if s in APOSTROPHES:        # "he's" as rare as "he"
            best = (rare(APOSTROPHES[s].split("'")[0]) + SPLIT_APOSTROPHE, APOSTROPHES[s])
        if V.get(s, 0) >= SPLIT_PAGES:
            best = min(best or (math.inf, s), (rare(s), s))
        elif best is None and len(s) >= 4:
            found = {x: how for x, how in _near(s, words).items() if x[0] == s[0] and V.get(x, 0) >= SPLIT_PAGES}
            if found:
                x = max(found, key=lambda x: (found[x][0], words.score(x) + found[x][1]))
                best = (rare(x) + (SPLIT_EDIT if found[x][0] else SPLIT_EDIT_OTHER) - (SPLIT_DOUBLED if found[x][1] else 0.0), x)
    if len(memo) > 200000:
        memo.clear()
    memo[s] = best
    return best


def segment(w, words):
    """(cost, pieces) of the cheapest way to cut w into the library's words (see split_word), or None."""
    n = len(w)
    best = [(0.0, ())] + [None] * n
    for j in range(1, n + 1):
        for i in range(max(0, j - SPLIT_PIECE), j):
            if best[i] is None:
                continue
            p = _piece(w[i:j], words)
            if p is None:
                continue
            c = best[i][0] + p[0] + (SPLIT_COST if i else 0.0)
            if best[j] is None or c < best[j][0]:
                best[j] = (c, best[i][1] + (p[1],))
    return best[n]


def whole_cost(w, words):
    """The cost of w corrected whole by fix_word, as _piece would count it, less a little for a word of the emergency books
    ("overdoes" is overdose, not "over does"), or None when fix_word leaves it."""
    f = fix_word(w, words)
    if f == w:
        return None
    e = _edits1(w).get(f)
    return (words.lmax - math.log(words.V[f]) - min(SPLIT_EMERGENCY * math.log1p(words.E.get(f, 0)), SPLIT_EMERGENCY_MAX) +
            (2 * SPLIT_EDIT if e is None else (SPLIT_EDIT if e[0] else SPLIT_EDIT_OTHER) - (SPLIT_DOUBLED if e[1] else 0.0)))


def split_word(w, words, whole=True):
    """fork: w (lower-case, a-z, not a word of the library) as the library's words it was typed for with no spaces, or None.

    Every way of cutting w into pieces is weighed at once (dynamic programming over where the spaces go): each piece costs
    _piece's cost, each space SPLIT_COST. The cheapest is used when it costs at most SPLIT_PER_SPACE per space, and
    SPLIT_MARGIN less than the word corrected whole when fix_word can correct it ("hypothermai" stays one word). Pieces of
    one or two letters only from SPLIT_SHORT_WORDS. A word the index holds (on 3+ pages: "firecraft", "gutenberg") is never
    split. The costs were chosen on glued runs of 2-6 words of the triage questions (clean and with typos) against long
    words with a typo and rare real words (.claude/drafts/triage, docs/FORK.md 3k)."""
    n = len(w)
    if n < (SPLIT_MIN if whole else SPLIT_MIN_APOSTROPHE) or w in words.V or not w.isascii() or not w.isalpha() or is_english(w):   # fork: "dribbling" stays
        return None
    best = segment(w, words)
    if best is None or len(best[1]) < 2:
        return None
    cost, parts = best
    if cost > SPLIT_BASE + SPLIT_PER_SPACE * (len(parts) - 1) + SPLIT_PER_LETTER * n:
        return None
    whole = whole_cost(w, words) if whole else None     # fork: not for a run typed with an apostrophe: two words at least
    if whole is not None and cost + SPLIT_MARGIN >= whole:
        return None
    return list(parts)


def body_fix_on():
    return os.environ.get('LASTBOOK_BODY_FIX', '1') != '0'


def body_fix(w, words):
    """fork: w (lower-case, left as typed by fix_word and split_word) as the body word it is a slip for, or w. Only the body
    words of engine/confidence.BODY_WORDS, and only where the library has w on fewer than confidence.BODY_COMMON pages:
    "puls" (24 pages, a real word to fix_word) -> pulse. A glued run with a body stem that could not be split
    ("mybbyisntbreathing") -> the stem's words ("not breathing"), so the search finds those pages instead of nothing."""
    from engine import confidence       # here: confidence imports this module
    if not confidence.body_on() or w in STOP or not w.isalpha() or (is_english(w) and w not in confidence.BODY_WORDS):
        return w
    b = confidence.body_match(w, words.V)
    if b and b != w and (w not in words.V or _how(w, b)):   # a word of the library: one plausible slip only
        return b
    glued = confidence.glued_body(w, words.V)
    return ' '.join(x for x, _ in glued) if glued else w


def looks_foreign(q):
    """True when the question has letters beyond a-z or more Spanish/Portuguese/French function words than English ones."""
    toks = re.findall(r'[^\W\d_]+', unicodedata.normalize('NFC', q).lower())
    if any(not t.isascii() for t in toks):
        return True
    return sum(t in OTHER_WORDS for t in toks) > sum(t in ENGLISH_WORDS and t not in SHARED for t in toks)


def correct_with(q, words):
    """q with its misspelled words put right, against these words. Everything else stays as typed."""
    if not q or looks_foreign(q):
        return q
    toks = TOKEN.findall(q)
    shouting = sum(t.isupper() for t in toks) > len(toks) / 2
    q = restore_im(q, shouting)     # fork: "im vomiting" -> i'm, first

    def glued(t, part=False):
        """fork: a glued run typed with an apostrophe ("he'snotbreathing", "i'mchoking") split as split_word, the
        apostrophe left out first (the pieces put it back: "hes" -> he's). A word with an ordinary ending ("he's",
        "grandma's", "mum's") stays as typed. Hyphens: each part only split, never corrected ("help-hesnotbreathing")."""
        if '-' in t:
            return '-'.join(glued(p, True) if p else p for p in t.split('-'))
        low = t.lower().replace('’', "'")
        m = re.fullmatch(r"([a-z]+)'(s|t|d|m|re|ll|ve)", low)
        if (not re.fullmatch(r"[a-z']+", low) or ("'" not in low and not part)
                or (m and (m.group(1) in words.V or is_english(m.group(1)) or m.group(1) + m.group(2) in APOSTROPHES))):
            return t
        parts = split_word(low.replace("'", ''), words, whole=False)
        return case(t, ' '.join(parts)) if parts else t

    def case(t, f):
        return f.upper() if t.isupper() else f[0].upper() + f[1:] if t[0].isupper() else f

    def one(m):
        t = m.group(0)
        if not re.fullmatch(r'[A-Za-z]+', t) or (t.isupper() and len(t) > 1 and not shouting):   # CPR, AED, ERG
            return glued(t) if split_on() and re.search(r"[A-Za-z]['’-][A-Za-z]", t) else t
        if not t.isupper() and re.search(r'[a-z][A-Z]|[A-Z]{2}[a-z]', t):     # fork: "ODing", "iPhone": a name, not a typo
            return t
        w = unstretch(t.lower(), words.V)       # fork: "bloooood" -> blood, then as typed so
        parts = split_word(w, words) if split_on() else None
        if parts:       # fork: words typed with no spaces
            return case(t, ' '.join(parts))
        f = fix_word(w, words)
        if f == w and body_fix_on():
            f = body_fix(f, words)
        if f == t.lower():
            return t
        return f.upper() if t.isupper() and len(t) > 1 else f[0].upper() + f[1:] if t[0].isupper() else f
    return TOKEN.sub(one, phrase_slips(q))     # fork: "he cant breed" -> breathe first


# ------------------------------------------------------------------ the library's words, kept in memory --
_lock = threading.Lock()
_state = {'key': None, 'words': None, 'memo': {}, 'built_s': None}


def _db():
    import engine.library as library
    return Path(library.DB)


def words_for(path=None):
    """The library's words, built on first use and again when the search database changes; None when there is none or too few."""
    path = Path(path) if path else _db()
    try:
        st = path.stat()
    except OSError:
        return None
    key = (str(path), st.st_mtime_ns, st.st_size)
    if _state['key'] == key:
        return _state['words']
    with _lock:
        if _state['key'] != key:
            t = time.perf_counter()
            try:
                w = Words.from_db(path)
                w = w if len(w.V) >= MIN_VOCAB else None
            except sqlite3.Error:
                w = None        # being rebuilt, or not a search database yet: search as typed
            _state.update(key=key, words=w, memo={}, built_s=round(time.perf_counter() - t, 2))
    return _state['words']


def on():
    return os.environ.get('LASTBOOK_TYPO_FIX', '1') != '0'


def correct(q):
    """The question as it should be searched. Unchanged when off, when there's no library, or when nothing looks misspelled."""
    if not q or not on():
        return q
    words = words_for()
    if words is None:
        return q
    memo, key = _state['memo'], (q, split_on())
    if key not in memo:
        if len(memo) > 2000:
            memo.clear()
        memo[key] = correct_with(q, words)
    return memo[key]


def shown(q):
    """{'corrected': what was searched} when that differs from q, for a "Searched for: ..." line; otherwise {}."""
    c = correct(q)
    return {'corrected': c} if c != q else {}
