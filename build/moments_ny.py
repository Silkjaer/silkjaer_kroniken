"""Signature moments: one scene in every chapter and appendix, built from the chronicle's own words, pictures and
records. Nothing here adds or removes text of the chronicle; the scenes move the chronicle's own blocks into staged
layouts and add pictures drawn from what the text says. Labels inside the scenes are new text and are listed in
NYE-TEKSTER.md."""
import html as _html
import json as _json
import re as _re

from bs4 import BeautifulSoup, NavigableString, Tag

ASSET = '@@A@@/'

_E = lambda x: _html.escape(str(x), quote=True)


def frag(soup, markup):
    return BeautifulSoup(markup, 'html.parser').contents[0]


def blocks(flow):
    return [b for b in flow.find_all(recursive=False) if isinstance(b, Tag)]


def find_block(flow, pat, start=0, kind=None):
    bs = blocks(flow)
    for b in bs[start:]:
        if kind and ('b-' + kind) not in (b.get('class') or []):
            continue
        if _re.search(pat, b.get_text(' ', strip=True)):
            return b
    return None


def index_of(flow, b):
    return blocks(flow).index(b)


def make_stage(ed, first, groups, vis_html, kind, cls='', side='left', attrs=None, caps=None):
    """A full-bleed stage: the visual stays on screen while the chronicle's own paragraphs pass over it as cards.
    groups: list of lists of blocks; each list becomes one step. attrs: per step, data attributes for the visual.
    caps: per step, a caption (taken from a figure) that closes the card."""
    s = ed.soup
    st = s.new_tag('section', attrs={'class': f'b b-scene w-full stage {cls}'.strip(), 'data-scene': 'stage', 'data-vis': kind, 'data-side': side})
    first.insert_before(st)
    st.append(frag(s, f'<div class="stage-vis">{vis_html}</div>'))
    steps = s.new_tag('div', attrs={'class': 'stage-steps'})
    for i, g in enumerate(groups):
        a = {'class': 'stage-step', 'data-i': str(i)}
        for k, v in ((attrs or [{}] * len(groups))[i] or {}).items():
            a['data-' + k] = str(v)
        step = s.new_tag('div', attrs=a)
        card = s.new_tag('div', attrs={'class': 'stage-card'})
        for b in g:
            card.append(b.extract())
        c = (caps or [None] * len(groups))[i]
        if c is not None:
            card.append(c)
        if len(card.contents):
            step.append(card)
        else:
            step['class'] = ['stage-step', 'empty']
        steps.append(step)
    st.append(steps)
    return st


def take_fig(ed, fig):
    """Take a figure apart for a stage: its picture goes to the visual, its caption closes a card."""
    img = fig.find('img')
    img = img.extract() if img is not None else None
    cap = fig.find('figcaption')
    if cap is not None:
        cap = cap.extract()
        cap.name = 'div'
        cap['class'] = ['stage-cap', 't-s']
        if cap.has_attr('style'):
            del cap['style']
    return img, cap


def shot_html(img, mode='cover', marks=None, tone=''):
    """One picture of a photo stage. marks: [(n, left %, top %)] numbered points on the picture."""
    img = _copy_img(img)
    mk = ''.join(f'<span class="sv-mk" data-n="{n}" style="left:{x}%;top:{y}%" aria-hidden="true">{n}</span>' for n, x, y in (marks or []))
    return f'<div class="sv-shot {tone}" data-mode="{mode}"><div class="sv-pic">{img}{mk}</div></div>'


def _copy_img(img):
    if img is None:
        return ''
    t = BeautifulSoup(str(img), 'html.parser').find('img')
    for k in ('style', 'loading'):
        if t.has_attr(k):
            del t[k]
    t['decoding'] = 'async'
    t['draggable'] = 'false'
    return str(t)


def photo_stage(ed, first, steps, shots, cls='', side='left'):
    """steps: dicts with blocks, cap, shot, x, y, z (focus in % of the picture, zoom), mark ('2 4')."""
    vis = ''.join(shot_html(*sh) if isinstance(sh, tuple) else shot_html(sh) for sh in shots)
    groups = [st.get('blocks', []) for st in steps]
    attrs = [{k: st[k] for k in ('shot', 'x', 'y', 'z', 'mark') if k in st} for st in steps]
    caps = [st.get('cap') for st in steps]
    return make_stage(ed, first, groups, vis, 'photos', ('stage-photos ' + cls).strip(), side, attrs, caps)


# ------------------------------------------------------------------------------------------------ maps
import math as _math

PL = {  # key: lat, lon, Danish name, English name, label anchor (dx, dy, anchor) in label heights
    'husby': (56.2818, 8.176, 'Husby', 'Husby', (1, -.2, 'start')),
    'oekjaer': (56.274, 8.136, 'Økjær', 'Økjær', (-1, .9, 'end')),
    'aargab': (55.97, 8.125, 'Årgab', 'Årgab', (-1, .35, 'end')),
    'esbjerg': (55.467, 8.452, 'Esbjerg', 'Esbjerg', (1, .35, 'start')),
    'raekkermoelle': (55.9539, 8.5322, 'Rækker Mølle', 'Rækker Mølle', (1, .35, 'start')),
    'saedding': (55.93, 8.60, 'Sædding', 'Sædding', (1, 1.1, 'start')),
    'vorgod': (56.1339, 8.7539, 'Vorgod', 'Vorgod', (1, .35, 'start')),
    'ikast': (56.1394, 9.1547, 'Ikast', 'Ikast', (1, .35, 'start')),
    'oesteralling': (56.4119, 10.3146, 'Øster Alling', 'Øster Alling', (-1, .3, 'end')),
    'auning': (56.4306, 10.3833, 'Auning', 'Auning', (1, .45, 'start')),
    'oustrup': (56.476, 10.05, 'Oustrup', 'Oustrup', (-1, -.3, 'end')),
    'vejlby': (56.4680, 10.3379, 'Vejlby', 'Vejlby', (1, -.4, 'start')),
    'gudum': (56.5195, 8.4587, 'Gudum', 'Gudum', (-1, -.3, 'end')),
    'struer': (56.4917, 8.5889, 'Struer', 'Struer', (1, .35, 'start')),
    'skaevinge': (55.9072, 12.1542, 'Skævinge', 'Skævinge', (1, .35, 'start')),
    'frederiksvaerk': (55.97, 12.0228, 'Frederiksværk', 'Frederiksværk', (-1, -.3, 'end')),
    'nrnissum': (56.5611, 8.4056, 'Nørre Nissum', 'Nørre Nissum', (1, -.4, 'start')),
    'tim': (56.1911, 8.3139, 'Tim', 'Tim', (1, .35, 'start')),
    'fjand': (56.3261, 8.1406, 'Fjand', 'Fjand', (-1, .1, 'end')),
    'vallensbaek': (55.6233, 12.3847, 'Vallensbæk', 'Vallensbæk', (-1, 1.1, 'end')),
    'harboore': (56.6177, 8.1795, 'Harboøre', 'Harboøre', (1, .35, 'start')),
    'haurvig': (55.9389, 8.1658, 'Haurvig', 'Haurvig', (1, .35, 'start')),
    'holmsland': (56.1237, 8.1760, 'Holmsland', 'Holmsland', (1, .35, 'start')),
    'lyngvig': (56.037, 8.110, 'Lyngvig', 'Lyngvig', (-1.3, -.7, 'end')),
}


def pxy(k):
    lat, lon = PL[k][0], PL[k][1]
    x = 68.0310949 * lon + 122.41370741
    y = -3897.57142788 * _math.log(_math.tan(_math.pi / 4 + _math.radians(lat) / 2)) + 5030.08372967
    return round(x, 2), round(y, 2)


MR = _json.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'maprast.json')))
MAP_IW, MAP_IH = MR['rw'] * MR['s'], MR['rh'] * MR['s']


def mpx(k):
    """A place on the survey-style map of Denmark (assets/maps/danmark.jpg), in pixels of that image."""
    x, y = pxy(k)
    return round((x - MR['x0']) * MR['s'], 1), round((y - MR['y0']) * MR['s'], 1)


# the survey sheets themselves (Generalstabens høje målebordsblade, farvemønsterblade), cut to the places of the story
SHEETS = {
    'hjemegn': ('hjemegn-1872.jpg', 1500, 2036, 4200,
                'Fire målebordsblade fra 1872 lagt sammen: klitterne og stranden fra Husby Klit til Vedersø Klit, og inde bag dem Øby, Husby og Nørresø',
                'Four survey sheets of 1872 joined: the dunes and the beach from Husby Klit to Vedersø Klit, and behind them Øby, Husby and Nørresø'),
    'aargab': ('aargab-1871.jpg', 1300, 2708, 3600,
               'Målebordsbladet AA11 Aargab fra 1871: Holmsland Klit fra Renderne i nord til Havrvig i syd, havet mod vest og fjorden mod øst',
               'Survey sheet AA11 Aargab of 1871: Holmsland Klit from Renderne in the north to Havrvig in the south, the sea to the west and the fjord to the east'),
    'esbjerg': ('esbjerg-1899.jpg', 1600, 1095, 3800,
                'Målebordsbladet Z4 Esbjerg, tegnet 1899: byens gader i net, havnen og forhavnen med de to fyr, og Strandby mod nord',
                'Survey sheet Z4 Esbjerg, drawn 1899: the grid of the town, the harbour and the outer harbour with its two lights, and Strandby to the north'),
    'oesteralling': ('oester-alling-1878.jpg', 1600, 1250, 3200,
                     'Målebordsbladet G17 Hvilsager fra 1878 med Øster Alling og præstegården',
                     'Survey sheet G17 Hvilsager of 1878 with Øster Alling and its parsonage'),
}


# what each map shows, in the words of the caption (Danish, English), the sheets and the year they were surveyed
SHEET_CAPS = {
    'kap1': ('»Öby« på målebordsbladet.', '“Öby” on the survey sheet.', 'Ø15 og Ø16', 'Ø15 and Ø16', 1872),
    'kap2': ('Klitterne og den åbne strand ved Husby Klit.', 'The dunes and the open beach at Husby Klit.', 'AA16 og Ø16', 'AA16 and Ø16', 1872),
    'kap7': ('»Redningsstation« ved Øhuse på Vedersø Klit — og bag klitterne Øby og Husby.',
             '“Redningsstation” — the rescue station — at Øhuse on Vedersø Klit, and behind the dunes Øby and Husby.',
             'AA15, AA16, Ø15 og Ø16', 'AA15, AA16, Ø15 and Ø16', 1872),
    'kap9': ('Holmsland Klit fra Renderne til Havrvig: Årgab midt på kortet, havet mod vest og fjorden mod øst.',
             'Holmsland Klit from Renderne to Havrvig: Årgab in the middle, the sea to the west and the fjord to the east.', 'AA11', 'AA11', 1871),
    'kap11': ('»Havn« og »Forhavn« neden for byens gader.',
              '“Havn” and “Forhavn” — the harbour and the outer harbour — below the streets of the town.',
              'Z4', 'Z4', ('1870, rettet i marken 1896, tegnet 1899', '1870, revised in the field 1896, drawn 1899')),
    'kap14': ('»Husby Kᵉ« — kirken, hvor hun blev døbt og viet — og sognet omkring den: klitten, kærene og søen.',
              '“Husby Kᵉ” — the church where she was baptised and married — and the parish around it: the dunes, the marshes and the lake.',
              'AA15, AA16, Ø15 og Ø16', 'AA15, AA16, Ø15 and Ø16', 1872),
    'kap19': ('»Præstegaard« under Øster Alling.', '“Præstegaard” — the parsonage — below Øster Alling.', 'G17', 'G17', 1878),
}


# the sheets in the picture register (appendix E), numbered on from the chronicle's own map, no. 1 and 1b
SHEET_REG = {
    'hjemegn': ('1c', 'Målebordsblade AA15 Bavnbjerg, AA16 Bjerghuse, Ø15 Aabjerg og Ø16 Husby, målt 1872, lagt sammen ved bladrammerne',
                'Survey sheets AA15 Bavnbjerg, AA16 Bjerghuse, Ø15 Aabjerg and Ø16 Husby, surveyed 1872, joined at the sheet edges'),
    'aargab': ('1d', 'Målebordsblad AA11 Aargab, målt 1871', 'Survey sheet AA11 Aargab, surveyed 1871'),
    'oesteralling': ('1e', 'Målebordsblad G17 Hvilsager, målt 1878', 'Survey sheet G17 Hvilsager, surveyed 1878'),
    'esbjerg': ('1f', 'Målebordsblad Z4 Esbjerg, målt 1870, rettet i marken 1896, tegnet 1899', 'Survey sheet Z4 Esbjerg, surveyed 1870, revised in the field 1896, drawn 1899'),
}
SHEET_OF = {'kap1': 'hjemegn', 'kap2': 'hjemegn', 'kap7': 'hjemegn', 'kap14': 'hjemegn', 'kap9': 'aargab', 'kap11': 'esbjerg', 'kap19': 'oesteralling'}


def sheet_caption(ed, key):
    da, en, sd, se, y = SHEET_CAPS[key]
    nr = SHEET_REG[SHEET_OF[key]][0]
    return sheet_cap(ed, da if ed.lang == 'da' else en, sd if ed.lang == 'da' else se, y, nr)


def sheet_img(ed, k):
    f, w, h, hw, da, en = SHEETS[k]
    return (f'<img src="{ASSET}maps/{f}" alt="{_E(da if ed.lang == "da" else en)}" width="{w}" height="{h}" '
            f'data-hi="{ASSET}hi/{f}" data-fw="{hw}" decoding="async" draggable="false">')


def sheet_cap(ed, text, sheets, year, nr=None):
    """A caption in the chronicle's own form for a map: what is seen, then the picture number, the sheet and the credit."""
    da = ed.lang == 'da'
    many = ',' in sheets or ' og ' in sheets or ' and ' in sheets
    pre = (f'Billede {nr} · ' if da else f'Image {nr} · ') if nr else ''
    if isinstance(year, tuple):
        year = year[0] if da else year[1]
    cr = pre + (f'Målebordsblade 1:20.000, {"kortblade" if many else "kortblad"} {sheets}, målt {year} · frit kortmateriale · kreditér' if da else
                f'Survey sheets 1:20,000, {"sheets" if many else "sheet"} {sheets}, surveyed {year} · free map material · credit')
    return (f'<div class="stage-cap t-s">{text}<div class="m-s uc c-mut2" style="margin-top:8px">{cr} '
            f'<a class="c-sea" href="https://historiskekort.dk" rel="noopener" target="_blank">historiskekort.dk</a></div></div>')


def sheet_stage(ed, first, k, steps, cls):
    """A survey sheet on a stage: the camera goes to the names the surveyors wrote."""
    shot = f'<div class="sv-shot paper" data-mode="cover"><div class="sv-pic">{sheet_img(ed, k)}</div></div>'
    groups = [st.get('blocks', []) for st in steps]
    attrs = [{kk: st[kk] for kk in ('shot', 'x', 'y', 'z', 'fit') if kk in st} for st in steps]
    caps = [frag(ed.soup, st['cap']) if st.get('cap') else None for st in steps]
    return make_stage(ed, first, groups, shot, 'photos', ('stage-photos stage-sheet ' + cls).strip(), 'left', attrs, caps)


# the second line under a place name on the maps: what happened there, in the chronicle's own figures
SUBS_KAP10 = {'harboore': ('26 druknede · 1893', '26 drowned · 1893'), 'aargab': ('forliset · 1896', 'the wreck · 1896'),
              'haurvig': ('Getsemane · 1899', 'Getsemane · 1899'), 'holmsland': ('Thabor · 1899', 'Thabor · 1899'),
              'lyngvig': ('Ebenezer · 1910', 'Ebenezer · 1910')}
SUBS_KAP15 = {'husby': ('1883—1906', '1883—1906'), 'raekkermoelle': ('1908—1917', '1908—1917'), 'vorgod': ('1930', '1930')}


def map_stage(ed, first, steps, legs, keys, cls='', side='left', subs=None):
    """A journey on the map: the map is a picture on a photo stage, the route is drawn over it as it is read.
    steps: dicts with blocks, view (place keys to frame, or cx, cy, width in map units), legs, stops, done."""
    li = 0 if ed.lang == 'da' else 1
    L = []
    for i, (a, b, bend) in enumerate(legs):
        (x1, y1), (x2, y2) = mpx(a), mpx(b)
        mx, my, dx, dy = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
        L.append(f'<path class="leg" pathLength="1" data-i="{i}" data-a="{a}" data-b="{b}" d="M{x1},{y1} Q{mx - dy * bend:.1f},{my + dx * bend:.1f} {x2},{y2}"/>')
    dots = ''
    for k in keys:
        x, y = mpx(k)
        dx, dy, anc = PL[k][4]
        dots += (f'<span class="sv-dot" data-k="{k}" style="left:{x / MAP_IW * 100:.3f}%;top:{y / MAP_IH * 100:.3f}%" aria-hidden="true"></span>'
                 f'<span class="sv-lab {anc}" data-k="{k}" style="left:{x / MAP_IW * 100:.3f}%;top:{y / MAP_IH * 100:.3f}%;--dx:{dx};--dy:{dy}">{_E(PL[k][2 + li])}'
                 + (f'<small>{_E(subs[k][li])}</small>' if subs and k in subs else '') + '</span>')
    over = (f'<svg class="sv-route" viewBox="0 0 {MAP_IW} {MAP_IH}" preserveAspectRatio="none" aria-hidden="true">{"".join(L)}'
            f'<circle class="here" r="6" cx="-50" cy="-50"/></svg>{dots}')
    img = f'<img src="{ASSET}maps/danmark.jpg" alt="" width="{MAP_IW}" height="{MAP_IH}" draggable="false">'
    vis = f'<div class="sv-shot paper" data-mode="cover"><div class="sv-pic">{img}{over}</div></div>'
    groups, attrs = [], []
    for st in steps:
        v = st.get('view')
        if v and isinstance(v[0], str):
            pts = [mpx(k) for k in v]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            pad = st.get('pad', 1.3)
            m = 26 * MR['s']
            vw = (max(xs) - min(xs) + m) * pad
            vh = (max(ys) - min(ys) + m) * pad
            cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        else:
            cx, cy, vw = (v[0] - MR['x0']) * MR['s'], (v[1] - MR['y0']) * MR['s'], v[2] * MR['s']
            vh = vw * .6
        a = {'shot': 0, 'x': f'{cx / MAP_IW * 100:.2f}', 'y': f'{cy / MAP_IH * 100:.2f}', 'z': 1, 'vw': f'{vw:.0f}', 'vh': f'{vh:.0f}',
             'legs': ' '.join(str(i) for i in st.get('legs', [])), 'stops': ' '.join(st.get('stops', []))}
        if st.get('done'):
            a['done'] = ' '.join(str(i) for i in st['done'])
        attrs.append(a)
        groups.append(st.get('blocks', []))
    return make_stage(ed, first, groups, vis, 'photos', ('stage-photos stage-map ' + cls).strip(), side, attrs,
                      [st.get('cap') for st in steps])


# ------------------------------------------------------------------------------------------------ small scenes
def sentences(ed, p):
    """Wrap the sentences of a paragraph so they can come up one at a time as it is read."""
    if p is None:
        return
    p['data-scene'] = 'sentences'
    for node in list(p.children):
        if isinstance(node, NavigableString) and node.strip():
            parts = _re.split(r'(?<=[.!?»])\s+(?=[A-ZÆØÅ»])', str(node))
            if len(parts) < 2:
                continue
            new = []
            for j, part in enumerate(parts):
                sp = ed.soup.new_tag('span', attrs={'class': 'sent'})
                sp.string = part + (' ' if j < len(parts) - 1 else '')
                new.append(sp)
            node.replace_with(*new)
    # a paragraph without inner sentence breaks gets one span per text node
    if not p.find(class_='sent'):
        for node in list(p.children):
            if isinstance(node, NavigableString) and node.strip():
                sp = ed.soup.new_tag('span', attrs={'class': 'sent'})
                sp.string = str(node)
                node.replace_with(sp)


def zoom_fig(ed, fig, z, ox, oy, direction='out', cut=False):
    """A picture on a tall track: it starts close on one place and draws back to the whole (or the reverse)."""
    if fig is None:
        return
    s = ed.soup
    img = fig.find('img')
    fig['class'] = [c for c in fig.get('class', []) if c not in ('w-text', 'w-wide', 'w-side')] + ['w-full', 'pan-fig']
    fig['data-scene'] = 'zoomout'
    fig['data-z'], fig['data-ox'], fig['data-oy'], fig['data-dir'] = str(z), str(ox), str(oy), direction
    if cut:
        fig['data-cut'] = '1'
    if fig.get('style'):
        del fig['style']
    box = img.parent if img.parent is not fig else None
    track = s.new_tag('div', attrs={'class': 'pan-track'})
    inner = s.new_tag('div', attrs={'class': 'pan-in'})
    track.append(inner)
    if img.has_attr('style'):
        del img['style']
    inner.append(img.extract())
    if box is not None:
        box.replace_with(track)
    else:
        fig.insert(0, track)


def panorama(ed, fig):
    """A wide picture on a track: the reader walks along it."""
    if fig is None:
        return
    s = ed.soup
    img = fig.find('img')
    fig['class'] = [c for c in fig.get('class', []) if c not in ('w-text', 'w-wide')] + ['w-full', 'pano-fig']
    fig['data-scene'] = 'pano'
    box = img.parent if img.parent is not fig else None
    track = s.new_tag('div', attrs={'class': 'pano-track'})
    inner = s.new_tag('div', attrs={'class': 'pano-in'})
    track.append(inner)
    if img.has_attr('style'):
        del img['style']
    inner.append(img.extract())
    if box is not None:
        box.replace_with(track)
    else:
        fig.insert(0, track)


def counters(grid):
    for h in grid.find_all(class_='h-m'):
        t = h.get_text(strip=True)
        if t.isdigit():
            h['data-count'] = t
    grid['data-scene'] = 'count'


def births(ed, grid, pat=r'f\. (\d{1,2})\.(\d{1,2})\.(\d{4})', name_sel=('h-s', 't-l')):
    """A time axis over a grid of children: each birth a mark on the years, lit as the card is read."""
    cells = [c for c in grid.find_all(recursive=False) if isinstance(c, Tag)]
    pts = []
    for i, c in enumerate(cells):
        m = _re.search(pat, c.get_text(' ', strip=True))
        n = c.find(class_=list(name_sel))
        if not m:
            continue
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        pts.append((i, y + (mo - 1) / 12 + (d - 1) / 365, n.get_text(' ', strip=True) if n else ''))
        c['data-b'] = str(i)
    if len(pts) < 3:
        return
    y0, y1 = int(min(p[1] for p in pts)), int(max(p[1] for p in pts)) + 1
    ticks = ''.join(f'<span class="bt-t" style="--x:{(y - y0) / (y1 - y0) * 100:.2f}%">{y}</span>' for y in range(y0, y1 + 1) if (y % 5 == 0 or y in (y0, y1)))
    dots = ''.join(f'<span class="bt-d" data-b="{i}" style="--x:{(v - y0) / (y1 - y0) * 100:.2f}%" title="{_E(n)}"><i></i><b>{_E(n.split()[0])}</b></span>' for i, v, n in pts)
    ax = frag(ed.soup, f'<div class="births" aria-hidden="true"><div class="bt-line"></div>{dots}{ticks}</div>')
    grid.insert(0, ax)
    grid['data-scene'] = 'births'
    grid['class'] = grid.get('class', []) + ['has-births']


def lives(ed, box, a0, a1, marks=(), arc=None):
    """Each row of a genealogy box gets its life drawn to scale on one axis."""
    rows = []
    for row in box.find_all('div', recursive=True):
        t = row.find(class_=['t', 't-l'], recursive=False)
        if t is None:
            continue
        m = _re.search(r'(?:ca\. )?(\d{4})\s*[—–-]\s*(\d{4})', t.get_text(' ', strip=True))
        if not m:
            continue
        a, b = int(m.group(1)), int(m.group(2))
        bar = frag(ed.soup, f'<div class="life" style="--a:{(a - a0) / (a1 - a0) * 100:.2f}%;--b:{(b - a0) / (a1 - a0) * 100:.2f}%" aria-hidden="true"><i></i></div>')
        row.append(bar)
        rows.append(row)
    if not rows:
        return
    ticks = ''.join(f'<span style="--x:{(y - a0) / (a1 - a0) * 100:.2f}%">{y}</span>' for y in range(a0, a1 + 1, 50))
    mk = ''.join(f'<span class="lv-m" style="--x:{(y - a0) / (a1 - a0) * 100:.2f}%"><b>{_E(lab)}</b></span>' for y, lab in marks)
    head = rows[0].parent
    head.insert(0, frag(ed.soup, f'<div class="lives-axis" aria-hidden="true">{ticks}</div>'))
    if arc:
        x0, x1, lab = arc
        mk += f'<span class="lv-arc" style="--a:{(x0 - a0) / (a1 - a0) * 100:.2f}%;--b:{(x1 - a0) / (a1 - a0) * 100:.2f}%" data-at="{(x1 - a0) / (a1 - a0) * 100:.2f}"><em>{_E(lab)}</em></span>'
    head.append(frag(ed.soup, f'<div class="lives-marks" aria-hidden="true">{mk}</div>'))
    head['class'] = head.get('class', []) + ['lives']
    head['data-a0'], head['data-a1'] = str(a0), str(a1)
    box['data-scene'] = 'lives'


def ladder(box, rows, cls=''):
    """A sequence of lines on a tall track: each comes up as the one before it steps back."""
    if not rows:
        return
    box['data-scene'] = 'ladder'
    box['class'] = box.get('class', []) + ['ladder'] + ([cls] if cls else [])
    box['style'] = f'--n:{len(rows)}'
    for i, r in enumerate(rows):
        r['class'] = r.get('class', []) + ['rung']
        r['data-i'] = str(i)


# ------------------------------------------------------------------------------------------------ chapter 5
ROWER = ('<g transform="translate({x},0)"><path class="oar" d="M3,-11 L-30,20"/>'
         '<path d="M-5,0 C-7,-6 -6,-12 -1,-15 L4,-15 C6.5,-11 6.5,-5 5,0 Z"/>'
         '<circle cx="1.2" cy="-18.6" r="3.7"/><path d="M-4.6,-19.4 Q1,-25.5 6.4,-19.6 Q1.4,-17.2 -4.6,-19.4 Z"/></g>')
STANDER = ('<g transform="translate({x},{y})"><path d="M-3,0 L-2.4,-10 L-4.4,-10.5 L-4.2,-18.5 C-4,-21.5 4,-21.5 4.2,-18.5 L4.4,-10.5 L2.4,-10 L3,0 L1,0 L0,-8 L-1,0 Z"/>'
           '<circle cx="0" cy="-23.4" r="3.1"/><path d="M-4.4,-24 Q0,-28.6 4.4,-24 Q0,-22.4 -4.4,-24 Z"/></g>')


def capsize_svg(ui):
    """The beach at Husby in cross-section, 9 November 1878, drawn like an engraved coastal profile (see
    xsec_art): sea from the left, the outer and the inner bar, the beach, the dune with its marram, the lifeboat
    house and the signal mast. The sea and the sky are painted by a shader behind the drawing; the script moves the
    boat, the waves, the rockets and the men, and pins the labels to what they name."""
    import random as _r
    import xsec_art as X
    E = _E
    rnd = _r.Random(1878)
    # the six men are not drawn as figures: in the boat, six heads above the gunwale; in the water, each man a pale
    # point with a ring round it, which goes out when he is gone. The names on the two who were seen longest.
    rowers = ''.join(f'<circle class="hd" cx="{x}" cy="-12" r="3.1"/>' for x in (-40, -24, -8, 8, 24))
    helm = '<circle class="hd" cx="-55" cy="-15.5" r="3.1"/>'
    mark = '<circle class="rg" r="7"/><circle class="pt" r="2.4"/>'
    lost = ''.join(f'<g class="lm" transform="translate({x},{y})">{mark}</g>' for x, y in ((-26, 0), (-8, 6), (12, -2), (30, 4)))
    crew = ''
    swim = f'<path class="oar" d="M-22,2 L22,-2"/>{mark}'
    bed = X.profile_d()
    t1 = X.stipple_tile(rnd, 34, 56, .45, 1.05)
    t2 = X.stipple_tile(rnd, 12, 56, .4, .8)
    # the breaking sea: a steep, heavy crest rising on the inner bar, not a curl — foam on its face, no picture-book lip
    brk = 'M1086,474 C1138,471 1170,458 1190,436 C1203,421 1214,410 1226,408 C1240,407 1250,420 1262,440 C1278,462 1300,471 1330,474 Z'
    r0x, r0y = X.ROCKET0
    tags = (f'<span class="xs-tag dn" data-x="{X.OUT}" data-y="{X.f(X.ground(X.OUT))}"><i></i><b>{E(ui["sec_outer"])}</b></span>'
            f'<span class="xs-tag dn" data-x="{X.INN}" data-y="{X.f(X.ground(X.INN))}"><i></i><b>{E(ui["sec_inner"])}</b></span>'
            f'<span class="xs-tag up st" data-x="{X.ST_X + 40}" data-y="{X.f(X.ground(X.ST_X + 40) - 96)}"><i></i><b>{E(ui["sec_station"])}</b></span>'
            f'<span class="xs-tag up nm n1"><i></i><b>Anders Knudsen</b></span>'
            f'<span class="xs-tag up nm n2"><i></i><b>Esper Jensen Ø.</b></span>'
            f'<span class="xs-tag up rk"><i></i><b>{E(ui["sec_rockets"])}</b></span>'
            f'<span class="xs-clock">{E(ui["sec_clock"])}</span>')
    return f'''<canvas class="stage-rain"></canvas>
<svg class="xs xs-back" viewBox="780 110 1200 675" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<rect class="xs-sky" x="-1200" y="-900" width="4000" height="2800" fill="url(#xs-sky)"/>
<rect class="xs-flash" x="-1200" y="-900" width="4000" height="2800" fill="url(#xs-flash)" opacity="0"/>
<path class="xs-seafill" d="M-400,470 L2000,470 L2000,1900 L-400,1900 Z" fill="url(#xs-sea)"/>
</svg>
<svg class="xs" viewBox="780 110 1200 675" preserveAspectRatio="xMidYMid slice" data-out="{X.OUT}" data-inn="{X.INN}" data-shore="{X.SHORE}" data-b0="{X.B0}" data-ashore="{X.ASHORE}" data-ground="{X.f(X.ground(X.ASHORE))}">
<defs>
 <linearGradient id="xs-sky" gradientUnits="userSpaceOnUse" x1="0" y1="-300" x2="0" y2="480"><stop offset="0" stop-color="#05080a"/><stop offset=".6" stop-color="#121c21"/><stop offset="1" stop-color="#26363f"/></linearGradient>
 <linearGradient id="xs-sea" gradientUnits="userSpaceOnUse" x1="0" y1="440" x2="0" y2="1000"><stop offset="0" stop-color="#2a4650"/><stop offset=".3" stop-color="#15252c"/><stop offset="1" stop-color="#060d10"/></linearGradient>
 <linearGradient id="xs-sand" gradientUnits="userSpaceOnUse" x1="0" y1="290" x2="0" y2="1000"><stop offset="0" stop-color="#4a4334"/><stop offset=".14" stop-color="#342f26"/><stop offset=".26" stop-color="#1f1e1a"/><stop offset=".4" stop-color="#121719"/><stop offset=".7" stop-color="#0a0e10"/><stop offset="1" stop-color="#05080a"/></linearGradient>
 <linearGradient id="xs-ink" gradientUnits="userSpaceOnUse" x1="0" y1="300" x2="0" y2="760"><stop offset="0" stop-color="#efe6d2"/><stop offset=".36" stop-color="#efe6d2"/><stop offset=".38" stop-color="#9fb4b8" stop-opacity=".7"/><stop offset="1" stop-color="#9fb4b8" stop-opacity=".25"/></linearGradient>
 <pattern id="xs-stip" width="56" height="56" patternUnits="userSpaceOnUse"><g fill="#efe6d2">{t1}</g></pattern>
 <pattern id="xs-stip2" width="56" height="56" patternUnits="userSpaceOnUse"><g fill="#efe6d2">{t2}</g></pattern>
 <clipPath id="xs-bedclip"><path d="{bed}"/></clipPath>
 <radialGradient id="xs-flash" gradientUnits="userSpaceOnUse" cx="1000" cy="0" r="1300"><stop offset="0" stop-color="#e3ecef" stop-opacity=".6"/><stop offset="1" stop-color="#e3ecef" stop-opacity="0"/></radialGradient>
</defs>
<g class="xs-mastg">{X.station()}</g>
<g class="xs-ground">
 <path class="xs-bed" fill="url(#xs-sand)" d="{bed}"/>
 <g clip-path="url(#xs-bedclip)"><path class="xs-stip" fill="url(#xs-stip)" d="{X.band(0, 34)}"/><path class="xs-stip b" fill="url(#xs-stip2)" d="{X.band(34, 120)}"/><g class="xs-strata">{X.strata()}</g></g>
 <path class="xs-bedline" d="{X.profile_d(False)}"/>
</g>
<g class="xs-grass">{X.grass(rnd)}</g>
{X.heath(rnd)}
<g class="xs-lab"><text x="{X.OUT}" y="{X.f(X.ground(X.OUT) + 52)}" text-anchor="middle">{E(ui['sec_outer'])}</text><text x="{X.INN}" y="{X.f(X.ground(X.INN) + 52)}" text-anchor="middle">{E(ui['sec_inner'])}</text><text x="{X.ST_X + 70}" y="200" text-anchor="middle">{E(ui['sec_station'])}</text></g>
</svg>
<svg class="xs xs-front" viewBox="780 110 1200 675" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<g class="xs-crew" opacity="0">{X.lifeboat()}{X.rocket_stand()}{crew}</g>
<path class="xs-surf" d="M-1200,470 L{X.SHORE},470"/>
<path class="xs-foam f1" d="M{X.OUT - 90},470 L{X.OUT + 90},470"/>
<path class="xs-foam f2" d="M{X.INN - 80},470 L{X.INN + 100},470"/>
<path class="xs-foam f3" d="M{X.SHORE - 150},470 L{X.SHORE - 8},470"/>
<path class="xs-breaker" d="{brk}"/>
<g class="xs-boat"><g class="crew">{rowers}{helm}</g><g class="heads"></g><path class="hull" d="M-66,-16 C-54,-9 -22,-6 10,-6 C40,-6 60,-10 72,-22 C70,-8 62,4 46,10 C22,15 -26,15 -46,11 C-58,8 -65,0 -66,-16 Z"/><path class="strake" d="M-62,-10 C-48,-3 -20,-1 10,-1 C40,-1 58,-5 69,-14 M-56,0 C-40,6 -16,7 10,7 C36,7 52,4 62,-4"/><path class="stem" d="M72,-22 L75,-27 M-66,-16 L-68,-21"/></g>
<g class="xs-lost" opacity="0">{lost}</g>
<g class="xs-swim s1" opacity="0">{swim}</g>
<g class="xs-swim s2" opacity="0">{swim}</g>
<g class="xs-man" opacity="0" transform="translate({X.ASHORE},{X.f(X.ground(X.ASHORE) - 2)})"><circle class="rg" r="7"/><circle class="pt" r="2.4"/></g>
<path class="xs-rocket r1" pathLength="1" d="M{r0x},{r0y} Q1258,366 {X.INN - 34},468" data-lie="1268,470"/>
<path class="xs-rocket r2" pathLength="1" d="M{r0x},{r0y} Q1282,384 {X.INN + 16},469" data-lie="1290,471"/>
<circle class="xs-spark k1" r="4" cx="{r0x}" cy="{r0y}" opacity="0"/>
<circle class="xs-spark k2" r="4" cx="{r0x}" cy="{r0y}" opacity="0"/>
</svg>

<div class="xs-tags" aria-hidden="true">{tags}</div>'''


def kap5(ed, it):
    s = ed.soup
    flow = it['flow']
    ui = ed.ui
    sec = it['el']
    # 1. rain and lightning over the whole width of the chapter head
    host = sec.find_parent('article') or sec
    host.insert(0, frag(s, '<div class="storm-sky" data-scene="storm" aria-hidden="true"><canvas></canvas></div>'))
    # 2. the capsizing, on a stage: the three paragraphs that tell it pass over the beach in cross-section
    lab = next((b for b in blocks(flow) if 'b-label' in b.get('class', []) and b.get_text(strip=True) in ('Seks mand · én båd', 'Six men · one boat')), None)
    if lab is not None:
        ps = []
        n = lab.find_next_sibling()
        while n is not None and len(ps) < 3:
            if 'b-p' in (n.get('class') or []):
                ps.append(n)
            n = n.find_next_sibling()
        make_stage(ed, ps[0], [[ps[0]], [ps[1]], [ps[2]]], capsize_svg(ui), 'xsec', 'stage-storm')
    # 3. the five names, read out one by one
    names = [d for d in flow.find_all('div') if 'bb-acc' in (d.get('class') or []) and not d.find('div') and d.find('strong')]
    if names:
        box = names[0].parent
        box['data-scene'] = 'register'
        for d in names:
            d['class'] = (d.get('class') or []) + ['nm']
    # 4. the empty sea of the 1878 atlas sheet: from the land at the right edge out to the whole, empty sheet
    fig = next((f for f in flow.find_all('figure') if f.find('img') and '12-atlasblad' in f.find('img').get('src', '')), None)
    if fig is not None:
        img = fig.find('img')
        fig['class'] = [c for c in fig.get('class', []) if c not in ('w-text', 'w-wide')] + ['w-full', 'pan-fig']
        fig['data-scene'] = 'zoomout'
        fig['data-z'] = '3.1'
        fig['data-ox'] = '88'
        fig['data-oy'] = '46'
        for k in ('data-pan-from', 'data-pan-to'):
            fig.attrs.pop(k, None)
        if fig.get('style'):
            del fig['style']
        box = img.parent if img.parent is not fig else None
        track = s.new_tag('div', attrs={'class': 'pan-track'})
        inner = s.new_tag('div', attrs={'class': 'pan-in'})
        track.append(inner)
        img['style'] = ''
        del img['style']
        inner.append(img.extract())
        if box is not None and box is not fig:
            box.replace_with(track)
        else:
            fig.insert(0, track)


def gallery_stage(ed, gal, lead=None, focus=None, tone='sepia', side='left', cls=''):
    """A gallery becomes a stage: each picture in turn, large and living, its caption the card."""
    fs = figs_of(gal)
    if not fs:
        return None
    parts = [take_fig(ed, f) for f in fs]
    steps = []
    for i, (im, cap) in enumerate(parts):
        fx = (focus or [])[i] if focus and i < len(focus) else (50, 50, 1.1)
        steps.append({'blocks': ([lead] if (lead is not None and i == 0) else []), 'cap': cap, 'shot': i, 'x': fx[0], 'y': fx[1], 'z': fx[2]})
    def mode(im):
        w, h = int(im.get('width') or 1000), int(im.get('height') or 700)
        return 'cover' if (w >= 900 and w / max(1, h) >= 1.1) else 'contain'
    st = photo_stage(ed, gal, steps, [(im, mode(im), None, tone) for im, c in parts], cls, side)
    gal.decompose()
    return st


def B(it, i, kind=None):
    """Block i of the chapter's flow — the same in both languages, since the English is set on the same blocks."""
    bs = blocks(it['flow'])
    if i >= len(bs):
        return None
    b = bs[i]
    if kind and ('b-' + kind) not in (b.get('class') or []):
        return None
    return b


def figs_of(b):
    return [f for f in (b.find_all('figure') if b is not None else []) if f.find('img')]


# ------------------------------------------------------------------------------------------------ chapter 1
def kap1(ed, it):
    s = ed.soup
    box = B(it, 2, 'box')
    if box is not None:
        box.insert(0, frag(s, '<div class="split" data-scene="split" aria-hidden="true"><span class="sp-a">Sil</span><span class="sp-b">kjær</span></div>'))
        box['class'] = box.get('class', []) + ['has-split']
    fig = B(it, 5, 'fig')
    p3, p4, p6 = B(it, 3, 'p'), B(it, 4, 'p'), B(it, 6, 'p')
    # the deed of 1855 itself: the camera goes from the whole page to the three words, and the words lift off it
    app = ed.byid.get('appendiks-a')
    full = next((i for i in (app.find_all('img') if app is not None else []) if '51-skoede' in i.get('src', '')), None)
    if fig is not None and full is not None and None not in (p3, p4, p6):
        words, cap = take_fig(ed, fig)
        ring = '<svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="M8,23 C9,7 88,1 95,17 C100,33 24,41 9,29 C3,24 6,13 20,9"/></svg>'
        shot = shot_html(full, 'contain', None, 'paper').replace('</div></div>', f'<span class="sv-mk ring" data-n="1" style="left:38.9%;top:40.6%;width:230px;height:62px;--rot:-1deg">{ring}</span></div></div>', 1)
        slip = f'<div class="sv-slip lift" data-k="words"><div class="slip-paper">{_copy_img(words)}</div></div>'
        # first the place on the survey sheets — Øby, as the surveyors of 1872 wrote it — then the paper
        mapshot = f'<div class="sv-shot paper" data-mode="cover"><div class="sv-pic">{sheet_img(ed, "hjemegn")}</div></div>'
        mcap = frag(s, sheet_caption(ed, 'kap1'))
        steps = [
            {'blocks': [p3], 'cap': mcap, 'shot': 0, 'x': 37, 'y': 32.5, 'z': 2.5},
            {'blocks': [p4], 'shot': 1, 'x': 39, 'y': 41, 'z': 2.6, 'mark': '1'},
            {'blocks': [p6], 'cap': cap, 'shot': 1, 'x': 39, 'y': 41, 'z': 3.1, 'mark': '1', 'slip': 'words'},
        ]
        groups = [st['blocks'] for st in steps]
        attrs = [{k: st[k] for k in ('shot', 'x', 'y', 'z', 'mark', 'slip') if k in st} for st in steps]
        make_stage(ed, p3, groups, mapshot + shot + slip, 'photos', 'stage-photos stage-deed', 'left', attrs, [st.get('cap') for st in steps])
        fig.decompose()
    lad = B(it, 8, 'box')
    if lad is not None:
        ladder(lad, [d for d in lad.find_all('div', recursive=False)], 'ladder-name')


# ------------------------------------------------------------------------------------------------ chapter 2
def kap2(ed, it):
    p1, p2, p3, gal = B(it, 1, 'p'), B(it, 2, 'p'), B(it, 3, 'p'), B(it, 4, 'gallery')
    fs = figs_of(gal)
    if None in (p1, p2, p3) or len(fs) < 3:
        return
    parts = [take_fig(ed, f) for f in fs]
    shots = [(parts[0][0], 'cover', None, 'sepia'), (parts[1][0], 'cover', None, 'sepia'), (parts[2][0], 'cover', None, 'paper'),
             (sheet_img(ed, 'hjemegn'), 'cover', None, 'paper')]
    steps = [
        {'blocks': [p1], 'shot': 3, 'x': 34, 'y': 7, 'z': 1.6},
        {'blocks': [p2], 'cap': frag(ed.soup, sheet_caption(ed, 'kap2')),
         'shot': 3, 'x': 14, 'y': 21, 'z': 2.6},
        {'blocks': [p3], 'cap': parts[0][1], 'shot': 0, 'x': 50, 'y': 56, 'z': 1.12},
        {'blocks': [], 'cap': parts[1][1], 'shot': 1, 'x': 46, 'y': 45, 'z': 1.14},
        {'blocks': [], 'cap': parts[2][1], 'shot': 2, 'x': 50, 'y': 50, 'z': 1, 'fit': 'contain'},
    ]
    st = photo_stage(ed, p1, steps, shots, 'stage-land')
    for i, x in enumerate(st.find_all(class_='stage-step')):
        if steps[i].get('fit'):
            x['data-fit'] = steps[i]['fit']
    gal.decompose()


# ------------------------------------------------------------------------------------------------ chapter 3
def kap3(ed, it):
    box = B(it, 5, 'box')
    if box is not None:
        lives(ed, box, 1700, 1900, marks=((1816, '1816'), (1878, '1878')), arc=(1816, 1878, '62 år' if ed.lang == 'da' else '62 years'))
        for row in box.find_all(class_='life'):
            t = row.parent.get_text(' ', strip=True).lower()
            if 'strandfoged' in t or 'bailiff' in t:
                row['class'] = row.get('class', []) + ['sf']
    sentences(ed, B(it, 6, 'p'))


# ------------------------------------------------------------------------------------------------ chapter 4
def kap4(ed, it):
    ps = [B(it, i, 'p') for i in (1, 2, 3, 4)]
    fig = B(it, 10, 'fig')
    if None in ps or fig is None:
        return
    img, cap = take_fig(ed, fig)
    steps = [
        {'blocks': [], 'cap': cap, 'shot': 0, 'x': 50, 'y': 50, 'z': 1},
        {'blocks': [ps[0]], 'shot': 0, 'x': 66, 'y': 78, 'z': 1.7},
        {'blocks': [ps[1]], 'shot': 0, 'x': 58, 'y': 80, 'z': 2.1},
        {'blocks': [ps[2]], 'shot': 0, 'x': 36, 'y': 40, 'z': 1.5},
        {'blocks': [ps[3]], 'shot': 0, 'x': 50, 'y': 55, 'z': 1.05},
    ]
    photo_stage(ed, ps[0], steps, [(img, 'cover', None, 'dim')], 'stage-church')
    fig.decompose()
    grid = next((b for b in blocks(it['flow']) if 'b-grid' in b.get('class', [])), None)
    if grid is not None:
        grid['data-scene'] = 'register'
        for c in grid.find_all('div', recursive=False):
            c['class'] = c.get('class', []) + ['nm']


# ------------------------------------------------------------------------------------------------ chapter 6
def name_forms(ed, box):
    """The name's forms as the papers give them, set as a table: given name, patronymic and farm name each keep their
    own column, so the eye sees the patronymic fall away and the farm name come in. The children's row of 1890 sits
    in the same columns. Every word stays where the chronicle has it, in the same order."""
    s, ui = ed.soup, ed.ui
    rows = box.find_all('div', recursive=False)
    body, states = [], []
    for r in rows:
        spans = r.find_all('span', recursive=False)
        if len(spans) < 2:
            return
        key, nm = spans[0], spans[1]
        acc = nm.find('span', class_='c-acc')
        note = nm.find('span', class_='t')
        lead = ''.join(str(c) for c in nm.contents if isinstance(c, str)).strip()
        accs = acc.get_text(' ', strip=True) if acc else ''
        kids = lead.endswith(':')
        if kids:
            given, patr = lead, (accs.split(' ', 1)[0] if ' ' in accs else '')
            farm = accs.split(' ', 1)[1] if ' ' in accs else accs
        else:
            w = lead.split(' ', 1)
            given, patr, farm = w[0], (w[1] if len(w) > 1 else ''), accs
        y = nm.get('data-y')
        cls = ' class="kids"' if kids else ''
        ya = f' data-y="{_E(y)}"' if y else ''
        # the children's row: who it is stands small over their patronymic, so the given-name column stays empty
        g_cell, p_cell = ('', f'<small>{_E(given)}</small> {_E(patr)}') if kids else (_E(given), _E(patr))
        body.append(f'<tr{cls}{ya}><th scope="row">{_E(key.get_text(strip=True))}</th><td class="g">{g_cell}</td>'
                    f'<td class="p">{p_cell}</td><td class="f">{_E(farm)}</td></tr>')
        if note is not None:
            body.append(f'<tr class="nt"><td></td><td colspan="3">{_E(note.get_text(" ", strip=True))}</td></tr>')
        states.append({'k': key.get_text(strip=True), 'g': given, 'p': patr, 'f': farm, 'kids': kids,
                       'n': note.get_text(' ', strip=True) if note is not None else ''})
    head = (f'<thead><tr><td></td><th scope="col">{_E(ui["nf_given"])}</th><th scope="col">{_E(ui["nf_patr"])}</th>'
            f'<th scope="col">{_E(ui["nf_farm"])}</th></tr></thead>')
    # the same forms, set in motion: the farm name comes into the father's name from below, through the children,
    # and the patronymic falls away (the table under it is the record; this is only its picture)
    scene = ''
    if len(states) >= 3 and any(x['kids'] for x in states):
        scene = (f'<div class="b w-wide nm-scene" data-scene="namemorph" aria-hidden="true" style="--n:{len(states)}" '
                 f'data-states="{_E(_json.dumps(states, ensure_ascii=False))}"><div class="nm-pin"><div class="nm-when"></div>'
                 f'<div class="nm-stage"></div><div class="nm-note"></div><div class="nm-steps"></div></div></div>')
    box.replace_with(frag(s, f'<table class="nf">{head}<tbody>{"".join(body)}</tbody></table>'))
    return scene


def kap6(ed, it):
    s = ed.soup
    box = B(it, 2, 'box')
    if box is not None:
        rows = box.find('div', class_='bl2')
        days = ''.join(f'<span class="dd{" on" if d in (9, 14, 17) else ""}" data-d="{d}"><b>{d}</b></span>' for d in range(9, 18))
        if rows is not None:
            rows.insert_before(frag(s, f'<div class="days" data-scene="days" aria-hidden="true">{days}</div>'))
    nb = B(it, 11, 'box')
    if nb is not None:
        inner = next((d for d in nb.find_all('div', recursive=False) if len(d.find_all('div', recursive=False)) >= 4), None)
        if inner is not None:
            scene = name_forms(ed, inner)
            if scene:
                nb.insert_before(frag(s, scene))


# ------------------------------------------------------------------------------------------------ chapter 7
CREW = [(1, 6.6, 74), (2, 13.9, 75), (3, 19.3, 77), (4, 27, 72), (5, 36.3, 77), (6, 44.8, 73), (7, 53.4, 72), (8, 59.8, 73),
        (9, 66.3, 76), (10, 73, 73), (11, 79.3, 74), (12, 86, 76), (13, 93, 74)]


def kap7(ed, it):
    s = ed.soup
    p0 = B(it, 0, 'p')
    gal = B(it, 7, 'gallery')
    p1, lst, p3, who, p5 = B(it, 1, 'p'), B(it, 2, 'box'), B(it, 3, 'p'), B(it, 4, 'box'), B(it, 5, 'p')
    gal2, lab = B(it, 11, 'gallery'), B(it, 10, 'label')
    if gal is not None and None not in (p1, lst, p3, who, p5):
        img = figs_of(gal)[0].find('img')
        # the positions of the numbers on the photo, as the gallery overlay has them
        marks = []
        for d in gal.find_all('div'):
            st = d.get('style', '')
            t = d.get_text(strip=True)
            m1, m2 = _re.search(r'top:([\d.]+)%', st), _re.search(r'left:([\d.]+)%', st)
            if t.isdigit() and m1 and m2:
                marks.append((int(t), float(m2.group(1)), float(m1.group(1))))
        marks = marks or CREW
        # the photograph is shown once, on the stage: its caption closes the last card, and the gallery after the
        # stage keeps only the handwritten note that names the men
        f0 = figs_of(gal)[0]
        _im, cap0 = take_fig(ed, f0)
        steps = [
            {'blocks': [p1], 'shot': 0, 'x': 50, 'y': 50, 'z': 1},
            {'blocks': [lst], 'shot': 0, 'x': 50, 'y': 62, 'z': 1.08, 'mark': 'all'},
            {'blocks': [p3], 'shot': 0, 'x': 20.5, 'y': 58, 'z': 2.3, 'mark': '2 4'},
            {'blocks': [who], 'shot': 0, 'x': 13.9, 'y': 52, 'z': 2.6, 'mark': '2'},
            {'blocks': [p5], 'cap': cap0, 'shot': 0, 'x': 50, 'y': 50, 'z': 1},
        ]
        photo_stage(ed, p1, steps, [(img, 'contain', marks, 'sepia')], 'stage-crew', 'right')
        f0.decompose()
    if gal2 is not None:
        fs = figs_of(gal2)
        parts = [take_fig(ed, f) for f in fs]
        focus = [(50, 40, 1.1), (50, 55, 1.12), (55, 55, 1.12), (58, 50, 1.15), (45, 55, 1.1), (50, 55, 1.1)]
        steps = [{'blocks': [lab] if (i == 0 and lab is not None) else [], 'cap': c, 'shot': i, 'x': focus[i % 6][0], 'y': focus[i % 6][1], 'z': focus[i % 6][2]}
                 for i, (im, c) in enumerate(parts)]
        photo_stage(ed, gal2, steps, [(im, 'cover', None, 'sepia') for im, c in parts], 'stage-film')
        gal2.decompose()
    # the rescue station as the surveyors found it in 1872, a few hundred metres inside the dunes, with the farms behind
    if p0 is not None:
        cap = sheet_caption(ed, 'kap7')
        sheet_stage(ed, p0, 'hjemegn', [
            {'blocks': [p0], 'shot': 0, 'x': 23, 'y': 40, 'z': 2.7},
            {'blocks': [], 'cap': cap, 'shot': 0, 'x': 30, 'y': 34, 'z': 1.2},
        ], 'stage-vedersoe')


# ------------------------------------------------------------------------------------------------ chapter 8
def kap8(ed, it):
    g, gal, f1, f2 = B(it, 1, 'grid'), B(it, 2, 'gallery'), B(it, 4, 'fig'), B(it, 5, 'fig')
    if g is not None:
        births(ed, g)
    if gal is not None:
        gallery_stage(ed, gal, focus=[(50, 45, 1.05), (50, 40, 1.05)], cls='stage-sisters')
    for f in (f1, f2):
        if f is not None and f.find('img'):
            zoom_fig(ed, f, 1.45, 50, 58, 'in')


# ------------------------------------------------------------------------------------------------ chapter 9
def drift_svg(ed):
    """The beach at Årgab seen from above, drawn as a coastal chart: the sea in engraved water lines, the two bars,
    the surf, the beach and the dune. The boat went down on the outer bar; the two men on the wreckage drifted south
    in the surf, to scale — 2500 and 6000 alen, as the chronicle gives them — while the fishermen followed them along
    the beach, and at the end of the longer drift the line went out from the shore."""
    import random as _r
    rnd = _r.Random(1896)
    # the chart is oriented as one stands on the beach and looks out: the sea (west) at the top, the land (east) below,
    # and so south is to the left — the drift runs from the wreck on the right towards the left
    X0, X1 = 110, 910                      # 6000 and 0 alen
    ax = lambda a: X1 - (X1 - X0) * a / 6000
    OB, IB, SURF, BEACH, DUNE = 96, 150, 196, 214, 248
    n = (lambda v: f'{v:,}') if ed.lang == 'en' else (lambda v: f'{v:,}'.replace(',', '.'))
    def wline(y, amp, x0=-20, x1=1020, step=14):
        pts = []
        for x in range(x0, x1 + 1, step):
            pts.append(f'{x},{y + amp * _math.sin(x * .045 + y) + rnd.uniform(-.4, .4):.1f}')
        return 'M' + ' L'.join(pts)
    water = ''.join(f'<path d="{wline(y, .8 + (y > OB - 12) * .6)}" style="opacity:{.55 - y / 420:.2f}"/>' for y in range(8, SURF - 6, 9))
    bars = (f'<path class="bar" d="{wline(OB, 1.4, step=10)}"/><path class="bar" d="{wline(IB, 1.2, step=10)}"/>')
    surf = ''.join(f'<path d="M{x:.0f},{SURF - 4 + rnd.uniform(-2, 2):.1f} q5,-5 10,0 q5,-5 10,0"/>' for x in [rnd.uniform(-10, 1000) for _ in range(70)])
    sand = ''.join(f'<circle cx="{rnd.uniform(-20, 1020):.1f}" cy="{rnd.uniform(SURF + 2, BEACH + 20):.1f}" r="{rnd.uniform(.5, 1.1):.2f}"/>' for _ in range(420))
    dune = ''.join(f'<path d="M{x:.0f},{y:.0f} l-3,-7 M{x:.0f},{y:.0f} l1,-8 M{x:.0f},{y:.0f} l4,-6"/>' for x, y in [(rnd.uniform(-10, 1010), rnd.uniform(BEACH + 22, DUNE + 18)) for _ in range(150)])
    # the two drifts: from the wreck on the outer bar into the surf and south along it
    def track(a_end, y_run, wob):
        pts = [(ax(0), OB)]
        for k in range(1, 41):
            f = k / 40
            x = ax(0) + (ax(a_end) - ax(0)) * f
            e = min(1, f * 3.2)
            y = OB + (y_run - OB) * (1 - (1 - e) ** 2.4) + wob * _math.sin(f * 17 + y_run) * min(1, f * 5)
            pts.append((x, y))
        return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    t1 = track(6000, SURF - 16, 2.2)
    t2 = track(2500, SURF - 30, 1.6)
    ticks = ''.join(f'<path d="M{ax(a):.1f},{DUNE + 40} v{8 if a % 2000 == 0 else 5}"/>' for a in range(0, 6001, 500))
    tlab = ''.join(f'<span class="dr-s" style="left:{ax(a) / 10:.2f}%;top:{(DUNE + 52) / 3.2:.2f}%">{n(a)}</span>' for a in range(0, 6001, 2000))
    pin = lambda cls, x, y, txt, side='up': f'<span class="dr-tag {cls} {side}" style="left:{x / 10:.2f}%;top:{y / 3.2:.2f}%"><i></i><b>{txt}</b></span>'
    tags = (pin('t0', ax(0), OB, _E(ed.ui['sec_outer']), 'up end')
            + pin('t2', ax(2500), SURF - 30, f'Peder Enevoldsen · {n(2500)} alen', 'up p2')
            + pin('t1', ax(6000), SURF - 16, f'Søren Andersen Jensen · {n(6000)} alen', 'up beg')
            + pin('t3', ax(6000), BEACH + 6, 'Enevold Enevoldsen', 'dn beg'))
    return (f'<figure class="b b-fig w-wide drift" data-scene="drift" aria-hidden="true"><div class="dr-in"><svg viewBox="0 0 1000 320" preserveAspectRatio="xMidYMid meet">'
            f'<rect class="sea" x="0" y="0" width="1000" height="{SURF}"/><g class="water">{water}</g><g class="bars">{bars}</g>'
            f'<path class="land" d="M0,{SURF} H1000 V320 H0 Z"/><path class="shore" d="{wline(SURF, 1.2, step=8)}"/>'
            f'<g class="sand">{sand}</g><path class="duneline" d="{wline(BEACH + 20, 2.5, step=12)}"/><g class="dune">{dune}</g>'
            f'<g class="surf">{surf}</g>'
            f'<path class="walk" pathLength="1" d="M{ax(0):.1f},{BEACH - 4} L{ax(6000):.1f},{BEACH - 4}"/>'
            f'<path class="dr d2" pathLength="1" d="{t2}"/><path class="dr d1" pathLength="1" d="{t1}"/>'
            f'<g class="wreck" transform="translate({ax(0):.1f},{OB})"><path d="M-7,-7 L7,7 M-7,7 L7,-7"/></g>'
            f'<path class="gone" d="M{ax(2500) - 5:.1f},{SURF - 35} l10,10 M{ax(2500) + 5:.1f},{SURF - 35} l-10,10"/>'
            f'<path class="line" pathLength="1" d="M{ax(6000) - 6:.1f},{BEACH + 2} Q{ax(6000) - 14:.1f},{SURF - 2} {ax(6000):.1f},{SURF - 16}"/>'
            f'<g class="scale"><path d="M{ax(0):.1f},{DUNE + 44} H{ax(6000):.1f}"/>{ticks}</g>'
            f'</svg>{tags}{tlab}<span class="dr-s u" style="left:{(ax(0) + 24) / 10:.2f}%;top:{(DUNE + 52) / 3.2:.2f}%">alen</span>'
            f'<span class="dr-s so">← {_E(ed.ui["south"])}</span><span class="dr-s no">N</span></div>'
            # on a phone the chart is too low for pinned names; there they stand in a key beneath it, lit in the same order
            f'<div class="dr-key"><span class="k1"><i></i>Søren Andersen Jensen · {n(6000)} alen</span>'
            f'<span class="k2"><i></i>Peder Enevoldsen · {n(2500)} alen</span><span class="k3"><i></i>Enevold Enevoldsen</span></div></figure>')


def kap9(ed, it):
    opening = [B(it, i, 'p') for i in range(6)]
    box = B(it, 6, 'box')
    stone = B(it, 7, 'fig')
    beat = B(it, 15, 'p')
    if box is not None:
        rows = [d for d in box.find_all('div', recursive=False) if d.find('span') and len(d.find_all('span', recursive=False)) >= 2]
        if rows:
            wrap = ed.soup.new_tag('div', attrs={'class': 'crew-roll', 'data-scene': 'register'})
            rows[0].insert_before(wrap)
            for r in rows:
                r['class'] = r.get('class', []) + ['nm']
                wrap.append(r.extract())
        ps = box.find_all('p', recursive=False)
        tgt = next((q for q in ps if _re.search(r'2[.,]?500', q.get_text())), None)
        if tgt is not None:
            tgt.insert_after(frag(ed.soup, drift_svg(ed)))
    if stone is not None:
        zoom_fig(ed, stone, 2.7, 51, 40, 'in')
    gal9 = B(it, 20, 'gallery')
    if gal9 is not None:
        gallery_stage(ed, gal9, focus=[(50, 40, 1.0), (52, 50, 1.12), (50, 50, 1.08)], cls='stage-aargab')
    # Holmsland Klit as the surveyors drew it in 1871: the strand, the dunes, Årgab, and the chapel at Havrvig
    if None not in opening:
        cap = sheet_caption(ed, 'kap9')
        st = sheet_stage(ed, opening[0], 'aargab', [
            {'blocks': [opening[0]], 'shot': 0, 'x': 40, 'y': 48, 'z': 1.05},
            {'blocks': [opening[1]], 'shot': 0, 'x': 52, 'y': 49, 'z': 2.3},
            {'blocks': [opening[2], opening[3]], 'shot': 0, 'x': 56, 'y': 66, 'z': 1.0},
            {'blocks': [opening[4]], 'shot': 0, 'x': 76, 'y': 82, 'z': 2.4},
            {'blocks': [opening[5]], 'cap': cap, 'shot': 0, 'x': 31, 'y': 50, 'z': 1.9},
        ], 'stage-aargab-map')
    if beat is not None:
        beat['data-scene'] = 'tick'
        beat['data-from'], beat['data-to'] = '1896', '1906'
        beat.insert(0, frag(ed.soup, '<span class="tick" aria-hidden="true"><span class="odo"></span></span>'))


# ------------------------------------------------------------------------------------------------ chapter 10
def wave_svg():
    return ('<div class="wave" data-scene="wave" aria-hidden="true"><svg viewBox="0 0 1000 120" preserveAspectRatio="none">'
            '<path pathLength="1" d="M0,96 C120,92 220,98 330,90 C430,82 520,60 590,30 C630,12 690,6 720,26 C700,20 676,30 684,48 C694,74 760,92 860,96 C920,98 960,96 1000,96"/>'
            '</svg></div>')


def kap10(ed, it):
    q = B(it, 7, 'quote')
    if q is not None:
        q['data-scene'] = 'spot'
        q['data-hush'] = ''
    h = B(it, 12, 'h')
    if h is not None:
        h.append(frag(ed.soup, wave_svg()))
    q2 = B(it, 4, 'quote')
    if q2 is not None:
        q2['data-scene'] = 'spot'
    # the movement along the coast: the lights come on one by one, from the drowning to the houses of prayer
    g1, g2, g3 = B(it, 26, 'p'), B(it, 27, 'p'), B(it, 28, 'p')
    if None not in (g1, g2, g3):
        legs = [('harboore', 'aargab', .16), ('aargab', 'haurvig', .5), ('haurvig', 'holmsland', .3), ('haurvig', 'lyngvig', .3)]
        steps = [
            {'blocks': [g1], 'view': ('harboore', 'haurvig'), 'pad': 1.15, 'stops': ['harboore'], 'legs': [0, 1]},
            {'blocks': [g2], 'view': ('aargab', 'haurvig'), 'pad': .95},
            {'blocks': [g3], 'view': ('haurvig', 'holmsland', 'lyngvig'), 'pad': 1.0, 'legs': [2, 3]},
        ]
        map_stage(ed, g1, steps, legs, ['harboore', 'aargab', 'haurvig', 'holmsland', 'lyngvig'], 'stage-revival', subs=SUBS_KAP10)


# ------------------------------------------------------------------------------------------------ chapter 11
def kap11(ed, it):
    p1, p2, p3 = B(it, 1, 'p'), B(it, 2, 'p'), B(it, 3, 'p')
    gal, fin = B(it, 21, 'gallery'), B(it, 22, 'p')
    move = B(it, 19, 'p')
    if None not in (p1, p2, p3):
        legs = [('oekjaer', 'esbjerg', .12), ('esbjerg', 'aargab', -.18), ('aargab', 'esbjerg', -.18)]
        steps = [
            {'blocks': [p1], 'view': ('oekjaer', 'esbjerg'), 'pad': 1.25, 'stops': ['oekjaer']},
            {'blocks': [p2], 'view': ('oekjaer', 'esbjerg'), 'pad': 1.25, 'legs': [0], 'stops': ['esbjerg']},
            {'blocks': [p3], 'view': ('aargab', 'esbjerg'), 'pad': 1.2, 'legs': [1, 2], 'stops': ['aargab']},
        ]
        map_stage(ed, p1, steps, legs, ['oekjaer', 'esbjerg', 'aargab'], 'stage-west')
    # from boats hauled up on the sand to the harbour: Esbjerg on the survey sheet, the camera on »Havn«, then the town
    if move is not None and _re.search(r'Flytningen|move from', move.get_text()):
        sheet_stage(ed, move, 'esbjerg', [
            {'blocks': [move], 'shot': 0, 'x': 37, 'y': 72, 'z': 2.4},
            {'blocks': [], 'cap': sheet_caption(ed, 'kap11'), 'shot': 0, 'x': 33, 'y': 60, 'z': 1.05},
        ], 'stage-esbjerg')
    if gal is not None:
        gal['data-scene'] = 'triptych'
        gal['class'] = gal.get('class', []) + ['triptych']
    if fin is not None:
        sentences(ed, fin)


# ------------------------------------------------------------------------------------------------ chapter 13
def _fields(ed, host, sep=' — '):
    """Split a transcribed record into its columns at the dashes; each column becomes a span."""
    groups, cur = [], []
    stop = None
    for node in list(host.children):
        if isinstance(node, Tag) and node.name == 'div':
            stop = node
            break
        if isinstance(node, NavigableString):
            parts = str(node).split(sep)
            for j, part in enumerate(parts):
                if j > 0:
                    groups.append(cur)
                    cur = []
                if part:
                    cur.append(NavigableString(part))
            node.extract()
        else:
            cur.append(node.extract())
    groups.append(cur)
    out = []
    for k, g in enumerate(groups):
        sp = ed.soup.new_tag('span', attrs={'class': 'fld', 'tabindex': '0'})
        for n in g:
            sp.append(n)
        out.append(sp)
    for k, sp in enumerate(out):
        if stop is not None:
            stop.insert_before(sp)
            if k < len(out) - 1:
                stop.insert_before(NavigableString(sep))
        else:
            host.append(sp)
            if k < len(out) - 1:
                host.append(NavigableString(sep))
    return out


COLS = [(4.3, 11), (11, 24), (24, 37.5), (37.5, 56.5), (56.5, 66), (66, 78), (78, 100)]


def kap13(ed, it):
    q1, p7, p8, q2 = B(it, 6, 'quote'), B(it, 7, 'p'), B(it, 8, 'p'), B(it, 9, 'quote')
    fig = B(it, 16, 'fig')
    if None in (q1, p7, p8, q2, fig):
        return
    s = ed.soup
    run = s.new_tag('div', attrs={'class': 'b b-scene w-wide lt-strip', 'data-scene': 'ltstrip'})
    q1.insert_before(run)
    fig.extract()
    fig['class'] = [c for c in fig.get('class', []) if c not in ('w-wide', 'w-text')] + ['lts-fig']
    box = fig.find('img').parent
    hl = ''.join(f'<i class="lts-hl" data-c="{k}" style="left:{a}%;width:{b - a}%"></i>' for k, (a, b) in enumerate(COLS))
    box.append(frag(s, f'<span class="lts-layer" aria-hidden="true">{hl}</span>'))
    run.append(fig)
    for b in (q1, p7, p8, q2):
        run.append(b.extract())
    h1 = q1.find('span', attrs={'data-s': True}) or q1
    h2 = q2.find('span', attrs={'data-s': True}) or q2
    f1 = _fields(ed, h1)
    f2 = _fields(ed, h2)
    for k, sp in enumerate(f1[:4]):
        sp['data-c'] = str(k)
    for k, sp in enumerate(f2[:3]):
        sp['data-c'] = str(4 + k)


# ------------------------------------------------------------------------------------------------ chapter 14
def kap14(ed, it):
    p0 = B(it, 0, 'p')
    if p0 is not None:
        p0['data-scene'] = 'rewind'
        p0['data-from'], p0['data-to'] = '1998', '1883'
        p0.insert(0, frag(ed.soup, '<span class="rewind" aria-hidden="true"><span class="odo"></span></span>'))
    sentences(ed, B(it, 4, 'quote'))
    # the wedding in Husby Church, on the survey sheet: the camera on »Husby Kᵉ«, then back to the whole parish —
    # the one landscape every woman before her had married within
    p3 = B(it, 3, 'p')
    if p3 is not None:
        sheet_stage(ed, p3, 'hjemegn', [
            {'blocks': [p3], 'shot': 0, 'x': 54.4, 'y': 15.2, 'z': 2.6},
            {'blocks': [], 'cap': sheet_caption(ed, 'kap14'), 'shot': 0, 'x': 46, 'y': 34, 'z': 1.0},
        ], 'stage-wedding')


# ------------------------------------------------------------------------------------------------ chapter 15
def kap15(ed, it):
    p0, grid, p2 = B(it, 0, 'p'), B(it, 1, 'grid'), B(it, 2, 'p')
    kids = B(it, 7, 'grid')
    air = B(it, 11, 'fig')
    if air is not None:
        zoom_fig(ed, air, 1.7, 46, 48, 'in')
    if kids is not None:
        births(ed, kids, name_sel=('t-l',))
    if None in (p0, grid):
        return
    cells = [c for c in grid.find_all('div', recursive=False)]
    if len(cells) < 3:
        return
    legs = [('husby', 'raekkermoelle', .1), ('raekkermoelle', 'vorgod', -.2)]
    steps = [
        {'blocks': [p0], 'view': ('husby', 'raekkermoelle', 'vorgod'), 'pad': 1.2, 'stops': ['husby']},
        {'blocks': [cells[0]], 'view': ('husby',), 'pad': .9, 'stops': ['husby']},
        {'blocks': [cells[1]], 'view': ('husby', 'raekkermoelle'), 'pad': 1.25, 'legs': [0], 'stops': ['raekkermoelle']},
        {'blocks': [cells[2]] + ([p2] if p2 is not None else []), 'view': ('husby', 'raekkermoelle', 'vorgod'), 'pad': 1.2, 'legs': [1], 'stops': ['vorgod']},
    ]
    for c in cells:
        c['class'] = [x for x in c.get('class', []) if x != 'br'] + ['cell']
    map_stage(ed, p0, steps, legs, ['husby', 'raekkermoelle', 'vorgod'], 'stage-inland', subs=SUBS_KAP15)
    grid.decompose()


# ------------------------------------------------------------------------------------------------ chapter 16
def kap16(ed, it):
    p3 = B(it, 3, 'p')
    if p3 is not None:
        p3['data-scene'] = 'glow'
        p3['class'] = p3.get('class', []) + ['glow']
    st, gal = B(it, 7, 'fig'), B(it, 6, 'gallery')
    if st is not None:
        zoom_fig(ed, st, 2.2, 50, 52, 'in')


# ------------------------------------------------------------------------------------------------ chapter 18
BOARD = [('1949', 'ANNE KIRSTINE', 'E.94'), ('1976', 'LINDA VIG', 'L.651'), ('1980', 'JOHNNY MARIANNE', 'L.651'), ('1981', 'CHARLOTTE FRANK', 'L.651'), ('1990', '', '')]


def kap18(ed, it):
    box = B(it, 10, 'box')
    log = B(it, 2, 'box')
    gal = B(it, 12, 'gallery')
    if gal is not None:
        gallery_stage(ed, gal, focus=[(50, 45, 1.0), (40, 55, 1.25)], cls='stage-harbour')
    if box is not None:
        gone = 'OPHUGGET' if ed.lang == 'da' else 'BROKEN UP'
        # the transom of the cutter, and the names painted on it one after another; at the end the registry's stamp
        let = lambda t: ''.join(f'<i style="--j:{j}">{_E(c) if c != " " else "&nbsp;"}</i>' for j, c in enumerate(t))
        names = ''.join(f'<div class="nb-n" data-i="{i}"><b>{let(n)}</b><span>{let(no)}</span></div>' for i, (y, n, no) in enumerate(BOARD) if n)
        years = ''.join(f'<em data-i="{i}">{y}</em>' for i, (y, n, no) in enumerate(BOARD))
        planks = ''.join(f'<path d="M0,{34 + k * 27} Q300,{8 + k * 27} 600,{34 + k * 27}"/>' for k in range(1, 8))
        hull = ('<svg class="nb-hull" viewBox="0 0 600 230" preserveAspectRatio="xMidYMid meet"><defs><clipPath id="nb-cl">'
                '<path d="M18,34 Q300,4 582,34 L562,122 Q540,204 300,218 Q60,204 38,122 Z"/></clipPath></defs>'
                '<path class="nb-body" d="M18,34 Q300,4 582,34 L562,122 Q540,204 300,218 Q60,204 38,122 Z"/>'
                f'<g clip-path="url(#nb-cl)" class="nb-planks">{planks}</g>'
                '<path class="nb-rail" d="M12,36 Q300,2 588,36"/><path class="nb-post" d="M300,176 V230"/></svg>')
        box.insert(1, frag(ed.soup, f'<div class="nameboard" data-scene="nameboard" aria-hidden="true"><div class="nb-stern">{hull}'
                                    f'<div class="nb-names">{names}</div><div class="nb-paint"></div>'
                                    f'<div class="nb-years">{years}</div><div class="nb-stamp"><b>{_E(gone)}</b><span>{BOARD[-1][0]}</span></div></div></div>'))
    if log is not None:
        log['data-scene'] = 'log'
        log['class'] = log.get('class', []) + ['shiplog']


# ------------------------------------------------------------------------------------------------ chapter 19
def kap19(ed, it):
    p1, p2, p5, p6 = B(it, 1, 'p'), B(it, 2, 'p'), B(it, 5, 'p'), B(it, 6, 'p')
    gal = B(it, 4, 'gallery')
    if gal is not None:
        cap = sheet_caption(ed, 'kap19').replace('stage-cap t-s', 't-s')
        fig = frag(ed.soup, f'<figure class="b b-fig w-wide sheet-fig">{sheet_img(ed, "oesteralling")}<figcaption class="t-s">{cap}</figcaption></figure>')
        gal.insert_before(fig)
        zoom_fig(ed, gal.find_previous_sibling('figure'), 3.2, 42.5, 31, 'out')
    if gal is not None and len(figs_of(gal)) == 2:
        gal['data-scene'] = 'flip'
        gal['data-turn'] = ed.ui['turn']
        gal['class'] = gal.get('class', []) + ['postcard']
    if None not in (p1, p2, p5, p6):
        legs = [('oekjaer', 'oesteralling', -.12), ('oesteralling', 'vejlby', .3)]
        steps = [
            {'blocks': [p1], 'view': ('oekjaer',), 'pad': 1.8, 'stops': ['oekjaer']},
            {'blocks': [p2], 'view': ('oekjaer', 'oesteralling'), 'pad': 1.2, 'legs': [0], 'stops': ['oesteralling']},
            {'blocks': [p5], 'view': ('oesteralling', 'auning'), 'pad': 2.2, 'stops': ['oekjaer', 'oesteralling', 'auning'], 'done': [0]},
            {'blocks': [p6], 'view': ('oesteralling', 'vejlby', 'auning'), 'pad': 1.8, 'legs': [1], 'stops': ['vejlby']},
        ]
        # the postcard and its paragraph are kept together: the stage stops before the gallery and resumes after it
        st = map_stage(ed, p1, [steps[0], steps[1]], legs[:1], ['oekjaer', 'oesteralling'], 'stage-east')
        map_stage(ed, p5, [steps[2], steps[3]], legs, ['oekjaer', 'oesteralling', 'auning', 'vejlby'], 'stage-east stage-east2')


# ------------------------------------------------------------------------------------------------ chapter 20
def kap20(ed, it):
    g = B(it, 12, 'grid')
    if g is not None:
        counters(g)
    p1 = B(it, 1, 'p')
    if p1 is not None:
        # the branches drawn from Husby on the map of Denmark the journeys use: one line to each place the name went
        keys = ['husby', 'gudum', 'vejlby', 'esbjerg', 'fjand', 'vallensbaek']
        li = 0 if ed.lang == 'da' else 1
        V = (1300, 240, 2100, 1060)
        P = {k: mpx(k) for k in keys}
        (hx, hy) = P['husby']
        anc = {'husby': (-18, 10, 'end'), 'fjand': (-18, -8, 'end'), 'gudum': (18, -10, 'start'), 'vejlby': (18, -12, 'start'),
               'esbjerg': (18, 12, 'start'), 'vallensbaek': (-18, -14, 'end')}
        pts = ''.join(f'<g class="br-p{" o" if k == "husby" else ""}" data-k="{k}"><circle cx="{x}" cy="{y}" r="{11 if k == "husby" else 8}"/>'
                      f'<text x="{x + anc[k][0]}" y="{y + anc[k][1] + 10}" text-anchor="{anc[k][2]}">{_E(PL[k][2 + li])}</text></g>' for k, (x, y) in P.items())
        def leg(k):
            x, y = P[k]
            bend = .12 if x > hx else -.3
            return (f'<path class="br-l" pathLength="1" d="M{hx},{hy} Q{(hx + x) / 2 + (y - hy) * bend:.1f},{(hy + y) / 2 - (x - hx) * bend:.1f} {x},{y}"/>')
        legs = ''.join(leg(k) for k in keys[1:])
        img = f'<image href="{ASSET}maps/danmark.jpg" x="0" y="0" width="{MAP_IW}" height="{MAP_IH}" preserveAspectRatio="none"/>'
        p1.insert_after(frag(ed.soup, f'<figure class="b b-fig w-wide branches on-map" data-scene="branches" aria-hidden="true"><svg viewBox="{V[0]} {V[1]} {V[2]} {V[3]}">{img}{legs}{pts}</svg></figure>'))


# ------------------------------------------------------------------------------------------------ chapter 21
def kap21(ed, it):
    box = B(it, 3, 'box')
    if box is not None:
        box['data-scene'] = 'align'
        box['class'] = box.get('class', []) + ['cousins']


# ------------------------------------------------------------------------------------------------ chapter 22
def kap22(ed, it):
    beat, stone, pano, gal = B(it, 4, 'p'), B(it, 6, 'fig'), B(it, 8, 'fig'), B(it, 9, 'gallery')
    if gal is not None:
        gallery_stage(ed, gal, focus=[(50, 55, 1.08), (50, 50, 1.1), (50, 55, 1.08), (50, 55, 1.0)], tone='', cls='stage-farm')
    if beat is not None:
        sentences(ed, beat)
        beat['class'] = beat.get('class', []) + ['finale']
    if stone is not None:
        zoom_fig(ed, stone, 3.4, 64.5, 74, "in", cut=True)
    if pano is not None:
        panorama(ed, pano)


# ------------------------------------------------------------------------------------------------ appendices
def app_a(ed, it):
    f9, f11 = B(it, 9, 'fig'), B(it, 11, 'fig')
    if f9 is not None and f9.find('img', src=_re.compile('51-skoede')):
        zoom_fig(ed, f9, 3.2, 38.9, 40.6, 'in')
    if f11 is not None and f11.find('img', src=_re.compile('52-skoede')):
        zoom_fig(ed, f11, 1.9, 22, 62, 'in')


def app_b(ed, it):
    g = B(it, 2, 'grid')
    if g is None:
        return
    cells = [c for c in g.find_all('div', recursive=False)]
    names = []
    for i, c in enumerate(cells):
        h = c.find(class_='h-m')
        if h is None:
            continue
        c['data-f'] = str(i)
        names.append((i, h.get_text(' ', strip=True)))
    if len(names) < 2:
        return
    chips = f'<button type="button" class="chip on" data-f="*">{_E(ed.ui["all"])}</button>' + ''.join(f'<button type="button" class="chip" data-f="{i}">{_E(n)}</button>' for i, n in names)
    g.insert_before(frag(ed.soup, f'<div class="b w-wide chips" data-scene="filter" role="toolbar" aria-label="{_E(ed.ui["filter"])}">{chips}</div>'))


def app_d(ed, it):
    g = B(it, 4, 'grid')
    if g is None:
        return
    g['class'] = g.get('class', []) + ['caveats']
    g.insert_before(frag(ed.soup, f'<div class="b w-wide seek" data-scene="seek" data-tpl="{_E(ed.ui["seek_n"])}"><label class="seek-l"><span class="vh">{_E(ed.ui["seek"])}</span>'
                                  f'<input type="search" placeholder="{_E(ed.ui["seek"])}" autocomplete="off" spellcheck="false"></label><span class="seek-n" aria-live="polite"></span></div>'))


def app_e(ed, it):
    box = B(it, 1, 'box')
    if box is None:
        return
    # the register's numbers are the chronicle's own »Billede N« in the captions: find each picture by its number
    pics = {}
    for fig in ed.soup.find_all('figure'):
        cap = fig.find('figcaption')
        img = fig.find('img')
        if cap is None or img is None:
            continue
        for m in _re.finditer(r'(?:Billede|Image)\s+(\d+[a-z]?)', cap.get_text(' ')):
            pics.setdefault(m.group(1), img)
    # rows whose captions carry no number: the register's own entry, matched by hand to its file
    files = {'1': '01-maalebordsblad-husby-1872', '1b': '12-atlasblad-husby-1878', '3': '03-klitgaard-husby-klit',
             '4': '04-strandgaarden-interioer', '5': '05-husby-skole-1919', '5b': '05a-husby-skole-1915',
             '6': '06-redningsmandskabet-vedersoe-1915', '7': '07-silkjaer-luftfoto', '8': '08-e169-lola-neutralitetsmaerker',
             '9': '09-niels-silkjaer-portraet', '10': '10-husby-skole-1960', '12': '13-silkjaer-skraafoto-2025',
             '13': '14-johannes-madsen-silkaer', '14': '21-christiane-enevoldsen', '15': '34-havskib-fjord-1924',
             '16': '25-laura-madsen', '17': '33-gravsten-fjelstervang', '18': '27-haurvig-kirke', '19': '28-henry-silkjaer',
             '20': '29-husby-kirke-kirkegaard', '21': '30-vejlby-kirke', '22': '31-esbjerg-fiskerihavn-1956',
             '23': '32-e94-anne-kirstine', '33': '44-arne-enevoldsen-fest-1944', '39': '55-tropil-etiket-grape-squash',
             '40': '56-tropil-etiket-cocktail-drik', '52': '72-karen-marie-og-soestre', '53': '71-kristian-kornelius-boendergaard',
             '54': '73-knud-vognsgaard-1959', '55': '74-esper-jensine-bryllup-1913', '56': '75-silkjaer-gudum-familiefoto',
             '57': '76-hjerm-tolv-boern-daab'}
    by_file = {}
    for im in ed.soup.find_all('img'):
        src = im.get('src') or ''
        base = src.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        if base and base not in by_file:
            by_file[base] = im
    # the survey sheets this edition sets into the chapters, entered after the chronicle's own map sheets
    rows = box.find_all('div', attrs={'data-imgrow': True})
    after = next((r for r in rows if r.find('div', attrs={'data-k': True}) and r.find('div', attrs={'data-k': True}).get_text(strip=True) == '1b'), None)
    if after is not None:
        for key in reversed(list(SHEET_REG)):
            nr, da, en = SHEET_REG[key]
            new = BeautifulSoup(str(after), 'html.parser').find('div')
            cells = new.find_all('div', attrs={'data-k': True})
            cells[0].string = nr
            cells[1].clear(); cells[1].append(da if ed.lang == 'da' else en)
            cells[2].clear(); cells[2].append('Generalstabens høje målebordsblade · historiskekort.dk · ' if ed.lang == 'da' else 'Generalstabens høje målebordsblade · historiskekort.dk · ')
            cells[2].append(frag(ed.soup, '<a href="https://historiskekort.dk" rel="noopener" target="_blank">historiskekort.dk</a>'))
            after.insert_after(new)
            pics[nr] = BeautifulSoup(sheet_img(ed, key), 'html.parser').find('img')
    n = 0
    for row in box.find_all('div', attrs={'data-imgrow': True}):
        for c, kc in zip(row.find_all('div', recursive=False), ('nr', 'mot', 'own', 'rep')):
            c['data-kc'] = kc
        nr = row.find('div', attrs={'data-k': True})
        if nr is None:
            continue
        k = nr.get_text(strip=True)
        img = pics.get(k) or by_file.get(files.get(k, ''))
        if img is None:
            continue
        t = BeautifulSoup(str(img), 'html.parser').find('img')
        for at in ('style', 'data-depth'):
            if t.has_attr(at):
                del t[at]
        t['loading'] = 'lazy'
        t['class'] = ['reg-thumb']
        t['alt'] = ''
        cells = row.find_all('div', attrs={'data-k': True})
        (cells[1] if len(cells) > 1 else nr).insert(0, t)
        n += 1
    if n:
        box['class'] = box.get('class', []) + ['contact']


MOMENTS = {'kap1': kap1, 'kap2': kap2, 'kap3': kap3, 'kap4': kap4, 'kap5': kap5, 'kap6': kap6, 'kap7': kap7, 'kap8': kap8,
           'kap9': kap9, 'kap10': kap10, 'kap11': kap11, 'kap13': kap13, 'kap14': kap14, 'kap15': kap15, 'kap16': kap16,
           'kap18': kap18, 'kap19': kap19, 'kap20': kap20, 'kap21': kap21, 'kap22': kap22,
           'appendiks-a': app_a, 'navnenoegle': app_b, 'kilder': app_d, 'billeder': app_e}


def apply(ed):
    for it in ed.pages:
        f = MOMENTS.get(it['id'])
        if f and it.get('flow') is not None:
            f(ed, it)
