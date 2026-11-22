"""#241's 21 questions (app/tests/test_topic_search_emergency.py on origin/main, 093b8d3), labelled for the triage
scorer (score.py), to run them through the document search and the confidence model. Invented situations only.

#241 scores the GUIDES (web/words.js rankTopics over content/topics: guide + choice), not the library's pages. Here the
same questions are scored on the first search's top 8 pages, as cases.py is.

Labelled BLIND, 2026-11-18, from each question's meaning, before running them through the document search. #241's own
guide expectations had been read (they are in the file); cases.py / cases154.py labels for the overlapping questions
were not looked up while writing these (agreement is checked afterwards in LESSONS_154.md). No typos: #241 has none,
and this set is for comparing with theirs.
  group      'emergency' or 'counter', as #241 has them.
  guide241   #241's expected (guide, choice); base241 its recorded baseline first result.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('cases154', Path(__file__).resolve().parent / 'cases154.py')
_c154 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_c154)

P = dict(_c154.P)          # cases.py's keys plus FIRESPREAD, WATERDAMAGE
P['PUMP'] = r"pump|well\b|motor|troubleshoot|pressure (switch|tank)"
P['FAINT'] = r"faint|syncope|passed out|unconscious|recovery position|raise (the )?legs|lightheaded|dizz"


def C(group, q, colour, need, guide241, base241, context=(), not_first=()):
    return {'group': group, 'q': q, 'colour': colour, 'need': list(need), 'context': list(context),
            'not_first': list(not_first), 'guide241': list(guide241), 'base241': list(base241), 'typos': []}


CASES = [
    C('emergency', 'treat water in the lungs after drowning', 'red', ['DROWN', 'CPR'], ('hurt', 'breathing'),
      ('water', 'keepclean'), ['C_WATERTREAT']),
    C('emergency', 'someone fell in the rainwater pool and is not breathing', 'red', ['CPR', 'DROWN'], ('hurt', 'breathing'),
      ('hurt', 'breathing'), ['C_POOL']),
    C('emergency', 'my son nearly drowned in the rainwater pool', 'red', ['DROWN', 'CPR'], ('hurt', 'breathing'),
      ('water', 'outside'), ['C_POOL']),
    C('emergency', 'i burnt my fingers lighting the campfire', 'yellow', ['BURN'], ('hurt', 'burn'), ('hurt', 'heatcold'),
      ['C_FIREMAKE']),
    C('emergency', 'burned my hand trying to light a fire', 'yellow', ['BURN'], ('hurt', 'burn'),
      ('disaster', 'earthquake-after'), ['C_FIREMAKE']),
    C('emergency', 'my clothes caught fire while starting the fire', 'red', ['CLOTHES', 'BURN'], ('hurt', 'burn'),
      ('disaster', 'earthquake-after'), ['C_FIREMAKE']),
    C('emergency', 'i burned my hand on the camp stove', 'yellow', ['BURN'], ('hurt', 'burn'), ('food', 'cook'), ['C_TENT']),
    C('emergency', 'my child swallowed lamp oil', 'red', ['HYDROCARB'], ('hurt', 'poison'), ('hurt', 'poison')),
    C('emergency', 'carbon monoxide from making a fire in the tent', 'red', ['CO'], ('shelter', 'co'), ('shelter', 'damaged'),
      ['C_FIREMAKE', 'C_TENT']),
    C('counter', 'not responding to antibiotics', 'yellow', ['INFECT'], ('health', 'medicine'), ('health', 'medicine'),
      not_first=['CPR', 'RECOVERY']),
    C('counter', 'the pump is not responding', 'green', ['PUMP'], ('hurt', 'breathing'), ('hurt', 'breathing'),
      not_first=['CPR', 'RECOVERY']),
    C('counter', 'choking on smoke', 'red', ['SMOKEINH', 'ESCAPE'], ('disaster', 'smoke'), ('disaster', 'smoke'),
      not_first=['CHOKE']),
    C('counter', 'allergic reaction choking', 'red', ['ANAPH'], ('hurt', 'allergy'), ('hurt', 'allergy'), not_first=['CHOKE']),
    C('counter', 'how do i light a campfire', 'green', ['FIREMAKE'], ('power', None), ('power', 'first-hours'),
      not_first=['BURN']),
    C('counter', 'how do i start a fire', 'green', ['FIREMAKE'], ('disaster', None), ('disaster', 'earthquake-after'),
      not_first=['BURN', 'ESCAPE']),
    C('counter', 'boil water', 'green', ['BOIL', 'PURIFY'], ('water', 'unsafe'), ('water', 'unsafe')),
    C('counter', 'make a fire escape plan for my family', 'green', ['ESCAPE'], ('disaster', None),
      ('disaster', 'earthquake-after'), not_first=['FIREMAKE', 'BURN']),
    C('counter', 'what could make a fire spread faster', 'green', ['FIRESPREAD'], ('disaster', None),
      ('disaster', 'earthquake-after'), not_first=['FIREMAKE']),
    C('counter', 'trouble breathing', 'red', ['ASTHMA', 'ANAPH'], ('hurt', 'allergy'), ('hurt', 'allergy')),
    C('counter', 'someone fainted', 'yellow', ['FAINT'], ('hurt', 'breathing'), ('hurt', 'breathing')),
    C('counter', 'food went bad', 'green', ['FOODSPOIL'], ('food', None), ('food', 'outage')),
]


def cases():
    return [dict(c, id=f'241.{i:02d}', topic='241: ' + c['q'], typo_of=None) for i, c in enumerate(CASES)]
