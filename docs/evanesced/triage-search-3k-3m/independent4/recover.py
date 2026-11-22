r"""Recover list 4's messages from messy model logs into clean JSON Lines, without anyone reading them.

Put the raw logs (any text: .txt, .log, .md, .json) in one folder per prompt, or straight into raw/ when it can't be
told which prompt made them (they become phrases_mixed.jsonl, with a guessed language per message):

    .claude/drafts/independent4/raw/serious/
    .claude/drafts/independent4/raw/messy/
    .claude/drafts/independent4/raw/multilingual/

then run, from the repo root:

    python .claude/drafts/independent4/recover.py

It writes phrases_serious.jsonl, phrases_messy.jsonl and phrases_multilingual.jsonl next to this script, plus
recover_report.json. What it PRINTS is counts only, never a message's text, so whoever runs it stays blind; the parts
it could not read go to rejected_<kind>.txt, for <owner> alone to look at if he wants.

How it reads: every {...} block anywhere in the text (inside code fences, after log prefixes, several per line or one
spread over several lines) is tried as JSON; if that fails, with common repairs (smart quotes, trailing commas,
Python-style 'single quotes' / True / None, a missing closing brace at the end of a block). An object is kept when it
has a non-empty "text" and a triage of red, yellow or green (also read from "label", "urgency", "colour"/"color",
any case). Missing optional fields get defaults; extra fields are kept. Duplicates (same text, ignoring case and
spaces) are dropped.
"""
import ast
import html
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / 'raw'
KINDS = ('serious', 'messy', 'multilingual', 'mixed')
TRIAGE_KEYS = ('triage', 'label', 'urgency', 'colour', 'color', 'level')
TRIAGE = {'red': 'red', 'yellow': 'yellow', 'green': 'green', 'amber': 'yellow', 'orange': 'yellow'}
SMART = str.maketrans({'“': '"', '”': '"', '„': '"', '‘': "'", '’': "'"})


def blocks(text):
    """Every top-level {...} block, by brace depth, ignoring braces inside double-quoted strings."""
    out, depth, start, in_str, esc = [], 0, None, False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"' and depth:
            in_str = True
        elif ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}' and depth:
            depth -= 1
            if depth == 0:
                out.append(text[start:i + 1])
                start = None
        elif ch == '\n' and depth and start is not None and text[start:i].count('\n') > 40:
            depth, start = 0, None          # a runaway block (an unclosed brace): give up on it
    if depth and start is not None:
        out.append(text[start:] + '}' * depth)   # cut off at the end of the log
    return out


def parse(block):
    """(object or None, how): plain JSON first, then repairs."""
    tries = [('json', block)]
    fixed = block.translate(SMART)
    fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
    tries.append(('repaired', fixed))
    for how, s in tries:
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return obj, how
        except ValueError:
            pass
    for tail in ('"]}', '"}', ']}'):    # cut off inside a string or a list at the end of a log
        try:
            obj = json.loads(fixed.rstrip('}').rstrip() + tail)
            if isinstance(obj, dict):
                return obj, 'cut-off, closed'
        except ValueError:
            pass
    try:
        obj = ast.literal_eval(re.sub(r'\b(true|false|null)\b',
                                      lambda m: {'true': 'True', 'false': 'False', 'null': 'None'}[m.group(1)], fixed))
        if isinstance(obj, dict):
            return obj, 'python-style'
    except (ValueError, SyntaxError, MemoryError, RecursionError):
        pass
    return None, None


LABEL = r'(?:triage|label|urgency|colou?r)?\s*[:=]?\s*[\[(]?\s*(red|yellow|green|amber)\s*[\])]?'
PLAIN = [   # a message on its own line with a label after or before it; numbering, bullets and quotes stripped
    # label last: "he cant breathe - RED", "my car is bleeding oil (green)", "text | triage: yellow"
    re.compile(r'^\s*(?:\d+[.)]|[-*•])?\s*(?P<t>.+?)\s*[-:|,(\[]+\s*' + LABEL + r'\s*$', re.I),
    # label first, only when bracketed or followed by a separator: "[RED] he cant breathe", "green: my car ..."
    re.compile(r'^\s*(?:\d+[.)]|[-*•])?\s*(?:[\[(]\s*(red|yellow|green|amber)\s*[\])]|(?:triage\s*[:=]\s*)?'
               r'(red|yellow|green|amber)\s*[-:|])\s*(?P<t>.+?)\s*$', re.I),
]


def plain_lines(text):
    """Messages written as plain lines with a red/yellow/green label, outside any {...} block."""
    outside = text
    for b in blocks(text):
        outside = outside.replace(b, '\n')
    out, section, counter = [], None, False
    for line in outside.splitlines():
        if not line.strip() or len(line) > 600:
            continue
        head = re.sub(r'[#*_:=\s]+', ' ', line).strip()
        hm = re.match(r'(red|yellow|green|amber)\b', head, re.I)
        if hm and len(head) <= 40 and (line.rstrip().endswith(':') or line.lstrip().startswith(('#', '**', '=='))
                                       or head.lower() == hm.group(1).lower()):
            section, counter = hm.group(1), 'counter' in head.lower()   # a heading: "RED:", "## Green (counterexamples)", "**Yellow**"
            continue
        for rx in PLAIN:
            m = rx.match(line)
            if m:
                t = clean(m.group('t'))
                tri = next(g for g in m.groups() if g and g.lower() in TRIAGE)
                if len(t) >= 3 and not re.fullmatch(LABEL, t, re.I):
                    out.append({'text': t, 'triage': tri})
                break
        else:
            m = re.match(r'^\s*(?:\d+[.)]|[-*•])\s+(?P<t>.+?)\s*$', line)
            if section and m and len(clean(m.group('t'))) >= 3:
                out.append({'text': clean(m.group('t')), 'triage': section, '_heading': True, **({'kind': ['counterexample']} if counter else {})})
    return out


def clean(t):
    t = re.sub(r'^(?:message|text|msg|q|user|phrase)\s*[:=]\s*', '', t.strip(), flags=re.I)
    return t.strip().strip('"\'“”‘’').strip()


def norm(obj, kind):
    """The object in list 3's shape, or (None, why)."""
    obj = {str(k).strip().lower(): v for k, v in obj.items()}
    text = obj.get('text') or obj.get('message') or obj.get('phrase')
    if not isinstance(text, str) or not text.strip():
        return None, 'no text'
    tri = next((obj[k] for k in TRIAGE_KEYS if isinstance(obj.get(k), str)), '')
    tri = TRIAGE.get(tri.strip().lower())
    if not tri:
        return None, 'no red/yellow/green'
    out = dict(obj)
    for k in ('message', 'phrase', 'label', 'urgency', 'colour', 'color', 'level'):
        out.pop(k, None)
    out['text'] = text.strip()
    out['triage'] = tri
    out['meaning'] = out.get('meaning') if isinstance(out.get('meaning'), str) else ''
    for k in ('signs', 'kind'):
        v = out.get(k)
        out[k] = [str(x) for x in v] if isinstance(v, list) else ([v] if isinstance(v, str) and v else [])
    out.setdefault('persona', '')
    out['source'] = out.get('source') if out.get('source') in ('invented', 'web-inspired') else 'invented'
    out['list'] = f'4-{kind}'
    if not isinstance(out.get('lang'), str) or not out['lang'].strip():
        out['lang'] = guess_lang(out['text'])
        out['lang_guessed'] = True
    return out, None


# A rough language guess from common short words, for files that don't say. Messages are short and typed casually, so
# it is a hint for splitting the results, not a fact; "lang_guessed" marks it.
COMMON = {
    'en': 'the a an is are was i my me he she it you and to of in on not dont cant wont im hes shes what how help his her'.split(),
    'es': 'el la los las es está esta mi me se que y de en no un una por para con como ayuda tiene estoy hijo hija'.split(),
    'pt': 'o a os as é está meu minha não que e de em um uma por para com como socorro ele ela tá tô'.split(),
    'fr': 'le la les est mon ma mes il elle je ne pas que et de en un une pour avec comment aide'.split(),
    'de': 'der die das ist mein meine er sie ich nicht und zu von mit wie hilfe ein eine kann'.split(),
    'it': 'il la lo è mio mia lui lei io non che e di in un una per con come aiuto sta'.split(),
}
COMMON = {k: set(v) for k, v in COMMON.items()}


def guess_lang(text):
    words = re.findall(r"[a-záéíóúâêôãõçàèìòùäöüßñ']+", text.lower())
    score = {k: sum(w in v for w in words) for k, v in COMMON.items()}
    best = max(score, key=score.get)
    if score[best] == 0:
        return '?'
    tied = [k for k, v in score.items() if v == score[best]]
    return best if len(tied) == 1 else ('en' if 'en' in tied else '?')


def main():
    report = {}
    for kind in KINDS:
        if kind == 'mixed':     # files put straight into raw/, when it can't be told which prompt made them
            files = sorted(p for p in RAW.glob('*') if p.is_file()) if RAW.is_dir() else []
        else:
            folder = RAW / kind
            files = sorted(p for p in folder.rglob('*') if p.is_file()) if folder.is_dir() else []
        if not files:
            continue
        keep, seen, rejected = [], set(), []
        c = collections.Counter()
        for f in files:
            raw = f.read_bytes().decode('utf-8', errors='replace')
            # A log can hold the model's output as an escaped string (\" and \n), and parts of it HTML-escaped again
            # (&quot;text&quot;: ...). The file is read as it is and again with every layer of escaping undone; the
            # duplicates this makes are dropped below.
            flat = raw
            for _ in range(3):
                before = flat
                flat = html.unescape(flat)
                flat = flat.replace('\\\\', '\x00').replace('\\"', '"').replace('\\n', '\n').replace('\\t', ' ').replace('\x00', '\\')
                if flat == before:
                    break
            found = []
            for text in ((raw, flat) if flat != raw else (raw,)):
                found += [(b, *parse(b)) for b in blocks(text)] + [
                    (None, o, 'plain line under a heading' if o.pop('_heading', False) else 'plain line') for o in plain_lines(text)]
            for b, obj, how in found:
                c['blocks' if b is not None else 'plain lines seen'] += 1
                b = b if b is not None else obj['text']
                if obj is None:
                    c['unreadable'] += 1
                    rejected.append(f'--- {f.name}: unreadable\n{b}\n')
                    continue
                c[how] += 1
                row, why = norm(obj, kind)
                if row is None:
                    c[why] += 1
                    rejected.append(f'--- {f.name}: {why}\n{b}\n')
                    continue
                key = re.sub(r'\s+', ' ', row['text'].lower())
                if key in seen:
                    c['duplicate'] += 1
                    continue
                seen.add(key)
                keep.append(row)
        with open(HERE / f'phrases_{kind}.jsonl', 'w', encoding='utf-8', newline='\n') as out:
            for row in keep:
                out.write(json.dumps(row, ensure_ascii=False) + '\n')
        (HERE / f'rejected_{kind}.txt').write_text(''.join(rejected), encoding='utf-8')
        tri = collections.Counter(r['triage'] for r in keep)
        langs = collections.Counter(r.get('lang') or '?' for r in keep)
        report[kind] = {'files': len(files), 'kept': len(keep), 'red': tri['red'], 'yellow': tri['yellow'],
                        'green': tri['green'], 'with meaning': sum(1 for r in keep if r['meaning']),
                        'counterexamples': sum(1 for r in keep if 'counterexample' in r['kind']), **dict(c)}
        if langs:
            report[kind]['languages'] = dict(langs.most_common())
    (HERE / 'recover_report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    if not report:
        sys.exit(f'nothing found: put the logs in {RAW} (or in its serious, messy and multilingual folders)')
    for kind, r in report.items():   # counts only: no message text is printed
        print(kind, json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
