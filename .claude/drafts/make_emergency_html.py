"""Builds one self-contained HTML page (no network, no scripts) from content/emergency/*.json, for human review.
Also shows an empty entry form with every field, as a template for a future submit form."""
import json, html, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[2]
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / '.claude' / 'drafts' / 'emergency-review.html'
e = html.escape
UNKNOWN = '<span class="unk">unknown</span>'

def link(u):
    return f'<a href="{e(u)}">{e(u)}</a>' if u else UNKNOWN

def row(label, value, cls=''):
    return f'<tr class="{cls}"><th>{label}</th><td>{value}</td></tr>'

def chips(items):
    return ' '.join(f'<span class="chip">{e(x)}</span>' for x in items) if items else UNKNOWN

def card(i, s):
    free = {True: 'yes', False: 'no', None: None}[s.get('free')]
    r = [
        row('kind', e(s['kind'])), row('number', f'<b class="num">{e(s["number"])}</b>'),
        row('how', chips(s['how'])),
        row('works_from', chips(s['works_from'])),
        row('works_from_source', link(s.get('works_from_source')), 'src'),
        row('free', e(free) if free else UNKNOWN),
        row('free_source', link(s.get('free_source')), 'src'),
        row('keywords (local)', chips(s['keywords']['local'])),
        row('keywords (en)', chips(s['keywords']['en'])),
        row('when', e(s['when']) or UNKNOWN),
        row('source', link(s.get('source')), 'src'),
        row('url', link(s.get('url')) if s.get('url') else '<span class="unk">not set (optional)</span>'),
        row('checked_on', e(s['checked_on'])),
        row('verified', f'<span class="v {e(s["verified"])}">{e(s["verified"])}</span>'),
    ]
    return f'<section class="card"><h3><span class="idx">{i}</span> {e(s["name"])}</h3><table>{"".join(r)}</table></section>'

def form():
    f = lambda name, hint, tag='input': f'<label>{name}<small>{hint}</small><{tag} disabled></{tag}></label>' if tag == 'textarea' else f'<label>{name}<small>{hint}</small><input disabled></label>'
    def sel(name, hint, opts, multi=False):
        boxes = ' '.join(f'<label class="inl"><input type="{"checkbox" if multi else "radio"}" disabled> {o}</label>' for o in opts)
        return f'<div class="fld"><b>{name}</b><small>{hint}</small>{boxes}</div>'
    return ('<form onsubmit="return false">' + ''.join([
        f('country', 'English name'), f('code', 'ISO 3166-1 alpha-2, capitals'), f('calling_code', '+ and digits'),
        '<hr>',
        sel('kind', 'one', ['general', 'ambulance', 'fire', 'police', 'poison', 'crisis', 'other']),
        f('name', 'what it is called locally'), f('number', 'digits and spaces; leading + or * allowed'),
        sel('how', 'one or more', ['call', 'sms', 'chat', 'app'], True),
        sel('works_from', 'only what a source says; none = unknown', ['mobile', 'landline', 'voip'], True),
        f('works_from_source', 'required if works_from is not empty; otherwise leave empty'),
        sel('free', 'only if a source says', ['yes', 'no', 'unknown']),
        f('free_source', 'required if free is yes/no; otherwise leave empty'),
        f('keywords (local)', 'lower case, comma separated'), f('keywords (en)', 'lower case, comma separated'),
        f('when', 'only what the cited pages say', 'textarea'),
        f('source', 'page the number and name were read from'),
        f('url', 'optional: the service\'s own page'),
        f('checked_on', 'YYYY-MM-DD, the day you read it'),
        sel('verified', 'official = seen on an official page', ['official', 'found_online']),
    ]) + '</form>')

parts = []
for p in sorted((root / 'content' / 'emergency').glob('*.json')):
    d = json.loads(p.read_text(encoding='utf-8'))
    parts.append(f'<h2>{e(d["country"])} <small>{e(d["code"])} · {e(d["calling_code"])} · general: {e(str(d["general"])) if d["general"] else "none recorded"}</small></h2>')
    parts += [card(i, s) for i, s in enumerate(d['services'])]

page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Emergency numbers, review</title>
<style>
body{{font:15px/1.45 system-ui,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;color:#1b1b1b}}
h2 small{{font-weight:400;color:#555;font-size:.65em}} .card{{border:1px solid #ccc;border-radius:8px;margin:1rem 0;padding:.5rem 1rem}}
.idx{{color:#888}} table{{border-collapse:collapse;width:100%}} th{{text-align:left;width:11rem;color:#555;font-weight:500;vertical-align:top;padding:.2rem .5rem .2rem 0}}
td{{padding:.2rem 0;word-break:break-word}} .num{{font-size:1.3em}} .chip{{background:#eef;border-radius:4px;padding:0 .4rem;margin-right:.2rem}}
.unk{{color:#a60;font-style:italic}} tr.src a{{font-size:.85em}} .v{{padding:0 .4rem;border-radius:4px}} .official{{background:#dfd}} .found_online{{background:#fed}}
form{{border:2px dashed #999;border-radius:8px;padding:1rem}} label{{display:block;margin:.6rem 0}} label small,.fld small{{display:block;color:#666}}
input:not([type]),textarea{{width:100%;box-sizing:border-box}} .inl{{display:inline-block;margin-right:1rem}} .fld{{margin:.6rem 0}}
</style>
<h1>Emergency numbers: review sheet</h1>
<p>Generated from <code>content/emergency/*.json</code> on the current branch. Orange italic <span class="unk">unknown</span> = the field is empty or null by design. Links are for you to open; this page loads nothing itself.</p>
{''.join(parts)}
<h2>Empty entry (template for a submit form)</h2>
<p>Every field, in the same order as above, with the rule for each. Country fields first, then one service.</p>
{form()}
</html>'''
out.write_text(page, encoding='utf-8')
print(out)
