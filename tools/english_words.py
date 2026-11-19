#!/usr/bin/env python3
"""fork: builds engine/english_words.txt.gz, the ordinary English words engine/typos.py never "corrects" (docs/FORK.md 3k).

    python tools/english_words.py <en-US .bdic> engine/english_words.txt.gz

The input is the hunspell en_US dictionary as Chromium ships it for spell checking (en-US-10-2.bdic in Chrome's or
VS Code's "Dictionaries" folder; licence: engine/english_words.LICENSE.txt). Every form of every word is written, the
dictionary's affixes applied (keel -> keeled, keeling, keels), one per line, sorted: only words of plain lower-case a-z,
so names, abbreviations in capitals and words with apostrophes or digits are left out. Not run by the app or the build.

The .bdic layout (Chromium third_party/hunspell/google/bdict.h): a header ("BDic", version, offsets of the affix and
word sections), the affix section (the .aff file's AF groups and PFX/SFX rules as NUL-terminated lines), and the words as
a trie of leaf, lookup and list nodes; a leaf carries the number of the AF group of its word's affix flags.
"""
import gzip, re, struct, sys


def words_of(b):
    assert b[:4] == b'BDic', 'not a .bdic file'
    aff, dic = struct.unpack('<II', b[8:16])
    g_off, r_off, rep_off, _ = struct.unpack('<IIII', b[aff:aff + 16])
    lines = lambda o, end: [s.decode('utf-8') for s in b[o:end].split(b'\0')]
    groups = [g[3:] for g in lines(g_off, r_off) if g.startswith('AF ')]   # groups[0] is the count; affix id N -> groups[N]
    rules = {}
    for line in lines(r_off, rep_off):
        p = line.split()
        if len(p) == 4 and p[0] in ('PFX', 'SFX') and p[2] in 'YN' and p[3].isdigit():          # PFX A Y 1: the header
            rules.setdefault(p[1], {'kind': p[0], 'r': []})['cross'] = p[2] == 'Y'
        elif len(p) >= 4 and p[0] in ('PFX', 'SFX'):                                             # PFX A 0 re .
            rules.setdefault(p[1], {'kind': p[0], 'cross': False, 'r': []})['r'].append(
                ('' if p[2] == '0' else p[2], '' if p[3] == '0' else p[3].split('/')[0], p[4] if len(p) > 4 else '.'))
    entries = []
    stack = [(dic, b'')]
    while stack:
        o, prefix = stack.pop()
        t = b[o]
        if t & 0x80 == 0:                                   # leaf: affix id, the rest of the word, more affix ids
            p, word = o + 2, prefix
            entries.append(((t & 0x1F) << 8) | b[o + 1])
            if t & 0x40:
                e = b.index(b'\0', p)
                word, p = prefix + b[p:e], e + 1
            entries[-1] = (word, entries[-1])
            if t & 0x20:
                while True:
                    (x,) = struct.unpack('<H', b[p:p + 2])
                    p += 2
                    if x == 0xFFFF:
                        break
                    entries.append((word, x))
        elif t & 0xE0 == 0xC0:                              # lookup: a table of children by letter
            first, n, wide = b[o + 1], b[o + 2], t & 0x02
            size, p = (4 if wide else 2), o + 3
            table = []
            if t & 0x01:                                    # the word ends here
                table.append((None, p))
                p += size
            table += [(first + i, p + i * size) for i in range(n)]
            for ch, q in table:
                off = struct.unpack('<I' if wide else '<H', b[q:q + size])[0]
                if off:
                    stack.append((off if wide else o + off, prefix if ch is None else prefix + bytes([ch])))
        else:                                               # list: a few (letter, offset) pairs
            n, size = t & 0x0F, (3 if t & 0x10 else 2)
            base = o + 1 + n * size
            for i in range(n):
                q = o + 1 + i * size
                off = struct.unpack('<H', b[q + 1:q + 3])[0] if size == 3 else b[q + 1]
                stack.append((base + off, prefix if b[q] == 0 else prefix + bytes([b[q]])))
    out = set()
    for raw, aid in entries:
        w = raw.decode('utf-8')
        flags = groups[aid] if 0 < aid < len(groups) else ''
        out.add(w)
        crossed = [w]
        for f in flags:
            R = rules.get(f)
            if R and R['kind'] == 'SFX':
                for strip, add, cond in R['r']:
                    if re.search('(' + cond + ')$', w) and w.endswith(strip):
                        x = w[:len(w) - len(strip)] + add
                        out.add(x)
                        if R['cross']:
                            crossed.append(x)
        for f in flags:
            R = rules.get(f)
            if R and R['kind'] == 'PFX':
                for strip, add, cond in R['r']:
                    for x in (crossed if R['cross'] else [w]):
                        if re.search('^(' + cond + ')', x) and x.startswith(strip):
                            out.add(add + x[len(strip):])
    return sorted(w for w in out if re.fullmatch(r'[a-z]+', w))


if __name__ == '__main__':
    words = words_of(open(sys.argv[1], 'rb').read())
    with gzip.GzipFile(sys.argv[2], 'wb', compresslevel=9, mtime=0) as f:     # mtime 0: the same bytes each time
        f.write(('\n'.join(words) + '\n').encode('utf-8'))
    print(len(words), 'words ->', sys.argv[2])
