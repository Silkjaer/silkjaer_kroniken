#!/usr/bin/env python3
"""Write identity translations for name/date-only segments (people, years, archive codes).
Usage: autopass.py <block> [<block> ...]  -> i18n/en/zz-auto-<block>.txt (review before compile)"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from tr import parse_txt, SEG, EN
TAG = re.compile(r'</?t\d+/?>|<n\d+/>|<br/>')
STOP = set('''Enke Ugift Mor Far Søn Datter Gift Født Død Og Se Kilde Kilder Billede Side Bind Træk Alle Samme
Første Anden Tredje Fire Tre To Otte Tretten Klik Under Stiplet Ejer Holmslands Erhverv Flugten Dømt Sagen Efter Skilsmissen Foråret Sorgen Sønnen Appendiks Gårdmand Husmand Fisker Sogn Herred Kirke Kirkebog Skøde'''.split())
REPL = [('Kapitel', 'Chapter'), ('Australien', 'Australia'), ('Sygehus', 'Hospital'), ('Folketælling', 'Census'), ('Kbh.', 'Cph.')]
LOWER_OK = {'f', 'd', 'ca', 'b', 'nr', 'fol', 'og', 'amp'}
done = {}
for fn in glob.glob(os.path.join(EN, '*.txt')):
    if not os.path.basename(fn).startswith('zz-auto-'):
        done.update(parse_txt(fn))
for blk in sys.argv[1:]:
    d = json.load(open(os.path.join(SEG, blk + '.json'), encoding='utf-8'))
    out = []
    cand = []
    for k, v in d.items():
        if k in done:
            continue
        plain = TAG.sub(' ', v)
        toks = re.findall(r"[A-Za-zÆØÅæøåÉéÖöÜü]+", plain)
        ok = bool(toks)
        for t in toks:
            if t in STOP or (t[0].islower() and t not in LOWER_OK):
                ok = False
                break
        if not re.search(r'\d|[A-ZÆØÅ][a-zæøå]+', plain):
            ok = False
        if ok:
            cand.append((k, v, toks))
    names = set()
    for k, v, toks in cand:
        if re.search(r'\d', v):
            names.update(toks)
    for k, v, toks in cand:
        if not re.search(r'\d', v) and not all(t in names for t in toks):
            continue
        if True:
            e = re.sub(r'(?<![\wÆØÅæøå])f\. ', 'b. ', v)
            e = re.sub(r'(?<![\wÆØÅæøå])ca\. ', 'c. ', e)
            e = e.replace(' og ', ' and ')
            for a, b in REPL:
                e = e.replace(a, b)
            out.append((k, e))
    fn = os.path.join(EN, f'zz-auto-{blk}.txt')
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(f'# auto identity pass for {blk}\n')
        for k, e in out:
            f.write(f'@{k}\n{e}\n')
    print(blk, len(out), 'auto ->', fn)
