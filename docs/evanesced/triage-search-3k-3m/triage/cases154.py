"""Issue #154's 32 questions (check_search_tiers.py), labelled for the triage scorer (score.py).

Labelled BLIND, 2026-11-18: colour, need, context and not_first were written from each question's meaning before any
of this run's results were looked at. (The issue's aggregate before/after counts had been read; no per-hit titles.)
cases.py's own labels for the same questions were not consulted while writing these; agreement is checked afterwards
in RESULTS_154.md.

  colour   red = act now (airway, breathing, circulation, fire now, poisoning in a child); yellow = injury or illness
           without a danger sign; green = how-to / preparation.
  need     P keys, most urgent first; first result right = need[0] matches hit 1.
  context  the setting (fire being lit, pool, flood, water treatment): pages that match only this are "context".
  not_first  only for questions whose emergency word has an everyday meaning here (the first page must not be about it).
  typo     the same question typed in a panic (same rules as cases.py: dropped/doubled/swapped letters, sound-alikes,
           no apostrophes). Written before results too.
  pat154   #154's own topic regex (check_search_tiers.py), for its useful-of-8 count.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('cases', Path(__file__).resolve().parent / 'cases.py')
_cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cases)

P = dict(_cases.P)
# two needs no cases.py key describes
P['FIRESPREAD'] = r"spread|fire behavio|flammab|combustib|fire triangle|oxygen|fuel load|fire safety|fire prevent"
P['WATERDAMAGE'] = r"water damage|flood(ed|ing)? (home|house|building|floor)|mold|mould|dry(ing)? out|dehumidif|wet (floor|carpet)|flood clean"

BURN154 = r'burn|scald'
FIREMAKE154 = r'tinder|kindling|firecraft|fire ?start|bow drill|flint|ferro|friction|fire[- ]making|lighting a fire|starting a fire'
WATERSAFE154 = r'disinfect|purif|chlorin|bleach|boil(ing)? water|treat(ing|ment)? water|safe water|drinking water'


def C(group, q, pat154, colour, need, typo, context=(), not_first=()):
    return {'group': group, 'q': q, 'pat154': pat154, 'colour': colour, 'need': list(need), 'context': list(context),
            'not_first': list(not_first), 'typo': typo}


CASES = [
    C('injury+phrase', 'burned my hand trying to light a fire', BURN154, 'yellow', ['BURN'],
      'burnd my hand tryng to lite a fire', ['C_FIREMAKE']),
    C('injury+phrase', 'i burnt my fingers lighting the campfire', BURN154, 'yellow', ['BURN'],
      'i brunt my fingrs lighting the campfier', ['C_FIREMAKE']),
    C('injury+phrase', 'smoke inhalation from lighting a fire indoors', r'smoke|inhal|carbon monoxide', 'red',
      ['SMOKEINH', 'CO'], 'smoke inhalaton from lightin a fire inside', ['C_FIREMAKE']),
    C('injury+phrase', 'carbon monoxide from making a fire in the tent', r'carbon monoxide|\bco\b poison|monoxide', 'red',
      ['CO'], 'carbon monoxid from making a fire in the tnet', ['C_FIREMAKE', 'C_TENT']),
    C('injury+phrase', 'my clothes caught fire while starting the fire', r'burn|stop,? drop|roll|clothing (on|catch)', 'red',
      ['CLOTHES', 'BURN'], 'my cloths cought fire wile starting the fire', ['C_FIREMAKE']),
    C('injury+phrase', 'my kid fell into the fire while we were making a fire', BURN154, 'red', ['BURN'],
      'my kid fel into the fire wile we were makin a fire', ['C_FIREMAKE']),
    C('injury+phrase', 'treat water in the lungs after drowning', r'drown|resuscitat|rescue breath|cpr|near-drown', 'red',
      ['DROWN', 'CPR'], 'treat watter in the lungs after drownin', ['C_WATERTREAT']),
    C('injury+phrase', 'how do i treat water blisters on a burn', r'blister|burn', 'yellow', ['BURN', 'BLISTER'],
      'how do i treat water blisers on a burn', ['C_WATERTREAT']),
    C('injury+phrase', 'how do i treat water poisoning', r'poison|diarrh|contaminat|dehydrat|rehydrat|water-?borne', 'yellow',
      ['POISON', 'DIARR'], 'how do i treat water posioning'),
    C('injury+phrase', 'light a fire to keep him warm with hypothermia', r'hypotherm|rewarm|cold injur', 'red',
      ['HYPOTHERM'], 'lite a fire to keep him warm with hypothrmia', ['C_FIREMAKE']),
    C('injury', 'my son nearly drowned in the rainwater pool', r'drown|resuscitat|rescue breath|cpr', 'red',
      ['DROWN', 'CPR'], 'my sun neary drowned in the rainwater pool', ['C_POOL']),
    C('injury', "someone fell in the rainwater pool and isn't breathing",
      r'drown|resuscitat|rescue breath|cpr|not breathing|breathing', 'red', ['CPR', 'DROWN'],
      'somone fell in the rainwater pool and isnt breathing', ['C_POOL']),
    C('injury', "he swallowed pool water and now he's coughing", r'drown|cough|aspirat|breath', 'yellow', ['DROWN'],
      'he swalowed pool water and now hes coughing', ['C_POOL']),
    C('injury', 'drank creek water and now i have diarrhea', r'diarrh|rehydrat|dehydrat', 'yellow', ['DIARR'],
      'drank creek water now i have diarea', ['C_WATERTREAT']),
    C('injury', 'my child swallowed lamp oil', r'poison|kerosene|paraffin|petroleum|swallow', 'red', ['HYDROCARB'],
      'my kid swallowd lamp oyl'),
    C('injury', 'scorpion sting on my foot', r'scorpion|sting', 'yellow', ['SCORPION'], 'scorpian sting on my foot'),
    C('injury', 'rash from poison ivy', r'poison ivy|poison oak|rash|urushiol', 'yellow', ['RASH'], 'rash from posion ivy',
      not_first=['POISON']),
    C('injury', 'snake bite while camping', r'snake|bite|venom', 'red', ['SNAKE'], 'snak bite while campin', ['C_TENT']),
    C('injury', 'hypothermia after falling in cold water', r'hypotherm|rewarm|cold water', 'red', ['HYPOTHERM'],
      'hypothermia after faling in cold watr'),
    C('injury', 'someone got shocked by a wire in the flood water', r'electric|shock|electrocut', 'red', ['ELEC', 'CPR'],
      'somone got shoked by a wire in the flood watter', ['C_FLOOD']),
    C('injury', 'is it safe to put water on a burn', BURN154, 'yellow', ['BURN'], 'is it safe to put watr on a burn'),
    C('injury', 'i burned my hand on the camp stove', BURN154, 'yellow', ['BURN'], 'i burnt my hand on the camp stov',
      ['C_TENT']),
    C('injury', 'how do i treat a burn from a campfire', BURN154, 'yellow', ['BURN'], 'how do i treat a burn from a camp fier',
      ['C_FIREMAKE']),
    C('how-to', 'how do i light a campfire', FIREMAKE154, 'green', ['FIREMAKE'], 'how do i light a campfrie',
      not_first=['BURN']),
    C('how-to', 'i need to start a fire but i have no matches and no gas', FIREMAKE154, 'green', ['FIREMAKE'],
      'i need to start a fire but no matchs and no gas', not_first=['GASLEAK']),
    C('how-to', 'how do i make the water safe to drink', WATERSAFE154, 'green', ['PURIFY'],
      'how do i make the water safe to drik'),
    C('how-to', 'how do i purify water from a creek', WATERSAFE154, 'green', ['PURIFY'], 'how do i purfy water from a creek'),
    C('how-to', "how to make the water safe for a baby's formula", WATERSAFE154 + r'|formula', 'green', ['PURIFY', 'FORMULA'],
      'how to make the water safe for babys formla'),
    C('safety', 'make a fire escape plan for my family', r'escape|evacuat|exit|smoke alarm|fire safety', 'green', ['ESCAPE'],
      'make a fire escape plan for my famly', not_first=['BURN']),
    C('safety', 'what could make a fire spread faster', r'spread|fire safety|flammab|prevent', 'green', ['FIRESPREAD'],
      'what could make a fire spred faster', not_first=['BURN']),
    C('safety', 'pour water on a grease fire', r'grease|kitchen fire|cooking fire|smother|extinguish', 'red', ['GREASE'],
      'pour watter on a greese fire'),
    C('safety', 'how do i treat water damage on the floor', r'flood|water damage|mold|mould|dry(ing)? out', 'green',
      ['WATERDAMAGE'], 'how do i treat water damge on the floor', not_first=['C_WATERTREAT', 'POISON']),
]
