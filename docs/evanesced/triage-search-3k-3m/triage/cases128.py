"""PR #128's (and issue #126's) example questions, labelled for the triage scorer (score.py). Invented situations only.

Sources (read 2026-11-18, GitHub read-only):
  - #128's unit test SearchWords (app/tests/test_bridge.py in the PR diff): the phrases it must map and the controls it
    must not ("there is a building fire next door", "how do i make it safe to go back inside").
  - #128's review (wonderdawg): the two counterexamples the phrases broke, "how do i prevent a generator from starting
    a fire" and "how do i treat water intoxication".
  - #128's body / issue #126: check_search_fire.py's three questions, the "fire tinder" reference search, and the 20
    everyday prompts with 4 controls (the same list as tools/fork_search_check.py).
  - #128's body also names the phrase stems "make the water safe", "purify water", "treat water": only "treat water"
    is kept (bare and ambiguous); the other two are fragments of questions already here.
  - Not added: the end-to-end follow-up turn ("that looks like a... concerning oversight"): a conversation, not a
    first search (convos.py's format). The other PR the owner closed or finished recently, #170 (test_chat_steps
    reads Node's output as UTF-8), has no questions.

Duplicates of cases.py, left out (same question, or the same with a few words more or less):
  'how do i light a campfire'                                   = cases.py 'campfire' (108.0)
  'i need to start a fire but i have no matches and no gas'     = cases.py 'campfire' (108.1)
  '... no gas, how do i do it' (#126, #128, fork_search_check)  = the same, with "how do i do it"
  'how do i purify water from a creek'                          = cases.py 'purify water' (101.0)
  'how do i make the water safe' (#128 test)                    ~ cases.py 'how do i make the water safe to drink'
  'make the water safe', 'purify water' (#128 body)             ~ cases.py 'purify water' phrasings
  'there is a building fire next door' / 'the fire started in the kitchen' (#128 test) are kept once, in their
  longer fork_search_check wording.

Labelled BLIND, 2026-11-18, before any search result for these questions was run or read (#128's own aggregate
counts had been read long ago; no per-question titles). Same rules as cases.py:
  colour     red = act now (ABCDE; fire now); yellow = injury or illness without a danger sign; green = how-to.
  need       P keys, most urgent first; first_ok = need[0] matches hit 1.
  not_first  only where a word in the question has an emergency or how-to sense that is wrong here (the phrase
             rewrite #128's review caught: firecraft for a generator fire, disinfection for water intoxication).
  typos      the same question typed in a hurry, scored against the first phrasing.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('cases', Path(__file__).resolve().parent / 'cases.py')
_cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cases)

P = dict(_cases.P)
# needs no cases.py key describes
P['WATERINTOX'] = r"water intoxication|hyponatr|over-?hydrat|too much water|drinking too much|electrolyte|sodium"
P['REENTRY'] = r"re-?ent(er|ry|ering)|return(ing)? (home|to (your|the) home)|going back (in|home)|safe to (return|enter|go back)|after the (fire|flood|earthquake|storm)|structural damage|inspect"
P['NORTH'] = r"north|compass|navigat|direction|shadow|sun|stars?\b|bearing"
P['COOKNOPOWER'] = r"cook(ing)?|stove|grill|charcoal|solar cooker|fuel|camp ?fire|hay ?box|fireless"
P['INFANTFEED'] = r"infant (feeding|formula)|breast ?feed|breast ?milk|formula|baby food|wet nurs|relactat|feeding (a |your )?(baby|infant)"
P['ALERT'] = r"radio|noaa|broadcast|alert|warning|emergency (information|news)|news"
P['TPAPER'] = r"toilet paper|wipe|cloth|sanitation|hygiene|latrine|toilet"
P['FLUSH'] = r"flush|bucket|toilet|latrine|sanitation|gr[ae]y ?water"

T = _cases.T

TOPICS = [
    # ------------------------------------------------------------------ #128's purpose: making fire, making water safe
    T('green', 'make fire (128)', ['what is the best way to light a campfire', 'how to start a fire', 'make fire', 'fire tinder'],
      ['FIREMAKE'], typos=['whats the best way to lite a campfire', 'how to strat a fire', 'make fier']),
    T('green', 'water safe no fuel (128)', ['we have no fuel to boil water, how else can i make it safe',
                                            'can i drink the water without boiling it', 'treat water with bleach', 'treat water'],
      ['PURIFY'], typos=['we have no fuel to boil watter how else can i make it safe', 'can i drink the water with out boiling it',
                         'treat watter with bleech']),
    # ------------------------------------------------------------------ fork_search_check's everyday questions ("no X")
    T('green', 'cook without power (128)', ['how do i cook food without electricity or gas'], ['COOKNOPOWER'],
      typos=['how do i cook food with out electricty or gas']),
    T('green', 'out of formula (128)', ['i ran out of baby formula, what can i feed my baby'], ['INFANTFEED'],
      typos=['i ran out of baby formla what can i feed my baby']),
    T('green', 'no soap (128)', ['no soap, how do i wash my hands'], ['HANDWASH'], typos=['no sope how do i wash my hands']),
    T('green', 'keep warm no heating (128)', ['how to keep warm without heating in winter'], ['WARM', 'HEATHOME'],
      typos=['how to keep warm without heatting in winter']),
    T('red', 'bleeding no bandages (128)', ["i don't have bandages, how do i stop the bleeding"], ['BLEED', 'WOUND'],
      typos=['i dont have bandages how do i stop the bleding']),
    T('green', 'north no compass (128)', ['i have no compass, how do i find north'], ['NORTH'],
      typos=['i have no compas how do i find north']),
    T('green', 'food no fridge (128)', ['no refrigerator, how do i keep food safe'], ['FOODSPOIL'],
      typos=['no refridgerator how do i keep food safe']),
    T('green', 'car battery no cables (128)', ['my car battery is dead and i have no jumper cables'], ['CARBATT'],
      not_first=['CPR'], typos=['my car batery is dead and i have no jumper cabels']),
    T('green', 'emergency news no phone (128)', ['no internet or phone, how do i get emergency news'], ['ALERT'],
      typos=['no internet or phone how do i get emergancy news']),
    T('green', 'no toilet paper (128)', ['out of toilet paper, what can i use'], ['TPAPER'],
      typos=['out of toilet papper what can i use']),
    T('yellow', 'no insulin (128)', ['we ran out of insulin and the pharmacy is closed'], ['SUGAR'],
      typos=['we ran out of insulen and the pharmacy is closed']),
    T('green', 'flush no water (128)', ['we have no running water, how do we flush the toilet'], ['FLUSH'],
      typos=['we have no runing water how do we flush the toilet']),
    # ------------------------------------------------------------------ #128's controls (fire as danger, a pulse)
    T('red', 'building fire next door (128)', ['there is a building fire next door, what do we do'], ['ESCAPE'],
      not_first=['FIREMAKE'], typos=['there is a bulding fire next door what do we do']),
    T('red', 'kitchen fire (128)', ['the fire started in the kitchen, how do i put it out'], ['GREASE', 'EXTING'],
      not_first=['FIREMAKE'], typos=['the fire startd in the kitchen how do i put it out']),
    T('red', 'put out a fire (128)', ['how do i put out a fire'], ['EXTING', 'ESCAPE'], not_first=['FIREMAKE'],
      typos=['how do i put out a fier']),
    T('red', 'no pulse (128)', ['he has no pulse, what do i do'], ['CPR'], typos=['he has no puls what do i do']),
    # ------------------------------------------------------------------ #128's review: what the phrases must not catch
    T('green', 'generator fire (128 review)', ['how do i prevent a generator from starting a fire'], ['GENERATOR'],
      not_first=['FIREMAKE'], typos=['how do i prevent a genrator from starting a fire']),
    T('yellow', 'water intoxication (128 review)', ['how do i treat water intoxication'], ['WATERINTOX'],
      not_first=['PURIFY'], typos=['how do i treat water intoxicaton']),
    T('green', 'go back inside (128 test)', ['how do i make it safe to go back inside'], ['REENTRY'], not_first=['PURIFY'],
      typos=['how do i make it safe to go back insde']),
]


def cases():
    """Every phrasing as one case; typos as their own cases tied to the first phrasing (ids prefixed 128.)."""
    out = []
    for i, t in enumerate(TOPICS):
        for j, q in enumerate(t['qs']):
            out.append(dict(t, q=q, id=f'128.{i:02d}.{j}', typo_of=None))
        for j, q in enumerate(t['typos']):
            out.append(dict(t, q=q, id=f'128.{i:02d}.t{j}', typo_of=t['qs'][0]))
    return out
