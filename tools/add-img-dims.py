#!/usr/bin/env python3
"""Skriver intrinsic width/height på <img src="billeder/...">-tags, så browseren
kan reservere plads og undgå layout-hop, og sætter data-fuld på de billeder, der
har en original liggende i billeder/fuld/ (dem henter zoom). Idempotent."""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "Silkjaer.dc.html"


def dims(path):
    out = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        capture_output=True, text=True,
    ).stdout
    w = re.search(r"pixelWidth:\s*(\d+)", out)
    h = re.search(r"pixelHeight:\s*(\d+)", out)
    return (int(w.group(1)), int(h.group(1))) if w and h else None


html = SRC.read_text(encoding="utf-8")
cache, missing, patched = {}, [], 0


def fix(m):
    global patched
    tag = m.group(0)
    src = re.search(r'src="(billeder/[^"]+)"', tag)
    if not src:
        return tag
    rel = src.group(1)
    if rel not in cache:
        f = ROOT / rel
        cache[rel] = dims(f) if f.exists() else None
        if cache[rel] is None:
            missing.append(rel)
    d = cache[rel]
    if not d:
        return tag
    tag = re.sub(r'\s(?:width|height)="\d+"|\sdata-fuld', "", tag)
    fuld = " data-fuld" if (ROOT / re.sub(r"^billeder/", "billeder/fuld/", rel)).exists() else ""
    patched += 1
    return tag[:4] + f' width="{d[0]}" height="{d[1]}"{fuld}' + tag[4:]


html = re.sub(r"<img\s[^>]*>", fix, html)
SRC.write_text(html, encoding="utf-8")
print(f"{patched} img-tags fik mål")
if missing:
    print("uden fil:", *sorted(set(missing)), sep="\n  ", file=sys.stderr)
