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
(urgent()) gets the pages all the same. LASTBOOK_CONF=0 turns it off; LASTBOOK_CONF_BUTTONS and LASTBOOK_CONF_UNSURE
move the thresholds (0 to 1).
"""
import math
import os
import re

from engine import typos

BUTTONS = 0.60      # below this, the chat offers buttons (0.75 put them on 68 % of keyword-only questions)
UNSURE = 0.25       # below this, the chat asks the person to say more (and still gives the pages if it may be urgent)

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


def urgent(*texts):
    """True when any of the texts (the question as typed, as searched, its English words) may be about an emergency."""
    return any(URGENT.search((t or '').replace('’', "'")) for t in texts)


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


def estimate(hits, trace):
    """{'p': 0..1, 'mode': 'keyword' | 'hybrid', 'level': 'sure' | 'buttons' | 'unsure'} for one search."""
    m = mode(trace)
    p = probability(features(list(hits)[:8], trace), MODELS[m])
    buttons, unsure = thresholds()
    return {'p': round(p, 3), 'mode': m, 'level': 'unsure' if p < unsure else 'buttons' if p < buttons else 'sure'}
