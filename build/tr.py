#!/usr/bin/env python3
"""Translation helper.

  tr.py show <block> [from] [count]   print Danish segments as '@id' + text blocks
  tr.py compile                       i18n/en/*.txt -> i18n/en/*.json, checking placeholder tags
  tr.py status                        how many segments per block are still untranslated

Translation files use the same layout as 'show':  a line '@<id>' followed by the English text
(one or more lines, joined with a space). Lines starting with '#' are comments.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(HERE, 'segments')
EN = os.path.join(HERE, 'i18n', 'en')
TAG = re.compile(r'</?t\d+/?>|<n\d+/>|<br/>')


def load_src():
    src = {}
    for fn in glob.glob(os.path.join(SEG, '*.json')):
        src.update(json.load(open(fn, encoding='utf-8')))
    return src


def parse_txt(fn):
    out, cur, buf = {}, None, []
    for line in open(fn, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('#'):
            continue
        m = re.match(r'^@([0-9a-f]{12})\s*$', line)
        if m:
            if cur:
                out[cur] = ' '.join(x.strip() for x in buf if x.strip())
            cur, buf = m.group(1), []
        else:
            buf.append(line)
    if cur:
        out[cur] = ' '.join(x.strip() for x in buf if x.strip())
    return out


def tags(s):
    return sorted(TAG.findall(s))


def main():
    cmd = sys.argv[1]
    if cmd == 'show':
        blk = sys.argv[2]
        a = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        n = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 6
        d = json.load(open(os.path.join(SEG, blk + '.json'), encoding='utf-8'))
        done = {}
        for fn in glob.glob(os.path.join(EN, '*.txt')):
            done.update(parse_txt(fn))
        items = [(k, v) for k, v in d.items() if k not in done]
        for k, v in items[a:a + n]:
            print('@' + k)
            print(v)
        print(f'# {len(items)} untranslated in {blk}', file=sys.stderr)
    elif cmd == 'compile':
        src = load_src()
        allt = {}
        bad = 0
        for fn in sorted(glob.glob(os.path.join(EN, '*.txt'))):
            t = parse_txt(fn)
            for k, v in t.items():
                if k in src and tags(src[k]) != tags(v):
                    bad += 1
                    print('TAG MISMATCH', os.path.basename(fn), k, '\n  da:', src[k][:200], '\n  en:', v[:200])
                if not v:
                    bad += 1
                    print('EMPTY', k)
            allt.update(t)
            json.dump(t, open(fn[:-4] + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print('compiled', len(allt), 'segments;', bad, 'problems')
    elif cmd == 'status':
        done = {}
        for fn in glob.glob(os.path.join(EN, '*.txt')):
            done.update(parse_txt(fn))
        tot = 0
        for fn in sorted(glob.glob(os.path.join(SEG, '*.json'))):
            d = json.load(open(fn, encoding='utf-8'))
            left = [k for k in d if k not in done]
            tot += len(left)
            if left:
                print(os.path.basename(fn)[:-5], len(left), sum(len(d[k]) for k in left))
        print('left', tot)


if __name__ == '__main__':
    main()
