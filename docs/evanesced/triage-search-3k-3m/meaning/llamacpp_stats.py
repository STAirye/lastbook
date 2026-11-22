"""GGUF (llama.cpp runner) vs ONNX int8 meaning check, statistics run. Read-only; writes LLAMACPP_STATS.json next to it.
python -X utf8 llamacpp_stats.py"""
import importlib.util, json, subprocess, sys, threading, time
from pathlib import Path
import numpy as np, psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common                                   # noqa: E402  (sets LASTBOOK_DATA, imports engine)
import cv                                       # noqa: E402
from common import read_jsonl, corrected, words_flag  # noqa: E402

DRAFTS = HERE.parent
WT = Path(r'D:\git\lastbook\.claude\worktrees\meaning-check')
EXE = Path(r'D:\buildtools\lastbook-llm\work-meaning\bin-win\lastbook-llm.exe')
GGUF = HERE / 'gguf' / 'bge-small-en-v1.5-q8_0.gguf'


class Runner:
    def __init__(self):
        self.p = subprocess.Popen([str(EXE), '--model', str(GGUF), '--embed', '--cpu-only', '--threads', '2'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(EXE.parent))
        threading.Thread(target=lambda: [None for _ in self.p.stderr], daemon=True).start()
        while json.loads(self.p.stdout.readline()).get('ev') != 'ready':
            pass

    def embed(self, texts):
        self.p.stdin.write((json.dumps({'op': 'embed', 'id': 1, 'texts': texts, 'max_tokens': 320}, ensure_ascii=False) + '\n').encode('utf-8'))
        self.p.stdin.flush()
        ev = json.loads(self.p.stdout.readline())
        assert ev['ev'] == 'embedding', ev
        return np.array(ev['vectors'], dtype=np.float32)

    def mem(self):
        m = psutil.Process(self.p.pid).memory_info()
        return {'peak_wset_MB': round(m.peak_wset / 2**20), 'private_MB': round(m.private / 2**20), 'wset_MB': round(m.wset / 2**20)}


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


def main():
    res = {}
    r = Runner()
    # ---- 1. refit on examples only
    EX = cv.EX
    ex_t = corrected([x['text'] for x in EX])
    X = np.vstack([r.embed([t]) for t in ex_t])
    s = cv.oof_scores(X, lambda: cv.Centroid(True))
    th = {'strict': float(cv.threshold_for(s, .05)), 'wide': float(cv.threshold_for(s, .10))}
    cvres = {k: cv.summarize(s, t) for k, t in th.items()}
    m = cv.Centroid(True)
    m.fit(X, cv.LAB, cv.CAT)
    res['cv'] = {'thresholds': th, 'oof': cvres, 'int8_prototype': {'strict': 0.81, 'wide': 0.90},
                 'n_red_centroids': len(m.R), 'n_nonred_centroids': len(m.N), 'n_examples': len(EX)}
    np.savez(HERE / 'model_gguf.npz', red=m.R, nonred=m.N, strict=th['strict'], wide=th['wide'])
    print('CV', json.dumps(res['cv']), flush=True)

    # ---- int8 ONNX (branch 51c7a4f), shipped centroids and wide threshold
    spec = importlib.util.spec_from_file_location('meaning_red_wt', WT / 'engine' / 'meaning_red.py')
    mr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mr)
    i8 = mr.Model(WT / 'derived' / 'models' / 'meaning-red')
    i8.score('warm up')
    res['int8_threshold'] = {'wide': i8.threshold, 'strict': i8.strict}

    lists = {'list1': read_jsonl(DRAFTS / 'independent' / 'phrases.jsonl'),
             'list2': read_jsonl(DRAFTS / 'independent2' / 'phrases.jsonl'),
             'list3': read_jsonl(DRAFTS / 'independent3' / 'phrases.jsonl'),
             'triage_insample': load_triage()}
    times = []
    for name, rows in lists.items():
        texts = [x['text'] for x in rows]
        lab = np.array([x['triage'] for x in rows])
        corr = corrected(texts)
        words = np.array([words_flag(t) for t in texts])
        sg = np.zeros(len(rows))
        si = np.zeros(len(rows))
        for i, t in enumerate(corr):
            a = time.perf_counter()
            v = r.embed([t[:2000]])[0]
            sc = float((m.R @ v).max() - (m.N @ v).max())
            times.append((time.perf_counter() - a) * 1000)
            sg[i] = sc
            si[i] = i8.score(t[:2000])
        mg_w, mg_s = sg > th['wide'], sg > th['strict']
        mi_w, mi_s = si > i8.threshold, si > i8.strict
        flags = {'words': words, 'int8_wide': words | mi_w, 'int8_strict': words | mi_s,
                 'gguf_wide': words | mg_w, 'gguf_strict': words | mg_s,
                 'meaning_int8_wide': mi_w, 'meaning_gguf_wide': mg_w, 'meaning_gguf_strict': mg_s}
        out = {'n': {l: int((lab == l).sum()) for l in ('red', 'yellow', 'green')}, 'counts': {}}
        for k, f in flags.items():
            out['counts'][k] = {l: int(f[lab == l].sum()) for l in ('red', 'yellow', 'green')}
        if 'kind' in rows[0]:
            kinds = {}
            for kd in ('counterexample', 'mild'):
                idx = np.array([kd in x['kind'] for x in rows]) & (lab == 'green')
                kinds[kd] = {'n': int(idx.sum()), **{k: int(f[idx].sum()) for k, f in flags.items()}}
            out['green_kinds'] = kinds

        def ex(mask, n=60):
            return [{'text': texts[i], 'label': str(lab[i]), 'gguf': round(float(sg[i]), 4), 'int8': round(float(si[i]), 4),
                     'words': bool(words[i])} for i in np.where(mask)[0][:n]]
        for op, mg in (('wide', mg_w), ('strict', mg_s)):
            for l in ('red', 'yellow', 'green'):
                out[f'{l}_only_by_meaning_gguf_{op}'] = int((mg & ~words & (lab == l)).sum())
        for l in ('red', 'yellow', 'green'):
            out[f'{l}_only_by_meaning_int8_wide'] = int((mi_w & ~words & (lab == l)).sum())
        dis = mg_w != mi_w
        out['disagree_meaning_gguf_wide_vs_int8_wide'] = {
            'count': int(dis.sum()),
            'gguf_fires_int8_not': {l: int((dis & mg_w & (lab == l)).sum()) for l in ('red', 'yellow', 'green')},
            'int8_fires_gguf_not': {l: int((dis & mi_w & (lab == l)).sum()) for l in ('red', 'yellow', 'green')},
            'examples_gguf_only': ex(dis & mg_w, 40), 'examples_int8_only': ex(dis & mi_w, 40)}
        dis_or = flags['gguf_wide'] != flags['int8_wide']
        out['disagree_OR_verdict_wide'] = {'count': int(dis_or.sum()), 'examples': ex(dis_or, 60)}
        out['red_missed_gguf_wide_OR'] = [texts[i] for i in np.where(~flags['gguf_wide'] & (lab == 'red'))[0]]
        out['red_missed_int8_wide_OR'] = [texts[i] for i in np.where(~flags['int8_wide'] & (lab == 'red'))[0]]
        out['red_lost_vs_words_gguf_wide'] = [texts[i] for i in np.where(words & ~flags['gguf_wide'] & (lab == 'red'))[0]]
        out['red_only_by_meaning_gguf_wide_examples'] = [texts[i] for i in np.where(mg_w & ~words & (lab == 'red'))[0]]
        out['green_only_by_meaning_gguf_wide_examples'] = [texts[i] for i in np.where(mg_w & ~words & (lab == 'green'))[0]][:80]
        res[name] = out
        print(name, json.dumps(out['counts']), 'disagree', out['disagree_meaning_gguf_wide_vs_int8_wide']['count'], flush=True)

    # ---- speed
    t = np.array(times)
    res['speed'] = {'n': len(t), 'single_request_ms_median': round(float(np.median(t)), 2),
                    'p95': round(float(np.percentile(t, 95)), 2), 'p99': round(float(np.percentile(t, 99)), 2),
                    'max': round(float(t.max()), 1), 'mean': round(float(t.mean()), 2)}
    allc = [x for rows in lists.values() for x in corrected([y['text'] for y in rows])]
    ev = {}
    for bs in (8, 32, 128):
        a = time.perf_counter()
        for i in range(0, len(allc), bs):
            r.embed([x[:2000] for x in allc[i:i + bs]])
        tot = time.perf_counter() - a
        ev[f'batch{bs}'] = {'ms_per_question': round(tot / len(allc) * 1000, 2), 'total_s': round(tot, 1)}
    res['speed']['batching'] = ev
    ti = []
    for x in allc[::5]:
        a = time.perf_counter()
        i8.score(x[:2000])
        ti.append((time.perf_counter() - a) * 1000)
    res['speed']['int8_inprocess_ms_median'] = round(float(np.median(ti)), 2)
    res['speed']['int8_inprocess_ms_p95'] = round(float(np.percentile(ti, 95)), 2)
    res['runner_memory'] = r.mem()
    print(json.dumps(res['speed']), res['runner_memory'], flush=True)
    r.p.stdin.write(b'{"op":"quit"}\n')
    r.p.stdin.flush()
    json.dump(res, open(HERE / 'LLAMACPP_STATS.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)


if __name__ == '__main__':
    main()
