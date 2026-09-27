"""Re-typesetting: every chapter's classic markup (nested layout wrappers with inline widths) is turned into one flat
sequence of typed blocks on the book grid. Nothing is added to or removed from the text: elements are only unwrapped,
moved into the chapter head, or given a block type and a placement.

Block types (class "b b-<type>") and placements (class "w-<place>"):
  p       paragraph (the first becomes the lead)          text
  h       sub-heading, often with a date label             text
  label   a small label line before what follows            text
  quote   quotation                                         text
  fig     one figure                                        side | text | wide | full
  gallery several figures in a row                          wide
  cards   person cards                                      wide
  box     a framed box (lists, facts, genealogy)            text | wide
  doc     a transcript or other "read more" (details)       text | wide
  grid    a table-like grid of cells                         wide
  scene   a scene built by scenes_ny                         wide | full
"""
import re

from bs4 import NavigableString, Tag

from convert import style_dict, style_str

SURF = {'sf', 'sf2', 'sf-d', 'sf-grad', 'bx', 'bx2', 'bx3', 'bx-d', 'bl', 'bl2', 'bl3', 'bt', 'bb', 'br', 'bt2', 'bt3',
        'bb2', 'bb3', 'shd'}
TYPO = re.compile(r'^(t|t-l|t-s|t-xs|t-xxs|lead|h-s|h-m|h-l|disp|m|m-s|m-xs|m-l|uc|serif|h2|h2-s|h3)$')
BLOCK = {'p', 'div', 'figure', 'blockquote', 'details', 'ul', 'ol', 'table', 'h2', 'h3', 'h4', 'a', 'aside', 'section',
         'dl', 'img', 'svg'}
INLINE = {'span', 'a', 'em', 'strong', 'b', 'i', 'br', 'sup', 'sub', 'button', 'small', 'abbr', 'time', 'u', 's'}
LAYOUT_KEYS = {'max-width', 'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right', 'margin-inline',
               'margin-block', 'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
               'padding-inline', 'padding-block', 'display', 'grid-template-columns', 'gap', 'row-gap', 'column-gap',
               'align-items', 'justify-content', 'position', 'flex-direction', 'flex-wrap', 'width', 'min-width',
               'grid-template-rows', 'align-content', 'text-align'}
YEAR = re.compile(r'\b(1[6-9]\d\d|20[0-2]\d)\b')


def kids(el):
    return [c for c in el.children if isinstance(c, Tag)]


def cls(el):
    return set(el.get('class') or [])


def st(el):
    return dict(style_dict(el.get('style', '')))


def has_own_text(el):
    return any(isinstance(c, NavigableString) and c.strip() for c in el.children)


def is_grid(el):
    s = st(el)
    return s.get('display') in ('grid', 'flex', 'inline-grid', 'inline-flex')


def cols_of(el):
    s = st(el)
    g = s.get('grid-template-columns', '')
    if 'repeat(' in g:
        m = re.search(r'repeat\((\d+)', g)
        return int(m.group(1)) if m else 2
    return len([x for x in re.split(r'\s+(?![^(]*\))', g.strip()) if x]) if g else (2 if s.get('display') == 'flex' and s.get('flex-direction') != 'column' else 1)


def figureish(el):
    if el.name == 'figure':
        return True
    if el.name == 'div' and not has_own_text(el):
        k = kids(el)
        return len(k) >= 1 and all(figureish(x) or x.name == 'img' for x in k)
    return False


def textual(el):
    """A text-only element: typographic class and inline content only."""
    if el.name not in ('div', 'p', 'span'):
        return False
    return all(c.name in INLINE for c in kids(el))


def is_wrapper(el):
    if el.name not in ('div', 'section') or el.get('id') or el.has_attr('data-scene') or el.has_attr('data-pan') or el.has_attr('data-fade'):
        return False
    c = cls(el)
    if c & SURF or any(TYPO.match(x) for x in c) or c - {'rv'}:
        return False
    if has_own_text(el):
        return False
    k = kids(el)
    if not k or not all(x.name in BLOCK for x in k):
        return False
    s = st(el)
    if any(key not in LAYOUT_KEYS for key in s):
        return False
    if is_grid(el) and s.get('flex-direction') != 'column':
        # a row of figures or of person cards is a component; text beside a figure is only layout
        if all(figureish(x) for x in k) or all(x.name == 'a' and 'pn-card' in cls(x) for x in k):
            return False
        has_fig = any(figureish(x) for x in k)
        texty = [x for x in k if not figureish(x)]
        if has_fig and texty and all(x.name == 'div' and len(x.get_text(strip=True)) > 200 or x.name in ('p', 'blockquote') for x in texty):
            return True
        if all(x.name == 'div' and len(kids(x)) > 1 and len(x.get_text(strip=True)) > 400 for x in k):
            return True  # parallel columns of running text
        return False
    return True


def flatten(el):
    out = []
    for c in list(el.children):
        if isinstance(c, NavigableString):
            if c.strip():
                out.append(c)
            continue
        if not isinstance(c, Tag):
            continue
        if is_wrapper(c):
            out.extend(flatten(c))
        elif is_section(c):
            inner = flatten(c)
            first = next((x for x in inner if isinstance(x, Tag)), None)
            if first is not None:
                add(first, 'b-rule')
            out.extend(inner)
        else:
            out.append(c)
    return out


def is_section(el):
    """A ruled run of paragraphs (a border on top and nothing else): the rule stays, the frame goes."""
    if el.name != 'div' or el.get('id') or el.has_attr('data-scene'):
        return False
    c = cls(el) - {'bt-acc', 'bb-acc'}
    if not c or not c <= {'bt', 'bt2', 'bt3'}:
        return False
    k = kids(el)
    return len(k) >= 3 and sum(1 for x in k if x.name == 'p') >= 2 and not has_own_text(el) and not is_grid(el)


def classify(el):
    """(type, placement) for one block."""
    if isinstance(el, NavigableString):
        return 'p', 'text'
    c = cls(el)
    t = el.get_text(' ', strip=True)
    if el.has_attr('data-scene') or c & {'xsec-run', 'cross-run', 'case-run', 'storm-sky', 'route', 'lt'}:
        return 'scene', 'wide'
    if el.name == 'p':
        return 'p', 'text'
    if el.name in ('h3', 'h4'):
        return 'h', 'text'
    if el.name == 'blockquote':
        return 'quote', 'text'
    if el.name == 'figure':
        return 'fig', fig_place(el)
    if el.name == 'details':
        sm = el.find('summary')
        return 'doc', 'text'
    if el.name in ('ul', 'ol', 'dl'):
        return 'list', 'text'
    if el.name == 'table':
        return 'grid', 'wide'
    if el.name == 'a' and 'pn-card' in c:
        return 'cards', 'text'
    if el.name == 'div':
        k = kids(el)
        if k and all(x.name == 'a' and 'pn-card' in cls(x) for x in k):
            return 'cards', 'wide' if len(k) > 1 else 'text'
        if k and all(figureish(x) for x in k):
            return 'gallery', 'wide'
        if len(k) == 1 and k[0].name == 'details':
            return 'doc', 'text'
        if textual(el) and len(t) < 140 and (c & {'uc', 'm-s', 'm', 'm-xs'}):
            return 'label', 'text'
        if textual(el):
            return 'p', 'text'
        heads = el.find_all(lambda x: isinstance(x, Tag) and (x.name in ('h3', 'h4') or cls(x) & {'h-s', 'h-m', 'h-l'}))
        if heads and len(t) < 140 and not el.find(['p', 'figure', 'img']):
            return 'h', 'text'
        if is_grid(el) and cols_of(el) >= 2:
            return 'grid', 'wide'
        if c & SURF:
            return 'box', 'wide' if el.find(lambda x: isinstance(x, Tag) and is_grid(x) and cols_of(x) >= 3) else 'text'
        return 'box', 'text'
    return 'box', 'text'


def img_of(fig):
    return fig.find('img')


def fig_place(fig):
    im = img_of(fig)
    if im is None:
        return 'text'
    try:
        w, h = int(im.get('width') or 0), int(im.get('height') or 0)
    except ValueError:
        w = h = 0
    if not w or not h:
        return 'text'
    ar = w / h
    if w < 520 and ar < 1.25:
        return 'side'
    if ar >= 2.2:
        return 'wide'
    if ar >= 1.25 and w >= 1000:
        return 'wide'
    return 'text'


def add(el, *names):
    el['class'] = list(dict.fromkeys((el.get('class') or []) + list(names)))


def strip_layout(el):
    """Inline widths and margins belong to the old page grid; the block's placement replaces them."""
    s = [(k, v) for k, v in style_dict(el.get('style', '')) if k not in ('max-width', 'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right', 'width')]
    if s:
        el['style'] = style_str(s)
    elif el.has_attr('style'):
        del el['style']


# ---------------------------------------------------------------------------------------------- the whole chapter
KICK = re.compile(r'^(Kapitel|Appendiks|Chapter|Appendix)\b')
PORTRAIT = re.compile(r'^(Portræt|Atelierportræt|Portrait|Studio portrait)', re.I)


def refine(el, ty, pl):
    """Second look at a block with the neighbours' context known."""
    if isinstance(el, NavigableString):
        return ty, pl
    c = cls(el)
    t = el.get_text(' ', strip=True)
    if ty == 'p' and el.name == 'div' and c & {'h-s', 'h-m', 'h-l'} and len(t) < 80:
        return 'h', 'text'
    if ty == 'h' and is_grid(el) and len(kids(el)) >= 3:
        return 'grid', 'wide'
    if ty == 'p' and not t and not el.find(['img', 'svg', 'canvas']):
        return 'deco', 'text'
    if ty == 'fig':
        im = el.find('img')
        if im is not None and PORTRAIT.match(im.get('alt') or ''):
            return 'fig', 'side'
    return ty, pl


def p_role(el):
    """Paragraph roles on one scale: body, lead, a big one-line beat, or small print."""
    c = cls(el)
    if c & {'lead'}:
        return 'lead'
    if c & {'h-s', 'h-m', 'h-l', 'disp'}:
        return 'beat'
    if c & {'t-s', 't-xs', 't-xxs'}:
        return 'small'
    return 'body'


def typeset(ed, it):
    s = ed.soup
    sec = it['el']
    blocks = [b for b in flatten(sec) if not (isinstance(b, NavigableString) and not b.strip())]
    kick = next((b for b in blocks[:4] if isinstance(b, Tag) and b.name == 'div' and KICK.match(b.get_text(' ', strip=True))), None)
    title = next((b for b in blocks[:5] if isinstance(b, Tag) and b.name == 'h2'), None)
    head = s.new_tag('header', attrs={'class': 'ch-head'})
    num = s.new_tag('div', attrs={'class': 'ch-no', 'aria-hidden': 'true'})
    num.string = str(it['n'])
    head.append(num)
    if kick is not None:
        kick.extract()
        kick['class'] = ['ch-kick']
        strip_layout(kick)
        head.append(kick)
    if title is not None:
        title.extract()
        title.name = 'h1'
        title['class'] = ['ch-title']
        strip_layout(title)
        words = re.findall(r'\S+', title.get_text(' ', strip=True))
        title['style'] = f'--lw:{max((len(w) for w in words), default=8)};--tl:{len(title.get_text(" ", strip=True))}'
        head.append(title)
    flow = s.new_tag('div', attrs={'class': 'flow'})
    first_p = True
    for b in blocks:
        if b is kick or b is title:
            continue
        if isinstance(b, NavigableString):
            p = s.new_tag('p')
            p.string = str(b).strip()
            b.replace_with(p)
            b = p
        ty, pl = refine(b, *classify(b))
        b.extract()
        if ty == 'deco':
            continue
        strip_layout(b)
        names = ['b', 'b-' + ty, 'w-' + pl]
        if ty == 'p':
            role = p_role(b)
            if first_p and role in ('body', 'lead', 'beat') and b.name == 'p':
                role = 'lead'
            first_p = False
            names.append('p-' + role)
            b['class'] = [x for x in (b.get('class') or []) if not TYPO.match(x) and x not in ('c-mut', 'c-mut2', 'w3')] 
        add(b, *names)
        flow.append(b)
    # notes in running text move to the margin where there is one
    for n in flow.find_all('span', class_='note'):
        blk = n.find_parent(lambda x: isinstance(x, Tag) and 'b' in (x.get('class') or []))
        if blk is not None and ('b-p' in blk['class'] or 'b-list' in blk['class']):
            add(n, 'sn')
    for c in list(sec.contents):
        c.extract()
    sec.append(head)
    sec.append(flow)
    it['head'] = head
    it['flow'] = flow
    return flow
