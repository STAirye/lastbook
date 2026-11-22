# Whole-book pages: length penalty vs section split (2026-11-18)

Base: upstream `main` 256d52f. 362 questions from `cases.py`. kw = keyword-only, hy = hybrid.

- **penalty** (worktree `ab-penalty`, ranking only): HTML pages over 20,000 characters go after every normal page in
  the keyword list. Meaning-based search is unchanged.
- **split** (worktree `ab-split` + data folder `D:\LastbookData-split`): the 353 HTML pages over 20,000 characters
  became 7,634 sections of about 5,000 characters, cut after a sentence. 29,389 of their 29,394 meaning-based passages
  keep their vectors and are labelled with their section; 5 didn't match. Hybrid keeps the section number for HTML, so
  each section ranks on its own. Cut by length, not by headings, because the stored text has no headings.

Summary:
- **Split wins.** *Modern Machine-Shop Practice* appears in 26 hybrid questions on base, 19 with the penalty, and 1
  with the split. Keyword-only: 25 → 7 → 6.
- **The penalty only fixes the keyword side.** On hybrid the book still comes in through meaning-based search, where
  its 5,082 passages count as one page.
- **Split improves nearly everything a little.** All clean, first result right: hy 72% → 75%, kw 58% → 60%. Red,
  first result right: hy 67% → 70%. Useful pages: hy 5.63 → 5.75, kw 4.56 → 4.83.
- **Red questions with no useful page: hy 5 → 8.** All three new ones had at most 1 coincidental hit before. Nothing
  useful was lost.
- **Not tested:** the Guides and Library search (`server.find`), and opening a result at its section in the reader. A
  real fix also needs the reader to jump to the section, or a click still lands at the top of a 4 MB page.

| | base kw | penalty kw | base hy | penalty hy | split kw | split hy |
|---|---|---|---|---|---|---|
| Red: first result right | 44% | 45% | 67% | 68% | 46% | 70% |
| Red: useful in top 8 | 3.89 | 4.08 | 5.13 | 5.13 | 4.22 | 5.24 |
| Red: no useful page | 27 | 27 | 5 | 5 | 25 | 8 |
| Yellow: first right | 70% | 71% | 73% | 73% | 71% | 77% |
| Green: first right | 82% | 82% | 84% | 84% | 84% | 86% |
| Counterexamples: first right | 64% | 64% | 73% | 77% | 64% | 77% |
| All clean: useful in top 8 | 4.56 | 4.69 | 5.63 | 5.64 | 4.83 | 5.75 |
| All clean: first right | 58% | 59% | 72% | 73% | 60% | 75% |
| All clean: every need covered | 78% | 77% | 92% | 92% | 78% | 92% |
| Typos: useful in top 8 | 2.23 | 2.23 | 3.39 | 3.39 | 2.25 | 3.42 |
| Top-8 slots taken by whole-book pages (all 362 questions) | 414 | 272 | 268 | 233 | 221 | 209 |
| Questions with a whole-book page in the top 8 | 168 | 113 | 137 | 119 | 126 | 117 |
| Questions with Modern Machine-Shop Practice | 25 | 7 | 26 | 19 | 6 | 1 |

## penalty kw against base kw

Better: 11 questions. Worse: 0.

Worse:

Better:
- tick on my leg how to remove (useful 3→6, first wrong→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.328*
- he was working in the sun and now he is confused and hot (useful 1→1, first wrong→ok): first now *First Aid p.4*
- our car is stuck in rising flood water (useful 5→8, first ok→ok): first now *Floods, the Awesome Power p.4*
- her whole arm is badly burned (useful 5→8, first ok→ok): first now *Burns and Burn Disabilities p.1*
- my friend was struck by lightning (useful 5→8, first ok→ok): first now *Lightning Safety one-pager p.1*
- burned my hand trying to light a fire (useful 4→6, first wrong→wrong): first now *Trail Maintenance and Construction Notebook p.1*
- a power line fell on our car (useful 3→5, first wrong→wrong): first now *Astronomy 2e p.74*
- a snake bit my leg (useful 6→8, first ok→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.341*
- electric shock from a fallen wire (useful 3→5, first wrong→wrong): first now *University Physics Volume 2 p.459*
- he fell through the ice on the lake (useful 3→5, first wrong→wrong): first now *Owlie Skywarn for Kids Winter Storms p.9*
- pulled him out of the river, not breathing (useful 3→5, first ok→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.216*

## split kw against base kw

Better: 20 questions. Worse: 3.

Worse:
- dust in my eye will not come out (useful 2→0, first wrong→wrong): first now *Practical Blacksmithing - Volume 1 (1889-1891) p.236*
- i need to start a fire but i have no matches and no gas (useful 2→0, first wrong→wrong): first now *How to start a fire p.1*
- how to run a fire drill at home (useful 6→4, first ok→ok): first now *Practice Your Home Fire Escape Plan p.1*

Better:
- tick on my leg how to remove (useful 3→6, first wrong→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.328*
- make my home harder to break into (useful 1→2, first wrong→ok): first now *Easy ways to harden your home against intruders p.1*
- kid swallowed drain cleaner (useful 4→4, first wrong→ok): first now *ART: Medicines for HIV p.9*
- he was working in the sun and now he is confused and hot (useful 1→1, first wrong→ok): first now *First Aid p.4*
- wildfire is coming toward our house (useful 0→6, first wrong→wrong): first now *Types of seizures and how to identify them p.42*
- the ground is shaking right now (useful 0→5, first wrong→wrong): first now *Preparing Garden Beds with Double Digging p.None*
- clear brush around the house for wildfire (useful 4→8, first ok→ok): first now *CERT Basic Training Hazard Annexes (2019) p.36*
- what could make a fire spread faster (useful 1→5, first wrong→wrong): first now *Home Builders Guide to Construction in Wildfire Zones FEMA P-754 p.19*
- how to use a burn barrel for trash (useful 3→6, first ok→ok): first now *Index p.11*
- our car is stuck in rising flood water (useful 5→8, first ok→ok): first now *Floods, the Awesome Power p.4*
- her whole arm is badly burned (useful 5→8, first ok→ok): first now *Burns and Burn Disabilities p.1*
- my friend was struck by lightning (useful 5→8, first ok→ok): first now *Lightning Safety one-pager p.1*
- pulled him out of the river, not breathing (useful 3→6, first ok→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.216*
- kid has a nose bleed (useful 6→8, first ok→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.354*
- burned my hand trying to light a fire (useful 4→6, first wrong→wrong): first now *Trail Maintenance and Construction Notebook p.1*

## penalty hy against base hy

Better: 4 questions. Worse: 1.

Worse:
- his shirt is on fire (useful 4→2, first wrong→wrong): first now *Effects of Nuclear Weapons, by Samuel Glasstone and Philip J. Dolan p.299*

Better:
- how to build a root cellar for cold storage (useful 2→2, first wrong→ok): first now *High Tunnels and Other Season Extension Techniques p.4*
- carbon monoxide poisoning symptoms whole family sick (useful 6→6, first wrong→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.353*
- splinter deep in my finger (useful 2→4, first wrong→wrong): first now *FM 21-76 U.S. Army Survival Manual - Historical p.123*
- deep cut on my hand, does it need stitches (useful 5→7, first ok→ok): first now *First Aid p.16*

## split hy against base hy

Better: 16 questions. Worse: 3.

Worse:
- my phone is dead and no power (useful 6→6, first ok→wrong): first now *Discussion thread for this article p.6*
- his shirt is on fire (useful 4→2, first wrong→wrong): first now *Effects of Nuclear Weapons, by Samuel Glasstone and Philip J. Dolan p.299*
- i need to start a fire but i have no matches and no gas (useful 5→3, first ok→ok): first now *How to start a fire p.1*

Better:
- clear brush around the house for wildfire (useful 4→8, first wrong→ok): first now *Sesame Street Wildfires Activity Book p.5*
- how to use a burn barrel for trash (useful 3→6, first wrong→ok): first now *Solid Waste: Turning a Health Risk into a Resource p.24*
- wildfire is coming toward our house (useful 6→8, first wrong→ok): first now *https://www.ready.gov/sites/default/files/2020-07/how-to-prepare-for-a-wildfire p.2*
- i am drowning my tomato plants with too much water (useful 7→7, first wrong→ok): first now *Small-scale Aquaponic Food Production p.205*
- how can i know if my can food has gone bad (useful 5→5, first wrong→ok): first now *Food Preservation @ Home: Water Bath Canning p.None*
- dust in my eye will not come out (useful 2→2, first wrong→ok): first now *Problems with the Eyes and Seeing p.3*
- knife wound to the chest and he is struggling to breathe (useful 5→5, first wrong→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.267*
- carbon monoxide poisoning symptoms whole family sick (useful 6→6, first wrong→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.353*
- the ground is shaking right now (useful 3→8, first ok→ok): first now *Earthquake Preparedness: What Every Childcare Provider Should Know p.7*
- deep cut on my hand, does it need stitches (useful 5→8, first ok→ok): first now *First Aid p.16*
- grease fire in the pan (useful 4→7, first ok→ok): first now *FM 21-76 U.S. Army Survival Manual - Historical p.18*
- someone is full of blood, it does not stop (useful 5→8, first ok→ok): first now *Abortion p.14*
- heat the house without power (useful 5→7, first ok→ok): first now *#WinterReady p.1*
- wound not healing after two weeks (useful 6→8, first ok→ok): first now *International First Aid Resuscitation and Education Guidelines 2025 p.278*
- pour water on a grease fire (useful 4→6, first ok→ok): first now *A Healthy Home p.18*
