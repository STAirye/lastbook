r"""The integrated meaning check (branch fork/meaning-check) on the prototype's lists, read-only, no tuning.

  set LASTBOOK_DATA=D:\LastbookData-fork-test
  python -B -X utf8 integrated_eval.py CODE_DIR [CENTROIDS.npz] > out.json

Words = confidence.urgent(text, typos.correct(text)) as the prototype counted them; meaning = engine.meaning_red.check(
typos.correct(text) or text), the app's own call; also assistant.is_danger (the app's whole rule: danger signs, buttons,
words, OR meaning). CENTROIDS: another centroid file to load instead of the shipped one (the prototype's model_int8.npz).
"""
import json, os, sys, time
from pathlib import Path

CODE = Path(sys.argv[1])
DRAFTS = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(CODE)]
os.environ.pop('LASTBOOK_LOCAL_AI', None)
import psutil  # noqa: E402
P = psutil.Process()
from engine import sections as _sections  # noqa: E402
def _no_build(*a, **k):
    raise OSError('sections build refused (read-only run)')
_sections.build = _no_build
import retrieval  # noqa: E402
retrieval.AVAILABLE = False     # nothing of hybrid search is loaded here
import assistant  # noqa: E402
from engine import confidence, typos, meaning_red  # noqa: E402

rss0 = P.memory_info().rss
t = time.perf_counter()
ok = meaning_red.wait(60)
load_s = time.perf_counter() - t
rss1 = P.memory_info().rss
assert ok, meaning_red.status()
if len(sys.argv) > 2:
    import numpy as np
    with np.load(sys.argv[2]) as z:
        meaning_red._model.R, meaning_red._model.N = z['red'].astype(np.float32), z['nonred'].astype(np.float32)


def read_jsonl(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]


def load_triage():
    sys.path.insert(0, str(DRAFTS / 'triage'))
    out = []
    import cases, cases128, cases154, cases241, cases_glued
    for mod in (cases, cases128, cases154, cases241):
        for c in (mod.cases() if hasattr(mod, 'cases') else mod.CASES):
            out.append({'text': c['q'], 'triage': c['colour']})
    for c in cases_glued.CASES:
        out.append({'text': c['q'], 'triage': 'red' if c['red'] else 'green'})
    return out


lists = {'independent': read_jsonl(DRAFTS / 'independent' / 'phrases.jsonl'),
         'independent2': read_jsonl(DRAFTS / 'independent2' / 'phrases.jsonl'),
         'triage_insample': load_triage()}
res = {'threshold': meaning_red._model.threshold, 'load_s': round(load_s, 2), 'rss_MB_added_by_load': round((rss1 - rss0) / 2 ** 20)}
times_with, times_without = [], []
for name, rows in lists.items():
    c = {k: {l: 0 for l in ('red', 'yellow', 'green')} for k in ('words', 'meaning', 'or', 'is_danger', 'is_danger_words_only')}
    n = {l: 0 for l in ('red', 'yellow', 'green')}
    lost, rescued = [], []
    for r in rows:
        q, l = r['text'], r['triage']
        n[l] += 1
        fixed = typos.correct(q)
        w = bool(confidence.urgent(q, fixed))
        m = meaning_red.check(fixed or q)['fired']
        a = time.perf_counter(); d = assistant.is_danger(q); times_with.append(time.perf_counter() - a)
        os.environ['LASTBOOK_MEANING_RED'] = '0'
        a = time.perf_counter(); d0 = assistant.is_danger(q); times_without.append(time.perf_counter() - a)
        del os.environ['LASTBOOK_MEANING_RED']
        for k, v in (('words', w), ('meaning', m), ('or', w or m), ('is_danger', d), ('is_danger_words_only', d0)):
            c[k][l] += bool(v)
        if d0 and not d:
            lost.append(q)
        if l == 'red' and m and not w:
            rescued.append(q)
    res[name] = {k: {l: f'{v[l]}/{n[l]}' for l in v} for k, v in c.items()}
    res[name]['urgent_lost_by_meaning'] = lost
    res[name]['red_rescued_by_meaning'] = len(rescued)
times_with.sort(); times_without.sort()
ms = lambda ts, p: round(ts[int(len(ts) * p)] * 1000, 2)
res['is_danger_ms'] = {'with_meaning_median': ms(times_with, .5), 'with_meaning_p95': ms(times_with, .95),
                       'words_only_median': ms(times_without, .5), 'words_only_p95': ms(times_without, .95), 'n': len(times_with)}
res['rss_MB_end'] = round(P.memory_info().rss / 2 ** 20)
print(json.dumps(res, indent=1, ensure_ascii=False))
