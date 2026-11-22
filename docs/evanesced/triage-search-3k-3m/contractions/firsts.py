"""fork/contractions: first-page quality on the held-out lists, before vs after (rough: health-looking title, emergency book)."""
import json, re, sys
sys.path.insert(0, 'independent2')
HEALTH = re.compile(r'health|heart|seiz|epilep|bleed|newborn|bab(y|ies)|pregnan|birth|breath|belly|diarr|medic|nurs|first aid|'
                    r'injur|burn|poison|wound|fractur|stroke|cpr|doctor|emergenc|resusc|choking|allerg|drown|shock|fever|child|sick|'
                    r'disease|pain|hospital|clinic|patient|trauma|bites|stings', re.I)
load = lambda p: json.load(open(p, encoding='utf-8'))['rows']
for p0, p1 in zip(sys.argv[1::2], sys.argv[2::2]):
    out = []
    for R in (load(p0), load(p1)):
        ry = [r for r in R if r['triage'] in ('red', 'yellow')]
        t = lambda r: (r['top3'][0]['title'] or '') if r['top3'] else ''
        out.append((sum(bool(HEALTH.search(t(r))) for r in ry), sum(bool(r.get('first_emergency')) for r in ry),
                    sum(any(HEALTH.search(h['title'] or '') for h in r['top3']) for r in ry), len(ry)))
    print(p1, 'red+yellow: first title health-looking / first from emergency book / any of top3 health-looking (of n):', out[0], '->', out[1])
