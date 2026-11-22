"""Run tools/search_eval/score.py with engine.sections reading its file from a scratch folder.
argv: <score.py> <sections folder or -> <score.py args...>"""
import runpy, sys
from pathlib import Path
score_py, folder = sys.argv[1], sys.argv[2]
sys.argv = [score_py] + sys.argv[3:]
mod = runpy.run_path(score_py, run_name='score_mod')
orig = mod['start']

def start(code, mode):
    out = orig(code, mode)
    if folder != '-':
        from engine import sections
        sections.IDX = Path(folder)   # read here; the build itself stays refused by score.py
        print('sections folder', sections.IDX, flush=True)
    return out
mod['main'].__globals__['start'] = start
mod['main']()
