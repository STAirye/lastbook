"""Top-8 of /api/retrieve for each question on two servers (before = PR base, after = PR 128).
A hit counts as useful when its title or excerpt matches the question's topic pattern (rough, like PR 128's own measure)."""
import json, re, sys, urllib.parse, urllib.request

BEFORE, AFTER = 'http://127.0.0.1:8897', 'http://127.0.0.1:8895'
BURN = r'burn|scald'
FIREMAKE = r'tinder|kindling|firecraft|fire ?start|bow drill|flint|ferro|friction|fire[- ]making|lighting a fire|starting a fire'
WATERSAFE = r'disinfect|purif|chlorin|bleach|boil(ing)? water|treat(ing|ment)? water|safe water|drinking water'
CASES = [
    # group, question, topic
    ('injury+phrase', 'burned my hand trying to light a fire', BURN),
    ('injury+phrase', 'i burnt my fingers lighting the campfire', BURN),
    ('injury+phrase', 'smoke inhalation from lighting a fire indoors', r'smoke|inhal|carbon monoxide'),
    ('injury+phrase', 'carbon monoxide from making a fire in the tent', r'carbon monoxide|\bco\b poison|monoxide'),
    ('injury+phrase', 'my clothes caught fire while starting the fire', r'burn|stop,? drop|roll|clothing (on|catch)'),
    ('injury+phrase', 'my kid fell into the fire while we were making a fire', BURN),
    ('injury+phrase', 'treat water in the lungs after drowning', r'drown|resuscitat|rescue breath|cpr|near-drown'),
    ('injury+phrase', 'how do i treat water blisters on a burn', r'blister|burn'),
    ('injury+phrase', 'how do i treat water poisoning', r'poison|diarrh|contaminat|dehydrat|rehydrat|water-?borne'),
    ('injury+phrase', 'light a fire to keep him warm with hypothermia', r'hypotherm|rewarm|cold injur'),
    ('injury', 'my son nearly drowned in the rainwater pool', r'drown|resuscitat|rescue breath|cpr'),
    ('injury', "someone fell in the rainwater pool and isn't breathing", r'drown|resuscitat|rescue breath|cpr|not breathing|breathing'),
    ('injury', "he swallowed pool water and now he's coughing", r'drown|cough|aspirat|breath'),
    ('injury', 'drank creek water and now i have diarrhea', r'diarrh|rehydrat|dehydrat'),
    ('injury', 'my child swallowed lamp oil', r'poison|kerosene|paraffin|petroleum|swallow'),
    ('injury', 'scorpion sting on my foot', r'scorpion|sting'),
    ('injury', 'rash from poison ivy', r'poison ivy|poison oak|rash|urushiol'),
    ('injury', 'snake bite while camping', r'snake|bite|venom'),
    ('injury', 'hypothermia after falling in cold water', r'hypotherm|rewarm|cold water'),
    ('injury', 'someone got shocked by a wire in the flood water', r'electric|shock|electrocut'),
    ('injury', 'is it safe to put water on a burn', BURN),
    ('injury', 'i burned my hand on the camp stove', BURN),
    ('injury', 'how do i treat a burn from a campfire', BURN),
    ('how-to', 'how do i light a campfire', FIREMAKE),
    ('how-to', 'i need to start a fire but i have no matches and no gas', FIREMAKE),
    ('how-to', 'how do i make the water safe to drink', WATERSAFE),
    ('how-to', 'how do i purify water from a creek', WATERSAFE),
    ('how-to', 'how to make the water safe for a baby\'s formula', WATERSAFE + r'|formula'),
    ('safety', 'make a fire escape plan for my family', r'escape|evacuat|exit|smoke alarm|fire safety'),
    ('safety', 'what could make a fire spread faster', r'spread|fire safety|flammab|prevent'),
    ('safety', 'pour water on a grease fire', r'grease|kitchen fire|cooking fire|smother|extinguish'),
    ('safety', 'how do i treat water damage on the floor', r'flood|water damage|mold|mould|dry(ing)? out'),
]


def top(base, q):
    u = base + '/api/retrieve?' + urllib.parse.urlencode({'q': q, 'k': 8})
    with urllib.request.urlopen(u, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))['results']


def useful(hits, pat):
    return sum(1 for h in hits if re.search(pat, (h['title'] + ' ' + (h.get('excerpt') or '')), re.I))


rows = []
for grp, q, pat in CASES:
    b, a = top(BEFORE, q), top(AFTER, q)
    rows.append({'group': grp, 'q': q, 'before': useful(b, pat), 'after': useful(a, pat),
                 'before_titles': [f"{h['title']} p.{h['page']}" for h in b],
                 'after_titles': [f"{h['title']} p.{h['page']}" for h in a],
                 'after_excerpts': [(h.get('excerpt') or '')[:140] for h in a]})
    print(f"{grp:14} {rows[-1]['before']}/8 -> {rows[-1]['after']}/8  {q}")
json.dump(rows, open(sys.argv[1], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
