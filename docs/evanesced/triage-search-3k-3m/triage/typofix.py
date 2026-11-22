"""No-model typo correction against the library's own words, and what it does to search.

    python -I -X utf8 typofix.py SEARCH_DB VOCAB_CACHE OUT.json NAME=URL [NAME=URL ...]

Vocabulary: every term in the keyword index (FTS5 vocab) found in 3 or more pages, with its page count.
A word is corrected when it is not a stop word and appears in fewer than 20 pages: the most common vocabulary word one
edit away (letter dropped, added, changed or two swapped), else two edits away, if that word is at least 50 times more
common. The same correction runs on the clean questions too, to see whether it breaks anything.
"""
import json, math, re, sqlite3, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cases import cases  # noqa: E402
from score import agg, score, top  # noqa: E402

STOP = set('a an and are as at be but by can do does for from get got have help how i if in into is it its me my need '
           'no not of on or our please should so some that the their them then there these they this to up us was we '
           'what when where which who why will with without you your'.split())
# typed without the apostrophe: put it back rather than "correct" the word
APOS = {'isnt': "isn't", 'cant': "can't", 'wont': "won't", 'dont': "don't", 'doesnt': "doesn't", 'hes': "he's",
        'shes': "she's", 'im': "i'm", 'didnt': "didn't", 'wasnt': "wasn't", 'someones': "someone's", 'thats': "that's"}
LETTERS = 'abcdefghijklmnopqrstuvwxyz'
RARE, GAIN = 20, 50


def vocab(db, cache):
    cache = Path(cache)
    if cache.exists():
        return json.loads(cache.read_text(encoding='utf-8'))
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    con.execute("CREATE VIRTUAL TABLE temp.v USING fts5vocab(main, pages, row)")
    v = {t: d for t, d in con.execute("SELECT term, doc FROM temp.v WHERE doc >= 3") if re.fullmatch(r'[a-z]{2,}', t)}
    cache.write_text(json.dumps(v), encoding='utf-8')
    return v


EMERG_TITLES = r"first aid|emergency care|\bBEC\b|resuscitation|where there is no doctor|emergency response guidebook|fire safety|are you ready|cert basic"


def emergency_vocab(db, cache):
    """Word counts in the first-aid and emergency books of the library, so a correction prefers their words.
    Taken from the library, not from the test questions."""
    cache = Path(cache)
    if cache.exists():
        return json.loads(cache.read_text(encoding='utf-8'))
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    from collections import Counter
    c = Counter()
    for (body,) in con.execute("SELECT body FROM pages WHERE doc_id IN (SELECT DISTINCT doc_id FROM pages WHERE title LIKE '%first aid%' "
                               "OR title LIKE '%emergency care%' OR title LIKE 'BEC %' OR title LIKE '%resuscitation%' "
                               "OR title LIKE '%where there is no doctor%' OR title LIKE '%emergency response guidebook%' "
                               "OR title LIKE '%fire safety%' OR title LIKE '%are you ready%' OR title LIKE '%cert basic%')"):
        c.update(re.findall(r'[a-z]{3,}', (body or '').lower()))
    v = {k: n for k, n in c.items() if n >= 3}
    cache.write_text(json.dumps(v), encoding='utf-8')
    return v


E = {}


def edits1(w):
    s = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    return ({a + b[1:] for a, b in s if b} | {a + b[1] + b[0] + b[2:] for a, b in s if len(b) > 1} |
            {a + c + b[1:] for a, b in s if b for c in LETTERS} | {a + c + b for a, b in s for c in LETTERS})


def correct_word(w, V):
    if w in APOS:
        return APOS[w]
    if w in STOP or len(w) < 3 or not w.isalpha() or V.get(w, 0) >= RARE:
        return w
    own = V.get(w, 0)
    c1 = [x for x in edits1(w) if x in V]
    if not c1:
        c1 = list({y for x in edits1(w) for y in edits1(x) if y in V}) if len(w) >= 5 else []
    if not c1:
        return w
    c1 = [x for x in c1 if V[x] >= max(1, own) * GAIN]
    if not c1:
        return w
    # most typos keep the first letter; words of the emergency books first; then how common the word is
    best = max(c1, key=lambda x: (x[0] == w[0], math.log1p(E.get(x, 0)) * 2 + math.log(V[x])))
    return best


def correct(q, V):
    return re.sub(r"[A-Za-z']+", lambda m: correct_word(m.group(0).lower(), V) if "'" not in m.group(0) else m.group(0), q)


def main():
    db, cache, out = sys.argv[1], sys.argv[2], sys.argv[3]
    servers = dict(a.split('=', 1) for a in sys.argv[4:])
    t = time.time(); V = vocab(db, cache); print('vocabulary', len(V), 'terms', round(time.time() - t, 1), 's', flush=True)
    E.update(emergency_vocab(db, str(cache).replace('.json', '-emergency.json')))
    print('emergency-book words', len(E), flush=True)
    cs = cases()
    fixes = {c['q']: correct(c['q'], V) for c in cs}
    res = {'vocab': len(V), 'changed_typo': {q: f for q, f in fixes.items() if f.lower() != q.lower() and any(c['q'] == q and c['typo_of'] for c in cs)},
           'changed_clean': {q: f for q, f in fixes.items() if f.lower() != q.lower() and any(c['q'] == q and not c['typo_of'] for c in cs)},
           'by_server': {}}
    print('typo questions changed', len(res['changed_typo']), '| clean questions changed', len(res['changed_clean']), flush=True)
    for name, base in servers.items():
        rows = []
        for c in cs:
            hits, _ = top(base, fixes[c['q']])
            r = score(c, hits)
            r.update(q=c['q'], fixed=fixes[c['q']], topic=c['topic'], colour=c['colour'], typo=bool(c['typo_of']), counter=bool(c['not_first']))
            rows.append(r)
        s = {'typos_fixed': agg([r for r in rows if r['typo']]), 'clean_fixed': agg([r for r in rows if not r['typo']])}
        res['by_server'][name] = {'summary': s, 'rows': rows}
        print(name, json.dumps(s), flush=True)
    json.dump(res, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
