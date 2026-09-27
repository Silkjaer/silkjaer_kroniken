"""Coastlines of the southern North Sea for the crossing chart of chapter 17, written to northsea.json.

Run once by hand; the build reads only the JSON. Needs shapely and the Natural Earth coastlines in the npm
package world-atlas@2 (countries-10m.json):  npm pack world-atlas@2 && tar xzf world-atlas-2.0.2.tgz
    python3 make_northsea.py path/to/package/countries-10m.json

The chart is on Mercator, as a sea chart is: a straight line on it is a course held on the compass."""
import json
import math
import sys

from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union

LON0, LON1, LAT0, LAT1 = -1.2, 9.8, 52.9, 57.3     # the sheet
W = 1000.0
KEEP = {'826', '528', '276', '208', '056', '578'}     # UK, Netherlands, Germany, Denmark, Belgium, Norway


def merc(lat):
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


SX = W / (LON1 - LON0)
Y0, Y1 = merc(LAT1), merc(LAT0)
H = (Y0 - Y1) * SX


def project(lon, lat):
    return round((lon - LON0) * SX, 2), round((Y0 - merc(lat)) * SX, 2)


def decode(topo):
    sc, tr = topo['transform']['scale'], topo['transform']['translate']
    arcs = []
    for a in topo['arcs']:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)

    def arc(i):
        return arcs[i] if i >= 0 else arcs[~i][::-1]

    def ring(idx):
        out = []
        for i in idx:
            pts = arc(i)
            out.extend(pts if not out else pts[1:])
        return out
    return ring


def main(fn):
    topo = json.load(open(fn))
    ring = decode(topo)
    polys = []
    for g in topo['objects']['countries']['geometries']:
        if g.get('id') not in KEEP:
            continue
        parts = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]
        for p in parts:
            rings = [ring(r) for r in p]
            try:
                polys.append(Polygon(rings[0], rings[1:]).buffer(0))
            except Exception:
                pass
    land = unary_union(polys).intersection(box(LON0 - .5, LAT0 - .3, LON1 + .5, LAT1 + .3))
    # to the sheet's plane, then simplified to what a chart of this scale can show
    geoms = land.geoms if isinstance(land, MultiPolygon) else [land]
    out = []
    for g in geoms:
        ext = [project(*c) for c in g.exterior.coords]
        pg = Polygon(ext, [[project(*c) for c in r.coords] for r in g.interiors]).simplify(.35, preserve_topology=True)
        if pg.is_empty or pg.area < 1.2:
            continue
        for q in (pg.geoms if hasattr(pg, 'geoms') else [pg]):
            d = 'M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in q.exterior.coords) + 'Z'
            for r in q.interiors:
                d += 'M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in r.coords) + 'Z'
            out.append(d)
    json.dump({'lon': [LON0, LON1], 'lat': [LAT0, LAT1], 'W': W, 'H': round(H, 2), 'land': out},
              open('northsea.json', 'w'), separators=(',', ':'))
    print(len(out), 'polygons', sum(len(d) for d in out), 'chars', 'H', round(H, 1))


if __name__ == '__main__':
    main(sys.argv[1])
