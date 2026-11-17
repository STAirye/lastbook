"""Fork: how the first library search does on everyday questions, most of them saying what the person lacks ("no matches
and no gas"), plus controls.
Runs each prompt against two servers, before and after a change, and counts the top hits that look useful: their title or
excerpt has one of the words a useful page would have. A rough check, so it also prints the titles to read. See
docs/FORK.md, 3h.

    LASTBOOK_DATA=… python server.py --port 8898     (before: e.g. a checkout without the change)
    LASTBOOK_DATA=… python server.py --port 8897     (after)
    python tools/fork_search_check.py [--off 8898] [--on 8897] [-k 8] [-v]
"""
import argparse, json, re, urllib.parse, urllib.request

PROMPTS = [  # (prompt, words a useful page would have)
    ('i need to start a fire but i have no matches and no gas, how do i do it',
     ['flint', 'friction', 'bow', 'drill', 'tinder', 'spark', 'primitive', 'magnif', 'lens', 'steel wool', 'fire starter', 'ferro']),
    ("we have no fuel to boil water, how else can i make it safe",
     ['chlorine', 'bleach', 'disinfect', 'purif', 'iodine', 'solar', 'sodis', 'tablet']),
    ('how do i cook food without electricity or gas', ['cook', 'stove', 'camp', 'grill', 'charcoal', 'solar', 'canned']),
    ('i ran out of baby formula, what can i feed my baby', ['formula', 'infant', 'breast', 'baby']),
    ('no soap, how do i wash my hands', ['hand', 'wash', 'ash', 'sanitiz', 'hygiene']),
    ("how to keep warm without heating in winter", ['warm', 'cold', 'hypotherm', 'layer', 'blanket', 'insulat', 'shelter']),
    ("i don't have bandages, how do i stop the bleeding", ['bleeding', 'pressure', 'tourniquet', 'wound', 'cloth', 'dressing']),
    ('i have no compass, how do i find north', ['north', 'sun', 'star', 'shadow', 'navigat', 'direction']),
    ('no refrigerator, how do i keep food safe', ['food', 'spoil', 'perishable', 'cool', 'canned', 'storage']),
    ('can i drink the water without boiling it', ['water', 'disinfect', 'purif', 'chlorine', 'boil', 'treat']),
    ('my car battery is dead and i have no jumper cables', ['battery', 'jump', 'car', 'vehicle', 'charge']),
    ('no internet or phone, how do i get emergency news', ['radio', 'noaa', 'broadcast', 'alert', 'news', 'emergency']),
    ('out of toilet paper, what can i use', ['toilet', 'sanitation', 'latrine', 'hygiene', 'waste', 'paper']),
    ('we ran out of insulin and the pharmacy is closed', ['insulin', 'diabet', 'medic', 'sugar']),
    ('how do i purify water from a creek', ['disinfect', 'purif', 'chlorine', 'boil', 'filter', 'treat']),
    ('what is the best way to light a campfire', ['tinder', 'kindling', 'campfire', 'fire']),
    # Controls: the negated word is the point, a phrase upstream already reads, or "fire" meaning danger.
    ('there is a building fire next door, what do we do', ['evacuat', 'escape', 'smoke', '911', 'exit', 'get out']),
    ('the fire started in the kitchen, how do i put it out', ['extinguish', 'grease', 'smother', 'lid', 'baking soda', 'put out']),
    ('he has no pulse, what do i do', ['cpr', 'pulse', 'heart', 'compression', 'resuscitat', 'breathing']),
    ('we have no running water, how do we flush the toilet', ['toilet', 'flush', 'water', 'latrine', 'bucket', 'sanitation']),
]


def hits(port, q, k):
    url = f'http://127.0.0.1:{port}/api/retrieve?' + urllib.parse.urlencode({'q': q, 'k': k})
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)['results']


def useful(h, words):
    text = (h['title'] + ' ' + h['excerpt']).lower()
    return any(w in text for w in words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--off', type=int, default=8898)
    ap.add_argument('--on', type=int, default=8897)
    ap.add_argument('-k', type=int, default=8)
    ap.add_argument('-v', action='store_true', help='print the titles')
    a = ap.parse_args()
    tot = {'off': 0, 'on': 0}
    for q, words in PROMPTS:
        row = {}
        for arm, port in (('off', a.off), ('on', a.on)):
            hs = hits(port, q, a.k)
            row[arm] = (sum(useful(h, words) for h in hs), hs)
            tot[arm] += row[arm][0]
        print(f"{row['off'][0]}/{a.k} -> {row['on'][0]}/{a.k}  {q}")
        if a.v:
            for arm in ('off', 'on'):
                for h in row[arm][1]:
                    print(f"      {arm:3} {'+' if useful(h, words) else ' '} {h['title'][:60]} | p. {h['page']}")
    n = len(PROMPTS) * a.k
    print(f"useful hits in the top {a.k}: off {tot['off']} of {n}, on {tot['on']} of {n}")


if __name__ == '__main__':
    main()
