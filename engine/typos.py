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
# Typed without the apostrophe. Not "im" (intramuscular), "its", "were", "well", "ill" or "lets": those are words.
APOSTROPHES = {'isnt': "isn't", 'cant': "can't", 'wont': "won't", 'dont': "don't", 'doesnt': "doesn't", 'didnt': "didn't",
               'wasnt': "wasn't", 'arent': "aren't", 'couldnt': "couldn't", 'hes': "he's", 'shes': "she's",
               'thats': "that's", 'someones': "someone's", 'theyre': "they're"}
# Well-known misspellings of emergency words that edits cannot reach, or reach wrongly. Each is used only when the right
# word is in the library. "asma" is also asthma in Spanish and Portuguese.
KNOWN = {'asma': 'asthma', 'azma': 'asthma', 'asthama': 'asthma', 'nemonia': 'pneumonia', 'numonia': 'pneumonia',
         'newmonia': 'pneumonia', 'pnemonia': 'pneumonia', 'excema': 'eczema', 'exema': 'eczema',
         'diarea': 'diarrhea', 'diarrea': 'diarrhea', 'diarhea': 'diarrhea', 'diareah': 'diarrhea', 'diahrea': 'diarrhea'}
# A question in another language is not corrected into English. Common function words of Spanish, Portuguese and French that
# are not English words (as in assistant.OTHER_WORDS, which decides when the local AI writes English search words).
OTHER_WORDS = set('el la los las del al en y que es un una por para con sin pero como muy mi mis tu su sus se lo le les nos '
                  'yo este esta esto cuando tengo tiene necesito puedo hacer agua fuego nao um uma com isso voce tem '
                  'preciso fazer des du et est avec pas je comment pourquoi vous nous eau'.split())
ENGLISH_WORDS = STOP | set('am been were has had about after before out'.split())
# The library's own first-aid and emergency books, found by title. The financial "first aid kit" is not one.
EMERGENCY_TITLES = ('title:("first aid" OR "emergency care" OR resuscitation OR "where there is no doctor" OR '
                    '"emergency response guidebook" OR "fire safety" OR "are you ready" OR "cert basic") NOT title:financial')


class Words:
    """The library's words: pages per term (V) and how often the emergency books use each word (E)."""

    def __init__(self, vocab, emergency=None):
        self.V, self.E = vocab, emergency or {}
        self.common = {t for t, n in vocab.items() if n >= MIN_PAGES and len(t) >= 3}    # what a word can become
        self._drops = None

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


TOKEN = re.compile(r"[\w'’-]+")


def looks_foreign(q):
    """True when the question has letters beyond a-z or more Spanish/Portuguese/French function words than English ones."""
    toks = re.findall(r'[^\W\d_]+', unicodedata.normalize('NFC', q).lower())
    if any(not t.isascii() for t in toks):
        return True
    return sum(t in OTHER_WORDS for t in toks) > sum(t in ENGLISH_WORDS for t in toks)


def correct_with(q, words):
    """q with its misspelled words put right, against these words. Everything else stays as typed."""
    if not q or looks_foreign(q):
        return q
    toks = TOKEN.findall(q)
    shouting = sum(t.isupper() for t in toks) > len(toks) / 2

    def one(m):
        t = m.group(0)
        if not re.fullmatch(r'[A-Za-z]+', t) or (t.isupper() and len(t) > 1 and not shouting):   # CPR, AED, ERG
            return t
        f = fix_word(t.lower(), words)
        if f == t.lower():
            return t
        return f.upper() if t.isupper() and len(t) > 1 else f[0].upper() + f[1:] if t[0].isupper() else f
    return TOKEN.sub(one, q)


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
    memo = _state['memo']
    if q not in memo:
        if len(memo) > 2000:
            memo.clear()
        memo[q] = correct_with(q, words)
    return memo[q]


def shown(q):
    """{'corrected': what was searched} when that differs from q, for a "Searched for: ..." line; otherwise {}."""
    c = correct(q)
    return {'corrected': c} if c != q else {}
