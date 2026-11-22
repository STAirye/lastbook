
## Miss themes (what a later fix would target; nothing fixed here)

126 red/yellow lines have at least one miss (not urgent, a covered body sign not found, or red pages withheld in
either mode). Themes are assigned by regex on the text and labelled signs (then the meaning), first match wins, so
counts are approximate; every line is in Appendix C.

| # | theme | lines | what misses | examples |
|---|---|---|---|---|
| 1 | Unconscious euphemisms | 17 | urgent and body | "he turned a funny colour and slumped", "old lady on the floor ... wont answer me", "he's out cold on the pavement", "hard to rouse", "found him face down in the pond", "grandpa ... snoring loud cant wake him" (cant wake ≠ won't wake) |
| 2 | Real-word autocorrect / real-word typos | 13 | urgent, body, correction | "she is breeding a lot from the leg", "he cant breed", "hes not braking", "she is not breaking", "my son is having a sea sure", "he past out", "she keeled over" (-> peeled), "strock", "poisend", "brest/cheat pain", "chest pane" |
| 3 | Misspellings the corrector leaves or bends | 10 | urgent, body | "hemmorage", "unconshus man", "siezing" (-> seizing), "tournaquet", "blu lip baby", "sooo much bloooood", "pnemonia", "cellulitus" |
| 4 | Bleeding without blood/bleed | 10 | body (urgent mostly ok) | "i cut myself deep and it wont stop", "finger cut off", "he got shot in the leg", "bitten on the neck and its pouring", "cut on his shin that wont stop oozing ... warfarin", "heavy period soaking pad every hour", "nosebleed wont stop", "vomit looks like coffee grounds" |
| 5 | Yellow conditions with no urgent word | 10 | urgent | "my 2 yr old put a bead up her nose", "mum dementia hasnt peed all day", "erection lasting 5 hours", "ankle crunched ... cant stand on it", "broke my nose", "cat scratch ... swollen and red" |
| 6 | Chest pain / heart wordings | 9 | body | "feels like an elephant sitting on my chest", "tight chest jaw ache feel sick 58 m", "heart racing like crazy", "her heart is beating really slow like 30", "i cant feel his heart beating", "my mother she have pain in heart" |
| 7 | Stroke words | 9 | urgent | "mum suddenly cant lift her right arm and talking funny", "his smile is crooked", "cant feel the left side of my body", "cant really say words right ... dribbling out the side of his mouth", "sudden blind in one eye like a curtain", "had a funny turn", "come over all peculiar". (URGENT has droop/slurr/stroke/face, so the textbook words work; the lay words don't) |
| 8 | Overdose / poisoning without the word | 8 | urgent | "took a whole box of paracetamol but he says he feels fine", "took 20 of her sleeping tablets to rest", "let him sleep it off hes really drunk", "the child is drinking the cleaning water", "over dose on xanax", "took 2 extra panadol" (pills? is in URGENT; tablets isn't) |
| 9 | Seizure slang | 7 | body | "shes fitting and wont stop been 6 minutes" (the fit phrase wants "having/had a fit"), "shaking all over on the floor and foam from mouth", "HES SHAKING AND HIS EYES ARE ROLLING", "swallow his tongue" |
| 10 | Bare word / greeting / number | 5 | urgent, noise | "911" (noise route, asked), "hlep", "helo my son", head injury with repeated questions |
| 11 | CPR named, no body word | 3 | body only (urgent ok) | "how do i do cpr on a man", "how many pushes for cpr baby" |
| 12 | Suicide euphemisms | 3 | urgent | "killing myself tonight" (URGENT has kill (him\|her\|my...)sel\w*, not "killing myself"), "my friend texted goodbye and wont answer", "i want to disappear forever" |
| 13 | Agonal / noisy breathing | 2 (+2 under #1) | urgent, body | "she's gurgling", "stridor croup barky cough 3am", snoring lines |
| 14 | Non-English | 2 | urgent, body | "mi esposa no respira help" (urgent only via help), "ma tête tourne et je vois flou soudain" |
| – | Others, 1–2 each | 18 | urgent | blue alone ("hes blue"), can't feel legs / tight cast, cold exposure ("brandy hes frozen"), pregnancy ("leaking fluid 30 weeks"), misconceptions ("suck the venom out", "finger sweep"), eye ("hit by a firework cant see"), "worst headache ... thunderclap", "under the bath water", "red jelly poo", "asthma attack inhaler not working", "throat closing up ate shrimp", "colour is like ash" |

Cross-cutting: **allergy words** ("throat closing up", "tongue feels huge and itchy", "used the epi pen") are urgent
through other words ("ate", "medicine", "hospital") and so only reach ask+pages keyword-only; none is a body sign.
**Elderly** lines are the weakest tag (body 3/13 covered, 3 bare asks keyword-only), **rambling** next (urgent 5/9
red, 3 bare asks): the long-message p is low and the signs are in lay words.

**False positives** (for completeness; they cost only that pages are shown and the buttons are full-size): urgent on
green is driven by burn (9), bleeding (9), blood (7), cut (6), baby (6), head, bleed, heart, dead, blue, stroke (5
each). body_signs fires on 54 green lines, 44 of them counterexamples ("how to bleed brakes on bike", "breathing exercises
for yoga", "blood orange cake", "choking hazard toys age 3", "pulse lentils recipe"...; Appendix D).
