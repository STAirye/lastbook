"""Run a Lastbook server with meaning-based search off, for keyword-only measurements.

    python -B kwserver.py SERVER_DIR PORT

retrieval.AVAILABLE is set before server.py imports it, so the index status is 'off' and hybrid() uses keywords only.
Nothing in SERVER_DIR or the data folder is changed (--no-index)."""
import runpy, sys

src, port = sys.argv[1], sys.argv[2]
sys.path.insert(0, src)
import retrieval  # noqa: E402

retrieval.AVAILABLE = False
sys.argv = [src + '/server.py', '--port', port, '--no-index']
runpy.run_path(src + '/server.py', run_name='__main__')
