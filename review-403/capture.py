"""Before/after captures for wonderdawg's two #403 cases, through the app's own HTTP API, on a real data folder.

    python -B capture.py <code checkout> <data folder> <label> <port> <out.json>

Scenario 1 (build in progress): the sections file is removed, the server is started, and the first Library search is
sent at once and timed; then searches are repeated until the answer comes from sections.
Scenario 2 (damaged cache): a good sections file is put back with its FTS5 table dropped (long/section metadata
readable), the server is restarted, and the same searches are made.
Each step records /api/find, and for the first long book hit, /api/doc and /api/page of the cited section (or page 1).
The data folder's derived/index is written (sections file only); use a spare one. The server runs with --no-index.
"""
import json, shutil, sqlite3, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

code, data, label, port, out = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], int(sys.argv[4]), Path(sys.argv[5])
IDX = data / 'derived' / 'index'
Q = ['grease fire in a pan', 'kitchen fires', 'lathe chuck']
BASE = f'http://127.0.0.1:{port}'


def get(path, timeout=600):
    t0 = time.time()
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        body = json.loads(r.read().decode('utf-8'))
    return body, round(time.time() - t0, 2)


def start():
    p = subprocess.Popen([sys.executable, '-B', str(code / 'server.py'), '--data', str(data), '--port', str(port), '--no-index'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, cwd=str(code))
    for _ in range(600):
        try:
            get('/api/health', 2)
            return p
        except Exception:
            time.sleep(0.2)
    p.kill()
    raise SystemExit('server did not start: ' + p.stderr.read().decode('utf-8', 'replace')[-2000:])


def step(name):
    rec = {'step': name, 'files': sorted(f.name for f in IDX.glob('sections-*'))}
    for q in Q:
        try:
            body, s = get('/api/find?q=' + urllib.parse.quote(q))
        except Exception as e:
            rec[q] = {'error': f'{type(e).__name__}: {e}'}
            continue
        res = body.get('results') or []
        rec[q] = {'seconds': s, 'n': len(res), 'mode': body.get('mode'),
                  'top': [{'id': r['id'], 'title': r.get('title'), 'kind': r.get('kind'),
                           'hits': [{'page': h['page'], 'snippet': (h.get('snippet') or '')[:160]} for h in r['hits']]}
                          for r in res[:8]]}
        long_hit = next((r for r in res if r.get('kind') == 'html' and any(h['page'] for h in r['hits'])), None) or \
            next((r for r in res if r.get('kind') == 'html'), None)
        if long_hit:
            page = next((h['page'] for h in long_hit['hits'] if h['page']), 1)
            d, _ = get('/api/doc/' + urllib.parse.quote(long_hit['id']))
            pg, ps = get(f"/api/page/{urllib.parse.quote(long_hit['id'])}/{page}")
            rec[q]['opened'] = {'id': long_hit['id'], 'doc_sections': d.get('sections'), 'page': pg.get('page'),
                                'pages': pg.get('pages'), 'chars': len(pg.get('text') or ''),
                                'text_head': (pg.get('text') or '')[:300], 'seconds': ps}
    return rec


def run(log, name, repeat_until_sections=False):
    t0 = time.time()
    while True:
        r = step(name)
        r['t'] = round(time.time() - t0, 1)
        log.append(r)
        if not repeat_until_sections or any(h['page'] for x in Q if 'top' in r[x] for t in r[x]['top'] if t['kind'] == 'html' for h in t['hits']) or r['t'] > 60:
            return
        time.sleep(2)


log = []
good = sorted(IDX.glob('sections-*.sqlite'))
keep = out.parent / 'good-sections.sqlite'   # a copy of the good file, kept from the first run
if good and not keep.exists():
    shutil.copy2(good[0], keep)
for f in IDX.glob('sections-*'):
    f.unlink()
p = start()
try:
    run(log, 'build in progress: first search right after start', repeat_until_sections=True)
finally:
    p.kill(); p.wait()

# scenario 2: the good file back, with its search table dropped
name = sorted(IDX.glob('sections-*.sqlite'))
target = name[0] if name else IDX / keep.name
for f in IDX.glob('sections-*'):
    f.unlink()
shutil.copy2(keep, target)
con = sqlite3.connect(target)
con.execute('DROP TABLE pages')
con.commit()
con.close()
con = sqlite3.connect(target)
log.append({'step': 'damaged: long/section tables readable', 'long_rows': con.execute('SELECT count(*) FROM long').fetchone()[0]})
con.close()
p = start()
try:
    run(log, 'damaged cache: search after restart', repeat_until_sections=True)
finally:
    p.kill(); p.wait()
out.write_text(json.dumps({'code': label, 'log': log}, indent=1, ensure_ascii=False), encoding='utf-8')
print('done', label, len(log), 'steps')
