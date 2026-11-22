"""Writes runs/appendix.md (the full lists for RESULTS.md) from results.json.  python -B -X utf8 indep_report.py"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
d = json.load(open(HERE / 'results.json', encoding='utf-8'))
L = []
def row(r, extra=''):
    s = f"- \"{r['text']}\""
    if r['corrected'] != r['text']:
        s += f" (searched \"{r['corrected']}\")"
    s += f" — p {r['p']}, {r['action']}, urgent {'yes' if r['urgent'] else 'NO'}"
    if r['body']:
        s += f", body {'/'.join(r['body'])}"
    if r['n_hits'] == 0:
        s += ', no pages found'
    if r['route'] != 'first':
        s += f", route {r['route']}"
    return s + extra
names = {'kw': 'keyword-only', 'hy': 'hybrid'}
L.append('## Appendix A: critical failures, in full\n')
for m in ('kw', 'hy'):
    c = d['critical'][m]
    L.append(f"### {names[m]}: red lines that get the bare \"help me help you\" (ask, no answer, pages only as consulted) — {len(c['red_bare_ask'])}\n")
    L += [row(r) for r in c['red_bare_ask']] or ['- none']
    L.append('')
    L.append(f"### {names[m]}: red lines whose pages are withheld — {len(c['red_pages_withheld'])} (the same lines: every withheld red line is a bare ask)\n")
    L.append(f"### {names[m]}: red lines given pages without an answer (ask+pages, UNSURE_DANGER) — {len(c['red_ask_with_pages_no_answer'])}\n")
    L += [row(r) for r in c['red_ask_with_pages_no_answer']] or ['- none']
    L.append('')
    s = c['red_sure_non_emergency_first']
    off = [r for r in s if not r['first_health_looking']]
    L.append(f"### {names[m]}: red lines judged \"sure\" (answered, no buttons) whose first page is not from an emergency/first-aid book — {len(s)} of {c['red_sure_total']} sure red lines; {len(off)} of them with a title that doesn't even look like health (marked **off**)\n")
    for r in s:
        L.append(row(r, f" — first: {r['first']}" + ('' if r['first_health_looking'] else ' **off**')))
    L.append('')
L.append('## Appendix B: typo, glued and real-word-typo lines (keyword run; correction is the same in both modes)\n')
L.append('| status | typed | searched | meaning | urgent | body |')
L.append('|---|---|---|---|---|---|')
order = {'wrong word': 0, 'left as typed': 1, 'partly fixed': 2, 'fixed': 3, 'nothing to fix': 4}
for x in sorted(d['typos']['rows'], key=lambda x: order[x['status']]):
    L.append(f"| {x['status']} | {x['text']} | {x['corrected'] if x['corrected'] != x['text'] else '='} | {x['meaning']} | "
             f"{'yes' if x['urgent'] else 'NO'} | {'/'.join(x['body']) or '-'} |")
L.append('')
L.append('## Appendix C: miss themes, every line\n')
titles = {'combined_red_yellow': 'Red/yellow lines with any detection miss (not urgent, a covered body sign missed, or red pages withheld in either mode)',
          'not_urgent_red': 'Red lines not urgent (is_danger false)', 'not_urgent_yellow': 'Yellow lines not urgent',
          'body_missed_inscope_red_yellow': 'Red/yellow lines with a sign body_signs covers, not found'}
for k in ('combined_red_yellow', 'not_urgent_red', 'not_urgent_yellow', 'body_missed_inscope_red_yellow'):
    v = d['miss_themes'][k]
    L.append(f"### {titles[k]} — {sum(len(x) for x in v.values())}\n")
    for th, xs in v.items():
        L.append(f"- **{th}** ({len(xs)}): " + ' / '.join(f'"{x}"' for x in xs))
    L.append('')
L.append('## Appendix D: body_signs on green lines (false positives), in full\n')
for x in d['body_fp_green']:
    L.append(f"- \"{x['text']}\" — {'/'.join(x['body'])} ({', '.join(x['kind'])})")
(HERE / 'runs' / 'appendix.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
print(len(L))

# ---- breakdown table by kind tag and by source -> runs/tables.md
T = ['| group | n (r/y/g) | urgent: red | yellow | green (FP) | body: covered signs found | red bare ask kw / hy | '
     'red ask+pages kw / hy | red first page from emergency book kw / hy |', '|---|---|---|---|---|---|---|---|---|']
def frac(a, b):
    return f'{a}/{b}' if b else '–'
groups = list(d['by_kind'].items()) + [(f'source: {k}', v) for k, v in d['by_source'].items()]
for name, g in groups:
    k, h = g['kw'], g['hy']
    T.append(f"| {name} | {k['n']} ({k['red']}/{k['yellow']}/{k['green']}) | {frac(k['urgent_red'], k['red'])} | "
             f"{frac(k['urgent_yellow'], k['yellow'])} | {frac(k['urgent_green'], k['green'])} | "
             f"{frac(k['body_inscope_hit'], k['body_inscope'])} | {k['red_bare_ask']} / {h['red_bare_ask']} | "
             f"{k['red_ask_pages']} / {h['red_ask_pages']} | {frac(k['red_first_emergency'], k['red'])} / "
             f"{frac(h['red_first_emergency'], h['red'])} |")
(HERE / 'runs' / 'tables.md').write_text('\n'.join(T) + '\n', encoding='utf-8')
