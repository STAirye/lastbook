r"""Held-out list 2: before (4ea2d9f) vs after (19c2db2, fork/heldout-fixes), keyword-only and hybrid, with list 1's
numbers beside it (list 1 before = independent/runs/{kw,hy}.json, after = heldout-fixes/runs/ho_final_{kw,hy}.json).
Metrics are heldout-fixes/compare.py's (imported, unchanged).  python -B -X utf8 analyze2.py  -> results.json, runs/report.txt
Measurement only: nothing here feeds back into the code."""
import collections, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = HERE.parent
sys.path.insert(0, str(D / 'heldout-fixes'))
import compare as C  # noqa: E402

load = lambda p: json.load(open(p, encoding='utf-8'))['rows']
RUNS = {('before', m): load(HERE / 'runs' / f'before_{m}.json') for m in ('kw', 'hy')}
RUNS.update({('after', m): load(HERE / 'runs' / f'after_{m}.json') for m in ('kw', 'hy')})
L1 = {('before', 'kw'): load(D / 'independent' / 'runs' / 'kw.json'), ('before', 'hy'): load(D / 'independent' / 'runs' / 'hy.json'),
      ('after', 'kw'): load(D / 'heldout-fixes' / 'runs' / 'ho_final_kw.json'),
      ('after', 'hy'): load(D / 'heldout-fixes' / 'runs' / 'ho_final_hy.json')}
L1_TEXTS = {r['text'].lower() for r in L1[('before', 'kw')]}
OVERLAP = sorted({r['text'] for r in RUNS[('before', 'kw')] if r['text'].lower() in L1_TEXTS})

HEALTH = re.compile(r'health|heart|seiz|epilep|bleed|newborn|bab(y|ies)|pregnan|birth|breath|belly|diarr|medic|nurs|first aid|'
                    r'injur|burn|poison|wound|fractur|stroke|cpr|doctor|emergenc|resusc|choking|allerg|drown|shock|fever|child|sick|'
                    r'disease|pain|hospital|clinic|patient|trauma|bites|stings', re.I)   # indep_analyze.py's rough title check
red = lambda R: [r for r in R if r['triage'] == 'red']
first_title = lambda r: (r['top3'][0]['title'] or '') if r['top3'] else ''


def table(R):
    """compare.heldout plus the rows RESULTS.md / FORK.md 3l report."""
    d = C.heldout(R)
    rr = red(R)
    d['red sure, first page title not even health-looking (rough)'] = sum(
        r['chat_level'] == 'sure' and r['n_hits'] and not r['first_emergency'] and not HEALTH.search(first_title(r)) for r in rr)
    d['red sure (total)'] = sum(r['chat_level'] == 'sure' for r in rr)
    d['typo lines'] = C.typo_status(R)
    d['plea replies'] = C.plea_rows(R)
    d['all: plea action'] = sum(r['action'] == 'plea' for r in R)
    return d


T2 = {k: table(v) for k, v in RUNS.items()}
T1 = {k: table(v) for k, v in L1.items()}
# list 2 without the 6 lines also on list 1 (urgent rates only)
no_ov = lambda R: [r for r in R if r['text'] not in OVERLAP]
T2x = {k: table(no_ov(v)) for k, v in RUNS.items()}


def short(r, other=None):
    t = r['top3'][0] if r['top3'] else None
    return {'i': r['i'], 'text': r['text'], 'corrected': r['corrected'], 'triage': r['triage'], 'signs': r['signs'],
            'kind': r['kind'], 'action': r['action'], 'chat_level': r['chat_level'], 'p': r['p'], 'urgent': r['is_danger'],
            'body': r['body'], 'n_hits': r['n_hits'], 'first': f"{t['title']} p.{t['page']}" if t else None,
            'first_emergency': r['first_emergency']}


AK, AH, BK, BH = RUNS[('after', 'kw')], RUNS[('after', 'hy')], RUNS[('before', 'kw')], RUNS[('before', 'hy')]
text_diff = [(a['i'], k) for a, b in zip(AK, AH) for k in ('corrected', 'body', 'is_danger') if a[k] != b[k]]
crit = {
    'red_not_urgent_after': [short(r) for r in red(AK) if not r['is_danger']],
    'red_no_answer_or_no_pages_after': {m: [short(r) for r in red(R) if r['action'] not in ('answer', 'buttons', 'compact buttons')
                                            or not r['pages_shown']] for m, R in (('kw', AK), ('hy', AH))},
    'new_false_positives': [short(a) for a, b in zip(AK, BK) if a['triage'] == 'green' and a['is_danger'] and not b['is_danger']],
    'false_positives_fixed': [short(a) for a, b in zip(AK, BK) if a['triage'] == 'green' and b['is_danger'] and not a['is_danger']],
    'urgent_lost_red_yellow': [short(a) for a, b in zip(AK, BK) if a['triage'] != 'green' and b['is_danger'] and not a['is_danger']],
    'yellow_not_urgent_after': [short(r) for r in AK if r['triage'] == 'yellow' and not r['is_danger']],
    'green_urgent_after': [short(r) for r in AK if r['triage'] == 'green' and r['is_danger']],
    'red_sure_offtopic_after': {m: [short(r) for r in red(R) if r['chat_level'] == 'sure' and r['n_hits'] and not r['first_emergency']
                                    and not HEALTH.search(first_title(r))] for m, R in (('kw', AK), ('hy', AH))},
}
bent = lambda r: [c for c in r['changes'] if c[1] != 'split' and c[2] not in C.APOS and c[0].lower() in C.EN]
TYPO_TAGS = {'typo', 'glued', 'real-word-typo', 'voice-to-text'}
typo_after = []
for b, a in zip(BK, AK):
    if set(a['kind']) & TYPO_TAGS or bent(a) or a['changes']:
        typo_after.append({'text': a['text'], 'kind': a['kind'], 'meaning': a['meaning'], 'before': b['corrected'],
                           'after': a['corrected'], 'changes_after': a['changes'], 'english_bent_after': bent(a),
                           'urgent_before': b['is_danger'], 'urgent_after': a['is_danger']})
crit['typo_damage_after'] = [x for x in typo_after if x['english_bent_after']]
crit['typo_and_voice_lines'] = typo_after

TAGS = sorted({t for r in AK for t in r['kind']})


def by_kind(R, Rb):
    out = {}
    for t in TAGS:
        rows = [(a, b) for a, b in zip(R, Rb) if t in a['kind']]
        A = [a for a, _ in rows]
        B = [b for _, b in rows]
        g = lambda X, c: [r for r in X if r['triage'] == c]
        out[t] = {'n': len(A), 'r/y/g': f"{len(g(A, 'red'))}/{len(g(A, 'yellow'))}/{len(g(A, 'green'))}",
                  'urgent red before': sum(r['is_danger'] for r in g(B, 'red')), 'urgent red after': sum(r['is_danger'] for r in g(A, 'red')),
                  'urgent yellow before': sum(r['is_danger'] for r in g(B, 'yellow')), 'urgent yellow after': sum(r['is_danger'] for r in g(A, 'yellow')),
                  'urgent green before': sum(r['is_danger'] for r in g(B, 'green')), 'urgent green after': sum(r['is_danger'] for r in g(A, 'green')),
                  'body covered before': f"{sum(bool(r['body']) for r in B if C.cats(r['signs']))}/{sum(bool(C.cats(r['signs'])) for r in B)}",
                  'body covered after': f"{sum(bool(r['body']) for r in A if C.cats(r['signs']))}/{sum(bool(C.cats(r['signs'])) for r in A)}",
                  'red withheld before': sum(not r['pages_shown'] for r in g(B, 'red')), 'red withheld after': sum(not r['pages_shown'] for r in g(A, 'red'))}
    return out


BYK = {'kw': by_kind(AK, BK), 'hy': by_kind(AH, BH)}

# ---- miss themes (after, keyword run; text checks are the same in both modes). Tried on text + signs, then meaning.
THEMES = [
    ('non-English', r'\b(mi|hijo|niño|bebé|respira|no puede|ma |mon |je |il |elle |ne |pas)\b|[áéíóúñç]'),
    ('bare plea / number', r'^\W*(911|999|112|hlep|help\w*)\W*$'),
    ('mental health / suicide in other words', r'suicid|kill (my|him|her)self|end (it|my life)|not wake up|better off|goodbye|'
     r'disappear|cutting|self.?harm|hurt (my|him|her)self|voices|psychos|no point|bridge|rope|hang'),
    ('overdose / poisoning / ingestion without the word', r'overdose|pills|tablets|swallow|drank|ate (a|some|the)|battery|bleach|'
     r'poison|took (a|all|the|his|her|my)|mushroom|berries|antifreeze|detergent|pod|drunk|alcohol|opioid|fentanyl|heroin|xanax'),
    ('stroke wordings', r'stroke|droop|slur|one side|face (fell|went|looks)|arm (went|is) (weak|numb|dead)|can.?t (find|get) (his|her|my)? ?words|'
     r'speech|confus|vision|blind|lopsided|crooked|garbled|gibberish'),
    ('chest / heart wordings', r'chest|heart|jaw|left arm|indigestion|palpitat|pounding|racing'),
    ('breathing / airway wordings', r'breath|gasp|wheez|asthma|inhaler|choke|chok|throat|lips|blue|grey|gray|purple|stridor|'
     r'whoop|croup|ribs sucking|grunt|snor|gurgl|turning'),
    ('unconscious / unresponsive wordings', r'wake|limp|faint|pass(ed)? out|collaps|unrespons|unconscious|out cold|floppy|'
     r'not (moving|answering|responding)|slumped|floor|drowsy|sleepy|staring|zoned'),
    ('bleeding / wound wordings', r'blood|bleed|cut|gash|wound|spurt|stab|shot|bone|amputat|severed|deep|pouring|soak'),
    ('seizure wordings', r'seiz|fit\b|fitting|jerk|shak|convuls|eyes roll|twitch|stiff'),
    ('allergy / anaphylaxis', r'allerg|swell|hives|epi|peanut|sting|bee|wasp'),
    ('pregnancy / birth / newborn', r'pregnan|weeks|waters|labou?r|contraction|baby (is )?coming|bleeding.*pregnan|newborn|'
     r'fontanel|cord|placenta|kick'),
    ('child / baby specific', r'baby|infant|toddler|newborn|month.?old|kid|child|son|daughter'),
    ('head injury / fall', r'head|fell|fall|hit (his|her|my)'),
    ('burns / electric / heat / cold / drowning', r'burn|scald|electr|shock|heat|hot|cold|frozen|hypotherm|drown|water|pool|lake'),
    ('severe pain / belly', r'pain|belly|stomach|abdom|vomit|puk|throw|poo|stool|diarr|urine|pee'),
    ('fever / infection / rash / meningitis', r'fever|temp|rash|spots|neck|infect|red streak|sepsis|shiver'),
]


def theme(r):
    for t in (r['text'].lower() + ' | ' + ' '.join(r['signs']).lower(), r['meaning'].lower()):
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
    'red_not_urgent': themed([r for r in red(AK) if not r['is_danger']]),
    'yellow_not_urgent': themed([r for r in AK if r['triage'] == 'yellow' and not r['is_danger']]),
    'covered_sign_missed_red_yellow': themed([r for r in AK if C.cats(r['signs']) and r['triage'] != 'green' and not r['body']]),
    'green_urgent': themed([r for r in AK if r['triage'] == 'green' and r['is_danger']]),
    'combined_red_yellow': themed([a for a, h in zip(AK, AH) if a['triage'] != 'green' and (
        not a['is_danger'] or (C.cats(a['signs']) and not a['body']) or (a['triage'] == 'red' and (not a['pages_shown'] or not h['pages_shown'])))]),
}
fp_words = {
    'before': collections.Counter(w for r in BK if r['triage'] == 'green' and r['is_danger'] for w in r['urgent_words']).most_common(25),
    'after': collections.Counter(w for r in AK if r['triage'] == 'green' and r['is_danger'] for w in r['urgent_words']).most_common(25),
}

# the 19 red lines not urgent after, grouped by hand (read one by one; the regex themes above are rough)
HAND_THEMES = {
    'unresponsive / altered in other words (a turn, a do, staring and drooling, barely awake and icy)': [
        "my mate is having a turn, can't get a word out of him", "my missus is having a do and she's grey",
        'something wrong with grandma she just staring and drooling', 'found an old man outside in the snow, barely awake, skin icy'],
    'suicide / self-harm in other words': ['my son says voices are telling him to jump', 'cant do this no more. took everything in the cabinet',
                                          'unalive myself tonight how many'],
    'stroke / TIA / hypertensive wordings': ['stoke symptoms my dad', "mum's speech went weird for 5 mins then back to normal",
                                             'my bp is very high 200 and my vision is going blurry'],
    'drug slang / antidote (ODing, narcan)': ['my brother is ODing', 'narcan how'],
    'airway: throat closing, stridor': ['his throat is closing after peanuts', 'child has croup and making squeaky noise even when calm'],
    'bleeding without the word (pumping)': ['my mate chainsawed his thigh its pumping'],
    'CPR named by its parts (compressions)': ['compressions how fast'],
    'GI bleed (black tarry stool + lightheaded)': ['my poo is black and tarry and i feel a bit lightheaded'],
    'chemical eye injury': ['acid splashed in her eyes at work'],
    'voice-to-text garble ("anna flack sis" = anaphylaxis)': ['anna flack sis'],
}
assert sorted(x for v in HAND_THEMES.values() for x in v) == sorted(r['text'] for r in red(AK) if not r['is_danger'])
miss['red_not_urgent_by_hand'] = HAND_THEMES
# words the corrector still turns into another word after (read by hand from typo_and_voice_lines; none is new in 19c2db2)
WRONG_AFTER = ['rennie->ronnie', 'ODing->Oring', 'gouching->touching', 'gurgly->gargle', 'unalive->unlike', 'konked->kinked',
               'tbh->tbu', 'redback->repack', 'dhe->due', 'stooling->stooping', 'ako->amo', 'fluey->flue', 'doms->dams',
               'sniffly->stiffly (x2)', 'sipon->sion', 'fortnite->fortunate (x2)', 'elden->eden', 'bjj->bmj', 'adobo->adobe',
               "hasnt/havent/shouldnt -> hasn/haven/shouldn (x7: the 't' dropped, so the negation goes)"]
crit['typo_wrong_words_after_by_hand'] = WRONG_AFTER

key = lambda k: f'{k[0]}_{k[1]}'
out = {'list2': {key(k): v for k, v in T2.items()}, 'list2_without_list1_overlap': {key(k): v for k, v in T2x.items()},
       'list1': {key(k): v for k, v in T1.items()}, 'overlap_with_list1': OVERLAP,
       'text_checks_differ_between_modes_after': text_diff, 'critical': crit, 'by_kind': BYK, 'miss_themes': miss,
       'urgent_words_on_green': fp_words}
json.dump(out, open(HERE / 'results.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)

# ---- print
P = []
p = P.append
p(f'overlap with list 1 ({len(OVERLAP)}): {OVERLAP}')
p(f'text checks differ kw/hy after: {text_diff[:20]}')
for m in ('kw', 'hy'):
    p(f'===== {m}: list 2 before -> after   ||   list 1 before -> after')
    for k in T2[('before', m)]:
        if k in ('typo lines', 'plea replies'):
            continue
        p(f"{k[:66]:66} {T2[('before', m)][k]} -> {T2[('after', m)][k]}   ||   {T1[('before', m)].get(k)} -> {T1[('after', m)].get(k)}")
    for k in ('typo lines', 'plea replies'):
        p(f"{k}: L2 {T2[('before', m)][k]} -> {T2[('after', m)][k]}")
        p(f"      L1 {T1[('before', m)][k]} -> {T1[('after', m)][k]}")
p('===== list 2 without the overlap (kw): urgent red ' + T2x[('before', 'kw')]['urgent (is_danger) red'] + ' -> '
  + T2x[('after', 'kw')]['urgent (is_danger) red'] + '; counter ' + T2x[('after', 'kw')]['  counterexamples (urgent)'])
for k, v in crit.items():
    if isinstance(v, dict):
        for m, xs in v.items():
            p(f'== {k} {m}: {len(xs)}')
            for x in xs:
                p(f"   {x['text']!r} [{x['triage']}] -> {x['corrected']!r} {x['action']} urgent={x['urgent']} body={x['body']} hits={x['n_hits']} first={x['first']}")
    else:
        p(f'== {k}: {len(v)}')
        for x in v:
            if isinstance(x, str):
                p(f'   {x}')
            elif 'action' in x:
                p(f"   {x['text']!r} [{x['triage']}|{','.join(x['kind'])}] -> {x['corrected']!r} {x['action']} body={x['body']} first={x['first']}")
            else:
                p(f"   {x['text']!r} [{','.join(x['kind'])}] before {x['before']!r} after {x['after']!r} bent={x['english_bent_after']} urg {x['urgent_before']}->{x['urgent_after']}")
for m in ('kw', 'hy'):
    p(f'== by kind {m}')
    for t, g in BYK[m].items():
        p(f'   {t:16} {g}')
for k, v in miss.items():
    p(f'== themes {k}: {sum(len(x) for x in v.values())}')
    for th, xs in v.items():
        p(f'   {len(xs):3} {th} | ' + ' / '.join(xs))
p(f'urgent words on green: {fp_words}')
(HERE / 'runs' / 'report.txt').write_text('\n'.join(P) + '\n', encoding='utf-8')
print('\n'.join(P))
