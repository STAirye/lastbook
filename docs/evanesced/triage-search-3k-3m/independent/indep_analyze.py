r"""Scores runs/kw.json and runs/hy.json (indep_eval.py) against phrases.jsonl's labels -> results.json, and prints the
tables RESULTS.md is written from.  python -B -X utf8 indep_analyze.py
Measurement only: nothing here feeds back into the code."""
import json, re, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = {m: json.load(open(HERE / 'runs' / f'{m}.json', encoding='utf-8')) for m in ('kw', 'hy')}
KW, HY = RUNS['kw']['rows'], RUNS['hy']['rows']
assert len(KW) == len(HY) == 690

# ---- text checks must not depend on the search mode
TEXT_KEYS = ('corrected', 'body', 'urgent', 'is_danger', 'unknown_words', 'danger_signs')
text_diff = [(a['i'], k) for a, b in zip(KW, HY) for k in TEXT_KEYS if a[k] != b[k]]

# ---- body categories each labelled sign belongs to (what body_signs claims to cover)
CAT = [
    ('pulse', r'pulse|heartbeat|cardiac arrest'),
    ('breathing', r'breath|gasp'),
    ('blue', r'\bblue\b|grey skin'),
    ('unconscious', r'unresponsive|unconscious|collapsed|consciousness|hard to wake|fainted|fainting'),
    ('choking', r'chok|object in throat'),
    ('bleeding', r'bleed|(?<!high )(?<!low )blood(?! pressure| sugar)|spurting'),
    ('seizure', r'seizure'),
    ('chest pain', r'chest (pain|pressure|tightness|discomfort)'),
    ('not moving', r'floppy|\blimp\b|cannot move'),
    ('cold and clammy', r'clammy'),
]
def cats(signs):
    return sorted({c for s in signs for c, rx in CAT if re.search(rx, s)})


def pct(a, b):
    return f'{a}/{b} ({100 * a / b:.0f}%)' if b else '0/0'


def rate(rows, f):
    return sum(1 for r in rows if f(r)), len(rows)


TAGS = ['plain', 'typo', 'glued', 'real-word-typo', 'slang', 'non-native', 'fragment', 'misconception', 'child', 'baby',
        'elderly', 'pregnancy', 'caps', 'rambling', 'counterexample', 'mild']
red = lambda R: [r for r in R if r['triage'] == 'red']
yellow = lambda R: [r for r in R if r['triage'] == 'yellow']
green = lambda R: [r for r in R if r['triage'] == 'green']
counter = lambda R: [r for r in R if r['triage'] == 'green' and 'counterexample' in r['kind']]
mild = lambda R: [r for r in R if 'mild' in r['kind']]
bare = lambda r: r['action'] in ('ask', 'ask (danger, nothing found)')

out = {'text_checks_differ_between_modes': text_diff}

# ---------------------------------------------------------------- 1. text checks (mode-independent: keyword run)
R = KW
body_rows = [r for r in R if r['signs']]
inscope = [r for r in R if cats(r['signs'])]
tc = {
    'urgent': {g: rate(f(R), lambda r: r['urgent']) for g, f in
               (('red', red), ('yellow', yellow), ('green', green), ('green counterexample', counter), ('mild', mild))},
    'is_danger': {g: rate(f(R), lambda r: r['is_danger']) for g, f in
                  (('red', red), ('yellow', yellow), ('green', green), ('green counterexample', counter), ('mild', mild))},
    'danger_signs_only': {g: rate(f(R), lambda r: bool(r['danger_signs'])) for g, f in
                          (('red', red), ('yellow', yellow), ('green', green))},
    'body_any_sign_line': {g: rate([r for r in body_rows if r['triage'] == g], lambda r: bool(r['body']))
                           for g in ('red', 'yellow', 'green')},
    'body_inscope_any': {g: rate([r for r in inscope if r['triage'] == g], lambda r: bool(r['body']))
                         for g in ('red', 'yellow', 'green')},
    'body_inscope_right_category': {g: rate([r for r in inscope if r['triage'] == g],
                                            lambda r: bool(set(r['body']) & set(cats(r['signs']))))
                                    for g in ('red', 'yellow', 'green')},
    'body_fp': {'green counterexample': rate(counter(R), lambda r: bool(r['body'])),
                'green (all)': rate(green(R), lambda r: bool(r['body'])),
                'green, no in-scope sign': rate([r for r in green(R) if not cats(r['signs'])], lambda r: bool(r['body'])),
                'mild': rate(mild(R), lambda r: bool(r['body']))},
    'unknown_words': {g: rate(f(R), lambda r: r['unknown_words']) for g, f in
                      (('red', red), ('yellow', yellow), ('green', green))},
    'changed_by_correction': rate(R, lambda r: r['changed']),
}
by_cat = {}
for c, _ in CAT:
    rows = [r for r in R if c in cats(r['signs'])]
    by_cat[c] = {'n': len(rows), 'any_body': rate(rows, lambda r: bool(r['body']))[0],
                 'right_category': rate(rows, lambda r: c in r['body'])[0], 'urgent': rate(rows, lambda r: r['is_danger'])[0]}
tc['body_by_category'] = by_cat
out['text_checks'] = tc

# ---------------------------------------------------------------- 2. chat per mode
def chat(R):
    d = {}
    for g, f in (('red', red), ('yellow', yellow), ('green', green), ('all', lambda R: R)):
        rows = f(R)
        d[g] = {'n': len(rows), 'actions': dict(collections.Counter(r['action'] for r in rows)),
                'pages_withheld': rate(rows, lambda r: not r['pages_shown'])[0],
                'first_emergency_book': rate(rows, lambda r: r['first_emergency'])[0],
                'top3_emergency_book': rate(rows, lambda r: r['top3_emergency'])[0],
                'p_mean': round(sum(r['p'] or 0 for r in rows) / len(rows), 3),
                'unknown_capped': rate(rows, lambda r: r['conf_unknown'])[0]}
    return d
out['chat'] = {m: chat(RUNS[m]['rows']) for m in RUNS}


def short(r):
    t = r['top3'][0] if r['top3'] else None
    return {'i': r['i'], 'text': r['text'], 'corrected': r['corrected'], 'signs': r['signs'], 'kind': r['kind'],
            'p': r['p'], 'action': r['action'], 'urgent': r['is_danger'], 'body': r['body'], 'route': r['route'],
            'first': (f"{t['title']} p.{t['page']}" if t else None), 'n_hits': r['n_hits'],
            'first_health_looking': bool(t and HEALTH.search(t['title'] or ''))}

HEALTH = re.compile(r'health|heart|seiz|epilep|bleed|newborn|bab(y|ies)|pregnan|birth|breath|belly|diarr|medic|nurs|first aid|'
                    r'injur|burn|poison|wound|fractur|stroke|cpr|doctor|emergenc|resusc|choking|allerg|drown|shock|fever|child|sick|'
                    r'disease|pain|hospital|clinic|patient|trauma|bites|stings', re.I)   # rougher still than _emergency_book
crit = {}
for m in RUNS:
    R2 = RUNS[m]['rows']
    crit[m] = {
        'red_bare_ask': [short(r) for r in red(R2) if bare(r)],
        'red_pages_withheld': [short(r) for r in red(R2) if not r['pages_shown']],
        'red_ask_with_pages_no_answer': [short(r) for r in red(R2) if r['action'] == 'ask+pages'],
        'red_sure_non_emergency_first': [short(r) for r in red(R2) if r['chat_level'] == 'sure' and r['n_hits']
                                         and not r['first_emergency']],
        'red_sure_total': sum(1 for r in red(R2) if r['chat_level'] == 'sure'),
        'yellow_bare_ask': [short(r) for r in yellow(R2) if bare(r)],
    }
out['critical'] = crit

# ---------------------------------------------------------------- 3. typo / glued / real-word-typo correction
STOPW = set("""a an and are as at be but by can do does for from get got have how i if in into is it its me my need of on or
so the to was what when where which who why will with you your he she him her his hers they them their this that there
these those has had been were am about after before out just i'm i've it's he's she's im ive dont don't should would could
like up some very much any all one i'd we our us now""".split())
def words(s):
    return [w for w in re.findall(r"[a-z]+", s.lower().replace("'", '').replace('’', '')) if w not in STOPW and len(w) > 1]
def match(a, b):
    return a == b or (len(a) >= 4 and len(b) >= 4 and a[:4] == b[:4]) or (min(len(a), len(b)) >= 3 and (a.startswith(b) or b.startswith(a)))
def covered(ws, M):
    return {m for m in M if any(match(w, m) for w in ws)}

EXTRA_STOP = set("""wont cant isnt not no stop stopped hes shes im dont doesnt didnt help please pls what alot lot think
really so much now just very bit""".split())
def stem(w):
    for suf in ('ing', 'ed', 'es', 's', 'e', 'y'):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[:-len(suf)]
    return w
def content(s):
    return [w for w in words(s) if w not in EXTRA_STOP]
typo_rows = []
for r in KW:
    tags = set(r['kind']) & {'typo', 'glued', 'real-word-typo'}
    if not tags:
        continue
    M = {stem(w) for w in content(r['meaning'])}
    T, C = content(r['text']), content(r['corrected'])
    st = [w for w in T if stem(w) not in M]           # typed words the meaning doesn't have (exact, after a crude stem)
    sc = [w for w in C if stem(w) not in M]
    new_wrong = [w for w in sc if w not in T]          # words the correction brought that the meaning doesn't have
    if not st:
        status = 'nothing to fix'
    elif not sc:
        status = 'fixed'
    elif new_wrong:
        status = 'wrong word'
    elif len(sc) < len(st):
        status = 'partly fixed'
    else:
        status = 'left as typed'
    typo_rows.append({'i': r['i'], 'text': r['text'], 'corrected': r['corrected'], 'meaning': r['meaning'],
                      'tags': sorted(tags), 'status': status, 'changes': r['changes'], 'stray_typed': st,
                      'stray_after': sc, 'urgent': r['is_danger'], 'body': r['body'], 'triage': r['triage']})
# Read by hand after the automatic pass (paraphrase noise in "meaning"): the meaning-bearing word is right in these
HAND = {'should i put a tournaquet on or just press': 'fixed', 'slured speach and dizzy all of a suddon': 'fixed',
        'heart attak symtoms woman': 'fixed', 'breathin weird': 'fixed',
        'toddler vomitng and diahrea all day but drinking a bit': 'fixed', 'diahrrea': 'fixed',
        'blu lip baby': 'left as typed'}
for x in typo_rows:
    x['status_auto'] = x['status']
    x['status'] = HAND.get(x['text'], x['status'])
tsum = {}
for tag in ('typo', 'glued', 'real-word-typo'):
    rows = [x for x in typo_rows if tag in x['tags']]
    tsum[tag] = {'n': len(rows), **collections.Counter(x['status'] for x in rows)}
tsum['all lines'] = {'n': len(typo_rows), **collections.Counter(x['status'] for x in typo_rows)}
out['typos'] = {'summary': tsum, 'rows': typo_rows}

# ---------------------------------------------------------------- 4. by kind tag and by source
def group_stats(sel):
    g = {}
    for m in RUNS:
        R2 = [r for r in RUNS[m]['rows'] if sel(r)]
        rr, yy, gg = red(R2), yellow(R2), green(R2)
        s = [r for r in R2 if cats(r['signs'])]
        g[m] = {'n': len(R2), 'red': len(rr), 'yellow': len(yy), 'green': len(gg),
                'urgent_red': sum(r['is_danger'] for r in rr), 'urgent_yellow': sum(r['is_danger'] for r in yy),
                'urgent_green': sum(r['is_danger'] for r in gg),
                'body_inscope': len(s), 'body_inscope_hit': sum(bool(r['body']) for r in s),
                'red_bare_ask': sum(bare(r) for r in rr), 'red_withheld': sum(not r['pages_shown'] for r in rr),
                'red_ask_pages': sum(r['action'] == 'ask+pages' for r in rr),
                'red_first_emergency': sum(r['first_emergency'] for r in rr)}
    return g
out['by_kind'] = {t: group_stats(lambda r, t=t: t in r['kind']) for t in TAGS}
out['by_source'] = {s: group_stats(lambda r, s=s: r['source'] == s) for s in ('web-inspired', 'invented')}

# ---------------------------------------------------------------- 5. miss themes
THEMES = [  # (theme, regex); tried on the text + labelled signs first, then on the meaning; first match wins
    ('non-English', r'ma tête|je vois|respira|esposa'),
    ('bare word / greeting ("911", "hlep")', r'^(911|hlep|helo my son)$'),
    ('real-word autocorrect / real-word typo (breeding, breaking, sea sure, past out)',
     r'breed|sea sure|strock|poisend|coking|past out|keeled|braking|breaking|cheat pain|chest pane|brest pain'),
    ('misspelling the corrector left or bent', r'tournaquet|siezing|unconshus|hemmorage|bloooood|reponding|pnemonia|'
     r'cellulitus|\bblu\b|blueslips'),
    ('CPR named, no body word (body_signs only)', r'\bcpr\b'),
    ('seizure slang (fitting, shaking, eyes rolling, tongue)', r'fitting|shaking|eyes (are )?roll|tongue|foam'),
    ('chest pain / heart wordings (elephant, tight chest, heart racing)', r'chest|heart|elephant|jaw'),
    ('bleeding wordings without blood/bleed (pouring, oozing, cut off, shot)', r'pouring|oozing|cut off|shot|bone sticking|'
     r'sliced|nosebleed|soaking|coffee grounds|cut myself'),
    ('blue alone ("hes blue")', r'\bblue\b'),
    ('eye injury', r'firework|in my eye'),
    ('stroke words (face, arm, speech, one side, vision)', r'drooping|slurr|stroke|speech|crooked|one-sided|cant lift|'
     r'talking funny|say words|dribbling|left side of my body|blind in one eye|vision|arm weakness|arm feels heavy|peculiar|'
     r'funny turn'),
    ('suicide / self-harm euphemisms', r'suicid|killing myself|goodbye|disappear|end it|better off'),
    ('overdose / poisoning without the word', r'overdose|over dose|paracetamol|panadol|tablets|pills|xanax|poison|cleaning|'
     r'drunk|swallowed'),
    ('unconscious euphemisms (slumped, out cold, on the floor, won\'t answer, hard to rouse)',
     r'slump|out cold|dropped like|on the floor|kitchen floor|not answering|wont answer|rouse|not responding|responsive|'
     r'fairies|face down|fainting|cant wake'),
    ('agonal / noisy breathing (snoring, gurgling, stridor)', r'snor|gurgl|stridor|gasp|grunting|barky'),
    ('colour words (grey, ash, funny colour)', r'grey|gray|\bash\b|colour'),
    ('allergy / anaphylaxis words', r'allerg|anaphyla|hives|throat closing|shrimp|peanut'),
    ('breathing difficulty words (asthma, inhaler)', r'asthma|inhaler|breathless|wheez'),
    ('child/baby specific (red jelly poo)', r'jelly|fontanelle|nappies'),
    ('pregnancy / birth', r'pregnan|weeks|waters|labour|fetal'),
    ('cold / heat exposure', r'frozen|hypotherm|heat'),
    ('first-aid misconception (venom, finger sweep)', r'venom|finger sweep|brandy'),
    ('limb / circulation (can\'t feel legs, tight cast)', r'cast|feel her legs|numb|cold toes'),
    ('severe headache', r'headache|thunderclap'),
    ('drowning / submersion without the word', r'under the bath|pond'),
    ('yellow conditions with no urgent word (fracture, tooth, urine, infection, object)', r'broke|ankle|tooth|bead|scratch|'
     r'swollen|erection|peed|pee\b|eye'),
]
def theme(r):
    for t in (r['text'].lower() + ' | ' + ' '.join(r['signs']), r['meaning'].lower()):
        for name, rx in THEMES:
            if re.search(rx, t):
                return name
    return 'other'

def themed(rows):
    d = collections.defaultdict(list)
    for r in rows:
        d[theme(r)].append(r['text'])
    return dict(sorted(d.items(), key=lambda kv: -len(kv[1])))

miss = {
    'not_urgent_red': themed([r for r in red(KW) if not r['is_danger']]),
    'not_urgent_yellow': themed([r for r in yellow(KW) if not r['is_danger']]),
    'body_missed_inscope_red_yellow': themed([r for r in KW if cats(r['signs']) and r['triage'] != 'green' and not r['body']]),
    'red_withheld_kw': themed([r for r in red(KW) if not r['pages_shown']]),
    'red_withheld_hy': themed([r for r in red(HY) if not r['pages_shown']]),
}
out['miss_themes'] = miss
# combined: every red/yellow line with any detection miss (not urgent, or in-scope sign missed, or red pages withheld)
comb = [r for r, h in zip(KW, HY) if r['triage'] != 'green' and (not r['is_danger'] or (cats(r['signs']) and not r['body'])
        or (r['triage'] == 'red' and (not r['pages_shown'] or not h['pages_shown'])))]
out['miss_themes']['combined_red_yellow'] = themed(comb)
out['urgent_fp_green_words'] = collections.Counter(w for r in green(KW) if r['is_danger'] for w in r['urgent_words']).most_common(30)
out['body_fp_green'] = [{'text': r['text'], 'body': r['body'], 'kind': r['kind']} for r in green(KW) if r['body']]

json.dump(out, open(HERE / 'results.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- print
print('text differ between modes:', text_diff)
for k in ('urgent', 'is_danger', 'danger_signs_only', 'body_any_sign_line', 'body_inscope_any', 'body_inscope_right_category',
          'body_fp', 'unknown_words'):
    print(k, {g: pct(*v) for g, v in tc[k].items()})
print('changed', pct(*tc['changed_by_correction']))
print('by cat', by_cat)
for m in RUNS:
    print(m, json.dumps(out['chat'][m]))
    for k, v in crit[m].items():
        print(' ', m, k, v if isinstance(v, int) else len(v))
print('typos', tsum)
for t in TAGS:
    print(t, out['by_kind'][t])
print(out['by_source'])
for k, v in miss.items():
    print('==', k, sum(len(x) for x in v.values()))
    for th, xs in v.items():
        print('  ', len(xs), th, '|', ' / '.join(xs[:4]))
print('urgent FP words', out['urgent_fp_green_words'])
