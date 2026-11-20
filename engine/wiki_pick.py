"""fork: the encyclopedia articles for Chat's first results, picked by their best section.

Upstream (1.1.13) sends the first INITIAL_CHARS (2,000) characters of the top 3 encyclopedia hits for the raw question.
Measured on the fork's 253 clean test questions over the MDWiki, Appropedia and Wikibooks files
(.claude/drafts/encyclopedia/): the median article is 28,000 characters, 136 of 752 are over 100,000, and whole books
saved as one article ("Mirad Grammar/print version", 1.35 MB; "US History/Print version") came first for "my toddler
drank bleach" and "my eyes sting from wildfire smoke", as whole books saved as one web page did in library search
(engine/sections.py). And the words a useful answer needs were in the first 2,000 characters for only 259 of the 622
articles that held them.

So here, as engine/sections.py does for long web pages:
- the encyclopedias' own search gets the question's content words (server.STOP dropped: "my" and "has" matched every
  book), and more candidates (PER_FILE per file);
- print and printable versions of whole books are skipped (each chapter is its own article too), and so are articles
  bigger than MAX_BYTES;
- each candidate is cut into sections of about SECTION characters (sections.cut); an article scores by its best
  section's share of the question's words (a word matches by its first STEM letters, so "burns" finds "burned"), plus a
  little for words in its title; ties keep the encyclopedia's own order;
- the excerpt is the part of that best section where the words are (encyclopedias.pick_section), not the article's start.
Any failure falls back to upstream's search (the caller's).
"""
import re

from engine import encyclopedias, sections
from engine.typos import STOP as LIBRARY_STOP

# server.STOP plus the small words every book holds, which the library's own search keeps (they rank its pages fine)
STOP = LIBRARY_STOP | set('am been were has had he she his her him hers it they just now very really about after before '
                          'out all any one would could also than too much many off over'.split())
PER_FILE = 6
SECTION = sections.SECTION
MAX_BYTES = 800_000
STEM = 5
TITLE_WEIGHT = 0.25
PRINT = re.compile(r'/(print(able)?[ _]version|print)$|[ _]\(print version\)$', re.I)


def words_of(q):
    """The question's content words, in order, once each."""
    out = []
    for w in re.findall(r"[a-z0-9]+(?:'[a-z]+)?", (q or '').lower()):
        w = w.split("'")[0]
        if len(w) >= 3 and w not in STOP and w not in out:
            out.append(w)
    return out


def _pattern(w):
    """A word's start: its ending (-s, -es, -ed, -ing) dropped, at most STEM letters ("burns" and "burned": "burn")."""
    for end in ('ing', 'ed', 'es', 's'):
        if w.endswith(end) and len(w) - len(end) >= 3:
            w = w[:-len(end)]
            break
    return re.compile(r'\b' + re.escape(w[:STEM]), re.I)


def best_section(text, pats):
    """(share of the words in the best section, that section's text). Earlier sections win ties."""
    best = (-1.0, '')
    for _, sec in sections.cut(sections.norm_ws(text), SECTION):
        n = sum(1 for p in pats if p.search(sec))
        if n > best[0] * len(pats):
            best = (n / len(pats), sec)
            if n == len(pats):
                break
    return best


def _size(arc, article):
    try:
        return int(encyclopedias._follow(arc.get_entry_by_path(article)).get_item().size)
    except Exception:
        return 0


def pick(q, limit=encyclopedias.INITIAL_LIMIT, excerpt=encyclopedias.INITIAL_CHARS, root=None, opener=None):
    """Up to `limit` encyclopedia hits for q (the dicts of encyclopedias.search), each with the best part of its best
    section as 'excerpt'. Raises what encyclopedias.search raises; the caller falls back."""
    words = words_of(q)
    if not words:
        return []
    query = ' '.join(words)
    pats = [_pattern(w) for w in words]
    cands = encyclopedias.search(query, per_file=PER_FILE, limit=encyclopedias.SEARCH_LIMIT, root=root, read_text=False,
                                 excerpt=0)
    opener = opener or encyclopedias._open_archive
    scored = []
    for rank, h in enumerate(cands):
        if PRINT.search(h['article']) or PRINT.search(h.get('title') or ''):
            continue
        try:
            arc = opener(encyclopedias.zim_path(h['zim'], root))
        except Exception:
            continue
        if _size(arc, h['article']) > MAX_BYTES:
            continue
        got = encyclopedias.entry_text(arc, h['article'], cap=None)
        if not got or not got[1]:
            continue
        title, text = got
        share, sec = best_section(text, pats)
        if share <= 0:
            continue
        in_title = sum(1 for p in pats if p.search(title)) / len(pats)
        scored.append((-(share + TITLE_WEIGHT * in_title), rank, dict(h, title=title,
                                                                      excerpt=encyclopedias.pick_section(sec, query, excerpt))))
    scored.sort(key=lambda t: t[:2])
    return [h for _, _, h in scored[:limit]]
