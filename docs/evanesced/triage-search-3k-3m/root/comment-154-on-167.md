#167 fixes the same kind of failure in the guides: both searches count matching words, so the words around an emergency
outvote the sign that matters ("burn and not breathing" shows Burn; "water in the lungs after drowning" shows wastewater
manuals). #167 handles it with `urgent` phrases on a choice. Three things this issue should take from it:

- **One list of emergency words, not two.** #167's list for Not breathing is "not breathing", "stopped breathing", "isn't
  breathing", "isnt breathing" and "unconscious". `server.PHRASES` has "not breathing" and "stopped breathing" but not
  "isn't breathing", which is part of why "someone fell in the rainwater pool and isn't breathing" gets 3 of 8 above. A
  list in `words.js` and another in `server.py` will drift apart. The server could read the `urgent` phrases from
  `content/topics/` instead.
- **Leave out words that also describe non-emergencies.** #167 leaves out "not responding", "unresponsive" and "choking"
  for that reason ("not responding to antibiotics", "allergic reaction choking"). The list proposed above has "choking"
  and "shock(ed)", which have the same problem ("choking on smoke" with a burn, an electric shock against circulatory
  shock). They should go too, or need a narrower phrase.
- **Check every combination.** #167 paired every phrase with every guide word (10,213 searches) and found that only the
  intended choice changed. The check here could do the same with every emergency word and every `PHRASES` entry, on top
  of the 32 questions.

#167 picks the choice within a guide, not which guide shows: its own limit is "unresponsive after a seizure", which
still lists the earthquake guide first. That is the guide-level version of the tiers proposed here, so the two could
share the same rule once this one is settled.
