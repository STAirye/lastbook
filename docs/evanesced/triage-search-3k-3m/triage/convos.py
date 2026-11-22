"""Multi-turn conversations for triage-ranked search. Invented situations only.

Each conversation is a list of (message, kind) where kind is what the message is to the conversation so far:
  first     the opening message
  follow    follow-up on the same need ("and at night?")
  add       adds a need or a danger sign ("now he's not breathing")
  correct   replaces what the earlier message asked ("NO NO I MEAN the smoke")
  noise     unrelated or garbled (pocket typing, "sorry wrong chat"): changes nothing, should get buttons
  new       a different emergency, not noise ("THE KITCHEN IS ON FIRE")
need / context are pattern keys from cases.P for the LAST message, as in cases.py.
"""


def C(colour, turns, need, context=()):
    return {'colour': colour, 'turns': turns, 'need': list(need), 'context': list(context), 'not_first': []}


CONVOS = [
    # ------------------------------------------------------------------ follow-up
    C('green', [('how do i purify water from a creek', 'first'), ('and if i have no bleach?', 'follow')], ['PURIFY']),
    C('green', [('how to use a fire extinguisher', 'first'), ('which type for the kitchen', 'follow')], ['EXTING']),
    C('red', [('snake bite while camping', 'first'), ('what should i not do', 'follow')], ['SNAKE']),
    C('yellow', [('my baby has a fever', 'first'), ('how much paracetamol can she have', 'follow')], ['FEVER']),
    C('green', [('how do i light a campfire', 'first'), ('what if the wood is wet', 'follow')], ['FIREMAKE']),
    C('yellow', [('i think my arm is broken', 'first'), ('how do i make a splint', 'follow')], ['SPLINT', 'FRACTURE']),
    C('red', [('heat stroke what to do', 'first'), ('how do i cool him down fast', 'follow')], ['HEATSTROKE']),
    C('red', [('i smell gas in the house', 'first'), ('should i open the windows', 'follow')], ['GASLEAK']),
    C('green', [('how to store water for an emergency', 'first'), ('how long does it keep', 'follow')], ['STOREWATER']),
    C('yellow', [('a dog bit my hand', 'first'), ('do i need a rabies shot', 'follow')], ['BITE']),
    C('yellow', [('my child has diarrhea', 'first'), ('how do i make the salt and sugar drink', 'follow')], ['DIARR', 'DEHYD']),
    C('red', [('earthquake happening what do i do', 'first'), ('and after the shaking stops?', 'follow')], ['QUAKE']),
    # ------------------------------------------------------------------ addition
    C('red', [('cut my hand badly with a knife', 'first'), ('now he is pale and dizzy', 'add')], ['SHOCK', 'BLEED']),
    C('red', [('i burned my hand on the stove', 'first'), ("and now he can't breathe from the smoke", 'add')], ['SMOKEINH', 'BURN']),
    C('red', [('he fell off the roof', 'first'), ('and his leg is bent the wrong way', 'add')], ['FRACTURE', 'SPINE']),
    C('red', [('stung by a bee', 'first'), ('now her throat is swelling', 'add')], ['ANAPH']),
    C('red', [('my kid hit his head', 'first'), ('now he keeps vomiting', 'add')], ['HEAD']),
    C('red', [('hypothermia after falling in cold water', 'first'), ('he also has white numb fingers', 'add')], ['HYPOTHERM', 'FROSTBITE']),
    C('red', [('diarrhea for two days', 'first'), ("now she's very sleepy and won't drink", 'add')], ['DEHYD']),
    C('red', [('the oil in the pan caught fire', 'first'), ('and my husband burned his arm', 'add')], ['BURN', 'GREASE']),
    C('red', [('flood water in the house', 'first'), ('and there are electric wires in the water', 'add')], ['ELEC'], ['C_FLOOD']),
    C('red', [('a snake bit my leg', 'first'), ('now the leg is swelling a lot', 'add')], ['SNAKE']),
    # ------------------------------------------------------------------ correction
    C('red', [('burned my hand lighting the fire', 'first'), ("no no i mean the smoke, he can't breathe", 'correct')], ['SMOKEINH'], ['C_FIREMAKE']),
    C('red', [('my son is choking', 'first'), ('no i mean he swallowed bleach', 'correct')], ['CAUSTIC']),
    C('red', [('how do i treat a burn', 'first'), ('not me, the baby, boiling water spilled on her', 'correct')], ['BURN']),
    C('red', [('my dad is dizzy', 'first'), ("no i mean he's having chest pain down his arm", 'correct')], ['HEART']),
    C('red', [('how to start a fire', 'first'), ('no, how to put out a grease fire in the pan', 'correct')], ['GREASE'], ['C_FIREMAKE']),
    C('red', [('she fell in the pool', 'first'), ("no she's out of the water but not breathing", 'correct')], ['CPR', 'DROWN'], ['C_POOL']),
    C('yellow', [('how do i purify water', 'first'), ('no i mean he drank dirty water and has diarrhea', 'correct')], ['DIARR'], ['C_WATERTREAT']),
    C('red', [('a power line is down on the street', 'first'), ('no i mean he touched it and collapsed', 'correct')], ['ELEC', 'CPR']),
    C('red', [('my baby has a rash', 'first'), ("no the rash doesn't fade when pressed and she has a fever", 'correct')], ['MENING', 'FEVER']),
    C('yellow', [('spider bite on my foot', 'first'), ('no it was a scorpion', 'correct')], ['SCORPION']),
    C('red', [('where to put a carbon monoxide detector', 'first'), ('NO I MEAN WE ALL HAVE HEADACHES AND THE GENERATOR IS INSIDE', 'correct')], ['CO'], ['C_GENERATOR']),
    C('green', [('how do i use a compass', 'first'), ("no i mean we're lost, how do we signal for help", 'correct')], ['SIGNAL']),
    C('red', [('he is shaking', 'first'), ('no i mean a seizure, foaming at the mouth', 'correct')], ['SEIZURE']),
    # ------------------------------------------------------------------ noise, then the real message
    C('red', [('burned my hand lighting a fire', 'first'), ('jdjdjdk', 'noise'), ('no no the smoke he cant breathe', 'correct')], ['SMOKEINH'], ['C_FIREMAKE']),
    C('red', [('my son is choking', 'first'), ('sorry wrong chat', 'noise'), ("he's turning blue", 'add')], ['CHOKE', 'CPR']),
    C('red', [('snake bite while camping', 'first'), ('asdfgh', 'noise'), ('what do i not do', 'follow')], ['SNAKE']),
    C('red', [('my baby has a fever', 'first'), ('😭😭😭', 'noise'), ('now she is shaking all over', 'add')], ['SEIZURE', 'FEVER']),
    C('red', [('my house is on fire', 'first'), ('wait', 'noise'), ('the kids are upstairs', 'add')], ['ESCAPE']),
    C('red', [('cut my hand', 'first'), ('hhhhhhh', 'noise'), ('it wont stop bleeding', 'add')], ['BLEED']),
    C('red', [('i smell gas', 'first'), ('ok', 'noise'), ('should i turn off the stove', 'follow')], ['GASLEAK']),
    C('red', [('he fell through the ice', 'first'), ('lol sorry', 'noise'), ("he's shivering and confused", 'add')], ['HYPOTHERM']),
    C('red', [('my toddler drank something', 'first'), ('the duck is a mint', 'noise'), ('it was bleach', 'add')], ['CAUSTIC']),
    C('red', [('chest pain', 'first'), ('jfjfjfjf', 'noise'), ('it goes to his left arm', 'add')], ['HEART']),
    C('red', [('stung by a bee', 'first'), ('ignore that', 'noise'), ('her lips are swelling', 'add')], ['ANAPH']),
    C('red', [('flooding in the street', 'first'), ('kkkkk', 'noise'), ('our car is stuck in the water', 'add')], ['FLOODCAR'], ['C_FLOOD']),
    # ------------------------------------------------------------------ a new emergency, not noise
    C('red', [('how do i purify water', 'first'), ('THE KITCHEN IS ON FIRE', 'new')], ['GREASE', 'ESCAPE'], ['C_WATERTREAT']),
    C('red', [('how to store food', 'first'), ('my kid is not breathing', 'new')], ['CPR']),
    C('red', [('how do i use a compass', 'first'), ('a snake just bit my leg', 'new')], ['SNAKE']),
    C('red', [('how to grow tomatoes', 'first'), ('i smell gas in the kitchen', 'new')], ['GASLEAK']),
    C('red', [('how to build a shelter', 'first'), ('my friend fell and is bleeding a lot', 'new')], ['BLEED']),
]
