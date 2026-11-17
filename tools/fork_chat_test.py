"""Fork: a 10-turn chat with a confused user, run against a test server the way the browser runs it, to measure how the
local AI cites. Each earlier answer goes back with its [Sn] keys turned into "(Title, p. N)", as web/chat.js history_()
does. Turn 5 corrects a unit, turn 6 misremembers what the assistant said (that boiling removes chemicals), turn 7 is
confusion. See docs/FORK.md, 3g.

    LASTBOOK_DATA=D:\\LastbookData LASTBOOK_LOCAL_AI=1 python server.py --port 8899
    python tools/fork_chat_test.py LABEL [CONVERSATIONS] [--turns N]

Writes LABEL.json (every answer) in the current folder and prints a line per turn. An answer counts as good when it has
[Sn] keys, no "(Title, p. N)" or "[Title, p. N]" citation and no thinking shows."""
import argparse, json, re, time, urllib.request

QS = [
    'tap water is out, i have tap water stored in sealed containers but its around 6 months old, it looks fine, can i drink it?',
    'in other words, its better to treat it as water that looks clean, but is not reliably safe for drinking. boiling should work?',
    'its stored in a airtight, 5 gallons, plastic cap, glass container. so boiling it is.',
    'how long do i boil it, i live kinda high up, like 2500 feet??',
    'wait sorry i meant 2500 meters not feet, does that change anything',
    'ok so you said boiling also gets rid of chemicals right? the water smells a bit like bleach so after boiling it should be fine',
    'hm ok im confused now. so can i drink it or not',
    'what if i dont have fuel to boil, can i use bleach instead? how much for 5 gallons',
    'my kid is 3, is the treated water ok for her or does she need something different',
    'ok final: give me the short steps again, everything i should do',
]


def ask(port, messages):
    """One answer from /api/chat: its done event, or {'answer': '', 'error': ...}."""
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api/chat', json.dumps({'messages': messages}).encode(),
                                 {'Content-Type': 'application/json'})
    done = None
    with urllib.request.urlopen(req, timeout=600) as r:
        for raw in r:
            line = raw.decode('utf-8').strip()
            if not line.startswith('data:'):
                continue
            try:
                ev = json.loads(line[5:])
            except ValueError:
                continue
            if ev.get('type') == 'done':
                done = ev
            elif ev.get('type') == 'error' and not done:
                done = {'answer': '', 'sources': [], 'error': ev.get('error')}
    return done or {'answer': '', 'sources': []}


def as_history(done):
    """The answer as web/chat.js history_() sends it back: [S2] -> (Title, p. 12), unknown keys removed."""
    by = {s['key']: s for s in done.get('sources') or []}

    def sub(m):
        s = by.get(m.group(1))
        if not s:
            return ''
        return f"({s['title']}{', p. ' + str(s['page']) if s.get('page') else ''})"
    return re.sub(r'\[([SM]\d+)\]', sub, done.get('answer') or '')


def score(d):
    t = d.get('answer') or ''
    return {'keys': len(re.findall(r'\[[SM]\d+\]', t)),
            'plain': len(re.findall(r'\([^()]*p\. \d+\)', t)),
            'bracket': len(re.findall(r'\[[^\[\]]*p\. \d+\]', t)),
            'linked': len(d.get('sources') or []),
            'invalid': len(d.get('invalid') or []),
            'leak': bool(re.search(r'thinking process|<channel\|>|<\|channel>|<\|turn>', t, re.I)),
            'chars': len(t),
            'secs': (d.get('latency') or {}).get('total_s')}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('label')
    ap.add_argument('conversations', type=int, nargs='?', default=2)
    ap.add_argument('--turns', type=int, default=len(QS))
    ap.add_argument('--port', type=int, default=8899)
    a = ap.parse_args()
    for _ in range(60):     # wait for the model to load
        try:
            if ask(a.port, [{'role': 'user', 'content': 'hi'}])['answer']:
                break
        except OSError:
            pass
        time.sleep(3)
    out = []
    for c in range(a.conversations):
        msgs, turns = [], []
        for n, q in enumerate(QS[:a.turns], 1):
            msgs.append({'role': 'user', 'content': q})
            d = ask(a.port, msgs)
            s = score(d)
            turns.append(dict(s, q=q, answer=d.get('answer') or '', error=d.get('error')))
            print(f"{a.label} conv {c + 1} turn {n:2}: keys {s['keys']:2} | (title) {s['plain']:2} | [title] {s['bracket']:2} | "
                  f"linked {s['linked']:2} | invalid {s['invalid']} | leak {s['leak']} | {s['chars']:5} chars | {s['secs']} s", flush=True)
            h = as_history(d)
            if h:
                msgs.append({'role': 'assistant', 'content': h})
            else:
                msgs.pop()      # chat.js drops an empty answer
        out.append(turns)
    with open(f'{a.label}.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    good = sum(t['keys'] > 0 and t['plain'] == 0 and t['bracket'] == 0 and not t['leak'] for conv in out for t in conv)
    print(f'{a.label}: answers citing with keys only, no thinking shown: {good} of {sum(len(c) for c in out)}')


if __name__ == '__main__':
    main()
