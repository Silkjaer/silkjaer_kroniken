"""Read the original chronicle (index.html) and turn it into clean, static section fragments.

The original is an x-dc page: React-rendered templates ({{ }}, <sc-for>, <sc-if>), inline click handlers
and data tables in a script. This module renders all of that at build time, so the immersive edition
ships every word as plain HTML (readable without JavaScript, indexable, printable).
"""
import html as H
import json
import re
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

FONT_SUBS = [
    (re.compile(r"'IBM Plex Mono',\s*monospace"), 'var(--mono)'),
    (re.compile(r"'Newsreader',\s*Georgia,\s*serif"), 'var(--serif)'),
    (re.compile(r"'Newsreader',\s*serif"), 'var(--serif)'),
]
REVEAL_PROPS = ('opacity', 'transform', 'transition')


def style_dict(st):
    out = []
    for part in (st or '').split(';'):
        if ':' not in part:
            continue
        k, v = part.split(':', 1)
        out.append((k.strip(), v.strip()))
    return out


def style_str(pairs):
    return ';'.join(f'{k}:{v}' for k, v in pairs if k)


def load(path):
    src = open(path, encoding='utf-8').read()
    b0 = src.index('<header')
    b1 = src.index('<sc-if value="{{ zoom }}"')
    body = src[b0:b1]
    return src, body


class Converter:
    def __init__(self, data, img_base='billeder/'):
        self.data = data
        self.img_base = img_base
        self.note_n = 0
        self.hover_css = {}

    # ---------- templates ----------
    def render_templates(self, soup):
        """Expand <sc-for>/<sc-if> and {{ x.y }} placeholders with the data tables."""
        lists = {
            'mandskab': self.data['MANDSKAB'],
            'forbehold': self.data['FORBEHOLD'],
            'kilder': self.data['KILDER'],
            'billeder': self.data['BILLEDER'],
        }
        for loop in soup.find_all('sc-for'):
            name = re.search(r'\{\{\s*(\w+)\s*\}\}', loop['list']).group(1)
            var = loop['as']
            tpl = ''.join(str(c) for c in loop.contents)
            parts = []
            for item in lists[name]:
                parts.append(self._fill(tpl, var, item))
            frag = BeautifulSoup(''.join(parts), 'html.parser')
            loop.replace_with(frag)
        return soup

    def _fill(self, tpl, var, item):
        # sc-if blocks inside the loop template
        def ifrep(m):
            key = m.group(1)
            inner = m.group(2)
            return inner if item.get(key) else ''
        t = re.sub(r'<sc-if value="\{\{\s*' + var + r'\.(\w+)\s*\}\}"[^>]*>(.*?)</sc-if>', ifrep, tpl, flags=re.S)

        def rep(m):
            v = item.get(m.group(1), '')
            return H.escape(str(v), quote=True)
        return re.sub(r'\{\{\s*' + var + r'\.(\w+)\s*\}\}', rep, t)

    # ---------- element clean-up ----------
    def clean_styles(self, soup):
        for el in soup.find_all(True):
            if el.has_attr('data-reveal'):
                del el['data-reveal']
                el['data-rv'] = ''
                if el.has_attr('style'):
                    el['style'] = style_str([(k, v) for k, v in style_dict(el['style']) if k not in REVEAL_PROPS])
            if el.has_attr('style'):
                st = el['style']
                for rx, rep in FONT_SUBS:
                    st = rx.sub(rep, st)
                el['style'] = st
                if not st.strip():
                    del el['style']
            if el.has_attr('style-hover'):
                hv = el['style-hover']
                for rx, rep in FONT_SUBS:
                    hv = rx.sub(rep, hv)
                cls = self.hover_css.setdefault(hv, f'hv{len(self.hover_css) + 1}')
                el['class'] = (el.get('class') or []) + [cls]
                del el['style-hover']
            for a in list(el.attrs):
                if a.startswith('hint-placeholder') or a == 'onclick' or a == 'oninput':
                    del el[a]
            if el.name == 'img':
                src = el.get('src', '')
                if src.startswith('billeder/'):
                    el['src'] = self.img_base + src[len('billeder/'):]
        return soup

    def persons(self, soup):
        for b in soup.find_all('button', attrs={'data-person': True}):
            key = b['data-person']
            a = soup.new_tag('a')
            a['href'] = f'#person-{key}'
            a['data-person'] = key
            inline_only = all(isinstance(c, NavigableString) or c.name in ('span', 'em', 'strong') for c in b.contents)
            if inline_only:
                a['class'] = ['pn']
            else:
                a['class'] = ['pn-card'] + [c for c in (b.get('class') or []) if c.startswith('hv')]
                if b.has_attr('style'):
                    a['style'] = b['style']
            for c in list(b.contents):
                a.append(c.extract())
            b.replace_with(a)
        return soup

    def notes(self, soup):
        """Forbehold/Kilde question marks + their hidden panel -> accessible note widgets."""
        for b in soup.find_all('button', attrs={'title': ['Forbehold', 'Kilde']}):
            kind = b['title']
            panel = b.find_next_sibling(attrs={'data-panel': True})
            self.note_n += 1
            nid = f'n{self.note_n}'
            nb = soup.new_tag('button')
            nb['type'] = 'button'
            nb['class'] = ['q']
            nb['aria-expanded'] = 'false'
            nb['aria-controls'] = nid
            nb['data-kind'] = 'forbehold' if kind == 'Forbehold' else 'kilde'
            nb['aria-label'] = kind
            nb.string = '?' if kind == 'Forbehold' else (b.get_text(strip=True) or 'i')
            b.replace_with(nb)
            if panel is not None:
                panel.name = 'span'
                del panel['data-panel']
                panel['class'] = ['note']
                panel['id'] = nid
                panel['role'] = 'note'
                if panel.has_attr('style'):
                    panel['style'] = style_str([(k, v) for k, v in style_dict(panel['style']) if k != 'display'])
        return soup

    def toggles(self, soup):
        """'Læs mere'-knapper (+) med et skjult panel -> <details>/<summary>."""
        for b in soup.find_all('button'):
            if b.get('data-kind') or b.has_attr('data-pan-btn') or b.get('class') and 'q' in b.get('class'):
                continue
            if b.get('type') != 'button':
                continue
            panel = b.find_next_sibling(attrs={'data-panel': True})
            if panel is None:
                continue
            det = soup.new_tag('details')
            det['class'] = ['more']
            summ = soup.new_tag('summary')
            if b.has_attr('style'):
                summ['style'] = b['style']
            for c in list(b.contents):
                # drop the literal "+" indicator span; CSS draws the state
                if isinstance(c, Tag) and c.name == 'span' and c.get_text(strip=True) in ('+', '−'):
                    c.decompose()
                    continue
                summ.append(c.extract())
            summ.append(soup.new_tag('i', attrs={'class': 'pm', 'aria-hidden': 'true'}))
            b.insert_before(det)
            b.extract()
            panel.extract()
            del panel['data-panel']
            if panel.has_attr('style'):
                panel['style'] = style_str([(k, v) for k, v in style_dict(panel['style']) if k != 'display'])
                if not panel['style']:
                    del panel['style']
            det.append(summ)
            det.append(panel)
        return soup

    def misc(self, soup):
        for b in soup.find_all('button', attrs={'data-goto': True}):
            a = soup.new_tag('a', href='#' + b['data-goto'])
            a['class'] = ['goto']
            for c in list(b.contents):
                a.append(c.extract())
            b.replace_with(a)
        for b in soup.find_all('button'):
            if b.has_attr('data-pan-btn') or b.get('data-kind') or 'q' in (b.get('class') or []):
                continue
            if 'Vis hvem der er hvem' in b.get_text():
                b['data-act'] = 'overlay'
                continue
            # a card styled as a button but without any action: keep the look, drop the role
            b.name = 'div'
            b['class'] = ['pn-card', 'is-static'] + [c for c in (b.get('class') or []) if c.startswith('hv')]
            for a in ('type',):
                if b.has_attr(a):
                    del b[a]
        return soup

    def counters(self, html):
        return (html.replace('{{ antalBilleder }}', str(len(self.data['BILLEDER'])))
                    .replace('{{ antalKilder }}', str(len(self.data['KILDER']))))

    def run(self, body_html):
        body_html = self.counters(body_html)
        soup = BeautifulSoup(body_html, 'html.parser')
        for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
            c.extract()
        self.render_templates(soup)
        self.clean_styles(soup)
        self.persons(soup)
        self.notes(soup)
        self.toggles(soup)
        self.misc(soup)
        return soup

    def hover_stylesheet(self):
        return '\n'.join(f'.{c}:hover{{{css}}}' for css, c in self.hover_css.items())


def split_blocks(soup):
    """Top-level pieces in reading order: header, sections, part dividers, footer."""
    blocks = []
    for el in soup.contents:
        if not isinstance(el, Tag):
            continue
        if el.name in ('nav',) or el.has_attr('data-locator') or el.has_attr('data-toc') or el.has_attr('data-progress'):
            continue
        if el.name == 'div' and el.has_attr('data-part'):
            blocks.append(('part', el))
        elif el.name == 'section':
            blocks.append(('section', el))
        elif el.name == 'header':
            blocks.append(('header', el))
        elif el.name == 'footer':
            blocks.append(('footer', el))
        else:
            blocks.append(('other', el))
    return blocks
