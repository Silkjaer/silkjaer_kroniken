"""The crossing of March 1945 drawn as a sea chart: the southern North Sea on Mercator, as a chart is, with the
shallows tinted along the coasts, a compass rose and a scale of nautical miles. The course is pencilled on it: out
from Esbjerg through the channel north of Fanø to the rendezvous on Outer Silver Pit, and home again. The coastlines
are Natural Earth's (see make_northsea.py); the camera moves over the sheet as the dated entries are read."""
import json
import math
import os


NS = json.load(open(os.path.join(os.path.dirname(__file__), 'northsea.json')))
LON0, LON1 = NS['lon']
LAT0, LAT1 = NS['lat']
W, H = NS['W'], NS['H']
SX = W / (LON1 - LON0)


def merc(lat):
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


MY1 = merc(LAT1)


def P(lon, lat):
    return round((lon - LON0) * SX, 1), round((MY1 - merc(lat)) * SX, 1)


PLACES = {'esbjerg': (8.445, 55.461), 'hvidesande': (8.128, 55.999), 'thyboroen': (8.222, 56.699), 'osp': (1.9, 54.3)}
# the course out: from the harbour north-west between Fanø and Skallingen, then on across the sea
HARBOUR = [(8.445, 55.461), (8.428, 55.4675), (8.405, 55.4722), (8.37, 55.4728), (8.335, 55.4685), (8.30, 55.464), (8.25, 55.459), (8.1, 55.445)]
OUT = HARBOUR + [(7.9, 55.43), (6.4, 55.18), (4.4, 54.82), (2.9, 54.55), (1.9, 54.3)]
BACK = [(1.9, 54.3), (3.2, 54.52), (5.0, 54.88), (6.6, 55.2), (7.95, 55.42)] + HARBOUR[::-1]
# views of the camera, one per dated entry (lon0, lat0, lon1, lat1); the first is the sheet itself
VIEWS = [
    (-1.2, 52.9, 9.8, 57.3),      # 6 January: the rendezvous agreed, and ten weeks of storm
    (6.9, 55.25, 9.6, 56.95),     # 8 March: Hvide Sande given up, Thyborøn
    (-1.0, 53.3, 9.4, 56.2),      # 16 March: out to the fishing bank, with the English coast in view
    (-1.05, 53.25, 3.7, 55.1),    # the cargo, on Outer Silver Pit
    (-1.0, 53.3, 9.4, 56.2),      # Easter Saturday: home through the harbour control
    (7.75, 55.25, 8.95, 55.72),   # the night after: ashore at Esbjerg
]


def path(pts, smooth=True):
    xy = [P(*p) for p in pts]
    if not smooth or len(xy) < 3:
        return 'M' + ' L'.join(f'{x},{y}' for x, y in xy)
    # a Catmull-Rom line through the points, as a course pencilled with a ship's curve
    d = f'M{xy[0][0]},{xy[0][1]}'
    for i in range(len(xy) - 1):
        p0 = xy[i - 1] if i else xy[i]
        p1, p2 = xy[i], xy[i + 1]
        p3 = xy[i + 2] if i + 2 < len(xy) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f' C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]},{p2[1]}'
    return d


def graticule():
    out = []
    for lon in range(math.ceil(LON0), math.floor(LON1) + 1):
        x = P(lon, LAT0)[0]
        out.append(f'<path d="M{x},0 V{H}"/>')
    for lat in range(math.ceil(LAT0), math.floor(LAT1) + 1):
        y = P(LON0, lat)[1]
        out.append(f'<path d="M0,{y} H{W}"/>')
    return ''.join(out)


def rose(lon, lat, r):
    cx, cy = P(lon, lat)
    t = []
    for a in range(0, 360, 5):
        rr = r * (.9 if a % 10 else .84) if a % 30 else r * .8
        ang = math.radians(a)
        t.append(f'M{cx + r * math.sin(ang):.1f},{cy - r * math.cos(ang):.1f} L{cx + rr * math.sin(ang):.1f},{cy - rr * math.cos(ang):.1f}')
    star = []
    for k in range(8):
        a = math.radians(k * 45)
        L = r * (.72 if k % 2 == 0 else .46)
        s = r * .09
        tip = (cx + L * math.sin(a), cy - L * math.cos(a))
        l = (cx + s * math.sin(a - math.pi / 2), cy - s * math.cos(a - math.pi / 2))
        rgt = (cx + s * math.sin(a + math.pi / 2), cy - s * math.cos(a + math.pi / 2))
        star.append(f'<path class="rs-d" d="M{cx},{cy} L{l[0]:.1f},{l[1]:.1f} L{tip[0]:.1f},{tip[1]:.1f} Z"/>'
                    f'<path class="rs-l" d="M{cx},{cy} L{rgt[0]:.1f},{rgt[1]:.1f} L{tip[0]:.1f},{tip[1]:.1f} Z"/>')
    return (f'<g class="rose"><circle cx="{cx}" cy="{cy}" r="{r}"/><circle cx="{cx}" cy="{cy}" r="{r * .8:.1f}"/>'
            f'<path class="rs-t" d="{" ".join(t)}"/>{"".join(star)}'
            f'<text x="{cx}" y="{cy - r - 6:.1f}" text-anchor="middle">N</text></g>')


def scale_bar(lon, lat, nm, label):
    x0, y = P(lon, lat)
    per = SX / 60 / math.cos(math.radians(lat))       # chart units in one nautical mile at this latitude
    segs = []
    for i in range(0, nm, 10):
        segs.append(f'<rect class="{"f" if (i // 10) % 2 == 0 else "e"}" x="{x0 + i * per:.1f}" y="{y}" width="{10 * per:.1f}" height="3.2"/>')
    ticks = ''.join(f'<text x="{x0 + i * per:.1f}" y="{y - 4:.1f}" text-anchor="middle">{i}</text>' for i in (0, nm // 2, nm))
    return f'<g class="nm">{"".join(segs)}{ticks}<text class="u" x="{x0 + nm * per / 2:.1f}" y="{y + 13:.1f}" text-anchor="middle">{label}</text></g>'


def storm():
    """Ten weeks of storm: streaks of wind over the open sea."""
    import random
    rnd = random.Random(1945)
    out = []
    for _ in range(46):
        lon, lat = rnd.uniform(1.0, 7.4), rnd.uniform(53.9, 57.1)
        x, y = P(lon, lat)
        L = rnd.uniform(22, 60)
        out.append(f'<path d="M{x:.1f},{y:.1f} q{L * .5:.1f},{-L * .09:.1f} {L:.1f},{L * .05:.1f}"/>')
    return ''.join(out)


def chart_svg(lang, title):
    da = lang == 'da'
    land = ''.join(f'<path d="{d}"/>' for d in NS['land'])
    ex, ey = P(*PLACES['esbjerg'])
    hx, hy = P(*PLACES['hvidesande'])
    tx, ty = P(*PLACES['thyboroen'])
    ox, oy = P(*PLACES['osp'])
    lab = lambda cls, x, y, txt, anc='start', dy=0: f'<text class="{cls}" x="{x}" y="{y + dy}" text-anchor="{anc}">{txt}</text>'
    sea_x, sea_y = P(3.4, 55.75)
    en_x, en_y = P(-0.84, 53.98)
    ju_x, ju_y = P(9.05, 56.25)
    d16 = P(7.35, 55.33)
    d31 = P(6.2, 55.02)
    views = ';'.join(','.join(f'{v}' for v in vw) for vw in VIEWS)
    return (f'<aside class="chart sea-chart" data-scene="chart" aria-hidden="true" data-lon0="{LON0}" data-lon1="{LON1}" data-lat1="{LAT1}" '
            f'data-sx="{SX:.6f}" data-w="{W}" data-h="{H}" data-views="{views}" data-lat-lbl="{"N" if da else "N"}" data-lon-lbl="{"Ø" if da else "E"}">'
            f'<div class="chart-in"><div class="m-s uc c-acc chart-t">{title}</div><div class="sc-sheet">'
            f'<svg class="sc-map" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">'
            f'<rect class="sc-sea" x="-2000" y="-2000" width="{W + 4000}" height="{H + 4000}"/>'
            f'<g class="sc-shoal2">{land}</g><g class="sc-shoal">{land}</g>'
            f'<g class="sc-grat">{graticule()}</g>'
            f'<g class="sc-storm">{storm()}</g>'
            f'<g class="sc-land">{land}</g>'
            f'{rose(5.35, 56.55, 58)}'
            f'{scale_bar(2.3, 53.22, 50, "Sømil" if da else "Nautical miles")}'
            f'{lab("sc-sea-n", sea_x, sea_y, "NORDSØEN" if da else "NORTH SEA", "middle")}'
            f'<text class="sc-land-n" x="{en_x}" y="{en_y}" text-anchor="middle" transform="rotate(-72 {en_x} {en_y})">ENGLAND</text>'
            f'{lab("sc-land-n", ju_x, ju_y, "JYLLAND" if da else "JUTLAND", "middle")}'
            f'<path class="plan" d="{path(OUT)}"/>'
            f'<path class="leg out" pathLength="1" d="{path(OUT)}"/>'
            f'<path class="leg back" pathLength="1" d="{path(BACK)}"/>'
            f'<g class="pt pt-e"><circle cx="{ex}" cy="{ey}" r="3.2"/>{lab("pn", ex + 7, ey, "Esbjerg", "start", 4)}</g>'
            f'<g class="pt pt-h"><circle cx="{hx}" cy="{hy}" r="2.6"/><path class="x" d="M{hx - 6},{hy - 6} L{hx + 6},{hy + 6} M{hx + 6},{hy - 6} L{hx - 6},{hy + 6}"/>{lab("pn", hx + 8, hy, "Hvide Sande", "start", 4)}</g>'
            f'<g class="pt pt-t"><circle cx="{tx}" cy="{ty}" r="2.6"/>{lab("pn", tx + 8, ty, "Thyborøn", "start", 4)}</g>'
            f'<g class="pt pt-o"><circle class="ring" cx="{ox}" cy="{oy}" r="11"/><circle cx="{ox}" cy="{oy}" r="3.2"/>{lab("pn", ox + 12, oy, "Outer Silver Pit", "start", 16)}</g>'
            f'{lab("pencil p16", d16[0], d16[1], "16/3")}{lab("pencil p31", d31[0], d31[1], "31/3")}'
            f'<g class="boat"><circle r="3.4"/></g>'
            f'</svg><svg class="sc-frame" aria-hidden="true"></svg></div></div></aside>')


if __name__ == '__main__':
    from shapely.geometry import LineString, Polygon
    # self-check: the pencilled courses stay at sea (the harbour ends excepted)
    polys = []
    for d in NS['land']:
        for ring in d.split('Z'):
            ring = ring.strip()
            if ring:
                pts = [tuple(map(float, q.split(','))) for q in ring[1:].split('L')]
                if len(pts) > 2:
                    polys.append(Polygon(pts).buffer(0))
    for name, pts in (('out', OUT), ('back', BACK)):
        for a, b in zip(pts, pts[1:]):
            seg = LineString([P(*a), P(*b)])
            hit = any(p.intersects(seg) for p in polys)
            print(name, a, b, 'LAND' if hit else 'sea')
