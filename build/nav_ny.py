"""Navigation built from the chronicle itself: the timeline of chapters (1688 → today) and the family tree with every
person's life on the same time axis. Both are plain HTML lists, readable without script and in print."""
import html as H
import re

from ui_ny import CHAPTERS

A0, A1 = 1680, 2030          # the chapters' axis
P0, P1 = 1800, 2030          # the people's axis
TICKS = (1700, 1750, 1800, 1850, 1900, 1950, 2000)
PTICKS = (1800, 1850, 1900, 1950, 2000)
NOW = 2025

# the family, in the order of the tree: (person key, generation depth, spouse?)
TREE = [
    ('thomasjensen', 0, False), ('annemarie', 0, True),
    ('nielsthomsen', 1, False), ('anejohannek', 1, True), ('anejensen', 1, True),
    ('anemarie', 2, False),
    ('thomasns', 2, False), ('kristiane', 2, True), ('kristineoline', 3, False), ('arne', 3, False),
    ('anejohanne', 2, False), ('laura', 3, False),
    ('jensclaus', 2, False), ('bodilmarie', 2, True),
    ('esper', 2, False), ('karenmarie', 2, False), ('anekirstine', 2, False), ('sidsel', 2, False),
    ('jensine', 2, False), ('ellen', 2, False),
]


def esc(s):
    return H.escape(str(s or ''), quote=True)


def pct(y, a=A0, b=A1):
    return f'{(min(max(y, a), b) - a) / (b - a) * 100:.2f}%'


def years(txt):
    ys = [int(y) for y in re.findall(r'\b(1[6-9]\d\d|20[0-2]\d)\b', txt or '')]
    return (ys[0], ys[-1]) if ys else (None, None)


def span_label(a, b, today):
    if a == b:
        return str(a)
    return f'{a}—{today if b >= NOW else b}'


def chapter_numbers(txt):
    """'Kapitel 1—6 · nævnt igen i kapitel 9' → ([1..6], [9])"""
    main, _, rest = (txt or '').partition('·')

    def nums(t):
        out = []
        for a, b in re.findall(r'(\d+)(?:\s*[—–-]\s*(\d+))?', t):
            a = int(a)
            out.extend(range(a, int(b) + 1) if b else [a])
        return out
    m = nums(main)
    return m, [n for n in nums(rest) if n not in m]


def ticks_html(ticks, a, b, cls):
    return ''.join(f'<span class="{cls}" style="--x:{pct(t, a, b)}">{t}</span>' for t in ticks)


def timeline(site, e, path, current=None):
    u = e.ui
    rows = []
    for p in e.parts:
        chs = [it for it in p['items'] if not it['is_app']]
        if not chs:
            continue
        rows.append(f'<li class="tl-part"><span class="tl-pn">{esc(p["num"])}</span><span class="tl-pt">{esc(p["title"])}</span></li>')
        for it in chs:
            a, b = CHAPTERS[it['id']]['span']
            cur = ' aria-current="page"' if it['path'] == current and not it.get('host') else ''
            rows.append(
                f'<li><a class="tl-row" href="{site.rel(path, it["path"])}{"#" + it["id"] if it.get("host") else ""}" data-ch="{it["id"]}" style="--a:{pct(a)};--b:{pct(b)}"{cur}>'
                f'<span class="tl-n">{esc(it["n"])}</span><span class="tl-t">{esc(it["title"])}</span>'
                f'<span class="tl-bar" aria-hidden="true"><i></i></span><span class="tl-y">{span_label(a, b, u["today"])}</span></a></li>')
    apps = [it for it in e.pages if it['is_app']]
    CUR = ' aria-current="page"'
    app = ''.join(f'<li><a href="{site.rel(path, it["path"])}"{CUR if it["path"] == current else ""}><span class="tl-n">{esc(it["n"])}</span><span class="tl-t">{esc(it["title"])}</span></a></li>' for it in apps)
    return (f'<div class="tl">'
            f'<div class="tl-axis" aria-hidden="true"><span class="tl-sp"></span><span class="tl-ticks">{ticks_html(TICKS, A0, A1, "tk")}</span></div>'
            f'<ol class="tl-rows">{"".join(rows)}</ol>'
            f'<div class="tl-apps"><div class="m-s uc c-acc">{esc(u["appendices"])}</div><ol>{app}</ol></div></div>')


def family(site, e, path):
    u = e.ui
    P = e.data_people
    by_n = {str(it['n']): it for it in e.pages if not it['is_app']}
    card = next(it for it in e.pages if it['id'] == 'stamtavle')
    rows = []
    for key, depth, spouse in TREE:
        pr = P.get(key)
        if not pr:
            continue
        a, b = years(pr['leve'])
        if a and b == a:
            b = None
        kap = next((f['v'] for f in pr.get('facts', []) if f['k'] in ('Kapitler', 'Chapters')), '')
        main, more = chapter_numbers(kap)
        chips = ''.join(
            f'<a class="ft-c{" m" if n in main else ""}" href="{site.rel(path, by_n[str(n)]["path"])}{"#" + by_n[str(n)]["id"] if by_n[str(n)].get("host") else ""}" title="{esc(e.ui["chapter"])} {n}: {esc(by_n[str(n)]["title"])}">{n}</a>'
            for n in sorted(set(main + more)) if str(n) in by_n)
        href = site.rel(path, card['path']) + '#person-' + key
        rows.append(
            f'<li class="ft-row{" sp" if spouse else ""}" style="--i:{depth};--a:{pct(a or P0, P0, P1)};--b:{pct(b or a or P0, P0, P1)}">'
            f'<span class="ft-who"><a class="ft-name pn" data-person="{key}" href="{href}">{esc(pr["navn"])}</a><span class="ft-role">{esc(pr["rolle"])}</span></span>'
            f'<span class="ft-bar" aria-hidden="true"><i></i></span><span class="ft-y">{esc(pr["leve"])}</span>'
            f'<span class="ft-ch" aria-label="{esc(e.ui["chapters"])}">{chips}</span></li>')
    return (f'<div class="ft">'
            f'<div class="ft-axis" aria-hidden="true"><span class="ft-sp"></span><span class="ft-ticks">{ticks_html(PTICKS, P0, P1, "tk")}</span></div>'
            f'<ol class="ft-rows">{"".join(rows)}</ol></div>')


def rail(e, it):
    """The small timeline in the top bar: the chapter's years on the axis, and a dot for the year being read."""
    if it and not it['is_app']:
        sp = [CHAPTERS[m['id']]['span'] for m in (it.get('group') or [it])]
        a, b = min(x[0] for x in sp), max(x[1] for x in sp)
    else:
        a = b = None
    band = f'<i class="rail-band" style="--a:{pct(a)};--b:{pct(b)}"></i>' if a else ''
    return (f'<button type="button" class="rail" data-act="timeline" aria-haspopup="dialog" aria-controls="menu" title="{esc(e.ui["rail_title"])}">'
            f'<span class="rail-y" aria-hidden="true"><span class="odo"></span></span>'
            f'<span class="rail-track" aria-hidden="true">{band}<i class="rail-dot"></i></span>'
            f'<span class="vh">{esc(e.ui["timeline"])}</span></button>')
