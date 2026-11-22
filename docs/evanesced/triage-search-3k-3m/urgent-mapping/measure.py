"""Urgent-phrase mapping: inventory of the fork's rules and a measurement against the labelled lists.

Run from anywhere:  python -B measure.py        (writes measure_out.json next to it, prints the tables)
Read-only: reads repo files and the library's search index (through engine.typos), writes only measure_out.json here.
No network, no meaning model (engine.meaning_red is never imported or called).
"""
import json, os, re, subprocess, sys, shutil, unicodedata
from pathlib import Path

import regex   # \p{Script=Latin} like web/words.js

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
os.environ.setdefault('LASTBOOK_DATA', r'D:\LastbookData')
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / '.claude' / 'drafts' / 'triage'))

# ----------------------------------------------------------------------------------------------------------------
# Port of web/words.js: fold, splitWords, names (phrase words in order, whole words, stop words included)
LATIN_MARKS = regex.compile(r'(\p{Script=Latin})\p{M}+')
NOT_WORD = regex.compile(r'[^\p{L}\p{M}\p{N}]+')


def fold(s):
    s = unicodedata.normalize('NFKD', str(s).lower())
    s = LATIN_MARKS.sub(r'\1', s)
    return unicodedata.normalize('NFC', s).replace('\u03c2', '\u03c3')


def split_words(text):
    # words.js segments with Intl.Segmenter first, then splits each segment on NOT_WORD: for text in spaced scripts
    # that is the same as splitting on NOT_WORD ("isn't" -> isn, t). Checked against Node below.
    return [f for f in (fold(p) for p in NOT_WORD.split(str(text))) if f]


def names(all_words, p):
    n = len(p)
    return any(all_words[i:i + n] == p for i in range(len(all_words)) if i + n <= len(all_words))


def compile_phrases(phrases):
    return [(ph, p) for ph in phrases for p in [split_words(ph)] if p]


def matches(text, compiled):
    a = split_words(text)
    return [ph for ph, p in compiled if names(a, p)]


# ----------------------------------------------------------------------------------------------------------------
# Phrase sets
def load_current():
    out = {}
    for f in sorted((REPO / 'content' / 'topics').glob('*.json')):
        d = json.loads(f.read_text(encoding='utf-8'))
        for c in d.get('choices', []):
            if c.get('urgent'):
                out[f"{d['id']}/{c['id']}"] = c['urgent']
    return out


def load_proposed():
    d = json.loads((HERE / 'proposed_urgent.json').read_text(encoding='utf-8'))
    return {f'{t}/{c}': ph for t, cs in d.items() for c, ph in cs.items()}


def flat(sets):
    return [(k, ph) for k, phs in sets.items() for ph in phs]


# ----------------------------------------------------------------------------------------------------------------
# Labelled lines
def load_lines():
    sets = {}
    for name in ('independent', 'independent2', 'independent3'):
        p = REPO / '.claude' / 'drafts' / name / 'phrases.jsonl'
        rows = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
        sets[name] = [(r['text'], r['triage']) for r in rows]
    import cases
    sets['triage'] = [(c['q'], c['colour']) for c in cases.cases()]
    return sets


# ----------------------------------------------------------------------------------------------------------------
# The fork's keyword-only urgency (no meaning model)
def fork_funcs():
    import assistant
    from engine import confidence, typos
    assert typos.words_for() is not None, 'library search index not found: set LASTBOOK_DATA'

    def c1(t):   # assistant.danger_signs
        return bool(assistant.danger_signs(t))

    def c2(t):   # confidence.urgent as typed
        return bool(confidence.urgent(t))

    def c3(t):   # confidence.urgent with typo correction, as assistant.is_danger calls it
        return bool(confidence.urgent(t, typos.correct(t)))

    def c(t):    # assistant.is_danger without the meaning check: danger_signs OR urgent(typed, corrected)
        fixed = typos.correct(t)
        return bool(assistant.danger_signs(t) or confidence.urgent(t, fixed))
    return assistant, confidence, typos, {'danger_signs': c1, 'urgent_typed': c2, 'urgent_typo_fixed': c3, 'fork': c}


# ----------------------------------------------------------------------------------------------------------------
# Inventory
def split_top(s):
    """Split a regex string at its depth-0 '|'."""
    out, d, cur, i, cls = [], 0, '', 0, False
    while i < len(s):
        ch = s[i]
        if ch == '\\':
            cur += s[i:i + 2]; i += 2; continue
        if cls:
            cls = ch != ']'
        elif ch == '[':
            cls = True
        elif ch == '(':
            d += 1
        elif ch == ')':
            d -= 1
        if ch == '|' and d == 0 and not cls:
            out.append(cur); cur = ''
        else:
            cur += ch
        i += 1
    out.append(cur)
    return [x for x in out if x]


def outer_groups(pattern):
    """The contents of each top-level \\b( ... )\\b group of a pattern (URGENT, BODY_*)."""
    out, i = [], 0
    while True:
        j = pattern.find(r'\b(', i)
        if j < 0:
            return out
        k, d = j + 3, 1
        while d:
            if pattern[k] == '\\':
                k += 2; continue
            d += (pattern[k] == '(') - (pattern[k] == ')')
            k += 1
        out.append(pattern[j + 3:k - 1]); i = k


def kind(alt):
    a = alt.replace(r"'?", "'")           # can'?t is a plain contraction with an optional apostrophe
    if re.fullmatch(r"[a-z' ]+", a) and "'?" not in alt and alt == a:
        return 'plain word/phrase'
    if re.fullmatch(r"[a-z' ]+(\\w\*)?", a):
        return 'stem (word\\w*)'
    if re.search(r"\.\{\d,\d+\}|\(\\w\+ \)\{|\\b.*\.\{", alt):
        return 'window (words in between)'
    if '(' in alt or '?' in alt or '[' in alt:
        return 'regex with optional/alternative words'
    return 'plain word/phrase' if re.fullmatch(r"[a-z' ]+", alt) else 'stem (word\\w*)'


CATS = [
    ('suicide / self-harm', r"suicid|kill\W*\(?.*sel|self.harm|live anymore|end \(?it|goodbye|disappear|better off|no reason to live|to die|take my|hang"),
    ('choking', r"chok"),
    ('not breathing / airway', r"breath|suffocat|strangl|gasp|gurgl|agonal|stridor|snor"),
    ('unconscious / collapse / not responding', r"unconsc|unrespons|collaps|faint|pass\(ed\)\? out|passed|blacked|wake|rous|out cold|keel|slump|face ?down|on the \(?(floor|ground)|\bfloor\b|respon|react|answer|limp|floppy|not moving|mov(e|ing)|paralys|dropped|went down|fell down|come round|com\(e|open"),
    ('cardiac / pulse / CPR', r"pulse|cpr|heart|cardiac|palpit"),
    ('chest pain', r"chest"),
    ('stroke', r"stroke|droop|slurr|speak|crooked|lopsided|talk|words|(arms?|legs?|feet|toes|hands?|side|face|body)|eye|sight|vision|headache|funny turn|came over|c\(a\|o\)me"),
    ('anaphylaxis / allergy / asthma', r"allerg|anaphyl|epi ?pen|swell|lips?|sting|stung|wheez|asthma|venom|tongue"),
    ('overdose / poisoning', r"poison|swallow|overdos|over ?dos|pill|tablet|capsule|drank|\bate\b|eaten|bleach|chemical|kerosene|opioid|heroin|fentanyl|xanax|valium|paracetamol|acetaminophen|tylenol|panadol|ibuprofen|aspirin|medic|painkill|drunk|drink|cleaning|box|bottle|downed|sleep"),
    ('seizure / fit', r"seiz|siez|convuls|\bfit|shaking|foam|froth|roll|twitch|jerk"),
    ('bleeding / wounds', r"bleed|blood|spurt|wound|gash|hem\w*rrhag|haemorrhag|tourniquet|gush|pour|squirt|pump|soak|stab|shot|shoot|gun|knife|impal|amputat|sever|cut|sliced|bleeding|oozing|dripping"),
    ('burns / fire / smoke', r"burn|scald|fire|flame|smok|spark|explo|blister|firework"),
    ('drowning / water / flood', r"drown|submerg|swept|current|flood|\bice\b|under \(|water|sinking"),
    ('gas / CO / fumes', r"gas\b|fumes|carbon monoxide|monoxide|generator"),
    ('electric / lightning', r"electr|shock|lightning|live wire|power ?line"),
    ('pregnancy / birth / newborn', r"labou?r|birth|pregnan|contraction|water broke|newborn|baby|infant|miscarr"),
    ('hypothermia / heat / cold', r"hypotherm|frostbite|shiver|heat|frozen|freezing|toes"),
    ('head / spine / fall / crush / trapped', r"head|skull|neck|spine|spinal|fell|fall|roof|crush|trapped|pinned|rubble|buried|landslide|mud|avalanche"),
    ('injury / fracture / eye / teeth', r"injur|fractur|bone|broke|broken|eye|tooth|teeth|nose|ear\)|cast|hurt|accident|nail|stuck|car\b|crash|vehicle"),
    ('disaster / violence', r"earthquake|tsunami|tornado|hurricane|attack|intruder|break|braking|riot|hostage|bomb|radiation|fallout|nuclear"),
    ('infection / sepsis / swelling', r"cellulit|sepsis|septic|swollen|red\)|leaking"),
    ('generic distress (help, pain, pale, sweaty, weak, ...)', r"help|emergency|ambulance|hospital|pain|weak|numb|sweat|pale|blue|grey|gray|ashen|mottled|dying|dead|sleepy|drowsy|vomit|puk|throw|spew|fever|rash|colou?r|confus|sugar|diabet|not making|stand|walk|pee|wee|urin|lips"),
]


def category(alt):
    for name, rx in CATS:
        if re.search(rx, alt, re.I):
            return name
    return 'other'


def inventory(assistant, confidence, typos):
    rows = []     # (source, category, kind, text)
    for k, rx in assistant.DANGER.items():
        for alt in split_top(rx.pattern):
            rows.append(('assistant.DANGER', k, kind(alt), alt))
    for g in outer_groups(confidence.URGENT.pattern):
        for alt in split_top(g):
            rows.append(('confidence.URGENT', category(alt), kind(alt), alt))
    for k, rx in confidence.BODY_PHRASES.items():
        for alt in split_top(rx.pattern):
            rows.append(('confidence.BODY_PHRASES', k, kind(alt), alt))
    for w, s in confidence.BODY_WORDS.items():
        rows.append(('confidence.BODY_WORDS', s, 'plain word/phrase', w))
    for rx, words, sign in confidence.BODY_GLUED:
        rows.append(('confidence.BODY_GLUED', sign, 'glued stem', rx.pattern))
    nu = confidence.NOT_URGENT
    for alt in split_top(nu.pattern.replace(r'\b(?:', r'\b(')):
        rows.append(('confidence.NOT_URGENT (suppresses)', 'idioms', 'regex', alt))
    ty = {'typos.SLIPS': len(getattr(typos, 'SLIPS', {})), 'typos.PHRASE_SLIPS': len(getattr(typos, 'PHRASE_SLIPS', {})),
          'typos.APOSTROPHES': len(getattr(typos, 'APOSTROPHES', {}))}
    return rows, ty


# ----------------------------------------------------------------------------------------------------------------
def node_check(texts, sets_by_name):
    """Run web/words.js itself in Node over every text and phrase set; return the number of disagreements with the port."""
    node = shutil.which('node')
    if not node:
        return None
    js = r"""
const fs=require('fs');globalThis.window=globalThis;require(process.argv[2]);const W=globalThis.SearchWords;
const inp=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
function names(all,p){return all.some((_,i)=>p.every((w,j)=>all[i+j]===w))}
const out={};
for(const [setname,phrases] of Object.entries(inp.sets)){
  const ps=phrases.map(ph=>[ph,W.splitWords(ph)]).filter(x=>x[1].length);
  out[setname]=inp.texts.map(t=>{const a=W.splitWords(t);return ps.filter(x=>names(a,x[1])).map(x=>x[0])});
}
fs.writeFileSync(process.argv[4],JSON.stringify(out));
"""
    tmp = HERE / '_node_tmp'
    tmp.mkdir(exist_ok=True)
    (tmp / 'check.js').write_text(js, encoding='utf-8')
    (tmp / 'in.json').write_text(json.dumps({'texts': texts, 'sets': sets_by_name}), encoding='utf-8')
    r = subprocess.run([node, str(tmp / 'check.js'), str(REPO / 'web' / 'words.js'), str(tmp / 'in.json'), str(tmp / 'out.json')],
                       capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        return f'node failed: {r.stderr[:300]}'
    res = json.loads((tmp / 'out.json').read_text(encoding='utf-8'))
    diff = 0
    for name, phrases in sets_by_name.items():
        cp = compile_phrases(phrases)
        for t, js_m in zip(texts, res[name]):
            if sorted(matches(t, cp)) != sorted(js_m):
                diff += 1
    shutil.rmtree(tmp, ignore_errors=True)
    return diff


# ----------------------------------------------------------------------------------------------------------------
def main():
    cur, prop = load_current(), load_proposed()
    cur_c, prop_c = compile_phrases([p for _, p in flat(cur)]), compile_phrases([p for _, p in flat(prop)])
    lines = load_lines()
    assistant, confidence, typos, F = fork_funcs()

    out = {'sets': {}, 'phrase_counts': {'current': sum(len(v) for v in cur.values()), 'proposed': sum(len(v) for v in prop.values()),
                                         'proposed_per_choice': {k: len(v) for k, v in prop.items()}}}
    per_phrase = {}
    examples = {'green_flagged_by_b': [], 'yellow_flagged_by_b': [], 'red_missed_by_d': [], 'red_only_fork': [], 'red_only_b': []}
    for name, rows in lines.items():
        cnt = {}
        for i, (t, col) in enumerate(rows):
            a = bool(matches(t, cur_c))
            bm = matches(t, prop_c)
            b = bool(bm)
            e = bool(matches(confidence.not_urgent_text(t), prop_c))
            cs = {k: f(t) for k, f in F.items()}
            c = cs['fork']
            flags = {'a': a, 'b': b, 'c': c, 'd': b or c, 'e': e, 'f': e or c, 'c_danger_signs': cs['danger_signs'], 'c_urgent_typed': cs['urgent_typed'],
                     'c_urgent_typo_fixed': cs['urgent_typo_fixed'], 'b_only_not_c': b and not c, 'c_only_not_b': c and not b}
            cc = cnt.setdefault(col, {'n': 0})
            cc['n'] += 1
            for k, v in flags.items():
                cc[k] = cc.get(k, 0) + int(v)
            for ph in bm:
                pp = per_phrase.setdefault(ph, {'red': 0, 'yellow': 0, 'green': 0})
                pp[col] += 1
            tag = f'{name}: {t}'
            if b and col == 'green': examples['green_flagged_by_b'].append((tag, bm))
            if b and col == 'yellow': examples['yellow_flagged_by_b'].append((tag, bm))
            if col == 'red' and not flags['d']: examples['red_missed_by_d'].append(tag)
            if col == 'red' and c and not b: examples['red_only_fork'].append(tag)
            if col == 'red' and b and not c: examples['red_only_b'].append(tag)
        out['sets'][name] = cnt
    out['per_phrase_hits'] = dict(sorted(per_phrase.items(), key=lambda kv: -(kv[1]['green'] * 3 + kv[1]['yellow'])))
    out['examples'] = examples

    alltexts = [t for rows in lines.values() for t, _ in rows]
    out['node_check_disagreements'] = node_check(alltexts, {'current': [p for _, p in flat(cur)], 'proposed': [p for _, p in flat(prop)]})

    rows, ty = inventory(assistant, confidence, typos)
    inv = {}
    for src, cat, kd, _ in rows:
        inv.setdefault(src, {}).setdefault(cat, {}).setdefault(kd, 0)
        inv[src][cat][kd] += 1
    out['inventory'] = inv
    out['inventory_typo_tables'] = ty
    out['inventory_alternatives'] = [list(r) for r in rows]
    (HERE / 'measure_out.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')

    # ---- print
    print('phrases: current', out['phrase_counts']['current'], 'proposed', out['phrase_counts']['proposed'])
    print('node check disagreements (port vs web/words.js):', out['node_check_disagreements'])
    hdr = f"{'list':13} {'colour':7} {'n':>4} | {'a #167 now':>10} {'b proposed':>10} {'c fork kw':>10} {'d b OR c':>9} | c: signs / typed / typo-fixed | b-not-c c-not-b | e: b after NOT_URGENT | f: e OR c"
    print(hdr)
    tot = {}
    for name, cnt in out['sets'].items():
        for col in ('red', 'yellow', 'green'):
            x = cnt[col]
            print(f"{name:13} {col:7} {x['n']:>4} | {x['a']:>10} {x['b']:>10} {x['c']:>10} {x['d']:>9} | {x['c_danger_signs']:>4} / {x['c_urgent_typed']:>4} / {x['c_urgent_typo_fixed']:>4} | {x['b_only_not_c']:>4} {x['c_only_not_b']:>4} | {x['e']:>4} | {x['f']:>4}")
            t = tot.setdefault(col, {})
            for k, v in x.items():
                t[k] = t.get(k, 0) + v
    for col, x in tot.items():
        print(f"{'ALL':13} {col:7} {x['n']:>4} | {x['a']:>10} {x['b']:>10} {x['c']:>10} {x['d']:>9} | {x['c_danger_signs']:>4} / {x['c_urgent_typed']:>4} / {x['c_urgent_typo_fixed']:>4} | {x['b_only_not_c']:>4} {x['c_only_not_b']:>4} | {x['e']:>4} | {x['f']:>4}")
    out['totals'] = tot
    (HERE / 'measure_out.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print('\ninventory (alternatives per source / category / kind):')
    for src, cats in inv.items():
        print(src, sum(sum(k.values()) for k in cats.values()))
        for cat, kinds in sorted(cats.items(), key=lambda kv: -sum(kv[1].values())):
            print('   ', cat, sum(kinds.values()), dict(kinds))
    print(ty)
    print('\nphrases with most green/yellow hits:')
    for ph, v in list(out['per_phrase_hits'].items())[:15]:
        print('  ', ph, v)
    print('\nred missed by d:', len(examples['red_missed_by_d']), ' green flagged by b:', len(examples['green_flagged_by_b']))


if __name__ == '__main__':
    main()
