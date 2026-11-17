"""Fork: ask the local AI questions whose answer is one row of a dose or quantity table, against a test server, and check
the amount it gives. See docs/FORK.md, 3j.

    LASTBOOK_DATA=D:\\LastbookData LASTBOOK_LOCAL_AI=1 python server.py --port 8899      (LASTBOOK_AI_TABLES=0 for the old reading)
    python tools/fork_table_test.py LABEL [RUNS]

Writes LABEL.json (every answer) in the current folder and prints one line per answer and a summary. An answer is
"right" when it gives the table's amount for that row and no other row's amount as the dose, "wrong" when it gives
another row's amount, and "none" when it gives neither (a refusal, or an amount from elsewhere). Read the answers too:
the check looks for the amounts, not for whether the sentence around them is right."""
import json, re, sys, time, urllib.request

# (question, right, wrong): patterns are matched against the answer in lower case
EPI = r'3[.,]5\s*m[lg]'   # 3.5 mL of 1 mg/mL is 3.5 mg
EPI_WRONG = r'(?<![\d.,])(2[.,]5|3|4|4[.,]5)\s*m[lg]\b'   # the 5, 6, 8 and 9 kg rows
HALF = r'(1/2|½|half( a)?|media|0[.,]5)\s*(tea)?(spoon|cucharadita)'
QS = [
    ('how much bleach do i add to 1 liter of water to make it safe to drink?', r'\b2\s*(drops|gotas)', r'\b8\s*(drops|gotas)|' + HALF),
    ('how much bleach for 4 liters of water?', r'\b8\s*(drops|gotas)', r'\b2\s*(drops|gotas)|' + HALF),
    ('how much bleach for 20 liters of water?', HALF, r'\b5\s*(tea)?spoons|\b5\s*cucharaditas|\b8\s*(drops|gotas)'),
    ('how much bleach for a 200 liter barrel of water?', r'\b5\s*(teaspoons|cucharaditas)', HALF + r'|\b8\s*(drops|gotas)'),
    ('¿cuánto cloro le echo a 1 litro de agua?', r'\b2\s*(drops|gotas)', r'\b8\s*(drops|gotas)|' + HALF),
    ('¿cuánto cloro para 4 litros de agua?', r'\b8\s*(drops|gotas)', r'\b2\s*(drops|gotas)|' + HALF),
    ('¿cuánto cloro le echo a 20 litros de agua?', HALF, r'\b5\s*(tea)?spoons|\b5\s*cucharaditas|\b8\s*(drops|gotas)'),
    ('¿cuánto cloro le echo a un tambor de 200 litros de agua?', r'\b5\s*(teaspoons|cucharaditas)', HALF + r'|\b8\s*(drops|gotas)'),
    # Good Food Makes Good Health p. 39 / Caring for Children p. 54: 2 to 12 years, 300 mg (1 tablet of 300 mg)
    ('how much ferrous sulfate should i give my 5 year old with anemia?', r'\b300\s*mg|\b1 tablet|\bone tablet|\bun comprimido|\buna tableta',
     r'\b125\s*mg|\b600\s*mg|\b2 tablets|\btwo tablets'),
    ('¿cuánto sulfato ferroso le doy a mi hijo de 5 años con anemia?', r'\b300\s*mg|\b1 tablet|\bun comprimido|\buna tableta|\bun tableta',
     r'\b125\s*mg|\b600\s*mg|\b2 tablet|\bdos (comprimidos|tabletas)'),
    # Children Who Stay Small or Have Weak Bones p. 1: 1 to 12 months, 1000-2000 IU (a table the old reading got right)
    ('what dose of vitamin d for a 6 month old baby with rickets?', r'1[,.]?000\s*(-|–|to|a)\s*2[,.]?000', r'\b6[,.]?000|2[,.]?000\s*(-|–|to|a)\s*6[,.]?000'),
    ('¿qué dosis de vitamina d le doy a un bebé de 6 meses con raquitismo?', r'1[,.]?000\s*(-|–|to|a)\s*2[,.]?000', r'\b6[,.]?000|2[,.]?000\s*(-|–|to|a)\s*6[,.]?000'),
    # MSF Measles p. 206: 7 kg child, 3.5 mL epinephrine (1 mg/ml) + 1 mL 0.9% NaCl
    ('how much nebulized epinephrine for a 7 kg child with croup?', EPI, EPI_WRONG),
    ('¿cuánta epinefrina nebulizada para un niño de 7 kg con crup?', EPI, EPI_WRONG),
]


def ask(port, question):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api/chat', json.dumps({'messages': [{'role': 'user', 'content': question}]}).encode(),
                                 {'Content-Type': 'application/json'})
    done = None
    with urllib.request.urlopen(req, timeout=600) as r:
        for raw in r:
            line = raw.decode('utf-8').strip()
            if line.startswith('data:'):
                try:
                    ev = json.loads(line[5:])
                except ValueError:
                    continue
                if ev.get('type') == 'done':
                    done = ev
    return done or {'answer': '', 'sources': []}


def verdict(answer, right, wrong):
    a = answer.lower().replace('\u00a0', ' ')
    r, w = re.search(right, a), re.search(wrong, a)
    return 'right' if r and not w else 'wrong' if w and not r else 'both' if r and w else 'none'


def main():
    label = sys.argv[1]
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    port = 8899
    out, tally = [], {}
    ask(port, 'hello')   # the model loads on the first question; an answer during loading comes back empty
    for run in range(runs):
        for q, right, wrong in QS:
            t0 = time.time()
            d = ask(port, q)
            v = verdict(d.get('answer') or '', right, wrong)
            cites = sorted({f"{s['title'][:30]} p{s.get('page')}" for s in d.get('sources') or [] if f"[{s['key']}]" in (d.get('answer') or '')})
            out.append({'run': run, 'q': q, 'verdict': v, 'answer': d.get('answer'), 'cited': cites, 's': round(time.time() - t0, 1)})
            tally.setdefault(q, []).append(v)
            print(f"{run} {v:5} {time.time() - t0:5.1f}s {q[:60]}", flush=True)
            json.dump(out, open(f'{label}.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nsummary', label)
    total = {}
    for q, vs in tally.items():
        print(f"  {vs.count('right')}/{len(vs)} right, {vs.count('wrong')} wrong, {vs.count('both')} both  {q[:70]}")
        for v in vs:
            total[v] = total.get(v, 0) + 1
    print(' ', total)


if __name__ == '__main__':
    main()
