"""Glued words and gibberish for engine/typos.py (splitting) and engine/confidence.py (the unknown-word rule). Invented.

Written 2026-11-18 after the owner's live test: "heschuokinghelkp" (he's choking help, typed with no spaces) got no buttons
and was read as "help". Each case:
  q        the question as typed
  kind     glued_red | glued_everyday | mash | autocorrect | unknown_word | long_word
  split    what the glued question should be searched as (None: nothing to split; for long_word: stays as typed)
  red      it is an emergency: urgent() should be true once the question is understood
  need     cases.py P keys: the first result should match need[0] (empty: no right page, e.g. keyboard mash)
  unsure   the chat should ask for more words (True), should not (False), or either (None)
"""

def C(q, kind, split=None, red=False, need=(), unsure=None):
    return {'q': q, 'kind': kind, 'split': split, 'red': red, 'need': list(need), 'unsure': unsure}


CASES = [
    # glued emergencies (some with typos inside)
    C('heschuokinghelkp', 'glued_red', "he's choking help", True, ['CHOKE'], False),
    C('hesnotbreathing', 'glued_red', "he's not breathing", True, ['CPR'], False),
    C('mybabyisblue', 'glued_red', 'my baby is blue', True, ['CPR', 'CHOKE', 'NEWBORN'], False),
    C('kitchenonfire', 'glued_red', 'kitchen on fire', True, ['GREASE', 'EXTING', 'ESCAPE'], False),
    C('cantstopbleeding', 'glued_red', "can't stop bleeding", True, ['BLEED'], False),
    C('sheschoking', 'glued_red', "she's choking", True, ['CHOKE'], False),
    C('babynotbreathing', 'glued_red', 'baby not breathing', True, ['CPR'], False),
    C('mysonatebleach', 'glued_red', 'my son ate bleach', True, ['CAUSTIC', 'POISON'], False),
    C('snakebitmyleg', 'glued_red', 'snake bit my leg', True, ['SNAKE'], False),
    C('ismellgasinthehouse', 'glued_red', 'i smell gas in the house', True, ['GASLEAK'], False),
    C('hecollapsedandwontwakeup', 'glued_red', "he collapsed and won't wake up", True, ['CPR', 'RECOVERY'], False),
    C('myhusbandishavingaseizure', 'glued_red', 'my husband is having a seizure', True, ['SEIZURE'], False),
    C('chestpainandsweating', 'glued_red', 'chest pain and sweating', True, ['HEART'], False),
    C('hesbleedingalot', 'glued_red', "he's bleeding a lot", True, ['BLEED'], False),
    C('mybbyisntbreathing', 'glued_red', "my baby isn't breathing", True, ['CPR'], False),
    C('hescolapsednotbreathin', 'glued_red', "he's collapsed not breathing", True, ['CPR'], False),
    C('housefireeveryoneout', 'glued_red', 'house fire everyone out', True, ['ESCAPE', 'EXTING'], False),
    C('sheburnedherhand', 'glued_red', 'she burned her hand', True, ['BURN'], False),
    # glued everyday questions
    C('howtopurifywater', 'glued_everyday', 'how to purify water', False, ['PURIFY', 'BOIL'], False),
    C('howdoistorerice', 'glued_everyday', 'how do i store rice', False, [], False),
    C('howtotieabowline', 'glued_everyday', 'how to tie a bowline', False, ['KNOT'], False),
    C('buildarootcellar', 'glued_everyday', 'build a root cellar', False, ['ROOTCELLAR'], False),
    C('howtosplitfirewood', 'glued_everyday', 'how to split firewood', False, ['FIREWOOD', 'WOODCUT'], False),
    C('howtomakesoap', 'glued_everyday', 'how to make soap', False, [], False),
    # keyboard mash
    C('asdfghjkl', 'mash', None, False, [], True),
    C('jdjdk', 'mash', None, False, [], True),
    C('qwertyuiop', 'mash', None, False, [], True),
    C('sdfsdfsdf', 'mash', None, False, [], True),
    C('hjkhjkhjk', 'mash', None, False, [], True),
    C('zxcvbnm', 'mash', None, False, [], True),
    C('fjfjfj dkdkdk', 'mash', None, False, [], True),
    # autocorrect gibberish (real words, wrong ones): nothing to split; recorded, not required
    C('hes chalking help', 'autocorrect', None, None, ['CHOKE'], None),
    C('my bay is blew', 'autocorrect', None, None, [], None),
    C('the duck is a mint', 'autocorrect', None, False, [], None),
    # single unknown words
    C('blorft', 'unknown_word', None, False, [], True),
    C('fghfgh', 'unknown_word', None, False, [], True),
    C('xqzvw', 'unknown_word', None, False, [], True),
    # long real words and names that must stay whole
    C('hypothermia', 'long_word', None, True, ['HYPOTHERM'], False),
    C('electrocution', 'long_word', None, True, ['ELEC'], False),
    C('firecraft', 'long_word', None, False, ['FIREMAKE'], False),
    C('Gutenberg', 'long_word', None, False, [], False),
    C('anaphylaxis', 'long_word', None, True, ['ANAPH'], False),
    C('breastfeeding', 'long_word', None, False, [], False),
    C('overwintering', 'long_word', None, False, [], False),
    C('photosynthesis', 'long_word', None, False, [], False),
    C('how do i treat hypothermia in a child', 'long_word', None, True, ['HYPOTHERM'], False),
    C('what is electrocution', 'long_word', None, True, ['ELEC'], False),
    C('Schwarzenegger', 'long_word', None, False, [], None),
]
