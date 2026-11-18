"""fork: whole books saved as one web page, searched in sections.

About 350 saved web pages in the library are whole books (mostly Project Gutenberg), each stored as ONE page of up to
4.4 million characters in the keyword index (library-data/search.sqlite). A page that long holds nearly every word, so
it matched almost any question: "Modern Machine-Shop Practice" came in the top 8 for 26 of 362 unrelated emergency
questions. Here every HTML page over LONG characters is cut into sections of about SECTION characters (after a
sentence where possible), numbered 1..n, and keyword search reads those sections instead of the whole page.

search.sqlite is listed with its SHA-256 in the pack manifest, so it is never written. The sections live in a file of
their own under derived/index/ (like the meaning-based index), sections-<signature>.sqlite, holding only the sections
of long HTML pages: a `pages` FTS5 table with the same columns and tokenizer as the library's, a `long` table naming the
library rows they replace, and a `section` table (doc_id, section, start offset, rowid of its text). The signature is
the size and modification time of search.sqlite with LONG/SECTION/VERSION; when the library index changes, a new file
is built (a few seconds) on the next search, or at startup (server.init), and older ones are removed.

The text cut is norm_ws(body): whitespace runs squashed to one space, as the meaning-based index reads it, so a passage's
start offset says which section it falls in (retrieval.Index relabels existing passages this way, without re-embedding).
"""
import hashlib, os, re, sqlite3, threading, time
from pathlib import Path

import engine.paths as lastbook_paths
from engine.paths import ro_uri

LONG, SECTION = 20000, 5000
VERSION = 1
IDX = lastbook_paths.DATA / 'derived' / 'index'
_lock = threading.Lock()
_state = {'sig': None, 'path': None, 'skip': (), 'docs': {}, 'built': None, 'main': None, 'error': None}


def norm_ws(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def cut(text, size=SECTION):
    """(start offset, text) of each section of normalized text: about `size` characters, ending after a sentence ('. ')
    in the second half of the piece where there is one, else at a space."""
    out, i = [], 0
    while i < len(text):
        j = min(len(text), i + size)
        if j < len(text):
            k = text.rfind('. ', i + size // 2, j)
            if k > 0:
                j = k + 1
            else:
                sp = text.rfind(' ', i + size // 2, j)
                j = sp if sp > 0 else j
        piece = text[i:j].strip()
        if piece:
            out.append((i, piece))
        i = j
    return out


def section_of(starts, offset):
    """1-based number of the section an offset falls in, given the sections' start offsets in order."""
    lo, hi = 0, len(starts) - 1
    while lo < hi:  # last start <= offset
        mid = (lo + hi + 1) // 2
        if starts[mid] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1


def signature(main_db):
    st = Path(main_db).stat()
    return f'{st.st_size}:{st.st_mtime_ns}:{LONG}:{SECTION}:{VERSION}'


def _file_for(sig, folder):
    return Path(folder) / f"sections-{hashlib.sha256(sig.encode()).hexdigest()[:12]}.sqlite"


def build(main_db, kind_of, out):
    """Write the sections file `out` from the library index main_db. kind_of(doc_id) -> catalog kind. Returns a summary."""
    t0 = time.time()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + f'.{os.getpid()}.{threading.get_ident()}.tmp')
    if tmp.exists():
        tmp.unlink()
    src = sqlite3.connect(ro_uri(main_db), uri=True)
    db = sqlite3.connect(tmp)
    n_pages = n_sections = 0
    try:
        db.executescript('''PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
          CREATE VIRTUAL TABLE pages USING fts5(doc_id UNINDEXED,title,collection,category,path UNINDEXED,page UNINDEXED,body,tokenize="unicode61");
          CREATE TABLE long(rowid_main INTEGER PRIMARY KEY, doc_id TEXT, page INTEGER, nsections INTEGER);
          CREATE TABLE section(doc_id TEXT, sec INTEGER, start INTEGER, fts_rowid INTEGER, PRIMARY KEY(doc_id, sec));
          CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);''')
        rows = [(r, d) for r, d in src.execute('SELECT rowid, doc_id FROM pages WHERE length(body) > ?', (LONG,)) if kind_of(d) == 'html']
        if rows:  # only a web page saved whole, as one page: one with pages of its own keeps their numbers
            npages = dict(src.execute('SELECT doc_id, count(*) FROM pages GROUP BY doc_id').fetchall())
            rows = [(r, d) for r, d in rows if npages.get(d) == 1]
        for rowid, doc in rows:
            title, coll, cat, path, page, body = src.execute(
                'SELECT title, collection, category, path, page, body FROM pages WHERE rowid=?', (rowid,)).fetchone()
            secs = cut(norm_ws(body))
            for n, (start, text) in enumerate(secs, 1):
                cur = db.execute('INSERT INTO pages(doc_id,title,collection,category,path,page,body) VALUES (?,?,?,?,?,?,?)',
                                 (doc, title, coll, cat, path, n, text))
                db.execute('INSERT INTO section VALUES (?,?,?,?)', (doc, n, start, cur.lastrowid))
            db.execute('INSERT INTO long VALUES (?,?,?,?)', (rowid, doc, int(page or 1), len(secs)))
            n_pages += 1
            n_sections += len(secs)
        db.execute("INSERT INTO pages(pages) VALUES('optimize')")
        summary = {'long_pages': n_pages, 'sections': n_sections, 'seconds': round(time.time() - t0, 2)}
        db.executemany('INSERT INTO meta VALUES (?,?)', [(k, str(v)) for k, v in summary.items()])
        db.commit()
    except BaseException:
        db.close()
        tmp.unlink(missing_ok=True)
        raise
    finally:
        db.close()
        src.close()
    try:
        os.replace(tmp, out)
    except OSError:  # another process built the same file meanwhile and has it open: use theirs
        tmp.unlink(missing_ok=True)
        if not out.exists():
            raise
    return summary


def ensure(main_db, kind_of, folder=None):
    """The current sections file for main_db, built if missing. None when it cannot be had (keyword search then runs on
    the library index alone, as upstream)."""
    try:
        sig = signature(main_db)
    except OSError:
        return None
    current = lambda: _state['sig'] == sig and _state['main'] == str(main_db) and (_state['path'] is None or _state['path'].exists())
    if current():
        return _state['path']
    with _lock:
        if current():  # also a failure for this signature: not tried again on every search
            return _state['path']
        folder = Path(folder or IDX)
        out = _file_for(sig, folder)
        try:
            built = None
            if not out.exists():
                built = build(main_db, kind_of, out)
            con = sqlite3.connect(ro_uri(out), uri=True)
            try:
                skip = tuple(r[0] for r in con.execute('SELECT rowid_main FROM long'))
                docs = {d: (p, n) for d, p, n in con.execute('SELECT doc_id, page, nsections FROM long')}
            finally:
                con.close()
        except (OSError, sqlite3.Error) as e:
            _state.update(sig=sig, path=None, skip=(), docs={}, main=str(main_db), error=f'{type(e).__name__}: {e}'[:200])
            return None
        stale = [p for p in folder.glob('sections-*.tmp') if time.time() - p.stat().st_mtime > 3600]   # a build that was stopped
        for old in list(folder.glob('sections-*.sqlite')) + stale:  # files for an earlier library index
            if old != out:
                try:
                    old.unlink()
                except OSError:
                    pass  # open in another process; removed next time
        _state.update(sig=sig, path=out, skip=skip, docs=docs, built=built, main=str(main_db), error=None)
        return out


def status():
    return {k: _state.get(k) for k in ('path', 'built', 'error')} | {'long_pages': len(_state['docs'])}


def sectioned(doc_id):
    """Number of sections of a document read in sections, else 0. Valid after ensure()."""
    v = _state['docs'].get(doc_id)
    return v[1] if v else 0


def query(main_db, kind_of, select, order, match, limit):
    """Rows of  SELECT <select> FROM pages WHERE pages MATCH ? ORDER BY <order> LIMIT ?  over the library index, with
    the rows of long HTML pages replaced by their sections (whose page is the section number).

    The two tables are ranked by `order` (a bm25 call) each and merged by it. bm25 scores from two FTS5 tables are only
    roughly comparable (each uses its own document count and average length), so the merge is approximate; it measured
    well enough (docs/FORK.md). Raises sqlite3.OperationalError for a bad MATCH, as the plain query does."""
    path = ensure(main_db, kind_of)
    skip = _state['skip'] if path else ()
    where = f" AND rowid NOT IN ({','.join(str(int(r)) for r in skip)})" if skip else ''
    sql = f'SELECT {select}, {order} FROM pages WHERE pages MATCH ?{{w}} ORDER BY {order} LIMIT ?'
    con = sqlite3.connect(ro_uri(main_db), uri=True)
    try:
        rows = con.execute(sql.format(w=where), (match, limit)).fetchall()
    finally:
        con.close()
    if path:
        con = sqlite3.connect(ro_uri(path), uri=True)
        try:
            rows += con.execute(sql.format(w=''), (match, limit)).fetchall()
        finally:
            con.close()
        rows.sort(key=lambda r: r[-1])
    return [r[:-1] for r in rows[:limit]]


def texts(doc_id):
    """The sections' texts of a document read in sections, in order, else None. Valid after ensure()."""
    path = _state['path']
    if not path or doc_id not in _state['docs']:
        return None
    con = sqlite3.connect(ro_uri(path), uri=True)
    try:
        return [b for (b,) in con.execute('SELECT p.body FROM section s JOIN pages p ON p.rowid = s.fts_rowid '
                                          'WHERE s.doc_id=? ORDER BY s.sec', (doc_id,))]
    finally:
        con.close()


def text(doc_id, sec):
    path = _state['path']
    if not path or doc_id not in _state['docs']:
        return None
    con = sqlite3.connect(ro_uri(path), uri=True)
    try:
        r = con.execute('SELECT p.body FROM section s JOIN pages p ON p.rowid = s.fts_rowid WHERE s.doc_id=? AND s.sec=?',
                        (doc_id, int(sec))).fetchone()
        return r[0] if r else None
    finally:
        con.close()


def starts(path, doc_id):
    """Start offsets of a document's sections, in order, from a sections file."""
    con = sqlite3.connect(ro_uri(path), uri=True)
    try:
        return [s for (s,) in con.execute('SELECT start FROM section WHERE doc_id=? ORDER BY sec', (doc_id,))]
    finally:
        con.close()


def long_rows(path):
    """(rowid in the library index, doc_id, page) of every long HTML page in a sections file."""
    con = sqlite3.connect(ro_uri(path), uri=True)
    try:
        return con.execute('SELECT rowid_main, doc_id, page FROM long').fetchall()
    finally:
        con.close()
