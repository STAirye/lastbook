r"""Blind list 3: words (9bd116e) vs words OR meaning (51c7a4f, fork/meaning-check), keyword-only and hybrid.
Metrics are heldout-fixes/compare.py's (imported, unchanged); the extra rows and the miss themes are analyze2.py's.
"urgent" = assistant.is_danger (on 51c7a4f that is words OR meaning).
    python -B -X utf8 analyze3.py  -> results.json, runs/report.txt
Measurement only: nothing here feeds back into the code."""
import collections, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = HERE.parent
sys.path.insert(0, str(D / 'heldout-fixes'))
import compare as C  # noqa: E402

loadj = lambda p: json.load(open(p, encoding='utf-8'))
RAW = {(c, m): loadj(HERE / 'runs' / f'{c}_{m}.json') for c in ('words', 'meaning') for m in ('kw', 'hy')}
RUNS = {k: v['rows'] for k, v in RAW.items()}
WK, WH, MK, MH = RUNS[('words', 'kw')], RUNS[('words', 'hy')], RUNS[('meaning', 'kw')], RUNS[('meaning', 'hy')]

# --- analyze2.py's rough health-title check and miss themes (copied unchanged)
HEALTH = re.compile(r'health|heart|seiz|epilep|bleed|newborn|bab(y|ies)|pregnan|birth|breath|belly|diarr|medic|nurs|first aid|'
                    r'injur|burn|poison|wound|fractur|stroke|cpr|doctor|emergenc|resusc|choking|allerg|drown|shock|fever|child|sick|'
                    r'disease|pain|hospital|clinic|patient|trauma|bites|stings', re.I)
red = lambda R: [r for r in R if r['triage'] == 'red']
first_title = lambda r: (r['top3'][0]['title'] or '') if r['top3'] else ''
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


def table(R):
    d = C.heldout(R)
    rr = red(R)
    d['red sure, first page title not even health-looking (rough)'] = sum(
        r['chat_level'] == 'sure' and r['n_hits'] and not r['first_emergency'] and not HEALTH.search(first_title(r)) for r in rr)
    d['red sure (total)'] = sum(r['chat_level'] == 'sure' for r in rr)
    d['typo lines'] = C.typo_status(R)
    d['plea replies'] = C.plea_rows(R)
    return d


T = {f'{c}_{m}': table(v) for (c, m), v in RUNS.items()}

# --- consistency: same text checks in both commits; meaning-run words_danger == words-run is_danger
checks = {
    'corrected differs words vs meaning commit': [a['text'] for a, b in zip(WK, MK) if a['corrected'] != b['corrected']],
    'body differs': [a['text'] for a, b in zip(WK, MK) if a['body'] != b['body']],
    'words part differs (9bd116e is_danger vs 51c7a4f words)': [a['text'] for a, b in zip(WK, MK) if a['is_danger'] != b['words_danger']],
    'urgent differs kw vs hy (meaning commit)': [a['text'] for a, b in zip(MK, MH) if a['is_danger'] != b['is_danger']],
    'meaning state not ready': sorted({r['meaning_state'] for r in MK + MH if r['meaning_state'] != 'ready'}),
    'urgent lost by meaning (words urgent, OR not)': [a['text'] for a, b in zip(WK, MK) if a['is_danger'] and not b['is_danger']],
}


def short(r):
    t = r['top3'][0] if r['top3'] else None
    return {'i': r['i'], 'text': r['text'], 'corrected': r['corrected'], 'triage': r['triage'], 'signs': r['signs'],
            'kind': r['kind'], 'persona': r['persona'], 'action': r['action'], 'chat_level': r['chat_level'],
            'urgent': r['is_danger'], 'words': r.get('words_danger'), 'meaning_score': r.get('meaning_score'),
            'body': r['body'], 'n_hits': r['n_hits'], 'first': f"{t['title']} p.{t['page']}" if t else None,
            'first_emergency': r['first_emergency'], 'meaning_text': r['meaning']}


ANSWERED = ('answer', 'buttons', 'compact buttons')
contrib = {}
for lab in ('red', 'yellow', 'green'):
    contrib[f'{lab}: only meaning'] = [short(r) for r in MK if r['triage'] == lab and r['meaning_fired'] and not r['words_danger']]
    contrib[f'{lab}: meaning fired (any)'] = sum(r['meaning_fired'] for r in MK if r['triage'] == lab)
    contrib[f'{lab}: n'] = sum(r['triage'] == lab for r in MK)
for sub in ('counterexample', 'mild'):
    contrib[f'green {sub}: only meaning'] = sum(r['triage'] == 'green' and sub in r['kind'] and r['meaning_fired'] and not r['words_danger'] for r in MK)

crit = {
    'red_not_urgent_words': [short(r) for r in red(WK) if not r['is_danger']],
    'red_not_urgent_or': [short(r) for r in red(MK) if not r['is_danger']],
    'red_no_answer_or_no_pages': {f'{c}_{m}': [short(r) for r in red(RUNS[(c, m)]) if r['action'] not in ANSWERED or not r['pages_shown']]
                                  for c in ('words', 'meaning') for m in ('kw', 'hy')},
    'red_sure_offtopic': {f'{c}_{m}': [short(r) for r in red(RUNS[(c, m)]) if r['chat_level'] == 'sure' and r['n_hits']
                                       and not r['first_emergency'] and not HEALTH.search(first_title(r))]
                          for c in ('words', 'meaning') for m in ('kw', 'hy')},
    'yellow_not_urgent_or': [short(r) for r in MK if r['triage'] == 'yellow' and not r['is_danger']],
}
bent = lambda r: [c for c in r['changes'] if c[1] != 'split' and c[2] not in C.APOS and c[0].lower() in C.EN]
TYPO_TAGS = {'typo', 'glued', 'real-word-typo', 'voice-to-text'}
crit['typo_and_voice_lines'] = [{'text': r['text'], 'kind': r['kind'], 'meaning': r['meaning'], 'corrected': r['corrected'],
                                 'changes': r['changes'], 'english_bent': bent(r), 'urgent_words': r['is_danger']}
                                for r in WK if set(r['kind']) & TYPO_TAGS or r['changes']]
crit['english_bent'] = [x for x in crit['typo_and_voice_lines'] if x['english_bent']]


def group_stats(key_of):
    keys = sorted({k for r in MK for k in key_of(r)})
    out = {}
    for k in keys:
        idx = [i for i, r in enumerate(MK) if k in key_of(r)]
        g = lambda R, c: [R[i] for i in idx if R[i]['triage'] == c]
        nr, ny, ng = len(g(MK, 'red')), len(g(MK, 'yellow')), len(g(MK, 'green'))
        out[k] = {'n': len(idx), 'r/y/g': f'{nr}/{ny}/{ng}',
                  'red words': sum(r['is_danger'] for r in g(WK, 'red')), 'red or': sum(r['is_danger'] for r in g(MK, 'red')),
                  'yellow words': sum(r['is_danger'] for r in g(WK, 'yellow')), 'yellow or': sum(r['is_danger'] for r in g(MK, 'yellow')),
                  'green words': sum(r['is_danger'] for r in g(WK, 'green')), 'green or': sum(r['is_danger'] for r in g(MK, 'green')),
                  'body': f"{sum(bool(MK[i]['body']) for i in idx if C.cats(MK[i]['signs']))}/{sum(bool(C.cats(MK[i]['signs'])) for i in idx)}",
                  'red no answer/pages kw words/or': f"{sum(r['action'] not in ANSWERED or not r['pages_shown'] for r in g(WK, 'red'))}/"
                                                    f"{sum(r['action'] not in ANSWERED or not r['pages_shown'] for r in g(MK, 'red'))}",
                  'red no answer/pages hy words/or': f"{sum(r['action'] not in ANSWERED or not r['pages_shown'] for r in g(WH, 'red'))}/"
                                                    f"{sum(r['action'] not in ANSWERED or not r['pages_shown'] for r in g(MH, 'red'))}"}
    return out


BYK = group_stats(lambda r: r['kind'])
BYP = group_stats(lambda r: [r['persona']])

miss = {
    'red_not_urgent_words': themed([r for r in red(WK) if not r['is_danger']]),
    'red_not_urgent_or': themed([r for r in red(MK) if not r['is_danger']]),
    'yellow_not_urgent_or': themed([r for r in MK if r['triage'] == 'yellow' and not r['is_danger']]),
    'covered_sign_missed_red_yellow': themed([r for r in MK if C.cats(r['signs']) and r['triage'] != 'green' and not r['body']]),
    'green_urgent_or': themed([r for r in MK if r['triage'] == 'green' and r['is_danger']]),
    'green_only_meaning': themed([r for r in MK if r['triage'] == 'green' and r['meaning_fired'] and not r['words_danger']]),
}
# the 13 red lines not urgent with words OR meaning, grouped by hand (the regex themes above are rough)
HAND_THEMES = {
    'suicide / self-harm in other words (notes and giving the cat away, on the bridge, "kms")': [
        'ive written the notes and given my cat to my sister', 'standing on the bridge', 'kms fr this time'],
    'eye and sudden vision loss (amaurosis/TIA, retinal detachment, chemical eye)': [
        'probably nothing but my vision went black in one eye for a couple mins this morning',
        'flashing lights and a curtain coming down over my vision', 'splashed sheep dip in me eye stings like hell'],
    'downplayed classic red flags with no urgent word (thunderclap headache, crushing chest by simile)': [
        'bit of a headache. worst one ive ever had tbh came on all at once while lifting', 'feel like an elephant is sitting on me'],
    'hypertensive emergency (numbers + giddiness)': ['my mother is having giddiness since morning and BP machine showing 210/120'],
    'neutropenic sepsis (chemo + 38.2)': ['had my chemo tuesday temp is 38.2 now'],
    'amputation without the word': ['lawnmower blade took the top of my toe off. found the bit.'],
    'envenomation by name (funnel web)': ['funnel web in me boot bit me toe, mouth tingling'],
    'voice-to-text garble of CPR ("see PR")': ['how do I do see PR on a child'],
}
assert sorted(x for v in HAND_THEMES.values() for x in v) == sorted(r['text'] for r in red(MK) if not r['is_danger'])
miss['red_not_urgent_or_by_hand'] = HAND_THEMES
crit['typo_wrong_words_by_hand'] = ['rlly->rally', 'shud->shed', 'passd->pass', 'drnk->drink (x2; meant drunk)', 'nife->nice',
                                    'heoverdosedonheroin->"he overdose don heroin"', 'sees your (seizure), see PR (CPR), hippo (hypo), '
                                    'coffin (coughing), anna flat tick, breeding, sun, lite: real-word or voice garbles left as typed']
fp_words = collections.Counter(w for r in MK if r['triage'] == 'green' and r['is_danger'] for w in r['urgent_words']).most_common(30)

out = {'meaning_check': RAW[('meaning', 'kw')]['meaning_check'], 'meaning_check_hy': RAW[('meaning', 'hy')]['meaning_check'],
       'semantic': {k[0] + '_' + k[1]: v['semantic'] for k, v in RAW.items()},
       'table': T, 'consistency': checks, 'meaning_contribution': contrib, 'critical': crit, 'by_kind': BYK, 'by_persona': BYP,
       'miss_themes': miss, 'urgent_words_on_green_or': fp_words}
json.dump(out, open(HERE / 'results.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)

P = []
p = P.append
p(f"meaning: {out['meaning_check']}")
p(f"semantic: {out['semantic']}")
for k, v in checks.items():
    p(f'check {k}: {len(v)} {v[:10]}')
for m in ('kw', 'hy'):
    p(f'===== {m}: words (9bd116e) -> words OR meaning (51c7a4f)')
    for k in T[f'words_{m}']:
        p(f"{k[:66]:66} {T[f'words_{m}'][k]} -> {T[f'meaning_{m}'][k]}")
for k, v in contrib.items():
    if isinstance(v, list):
        p(f'== {k}: {len(v)}')
        for x in v:
            p(f"   {x['text']!r} score={x['meaning_score']} [{','.join(x['kind'])}|{x['persona']}]")
    else:
        p(f'== {k}: {v}')
for k, v in crit.items():
    if isinstance(v, dict):
        for m, xs in v.items():
            p(f'== {k} {m}: {len(xs)}')
            for x in xs:
                p(f"   {x['text']!r} -> {x['corrected']!r} {x['action']} urgent={x['urgent']} body={x['body']} hits={x['n_hits']} first={x['first']}")
    else:
        p(f'== {k}: {len(v)}')
        for x in v:
            if isinstance(x, str):
                p(f'   {x}')
            elif 'action' in x:
                p(f"   {x['text']!r} [{x['triage']}|{','.join(x['kind'])}|{x['persona']}] -> {x['corrected']!r} {x['action']} "
                  f"score={x['meaning_score']} body={x['body']} first={x['first']} || {x['meaning_text']}")
            else:
                p(f"   {x['text']!r} [{','.join(x['kind'])}] -> {x['corrected']!r} changes={x['changes']} bent={x['english_bent']} urg={x['urgent_words']} || {x['meaning']}")
for name, G in (('kind', BYK), ('persona', BYP)):
    p(f'== by {name}')
    for t, g in sorted(G.items(), key=lambda kv: -kv[1]['n']):
        p(f'   {t:32} {g}')
for k, v in miss.items():
    p(f'== themes {k}: {sum(len(x) for x in v.values())}')
    for th, xs in v.items():
        p(f'   {len(xs):3} {th} | ' + ' / '.join(xs))
p(f'urgent words on green (OR run): {fp_words}')
(HERE / 'runs' / 'report.txt').write_text('\n'.join(P) + '\n', encoding='utf-8')
print('\n'.join(P))
