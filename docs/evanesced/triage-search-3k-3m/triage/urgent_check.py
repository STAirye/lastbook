import json, re, sys
URGENT = re.compile(r"\b(breath\w*|breathing|chok\w*|unconscious|unresponsive|collaps\w*|pass(ed)? out|faint\w*|wake|pulse|cpr"
    r"|bleed\w*|blood\w*|spurt\w*|wound\w*|stab\w*|shot|shoot\w*|gun\w*|knife|impal\w*|amputat\w*|severed|cut off"
    r"|drown\w*|swept|current|flood\w*|ice|submerg\w*|electr\w*|shock\w*|lightning|live wire|power ?lines?"
    r"|burn\w*|scald\w*|fire|flames?|smoke|gas|fumes?|carbon monoxide|generator|explo\w*"
    r"|poison\w*|swallow\w*|drank|ate|pills?|overdos\w*|bleach|chemicals?|kerosene|bitten|bite|snake|sting|stung"
    r"|allerg\w*|swell\w*|anaphyla\w*|asthma|wheez\w*|lips?|blue|seizure\w*|convuls\w*|fit|shaking|foaming"
    r"|stroke|droop\w*|slurr\w*|speak|speek|face|chest|heart|cardiac|diabet\w*|sugar|confus\w*|not making sense"
    r"|fell|fall(en)?|roof|can'?t move|cannot move|paralys\w*|neck|spine|spinal|head injur\w*|skull|trapped|pinned|crush\w*"
    r"|rubble|buried|collapsed|landslide|mud|avalanche|earthquake|tsunami|tornado|hurricane"
    r"|labou?r|birth|pregnan\w*|contractions|newborn|baby|infant|miscarr\w*"
    r"|suicid\w*|kill (him|her|my|them)sel\w*|self.harm|hurt (him|her|my|them)sel\w*|attack\w*|intruder|break(ing)? in|braking into|riot\w*|hostage|bomb"
    r"|hypotherm\w*|frostbite|not shivering|heat ?stroke|hot and confused|emergency|dying|dead|help"
    r"|cut\w*|stuck|nail|pale|sweaty|accident\w*|acident\w*|injur\w*|hurt\w*|pain\w*|weak\w*|numb|not moving|struck|lightening"
    r"|medicine\w*|medication\w*|water broke|head|spark\w*|smok\w*|wildfire\w*|wildfrie|radiation|fallout|nuclear"
    r"|breaking|live anymore|end (it|my life)|car|crash\w*|vehicle|sinking)\b", re.I)
for f in sys.argv[1:]:
    d = json.load(open(f, encoding='utf-8'))
    rows = d['rows']
    for col in ('red', 'yellow', 'green'):
        rs = [r for r in rows if r['colour'] == col and not r['counter']]
        hit = [r for r in rs if URGENT.search(r['q']) or URGENT.search(r['corrected'] or '')]
        print(f, col, len(hit), 'of', len(rs))
        if col == 'red':
            for r in rs:
                if r not in hit: print('   missed:', r['q'])
    cs = [r for r in rows if r['counter']]
    print('counterexamples flagged', sum(1 for r in cs if URGENT.search(r['q'])), 'of', len(cs))
