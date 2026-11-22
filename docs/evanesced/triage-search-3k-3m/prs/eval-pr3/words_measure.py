r"""PR 3: what the typo corrector changes, read-only, no search.

    set LASTBOOK_DATA=<library folder>
    python -B words_measure.py <checkout> <out.json>

- triage.json, issue154.json: clean and typo questions changed by typos.correct.
- lists 1-4: lines with an English word bent (the typed word is in engine/english_words.txt.gz and the corrector changed
  it, not by a split and not by an apostrophe repair), with the English guard on (default) and off
  (LASTBOOK_TYPO_ENGLISH=0, which also turns off the real-word slips and the cutting of repeated letters).
"""
import gzip, json, os, re, sys
from pathlib import Path

code = Path(sys.argv[1])
sys.path.insert(0, str(code))
from engine import typos  # noqa: E402

EN = set(gzip.open(code / 'engine' / 'english_words.txt.gz', 'rt', encoding='utf-8').read().split())
APOS = set(typos.APOSTROPHES.values()) | {"i'm"}
W = typos.words_for()
assert W is not None, 'no library words'
print('vocabulary', len(W.V), 'emergency words', len(W.E), 'built in', typos._state['built_s'], 's', flush=True)


def word_changes(q):
    """[(as typed, split|fix, result)] for each plain word correct_with changes (same order of tries)."""
    out = []
    if not q or typos.looks_foreign(q):
        return out
    toks = typos.TOKEN.findall(q)
    shouting = sum(t.isupper() for t in toks) > len(toks) / 2
    for t in toks:
        if not re.fullmatch(r'[A-Za-z]+', t) or (t.isupper() and len(t) > 1 and not shouting):
            continue
        if not t.isupper() and re.search(r'[a-z][A-Z]|[A-Z]{2}[a-z]', t):
            continue
        w = typos.unstretch(t.lower(), W.V)
        parts = typos.split_word(w, W) if typos.split_on() else None
        if parts:
            out.append((t, 'split', ' '.join(parts)))
            continue
        f = typos.fix_word(w, W)
        if f != t.lower():
            out.append((t, 'fix', f))
    return out


def bent(q):
    return [c for c in word_changes(q) if c[1] != 'split' and c[2] not in APOS and c[0].lower() in EN]


res = {}
ev = code / 'tools' / 'search_eval'
tri = json.load(open(ev / 'data' / 'triage.json', encoding='utf-8'))
clean = [q for t in tri['topics'] for q in t['qs']]
typo = [q for t in tri['topics'] for q in t['typos']]
i154 = json.load(open(ev / 'data' / 'issue154.json', encoding='utf-8'))
cases154 = i154['cases'] if isinstance(i154, dict) else i154
c154 = [c['q'] for c in cases154]
t154 = [c['typo'] for c in cases154]
for name, qs in (('triage clean', clean), ('triage typos', typo), ('154 clean', c154), ('154 typos', t154)):
    ch = [(q, typos.correct_with(q, W)) for q in qs]
    ch = [(a, b) for a, b in ch if a != b]
    res[name] = {'n': len(qs), 'changed': len(ch), 'examples': ch[:400]}
    print(name, len(qs), 'changed', len(ch), flush=True)

for env in ('1', '0'):
    os.environ['LASTBOOK_TYPO_ENGLISH'] = env
    for n in (1, 2, 3, 4):
        rows = [json.loads(l) for l in open(ev / 'lists' / f'list{n}.jsonl', encoding='utf-8') if l.strip()]
        rows = [r for r in rows if 'text' in r]
        b = [(r['text'], bent(r['text'])) for r in rows]
        b = [(t, x) for t, x in b if x]
        changed = sum(typos.correct_with(r['text'], W) != r['text'] for r in rows)
        key = f'list{n} english_guard={"on" if env == "1" else "off"}'
        nos = sum(any(c[0].lower() not in typos.SLIPS for c in x) for _, x in b)
        res[key] = {'lines': len(rows), 'lines_changed': changed, 'lines_bent': len(b), 'lines_bent_not_slips': nos,
                    'words': sorted({f'{c[0].lower()}->{c[2]}' for _, x in b for c in x})}
        print(key, len(rows), 'changed', changed, 'bent', len(b), 'bent other than SLIPS', nos, flush=True)
os.environ.pop('LASTBOOK_TYPO_ENGLISH', None)
json.dump(res, open(sys.argv[2], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
