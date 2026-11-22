"""Which hit was useful, for a few triage questions. argv: score.py, code, sections folder or -, question ids..."""
import runpy, sys
mod = runpy.run_path(sys.argv[1], run_name='score_mod')
code, folder, ids = sys.argv[2], sys.argv[3], sys.argv[4:]
server, assistant, _ = mod['start'](code, 'keyword', None if folder == '-' else folder)
search = mod['searcher'](server, assistant, 'hybrid')
cases = {c['id']: c for c in mod['topic_cases'](mod['load_json']('triage.json'))}
RX = mod['RX']
for i in ids:
    c = cases[i]
    print(i, c['q'], 'need', c['need'])
    for h in search(c['q']):
        t = mod['text'](h)
        hit = [n for n in c['need'] if RX[n].search(t)]
        if hit:
            m = RX[hit[0]].search(t)
            print('   USEFUL', h['title'][:60], h.get('page'), hit, repr(t[max(0, m.start() - 60):m.end() + 40]))
