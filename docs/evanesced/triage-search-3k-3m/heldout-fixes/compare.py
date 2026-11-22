r"""Before (4ea2d9f) vs after (fork/heldout-fixes): the held-out list 1 (heldout_eval.py runs) and the in-sample sets
(insample_eval.py runs).  python -B -X utf8 compare.py HO_BEFORE HO_AFTER INS_BEFORE INS_AFTER [label]
Measurement only."""
import collections, gzip, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EN = set(gzip.open(r'D:\git\lastbook\.claude\worktrees\heldout-fixes\engine\english_words.txt.gz', 'rt', encoding='utf-8').read().split())
APOS = {"isn't", "can't", "won't", "don't", "doesn't", "didn't", "wasn't", "aren't", "couldn't", "he's", "she's", "that's",
        "someone's", "they're"}
CAT = [('pulse', r'pulse|heartbeat|cardiac arrest'), ('breathing', r'breath|gasp'), ('blue', r'\bblue\b|grey skin'),
       ('unconscious', r'unresponsive|unconscious|collapsed|consciousness|hard to wake|fainted|fainting'),
       ('choking', r'chok|object in throat'), ('bleeding', r'bleed|(?<!high )(?<!low )blood(?! pressure| sugar)|spurting'),
       ('seizure', r'seizure'), ('chest pain', r'chest (pain|pressure|tightness|discomfort)'),
       ('not moving', r'floppy|\blimp\b|cannot move'), ('cold and clammy', r'clammy')]
cats = lambda signs: sorted({c for s in signs for c, rx in CAT if re.search(rx, s)})
load = lambda p: json.load(open(p, encoding='utf-8'))['rows']
WITHHELD = ('ask', 'ask (danger, nothing found)', 'ask (nothing found)')


def pct(a, b):
    return f'{a}/{b} ({100 * a / b:.0f}%)' if b else '0/0'


def heldout(R):
    red = [r for r in R if r['triage'] == 'red']
    yel = [r for r in R if r['triage'] == 'yellow']
    grn = [r for r in R if r['triage'] == 'green']
    ctr = [r for r in grn if 'counterexample' in r['kind']]
    mild = [r for r in R if 'mild' in r['kind']]
    ins = [r for r in R if cats(r['signs'])]
    clean = [r for r in R if not set(r['kind']) & {'typo', 'glued', 'real-word-typo'}]
    bent = lambda r: [c for c in r['changes'] if c[1] != 'split' and c[2] not in APOS and c[0].lower() in EN]
    d = collections.OrderedDict()
    d['urgent (is_danger) red'] = pct(sum(r['is_danger'] for r in red), len(red))
    d['urgent yellow'] = pct(sum(r['is_danger'] for r in yel), len(yel))
    d['urgent green (false positive)'] = pct(sum(r['is_danger'] for r in grn), len(grn))
    d['  counterexamples (urgent)'] = pct(sum(r['is_danger'] for r in ctr), len(ctr))
    d['  mild (urgent)'] = pct(sum(r['is_danger'] for r in mild), len(mild))
    d['body sign found, lines with a covered sign'] = pct(sum(bool(r['body']) for r in ins), len(ins))
    d['  right category'] = pct(sum(bool(set(r['body']) & set(cats(r['signs']))) for r in ins), len(ins))
    d['  red (body)'] = pct(sum(bool(r['body']) for r in ins if r['triage'] == 'red'), sum(r['triage'] == 'red' for r in ins))
    d['body sign on green'] = pct(sum(bool(r['body']) for r in grn), len(grn))
    d['  counterexamples (body)'] = pct(sum(bool(r['body']) for r in ctr), len(ctr))
    for name, rows in (('red', red), ('all', R)):
        a = collections.Counter(r['action'] for r in rows)
        d[f'{name}: actions'] = dict(sorted(a.items()))
        d[f'{name}: bare ask (pages withheld)'] = a.get('ask', 0)
        d[f'{name}: pages withheld (any reason)'] = sum(not r['pages_shown'] for r in rows)
        d[f'{name}: ask+pages (pages, no answer)'] = a.get('ask+pages', 0)
        d[f'{name}: nothing found'] = sum(r['n_hits'] == 0 for r in rows)
    d['red sure with first page from an emergency book'] = sum(r['chat_level'] == 'sure' and r['first_emergency'] for r in red)
    d['red sure, first page not from one'] = sum(r['chat_level'] == 'sure' and r['n_hits'] and not r['first_emergency'] for r in red)
    d['clean lines changed by the corrector'] = pct(sum(r['changed'] for r in clean), len(clean))
    d['  changed other than apostrophes'] = sum(any(c[2] not in APOS for c in r['changes']) for r in clean)
    d['lines with an English word bent (typed word in the list, not split/apostrophe)'] = sum(bool(bent(r)) for r in R)
    d['  clean lines'] = sum(bool(bent(r)) for r in clean)
    d['  the words'] = sorted({f'{c[0]}->{c[2]}' for r in R for c in bent(r)})
    return d


# ---- typo / glued / real-word-typo lines: the meaning word right after correction (indep_analyze.py's rule and HAND list)
STOPW = set("""a an and are as at be but by can do does for from get got have how i if in into is it its me my need of on or
so the to was what when where which who why will with you your he she him her his hers they them their this that there
these those has had been were am about after before out just i'm i've it's he's she's im ive dont don't should would could
like up some very much any all one i'd we our us now""".split())
EXTRA_STOP = set("""wont cant isnt not no stop stopped hes shes im dont doesnt didnt help please pls what alot lot think
really so much now just very bit""".split())
def _words(s):
    return [w for w in re.findall(r"[a-z]+", s.lower().replace("'", '').replace('’', '')) if w not in STOPW and len(w) > 1]
def _stem(w):
    for suf in ('ing', 'ed', 'es', 's', 'e', 'y'):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[:-len(suf)]
    return w
def _content(s):
    return [w for w in _words(s) if w not in EXTRA_STOP]
HAND = {'should i put a tournaquet on or just press': 'fixed', 'slured speach and dizzy all of a suddon': 'fixed',
        'heart attak symtoms woman': 'fixed', 'breathin weird': 'fixed',
        'toddler vomitng and diahrea all day but drinking a bit': 'fixed', 'diahrrea': 'fixed'}
def typo_status(R):
    out = collections.Counter()
    for r in R:
        if not set(r['kind']) & {'typo', 'glued', 'real-word-typo'}:
            continue
        M = {_stem(w) for w in _content(r['meaning'])}
        T, C = _content(r['text']), _content(r['corrected'])
        st = [w for w in T if _stem(w) not in M]
        sc = [w for w in C if _stem(w) not in M]
        new_wrong = [w for w in sc if w not in T]
        status = ('nothing to fix' if not st else 'fixed' if not sc else 'wrong word' if new_wrong
                  else 'partly fixed' if len(sc) < len(st) else 'left as typed')
        out[HAND.get(r['text'], status)] += 1
    return dict(out)


def plea_rows(R):
    return {r['text']: r['action'] for r in R if re.fullmatch(r"(?i)\W*(911|999|112|help\w*|hlep|halp|emergency|sos|help me\W*|helo my son)\W*", r['text'])}


def insample(R):
    out = collections.OrderedDict()
    sets = ['cases', 'cases154', 'cases128', 'cases241', 'cases_glued', 'convos']
    for s in sets + ['all']:
        rows = [r for r in R if s == 'all' or r['set'] == s]
        sc = [r for r in rows if r['first_ok'] is not None]
        red = [r for r in rows if r['colour'] == 'red' and not r['counter']]
        grn = [r for r in rows if r['colour'] == 'green']
        ctr = [r for r in rows if r['counter']]
        a = collections.Counter(r['action'] for r in rows)
        out[s] = {'n': len(rows), 'first right': sum(bool(r['first_ok']) for r in sc), 'top3 right': sum(bool(r['top3_ok']) for r in sc),
                  'useful': round(sum(r['useful'] or 0 for r in sc) / max(1, len(sc)), 2),
                  'urgent red': f"{sum(r['danger'] for r in red)}/{len(red)}", 'urgent green': f"{sum(r['danger'] for r in grn)}/{len(grn)}",
                  'urgent counter': f"{sum(r['danger'] for r in ctr)}/{len(ctr)}", 'body': sum(bool(r['body']) for r in rows),
                  'actions': dict(sorted(a.items())), 'pages withheld': sum(r['action'] in WITHHELD and r['n_hits'] > 0 for r in rows)}
    return out


def diff_ins(B, A):
    key = lambda r: (r['set'], r['id'])
    bb = {key(r): r for r in B}
    ch = collections.Counter()
    ex = collections.defaultdict(list)
    for a in A:
        b = bb[key(a)]
        for k in ('searched', 'danger', 'action', 'first', 'first_ok'):
            if a[k] != b[k]:
                ch[k] += 1
                ex[k].append((a['set'], a['colour'], a['q'], b[k], a[k]))
        if b['danger'] and not a['danger']:
            ch['urgent lost'] += 1
            ex['urgent lost'].append((a['set'], a['colour'], a['q']))
        if b['first_ok'] and not a['first_ok']:
            ch['first right lost'] += 1
        if a['first_ok'] and not b['first_ok']:
            ch['first right gained'] += 1
        if (b['useful'] or 0) > (a['useful'] or 0):
            ch['fewer useful'] += 1
        if (b['useful'] or 0) < (a['useful'] or 0):
            ch['more useful'] += 1
    return ch, ex


if __name__ == '__main__':
    hb, ha, ib, ia = (load(p) for p in sys.argv[1:5])
    HB, HA = heldout(hb), heldout(ha)
    print('== held-out list 1:', sys.argv[1], '->', sys.argv[2])
    for k in HB:
        print(f'{k:70} {HB[k]}  ->  {HA[k]}')
    print('typo lines before', typo_status(hb), ' after', typo_status(ha))
    print('pleas before', plea_rows(hb))
    print('pleas after ', plea_rows(ha))
    IB, IA = insample(ib), insample(ia)
    print('== in-sample:', sys.argv[3], '->', sys.argv[4])
    for s in IB:
        print(s, '\n   before', IB[s], '\n   after ', IA[s])
    ch, ex = diff_ins(ib, ia)
    print('changes', dict(ch))
    for k in ('searched', 'danger', 'urgent lost', 'first_ok', 'action'):
        for e in ex[k][:60]:
            print('  ', k, e)
