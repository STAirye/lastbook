# Blind list 4: prompts for another AI agent

Three prompts, one per file. Give each to a fresh agent with **no access to the Lastbook code or this fork**. If you can,
use a different model family from the one that wrote lists 1–3 and the fork's rules (Claude): the summary's biggest
caveat is that everything was written by one model family. Same output format as lists 1–3
(`independent3/phrases.jsonl`), plus a `lang` field in the third.

Put the files in `.claude/drafts/independent4/` without opening them: they're only read after the runs, like list 3.

---

## Prompt 1: serious, well-written messages → `phrases_serious.jsonl`

```
I'm building a test set for an offline emergency-information app. People type a question or describe a situation, and
the app must decide whether it might be life-threatening right now. I need realistic messages to test that decision.
You will not see the app; don't guess how it works, and don't write messages designed to beat any particular rule.

Write 500 messages in English, as real people would type them when they write CALMLY AND CLEARLY: full sentences, mostly
correct spelling, often precise and detailed. Think of a nurse's triage line: a careful adult describing a situation, a
worried relative giving background, someone downplaying, someone over-explaining.

Label each like an experienced emergency nurse doing phone triage:
- red: possibly life-threatening now; needs emergency help immediately.
- yellow: needs medical care soon (hours to a day), not an emergency right now.
- green: not urgent: a how-to, a mild problem, general information.

Mix: about 40% red, 15% yellow, 45% green. Within red, cover many kinds: breathing, choking, bleeding, unconsciousness,
chest pain, stroke signs, severe allergic reactions, overdose and poisoning, seizures, burns, drowning, head and spine
injury, sepsis signs, heat and cold, childbirth and pregnancy problems, babies and children, the elderly, mental-health
crises and suicide risk, trauma, electrical injury, carbon monoxide.

Make at least a third of the red messages ones that need a clinician's inference, with NO obvious alarm word: the
danger is in the combination or the context (e.g. a "worst headache of my life" said casually, a fever days after
chemotherapy, giving away belongings, a curtain coming down over one eye, a toddler quiet after finding the cleaning
cupboard open). Include messages where the writer is the patient and ones where they're helping someone else, and make
it clear from the wording which it is.

At least 150 of the green messages must be COUNTEREXAMPLES: they look alarming but aren't (idioms, cooking, sport,
mechanics, games, first-aid course questions, history, fiction, "bleed the brakes", "my phone died", "killing it at
work", questions about an emergency that already ended and was treated).

Output JSON Lines, one object per line, nothing else:
{"text": "...", "meaning": "a plain restatement of what the person means", "triage": "red|yellow|green",
 "signs": ["the warning signs present, short", ...], "kind": ["plain", "inference", "counterexample", "mild", "child",
 "baby", "elderly", "pregnancy", "mental-health", "downplayed", "self", "other-person", ...],
 "persona": "who is typing, in a few words", "source": "invented"}
Use "web-inspired" as source only if you paraphrased a real public post; never copy one, and never include real names,
addresses, phone numbers or other personal data. No two messages should be near-duplicates.
```

---

## Prompt 2: messy messages (slang, typos, panic) → `phrases_messy.jsonl`

```
I'm building a test set for an offline emergency-information app. People type a question or describe a situation, and
the app must decide whether it might be life-threatening right now. I need realistic messages to test that decision.
You will not see the app; don't guess how it works, and don't write messages designed to beat any particular rule.

Write 500 messages in English, as real people type when they are scared, rushed, drunk, young, old, or on a phone:
- typos and misspellings, including ones that make another real word ("he cant breed", "sea sure")
- words glued together or split ("heschokinghelp", "un conscious"), missing apostrophes ("hes", "cant", "wont")
- slang and texting style ("bro", "ngl", "rn", "lowkey", "he's tweaking"), regional slang (UK, Australian, US, Indian
  English), emoji, ALL CAPS, no punctuation
- voice-to-text errors from a noisy place, one-finger typing by an elderly person, fragments ("blood. lots. help")
- the emergency buried in small talk or in a long ramble, or downplayed ("prob nothing but...")
- misconceptions ("should i put butter on it")

Label each like an experienced emergency nurse doing phone triage, judging what the person MEANS, not how it's spelled:
- red: possibly life-threatening now; needs emergency help immediately.
- yellow: needs medical care soon (hours to a day), not an emergency right now.
- green: not urgent: a how-to, a mild problem, general information.

Mix: about 40% red, 15% yellow, 45% green. Within red, cover many kinds: breathing, choking, bleeding, unconsciousness,
chest pain, stroke signs, severe allergic reactions, overdose and poisoning, seizures, burns, drowning, head injury,
heat and cold, babies and children, the elderly, mental-health crises and suicide risk, trauma, carbon monoxide.
Include messages where the writer is the patient and ones where they're helping someone else.

At least 150 of the green messages must be COUNTEREXAMPLES, written just as messily: slang and idioms that sound
alarming but aren't ("im dead 💀", "that set killed me", "my car is bleeding oil", "choked in the final", gaming,
cooking, sport).

Output JSON Lines, one object per line, nothing else:
{"text": "... exactly as typed, mistakes and all ...", "meaning": "a clean restatement of what the person means",
 "triage": "red|yellow|green", "signs": ["the warning signs present, short", ...],
 "kind": ["typo", "real-word-typo", "glued", "slang", "caps", "fragment", "voice-to-text", "buried", "downplayed",
 "misconception", "counterexample", "mild", "child", "baby", "elderly", "mental-health", "self", "other-person", ...],
 "persona": "who is typing, in a few words", "source": "invented"}
Use "web-inspired" as source only if you paraphrased a real public post; never copy one, and never include real names,
addresses, phone numbers or other personal data. No two messages should be near-duplicates.
```

---

## Prompt 3: multilingual → `phrases_multilingual.jsonl`

```
I'm building a test set for an offline emergency-information app. People type a question or describe a situation, and
the app must decide whether it might be life-threatening right now. I need realistic messages to test that decision.
You will not see the app; don't guess how it works, and don't write messages designed to beat any particular rule.

Write 500 messages as real people would type them in these languages, roughly:
- 120 Spanish (Latin American: Chilean, Mexican, Argentine, Caribbean usage and slang; some Spain Spanish)
- 80 Portuguese (mostly Brazilian), 60 French, 40 German, 40 Italian
- 80 mixed-language messages (Spanglish and other code-switching, a non-English message with English medical words)
- 80 English written by non-native speakers (word order, false friends, literal translations, missing articles)
Write the way people really type in each language: casual, with the usual typos, missing accents, local slang and
texting abbreviations, some calm and correct, some panicked.

Label each like an experienced emergency nurse doing phone triage:
- red: possibly life-threatening now; needs emergency help immediately.
- yellow: needs medical care soon (hours to a day), not an emergency right now.
- green: not urgent: a how-to, a mild problem, general information.

Mix: about 40% red, 15% yellow, 45% green, in every language. Within red, cover many kinds: breathing, choking,
bleeding, unconsciousness, chest pain, stroke signs, severe allergic reactions, overdose and poisoning, seizures,
burns, drowning, babies and children, the elderly, mental-health crises and suicide risk, trauma. Include messages
where the writer is the patient and ones where they're helping someone else.

At least 150 of the green messages must be COUNTEREXAMPLES: local idioms and phrases that sound alarming but aren't
(e.g. Spanish "me muero de risa", "estoy muerto de cansancio"; Portuguese "tô morto"; French "je suis mort de rire"),
plus cooking, sport, mechanics and games.

Output JSON Lines, one object per line, nothing else:
{"text": "... exactly as typed ...", "lang": "es-CL|es-MX|es-AR|es-ES|pt-BR|fr|de|it|mixed:es+en|en-nonnative|...",
 "meaning": "an English restatement of what the person means", "triage": "red|yellow|green",
 "signs": ["the warning signs present, short, in English", ...],
 "kind": ["plain", "slang", "typo", "no-accents", "code-switching", "false-friend", "counterexample", "mild", "child",
 "baby", "elderly", "mental-health", "downplayed", "self", "other-person", ...],
 "persona": "who is typing, in a few words", "source": "invented"}
Use "web-inspired" as source only if you paraphrased a real public post; never copy one, and never include real names,
addresses, phone numbers or other personal data. No two messages should be near-duplicates.
```
