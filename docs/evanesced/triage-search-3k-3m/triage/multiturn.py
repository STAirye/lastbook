"""Score how the last message of a conversation is searched, under several strategies.

    python -I -X utf8 multiturn.py OUT.json SEARCH_DB VOCAB_CACHE NAME=URL [NAME=URL ...]

Strategies (each turns the conversation into the top 8 hits for the last message):
  latest     upstream: search the latest message only
  fork       the fork today (assistant.chat): the latest message's own search, the previous message joined with it,
             and the previous answer's citations first (approximated: the previous turn's top 3). followup_hits order.
  sensible   as fork, but "previous" is the last message that was not noise
  aware      no-model classifier: noise -> no search, keep the last results and show buttons; correction -> correction
             words stripped, pages already shown go last, no carried pages; addition / new / follow-up -> this message's
             own best 4 first, then the joined search, then carried pages
  aware+typo as aware, with typofix.correct on every message first
  combined   noise -> as aware (no search, buttons, never "previous"); correction -> as aware; a danger sign (DANGER)
             that the earlier sensible messages did not have -> as a new emergency: own best 5, then joined, no carried
             pages; otherwise (follow / add) -> the fork order with "previous" = the last sensible message
  combined+typo as combined, with typofix.correct on every message first
The classifier's guesses are compared with the labelled kind of every message after the first.
"""
import json, re, sys, urllib.parse, urllib.request
from collections import Counter
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convos import CONVOS  # noqa: E402
from score import agg, score  # noqa: E402
import typofix  # noqa: E402

K = 8
NOISE_PHRASE = re.compile(r"^\s*(sorry,? )?(wrong (chat|window|person|number)|ignore (that|this)|never ?mind|nvm|oops|lol( sorry)?|ok(ay)?|k|wait|sorry|hm+|test)\s*[.!]*\s*$", re.I)
CORRECT = re.compile(r"^\s*(no+\b[\s,!.]*)+|\b(i mean[t]?|not that|that'?s not|thats not|wrong one|not me|not him|not her|instead)\b", re.I)
CORRECT_STRIP = re.compile(r"^\s*(no+\b[\s,!.]*)+|\b(i mean[t]?|not that|that'?s not it|thats not it|wrong one)\b[\s,]*", re.I)
ADD = re.compile(r"\b(also|too|as well|and now|now (he|she|it|they|the|my|her|his)|plus|on top of)\b", re.I)

# Danger signs for `combined` (a new emergency inside a conversation). Built without the test labels.
# Each entry: name -> regex. Source of each part:
#   [P] server.PHRASES in worktrees/search-before/server.py (everyday emergency phrases)
#   [S] server.SYN keys in the same file that are ABCDE danger words (choking, unconscious, cpr)
#   [H] short hand list: ABCDE / fire / gas / flood danger words
# content/topics/*.json has no "urgent" phrases (checked 2026-11-18), so nothing comes from there.
POISON = r"(bleach|poison\w*|pills|tablets|medicine|detergent|cleaner|chemicals?|kerosene|paraffin|petrol|gasoline|antifreeze|lye|drain cleaner|rat poison|pesticide|weed ?killer)"
DANGER = {
    'heart attack': r"heart attack",                                            # [P]
    'passed out': r"(passed|blacked) out|faint(ed|ing)",                        # [P]
    'not breathing': r"can'?t breathe|cannot breathe|not breathing|stopped breathing",  # [P] (+[H] not breathing)
    'choking': r"\bchok(e|es|ed|ing)\b",                                       # [S] choking, [H]
    'unconscious': r"unconscious|unresponsive|won'?t wake( up)?|collapsed",     # [S] unconscious, [H]
    'cpr': r"\bcpr\b|no pulse",                                                # [S] cpr
    'bleeding a lot': r"bleeding (a lot|badly|heavily|everywhere)|won'?t stop bleeding|heavy bleeding|lots of blood|blood everywhere|spurting",  # [H]
    'seizure': r"seizures?|convuls\w*|fitting",                                 # [H]
    'chest pain': r"chest pains?|pain in (his|her|my|the) chest",               # [H]
    'on fire': r"on fire|caught fire|in flames",                                # [H]
    'smell gas': r"smell(s|ing)? (of )?gas|gas leak",                           # [H]
    'snake bit': r"snake ?bit(e|ten)?|bitten by a snake|snake .{0,12}\bbit\b",  # [H]
    'poison': r"(swallow\w*|drank|drunk|drink\w*|ate|eaten|ingest\w*) .{0,30}" + POISON + r"|poison(ed|ing)",  # [H]
    'stuck in water': r"(stuck|trapped|swept( away)?|drowning) (in|into|by) (the )?(water|river|flood\w*|pool|sea|current)|\bdrowning\b",  # [H]
    'trapped': r"\btrapped\b|pinned (under|down)|buried (under|alive)",          # [H]
}
DANGER_RX = {k: re.compile(v, re.I) for k, v in DANGER.items()}


def danger_signs(msg):
    m = msg.lower().replace('’', "'")
    return {k for k, rx in DANGER_RX.items() if rx.search(m)}


@lru_cache(maxsize=None)
def search(base, q):
    if not q.strip():
        return ()
    u = base + '/api/retrieve?' + urllib.parse.urlencode({'q': q[:300], 'k': K})
    with urllib.request.urlopen(u, timeout=180) as r:
        return tuple(json.loads(r.read().decode('utf-8'))['results'])


def key(h):
    return (h.get('doc_id'), h.get('page'), h.get('t'))


def merge(*parts, k=K, last=()):
    """parts: (hits, how_many) in order; then `last` at the very end. Each page once."""
    out, seen = [], set()
    for hits, n in parts:
        for h in list(hits)[:n]:
            if key(h) not in seen and len(out) < k:
                seen.add(key(h)); out.append(h)
    for h in last:
        if key(h) not in seen and len(out) < k:
            seen.add(key(h)); out.append(h)
    return out


def followup_hits(own, joined, first):
    return merge((own, first), (joined, K), (own[first:], K))


def classify(msg, V):
    """No model: noise, correct, add or follow (new is not told apart from follow without a model)."""
    if NOISE_PHRASE.match(msg) or not re.search(r'[a-z]', msg, re.I):
        return 'noise'
    # noise = mostly not words (pocket typing, keyboard mashing); short everyday words ("what do i not do") are words
    words = [w.strip("'") for w in re.findall(r"[a-z']+", msg.lower()) if w.strip("'")]
    known = [w for w in words if w in typofix.STOP or w in typofix.APOS or V.get(typofix.correct_word(w, V), 0) >= 20]
    if not words or len(known) / len(words) < 0.5:
        return 'noise'
    if CORRECT.search(msg):
        return 'correct'
    if ADD.search(msg):
        return 'add'
    return 'follow'


def run(base, turns, strategy, V):
    """Return (hits for the last message, buttons shown on the last message, guesses for each message after the first)."""
    prev_msg, prev_hits = None, []          # the message the next one is joined with, and its results
    sensible_msg, sensible_hits = None, []
    hits, buttons, guesses = [], False, []
    for i, (msg, _) in enumerate(turns):
        m = typofix.correct(msg, V) if strategy == 'aware+typo' else msg
        buttons = False
        own = list(search(base, m))
        if i == 0 or strategy == 'latest':
            hits = own
        elif strategy == 'fork':
            carried = prev_hits[:3]
            hits = followup_hits(carried + own, list(search(base, (prev_msg[:200] + ' ' + m).strip())), len(carried) + 4)
        else:
            kind = classify(msg, V)
            guesses.append(kind)
            if kind == 'noise':
                hits, buttons = sensible_hits, True   # nothing searched; the last useful results stay, with buttons
                continue
            if kind == 'correct':
                q = CORRECT_STRIP.sub(' ', m).strip() or m
                own = list(search(base, q))
                shown = {key(h) for h in sensible_hits}
                joined = list(search(base, (sensible_msg[:200] + ' ' + q).strip()))
                hits = merge(([h for h in own if key(h) not in shown], K), ([h for h in joined if key(h) not in shown], K),
                             last=[h for h in own if key(h) in shown])
            else:
                joined = list(search(base, (sensible_msg[:200] + ' ' + m).strip()))
                hits = merge((own, 4), (joined, K), (sensible_hits[:3], 3), (own, K))
            buttons = len(own) < 3
        prev_msg, prev_hits = m, hits
        sensible_msg, sensible_hits = m, hits   # noise never reaches here in 'aware'
    return hits, buttons, guesses


def run_combined(base, turns, V, typo=False, log=None):
    """'combined': noise / correct as aware, a new danger sign as a new emergency, everything else the fork order."""
    s_msg, s_hits, s_danger, hits, buttons = None, [], set(), [], False
    for i, (msg, _) in enumerate(turns):
        m = typofix.correct(msg, V) if typo else msg
        buttons = False
        own = list(search(base, m))
        signs = danger_signs(m)
        if i == 0:
            hits = own
        else:
            kind = classify(msg, V)
            if kind == 'noise':
                hits, buttons = s_hits, True
                if log is not None:
                    log.append('noise')
                continue
            if kind == 'correct':
                q = CORRECT_STRIP.sub(' ', m).strip() or m
                own = list(search(base, q))
                shown = {key(h) for h in s_hits}
                joined = list(search(base, (s_msg[:200] + ' ' + q).strip()))
                hits = merge(([h for h in own if key(h) not in shown], K), ([h for h in joined if key(h) not in shown], K),
                             last=[h for h in own if key(h) in shown])
            elif signs - s_danger:
                kind = 'danger:' + ','.join(sorted(signs - s_danger))
                joined = list(search(base, (s_msg[:200] + ' ' + m).strip()))
                hits = merge((own, 5), (joined, K), (own, K))
            else:
                carried = s_hits[:3]
                hits = followup_hits(carried + own, list(search(base, (s_msg[:200] + ' ' + m).strip())), len(carried) + 4)
            buttons = len(own) < 3
            if log is not None:
                log.append(kind)
        s_msg, s_hits, s_danger = m, hits, s_danger | signs
    return hits, buttons


def run_sensible(base, turns, V):
    """'sensible': like fork, but noise (by the no-model classifier) is skipped when choosing the previous message."""
    s_msg, s_hits, hits = None, [], []
    for i, (msg, _) in enumerate(turns):
        own = list(search(base, msg))
        if i == 0:
            hits = own
        else:
            if classify(msg, V) == 'noise':
                hits = s_hits
                continue
            carried = s_hits[:3]
            hits = followup_hits(carried + own, list(search(base, (s_msg[:200] + ' ' + msg).strip())), len(carried) + 4)
        s_msg, s_hits = msg, hits
    return hits


def main():
    out, db, cache = sys.argv[1], sys.argv[2], sys.argv[3]
    servers = dict(a.split('=', 1) for a in sys.argv[4:])
    V = typofix.vocab(db, cache)
    typofix.E.update(typofix.emergency_vocab(db, str(cache).replace('.json', '-emergency.json')))
    res = {'conversations': len(CONVOS), 'by_server': {}}
    # classifier against the labels (same for every server)
    conf = Counter()
    for c in CONVOS:
        for msg, kind in c['turns'][1:]:
            conf[(kind, classify(msg, V))] += 1
    res['classifier'] = {f'{a}->{b}': n for (a, b), n in sorted(conf.items())}
    print('classifier (label->guess):', res['classifier'], flush=True)
    for name, base in servers.items():
        res['by_server'][name] = {}
        for strat in ('latest', 'fork', 'sensible', 'aware', 'aware+typo', 'combined', 'combined+typo'):
            rows = []
            for c in CONVOS:
                route = []
                if strat.startswith('combined'):
                    hits, buttons = run_combined(base, c['turns'], V, typo=strat.endswith('+typo'), log=route)
                elif strat == 'sensible':
                    hits, buttons = run_sensible(base, c['turns'], V), False
                else:
                    hits, buttons, _ = run(base, c['turns'], strat, V)
                r = score(c, hits)
                last_kind = c['turns'][-1][1]
                kinds = [k for _, k in c['turns'][1:]]
                r.update(q=' / '.join(m for m, _ in c['turns']), kind=last_kind, has_noise='noise' in kinds, buttons=buttons,
                         first_title=(hits[0].get('title') if hits else None), route=route)
                rows.append(r)
            by = {k: agg([r for r in rows if r['kind'] == k]) for k in ('follow', 'add', 'correct', 'new')}
            by['after_noise'] = agg([r for r in rows if r['has_noise']])
            by['all'] = agg(rows)
            res['by_server'][name][strat] = {'summary': by, 'rows': rows}
            print(name, strat, json.dumps({k: (v['first_ok'], v['useful_mean'], v['zero_useful']) for k, v in by.items()}), flush=True)
    json.dump(res, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
