"""Build PR 2's sections file for the test data folder into a scratch folder (never the data folder). argv: code, out folder."""
import sys, time
from pathlib import Path
code, folder = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(code))
import server
from engine import sections
sig = sections.signature(server.library.DB)
out = sections._file_for(sig, folder)
print('signature', sig, '->', out)
if not out.exists():
    print(sections.build(server.library.DB, server.kind_of, out))
else:
    print('exists')
