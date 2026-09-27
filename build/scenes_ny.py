"""Signature scenes for the new edition. Everything here decorates or annotates the chronicle's own markup;
no text is added or removed. apply(ed) runs after the English translation and the restyle."""

# place names and notes in English (the same table as the immersive edition's ui.py)
PLACES_EN = {
    'oversigt': ('West Jutland', 'The family’s landscape'),
    'silkjaer': ('Silkjær, Øhusevej', 'The smallholding the name came from'),
    'husby': ('Husby Church', 'Baptised, married, buried'),
    'husbyklit': ('Husby Klit', 'The sea-dunes and the beach'),
    'oekjaer': ('Økjær', 'The smallholding'),
    'tarp': ('Tarp, Vedersø', 'Anne Marie Jansdatter’s home'),
    'havet': ('Off Husby', '9 November 1878'),
    'vedersoe': ('Vedersø Lifeboat Station', 'The crew of 1915'),
    'landting': ('Landting Mark', 'Birthplace of Ane Jensen'),
    'raekkermoelle': ('Rækker Mølle, Sædding', 'The master mason’s village'),
    'ikast': ('The Ikast district', 'The trail goes on'),
    'vorgod': ('Vorgod Church', 'Laura’s last parish'),
    'esbjerg': ('Havnegade, Esbjerg', 'The skipper’s home'),
    'nordsoen': ('The North Sea', '16 March 1945'),
    'holmsland': ('Holmslands Klit', 'The Tarbensen branch'),
    'vejlby': ('Vejlby near Allingåbro', 'The gravedigger, and the name moves east'),
    'aargab': ('Årgab, Holmsland Klit', 'The widow from Årgab'),
    'vridsloeselille': ('Vridsløselille, Albertslund', 'Prisoner no. 240, 1913'),
    'hartlepool': ('Hartlepool, England', 'Run aground, 1948'),
}

# sounds tied to the case documents in chapters 12–13 (played once, when the image reaches the reading line)
SFX_IMG = {
    '63-': 'pen', '64-': 'pen', '77-': 'pen', '65-': 'pen', '66-': 'pen',
    '78-': 'stamp', '79-': 'stamp', '80-': 'stamp', '81-': 'stamp', '83-': 'stamp',
    '82-': 'telegraph', '84-': 'page', '85-': 'seal',
}


def apply(ed):
    case_file(ed)
    crossing(ed)
    import moments_ny
    moments_ny.apply(ed)
    # sticky scenes need ancestors that clip without becoming scroll containers
    # a chapter section never clips: its full-width pictures and stages reach the edges of the page
    for sec in ed.soup.select('section[data-chap]'):
        st = sec.get('style') or ''
        st = _re.sub(r'overflow(-[xy])?\s*:\s*(hidden|clip)\s*;?', '', st).strip()
        if st:
            sec['style'] = st
        elif sec.has_attr('style'):
            del sec['style']
    for el in ed.soup.select('.xsec, .chart, .case-cal, .lt-view, .stage, .storm-sky, .pan-fig, .run, [data-sticky]'):
        for a in el.parents:
            st = a.get('style') if hasattr(a, 'get') else None
            if st and _re.search(r'overflow(-[xy])?\s*:\s*hidden', st):
                a['style'] = _re.sub(r'overflow(-[xy])?\s*:\s*hidden', lambda m: m.group(0).replace('hidden', 'clip'), st)
    for sid in ('kap12', 'kap13'):
        sec = ed.byid.get(sid)
        if sec is None:
            continue
        for fig in sec.find_all('figure'):
            img = fig.find('img')
            name = img['src'].split('/')[-1] if img and img.get('src') else ''
            for pre, sfx in SFX_IMG.items():
                if name.startswith(pre):
                    fig['data-sfx'] = sfx
        # the court records themselves are read in silence
        for dt in sec.find_all('details'):
            sm = dt.find('summary')
            if sm and '·' in sm.get_text():
                dt['data-hush'] = ''


# ------------------------------------------------------------------------------------------ chapter 12: the case file
import copy as _copy
import html as _html
import json as _json
import os as _os
import re as _re

from bs4 import NavigableString as _NS

_HERE = _os.path.dirname(_os.path.abspath(__file__))
_SCANS = _json.load(open(_os.path.join(_HERE, 'scans_1913.json'), encoding='utf-8'))
_E = lambda x: _html.escape(str(x), quote=True)

# the light table: every transcript beside the photographed pages, paragraph by paragraph (lt_data.py)
from lt_data import LT as _LT, SL as _SL, PI as _PI  # noqa: E402

SRC = {
    'pp': ('Politiprotokollen', 'The police court record'),
    'rp': ('Rejsepolitiprotokollen', 'The travelling police court record'),
    'ra': ('Rapport A', 'Report A'),
    'kamp': ('Kamps indlæg', 'Kamp’s submission'),
    'dp': ('Domprotokollen', 'The judgment book'),
}


def _page_label(pid, lang):
    kind, rest = pid.split('-', 1)
    m = _re.match(r'(\d+)([LR]?)$', rest)
    n, half = m.group(1), m.group(2)
    if kind in ('ra', 'kamp'):
        return ('side ' if lang == 'da' else 'page ') + n
    side = {'L': ('venstre', 'left'), 'R': ('højre', 'right')}.get(half)
    lab = ('s. ' if lang == 'da' else 'p. ') + n
    if side:
        lab += ', ' + side[0 if lang == 'da' else 1]
    return lab


def _light_table(ed, dt, T):
    s = ed.soup
    L = ed.lang
    li = 0 if L == 'da' else 1
    ui = ed.ui
    wrap = s.new_tag('div', attrs={'class': 'lt', 'data-scene': 'lighttable'})
    text = s.new_tag('div', attrs={'class': 'lt-text'})
    for c in [c for c in dt.contents if not (getattr(c, 'name', None) == 'summary')]:
        text.append(c.extract())
    paras = text.find_all('p')[:len(T['paras'])]
    for i, p in enumerate(paras):
        p['data-lp'] = str(i)
    pages, meta = [], {}
    for pid in T['pages']:
        segs = [x for P in T['paras'] for x in P if x[0] == pid]
        meta[pid] = {'sl': list(_SL[pid]), 'pi': _PI[pid], 't': min(x[1] for x in segs), 'b': max(x[2] for x in segs)}
        kind = pid.split('-')[0]
        src_name = SRC[kind][li]
        lab = _page_label(pid, L)
        sc = _SCANS[pid]
        pages.append(
            f'<figure class="lt-page" data-pg="{pid}" style="--ar:{sc["w"]}/{sc["h"]}" hidden>'
            f'<div class="lt-sheet"><img src="@@IMG@@/1913/{pid}.jpg" data-fuld="@@IMG@@/1913/fuld/{pid}.jpg" data-zoom="" width="{sc["w"]}" height="{sc["h"]}" loading="lazy" decoding="async" '
            f'alt="{_E((src_name + ", " + lab + " — fotografi af originalen") if L == "da" else (src_name + ", " + lab + " — photograph of the original"))}">'
            f'<svg class="lt-hl" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><path class="hl-d" fill-rule="evenodd" d=""/><polygon class="hl-s" points=""/><polygon class="hl-p" points=""/></svg></div>'
            f'<figcaption class="lt-cap"><span>{_E(src_name)}</span> · {_E(lab)}</figcaption></figure>')
    tabs = ''.join(f'<button type="button" class="lt-tab" data-pg="{pid}" aria-pressed="false">{_E(_page_label(pid, L))}</button>' for pid in T['pages'])
    data = {'pages': meta, 'paras': [[[x[0], x[1], x[2]] for x in P] for P in T['paras']]}
    view = BeautifulSoupFragment(s, f'<div class="lt-view" aria-label="{_E(ui["lt_label"])}"><div class="lt-stage">{"".join(pages)}</div>'
                                    f'<div class="lt-bar"><div class="lt-tabs">{tabs}</div><p class="lt-hint">{_E(ui["lt_hint"])}</p></div></div>')
    wrap['data-lt'] = _json.dumps(data, separators=(',', ':'))
    wrap.append(text)
    wrap.append(view)
    dt.append(wrap)
    blk = dt.find_parent(class_='b')
    if blk is not None:
        blk['class'] = [c for c in blk['class'] if c not in ('w-text', 'w-wide')] + ['w-xwide', 'has-lt']


# ---- the calendar: every dated day of the case in February—April 1913, linked to the paragraph that tells it
CAL = [  # (month, day, Danish pattern of the first mention, Danish label, English label)
    (2, 13, r'torsdag den 13\. februar 1913', 'Kristine Oline betror sig til sin mor', 'Kristine Oline confides in her mother'),
    (2, 17, r'Mandag den 17\. februar', 'Betjent Jensen i Årgab · rapport A', 'Constable Jensen in Årgab · report A'),
    (2, 18, r'Skrivelsen af 18\. februar', 'Arrestrekvisitionen · bilag B', 'The arrest warrant · exhibit B'),
    (2, 21, r'Fredag den 21\. februar', 'Anholdt på Christianshavn', 'Arrested in Christianshavn'),
    (2, 24, r'Den 24\. februar kl', 'Første forhør i Ringkøbing', 'The first hearing in Ringkøbing'),
    (2, 28, r'Den 28\. februar —', 'Thomas’ forklaring', 'Thomas’s statement'),
    (3, 7, r'Den 7\. marts var', 'Kristianes forklaring', 'Kristiane’s statement'),
    (3, 17, r'Den 17\. marts klokken', 'Retten sat i Årgab', 'The court sits in Årgab'),
    (3, 22, r'Den 22\. marts, tilbage', 'Erkendelsen', 'The admission'),
    (3, 26, r'Den 26\. marts sluttede', 'Forhørene sluttet', 'The hearings close'),
    (3, 31, r'den 31\. marts kom aktionsordren', 'Aktionsordren', 'The order to prosecute'),
    (4, 2, r'og indlægget 2\. april', 'Aktors indlæg', 'The prosecutor’s submission'),
    (4, None, r'Kamps indlæg, dateret (\d+)\. april', 'Defensors indlæg', 'The defence submission'),
    (4, 11, r'den 11\. april kl', 'Domsforhandlingen', 'The trial'),
    (4, 14, r'mandag den 14\. april', 'Dommen', 'The judgment'),
    (4, 15, r'den 15\. april, forkyndte', 'Dommen forkyndt for Thomas', 'The judgment served on Thomas'),
    (4, 19, r'Den 19\. april gik', '— og for Kristine Oline', '— and on Kristine Oline'),
]
MONTHS = {2: ('Februar', 'February'), 3: ('Marts', 'March'), 4: ('April', 'April')}
WD = (('M', 'T', 'O', 'T', 'F', 'L', 'S'), ('M', 'T', 'W', 'T', 'F', 'S', 'S'))
MONTH_SHORT = {2: ('feb.', 'Feb'), 3: ('mar.', 'Mar'), 4: ('apr.', 'Apr')}
_CACHE = {}


def _stations(col):
    return [c for c in col.find_all('div', recursive=False) if 'bt-acc' in (c.get('class') or []) and 'display:flex' in (c.get('style') or '')]


def _calendar(ed, sec, col):
    import datetime
    L = ed.lang
    li = 0 if L == 'da' else 1
    paras = sec.find_all('p')
    if L == 'da':
        found = []
        for mo, day, pat, da, en in CAL:
            for i, p in enumerate(paras):
                if p.find_parent('details'):
                    continue
                m = _re.search(pat, p.get_text(' ', strip=True))
                if m:
                    d = day if day else int(m.group(1))
                    found.append((mo, d, i, da, en))
                    break
        st = _stations(col)
        labels = [x.get_text(' ', strip=True) for x in st]
        a = next(i for i, t in enumerate(labels) if t.startswith('14. december 1912'))
        b = next(i for i, t in enumerate(labels) if t.startswith('15. november 1913'))
        _CACHE['cal'] = (found, a, b)
    found, a, b = _CACHE['cal']
    s = ed.soup
    events = {}
    for mo, d, i, da, en in found:
        key = f'{mo:02d}{d:02d}'
        p = paras[i]
        if not p.get('id'):
            p['id'] = 'dag-' + key
        p['data-day'] = (p.get('data-day', '') + ' ' + key).strip()
        events[key] = (mo, d, p['id'], da if L == 'da' else en)
    # wrap the stations from January—February 1913 up to the sentence into a two-column run
    st = _stations(col)
    first, stop = st[a], st[b]
    run = s.new_tag('div', attrs={'class': 'case-run run b w-wide'})
    main = s.new_tag('div', attrs={'class': 'case-main'})
    first.insert_before(run)
    node = run.next_sibling
    while node is not None and node is not stop:
        nxt = node.next_sibling
        main.append(node.extract())
        node = nxt
    run.append(main)
    ui = ed.ui
    months = []
    for mo in (2, 3, 4):
        first_wd = datetime.date(1913, mo, 1).weekday()
        ndays = (datetime.date(1913, mo + 1, 1) - datetime.timedelta(days=1)).day
        cells = ''.join(f'<span class="cal-w">{w}</span>' for w in WD[li])
        cells += '<span class="cal-x"></span>' * first_wd
        for d in range(1, ndays + 1):
            k = f'{mo:02d}{d:02d}'
            if k in events:
                cells += f'<a class="cal-d ev" href="#{events[k][2]}" data-day="{k}" title="{_E(events[k][3])}">{d}</a>'
            else:
                wd = datetime.date(1913, mo, d).weekday()
                cells += f'<span class="cal-d{" sun" if wd == 6 else ""}">{d}</span>'
        months.append(f'<div class="cal-m" data-mo="{mo:02d}"><div class="cal-mh m-s uc">{MONTHS[mo][li]} 1913</div><div class="cal-g">{cells}</div></div>')
    items = ''.join(
        f'<li><a href="#{ev[2]}" data-day="{k}"><span class="d">{ev[1]}. {MONTH_SHORT[ev[0]][0]}</span><span class="t">{_E(ev[3])}</span></a></li>' if L == 'da' else
        f'<li><a href="#{ev[2]}" data-day="{k}"><span class="d">{ev[1]} {MONTH_SHORT[ev[0]][1]}</span><span class="t">{_E(ev[3])}</span></a></li>'
        for k, ev in sorted(events.items()))
    aside = BeautifulSoupFragment(s, f'<aside class="case-cal" data-scene="calendar" data-mo="02" aria-label="{_E(ui["case_calendar"])}">{_route_markup(ed, "route-side")}<div class="cal-in"><div class="m-s uc c-acc cal-t">{_E(ui["case_calendar"])}</div><div class="cal-months">{"".join(months)}</div><div class="cal-now t-s" aria-live="polite"></div><ol class="cal-list">{items}</ol></div></aside>')
    run.append(aside)


def BeautifulSoupFragment(soup, markup):
    from bs4 import BeautifulSoup
    frag = BeautifulSoup(markup, 'html.parser')
    return frag.contents[0]


# ---- the road from Årgab to Vridsløselille
ROUTE_VIEW = '624 344 412 292'
ROUTE_PTS = {'aargab': (675.2, 414.9), 'kiel': (811.1, 611.0), 'vamdrup': (754.2, 480.5), 'koebenhavn': (979.0, 450.8),
             'ringkoebing': (683.3, 400.3), 'vridsloeselille': (962.5, 451.7)}
ROUTE = [  # from, to, Danish date, English date, bend
    ('aargab', 'kiel', '14. december 1912', '14 December 1912', -.12),
    ('kiel', 'vamdrup', 'mellem jul og nytår', 'between Christmas and New Year', .1),
    ('vamdrup', 'koebenhavn', 'ved nytårstid', 'around New Year', -.1),
    ('koebenhavn', 'ringkoebing', '21.—24. februar 1913', '21—24 February 1913', .1),
    ('ringkoebing', 'vridsloeselille', '3. juli 1913', '3 July 1913', -.07),
]
ROUTE_NAMES = {'aargab': 'Årgab', 'kiel': 'Kiel', 'vamdrup': 'Vamdrup', 'koebenhavn': ('København', 'Copenhagen'),
               'ringkoebing': ('Ringkøbing', 'Ringkøbing'), 'vridsloeselille': 'Vridsløselille'}
LABEL_POS = {'aargab': (-7, 9, 'end'), 'kiel': (0, 13, 'middle'), 'vamdrup': (-7, 3, 'end'), 'koebenhavn': (4, 13, 'start'),
             'ringkoebing': (-7, -3, 'end'), 'vridsloeselille': (-5, -8, 'end')}


def _name(k, li):
    v = ROUTE_NAMES[k]
    return v if isinstance(v, str) else v[li]


LEG_PAT = [r'^Den 14\. december 1912 forlod', r'^Politirapporten i straffeakten fortæller', r'^Politirapporten i straffeakten fortæller',
           r'^Den 24\. februar kl', r'^I Vridsløselille blev sagen']


def _route_markup(ed, cls):
    L = ed.lang
    li = 0 if L == 'da' else 1
    legs, stops, items = [], [], []
    for i, (a, b, dd, de, bend) in enumerate(ROUTE):
        (x1, y1), (x2, y2) = ROUTE_PTS[a], ROUTE_PTS[b]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        cx, cy = mx - dy * bend, my + dx * bend
        legs.append(f'<path class="leg" pathLength="1" data-i="{i}" d="M{x1},{y1} Q{cx:.1f},{cy:.1f} {x2},{y2}"/>')
        items.append(f'<li data-i="{i}"><span class="d">{_E(dd if L == "da" else de)}</span><span class="t">{_E(_name(a, li))} → {_E(_name(b, li))}</span></li>')
    for i, k in enumerate(['aargab', 'kiel', 'vamdrup', 'koebenhavn', 'ringkoebing', 'vridsloeselille']):
        x, y = ROUTE_PTS[k]
        ox, oy, anc = LABEL_POS[k]
        stops.append(f'<g class="stop" data-i="{i}"><circle cx="{x}" cy="{y}" r="2.6"/><text x="{x + ox}" y="{y + oy}" text-anchor="{anc}">{_E(_name(k, li))}</text></g>')
    title = ed.ui['case_route']
    hidden = ' aria-hidden="true"' if 'route-side' in cls else ''
    return (f'<figure class="route {cls}" data-scene="route"{hidden}>'
            f'<div class="m-s uc c-acc route-t">{_E(title)}</div>'
            f'<svg viewBox="{ROUTE_VIEW}" role="img" aria-label="{_E(title)}"><use href="#silk-land" class="land"/>'
            f'<g class="legs">{"".join(legs)}</g><g class="stops">{"".join(stops)}</g><circle class="here" r="4" cx="-20" cy="-20"/></svg>'
            f'<ol class="route-legs">{"".join(items)}</ol></figure>')


def _route(ed, col):
    s = ed.soup
    st = _stations(col)
    head = st[1]  # 14 December 1912 — the flight
    after = head.find_next_sibling('p')
    (after or head).insert_after(BeautifulSoupFragment(s, _route_markup(ed, 'route-inline')))
    # the paragraphs that tell each leg of the journey (found in Danish, the same places in English)
    ps = [p for p in col.find_all('p', recursive=False)]
    if ed.lang == 'da':
        idx = []
        for k, pat in enumerate(LEG_PAT):
            i = next((j for j, p in enumerate(ps) if _re.search(pat, p.get_text(' ', strip=True))), None)
            idx.append(i)
        _CACHE['legs'] = idx
    for k, i in enumerate(_CACHE.get('legs', [])):
        if i is not None:
            ps[i]['data-leg'] = (ps[i].get('data-leg', '') + ' ' + str(k)).strip()


def case_file(ed):
    sec = ed.byid.get('kap12')
    if sec is None:
        return
    col = next((d for d in sec.find_all('div') if len(_stations(d)) >= 5), None)
    if col is None:
        return
    dts = [dt for dt in sec.find_all('details') if dt.find('summary') and '·' in dt.find('summary').get_text() and dt.find('p')]
    dts = [dt for dt in dts if not dt.find_parent('details')][-len(_LT):]
    for dt, T in zip(dts, _LT):
        _light_table(ed, dt, T)
    _route(ed, col)
    _calendar(ed, sec, col)


# ------------------------------------------------------------------------------------------ chapter 5: 9 November 1878
def storm(ed):
    sec = ed.byid.get('kap5')
    if sec is None:
        return
    s = ed.soup
    ui = ed.ui
    # 1. rain and lightning behind the chapter head (decoration only)
    sky = BeautifulSoupFragment(s, '<div class="storm-sky" data-scene="storm" aria-hidden="true"><canvas></canvas></div>')
    sec.insert(0, sky)
    # 2. the cross-section of the beach, sticky beside the three paragraphs that tell the capsizing
    lab = next((d for d in sec.find_all('div') if d.get_text(strip=True) in ('Seks mand · én båd', 'Six men · one boat') and not d.find('div')), None)
    if lab is None:
        return
    paras = []
    n = lab.find_next_sibling()
    while n is not None and len(paras) < 3:
        if getattr(n, 'name', None) == 'p':
            paras.append(n)
        n = n.find_next_sibling()
    E = _E
    svg = f"""<figure class="xsec" data-scene="xsec" aria-hidden="true"><svg viewBox="0 0 1000 250" preserveAspectRatio="xMidYMid meet">
<defs><linearGradient id="xs-sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--acc)" stop-opacity=".22"/><stop offset="1" stop-color="var(--acc)" stop-opacity=".05"/></linearGradient></defs>
<path class="xs-water" d="M0,118 L1000,118 L1000,250 L0,250 Z" fill="url(#xs-sea)"/>
<path class="xs-bed" d="M0,244 C120,236 220,178 330,152 C390,140 420,196 470,198 C540,200 580,150 640,146 C690,143 700,176 740,172 C780,168 800,126 830,118 C860,110 880,86 905,72 C930,58 960,56 1000,60 L1000,250 L0,250 Z"/>
<path class="xs-surf" d="M0,118 L1000,118"/>
<g class="xs-lab"><text x="330" y="222" text-anchor="middle">{E(ui['sec_outer'])}</text><text x="640" y="214" text-anchor="middle">{E(ui['sec_inner'])}</text></g>
<g class="xs-station"><path d="M930,56 l11,-9 l11,9 v10 h-22 z"/><text x="994" y="34" text-anchor="end">{E(ui['sec_station'])}</text></g>
<path class="xs-breaker" d="M560,118 C585,118 600,100 612,82 C624,64 648,62 656,76 C642,70 632,78 636,92 C642,108 664,116 690,118 Z"/>
<g class="xs-boat"><path d="M-16,-3 L16,-3 L11,5 L-11,5 Z"/><path d="M-6,-3 L-6,-9 M3,-3 L3,-8" class="xs-crew"/></g>
<path class="xs-rocket r1" pathLength="1" d="M846,106 Q760,-6 668,104"/>
<path class="xs-rocket r2" pathLength="1" d="M846,106 Q748,10 650,110"/>
<text class="xs-clock" x="24" y="40">{E(ui['sec_clock'])}</text>
<text class="xs-rk" x="748" y="16" text-anchor="middle">{E(ui['sec_rockets'])}</text>
</svg></figure>"""
    run = s.new_tag('div', attrs={'class': 'xsec-run'})
    paras[0].insert_before(run)
    run.append(BeautifulSoupFragment(s, svg))
    for p in paras:
        run.append(p.extract())
    # 3. the five names, read out one by one
    names = [d for d in sec.find_all('div') if 'bb-acc' in (d.get('class') or []) and not d.find('div')]
    if names:
        box = names[0].parent
        box['data-scene'] = 'register'
        for d in names:
            d['class'] = (d.get('class') or []) + ['nm']


# ------------------------------------------------------------------------------------------ chapter 17: the crossing in 1945
CHART_PTS = {'esbjerg': (697.3, 475.7), 'osp': (251.7, 619.5), 'hvidesande': (675.4, 411.5), 'thyboroen': (680.9, 325.3)}


def crossing(ed):
    sec = ed.byid.get('kap17')
    if sec is None:
        return
    s = ed.soup
    labs = [d for d in sec.find_all('div') if 'm-s' in (d.get('class') or []) and 'c-acc' in (d.get('class') or []) and not d.find('div')]
    if len(labs) < 6:
        return
    first, last = labs[0], labs[-1]
    anc = [first] + list(first.parents)
    cont = next(a for a in anc[1:] if last in a.descendants)
    top_first = next(a for a in anc if a.parent is cont)
    top_last = next(a for a in [last] + list(last.parents) if a.parent is cont)
    run = s.new_tag('div', attrs={'class': 'cross-run'})
    main = s.new_tag('div', attrs={'class': 'cross-main'})
    if cont.name in ('ol', 'ul'):
        # the dated entries are one list: the list moves into the run whole
        cont.insert_before(run)
        main.append(cont.extract())
        if cont.get('style'):
            cont['style'] = _re.sub(r'max-width:[^;]+;?', '', cont['style']).strip(';') or None
            if cont['style'] is None:
                del cont['style']
    else:
        top_first.insert_before(run)
        node = run.next_sibling
        while node is not None:
            nxt = node.next_sibling
            main.append(node.extract())
            if node is top_last:
                break
            node = nxt
    for i, l in enumerate(labs):
        l['data-leg'] = str(i)
    import chart_art as CA
    chart = CA.chart_svg(ed.lang, _E(ed.ui['chart_title']))
    run.append(main)
    run.append(BeautifulSoupFragment(s, chart))
