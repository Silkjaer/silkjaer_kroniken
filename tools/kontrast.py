#!/usr/bin/env python3
"""Måler WCAG-kontrast for hver color:-værdi i de inline styles mod den nærmeste
baggrund i forældrekæden. Rapporterer alt under 4.5:1."""
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "index.html")


def rgb(v):
    v = v.strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", v)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r"rgba?\(([\d.]+),([\d.]+),([\d.]+)(?:,([\d.]+))?\)", v.replace(" ", ""))
    if m:
        r, g, b = (float(m.group(i)) for i in (1, 2, 3))
        a = float(m.group(4)) if m.group(4) else 1.0
        return (r, g, b, a)
    return None


def flatten(fg, bg):
    if len(fg) == 3:
        return fg
    r, g, b, a = fg
    return tuple(c * a + d * (1 - a) for c, d in zip((r, g, b), bg))


def lum(c):
    def ch(x):
        x /= 255
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    a, b = lum(fg), lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


html = SRC.read_text(encoding="utf-8")
tags = [(m.start(), m.group(0)) for m in re.finditer(r"<[a-zA-Z][^>]*>|</[a-zA-Z]+>", html)]
VOID = {"img", "br", "hr", "meta", "link", "input", "source"}
PAGE = (242, 239, 232)

stack, findings = [PAGE], collections.Counter()
for _, tag in tags:
    if tag.startswith("</"):
        if len(stack) > 1:
            stack.pop()
        continue
    name = re.match(r"<([a-zA-Z-]+)", tag).group(1).lower()
    style = re.search(r'style="([^"]*)"', tag)
    css = style.group(1) if style else ""
    bg = stack[-1]
    bgm = re.search(r"background(?:-color)?:\s*(#[0-9a-fA-F]{6}|rgba?\([^)]*\))", css)
    if bgm:
        c = rgb(bgm.group(1))
        if c:
            bg = flatten(c, stack[-1])
    fgm = re.search(r"(?<![-a-z])color:\s*(#[0-9a-fA-F]{6}|rgba?\([^)]*\))", css)
    if fgm:
        c = rgb(fgm.group(1))
        if c:
            fg = flatten(c, bg)
            r = ratio(fg, bg)
            if r < 4.5:
                sizem = re.search(r"font(?:-size)?:\s*(?:\d+\s+)?(\d+)px", css)
                px = sizem.group(1) if sizem else "?"
                findings[(fgm.group(1), "#%02x%02x%02x" % tuple(int(round(v)) for v in bg), round(r, 2), px)] += 1
    if tag.endswith("/>") or name in VOID:
        continue
    stack.append(bg)

for (fg, bg, r, px), n in sorted(findings.items(), key=lambda kv: kv[0][2]):
    print(f"{r:5.2f}:1  {fg:>22} på {bg}  {px:>3}px  ×{n}")
print(f"\n{sum(findings.values())} elementer under 4.5:1")
