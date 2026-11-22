"""Score /api/retrieve against the labelled questions in cases.py.

    python -I score.py OUT.json NAME=URL [NAME=URL ...]      e.g. keyword=http://127.0.0.1:8896 hybrid=http://127.0.0.1:8897

Per question, on the top 8 (title + excerpt of each hit):
  useful      hits that match any need
  first_ok    the first hit matches the most urgent need (need[0]); for counterexamples, it also must not match not_first
  covered     every need appears somewhere in the top 8
  context     share of hits that match only the setting (context) and no need; over 0.5 breaks the topic cap
Typos are compared with the clean phrasings of the same topic.
"""
import json, re, sys, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cases import P, cases  # noqa: E402

RX = {k: re.compile(v, re.I) for k, v in P.items()}
K = 8


def top(base, q):
    u = base + '/api/retrieve?' + urllib.parse.urlencode({'q': q, 'k': K})
    with urllib.request.urlopen(u, timeout=180) as r:
        j = json.loads(r.read().decode('utf-8'))
    return j['results'], (j.get('semantic') or {}).get('state')


def text(h):
    return h['title'] + ' ' + (h.get('excerpt') or '')


def score(c, hits):
    ts = [text(h) for h in hits]
    m = lambda keys, t: any(RX[k].search(t) for k in keys)
    useful = sum(1 for t in ts if m(c['need'], t))
    first = ts[0] if ts else ''
    # a counterexample fails when the first page is about the emergency word and not the real topic
    # (the brake manual says "bleed" too, and is the right answer)
    wrong_sense = bool(ts) and m(c['not_first'], first) and not m(c['need'], first)
    first_ok = bool(ts) and bool(RX[c['need'][0]].search(first)) and not wrong_sense
    covered = all(any(RX[k].search(t) for t in ts) for k in c['need'])
    ctx = sum(1 for t in ts if c['context'] and m(c['context'], t) and not m(c['need'], t))
    return {'useful': useful, 'first_ok': first_ok, 'covered': covered, 'context_share': round(ctx / K, 3),
            'cap_broken': ctx / K > 0.5, 'wrong_sense_first': wrong_sense,
            'titles': [f"{h['title']} p.{h.get('page')}" for h in hits],
            'excerpts': [(h.get('excerpt') or '')[:160] for h in hits]}


def agg(rows):
    n = len(rows) or 1
    return {'n': len(rows), 'useful_mean': round(sum(r['useful'] for r in rows) / n, 2),
            'first_ok': round(sum(r['first_ok'] for r in rows) / n, 3),
            'covered': round(sum(r['covered'] for r in rows) / n, 3),
            'cap_broken': sum(r['cap_broken'] for r in rows), 'zero_useful': sum(r['useful'] == 0 for r in rows),
            'wrong_sense_first': sum(r['wrong_sense_first'] for r in rows)}


def main():
    out = sys.argv[1]
    servers = dict(a.split('=', 1) for a in sys.argv[2:])
    cs = cases()
    res = {'servers': servers, 'cases': len(cs), 'topics': len({c['topic'] for c in cs}), 'by_server': {}}
    for name, base in servers.items():
        rows, state, t0 = [], None, time.time()
        for c in cs:
            hits, state = top(base, c['q'])
            r = score(c, hits)
            r.update(id=c['id'], q=c['q'], topic=c['topic'], colour=c['colour'], typo=bool(c['typo_of']),
                     counter=bool(c['not_first']))
            rows.append(r)
        clean = [r for r in rows if not r['typo']]
        typo = [r for r in rows if r['typo']]
        by_topic = defaultdict(list)
        for r in clean:
            by_topic[r['topic']].append(r)
        typo_pairs = []
        for r in typo:
            base_rows = by_topic[r['topic']]
            typo_pairs.append({'q': r['q'], 'topic': r['topic'], 'useful': r['useful'], 'first_ok': r['first_ok'],
                               'clean_useful': round(sum(x['useful'] for x in base_rows) / len(base_rows), 2),
                               'clean_first_ok': round(sum(x['first_ok'] for x in base_rows) / len(base_rows), 2)})
        summary = {'semantic': state, 'seconds': round(time.time() - t0, 1), 'all_clean': agg(clean),
                   'counterexamples': agg([r for r in clean if r['counter']]),
                   'typos': agg(typo), 'typos_clean_same_topics': agg([x for t in {r['topic'] for r in typo} for x in by_topic[t]])}
        for col in ('red', 'yellow', 'green'):
            summary[col] = agg([r for r in clean if r['colour'] == col and not r['counter']])
        res['by_server'][name] = {'summary': summary, 'rows': rows, 'typo_pairs': typo_pairs}
        print(name, json.dumps(summary), flush=True)
    json.dump(res, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
