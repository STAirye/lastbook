"""Post the triage-based search proposal: push the 8 branches to the fork, open the issue, open the 8 PRs in order,
then fill the PR numbers into the issue. Dry run by default: renders every body into rendered/ and prints the commands.

    python post.py                 # dry run: rendered/*.md, nothing sent
    python post.py --go push       # push triage/1..8 to the fork (STAirye/lastbook)
    python post.py --go issue      # open the issue on Immortal-Protocols/lastbook
    python post.py --go prs        # open the PRs not opened yet, in order (needs the issue)
    python post.py --go fill       # put the PR numbers into the issue's list
State (issue and PR numbers) is kept in post_state.json, so every step can be rerun and skips what is done.
Each item is registered with the tracker after it is created.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = 'Immortal-Protocols/lastbook'
FORK_REMOTE = 'fork'
OWNER = 'STAirye'
LASTBOOK = Path(r'D:\git\lastbook')
TRACKER = LASTBOOK / '.claude' / 'tracker' / 'track.py'
AGENT = 'local_c9cd356e-22d7-44c7-b320-50728f3d05eb'
BRANCHES = {1: 'triage/1-search-eval', 2: 'triage/2-sections', 3: 'triage/3-typos', 4: 'triage/4-encyclopedias',
            5: 'triage/5-confidence', 6: 'triage/6-runner-embed', 7: 'triage/7-urgency', 8: 'triage/8-conversation'}
STATE = HERE / 'post_state.json'
OUT = HERE / 'rendered'


def state():
    return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'issue': None, 'prs': {}}


def save(s):
    STATE.write_text(json.dumps(s, indent=2), encoding='utf-8')


def split(path):
    """(title, body) of a draft: the first line is the title ('Title: ' dropped), the rest the body."""
    lines = path.read_text(encoding='utf-8').split('\n')
    title = re.sub(r'^Title:\s*', '', lines[0]).strip()
    return title, '\n'.join(lines[1:]).strip('\n') + '\n'


def fill(text, s, issue_list=False):
    text = text.replace('{ISSUE}', str(s['issue'] or '<issue>'))
    for n in range(1, 9):
        pr = s['prs'].get(str(n))
        if issue_list:      # in the issue's list: "(#N)" once a PR exists, nothing before
            text = text.replace(f' {{PR{n}}}', f' (#{pr})' if pr else '')
        else:
            text = text.replace(f'{{PR{n}}}', str(pr or f'<PR {n}>'))
    return text


def run(cmd, go):
    print('  $', ' '.join(cmd))
    if not go:
        return ''
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', cwd=LASTBOOK)
    if r.returncode:
        sys.exit(f'failed ({r.returncode}): {r.stderr.strip()}')
    return r.stdout.strip()


def register(url, note, go):
    run([sys.executable, str(TRACKER), 'register', url, '--agent', AGENT, '--note', note], go)


def drafts():
    return {n: next(HERE.glob(f'{n}-*.md')) for n in range(1, 9)}


def render(s):
    OUT.mkdir(exist_ok=True)
    title, body = split(HERE / '0-issue.md')
    (OUT / '0-issue.md').write_text(f'# {title}\n\n' + fill(body, s, issue_list=True), encoding='utf-8')
    for n, p in drafts().items():
        t, b = split(p)
        (OUT / p.name).write_text(f'# {t}\n\n' + fill(b, s), encoding='utf-8')
    left = [f.name for f in OUT.glob('*.md') if re.search(r'\{(ISSUE|PR\d)\}|<PR \d>|<issue>|\.claude/', f.read_text(encoding='utf-8'))]
    print('rendered into', OUT, '| still with slots or local paths:', left or 'none')


def main():
    go = '--go' in sys.argv
    step = sys.argv[-1] if go else None
    s = state()
    render(s)
    if not go:
        print('dry run; steps: push, issue, prs, fill')
        return
    if step == 'push':
        run(['git', 'push', FORK_REMOTE] + [f'{b}:{b}' for b in BRANCHES.values()], go)
    elif step == 'issue':
        if s['issue']:
            sys.exit(f'issue already open: #{s["issue"]}')
        title, body = split(HERE / '0-issue.md')
        f = OUT / '0-issue.body.md'
        f.write_text(fill(body, s, issue_list=True), encoding='utf-8')
        url = run(['gh', 'issue', 'create', '--repo', REPO, '--title', title, '--body-file', str(f)], go)
        s['issue'] = int(url.rstrip('/').split('/')[-1]); save(s)
        print('issue', url)
        register(url, 'triage-based search proposal (issue)', go)
    elif step == 'prs':
        if not s['issue']:
            sys.exit('open the issue first')
        for n, p in drafts().items():
            if str(n) in s['prs']:
                continue
            title, body = split(p)
            f = OUT / f'{n}.body.md'
            f.write_text(fill(body, s), encoding='utf-8')
            url = run(['gh', 'pr', 'create', '--repo', REPO, '--base', 'main', '--head', f'{OWNER}:{BRANCHES[n]}',
                       '--title', title, '--body-file', str(f)] + (['--draft'] if n > 1 else []), go)
            s['prs'][str(n)] = int(url.rstrip('/').split('/')[-1]); save(s)
            print(f'PR {n}', url)
            register(url, f'triage-based search, part {n} of 8', go)
    elif step == 'fill':
        title, body = split(HERE / '0-issue.md')
        f = OUT / '0-issue.body.md'
        f.write_text(fill(body, s, issue_list=True), encoding='utf-8')
        run(['gh', 'issue', 'edit', str(s['issue']), '--repo', REPO, '--body-file', str(f)], go)
    else:
        sys.exit('unknown step: ' + str(step))


if __name__ == '__main__':
    main()
