"""Split converted sections into translatable segments and put translations back.

A segment is the inline content of the lowest block that holds text. Inline tags are replaced by
numbered placeholders (<t1>…</t1>) so a translation can reorder them freely; note panels become
<nK/> markers and are translated as segments of their own. Segments are keyed by a hash of the
Danish source, so an edited Danish sentence shows up as untranslated instead of silently
keeping an outdated English version.
"""
import hashlib
import re
from bs4 import BeautifulSoup, NavigableString, Tag

INLINE = {'a', 'em', 'strong', 'b', 'i', 'span', 'sup', 'sub', 'br', 'small', 'code', 'button', 'u', 's'}
SKIP_TEXT = re.compile(r'^[\s\d.,:;·—–\-+→←↓↑()\[\]/%×∞?!»«"\'’]*$')


def is_note(el):
    return isinstance(el, Tag) and el.name == 'span' and 'note' in (el.get('class') or [])


def is_inline(el):
    if isinstance(el, NavigableString):
        return True
    if el.name not in INLINE:
        return False
    if is_note(el):
        return True  # handled as a placeholder
    if el.name == 'i' and 'pm' in (el.get('class') or []):
        return True
    # an inline tag that wraps block content is not inline for our purposes
    return all(is_inline(c) for c in el.children)


def has_text(el):
    if isinstance(el, NavigableString):
        return bool(el.strip())
    if is_note(el):
        return False
    return any(has_text(c) for c in el.children)


def seg_hash(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:12]


def norm_ws(s):
    return re.sub(r'\s+', ' ', s).strip()


class Segment:
    __slots__ = ('el', 'tags', 'notes', 'src', 'id', 'kind', 'attr')

    def __init__(self):
        self.tags = []
        self.notes = []


def encode(el):
    """Return (placeholder_text, tags, notes) for the inline children of el."""
    tags, notes = [], []

    def walk(node):
        out = []
        for c in node.children:
            if isinstance(c, NavigableString):
                out.append(str(c).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
            elif is_note(c):
                notes.append(c)
                out.append(f'<n{len(notes)}/>')
            elif c.name == 'br':
                out.append('<br/>')
            elif c.name == 'i' and 'pm' in (c.get('class') or []):
                tags.append(c)
                out.append(f'<t{len(tags)}/>')
            else:
                tags.append(c)
                k = len(tags)
                out.append(f'<t{k}>' + walk(c) + f'</t{k}>')
        return ''.join(out)

    return walk(el), tags, notes


def wrap_mixed(el, soup):
    """Wrap runs of inline content inside a block that also has block children."""
    runs, cur = [], []
    for c in list(el.children):
        if is_inline(c):
            cur.append(c)
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    for run in runs:
        if not any(has_text(c) for c in run):
            continue
        sp = soup.new_tag('span')
        sp['data-s'] = ''
        run[0].insert_before(sp)
        for c in run:
            sp.append(c.extract())


def collect(root, soup):
    """Find every segment under root (document order). Mutates root (wraps mixed runs)."""
    segs = []

    def visit(el):
        if isinstance(el, NavigableString):
            return
        if el.name in ('script', 'style', 'svg', 'canvas'):
            return
        if (el.get('aria-hidden') == 'true' and el.name != 'img') or el.has_attr('data-noseg'):
            return
        # attribute segments
        for attr in ('alt', 'aria-label'):
            v = el.get(attr)
            if v and not SKIP_TEXT.match(v) and not (el.name == 'button' and 'q' in (el.get('class') or [])):
                s = Segment()
                s.el, s.kind, s.attr = el, 'attr', attr
                s.src = norm_ws(v)
                s.id = seg_hash('@' + s.src)
                segs.append(s)
        if is_note(el):
            # the note itself is a block-ish container
            pass
        kids = list(el.children)
        if not kids:
            return
        inline_all = all(is_inline(c) for c in kids)
        if inline_all and not is_note_container_only(el):
            if any(has_text(c) for c in kids):
                s = Segment()
                s.el, s.kind, s.attr = el, 'html', None
                s.src, s.tags, s.notes = encode(el)
                s.src = norm_ws(s.src)
                if not SKIP_TEXT.match(re.sub(r'<[^>]+>', '', s.src)):
                    s.id = seg_hash(s.src)
                    segs.append(s)
                for n in s.notes:
                    visit(n)
            else:
                for c in kids:
                    if is_note(c):
                        visit(c)
            # attributes on inline descendants (e.g. img inside a span) still need visiting
            for d in el.find_all(True):
                for attr in ('alt', 'aria-label'):
                    v = d.get(attr)
                    if v and not SKIP_TEXT.match(v) and not (d.name == 'button' and 'q' in (d.get('class') or [])):
                        s2 = Segment()
                        s2.el, s2.kind, s2.attr = d, 'attr', attr
                        s2.src = norm_ws(v)
                        s2.id = seg_hash('@' + s2.src)
                        segs.append(s2)
            return
        if any(is_inline(c) and has_text(c) for c in kids):
            wrap_mixed(el, soup)
        for c in list(el.children):
            visit(c)

    visit(root)
    return segs


def is_note_container_only(el):
    return False


def decode(text, seg, soup):
    """Rebuild the inline children of seg.el from a translated placeholder string."""
    frag = BeautifulSoup('<x>' + text + '</x>', 'html.parser').x

    def build(node, parent):
        for c in list(node.children):
            if isinstance(c, NavigableString):
                parent.append(NavigableString(str(c)))
                continue
            m = re.fullmatch(r't(\d+)', c.name or '')
            n = re.fullmatch(r'n(\d+)', c.name or '')
            if c.name == 'br':
                parent.append(soup.new_tag('br'))
            elif m:
                orig = seg.tags[int(m.group(1)) - 1]
                new = soup.new_tag(orig.name, attrs=dict(orig.attrs))
                parent.append(new)
                if not (orig.name == 'i' and 'pm' in (orig.get('class') or [])):
                    build(c, new)
            elif n:
                parent.append(seg.notes[int(n.group(1)) - 1])
            else:
                raise ValueError(f'unexpected tag <{c.name}> in translation of {seg.id}')

    for n in seg.notes:
        n.extract()
    seg.el.clear()
    build(frag, seg.el)


def apply(segs, table, soup, missing):
    # notes first need translating inside, so process in reverse document order: children before parents
    for s in reversed(segs):
        tr = table.get(s.id)
        if tr is None:
            missing.append(s)
            continue
        if s.kind == 'attr':
            s.el[s.attr] = tr
        else:
            decode(tr, s, soup)
