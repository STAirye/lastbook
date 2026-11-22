r"""Blind list 4: the four runs (as typed / with the chat's English search words) x (keyword-only / hybrid), read after
they are all done. Measurement only: nothing here feeds back into the code.

    python -B .claude\drafts\independent4\analyze4.py   -> results.json, runs/report.txt (every missed red line in full)

"urgent" = assistant.is_danger (words OR meaning); "words" = what the words alone said; groups by language: the
messages' own lang field when the generator gave one, else recover.py's guess ("en", "es-*", other).
"""
import collections, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = {}
for en in ('typed', 'english'):
    for m in ('kw', 'hy'):
        p = HERE / 'runs' / f'{en}_{m}.json'
        if p.is_file():
            RUNS[(en, m)] = json.load(open(p, encoding='utf-8'))


def group(r):
    lang = (r.get('lang') or '?').lower()
    return 'English' if lang.startswith('en') else ('Spanish' if lang.startswith('es') else 'other')


def pct(a, b):
    return f'{a}/{b} ({round(100 * a / b)}%)' if b else '-'


def table(rows):
    out = {}
    for g in ('English', 'Spanish', 'other', 'all'):
        R = rows if g == 'all' else [r for r in rows if group(r) == g]
        if not R:
            continue
        red = [r for r in R if r['triage'] == 'red']
        yel = [r for r in R if r['triage'] == 'yellow']
        grn = [r for r in R if r['triage'] == 'green']
        cex = [r for r in grn if 'counterexample' in (r.get('kind') or [])]
        out[g] = {
            'lines (red/yellow/green)': f'{len(R)} ({len(red)}/{len(yel)}/{len(grn)})',
            'red urgent': pct(sum(r['is_danger'] for r in red), len(red)),
            'red urgent, words alone': pct(sum(bool(r['words_danger']) for r in red), len(red)),
            'red added by the meaning check': sum(1 for r in red if r['is_danger'] and not r['words_danger']),
            'yellow urgent': pct(sum(r['is_danger'] for r in yel), len(yel)),
            'green urgent (false alarm)': pct(sum(r['is_danger'] for r in grn), len(grn)),
            'counterexamples urgent': pct(sum(r['is_danger'] for r in cex), len(cex)),
            'red: pages shown': pct(sum(r['pages_shown'] for r in red), len(red)),
            'red: nothing found': pct(sum(r['n_hits'] == 0 for r in red), len(red)),
            'red: first page from an emergency book': pct(sum(bool(r['first_emergency']) for r in red), len(red)),
            'red: an emergency book in the top 3': pct(sum(bool(r['top3_emergency']) for r in red), len(red)),
            'red: what the chat does': dict(collections.Counter(r['action'] for r in red).most_common()),
            'green: what the chat does': dict(collections.Counter(r['action'] for r in grn).most_common()),
            'clean text changed by typo correction (green)': pct(sum(r['changed'] for r in grn), len(grn)),
        }
    return out


results = {f'{en} / {"keyword-only" if m == "kw" else "hybrid"}': dict(table(v['rows']), meta={
    k: v.get(k) for k in ('code', 'data', 'mode', 'semantic', 'english', 'seconds')} | {'meaning': (v.get('meaning_check') or {}).get('status')})
    for (en, m), v in RUNS.items()}
json.dump(results, open(HERE / 'results.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

lines = []
for (en, m), v in RUNS.items():
    lines.append(f'===== {en} / {m}: red lines not urgent, then green counterexamples flagged =====')
    for r in v['rows']:
        if r['triage'] == 'red' and not r['is_danger']:
            lines.append(f"MISS  [{group(r)}] {r['text']}  | english: {r.get('english')}  | meaning {r.get('meaning_score')}")
    for r in v['rows']:
        if r['triage'] == 'green' and r['is_danger'] and 'counterexample' in (r.get('kind') or []):
            lines.append(f"FALSE [{group(r)}] {r['text']}  | words: {r.get('urgent_words')}  | meaning fired {r.get('meaning_fired')}")
(HERE / 'runs').mkdir(exist_ok=True)
(HERE / 'runs' / 'report.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
for k, v in results.items():
    print('==', k)
    for g, t in v.items():
        if g != 'meta':
            print(' ', g, json.dumps(t, ensure_ascii=False))
