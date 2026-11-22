"""Build a data folder where whole-book HTML pages are split into sections, for the A/B test. Read-only on the source.

    python -I -X utf8 build_split.py SRC_DATA DST_DATA RETRIEVAL_DIR

DST_DATA gets junctions (folders) and hard links (files) to SRC_DATA for everything except:
  library-data/search.sqlite   copied; every HTML page over LONG characters replaced by sections of about SECTION
                               characters, cut after a sentence, numbered 1..n as pages
  derived/index/               copied; the passages of those pages keep their vectors, and their page becomes the section
                               their start falls in (no re-embedding: the passage text is the same)
"""
import json, os, re, shutil, sqlite3, subprocess, sys
from pathlib import Path

LONG, SECTION = 20000, 5000


def mirror(src, dst, skip):
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.iterdir():
        if p.name in skip:
            continue
        t = dst / p.name
        if t.exists():
            continue
        if p.is_dir():
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(t), str(p)], check=True, capture_output=True)
        else:
            os.link(p, t)


def sections(text):
    """Cut normalized text into pieces of about SECTION characters, after a sentence where possible."""
    out, i = [], 0
    while i < len(text):
        j = min(len(text), i + SECTION)
        if j < len(text):
            k = text.rfind('. ', i + SECTION // 2, j)
            j = k + 1 if k > 0 else (text.rfind(' ', i + SECTION // 2, j) if text.rfind(' ', i + SECTION // 2, j) > 0 else j)
        out.append((i, text[i:j].strip()))
        i = j
    return out


def chunk_starts(text, R):
    """Start offset of each passage retrieval.chunks_of keeps, in order (same loop, with offsets)."""
    out, i = [], 0
    while i < len(text):
        j = min(len(text), i + R.CHUNK)
        if j < len(text):
            k = text.rfind('. ', i + R.CHUNK // 2, j)
            j = k + 1 if k > 0 else (text.rfind(' ', i + R.CHUNK // 2, j) if text.rfind(' ', i + R.CHUNK // 2, j) > 0 else j)
        c = text[i:j].strip()
        if len(c) >= R.MINLEN and R.readable(c):
            out.append((i, c))
        if j >= len(text):
            break
        i = max(j - R.OVERLAP, i + 1)
    return out


def main():
    src, dst, rdir = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    sys.path.insert(0, rdir)
    os.environ['LASTBOOK_DATA'] = str(src)
    import retrieval as R

    mirror(src, dst, {'library-data', 'derived'})
    mirror(src / 'library-data', dst / 'library-data', {'search.sqlite'})
    mirror(src / 'derived', dst / 'derived', {'index'})
    (dst / 'derived' / 'index').mkdir(exist_ok=True)
    for name, s, d in (('search', src / 'library-data' / 'search.sqlite', dst / 'library-data' / 'search.sqlite'),
                       ('semantic', src / 'derived' / 'index' / 'semantic.sqlite', dst / 'derived' / 'index' / 'semantic.sqlite'),
                       ('vectors', src / 'derived' / 'index' / 'vectors.f16', dst / 'derived' / 'index' / 'vectors.f16')):
        if not d.exists():
            print('copy', name, flush=True)
            shutil.copyfile(s, d)

    kind = {r['id']: r['kind'] for r in json.load(open(src / 'library-data' / 'catalog.json', encoding='utf-8'))}
    con = sqlite3.connect(dst / 'library-data' / 'search.sqlite')
    sem = sqlite3.connect(dst / 'derived' / 'index' / 'semantic.sqlite')
    rows = [r for r in con.execute('SELECT rowid, doc_id, title, collection, category, path, page, body FROM pages '
                                   'WHERE length(body) > ?', (LONG,)) if kind.get(r[1]) == 'html']
    report = {'pages_split': 0, 'sections': 0, 'passages_relabelled': 0, 'passages_unmatched': 0}
    for rowid, doc, title, coll, cat, path, page, body in rows:
        text = R.norm_ws(body)
        secs = sections(text)
        con.execute('DELETE FROM pages WHERE rowid=?', (rowid,))
        con.executemany('INSERT INTO pages(doc_id,title,collection,category,path,page,body) VALUES (?,?,?,?,?,?,?)',
                        [(doc, title, coll, cat, path, n + 1, t) for n, (_, t) in enumerate(secs)])
        starts = [s for s, _ in secs]
        computed = chunk_starts(text, R)
        stored = sem.execute('SELECT id, text FROM chunk WHERE doc_id=? AND page=? ORDER BY id', (doc, page)).fetchall()
        ci = 0
        for cid, ctext in stored:  # walk both lists in order; the stored text is the computed text
            while ci < len(computed) and computed[ci][1] != ctext:
                ci += 1
            if ci == len(computed):
                report['passages_unmatched'] += 1
                ci = 0
                continue
            off = computed[ci][0]
            sec = max(n for n, s in enumerate(starts) if s <= off) + 1
            sem.execute('UPDATE chunk SET page=? WHERE id=?', (sec, cid))
            report['passages_relabelled'] += 1
            ci += 1
        report['pages_split'] += 1
        report['sections'] += len(secs)
    con.commit(); sem.commit()
    con.execute("INSERT INTO pages(pages) VALUES('optimize')"); con.commit()
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
