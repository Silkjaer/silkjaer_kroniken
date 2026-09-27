#!/usr/bin/env python3
"""Build the new edition of the Silkjær chronicle (ny/) from the classic index.html.

    python3 ny.py                       preview build: ny/ (noindex), Danish + English
    python3 ny.py --release             pages meant to live at the site root (indexable, canonical URLs)

The chronicle's own text is carried over word for word: the classic page is rendered (templates expanded), its
inline typography is replaced by the new design system's roles, and every chapter and appendix gets its own page in
both languages. The build ends with a content check that fails if any sentence of the classic edition is missing.
"""
import argparse
import colorsys
import copy
import datetime
import glob
import html as H
import json
import math
import os
import re
import shutil
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from convert import Converter, load, split_blocks, style_dict, style_str  # noqa: E402
import segments as SEG  # noqa: E402
from ui_ny import UI, PARTS, CHAPTERS, APPENDIX_LETTER  # noqa: E402
import scenes_ny as SC
import moments_ny as MOM

# the index shows small pictures: each is made once from the full image (a crop where the whole would show a face up close)
THUMB_CROP = {'11a-familien-ved-stenen.jpg': (555 / 1350, 1175 / 1800, 1175 / 1350, 1478 / 1800)}


def thumb(name, w=720):
    src = os.path.join(HERE, '..', 'billeder', name)
    base = os.path.splitext(os.path.basename(name))[0]
    dst = os.path.join(HERE, '..', 'assets', 'thumbs', base + '.jpg')
    if not os.path.exists(src):
        return None
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        from PIL import Image
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im = Image.open(src)
        im = im.convert('RGBA') if im.mode in ('P', 'LA') else im
        if im.mode == 'RGBA':
            bg = Image.new('RGB', im.size, (242, 235, 220)); bg.paste(im, mask=im.split()[3]); im = bg
        im = im.convert('RGB')
        c = THUMB_CROP.get(os.path.basename(name))
        if c:
            W, H = im.size
            im = im.crop((int(c[0] * W), int(c[1] * H), int(c[2] * W), int(c[3] * H)))
        if im.width > w:
            im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=80, optimize=True, progressive=True)
    return 'thumbs/' + base + '.jpg'


# chapters whose own text carries no picture wide enough for the index: a picture from the chronicle that belongs there
CARD_IMG = {'kap3': '34-havskib-fjord-1924.png', 'kap14': '02-husby-kirke-richardt.jpg', 'kap21': '11c-laengen-med-flag.jpg',
            'navnenoegle': '50-realregister-husby-fol53.jpg', 'stamtavle': '52-skoede-1876-thomas-jensen-silkjaer.jpg',
            'kilder': '61-laegdsrulle-1873-niels-thomsen.jpg', 'billeder': '06a-navneliste-vedersoe-1915.jpg'}
# pale drawings and documents are printed a little darker in the index, so they hold their own beside the photographs
CARD_LIFT = {'02-husby-kirke-richardt.jpg', '12-atlasblad-husby-1878.jpg', '50-realregister-husby-fol53.jpg', '52-skoede-1876-thomas-jensen-silkjaer.jpg',
             '61-laegdsrulle-1873-niels-thomsen.jpg', '06a-navneliste-vedersoe-1915.jpg', '53-skoede-1855-beliggende-i-silkjaer.png',
             '42-tfr-1944-forside.png', '39-kirkebog-1913-nr5.png', '63-politiprotokol-1913-s153.jpg', '30-korsoer-avis-1878-a.jpg'}  # noqa: E402
import typeset_ny as TS  # noqa: E402
import nav_ny as NAV  # noqa: E402

IMG = '@@IMG@@/'
_fuld_dir = os.path.join(HERE, '..', 'billeder', 'fuld')
HI_DIMS = json.load(open(os.path.join(HERE, 'hi_dims.json'), encoding='utf-8')) if os.path.exists(os.path.join(HERE, 'hi_dims.json')) else {}
FULD = set(os.listdir(_fuld_dir)) if os.path.isdir(_fuld_dir) else set(open(os.path.join(HERE, 'billeder_fuld.txt'), encoding='utf-8').read().split())
ASSET = '@@A@@/'
YEAR = re.compile(r'\b(1[6-9]\d\d|20[0-2]\d)\b')
PEOPLE_DA = {
    'people_kicker': 'Appendiks C · Personkort',
    'people_title': 'Personkortene',
    'people_intro': 'De brune navne i teksten åbner disse kort. Her står alle tyve samlet.',
    'sources_label': 'Kilder:',
}


def tag(soup, name, cls=None, **attrs):
    t = soup.new_tag(name)
    if cls:
        t['class'] = cls.split() if isinstance(cls, str) else cls
    for k, v in attrs.items():
        t[k.replace('_', '-')] = v
    return t


def head_text(el):
    c = copy.copy(el)
    for br in c.find_all('br'):
        br.replace_with(' ')
    return re.sub(r'\s+', ' ', c.get_text(' ', strip=True)).strip()


SLUG_STOP = {'og', 'i', 'paa', 'til', 'fra', 'af', 'en', 'et', 'den', 'det', 'de', 'med', 'som', 'for',
             'and', 'the', 'of', 'in', 'to', 'a', 'an', 'on', 'at', 'from', 'with'}


def slugify(s):
    s = s.lower()
    for a, b in (('æ', 'ae'), ('ø', 'oe'), ('å', 'aa'), ('é', 'e'), ('ü', 'u'), ('ö', 'oe'), ('’', ''), ("'", '')):
        s = s.replace(a, b)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    words, parts = [], s.split('-')
    for w in parts:
        if len('-'.join(words + [w])) > 48:
            break
        words.append(w)
    while len(words) < len(parts) and len(words) > 1 and words[-1] in SLUG_STOP:
        words.pop()
    return '-'.join(words)


def esc(s):
    return H.escape(s or '', quote=True)


# ---------------------------------------------------------------------------------------------- restyle
KEEP = {
    'display', 'grid-template-columns', 'grid-template-rows', 'grid-column', 'grid-row', 'grid-area', 'gap', 'row-gap',
    'column-gap', 'align-items', 'align-self', 'align-content', 'justify-content', 'justify-items', 'justify-self', 'flex',
    'flex-wrap', 'flex-direction', 'flex-basis', 'flex-shrink', 'flex-grow', 'flex-flow', 'order', 'position', 'inset',
    'top', 'left', 'right', 'bottom', 'width', 'max-width', 'min-width', 'height', 'max-height', 'min-height',
    'aspect-ratio', 'object-fit', 'object-position', 'overflow', 'overflow-x', 'overflow-y', 'margin', 'margin-top',
    'margin-bottom', 'margin-left', 'margin-right', 'margin-inline', 'margin-block', 'padding', 'padding-top',
    'padding-bottom', 'padding-left', 'padding-right', 'padding-inline', 'padding-block', 'text-align', 'white-space',
    'z-index', 'transform', 'transform-origin', 'font-style', 'vertical-align', 'list-style', 'columns', 'break-inside',
    'pointer-events', 'border-radius', 'clip-path', 'filter', 'opacity', 'box-sizing', 'float', 'clear', 'place-items',
    'place-content', 'overflow-wrap', 'word-break', 'hyphens', 'text-indent', 'counter-reset', 'counter-increment',
    'isolation', 'user-select', 'touch-action', 'visibility', 'scroll-snap-type', 'scroll-snap-align', 'grid-auto-flow',
    'grid-auto-rows', 'grid-auto-columns', 'image-rendering', 'cursor', 'list-style-type', 'text-underline-offset',
}
DARK_BG = ('#14181c', '#0f1317', '#1e1c18')


def parse_color(c):
    c = c.strip().lower()
    m = re.match(r'#([0-9a-f]{3,8})$', c)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = ''.join(x * 2 for x in h[:3])
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)), 1.0
    m = re.match(r'rgba?\(([^)]*)\)', c)
    if m:
        p = [x.strip() for x in m.group(1).split(',')]
        try:
            rgb = tuple(float(x) / 255 for x in p[:3])
            a = float(p[3]) if len(p) > 3 else 1.0
            return rgb, a
        except ValueError:
            return None
    return None


def color_role(c, dark):
    pc = parse_color(c)
    if not pc:
        return ''
    (r, g, b), a = pc
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s > .22 and .18 < l < .88:
        hue = h * 360
        if 170 <= hue <= 235:
            return 'c-sea'
        return 'c-acc'
    if dark:
        return '' if l >= .8 else ('c-mut' if l >= .58 else 'c-mut2')
    return '' if l <= .3 else ('c-mut' if l <= .47 else 'c-mut2')


def size_of(st):
    f = st.get('font', '')
    if f:
        for tok in f.split():
            m = re.match(r'(\d+(?:\.\d+)?)px', tok)
            if m:
                return float(m.group(1))
    fs = st.get('font-size', '')
    if fs:
        nums = [float(x) for x in re.findall(r'(\d+(?:\.\d+)?)px', fs)]
        if nums:
            return max(nums)
        m = re.match(r'(\d+(?:\.\d+)?)em', fs)
        if m:
            return None
    return None


def weight_of(st):
    w = st.get('font-weight')
    f = st.get('font', '')
    if not w and f:
        for tok in f.split():
            if re.match(r'^[1-9]00$', tok):
                w = tok
    try:
        return int(w) if w else None
    except ValueError:
        return {'bold': 600, 'normal': 400}.get(w)


def text_role(el, st):
    mono = 'var(--mono)' in st.get('font', '') or 'mono' in st.get('font-family', '').lower()
    size = size_of(st)
    upper = st.get('text-transform') == 'uppercase'
    cls = []
    if mono:
        if size is None:
            cls.append('m')
        elif size <= 9.5:
            cls.append('m-xs')
        elif size <= 10.5:
            cls.append('m-s')
        elif size <= 12.5:
            cls.append('m')
        else:
            cls.append('m-l')
        if upper:
            cls.append('uc')
        return cls
    if 'serif' in st.get('font-family', '') and not size:
        cls.append('serif')
    if size is None:
        if upper:
            cls.append('uc')
        return cls
    if el.name in ('h1', 'h2', 'h3', 'h4'):
        cls.append({'h1': 'h1', 'h2': 'h2' if size >= 30 else 'h2-s', 'h3': 'h3', 'h4': 'h3'}[el.name])
    elif size >= 44:
        cls.append('disp')
    elif size >= 34:
        cls.append('h-l')
    elif size >= 26:
        cls.append('h-m')
    elif size >= 21:
        cls.append('lead' if el.name in ('p', 'blockquote', 'figcaption') else 'h-s')
    elif size >= 19:
        cls.append('t-l')
    elif size >= 17:
        cls.append('t')
    elif size >= 15:
        cls.append('t-s')
    elif size >= 13:
        cls.append('t-xs')
    else:
        cls.append('t-xxs')
    if upper:
        cls.append('uc')
    return cls


def restyle(root, dark):
    """Replace inline typography, colour and surfaces with the design system's classes."""
    for el in root.find_all(True):
        if el.name in ('svg', 'path', 'circle', 'line', 'g', 'rect', 'text', 'polyline', 'polygon'):
            continue
        classes = [c for c in (el.get('class') or []) if not re.match(r'^hv\d+$', c)]
        st = dict(style_dict(el.get('style', '')))
        if not st:
            if classes != (el.get('class') or []):
                el['class'] = classes
            continue
        add = text_role(el, st)
        w = weight_of(st)
        if w:
            add.append('w3' if w <= 300 else ('w5' if w == 500 else ('w6' if w >= 600 else '')))
        col = st.get('color')
        if col and col != 'inherit':
            r = color_role(col, dark)
            if r:
                add.append(r)
        # surfaces and rules
        bg = st.get('background') or st.get('background-color')
        if bg and bg not in ('none', 'transparent', '0'):
            if 'gradient' in bg or 'url(' in bg:
                add.append('sf-grad')
            else:
                has_text = bool(el.get_text(strip=True))
                pc = parse_color(bg)
                if not has_text and el.name in ('span', 'div', 'i', 'b') and ('position' in st or 'height' in st or 'width' in st):
                    add.append('fill-' + (color_role(bg, dark) or 'c-line').replace('c-', ''))
                elif pc:
                    (r_, g_, b_), a = pc
                    l = colorsys.rgb_to_hls(r_, g_, b_)[1]
                    if dark:
                        add.append('sf' if (l > .5 and a > .5) else 'sf-d')
                    else:
                        add.append('sf2' if l < .86 else 'sf')
        for side, cl in (('border', 'bx'), ('border-left', 'bl'), ('border-top', 'bt'), ('border-bottom', 'bb'), ('border-right', 'br')):
            v = st.get(side)
            if not v or v.strip() in ('0', 'none', '0px'):
                continue
            m = re.match(r'(\d+(?:\.\d+)?)px', v.strip())
            wpx = float(m.group(1)) if m else 1
            dash = 'dashed' in v or 'dotted' in v
            k = cl + ('-d' if dash else '') + ('3' if wpx >= 3 else ('2' if wpx >= 2 else ''))
            if color_role(re.sub(r'^\S+\s+\S+\s+', '', v), dark) in ('c-acc', 'c-sea'):
                k += ' ' + cl + '-acc'
            add.extend(k.split())
        if st.get('box-shadow') and st['box-shadow'] != 'none':
            add.append('shd')
        keep = [(k, v) for k, v in st.items() if k in KEEP]
        if keep:
            el['style'] = style_str(keep)
        elif el.has_attr('style'):
            del el['style']
        out = classes + [c for c in add if c and c not in classes]
        if out:
            el['class'] = out
        elif el.has_attr('class'):
            del el['class']


# ---------------------------------------------------------------------------------------------- numbering
def number_maps(data):
    """The sources and caveats numbered afresh, 1, 2, 3 … in the order the catalogue gives them (a range like
    S22—S24 keeps its width). The classic edition keeps its own numbers; this edition closes the gaps."""
    nums = []
    for k in data['KILDER']:
        ends = [int(x[1:]) for x in k['id'].split('—')]
        nums.extend(range(ends[0], ends[-1] + 1))
    smap = {o: i + 1 for i, o in enumerate(nums)}
    cmap = {int(f['nr']): i + 1 for i, f in enumerate(data['FORBEHOLD'])}
    return smap, cmap


S_RX = re.compile(r'(?<![A-Za-z0-9])S(\d{1,3})(?!\d)')
CV_RX = re.compile(r'\b([Ff]orbehold(?:ene)?|[Cc]aveats?)(\s+)(\d{1,2}(?:(?:\s*,\s*|\s+(?:og|and)\s+|\s*[–—-]\s*)\d{1,2})*)(?!\d)')


def renumber_str(t, smap, cmap, bad=None):
    def s_(m):
        o = int(m.group(1))
        if o not in smap:
            if bad is not None:
                bad.add('S' + m.group(1))
            return m.group(0)
        return 'S' + str(smap[o])
    def c_(m):
        def one(mm):
            o = int(mm.group(0))
            if o not in cmap:
                if bad is not None:
                    bad.add('forbehold ' + mm.group(0))
                return mm.group(0)
            return f'{cmap[o]:02d}' if mm.group(0).startswith('0') else str(cmap[o])
        return m.group(1) + m.group(2) + re.sub(r'\d+', one, m.group(3))
    return CV_RX.sub(c_, S_RX.sub(s_, t))


# ---------------------------------------------------------------------------------------------- edition
GROUPS = [('kap1', 'kap2'), ('kap3', 'kap4'), ('kap14', 'kap15', 'kap16'), ('kap21', 'kap22')]


class Edition:
    def __init__(self, lang, o):
        self.lang = lang
        self.o = o
        self.ui = UI[lang]
        src, body = load(o.src)
        self.src = src
        self.data = json.load(open(os.path.join(HERE, 'data.da.json'), encoding='utf-8'))
        self.places = json.load(open(os.path.join(HERE, 'places.da.json'), encoding='utf-8'))
        self.map = json.load(open(os.path.join(HERE, 'map.json'), encoding='utf-8'))
        self.cv = Converter(self.data, img_base=IMG)
        self.soup = self.cv.run(body)
        self.blocks = split_blocks(self.soup)
        self.byid = {el.get('id'): el for k, el in self.blocks if isinstance(el, Tag) and el.get('id')}
        self.missing = []

    # ---- content additions shared with the immersive edition (so the translation table matches)
    def people_appendix(self):
        s = self.soup
        st = self.byid['stamtavle']
        inner = st.find('div')
        box = tag(s, 'div', 'people-wrap', id='personer')
        head = tag(s, 'div', 'people-head')
        k = tag(s, 'div', 'm-s uc c-acc kick')
        k.string = PEOPLE_DA['people_kicker']
        h = tag(s, 'h3', 'h-m')
        h.string = PEOPLE_DA['people_title']
        p = tag(s, 'p', 't-s c-mut')
        p.string = PEOPLE_DA['people_intro']
        head.extend([k, h, p])
        box.append(head)
        grid = tag(s, 'div', 'people')
        for key, pr in self.data['PERSONER'].items():
            art = tag(s, 'article', 'person', id=f'person-{key}')
            r = tag(s, 'p', 'person-role'); r.string = pr['rolle']
            n = tag(s, 'h3'); n.string = pr['navn']
            life = tag(s, 'p', 'person-life'); life.string = pr['leve']
            intro = tag(s, 'p', 'person-intro'); intro.string = pr['intro']
            art.extend([r, n, life, intro])
            dl = tag(s, 'dl')
            for f in pr.get('facts', []):
                dt = tag(s, 'dt'); dt.string = f['k']
                dd = tag(s, 'dd'); dd.string = f['v']
                dl.extend([dt, dd])
            art.append(dl)
            srcp = tag(s, 'p', 'person-src')
            lbl = tag(s, 'span'); lbl.string = PEOPLE_DA['sources_label']
            srcp.append(lbl)
            srcp.append(NavigableString(' ' + pr.get('kilder', '')))
            art.append(srcp)
            grid.append(art)
        box.append(grid)
        inner.append(box)

    def people_data(self):
        """The person cards as data, in this edition's language (for the family tree)."""
        out = {}
        for art in self.byid['stamtavle'].find_all('article', class_='person'):
            key = art['id'][len('person-'):]
            dts = art.find_all('dt')
            out[key] = {'navn': art.find('h3').get_text(' ', strip=True), 'rolle': art.find(class_='person-role').get_text(' ', strip=True),
                        'leve': art.find(class_='person-life').get_text(' ', strip=True),
                        'facts': [{'k': dt.get_text(' ', strip=True), 'v': dt.find_next_sibling('dd').get_text(' ', strip=True)} for dt in dts]}
        return out

    def mark_transcripts(self):
        """Stable ids on the transcript blocks of chapter 12 (same order in both languages)."""
        k12 = self.byid['kap12']
        n = 0
        for el in k12.find_all(['p', 'blockquote', 'li']):
            n += 1
            if not el.get('id'):
                el['id'] = f'k12-{n}'

    def translate(self):
        roots = [el for k, el in self.blocks if isinstance(el, Tag)]
        segs = []
        for r in roots:
            segs.extend(SEG.collect(r, self.soup))
        table = {}
        for fn in sorted(glob.glob(os.path.join(HERE, 'i18n', 'en', '*.json'))):
            table.update(json.load(open(fn, encoding='utf-8')))
        SEG.apply(segs, table, self.soup, self.missing)

    # ---- structure
    def kicker(self, sec):
        ks = sec.find_all(lambda t: t.name == 'div' and 'var(--mono)' in t.get('style', '') and t.get_text(strip=True))
        for k in ks:
            if re.match(r'(Kapitel|Appendiks|Chapter|Appendix)\b', k.get_text(' ', strip=True)):
                return k
        return ks[0] if ks else None

    def outline(self):
        """Parts, chapters and appendices in reading order, with their metadata."""
        self.parts, self.pages = [], []
        cur = None
        pi = 0
        for kind, el in self.blocks:
            if kind == 'part':
                meta = PARTS[pi]
                pi += 1
                divs = [d for d in el.find_all('div') if d.get_text(strip=True) and not d.find('div')]
                cur = {'id': meta['id'], 'num': meta['num'], 'img': meta['img'], 'pos': meta['pos'],
                       'kick': divs[0].get_text(' ', strip=True) if divs else '',
                       'title': divs[1].get_text(' ', strip=True) if len(divs) > 1 else '',
                       'range': divs[2].get_text(' ', strip=True) if len(divs) > 2 else '',
                       'el': el, 'items': []}
                self.parts.append(cur)
            elif kind == 'section' and el.get('id') in CHAPTERS:
                sid = el['id']
                k = self.kicker(el)
                h2 = el.find('h2')
                title = head_text(h2) if h2 else sid
                kick = k.get_text(' ', strip=True) if k else ''
                yrs = kick.split('·')[-1].strip() if '·' in kick else ''
                if not re.search(r'\d|i dag|today', yrs):
                    yrs = ''
                is_app = sid in APPENDIX_LETTER
                n = APPENDIX_LETTER[sid].upper() if is_app else re.sub(r'\D', '', sid)
                img = next((i for i in el.find_all('img') if i.get('alt') and i.get('aria-hidden') != 'true' and int(i.get('width') or 1000) >= 400), None)
                first_p = next((p for p in el.find_all('p') if len(p.get_text(strip=True)) > 90), None)
                words = len(el.get_text(' ').split())
                item = {'id': sid, 'n': n, 'is_app': is_app, 'title': title, 'kick': kick, 'years': yrs,
                        'img': img['src'].replace(IMG, '') if img else None, 'img_alt': img.get('alt', '') if img else '',
                        'desc': self.describe(first_p), 'minutes': max(1, round(words / 230)), 'el': el,
                        'part': cur['id'] if cur else None, 'meta': CHAPTERS[sid]}
                if sid in CARD_IMG:
                    item['img'], item['img_alt'] = CARD_IMG[sid], ''
                cur['items'].append(item)
                self.pages.append(item)
        # slugs and paths
        for it in self.pages:
            base = f"{int(it['n']):02d}" if not it['is_app'] else it['n'].lower()
            it['slug'] = base + '-' + slugify(it['title'])
            if self.lang == 'da':
                it['path'] = ('appendiks/' if it['is_app'] else 'kapitel/') + it['slug'] + '/index.html'
            else:
                it['path'] = 'en/' + ('appendix/' if it['is_app'] else 'chapter/') + it['slug'] + '/index.html'
        # short chapters share a page: the page takes the address of its first chapter, the others become sections
        # of it and their own addresses lead on to their place on it
        by = {it['id']: it for it in self.pages}
        for it in self.pages:
            it['href'] = it['path']
        for g in GROUPS:
            if not all(k in by for k in g):
                continue
            host = by[g[0]]
            host['group'] = [by[k] for k in g]
            for k in g[1:]:
                m = by[k]
                m['host'] = host
                m['old_path'] = m['path']
                m['path'] = host['path']
                m['href'] = host['path'] + '#' + k
        self.reading = [it for it in self.pages if 'host' not in it]
        self.cover_path = 'index.html' if self.lang == 'da' else 'en/index.html'
        self.print_path = 'print/index.html' if self.lang == 'da' else 'en/print/index.html'

    def describe(self, p):
        if p is None:
            return self.ui['description']
        t = re.sub(r'\s+', ' ', p.get_text(' ', strip=True))
        t = re.sub(r'\s*\[S[^\]]*\]', '', t)
        if len(t) <= 158:
            return t
        cut = t[:156]
        cut = cut[:cut.rfind(' ')]
        return cut.rstrip(',;:—– ') + ' …'

    # ---- sources and caveats numbered without gaps (after the translation: its table is keyed on the classic's text)
    def renumber(self):
        smap, cmap = number_maps(self.data)
        self.bad_numbers = set()
        for t in list(self.soup.find_all(string=True)):
            if t.find_parent(['script', 'style']):
                continue
            new = renumber_str(str(t), smap, cmap, self.bad_numbers)
            if new != str(t):
                t.replace_with(NavigableString(new))
        for el in self.soup.find_all(True):
            for at in ('href', 'id', 'data-s'):
                v = el.get(at)
                if isinstance(v, str) and S_RX.search(v):
                    el[at] = S_RX.sub(lambda m: 'S' + str(smap.get(int(m.group(1)), m.group(1))), v)
        # the number printed on each caveat in the catalogue
        k = self.byid['kilder']
        for d in k.find_all('div'):
            t = d.get_text(strip=True)
            if re.fullmatch(r'\d\d', t) and d.parent and d.parent.name == 'div' and not d.find('div') and len(d.parent.get_text()) > 60 and int(t) in cmap:
                d.string = f'{cmap[int(t)]:02d}'

    def link_caveats(self):
        """»Se forbehold 12« / »see caveat 12« leads to caveat 12 in the catalogue."""
        s = self.soup
        for t in list(s.find_all(string=CV_RX)):
            if t.find_parent(['a', 'script', 'style', 'button']):
                continue
            txt, pos, parts = str(t), 0, []
            for m in CV_RX.finditer(txt):
                parts.append(NavigableString(txt[pos:m.start()]))
                ns = list(re.finditer(r'\d+', m.group(3)))
                if len(ns) == 1:
                    a = tag(s, 'a', 'cvref', href=f'#forbehold-{int(ns[0].group(0)):02d}')
                    a.string = m.group(0)
                    parts.append(a)
                else:
                    parts.append(NavigableString(m.group(1) + m.group(2)))
                    q = 0
                    for n in ns:
                        parts.append(NavigableString(m.group(3)[q:n.start()]))
                        a = tag(s, 'a', 'cvref', href=f'#forbehold-{int(n.group(0)):02d}')
                        a.string = n.group(0)
                        parts.append(a)
                        q = n.end()
                    parts.append(NavigableString(m.group(3)[q:]))
                pos = m.end()
            parts.append(NavigableString(txt[pos:]))
            for p_ in parts:
                t.insert_before(p_)
            t.extract()

    # ---- post-translation transformations
    def post(self):
        s = self.soup
        self.renumber()
        # darkness of each section for the colour roles
        for kind, el in self.blocks:
            if not isinstance(el, Tag):
                continue
            st = dict(style_dict(el.get('style', '')))
            dark = (st.get('background', '') in DARK_BG) or kind == 'footer' or kind == 'header'
            if el.get('id') in CHAPTERS:
                w = CHAPTERS[el['id']]['world']
                dark = w in ('sea', 'storm', 'archive', 'night')
            restyle(el, dark)
            if el.has_attr('style'):
                keep = [(k, v) for k, v in style_dict(el['style']) if k not in ('padding', 'position', 'background', 'color')]
                if keep:
                    el['style'] = style_str(keep)
                else:
                    del el['style']
        # every chapter re-typeset as one flat sequence of blocks on the book grid
        for it in self.pages:
            TS.typeset(self, it)
        # a »+« that opens a few lines inside a paragraph is a note like the others (a <details> cannot live in a <p>)
        for k, det in enumerate(s.select('details.more')):
            sm = det.find('summary')
            if sm is None or sm.get_text(strip=True) != '+':
                continue
            nid = f'nm{k + 1}'
            btn = s.new_tag('button', attrs={'type': 'button', 'class': 'q', 'data-kind': 'more', 'aria-controls': nid, 'aria-expanded': 'false',
                                             'aria-label': 'Læs mere' if self.lang == 'da' else 'Read more'})
            btn.string = '+'
            note = s.new_tag('span', attrs={'class': 'note t-s sn', 'id': nid, 'role': 'note'})
            kids = [c for c in det.children if c is not sm and not (isinstance(c, NavigableString) and not c.strip())]
            if len(kids) == 1 and isinstance(kids[0], Tag) and kids[0].name == 'span':
                kids = list(kids[0].children)
            for c in kids:
                note.append(c.extract())
            det.replace_with(btn)
            btn.insert_after(note)
        # content images: zoom into the full-size copy where one exists
        for img in s.find_all('img'):
            if not img.has_attr('data-fuld'):
                continue
            name = img.get('src', '').replace(IMG, '')
            box = img.parent
            if img.get('aria-hidden') == 'true' or img.find_parent('a') or (box and box.find('img', attrs={'data-fade': True})):
                del img['data-fuld']
                continue
            base = os.path.splitext(name)[0]
            if name in FULD:
                img['data-fuld'] = IMG + 'fuld/' + name
            else:
                del img['data-fuld']
            img['data-zoom'] = ''
            if name in HI_DIMS:
                # a sharper copy, loaded only when the camera goes closer than this picture can carry
                img['data-hi'] = ASSET + 'hi/' + base + '.jpg'
                img['data-fw'] = str(HI_DIMS[name][0])
        # dated headings drive the year odometer
        for it in self.pages:
            for h in it['el'].find_all(['h3', 'h4']) + it['el'].find_all(class_=['h-s', 'h-m']):
                if h.get('data-y') or h.find_parent(['figure', 'details', 'table', 'figcaption']) or h.find_parent(class_=['note', 'person', 'people-wrap']):
                    continue
                t = h.get_text(' ', strip=True)
                m = YEAR.search(t)
                if not m:
                    prev = h.find_previous_sibling()
                    pt = prev.get_text(' ', strip=True) if prev is not None else ''
                    m = YEAR.search(pt) if len(pt) < 60 else None
                if m and len(t) < 110:
                    h['data-y'] = m.group(1)
        # a dated section head shows its year in the margin
        for it in self.pages:
            for b in it['el'].find_all(class_='b-h'):
                y = b.get('data-y') or next((x['data-y'] for x in b.find_all(attrs={'data-y': True})), None)
                if y:
                    b['data-y'] = y
        # source references [S12] -> links, and anchors in the catalogue
        self.link_sources()
        self.anchor_catalogue()
        if self.lang == 'en':
            self.link_omissions()
        self.link_caveats()
        SC.apply(self)

    def kicker_after(self, sec):
        for d in sec.find_all('div'):
            t = d.get_text(' ', strip=True)
            if re.match(r'(Kapitel|Appendiks|Chapter|Appendix)\b', t) and not d.find('div') and len(t) < 90:
                return d
        return None

    def link_sources(self):
        s = self.soup
        rx = re.compile(r'\[((?:S\d+(?:\s*[—–-]\s*S\d+)?)(?:\s*,\s*S\d+(?:\s*[—–-]\s*S\d+)?)*)\]')
        for t in list(s.find_all(string=rx)):
            if t.find_parent(['a', 'script', 'style', 'button']):
                continue
            parent = t.parent
            txt = str(t)
            parts = []
            pos = 0
            for m in rx.finditer(txt):
                parts.append(NavigableString(txt[pos:m.start()]))
                inner = m.group(1)
                span = tag(s, 'span', 'srefs')
                span.append(NavigableString('['))
                p2 = 0
                for mm in re.finditer(r'S\d+', inner):
                    span.append(NavigableString(inner[p2:mm.start()]))
                    a = tag(s, 'a', 'sref', href='#' + mm.group(0))
                    a['data-s'] = mm.group(0)
                    a.string = mm.group(0)
                    span.append(a)
                    p2 = mm.end()
                span.append(NavigableString(inner[p2:] + ']'))
                parts.append(span)
                pos = m.end()
            parts.append(NavigableString(txt[pos:]))
            for p in parts:
                t.insert_before(p)
            t.extract()

    def anchor_catalogue(self):
        k = self.byid['kilder']
        for sp in k.find_all('span'):
            t = sp.get_text(strip=True)
            if re.fullmatch(r'S\d+(—S\d+)?', t) and sp.parent and sp.parent.name == 'div':
                row = sp.parent
                sid = t.split('—')[0]
                if not row.get('id'):
                    row['id'] = sid
                    row['class'] = (row.get('class') or []) + ['src-row']
                if '—' in t:
                    a, b = t.split('—')
                    for n in range(int(a[1:]) + 1, int(b[1:]) + 1):
                        alias = tag(self.soup, 'span', 'alias', id=f'S{n}')
                        row.insert(0, alias)
        for d in k.find_all('div'):
            t = d.get_text(strip=True)
            if re.fullmatch(r'\d\d', t) and d.parent and d.parent.name == 'div' and not d.find('div'):
                box = d.parent
                if not box.get('id') and len(box.get_text()) > 60:
                    box['id'] = 'forbehold-' + t
                    box['class'] = (box.get('class') or []) + ['caveat']

    def link_omissions(self):
        """English only: every bracketed omission in the court records links to the same place in Danish."""
        rx = re.compile(r'\[[^\[\]]*(?:not translated|rather than translated)[^\[\]]*\]')
        da_page = next(it for it in self.pages if it['id'] == 'kap12')
        self.omission_links = []
        for t in list(self.soup.find_all(string=rx)):
            blk = t.find_parent(lambda x: isinstance(x, Tag) and x.get('id', '').startswith('k12-')) or t.find_parent(id=True)
            anchor = blk.get('id') if blk else 'kap12'
            txt = str(t)
            parts, pos = [], 0
            for m in rx.finditer(txt):
                parts.append(NavigableString(txt[pos:m.start()]))
                sp = tag(self.soup, 'span', 'omit')
                sp.append(NavigableString(m.group(0)))
                a = tag(self.soup, 'a', 'omit-link', href='@@DA12@@#' + anchor, hreflang='da', lang='da')
                a.string = self.ui['danish_original']
                sp.append(NavigableString(' '))
                sp.append(a)
                parts.append(sp)
                pos = m.end()
                self.omission_links.append(anchor)
            parts.append(NavigableString(txt[pos:]))
            for p in parts:
                t.insert_before(p)
            t.extract()


# ---------------------------------------------------------------------------------------------- pages
class Site:
    def __init__(self, o):
        self.o = o
        self.ed = {}
        for lang in ('da', 'en'):
            e = Edition(lang, o)
            e.people_appendix()
            e.mark_transcripts()
            if lang == 'en':
                e.translate()
            e.outline()
            e.data_people = e.people_data()
            e.post()
            self.ed[lang] = e
            if e.bad_numbers:
                print(f'warning ({lang}): numbers not in the catalogue: ' + ', '.join(sorted(e.bad_numbers)))
        self.today = datetime.date.today().isoformat()

    # ---- paths
    def rel(self, frm, to):
        """Relative URL from page frm to page to (both within the edition), keeping trailing index.html out."""
        fd = os.path.dirname(frm) or '.'
        if getattr(self.o, 'explicit', False) and to.endswith('index.html'):
            return os.path.relpath(to, fd)
        t = to[:-len('index.html')] if to.endswith('index.html') else to
        r = os.path.relpath(t or '.', fd)
        if t.endswith('/') or t == '':
            r = (r if r != '.' else '.') + '/'
            r = r.replace('//', '/')
        return r if r != './' else './'

    def site_rel(self, frm, site_path):
        """Relative URL from page frm to a path at the site root (billeder/ …)."""
        page_site = os.path.join(self.o.site_prefix, frm)
        return os.path.relpath(site_path, os.path.dirname(page_site) or '.') + ('/' if site_path.endswith('/') else '')

    def url(self, path):
        base = self.o.base.rstrip('/') + '/' + ('' if self.o.release else getattr(self.o, 'url_prefix', self.o.site_prefix))
        return base + (path[:-len('index.html')] if path.endswith('index.html') else path)

    # ---- chrome
    def head(self, e, path, title, desc, other_path, ld, img=None, extra=''):
        u = e.ui
        L = e.lang
        robots = '<meta name="robots" content="index, follow, max-image-preview:large">' if self.o.release else '<meta name="robots" content="noindex, follow">'
        og_img = self.url(('assets/og-silkjaer-da.jpg' if L == 'da' else 'assets/og-silkjaer-en.jpg'))
        a = self.rel(path, 'assets/')
        pre = ''.join(f'<link rel="preload" href="{a}fonts/{f}" as="font" type="font/woff2" crossorigin>' for f in ('source-serif-4-latin-opsz-normal.woff2', 'besley-latin-wght-normal.woff2'))
        return f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="Thomas Silkjær">
{robots}
<meta name="theme-color" content="#0e1619">
<link rel="canonical" href="{self.url(path)}">
<link rel="alternate" hreflang="{L}" href="{self.url(path)}">
<link rel="alternate" hreflang="{'en' if L == 'da' else 'da'}" href="{self.url(other_path)}">
<link rel="alternate" hreflang="x-default" href="{self.url(path if L == 'da' else other_path)}">
<meta property="og:type" content="{'book' if path in ('index.html', 'en/index.html') else 'article'}">
<meta property="og:site_name" content="{esc(u['site'])}">
<meta property="og:locale" content="{'da_DK' if L == 'da' else 'en_GB'}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{self.url(path)}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(u['og_alt'])}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{a}favicon.svg" type="image/svg+xml">
{pre}
<link rel="stylesheet" href="{a}ny.css">
<script>document.documentElement.classList.add('js');try{{if(matchMedia('(prefers-reduced-motion: reduce)').matches)document.documentElement.classList.add('rm')}}catch(e){{}}</script>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{extra}'''

    def topbar(self, e, path, other_path, crumb='', it=None):
        u = e.ui
        other = 'en' if e.lang == 'da' else 'da'
        return f'''<a class="skip" href="#main">{esc(u['skip'])}</a>
<header class="top" role="banner">
  <a class="brand" href="{self.rel(path, e.cover_path)}" data-nav>Silkjær</a>
  <div class="crumb" aria-hidden="true">{crumb}</div>
  {NAV.rail(e, it)}
  <div class="tools">
    <button type="button" class="tool t-sound" aria-pressed="false" data-act="sound" title="{esc(u['sound_title'])}"><i class="eq" aria-hidden="true"><b></b><b></b><b></b><b></b></i><span class="lbl">{esc(u['sound'])}</span></button>
    <a class="tool t-lang" href="{self.rel(path, other_path)}" hreflang="{other}" lang="{other}" data-lang-link title="{esc(u['other_lang_long'])}">{esc(u['other_lang'])}</a>
    <button type="button" class="tool t-print" data-act="print" aria-expanded="false" aria-controls="printmenu" title="{esc(u['print_title'])}"><span class="lbl">{esc(u['print'])}</span></button>
    <button type="button" class="tool t-menu" aria-expanded="false" aria-controls="menu" data-act="menu"><span class="lbl">{esc(u['contents'])}</span><i class="burger" aria-hidden="true"></i></button>
  </div>
  <div class="printmenu" id="printmenu" hidden>
    <button type="button" data-act="print-now">{esc(u['print_chapter'])}</button>
    <a href="{self.rel(path, e.print_path)}">{esc(u['print_book'])}</a>
  </div>
  <div class="prog" aria-hidden="true"><i></i></div>
</header>'''

    def menu(self, e, path):
        u = e.ui
        rows = []
        for p in e.parts:
            cur = ' aria-current="page"'
            items = ''.join(
                f'<li><a href="{self.rel(path, it["path"])}{"#" + it["id"] if it.get("host") else ""}"{cur if it["path"] == path and not it.get("host") else ""}><span class="n">{esc(it["n"])}</span><span class="t">{esc(it["title"])}</span><span class="y">{esc(it["years"])}</span></a></li>'
                for it in p['items'])
            rows.append(f'<li class="mpart"><div class="mh"><span>{esc(p["kick"])}</span> {esc(p["title"])}</div><ol>{items}</ol></li>')
        tabs = [('tl', u['timeline']), ('ft', u['family']), ('ch', u['chapters'])]
        tabbar = ''.join(f'<button type="button" role="tab" id="mt-{k}" aria-controls="mp-{k}" aria-selected="{"true" if i == 0 else "false"}" data-tab="{k}">{esc(t)}</button>' for i, (k, t) in enumerate(tabs))
        return f'''<nav class="menu" id="menu" aria-label="{esc(u['contents'])}" hidden>
  <div class="menu-in">
    <div class="menu-head"><a class="menu-cover" href="{self.rel(path, e.cover_path)}">{esc(u['site'])}</a><div class="menu-tabs" role="tablist">{tabbar}</div></div>
    <section class="mpanel" id="mp-tl" role="tabpanel" aria-labelledby="mt-tl"><h2 class="mp-t">{esc(u['timeline_title'])}</h2>{NAV.timeline(self, e, path, path)}</section>
    <section class="mpanel" id="mp-ft" role="tabpanel" aria-labelledby="mt-ft" hidden><h2 class="mp-t">{esc(u['family_title'])}</h2>{NAV.family(self, e, path)}</section>
    <section class="mpanel" id="mp-ch" role="tabpanel" aria-labelledby="mt-ch" hidden><h2 class="mp-t">{esc(u['contents_title'])}</h2><ol class="menu-parts">{''.join(rows)}</ol></section>
  </div>
  <button type="button" class="tool menu-close" data-close>{esc(u['close'])}</button>
</nav>'''

    def colophon(self, e, path, full=True):
        foot = next(el for k, el in e.blocks if k == 'footer')
        other = 'en' if e.lang == 'da' else 'da'
        if full:
            inner = ''.join(str(c) for c in foot.contents)
        else:
            ps = [c for c in foot.find_all(['p', 'div']) if c.get_text(strip=True)]
            inner = ''
        note = f'<p class="t-xs c-mut tnote">{esc(e.ui["translation_note"])}</p>' if e.lang == 'en' and full else ''
        return f'<footer class="colo w-sea" data-world="sea">{inner}{note}<div class="colo-line m-s uc"><a href="{self.rel(path, e.cover_path)}">{esc(e.ui["site"])}</a><span>·</span><a href="{self.rel(path, e.print_path)}">{esc(e.ui["book_page"])}</a></div></footer>'

    def dialogs(self, e):
        u = e.ui
        return f'''<div class="drawer" id="drawer" role="dialog" aria-modal="true" aria-label="{esc(u['person_card'])}" hidden><div class="scrim" data-close></div><div class="drawer-panel"><button type="button" class="tool dclose" data-close>{esc(u['close'])}</button><div class="drawer-body"></div></div></div>
<div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="{esc(u['image'])}" hidden><div class="lb-stage"><img alt="" draggable="false"></div><div class="lb-bar"><div class="lb-nav"><button type="button" class="tool lb-go" data-lb="-1" aria-label="{esc(u['prev'])}">←</button><span class="lb-n" aria-live="polite"></span><button type="button" class="tool lb-go" data-lb="1" aria-label="{esc(u['next'])}">→</button></div><div class="lb-cap"></div><div class="lb-hint">{esc(u['zoom_hint'])}</div></div><button type="button" class="tool lb-close" data-close>{esc(u['close'])}</button></div>
<div class="pop" id="pop" role="dialog" aria-label="{esc(u['source'])}" hidden><div class="pop-body"></div><a class="pop-more m-s uc" href="#">{esc(u['source_all'])} →</a></div>'''

    def defs(self):
        M = self.ed['da'].map
        land = ''.join(f'<path d="{d}"/>' for n, d in M['land'].items())
        return f'''<svg class="defs" width="0" height="0" aria-hidden="true" focusable="false"><defs><g id="silk-land">{land}</g></defs></svg>'''

    def page_data(self, e):
        places = {k: {'xy': self.ed['da'].map['pts'][k], 'n': (SC.PLACES_EN.get(k, (p['navn'], p['note']))[0] if e.lang == 'en' else p['navn']), 'd': (SC.PLACES_EN.get(k, (p['navn'], p['note']))[1] if e.lang == 'en' else p['note'])} for k, p in e.places.items()}
        ui = {k: e.ui.get(k, '') for k in ('sound_on', 'sound_off', 'hush_title', 'overlay_on', 'overlay_off', 'loading', 'person_all')}
        return (f'<script type="application/json" id="silk-places">{json.dumps(places, ensure_ascii=False)}</script>'
                f'<script type="application/json" id="silk-ui">{json.dumps(ui, ensure_ascii=False)}</script>')

    def da_links(self, path, html):
        """Each »Read this passage in the Danish original« leads to the Danish page that holds the same block."""
        da12 = next(it for it in self.ed['da'].pages if it['id'] == 'kap12')
        def one(m):
            return self.rel(path, self.idmap['da'].get(m.group(1), da12['path'])) + '#' + m.group(1)
        html = re.sub(r'@@DA12@@#([\w-]+)', one, html)
        return html.replace('@@DA12@@', self.rel(path, da12['path']))

    # ---- fix links in a page's html
    def fix(self, e, path, html):
        a = self.rel(path, 'assets/')
        html = html.replace(IMG, self.site_rel(path, 'billeder/'))
        html = html.replace(ASSET, a)
        if e.lang == 'en':
            html = self.da_links(path, html)
        soup = BeautifulSoup(html, 'html.parser')
        idpage = self.idmap[e.lang]
        for el in soup.find_all('a', href=True):
            h = el['href']
            if not h.startswith('#') or len(h) < 2:
                continue
            tid = h[1:]
            if tid in ('main', 'top'):
                continue
            target = idpage.get(tid)
            if target is None:
                continue
            if target == path:
                continue
            chap = next((it for it in e.pages if it['id'] == tid), None)
            if chap is not None:
                el['href'] = self.rel(path, chap['path']) + ('#' + tid if chap.get('host') else '')
            else:
                el['href'] = self.rel(path, target) + '#' + tid
        return str(soup)

    def build_idmap(self):
        self.idmap = {}
        for L, e in self.ed.items():
            m = {}
            for it in e.pages:
                for x in it['el'].find_all(id=True):
                    m.setdefault(x['id'], it['path'])
                m[it['id']] = it['path']
            for p in e.parts:
                m[p['id']] = next((it['path'] for it in p['items']), e.cover_path)
            m['intro'] = e.cover_path
            m['kilder'] = next(it['path'] for it in e.pages if it['id'] == 'kilder')
            self.idmap[L] = m

    # ---- page kinds
    def ld_chapter(self, e, it):
        book = self.url(e.cover_path) + '#book'
        return {'@context': 'https://schema.org', '@type': 'Chapter', 'name': it['title'], 'headline': it['title'],
                'position': it['n'], 'inLanguage': e.lang, 'url': self.url(it['path']), 'description': it['desc'],
                'isPartOf': {'@type': 'Book', '@id': book, 'name': e.ui['site']},
                'author': {'@type': 'Person', 'name': 'Thomas Silkjær'},
                **({'image': self.url_img(it['img'])} if it['img'] else {})}

    def url_img(self, name):
        return self.o.base.rstrip('/') + '/billeder/' + name

    def part_opener(self, e, it, path):
        p = next(p for p in e.parts if p['id'] == it['part'])
        if p['items'][0] is not it:
            return ''
        img = self.site_rel(path, 'billeder/') + p['img']
        return f'''<section class="part w-sea" data-world="sea" data-scene="part" id="{p['id']}" aria-labelledby="{p['id']}-t">
  <div class="part-bg" aria-hidden="true"><img src="{img}" alt="" style="object-position:{p['pos']}" decoding="async"></div>
  <div class="part-in">
    <div class="part-num" aria-hidden="true">{esc(p['num'])}</div>
    <div class="m-s uc part-k">{esc(p['kick'])}</div>
    <h2 class="part-t" id="{p['id']}-t">{esc(p['title'])}</h2>
    <div class="m-s uc part-r">{esc(p['range'])}</div>
  </div>
</section>'''

    def page_label(self, e, it):
        g = it.get('group')
        if g:
            return f'{e.ui["chapters_short"]} {g[0]["n"]}—{g[-1]["n"]}', ' · '.join(x['title'] for x in g)
        return f'{e.ui["appendix"] if it["is_app"] else e.ui["chapter"]} {it["n"]}', it['title']

    def nextprev(self, e, it, path):
        R = e.reading
        i = R.index(it)
        out = []
        for d, j in (('prev', i - 1), ('next', i + 1)):
            if 0 <= j < len(R):
                o = R[j]
                oimg = o['img'] or next((x['img'] for x in o.get('group', []) if x['img']), None)
                th = thumb(oimg) if oimg else None
                img = (f'<img src="{ASSET}{th}" alt="" loading="lazy" decoding="async">' if th else f'<img src="{self.site_rel(path, "billeder/")}{oimg}" alt="" loading="lazy" decoding="async">') if oimg else ''
                lab, ttl = self.page_label(e, o)
                yrs = o['years'] if not o.get('group') else ' — '.join(filter(None, [o['group'][0]['years'].split('—')[0].strip(), o['group'][-1]['years'].split('—')[-1].strip()]))
                out.append(f'<a class="np np-{d}" href="{self.rel(path, o["path"])}" rel="{d}"><span class="np-img">{img}</span><span class="np-txt"><span class="m-s uc">{esc(e.ui[d])} · {esc(lab)}</span><span class="np-t">{esc(ttl)}</span><span class="m-s c-mut">{esc(yrs)}</span></span></a>')
        return f'<nav class="nextprev" aria-label="{esc(e.ui["contents"])}">{"".join(out)}</nav>'

    def chapter_page(self, e, it):
        path = it['path']
        other = self.ed['en' if e.lang == 'da' else 'da']
        oit = next(x for x in other.pages if x['id'] == it['id'])
        lab, ttl = self.page_label(e, it)
        title = f'{lab}: {ttl} — {e.ui["site"]}'
        world = it['meta']['world']
        members = it.get('group') or [it]
        arts = []
        for m in members:
            ml = f'{e.ui["appendix"] if m["is_app"] else e.ui["chapter"]} {m["n"]}'
            arts.append(f'<article class="chap w-{m["meta"]["world"]}" data-world="{m["meta"]["world"]}" data-mins="{m["minutes"]}" data-cn="{esc(ml)}" data-ct="{esc(m["title"])}" data-amb="{m["meta"]["amb"]}">\n{m["el"]}\n</article>')
        body = '\n'.join(arts)
        first = members[0]
        crumb = f'<span class="n">{esc(e.ui["appendix"] if first["is_app"] else e.ui["chapter"])} {esc(first["n"])}</span><span class="t">{esc(first["title"])}</span>'
        R = e.reading
        i = R.index(it)
        nxt = R[i + 1] if i + 1 < len(R) else None
        extra = f'<link rel="prefetch" href="{self.rel(path, nxt["path"])}">' if nxt else ''
        spans = [CHAPTERS[m['id']].get('span') for m in members if CHAPTERS[m['id']].get('span')]
        a_, b_ = (min(x[0] for x in spans), max(x[1] for x in spans)) if spans else ('', '')
        html = f'''<!DOCTYPE html>
<html lang="{e.lang}" data-world="{world}">
<head>
{self.head(e, path, title, it['desc'], oit['path'], self.ld_chapter(e, it), extra=extra)}
</head>
<body data-page="{it['id']}" data-amb="{it['meta']['amb']}" data-y="{it['meta'].get('y', '')}" data-span="{a_} {b_}">
{self.topbar(e, path, oit['path'], crumb, it)}
{self.menu(e, path)}
<main id="main" data-world="{world}">
{self.part_opener(e, it, path)}
<div class="chaps">
{body}
</div>
{self.nextprev(e, it, path)}
</main>
{self.colophon(e, path)}
{self.defs()}
{self.dialogs(e)}
{self.page_data(e)}
<script src="{self.rel(path, 'assets/')}ny.js" defer></script>
</body>
</html>
'''
        return path, self.fix(e, path, html)

    def forward_page(self, e, it):
        """The address a chapter had before it shared a page: it leads on to its place on the page."""
        path = it['old_path']
        to = self.rel(path, it['path']) + '#' + it['id']
        canon = self.url(it['path']) + '#' + it['id']
        return path, f'''<!DOCTYPE html>
<html lang="{e.lang}"><head><meta charset="utf-8"><title>{esc(it['title'])} — {esc(e.ui['site'])}</title>
<meta name="robots" content="noindex"><link rel="canonical" href="{canon}">
<meta http-equiv="refresh" content="0; url={to}"><script>location.replace({json.dumps(to)} + '')</script></head>
<body><p><a href="{to}">{esc(it['title'])}</a></p></body></html>
'''

    def legacy_links(self, e, path):
        """The classic edition was one page with an anchor per chapter (/#kap5, /#kilder …): on the Danish cover those
        old links lead on to the chapter's own page."""
        if e.lang != 'da':
            return ''
        m = {it['id']: (self.rel(path, it['host']['path']) + '#' + it['id']) if it.get('host') else self.rel(path, it['path'])
             for it in e.pages}
        return ('\n<script>(function(){var m=' + json.dumps(m, separators=(',', ':'), ensure_ascii=False)
                + ',h=location.hash.slice(1);if(m.hasOwnProperty(h))location.replace(m[h])})()</script>')

    def cover_page(self, e):
        path = e.cover_path
        other = self.ed['en' if e.lang == 'da' else 'da']
        header = next(el for k, el in e.blocks if k == 'header')
        intro = e.byid['intro']
        imgp = self.site_rel(path, 'billeder/')
        # title block from the classic header (text kept verbatim)
        content = header.find('div', class_=False, style=re.compile('max-width')) or header
        kids = [c for c in header.find_all(recursive=True) if isinstance(c, Tag)]
        h1 = header.find('h1')
        kick = h1.find_previous_sibling('div') if h1 else None
        sub = h1.find_next_sibling('p') if h1 else None
        by = sub.find_next_sibling('div') if sub else None
        stats = by.find_next_sibling('div') if by else None
        parts = []
        for p in e.parts:
            cards = []
            for it in p['items']:
                th = thumb(it['img'], 1000 if len(p['items']) in (2, 7) else 640) if it['img'] else None
                lift = ' class="lift"' if it['img'] in CARD_LIFT else ''
                img = (f'<img src="{ASSET}{th}" alt=""{lift} loading="lazy" decoding="async">' if th else f'<img src="{imgp}{it["img"]}" alt=""{lift} loading="lazy" decoding="async">') if it['img'] else ''
                lab = f'{e.ui["appendix"] if it["is_app"] else e.ui["chapter"]} {it["n"]}'
                cards.append(f'<li><a class="card" href="{self.rel(path, it["path"])}{"#" + it["id"] if it.get("host") else ""}"><span class="card-img">{img}</span><span class="card-n" aria-hidden="true">{esc(it["n"])}</span><span class="m-s uc c-mut">{esc(lab)}{(" · " + esc(it["years"])) if it["years"] else ""}</span><span class="card-t">{esc(it["title"])}</span><span class="m-xs uc c-mut2">{it["minutes"]} {esc(e.ui["minutes"])}</span></a></li>')
            parts.append(f'<section class="toc-part" aria-labelledby="toc-{p["id"]}"><div class="toc-head"><div class="toc-num" aria-hidden="true">{esc(p["num"])}</div><div><div class="m-s uc c-acc">{esc(p["kick"])} · {esc(p["range"])}</div><h2 class="h-m" id="toc-{p["id"]}">{esc(p["title"])}</h2></div></div><ol class="cards n{len(cards)}">{"".join(cards)}</ol></section>')
        reading = ''
        if e.lang == 'en':
            ps = ''.join(f'<p>{esc(x)}</p>' for x in e.ui['reading_card'])
            reading = f'<aside class="reading w-paper"><div class="m-s uc c-acc">{esc(e.ui["site"])}</div><h2 class="h-m">{esc(e.ui["reading_card_title"])}</h2>{ps}</aside>'
        first = e.pages[0]
        ld = {'@context': 'https://schema.org', '@graph': [
            {'@type': ['Book', 'CreativeWork'], '@id': self.url(path) + '#book', 'name': e.ui['site'], 'headline': e.ui['title'],
             'description': e.ui['description'], 'inLanguage': e.lang, 'url': self.url(path), 'genre': e.ui['genre'],
             'author': {'@type': 'Person', 'name': 'Thomas Silkjær'}, 'dateModified': self.today, 'image': self.url_img('07-silkjaer-luftfoto.jpg'),
             ('translationOfWork' if e.lang == 'en' else 'workTranslation'): {'@id': self.url(other.cover_path) + '#book'},
             'hasPart': [{'@type': 'Chapter', 'name': it['title'], 'position': it['n'], 'url': self.url(it['href'])} for it in e.pages]},
        ]}
        # the intro, taken apart for the cover: its first three lines become the prologue, its main line a section
        intro_c = copy.copy(intro)
        divs = [c for c in intro_c.find_all('div', recursive=False)]
        first_div = divs[0] if divs else intro_c
        ps = [c for c in first_div.find_all('p', recursive=False)]
        pro = ps[:3]
        for x in pro:
            x.extract()
            x['class'] = ['pro-l']
            if x.has_attr('style'):
                del x['style']
        rest = first_div.decode_contents()
        mainline = divs[1].decode_contents() if len(divs) > 1 else ''
        pro_lines = ''.join(f'<div class="pro-step" data-i="{i}">{str(x)}</div>' for i, x in enumerate(pro))
        html = f'''<!DOCTYPE html>
<html lang="{e.lang}" data-world="paper">
<head>
{self.head(e, path, e.ui['title'], e.ui['description'], other.cover_path, ld, extra=f'<link rel="prefetch" href="{self.rel(path, first["path"])}">' + self.legacy_links(e, path))}
</head>
<body data-page="cover" data-amb="shore" data-y="1700">
{self.topbar(e, path, other.cover_path)}
{self.menu(e, path)}
<main id="main" data-world="paper">
{self.cover_stage(e, path, imgp, kick, h1, sub, by, stats, first, pro)}
<section class="intro w-paper" data-world="paper"><div>{rest}</div></section>
<section class="mainline w-paper" data-world="paper" data-scene="mainline"><div>{mainline}</div></section>
{reading}
<section class="home-sec home-tl" data-world="sea" id="tidslinje"><div class="in"><p class="home-k">{esc(e.ui['timeline'])}</p><h2 class="home-t">{esc(e.ui['timeline_title'])}</h2>{NAV.timeline(self, e, path)}</div></section>
<section class="home-sec home-ft w-paper" data-world="paper" id="slaegten"><div class="in"><p class="home-k">{esc(e.ui['family'])}</p><h2 class="home-t">{esc(e.ui['family_title'])}</h2>{NAV.family(self, e, path)}</div></section>
<div class="toc w-paper" data-world="paper" id="indhold">{''.join(parts)}</div>
</main>
{self.colophon(e, path)}
{self.defs()}
{self.dialogs(e)}
{self.page_data(e)}
<script src="{self.rel(path, 'assets/')}ny.js" defer></script>
</body>
</html>
'''
        return path, self.fix(e, path, html)

    # the kær names on the survey sheet of 1872, in pixels of the 1445 × 1800 image: centre x, y, width, height
    KAER = [(372, 413, 160, 46, -4), (352, 578, 150, 92, 3), (105, 1333, 128, 40, -2), (1190, 1230, 340, 60, 1), (750, 1636, 118, 38, -3)]

    def cover_stage(self, e, path, imgp, kick, h1, sub, by, stats, first, pro):
        """The cover is the survey sheet of 1872. The title lies on it; scrolling, the camera goes looking for the
        kær names the land is named after, and finds, at last, the three written words of the deed of 1855."""
        u = e.ui
        W, H = 1445, 1800
        ring = '<svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="M8,23 C9,7 88,1 95,17 C100,33 24,41 9,29 C3,24 6,13 20,9"/></svg>'
        marks = ''.join(f'<span class="sv-mk ring" data-n="{i + 1}" style="left:{x / W * 100:.2f}%;top:{y / H * 100:.2f}%;width:{w}px;height:{h}px;--rot:{r}deg">{ring}</span>' for i, (x, y, w, h, r) in enumerate(self.KAER))
        dep = ''
        hi = HI_DIMS.get('01-maalebordsblad-husby-1872.jpg')
        hia = f' data-hi="{ASSET}hi/01-maalebordsblad-husby-1872.jpg" data-fw="{hi[0]}"' if hi else ''
        mapimg = f'<img src="{imgp}01-maalebordsblad-husby-1872.jpg" alt="{esc(u["cover_map_alt"])}" width="{W}" height="{H}"{hia} decoding="async" fetchpriority="high" draggable="false">'
        deed = f'<img src="{imgp}53-skoede-1855-beliggende-i-silkjaer.png" alt="{esc(u["cover_deed_alt"])}" width="1024" height="236" decoding="async" loading="lazy" draggable="false">'
        steps = [
            ({'shot': 0, 'x': 44, 'y': 42, 'z': 1.0}, pro[0] if len(pro) > 0 else None),
            ({'shot': 0, 'x': 25, 'y': 27, 'z': 2.3, 'mark': '1 2'}, pro[1] if len(pro) > 1 else None),
            ({'shot': 0, 'x': 14, 'y': 72, 'z': 2.2, 'mark': '1 2 3'}, None),
            ({'shot': 0, 'x': 64, 'y': 78, 'z': 1.3, 'mark': '1 2 3 4 5'}, None),
            ({'shot': 0, 'x': 40, 'y': 46, 'z': 1.12, 'slip': 'deed'}, pro[2] if len(pro) > 2 else None),
        ]
        st = []
        for i, (a, p) in enumerate(steps):
            at = ' '.join(f'data-{k}="{v}"' for k, v in a.items())
            if p is not None:
                st.append(f'<div class="stage-step{" beat" if i == len(steps) - 1 else ""}" data-i="{i}" {at}><div class="stage-card pro-card">{str(p)}</div></div>')
            else:
                st.append(f'<div class="stage-step empty" data-i="{i}" {at}></div>')
        return f'''<section class="b-scene stage stage-photos stage-cover" data-scene="stage" data-vis="photos" data-side="left" id="intro" data-world="paper">
  <div class="stage-vis">
    <div class="sv-shot paper" data-mode="cover"><div class="sv-pic">{mapimg}{marks}</div></div>
    <div class="sv-slip" data-k="deed"><div class="slip-paper">{deed}</div></div>
  </div>
  <div class="stage-steps">
    <div class="cover-card" data-scene="cover">
      <div class="cartouche">
        {str(kick) if kick else ''}
        <h1 class="cover-t">{(h1.get_text() if h1 else 'Silkjær').capitalize()}</h1>
        {str(sub) if sub else ''}
        {str(by) if by else ''}
        <div class="cover-go"><a class="go" href="{self.rel(path, first['path'])}">{esc(u['start'])} →</a><a class="go go-cont" href="#" hidden data-continue>{esc(u['continue'])} →</a></div>
        {str(stats) if stats else ''}
      </div>
      <div class="cover-scroll" aria-hidden="true">{esc(u['cover_scroll'])}</div>
    </div>
    {''.join(st)}
  </div>
</section>'''

    def print_page(self, e):
        path = e.print_path
        other = self.ed['en' if e.lang == 'da' else 'da']
        header = next(el for k, el in e.blocks if k == 'header')
        h1 = header.find('h1')
        parts = []
        for p in e.parts:
            parts.append(f'<section class="bk-part"><div class="m-s uc">{esc(p["kick"])}</div><h2 class="part-t">{esc(p["title"])}</h2><div class="m-s uc">{esc(p["range"])}</div></section>')
            for it in p['items']:
                parts.append(f'<article class="chap bk-chap" id="{it["id"]}-bk">{it["el"].decode_contents()}</article>')
        toc = ''.join(f'<li><a href="#{it["id"]}-bk"><span>{esc((e.ui["appendix"] if it["is_app"] else e.ui["chapter"]) + " " + str(it["n"]))}</span> {esc(it["title"])}</a></li>' for it in e.pages)
        intro = e.byid['intro']
        foot = next(el for k, el in e.blocks if k == 'footer')
        html = f'''<!DOCTYPE html>
<html lang="{e.lang}" data-world="paper" class="book">
<head>
{self.head(e, path, e.ui['book_page'] + ' — ' + e.ui['site'], e.ui['description'], other.print_path, {'@context': 'https://schema.org', '@type': 'WebPage', 'name': e.ui['book_page']})}
</head>
<body data-page="print" class="bookpage">
<div class="bk-bar" data-screen-only><a href="{self.rel(path, e.cover_path)}">← {esc(e.ui['site'])}</a><span>{esc(e.ui['book_intro'])}</span><button type="button" class="tool" data-act="print-now">{esc(e.ui['print_now'])}</button></div>
<main id="main" class="book-main">
<section class="bk-title"><h1>{h1.decode_contents() if h1 else 'SILKJÆR'}</h1></section>
<section class="bk-toc"><h2>{esc(e.ui['contents'])}</h2><ol>{toc}</ol></section>
<section class="chap bk-intro">{intro.decode_contents()}</section>
{''.join(parts)}
<section class="chap bk-colo">{foot.decode_contents()}</section>
</main>
<script src="{self.rel(path, 'assets/')}ny.js" defer></script>
</body>
</html>
'''
        html = html.replace(IMG, self.site_rel(path, 'billeder/')).replace(ASSET, self.rel(path, 'assets/'))
        if e.lang == 'en':
            html = self.da_links(path, html)
        # in-book links point to the chapters inside this page
        soup = BeautifulSoup(html, 'html.parser')
        for dt in soup.find_all('details'):
            dt['open'] = ''
        # the printed book loads every picture at once: a picture still waiting to be scrolled to would print as an empty frame
        for im in soup.find_all('img'):
            if im.get('loading') == 'lazy':
                del im['loading']
        for el in soup.find_all('a', href=True):
            h = el['href']
            if h.startswith('#') and len(h) > 1 and self.idmap[e.lang].get(h[1:]):
                if h[1:] in [it['id'] for it in e.pages]:
                    el['href'] = f'#{h[1:]}-bk'
        return path, str(soup)

    # ---- data files for popovers and the person drawer
    def data_files(self, out):
        os.makedirs(os.path.join(out, 'assets', 'data'), exist_ok=True)
        for L, e in self.ed.items():
            k = e.byid['kilder']
            src = {}
            for row in k.find_all(class_='src-row'):
                c = copy.copy(row)
                for al in c.find_all(class_='alias'):
                    al.decompose()
                spans = [x for x in c.find_all('span', recursive=False)]
                txt = spans[-1].decode_contents() if spans else c.decode_contents()
                src[row['id']] = txt
                for al in row.find_all(class_='alias'):
                    src[al['id']] = txt
            people = {}
            for art in e.byid['stamtavle'].find_all('article', class_='person'):
                people[art['id'][len('person-'):]] = str(art)
            json.dump(src, open(os.path.join(out, 'assets', 'data', f'kilder.{L}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
            json.dump(people, open(os.path.join(out, 'assets', 'data', f'personer.{L}.json'), 'w', encoding='utf-8'), ensure_ascii=False)

    # ---- content check
    def check(self, out, written):
        """Every text block of the classic edition (rendered afresh) must appear in the Danish pages this build wrote."""
        fresh = Edition('da', self.o)
        fresh.renumber()
        norm = lambda x: re.sub(r'[^0-9a-zæøåA-ZÆØÅéü]', '', x).lower()
        texts = []
        for rel in written:
            fn = os.path.join(out, rel)
            if rel.startswith('en/') or rel.startswith('print'):
                continue
            s = BeautifulSoup(open(fn, encoding='utf-8').read(), 'html.parser')
            for x in s(['script', 'style']):
                x.decompose()
            texts.append(s.get_text(' '))
        people = json.load(open(os.path.join(out, 'assets', 'data', 'personer.da.json'), encoding='utf-8'))
        texts.extend(BeautifulSoup(v, 'html.parser').get_text(' ') for v in people.values())
        NT = norm(' '.join(texts))
        blocks = []
        for el in fresh.soup.find_all(['p', 'div', 'span', 'li', 'h1', 'h2', 'h3', 'h4', 'figcaption', 'blockquote', 'dd', 'dt', 'summary', 'td', 'th', 'a', 'em', 'strong']):
            if el.find(['p', 'div', 'li', 'h2', 'h3', 'figcaption', 'blockquote', 'figure', 'table']):
                continue
            if el.has_attr('data-revision'):
                continue
            t = re.sub(r'\s+', ' ', el.get_text(' ', strip=True))
            if len(t) >= 12:
                blocks.append(t)
        # the classic header's scroll cue is page furniture, not text of the chronicle; so are the button, the hint and
        # the legend of the classic's »who is who« overlay on the Vedersø photograph, which this edition shows as the
        # numbered marks and the full list of names on the photograph's own stage (chapter 7)
        skip = {'scroll', 'rul'} | {norm(x) for x in ('2 · Niels Silkjær, Silkjær · 4 · Ole Pedersen, nabo til Silkjær',
                                                      'Vis hvem der er hvem Nummereret fra venstre, som på sedlen',
                                                      'Nummereret fra venstre, som på sedlen')}
        miss = [b for b in blocks if norm(b) not in NT and norm(b) not in skip]
        return len(blocks), miss

    # ---- sitemap with both languages for every page (release only)
    def sitemap(self, out):
        da, en = self.ed['da'], self.ed['en']
        pairs = [(da.cover_path, en.cover_path, '1.0')] + [(a['path'], b['path'], '0.8') for a, b in zip(da.reading, en.reading)] + [(da.print_path, en.print_path, '0.3')]
        rows = []
        for a, b, pr in pairs:
            for me in (a, b):
                rows.append(f'  <url><loc>{self.url(me)}</loc><lastmod>{self.today}</lastmod><priority>{pr}</priority>'
                            f'<xhtml:link rel="alternate" hreflang="da" href="{self.url(a)}"/>'
                            f'<xhtml:link rel="alternate" hreflang="en" href="{self.url(b)}"/>'
                            f'<xhtml:link rel="alternate" hreflang="x-default" href="{self.url(a)}"/></url>')
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
               'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(rows) + '\n</urlset>\n')
        open(os.path.join(out, 'sitemap.xml'), 'w', encoding='utf-8').write(xml)

    # ---- the review list of every piece of new text around the chronicle
    def new_texts(self, out):
        da, en = UI['da'], UI['en']
        L = ['# Nye tekster i den nye udgave', '',
             'Alt herunder er tekst, som den nye udgave tilføjer omkring krøniken — knapper, overskrifter i scenerne,',
             'billedtekster til de fotograferede sider og metabeskrivelser. Krønikens egen tekst er uændret og står ikke her.',
             'Filen skrives af `build/ny.py` ved hver build; ret teksterne i `build/ui_ny.py` og `build/scenes_ny.py`.', '',
             '## Grænseflade', '', '| Nøgle | Dansk | English |', '|---|---|---|']
        cell = lambda x: str(x).replace('|', '\\|').replace('\n', ' ')
        for k in da:
            if isinstance(da[k], list) or isinstance(en.get(k), list):
                continue
            L.append(f'| `{k}` | {cell(da[k]) or "—"} | {cell(en.get(k, "")) or "—"} |')
        L += ['', '## Kun på engelsk', '', f'**{en["reading_card_title"]}** (forsiden)', '']
        L += [f'> {x}' + '\n' for x in en['reading_card']]
        L += [f'**Oversættelsesnote** (kolofonen): {en["translation_note"]}', '',
              f'**Link ved hver udeladelse i retsakterne:** »{en["danish_original"]}« — {len(getattr(self.ed["en"], "omission_links", []))} steder, hvert til samme blok på den danske side.', '',
              '## Scener', '', '### Kapitel 5 · tværsnittet af stranden', '',
              '| Dansk | English |', '|---|---|']
        for k in ('sec_outer', 'sec_inner', 'sec_station', 'sec_clock', 'sec_rockets'):
            L.append(f'| {da[k]} | {en[k]} |')
        L += ['', '### Kapitel 12 · sagens kalender', '', '| Dag | Dansk | English |', '|---|---|---|']
        for mo, day, pat, dtx, etx in SC.CAL:
            L.append(f'| {day or "(fra teksten)"}/{mo} 1913 | {dtx} | {etx} |')
        L += ['', '### Kapitel 12 · vejen fra Årgab til Vridsløselille', '', '| Strækning | Dansk | English |', '|---|---|---|']
        for a_, b_, dd, de, _ in SC.ROUTE:
            L.append(f'| {SC._name(a_, 0)} → {SC._name(b_, 0)} | {dd} | {de} |')
        L += ['', '### Kapitel 12 · lysbordet (renskrift ved siden af originalen)', '',
              'Billedtekst under hver side: »<kilde> · s. 154, højre« / »<source> · p. 154, right«. Kildenavne:', '']
        for k, (d_, e_) in SC.SRC.items():
            L.append(f'- {d_} / {e_}')
        L += ['', 'Alt-tekst: »<kilde>, s. 154, højre — fotografi af originalen« / »… — photograph of the original«.', '',
              f'Billederne ligger i `billeder/1913/` (visning, 900 px) og `billeder/1913/fuld/` (lysbordets zoom, 1800 px), beskåret til sagen på hver side.', '',
              '### Kapitel 17 · søkortet over overfarten', '', f'Titel: »{da["chart_title"]}«. Stednavne: Esbjerg, Hvide Sande, Thyborøn, Outer Silver Pit; farvands- og landnavne »NORDSØEN« / »NORTH SEA«, »JYLLAND« / »JUTLAND«, »ENGLAND«; blyantsdatoerne »16/3« og »31/3« (fra teksten); målestok 0—50 »Sømil« / »Nautical miles«; gradtal i rammen (»55° N«, »8° Ø« / »8° E«). Kystlinjerne er Natural Earths (public domain), tegnet på Mercator som et søkort; kursen ud går nord om Fanø gennem løbet ved Skallingen.', '',
              '### Den nye udgaves scener', '',
              'Scenerne bruger krønikens egne tekster som kort; det eneste nye er mærkaterne på tegningerne og kortene:', '',
              '- Kapitel 5, tværsnittet: navnene »Anders Knudsen« og »Esper Jensen Ø.« ved de to mænd på årerne (fra teksten), mærkaterne ovenfor.',
              f'- Kapitel 9, afdriften langs stranden (set fra stranden ud over havet: vest opad, syd til venstre): »Søren Andersen Jensen · 6.000 alen«, »Peder Enevoldsen · 2.500 alen«, »Enevold Enevoldsen« (navne og tal fra teksten), målestok 0—6.000 alen, »← {UI["da"]["south"]}« / »← {UI["en"]["south"]}«, »N«. På telefon står navnene i en nøgle under kortet.',
              '- Kildehenvisninger og forbehold er nummereret fortløbende (kilde 1—180, forbehold 1—43) i katalogets rækkefølge; manuskriptet i `build/kilde/` beholder sine gamle numre. Hvert »se forbehold 12« er et link til forbeholdet.',
              '- Kapitel 6, ni dage i november: dagene 9—17 som tal; 9., 14. og 17. fremhævet.',
              '- Kapitel 18, agterspejlet: ' + ' → '.join(f'{n or "(ophugget)"} {no} {y}'.strip() for y, n, no in MOM.BOARD) + ' (fra flåderegistret i teksten).',
              '- Kortene (kapitel 11, 14—16, 19, 20): stednavnene ' + ', '.join(sorted({v[2] for v in MOM.PL.values()})) + '.',
              '- Kortbilledet af Danmark (assets/maps/danmark.jpg): byerne Ringkøbing, Herning, Holstebro, Lemvig, Skjern, Varde, Viborg, Aarhus, Randers, Silkeborg, Vejle, Kolding, Grenaa, Thisted, Skive, Odense, Ribe, Aalborg, Horsens, Fredericia; »RINGKØBING FJORD«, »LIMFJORDEN«, »KATTEGAT«; breddegrader og længdegrader.',
              '- Forsiden: kær-navnene cirkles ind på målebordsbladet (kortets egen skrift); skødets tre ord lægges på kortet som et billede.',
              '- Tallene i kapitel 9 og 14 (1896 → 1906, 1998 → 1883) er årstal, der tæller.',
              '- Kapitel 3, de to liv på én tidsakse: årstallene 1700, 1750, 1800, 1850, 1900; mærkerne »1816« og »1878«; buen mellem dem »62 år« / »62 years«.',
              '- Kapitel 5, tværsnittet: redningsbåden på sin vogn, raketstativet og signalmasten er tegnet ind; de nævnes i teksten eller hører til stationen. Ingen nye ord.',
              '- Kapitel 10, kortet over vækkelsen — anden linje under stednavnet: ' + '; '.join(f'{MOM.PL[k][2]}: »{d_}« / »{e_}«' for k, (d_, e_) in MOM.SUBS_KAP10.items()) + '.',
              '- Kapitel 15, kortet over vejen ind i landet — årene under stednavnet: ' + '; '.join(f'{MOM.PL[k][2]}: {d_}' for k, (d_, e_) in MOM.SUBS_KAP15.items()) + '.',
              '- Kapitel 18, agterspejlet: det sidste skilt siger »OPHUGGET« / »BROKEN UP«.',
              f'- Kapitel 6, navnets forvandling: sat som tabel med kolonneoverskrifterne »{UI["da"]["nf_given"]} · {UI["da"]["nf_patr"]} · {UI["da"]["nf_farm"]}« / »{UI["en"]["nf_given"]} · {UI["en"]["nf_patr"]} · {UI["en"]["nf_farm"]}«; ordene i rækkerne er krønikens egne.',
              '- Knappen ved hver lille note i teksten: skærmlæser-teksten »Læs mere« / »Read more«.', '',
              '### Målebordsbladene', '',
              'Udsnit af Generalstabens høje målebordsblade (farvemønsterblade) fra historiskekort.dk. De fire blade AA15, AA16, Ø15 og Ø16 er lagt sammen ved bladrammerne til ét kort over hjemegnen. Kameraet går hen til de navne, landmålerne selv skrev; der er ikke sat nye navne på kortene.', '',
              '| Hvor | Dansk | English | Blade |', '|---|---|---|---|']
        for k, (d_, e_, sd, se, y) in MOM.SHEET_CAPS.items():
            L.append(f'| {k} | {d_} | {e_} | {sd}, målt {y} |')
        L += ['', 'Alt-tekster: ' + '; '.join(f'»{v[4]}« / »{v[5]}«' for v in MOM.SHEETS.values()) + '.', '',
              'Nye rækker i billedregistret (appendiks E), efter nr. 1 og 1b; ejer »Generalstabens høje målebordsblade · historiskekort.dk«, gengivelse som nr. 1:', '']
        L += [f'- {nr}: {d_} / {e_}' for nr, d_, e_ in MOM.SHEET_REG.values()]
        L += ['',
              '## Metabeskrivelser (søgemaskiner og deling)', '',
              'Genereret af første længere afsnit i hvert kapitel, afkortet til ca. 155 tegn.', '']
        for lang in ('da', 'en'):
            L += [f'### {"Dansk" if lang == "da" else "English"}', '']
            for it in self.ed[lang].pages:
                L.append(f'- **{it["n"]} {it["title"]}** (`{it["path"][:-len("index.html")]}`) — {it["desc"]}')
            L.append('')
        open(os.path.join(HERE, 'NYE-TEKSTER.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')

    # ---- write everything
    def write(self):
        out = self.o.out
        # generated folders are rebuilt from scratch so renamed pages leave nothing behind
        for d in ('kapitel', 'appendiks', 'print', 'en'):
            p = os.path.join(out, d)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, '..', 'build', 'ny.py')):
                shutil.rmtree(p)
        self.build_idmap()
        pages = []
        for L, e in self.ed.items():
            for it in e.reading:
                pages.append(self.chapter_page(e, it))
            for it in e.pages:
                if it.get('host'):
                    pages.append(self.forward_page(e, it))
            pages.append(self.cover_page(e))
            pages.append(self.print_page(e))
        today = datetime.date.today() if not os.environ.get('SILK_REVISED') else datetime.date.fromisoformat(os.environ['SILK_REVISED'])
        MDA = ['januar', 'februar', 'marts', 'april', 'maj', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'december']
        MEN = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        rev = {'da': f'Senest revideret {today.day}. {MDA[today.month - 1]} {today.year}', 'en': f'Last revised {today.day} {MEN[today.month - 1]} {today.year}'}
        for path, html in pages:
            L = 'en' if path.startswith('en/') else 'da'
            html = re.sub(r'(<div[^>]*data-revision[^>]*>)[^<]*(</div>)', lambda m: m.group(1) + rev[L] + m.group(2), html)
            fn = os.path.join(out, path)
            os.makedirs(os.path.dirname(fn), exist_ok=True)
            open(fn, 'w', encoding='utf-8').write(html)
        self.data_files(out)
        self.new_texts(out)
        if self.o.release:
            self.sitemap(out)
        n, miss = self.check(out, [p for p, _ in pages])
        print(f'pages: {len(pages)} · content check: {n} text blocks, {len(miss)} missing · english untranslated: {len(self.ed["en"].missing)}')
        for m in miss[:20]:
            print('  MISSING:', m[:160])
        un = os.path.join(HERE, 'segments', 'untranslated.json')
        if os.path.exists(un):
            os.remove(un)
        if self.ed['en'].missing:
            os.makedirs(os.path.dirname(un), exist_ok=True)
            json.dump({m.id: m.src for m in self.ed['en'].missing}, open(un, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
            print('  the Danish of these segments is in build/segments/untranslated.json — see `python3 tr.py show untranslated`')
            for m in self.ed['en'].missing[:10]:
                print('  UNTRANSLATED:', m.id, m.src[:100])
        if miss:
            sys.exit('content check failed: the classic edition has sentences that are not in the new edition')


def refresh_data(src):
    """Re-extract the data tables and map places from the classic edition when it is newer than our copy."""
    import subprocess
    data = os.path.join(HERE, 'data.da.json')
    mapjs = os.path.join(os.path.dirname(os.path.abspath(src)), 'silkjaer-map.js')
    if os.path.exists(data) and os.path.getmtime(data) >= os.path.getmtime(src):
        return
    if not shutil.which('node'):
        print('note: node not found — using the existing data.da.json / places.da.json')
        return
    args = ['node', os.path.join(HERE, 'extract_data.js'), src, data]
    if os.path.exists(mapjs):
        args += [mapjs, os.path.join(HERE, 'places.da.json')]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.path.join(HERE, 'kilde', 'kroniken.html'))
    ap.add_argument('--out', default=os.path.join(HERE, '..'))
    ap.add_argument('--base', default='https://silkjaerkroniken.dk/')
    ap.add_argument('--site-prefix', default='', help='where the edition lives under the site root')
    ap.add_argument('--draft', action='store_true', help='a preview copy: pages marked noindex and no sitemap')
    ap.add_argument('--release', action='store_true', help=argparse.SUPPRESS)  # the default since the edition is the site
    ap.add_argument('--target', default='site', choices=['site', 'artifact'],
                    help='artifact: a self-contained preview (images copied, links to index.html files, the cover as the main page)')
    o = ap.parse_args()
    o.explicit = o.target == 'artifact'
    if o.target == 'artifact':
        o.url_prefix = o.site_prefix
        o.site_prefix = ''
        FULD.clear()
    o.release = o.target == 'site' and not o.draft
    if 'type="text/x-dc"' not in open(o.src, encoding='utf-8').read():
        sys.exit(f'{o.src} is not the classic edition (no x-dc template found)')
    if os.path.realpath(os.path.join(o.out, 'index.html')) == os.path.realpath(o.src):
        sys.exit('refusing to overwrite the manuscript: it belongs in build/kilde/kroniken.html (see README)')
    refresh_data(o.src)
    site = Site(o)
    site.write()
    if o.target == 'artifact':
        artifact_main(o)


def artifact_main(o):
    """The cover becomes the artifact's main page: the host adds the document skeleton, so the page keeps only its
    content, and a first script puts back what the <html> and <body> tags carried."""
    fn = os.path.join(o.out, 'index.html')
    h = open(fn, encoding='utf-8').read()
    html_attrs = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', re.search(r'<html([^>]*)>', h).group(1)))
    body_attrs = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', re.search(r'<body([^>]*)>', h).group(1)))
    head = re.search(r'<head>(.*?)</head>', h, re.S).group(1)
    body = re.search(r'<body[^>]*>(.*)</body>', h, re.S).group(1)
    head = re.sub(r'<title>.*?</title>', '<title>' + UI['da']['site'] + '</title>', head, flags=re.S)
    head = re.sub(r'<meta charset="utf-8"/?>|<meta content="width=device-width[^>]*>|<meta name="viewport"[^>]*>', '', head)
    boot = ('<script>(function(){var r=document.documentElement;'
            + ''.join(f"r.setAttribute({json.dumps(k)},{json.dumps(v)});" for k, v in html_attrs.items())
            + '})();</script>')
    # the body's attributes are set by a script that is certain to run inside <body>: right after the skip link
    battrs = ('<script>(function(){var b=document.body;'
              + ''.join(f"b.setAttribute({json.dumps(k)},{json.dumps(v)});" for k, v in body_attrs.items())
              + '})();</script>')
    body = re.sub(r'(<a class="skip"[^>]*>.*?</a>)', lambda m: m.group(1) + battrs, body, count=1, flags=re.S)
    open(fn, 'w', encoding='utf-8').write(boot + head + body)


if __name__ == '__main__':
    main()
