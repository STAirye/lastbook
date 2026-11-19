"""fork: how likely a search's first result is right, predicted at search time without a model.

A logistic regression over cheap signals of one search, read from the trace assistant.hybrid fills: how many of the
question's words (or their synonyms) the first page and its title carry, the first keyword row's bm25 against how rare
the question's words are, how many pages had every word, whether the first page is from a first-aid or emergency book,
and with meaning-based search the best passage's cosine, how fast the cosines fall, how much the two searches agree and
how many different documents the top 8 come from. Fitted on an invented, labelled test set (362 questions over 159
topics; grouped cross-validation by topic: AUC 0.78 keyword-only, 0.74 hybrid). One set of coefficients for keyword-only
search (what the desktop app ships), one for hybrid. The fit lives outside the repo (.claude/drafts/triage/conf_final.py).
It predicts the first page, not "one of the first 3": a model fitted for the top 3 sits higher (78-90 % of searches have a
right page there), so at the same cut it lets through 2-4 times as many searches whose first 3 pages are all wrong, and
ranks them no better (.claude/drafts/triage/conf_top3.py).

The chat uses it (assistant.chat): below BUTTONS it offers buttons; below UNSURE, on a conversation's own new question, it
asks the person to say more instead of answering from pages that are probably wrong. A question that may be an emergency
(urgent()) gets the pages all the same. An everyday question (one that may not be urgent) gets buttons only below
EVERYDAY_BUTTONS, much lower, and smaller ones (everyday_level()). LASTBOOK_CONF=0 turns it off; LASTBOOK_CONF_BUTTONS,
LASTBOOK_CONF_UNSURE and LASTBOOK_CONF_BUTTONS_EVERYDAY move the thresholds (0 to 1).

fork: when the question's words are not the library's (unknown_words: keyboard mash, a glued question that could not be
split), the search is unsure whatever the model says. LASTBOOK_CONF_UNKNOWN=0 turns that off.
"""
import math
import os
import re

from engine import typos

BUTTONS = 0.60      # below this, the chat offers buttons (0.75 put them on 68 % of keyword-only questions)
UNSURE = 0.25       # below this, the chat asks the person to say more (and still gives the pages if it may be urgent)
EVERYDAY_BUTTONS = 0.30   # an everyday question gets (smaller) buttons only below this; 4 % of the test set's everyday
                          # questions keyword-only, none whose first page was right (0.35: 10 %, 2 right ones)

# Coefficients on the raw signals of features(): p = 1 / (1 + exp(-(bias + sum(w * signal)))).
MODELS = {
    'keyword': {'bias': -3.6222, 'cover1': 2.6573, 'title1': 2.3746, 'kw_top_per_idf': 0.4326, 'idf_mean': 0.2656,
                'strict': 0.0508, 'emerg1': 0.8878},
    'hybrid': {'bias': -2.7284, 'cos1': 8.565, 'cos_drop': -12.2606, 'overlap': 1.1072, 'all1': 1.4529, 'title1': 2.0129,
               'docs': -3.2324, 'strict': 0.2002, 'emerg1': 0.5764},
}

# The library's first-aid and emergency books, by title (as engine/typos.EMERGENCY_TITLES). The financial one is not one.
EMERGENCY_TITLE = re.compile(r"first aid|emergency care|resuscitation|where there is no doctor|emergency response guidebook"
                             r"|fire safety|are you ready|cert basic|emergency medic|life support|wilderness medic", re.I)
NOT_EMERGENCY_TITLE = re.compile(r"financial", re.I)

# Words that may mean an emergency. Wide on purpose: a match only means the pages are never held back when the search
# is unsure, so an everyday "cut" or "car" costs nothing. assistant.DANGER is the narrow list that changes the search.
URGENT = re.compile(
    r"\b(breath\w*|chok\w*|unconscious|unresponsive|collaps\w*|pass(ed)? out|faint\w*|wake|pulse|cpr"
    r"|bleed\w*|blood\w*|spurt\w*|wound\w*|stab\w*|shot|shoot\w*|gun\w*|knife|impal\w*|amputat\w*|severed|cut\w*"
    r"|drown\w*|swept|current|flood\w*|ice|submerg\w*|sinking|electr\w*|shock\w*|lightning|lightening|struck|live wire"
    r"|power ?lines?|burn\w*|scald\w*|fire|flames?|smok\w*|spark\w*|wildfire\w*|gas|fumes?|carbon monoxide|generator"
    r"|explo\w*|radiation|fallout|nuclear|poison\w*|swallow\w*|drank|ate|pills?|medicine\w*|medication\w*|overdos\w*"
    r"|bleach|chemicals?|kerosene|bitten|bite|snake|sting|stung|allerg\w*|swell\w*|anaphyla\w*|asthma|wheez\w*|lips?"
    r"|blue|seizure\w*|convuls\w*|fit|shaking|foaming|stroke|droop\w*|slurr\w*|speak|face|chest|heart|cardiac|diabet\w*"
    r"|sugar|confus\w*|not making sense|fell|fall(en)?|roof|can'?t move|cannot move|not moving|paralys\w*|neck|spine"
    r"|spinal|head|skull|trapped|pinned|crush\w*|rubble|buried|landslide|mud|avalanche|earthquake|tsunami|tornado"
    r"|hurricane|labou?r|birth|water broke|pregnan\w*|contractions|newborn|baby|infant|miscarr\w*|suicid\w*"
    r"|kill (him|her|my|them|your)sel\w*|self.harm|live anymore|end (it|my life)|attack\w*|intruder|break(ing)?|braking|riot\w*"
    r"|hostage|bomb|hypotherm\w*|frostbite|shiver\w*|heat ?stroke|stuck|nail|pale|sweaty|accident\w*|injur\w*|hurt\w*"
    r"|pain\w*|weak\w*|numb|broken|fractur\w*|bone|sleepy|drowsy|vomit\w*|fever\w*|rash|car|crash\w*|vehicle|ambulance|hospital|emergency|dying|dead|help)\b",
    re.I)


# fork: the injury words of URGENT, for server.PHRASES. A how-to phrase ("light a fire", "treat water") is not used when the
# question also names an injury or a danger to the body: "light a fire to keep him warm with hypothermia" is about
# hypothermia, not firecraft. Not URGENT itself: its fire, smoke, gas, flood, baby and cut would also stop "how do i light a
# campfire", "make the water safe for a baby's formula" and "cut kindling". A bare "burn" or "smoke" is how a fire is
# made too ("wood that burns longer", "a fire without smoke"), so only a burn on someone and smoke breathed in count.
# Added to URGENT's words: lungs, monoxide alone, inhaled, blisters, electrocuted, coughing.
INJURY = re.compile(
    r"\b(breath\w*|chok\w*|unconscious|unresponsive|collaps\w*|pass(ed)? out|faint\w*|pulse|cpr|bleed\w*|blood\w*"
    r"|wound\w*|stab\w*|amputat\w*|drown\w*|submerg\w*|lungs?|cough\w*|electrocut\w*|shock\w*|live wire|lightning"
    r"|burn(ed|t)|scald\w*|blister\w*|inhal\w*|carbon monoxide|monoxide|fumes|poison\w*|swallow\w*|overdos\w*"
    r"|bitten|stung|anaphyla\w*|seizure\w*|convuls\w*|hypotherm\w*|frostbit\w*|shiver\w*|heat ?stroke|injur\w*|hurt\w*"
    r"|fractur\w*|caught fire|on fire|in flames|fell|fallen|dying)\b"
    r"|\b(a|the|my|his|her|their|bad|first|second|third)[ -](degree )?burns?\b|\bburns? (on|to)\b",
    re.I)


def injury(text):
    """True when the text names an injury or a danger to the body (INJURY): then server.PHRASES' how-to phrases are not used."""
    return bool(INJURY.search((text or '').replace('’', "'")))


# fork: body signs. A question that names one (no pulse, not breathing, blue lips, unconscious, choking, bleeding, a
# seizure, chest pain, not moving, cold and clammy) always gets an answer from its pages, never only "help me help you",
# and counts as urgent (assistant.turn_hits, assistant.chat). Matched one slip away too, and two for long words, the first
# letter kept, on a word the library itself has on fewer than BODY_COMMON pages: "puls" (24 pages, so typo correction
# leaves it) is pulse, but "bloom", "breeding", "pulses" and "chose" are words of their own. A one-slip match must be a
# plausible slip (engine/typos.py: a key next to it, a vowel for a vowel, a letter dropped, added or swapped), so "chore"
# is not choke nor "blond" blood. In a glued run the library doesn't hold ("mybbyisntbreathing") the stems of BODY_GLUED
# are looked for inside it. A subset of URGENT, with the slips: it narrows nothing. LASTBOOK_BODY_SIGNS=0 turns it off.
BODY_WORDS = {
    'pulse': 'pulse', 'heartbeat': 'pulse',
    'breathing': 'breathing', 'breathe': 'breathing', 'breath': 'breathing', 'breathes': 'breathing', 'breathed': 'breathing',
    'unconscious': 'unconscious', 'unresponsive': 'unconscious', 'collapsed': 'unconscious',
    'choking': 'choking', 'choke': 'choking', 'choked': 'choking',
    'bleeding': 'bleeding', 'bleed': 'bleeding', 'blood': 'bleeding',
    'seizure': 'seizure', 'seizures': 'seizure', 'convulsing': 'seizure', 'convulsions': 'seizure',
    'clammy': 'cold and clammy',
}
BODY_PHRASES = {
    'blue': r"\b(lips?|skin|face|fingers|he|she|baby) (is |are |was |were |look |looks |gone |going |turned |turning )*"
            r"(blue|grey|gray)\b|\b(turn(ed|ing)?|gone|going|went) (blue|grey|gray)\b|\bblue (lips?|skin|face)\b",
    'unconscious': r"\b(passed|blacked) out\b|\bwon'?t wake( up)?\b|\bnot waking\b|\bfainted\b",
    'chest pain': r"\bchest\b.{0,20}\b(pain\w*|hurts?|hurting|tight\w*|pressure|crushing)\b|\b(pain|pressure) in (his|her|my|the) chest\b",
    'not moving': r"\b(not|isn'?t|stopped|won'?t|can'?t|cannot) mov(e|ing)\b|\b(limp|floppy)\b",
    'seizure': r"\b(having|had|has|is|was|keeps?) (a )?fit(s|ting)?\b",
    'cold and clammy': r"\bcold and (wet|clammy|sweaty)\b|\b(wet|sweaty) and cold\b",
}
BODY_PHRASES = {k: re.compile(v, re.I) for k, v in BODY_PHRASES.items()}
BODY_COMMON = 50    # a word on this many pages or more is a word of its own: only an exact body word counts
# Stems looked for inside a glued run (a word of 8+ letters the library doesn't hold), in order, and the words a search
# gets for them (typos.correct_with, LASTBOOK_BODY_FIX). The first of a sign wins: "isntbreath" before "breath".
BODY_GLUED = [(re.compile(rx), words, sign) for rx, words, sign in (
    (r"(not|isnt|cant|stopped|wont)breath", 'not breathing', 'breathing'), (r"breath", 'breathing', 'breathing'),
    (r"nopulse", 'no pulse', 'pulse'), (r"pulse", 'pulse', 'pulse'), (r"heartbeat", 'heartbeat', 'pulse'),
    (r"bleed", 'bleeding', 'bleeding'), (r"blood", 'blood', 'bleeding'), (r"chok", 'choking', 'choking'),
    (r"seizur", 'seizure', 'seizure'), (r"convuls", 'convulsions', 'seizure'), (r"unconscious", 'unconscious', 'unconscious'),
    (r"unrespons", 'unresponsive', 'unconscious'), (r"coll?aps", 'collapsed', 'unconscious'),
    (r"passedout", 'passed out', 'unconscious'), (r"chestpain", 'chest pain', 'chest pain'),
    (r"notmoving", 'not moving', 'not moving'), (r"(isblue|turningblue|bluelips|lipsblue|lipsareblue)", 'blue lips', 'blue'),
)]


def body_on():
    return os.environ.get('LASTBOOK_BODY_SIGNS', '1') != '0'


def _osa(a, b):
    """Edits from a to b: letters dropped, added, changed, or two next to each other swapped."""
    d = [[i + j if not i * j else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def body_match(t, V=None):
    """The word of BODY_WORDS that the word t is, or is a slip for (see above), or None."""
    if t in BODY_WORDS:
        return t
    if len(t) < 4 or not t.isalpha() or (V or {}).get(t, 0) >= BODY_COMMON or t in typos.ENGLISH_WORDS:
        return None
    best = None
    for b in BODY_WORDS:
        n = 1 if len(b) <= 6 else 2
        if b[0] != t[0] or abs(len(b) - len(t)) > n:
            continue
        e = _osa(t, b)
        if (e == 1 and (typos._how(t, b) or (False,))[0]) or 1 < e <= n:
            if best is None or e < best[0]:
                best = (e, b)
    return best and best[1]


def body_word(t, V=None):
    """The sign of BODY_WORDS that the word t is, or is a slip for, or None."""
    b = body_match(t, V)
    return BODY_WORDS[b] if b else None


def glued_body(t, V=None):
    """[(search words, sign)] for the stems of BODY_GLUED inside t, a glued run of 8+ letters the library doesn't hold."""
    if len(t) < 8 or not t.isalpha() or (V or {}).get(t, 0):
        return []
    out, signs = [], set()
    for rx, words, sign in BODY_GLUED:
        if sign not in signs and rx.search(t):
            out.append((words, sign))
            signs.add(sign)
    return out


def body_signs(*texts):
    """fork: the body signs (see BODY_WORDS) that any of the texts names, as a set of names; empty when off."""
    if not body_on():
        return set()
    V, _ = _words()
    out = set()
    for text in texts:
        text = (text or '').lower().replace('’', "'")
        if not text:
            continue
        out |= {k for k, rx in BODY_PHRASES.items() if rx.search(text)}
        for t in re.findall(r"[a-z]+", text.replace("'", '')):
            s = body_word(t, V)
            if s:
                out.add(s)
            else:
                out |= {sign for _, sign in glued_body(t, V)}
    return out


def on():
    return os.environ.get('LASTBOOK_CONF', '1') != '0'


def _env(name, default):
    try:
        v = float(os.environ.get(name, ''))
        return v if 0 <= v <= 1 else default
    except ValueError:
        return default


def thresholds():
    """(buttons, unsure): the cut-offs in use, from the environment when set there."""
    return _env('LASTBOOK_CONF_BUTTONS', BUTTONS), _env('LASTBOOK_CONF_UNSURE', UNSURE)


def everyday_cut():
    """The buttons cut for an everyday question, from the environment when set there."""
    return _env('LASTBOOK_CONF_BUTTONS_EVERYDAY', EVERYDAY_BUTTONS)


def everyday_level(p):
    """'sure' | 'buttons' | 'unsure' for an everyday question of probability p: buttons below everyday_cut(), and the
    request to say more below UNSURE only where that is under the buttons cut too (never without the buttons)."""
    cut, unsure = everyday_cut(), thresholds()[1]
    return 'unsure' if p < min(unsure, cut) else 'buttons' if p < cut else 'sure'


def urgent(*texts):
    """True when any of the texts (the question as typed, as searched, its English words) may be about an emergency: a word
    of URGENT, or a body sign (body_signs: "he has no puls", "mybbyisntbreathing")."""
    return any(URGENT.search((t or '').replace('’', "'")) for t in texts) or bool(body_signs(*texts))


def _words():
    w = typos.words_for()
    return (w.V, max(w.V.values())) if w and w.V else ({}, 0)


def _df(term, V):
    """Pages that have the term: a phrase is on at most as many pages as its rarest word."""
    return min((V.get(p, 0) for p in re.findall(r"[a-z0-9]+", term.lower())), default=0)


def _has(text, group):
    return any(re.search(r'(?<![a-z0-9])' + re.escape(t.lower()) + r'(?![a-z0-9])', text) for t in group)


def _emergency_book(h):
    t = h.get('title') or ''
    return bool(EMERGENCY_TITLE.search(t)) and not NOT_EMERGENCY_TITLE.search(t)


def features(hits, trace):
    """The signals of one search: hits as assistant.hybrid returned them (the top 8), trace as it filled it. Plain numbers."""
    V, N = _words()
    groups = trace.get('groups') or []
    # how rare each word group is: a group matches a page with any of its words, so its pages are its commonest word's
    idf = [math.log((N + 1) / (max((_df(t, V) for t in g), default=0) + 1)) if N else 0.0 for g in groups]
    b = [-x for x in (trace.get('bm25') or [])]          # SQLite's bm25 is negative: bigger is better here
    cover = lambda t: sum(_has(t, g) for g in groups) / len(groups) if groups else 0.0
    first = ((hits[0].get('title') or '') + ' ' + (hits[0].get('excerpt') or '')).lower() if hits else ''
    f = {
        'cover1': cover(first),
        'all1': float(bool(groups) and cover(first) == 1.0),
        'title1': cover((hits[0].get('title') or '').lower()) if hits else 0.0,
        'kw_top_per_idf': b[0] / sum(idf) if b and sum(idf) > 0 else 0.0,
        'idf_mean': sum(idf) / len(idf) if idf else 0.0,
        'strict': math.log1p(trace.get('strict') or 0),
        'emerg1': float(bool(hits) and _emergency_book(hits[0])),
        'docs': len({h.get('doc_id') for h in hits[:8]}) / 8,
    }
    if trace.get('semantic'):
        cos, kwk, semk = trace.get('cos') or [], trace.get('kw_keys') or [], trace.get('sem_keys') or []
        f.update(cos1=cos[0] if cos else 0.0, cos_drop=(cos[0] - cos[min(7, len(cos) - 1)]) if cos else 0.0,
                 overlap=len({tuple(x) for x in kwk} & {tuple(x) for x in semk}) / 8)
    return f


def mode(trace):
    return 'hybrid' if trace.get('semantic') else 'keyword'


def probability(f, model):
    z = model.get('bias', 0.0) + sum(w * f.get(k, 0.0) for k, w in model.items() if k != 'bias')
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, z))))


# Not content words either, besides typos.ENGLISH_WORDS (the search's stop words): as assistant._SHORT.
NOT_CONTENT = set('he she him her his hers oh yes ok'.split())


def unknown_words(q):
    """fork: True when the question as searched (its misspellings put right and glued words split, engine/typos.py) has no
    content word at all, or when most of its content words are not words the library uses (on fewer than 3 pages): keyboard
    mash ("jdjdk", "asdfgh"), or a glued question the splitting could not take apart. The fitted model has no such signal
    (in the test set it was always 0), and a few chance matches can give mash a middling p. False without the library's
    words, for a question in another language (its words are not the library's), and for words with digits (EU2200i)."""
    if not q or not unknown_on():
        return False
    V, _ = _words()
    if not V or typos.looks_foreign(q):
        return False
    toks = re.findall(r"[a-z0-9]+", q.lower().replace('’', "'").replace("'", ' '))
    if any(re.search(r'\d', t) for t in toks):
        return False
    content = [t for t in toks if t not in typos.ENGLISH_WORDS and t not in NOT_CONTENT and len(t) > 1]
    return not content or sum(t not in V for t in content) * 2 > len(content)


def unknown_on():
    return os.environ.get('LASTBOOK_CONF_UNKNOWN', '1') != '0'


def estimate(hits, trace):
    """{'p': 0..1, 'mode': 'keyword' | 'hybrid', 'level': 'sure' | 'buttons' | 'unsure'} for one search. When the question's
    words are not the library's (unknown_words, on the question as searched: trace['q']), p is capped under both unsure cuts
    (UNSURE and the everyday one), whatever the fitted model says: the chat then asks for more words, with buttons, and
    still gives the pages if the question may be urgent. 'unknown_words': True and 'p_fitted' then say so."""
    m = mode(trace)
    p = probability(features(list(hits)[:8], trace), MODELS[m])
    buttons, unsure = thresholds()
    out = {'p': round(p, 3), 'mode': m}
    if unknown_words(trace.get('q')):
        cap = max(0.0, min(unsure, everyday_cut()) - 0.05)
        out.update(p=round(min(p, cap), 3), p_fitted=round(p, 3), unknown_words=True)
        p = out['p']
    out['level'] = 'unsure' if p < unsure else 'buttons' if p < buttons else 'sure'
    return out
