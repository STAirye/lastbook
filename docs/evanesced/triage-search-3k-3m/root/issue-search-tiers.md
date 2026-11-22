**Title:** Search: an injury question that mentions a how-to phrase loses its first-aid pages

**What happens**

`server.PHRASES` turns everyday wording into the manuals' words ("no power" → outage, and with #128 "start a fire" →
tinder/kindling/firecraft, "treat water" → disinfect/chlorine). The phrase's groups are joined to the rest of the
question with AND (`fts_expr`), in both `server.find` and `assistant._fts`. So when a phrase matches, a page has to contain
its words to be found at all. The any-word fallback only runs when fewer than 8 (`find`) or 10 (`_fts`) pages match, and a
large library almost always has more.

That is right for "how do i light a campfire". It is wrong when the question is about an injury and happens to contain
the phrase.

**What it does to results** (Medium pack, keyword search only, `/api/retrieve?k=8`, #128's base `256d52f` against #128)

I counted the top 8 hits whose title or excerpt has a word a useful page would have (burn, drown, resuscitation,
hypothermia, carbon monoxide…). It's rough, so I also read the titles.

| Question | before #128 | with #128 |
|---|---|---|
| treat water in the lungs after drowning | 5 of 8 | 0 of 8 |
| light a fire to keep him warm with hypothermia | 4 of 8 | 0 of 8 |
| carbon monoxide from making a fire in the tent | 8 of 8 | 3 of 8 |
| smoke inhalation from lighting a fire indoors | 6 of 8 | 4 of 8 |
| burned my hand trying to light a fire | 4 of 8 | 2 of 8 |
| i burnt my fingers lighting the campfire | 5 of 8 | 4 of 8 |
| my clothes caught fire while starting the fire | 2 of 8 | 1 of 8 |
| how do i treat water poisoning | 8 of 8 | 6 of 8 |
| make a fire escape plan for my family | 6 of 8 | 3 of 8 |
| what could make a fire spread faster | 3 of 8 | 2 of 8 |

What the titles show:

- **Drowning:** "Basic Emergency Care", "BEC Breathing" and two pages of the "International First Aid Resuscitation and
  Education Guidelines" are replaced by water-treatment notes and wastewater manuals.
- **Hypothermia:** the winter-storm and cold-weather pages are replaced by the fire-starting pages of the survival
  manuals.
- **Carbon monoxide in a tent:** "Outdoor Fire Safety", "Nuclear War Survival Skills" (ventilation) and the cold-weather
  manual are mostly replaced by tinder and kindling pages.

The how-to questions #128 is for do improve, as it says: "how do i light a campfire" 0 → 8 of 8, "start a fire … no
matches and no gas" 2 → 7, "make the water safe for a baby's formula" 5 → 8. Injury questions without a phrase (scorpion
sting, poison ivy, snake bite, a burn from a campfire, hypothermia after falling in cold water) are unchanged.

Adding exceptions to each phrase ("not if the question says burn, drowning, tent…") works for the cases you think of. It
doesn't scale: every new phrase (bites and stings, poisonous plants, cold) needs its own list, and a missed word fails
quietly.

**Some emergency questions are weak before any phrase is involved**

Same measure, the same on both commits:

| Question | top 8 |
|---|---|
| someone got shocked by a wire in the flood water | 0 of 8 |
| he swallowed pool water and now he's coughing | 1 of 8 |
| my son nearly drowned in the rainwater pool | 2 of 8 (a dam design book, a cover-crop survey, a physics textbook) |
| someone fell in the rainwater pool and isn't breathing | 3 of 8 |
| my child swallowed lamp oil | 3 of 8 |
| i burned my hand on the camp stove | 3 of 8 |

The library has these pages (the first-aid and resuscitation guides above). The words around the emergency — rainwater,
pool, flood, camp stove — pull in pages about those things instead.

**Proposal**

Three changes, in this order:

1. **Phrases rank, they don't filter.** Search with the phrase's words and without them, and merge the two result lists.
   Or keep one query and give pages with the phrase's words a bonus. Either way, the drowning pages stay among the
   results. The vocabulary from `PHRASES` is still needed: without it, "light a campfire" never reaches the survival
   manuals.
2. **Emergency words in the question.** A short list, in the same style as `CLINICAL`: burn(ed/t), drown(ed/ing),
   bitten/bite, sting/stung, poison(ed/ing), swallowed, carbon monoxide, smoke inhalation, bleeding, not breathing / isn't
   breathing, unconscious, choking, hypothermia, shock(ed). When the question has one, skip the how-to phrase expansions
   and raise emergency and first-aid documents.
3. **Document tiers, only for an emergency question:** emergency/first aid > general medical > general advice >
   clinical (as today). `find` already multiplies scores by `GENERAL` (×1.25) and `CLINICAL` (×0.6), and `hybrid` by
   `CLINICAL` (×0.55). This makes those multipliers depend on the question. Without an emergency word, nothing changes:
   "how do i start a fire" should still find the survival manuals, not first-aid books. This is also what should help the
   second table.

**How to check it**

The 32 questions above, plus #128's 20, scored on `main` and on the change with the same measure. A change is accepted
only if no question gets worse. I have the script and will attach it (or put it in a PR) if this direction fits.

**Relation to #128**

#128 adds the vocabulary for making fire and making water safe, and the how-to numbers above show it works. This issue is
about how any phrase is applied, so it would change #128's phrases from filters to bonuses rather than replace them.
#128's numbers would need scoring again after that.

**How I ran it**

```bash
LASTBOOK_DATA=/path/to/LastbookData python server.py --port 8897 --no-index   # on 256d52f
LASTBOOK_DATA=/path/to/LastbookData python server.py --port 8895 --no-index   # on #128
```

Then `/api/retrieve?q=<question>&k=8` on each. Windows 10, Medium pack, no AI and no meaning-based index (the desktop
app's default).
