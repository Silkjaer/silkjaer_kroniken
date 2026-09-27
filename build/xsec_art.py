"""Chapter 5: the beach at Husby on 9 November 1878, drawn as an engraved coastal profile.

One coordinate system for everything: x grows landwards, the still sea surface is y = 470. The ground is one
profile (the sea bed with its two bars, the beach, the dune and the heath behind it) interpolated without
overshoot, so the drawing, the hatching, the grass and the script all read the same ground. The script in ny.js
moves the boat, the waves, the rockets and the men, and places the labels on the features they name."""
import math
import random

SURF = 470
OUT, INN, SHORE = 900, 1180, 1340            # the outer bar, the inner bar, the waterline
B0 = 560                                     # where the boat is when the chapter's first card comes up
MAST = 1612                                  # the signal mast on the dune top
ST_X = 1728                                  # the station: left edge of its gable
ROCKET0 = (1344, 432)                        # the mouth of the rocket stand
ASHORE = 1346                                # where the helmsman stands up

PROFILE = [(-1600, 980), (-600, 930), (0, 880), (400, 790), (640, 700), (790, 630), (OUT, 592), (990, 626), (1070, 640),
           (1125, 606), (INN, 552), (1236, 572), (1290, 528), (SHORE, SURF), (1400, 456), (1450, 448), (1482, 440),
           (1506, 414), (1528, 370), (1548, 336), (1570, 322), (1590, 328), (MAST, 304), (1636, 310), (1660, 334),
           (1688, 356), (1720, 364), (1800, 366), (1900, 362), (2100, 368), (2400, 362), (2800, 368)]


def _pchip(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(pts)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    return xs, ys, h, m


_X, _Y, _H, _M = _pchip(PROFILE)


def ground(x):
    """The height of the ground at x."""
    if x <= _X[0]:
        return _Y[0]
    if x >= _X[-1]:
        return _Y[-1]
    i = 0
    while _X[i + 1] < x:
        i += 1
    h = _H[i]
    t = (x - _X[i]) / h
    t2, t3 = t * t, t * t * t
    return ((2 * t3 - 3 * t2 + 1) * _Y[i] + (t3 - 2 * t2 + t) * h * _M[i] + (-2 * t3 + 3 * t2) * _Y[i + 1]
            + (t3 - t2) * h * _M[i + 1])


def slope(x):
    return (ground(x + 2) - ground(x - 2)) / 4


def f(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def profile_d(close=True):
    """The ground as one smooth path; closed downwards when it is to be filled."""
    out = [f'M{f(_X[0])},{f(_Y[0])}']
    for i in range(len(_X) - 1):
        h = _H[i]
        c1 = (_X[i] + h / 3, _Y[i] + _M[i] * h / 3)
        c2 = (_X[i + 1] - h / 3, _Y[i + 1] - _M[i + 1] * h / 3)
        out.append(f'C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(_X[i + 1])},{f(_Y[i + 1])}')
    d = ' '.join(out)
    return d + f' L{_X[-1]},1900 L{_X[0]},1900 Z' if close else d


def _poly(pts):
    return 'M' + ' L'.join(f'{f(x)},{f(y)}' for x, y in pts)


def _smooth(x, w):
    if w <= 0:
        return ground(x)
    k = 7
    return sum(ground(x + w * (j / (k - 1) * 2 - 1)) for j in range(k)) / k


def strata():
    """Engraved follow-lines under the surface, flattening with depth, as a section of sand is cut."""
    lines = []
    for dk, w, op in ((5, 0, .55), (11, 8, .42), (19, 20, .32), (30, 38, .24), (44, 62, .17), (62, 92, .12), (84, 130, .08)):
        pts = [(x, _smooth(x, w) + dk) for x in range(120, 2560, 10)]
        lines.append(f'<path d="{_poly(pts)}" style="opacity:{op}"/>')
    return ''.join(lines)


def band(d0, d1, x0=120, x1=2560, step=12):
    """The strip of ground between two depths under the surface, for the stippled sand."""
    top = [(x, ground(x) + d0) for x in range(x0, x1 + 1, step)]
    bot = [(x, ground(x) + d1) for x in range(x1, x0 - 1, -step)]
    return _poly(top + bot) + 'Z'


def stipple_tile(rnd, n, size, r0, r1):
    return ''.join(f'<circle cx="{rnd.uniform(0, size):.1f}" cy="{rnd.uniform(0, size):.1f}" r="{rnd.uniform(r0, r1):.2f}"/>' for _ in range(n))


def grass(rnd):
    """Marram on the dune, bent landwards by the gale; each tuft sways on its own time."""
    tufts = []
    x = 1490
    while x < 1712:
        gap = rnd.uniform(11, 21) if x > 1526 else rnd.uniform(18, 30)
        x += gap
        if x > 1712:
            break
        by = ground(x) + 1.5
        n = rnd.randint(4, 7)
        hh = rnd.uniform(15, 26) * (0.7 if x > 1660 else 1)
        blades = []
        for j in range(n):
            bx = x + rnd.uniform(-4, 4)
            h = hh * rnd.uniform(.55, 1.05)
            lean = h * rnd.uniform(.2, .75)
            blades.append(f'M{f(bx)},{f(by)} q{f(lean * .15)},{f(-h * .6)} {f(lean)},{f(-h)}')
        dl = rnd.uniform(0, 2.4)
        tufts.append(f'<path d="{" ".join(blades)}" style="animation-delay:-{dl:.2f}s"/>')
    return ''.join(tufts)


def heath(rnd):
    """Heather and crowberry behind the dune: low rounded shrubs."""
    out = []
    x = 1690
    while x < 2560:
        x += rnd.uniform(9, 22)
        if ST_X - 12 < x < ST_X + 160:
            continue
        w, h = rnd.uniform(8, 20), rnd.uniform(3.5, 7.5)
        y = ground(x) + 1
        out.append(f'M{f(x - w / 2)},{f(y)} c{f(w * .1)},{f(-h * 1.1)} {f(w * .9)},{f(-h * 1.1)} {f(w)},0')
    return f'<path class="xs-heath" d="{" ".join(out)}"/>'


def station():
    """The lifeboat house behind the dune, drawn a little from the side: the gable with the boat doors, the tiled
    roof and the long wall with two windows; the signal mast stands on the top of the dune."""
    X, Y = ST_X, ground(ST_X + 40) + 1
    W, WH, RISE = 80, 46, 44
    DX, DY = 66, -34                                   # the depth of the house, drawn receding
    A = (X + W / 2, Y - WH - RISE)                     # apex of the front gable
    Rt = (X + W, Y - WH)
    ov = .12
    Ro = (Rt[0] + (Rt[0] - A[0]) * ov, Rt[1] + (Rt[1] - A[1]) * ov)
    Lo = (X - (Rt[0] - A[0]) * ov, Rt[1] + (Rt[1] - A[1]) * ov)
    pre = .05
    fA = (A[0] - DX * pre, A[1] - DY * pre)
    fR = (Ro[0] - DX * pre, Ro[1] - DY * pre)
    bA = (A[0] + DX * (1 + pre), A[1] + DY * (1 + pre))
    bR = (Ro[0] + DX * (1 + pre), Ro[1] + DY * (1 + pre))
    P = lambda *pts: _poly(pts) + 'Z'
    side = P((X + W, Y), (X + W + DX, Y + DY), (X + W + DX, Y + DY - WH), (X + W, Y - WH))
    front = P((X, Y), (X + W, Y), (X + W, Y - WH), A, (X, Y - WH))
    roof = P(fA, fR, bR, bA)
    # tile courses along the roof, brick courses along the wall
    tiles = []
    for k in range(1, 9):
        t = k / 9
        p = (fA[0] + (fR[0] - fA[0]) * t, fA[1] + (fR[1] - fA[1]) * t)
        tiles.append(f'M{f(p[0])},{f(p[1])} l{f(DX * (1 + 2 * pre))},{f(DY * (1 + 2 * pre))}')
    bricks = [f'M{f(X + W)},{f(Y - j * 4.6)} l{DX},{DY}' for j in range(1, 10)]
    fb = [f'M{f(X)},{f(Y - j * 4.6)} h{W}' for j in range(1, 10) if j * 4.6 < WH - 1]
    # the boat doors: two leaves of boards with a Z-brace each
    d0, d1, dt = X + 13, X + W - 13, Y - 38
    mid = (d0 + d1) / 2
    boards = ' '.join(f'M{f(x)},{f(Y)} V{f(dt)}' for x in [d0 + (d1 - d0) * k / 12 for k in range(1, 12)])
    brace = (f'M{f(d0)},{f(Y - 8)} H{f(d1)} M{f(d0)},{f(dt + 8)} H{f(d1)} '
             f'M{f(d0 + 1)},{f(Y - 8)} L{f(mid - 1)},{f(dt + 8)} M{f(mid + 1)},{f(Y - 8)} L{f(d1 - 1)},{f(dt + 8)}')
    wins = []
    for dd in (.28, .62):
        bx, by = X + W + DX * dd, Y + DY * dd - 17
        wx, wy = DX * .14, DY * .14
        wins.append(P((bx, by), (bx + wx, by + wy), (bx + wx, by + wy - 15), (bx, by - 15)))
    gw = (A[0], A[1] + 27)
    mast_top = 136
    mx, my = MAST, ground(MAST) + 1
    return f'''<g class="xs-station">
 <path class="shade" d="{side}"/><path class="hatch" d="{' '.join(bricks)}"/>
 <path class="win" d="{' '.join(wins)}"/>
 <path class="roof" d="{roof}"/><path class="hatch r" d="{' '.join(tiles)}"/>
 <path class="face" d="{front}"/><path class="hatch f" d="{' '.join(fb)}"/>
 <path class="door" d="M{f(d0)},{f(Y)} V{f(dt)} H{f(d1)} V{f(Y)} Z"/><path class="boards" d="{boards} M{f(mid)},{f(Y)} V{f(dt)} {brace}"/>
 <path class="line" d="M{f(d0 - 3)},{f(dt - 2.5)} H{f(d1 + 3)}"/>
 <path class="board" d="M{f(X + 22)},{f(Y - WH + 1)} h{W - 44} v-6 h-{W - 44} Z"/>
 <circle class="win" cx="{f(gw[0])}" cy="{f(gw[1])}" r="5.2"/><path class="line" d="M{f(gw[0] - 5.2)},{f(gw[1])} h10.4 M{f(gw[0])},{f(gw[1] - 5.2)} v10.4"/>
 <path class="barge" d="M{f(Lo[0] - DX * pre)},{f(Lo[1] - DY * pre)} L{f(fA[0])},{f(fA[1])} L{f(fR[0])},{f(fR[1])} M{f(fA[0])},{f(fA[1])} L{f(bA[0])},{f(bA[1])}"/>
 <path class="plinth" d="M{f(X - 4)},{f(Y)} H{f(X + W)} l{DX},{DY}"/>
</g>
<g class="xs-mast">
 <path class="stay" d="M{mx},{mast_top + 24} L{f(mx - 30)},{f(ground(mx - 30) + 1)} M{mx},{mast_top + 24} L{f(mx + 32)},{f(ground(mx + 32) + 1)} M{mx - 22},{mast_top + 42} L{mx - 22},{f(ground(mx - 22) - 8)} M{mx + 22},{mast_top + 42} L{mx + 22},{f(ground(mx + 22) - 20)}"/>
 <path class="pole" d="M{mx},{f(my)} V{mast_top} M{mx - 23},{mast_top + 42} H{mx + 23}"/>
 <circle class="ball" cx="{mx + 22}" cy="{mast_top + 50}" r="3.6"/>
 <path class="flag" d="M{mx},{mast_top + 1} l20,4 l-20,5 Z"/>
</g>'''


def lifeboat():
    """The station's lifeboat on its carriage, brought down to the beach and never launched."""
    ax, bx = 1414, 1468
    ya, yb = ground(ax) - 10, ground(bx) - 10
    cx, cy = (ax + bx) / 2, (ya + yb) / 2
    ang = math.degrees(math.atan2(yb - ya, bx - ax))
    wheel = lambda x, y: (f'<circle class="wh" cx="{f(x)}" cy="{f(y)}" r="10"/>'
                          + '<path class="sp" d="' + ' '.join(f'M{f(x)},{f(y)} l{f(10 * math.cos(a))},{f(10 * math.sin(a))}' for a in [k * math.pi / 4 for k in range(8)]) + '"/>')
    hull = ('M-50,-24 C-40,-12 -20,-9 0,-9 C20,-9 40,-12 50,-24 C47,-12 38,-3 24,-1 C10,1 -10,1 -24,-1 C-38,-3 -47,-12 -50,-24 Z')
    return (f'<g class="xs-lifeboat">'
            f'<g transform="translate({f(cx)},{f(cy)}) rotate({ang:.1f})"><path class="frame" d="M-34,0 H34 M-26,0 L-18,-8 M26,0 L18,-8 M-40,-2 L-50,4"/>'
            f'<path class="hull" d="{hull}"/><path class="strake" d="M-45,-18 C-32,-8 -14,-5 0,-5 C14,-5 32,-8 45,-18"/></g>'
            f'{wheel(ax, ya)}{wheel(bx, yb)}</g>')


def rocket_stand():
    x, y = 1356, ground(1356)
    mx, my = ROCKET0
    return (f'<g class="xs-stand"><path d="M{f(x)},{f(y - 16)} L{f(x - 9)},{f(y)} M{f(x)},{f(y - 16)} L{f(x + 8)},{f(y)} '
            f'M{f(x + 12)},{f(y - 6)} L{f(mx)},{f(my)}"/><rect class="box" x="{f(x + 13)}" y="{f(y - 7)}" width="10" height="7"/></g>')
