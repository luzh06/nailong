# Wall and ground equipment for houses: outdoor AC units with pipe covers and drains, meters, water heaters, intercoms, potted plants.
# Placed from Bld anchors and by a per-house scatter on rear and side walls. ENU frames as in blk_core (a along wall, b up, c outward).
from blk_core import *
from blk_arch import frange

CASE = ((.86, .85, .8), (.8, .8, .76), (.9, .88, .82), (.74, .72, .66))


def ac_unit(m, f, a, y, R, mount="ground"):
    """Outdoor AC at wall coords (a = centre along wall, y = bottom). Returns pipe start point (wall coords)."""
    W, H, D = .8, .58, .29; col = R.choice(CASE); x0 = a - W / 2; c0 = .1 if mount == "ground" else .16
    box(m, "paint", f, x0, x0 + W, y, y + H, c0, c0 + D, ch=.018, col=col)
    # front fan grille: dark disc, rings, spokes
    cx = x0 + .3; cy = y + H / 2; cz = c0 + D + .002
    P = [f.p(cx + .2 * cos(k * pi / 12), cy + .2 * sin(k * pi / 12), cz) for k in range(24)]
    m.poly("dark", P, None, (.05, .05, .05))
    for k in range(9):           # dense concentric guard rings, as on real outdoor units
        r = .035 + k * .021
        pts = [f.p(cx + r * cos(j * pi / 10), cy + r * sin(j * pi / 10), cz + .008) for j in range(21)]
        tube(m, "paint", pts, .0035, 4, tint(col, .75))
    for th in (0, pi / 2):
        tube(m, "paint", [f.p(cx - .21 * cos(th), cy - .21 * sin(th), cz + .011), f.p(cx + .21 * cos(th), cy + .21 * sin(th), cz + .011)], .006, 4, tint(col, .75))
    lathe_hub = [(.0, 0), (.035, .0), (.03, .03), (.0, .035)]
    from blk_temple import lathe
    lathe(m, "paint", f.p(cx, cy, cz - .06), lathe_hub, 10, (.2, .2, .2))
    decal(m, f, x0 + .02, y + .02, W - .04, H * .55, R.choice((4, 5)), off=c0 + D + .004 - 0)       # dust and splash on the lower casing
    # right-hand service panel, top louvres, nameplate
    box(m, "paint", f, x0 + .58, x0 + W - .03, y + .06, y + H - .06, c0 + D, c0 + D + .006, col=tint(col, .96))
    box(m, "paint", f, x0 + .62, x0 + .74, y + H - .16, y + H - .1, c0 + D + .006, c0 + D + .008, col=(.7, .7, .72))
    for k in range(6):
        box(m, "dark", f, x0 + .05, x0 + W - .05, y + H + .001, y + H + .004, c0 + .04 + k * .04, c0 + .055 + k * .04, col=(.2, .2, .2))
    if mount == "ground":
        for x in (x0 + .08, x0 + W - .18):
            box(m, "concrete", f, x - .02, x + .14, y - .12, y, c0 - .02, c0 + D + .03, ch=.008, col=(.6, .6, .57), sc=2.2)
    else:   # steel wall brackets
        for x in (x0 + .1, x0 + W - .14):
            box(m, "steel", f, x, x + .04, y - .03, y, 0, c0 + D + .05, col=(.45, .45, .43))
            box(m, "steel", f, x, x + .04, y - .38, y - .03, 0, .04, col=(.45, .45, .43))
            tube(m, "steel", [f.p(x + .02, y - .34, .03), f.p(x + .02, y - .02, c0 + D - .02)], .012, 4, (.45, .45, .43))
    # refrigerant lines in an insulated wrap from the left side, drain hose down
    p0 = (x0 - .02, y + .12)
    tube(m, "pvc", [f.p(x0 + .05, y + .12, c0 + .12), f.p(x0 - .08, y + .12, c0 + .12), f.p(x0 - .12, y + .18, .06)], .03, 8, (.9, .88, .8))
    tube(m, "dark", [f.p(x0 + .1, y + .03, c0 + .1), f.p(x0 + .05, y - .02, c0 + .06), f.p(x0 + .0, y - (y if mount == "ground" else .9), .05)], .009, 5, (.15, .15, .15))
    decal(m, f, a - .4, max(.05, y - .55), .8, .55, R.choice((6, 7)), off=.004) if mount != "ground" else None
    return (x0 - .12, y + .18)


def pipe_cover(m, f, a0, y0, a1, y1, col=(.82, .78, .66)):
    """Square plastic duct (keshou cover) along the wall, L shape, ending in a wall cap."""
    w = .075
    if abs(a1 - a0) > .02:
        box(m, "pvc", f, min(a0, a1) - w, max(a0, a1) + w, y0 - w, y0 + w, 0, .09, ch=.012, col=col)
    if abs(y1 - y0) > .02:
        box(m, "pvc", f, a1 - w, a1 + w, min(y0, y1) - w, max(y0, y1) + w, 0, .09, ch=.012, col=col)
    box(m, "pvc", f, a1 - .1, a1 + .1, y1 - .1, y1 + .1, 0, .12, ch=.02, col=tint(col, .95))


def gas_meter(m, f, a, y, R):
    box(m, "paint", f, a - .16, a + .16, y, y + .34, .05, .22, ch=.012, col=(.78, .8, .78))
    box(m, "glass", f, a - .1, a + .06, y + .17, y + .27, .22, .222, col=(1, 1, 1))
    for x in (a - .1, a + .1):
        tube(m, "steel", [f.p(x, y, .12), f.p(x, y - .25, .12), f.p(x, y - .3, .03)], .017, 6, (.55, .5, .4))
    tube(m, "steel", [f.p(a - .1, y - .3, .03), f.p(a - .1, y - (y - .05), .03)], .017, 6, (.55, .5, .4))
    box(m, "paint", f, a - .07, a + .07, y + .36, y + .42, .04, .08, col=(.85, .7, .2))       # yellow tag


def elec_meter(m, f, a, y):
    box(m, "pvc", f, a - .14, a + .14, y, y + .32, 0, .12, ch=.015, col=(.88, .88, .86))
    P = [f.p(a + .07 * cos(k * pi / 8), y + .2 + .07 * sin(k * pi / 8), .121) for k in range(16)]
    m.poly("glass", P, None, (1, 1, 1))
    tube(m, "pvc", [f.p(a, y + .32, .05), f.p(a, y + 1.6, .05)], .018, 6, (.6, .6, .58))


def intercom(m, f, a, y, name_col=(.78, .7, .55)):
    box(m, "paint", f, a - .06, a + .06, y, y + .16, 0, .03, ch=.008, col=(.25, .25, .26))
    box(m, "glass", f, a - .035, a + .035, y + .09, y + .13, .03, .032, col=(1, 1, 1))
    box(m, "plank", f, a + .14, a + .34, y + .02, y + .12, 0, .015, ch=.004, col=name_col, sc=1.)       # wooden nameplate (hyosatsu)


def water_heater(m, f, a, R):
    """Heat-pump water heater: slim tank and a fan unit beside it."""
    box(m, "paint", f, a - .32, a + .32, 0, 1.85, .08, .78, ch=.03, col=(.9, .9, .88))
    box(m, "dark", f, a - .25, a + .25, 1.55, 1.7, .78, .785, col=(.15, .15, .16))
    ac_unit(m, f, a + 1.05, .12, R)
    tube(m, "pvc", [f.p(a + .32, .4, .3), f.p(a + .6, .4, .3)], .03, 8, (.9, .88, .8))


PROPS = []      # (asset, ENU position, rotation about z, scale); instanced by blk_fill after flush


def potted(m, p, R, s=1.0):
    """Terracotta or plastic pot with soil; foliage is an instanced CC0 plant (fern / nettle)."""
    p = V(p); pc = R.choice(((.62, .32, .2), (.5, .28, .18), (.3, .3, .32), (.55, .52, .46)))
    lathe_pot = [(.12 * s, 0), (.15 * s, .04 * s), (.18 * s, .3 * s), (.2 * s, .31 * s), (.2 * s, .34 * s), (.17 * s, .34 * s)]
    from blk_temple import lathe
    lathe(m, "paint", p, lathe_pot, 14, pc)
    m.poly("dark", [p + V((.17 * s * cos(k * pi / 7), .17 * s * sin(k * pi / 7), .31 * s)) for k in range(14)], None, (.12, .09, .06))
    kind = R.choice(("fern_02", "fern_02", "nettle_plant"))
    PROPS.append((kind, (p.x, p.y, p.z + .3 * s), R.random() * 2 * pi, s * R.uniform(.7, 1.0) * (.5 if kind == "nettle_plant" else .85)))


def cable(m, p, q, sag, r=.011, col=(.08, .08, .08), n=14):
    """Catenary-ish span (parabola) between two points."""
    p, q = V(p), V(q)
    pts = [p.lerp(q, t) - V((0, 0, sag * 4 * t * (1 - t))) for t in (k / n for k in range(n + 1))]
    tube(m, "dark", pts, r, 5, col)


def utility_pole(m, x, y, z0, arm_dir, R, xfmr=False, H=12.4):
    """Concrete distribution pole: taper, guard sleeve, step bolts, crossarms with insulators, optional transformer.
    Returns attachment points {'hv': [3 points], 'lv': [2], 'tel': [2]} in ENU."""
    from blk_temple import lathe
    c = V((x, y, z0)); u = V((arm_dir[0], arm_dir[1], 0)).normalized(); w = V((-u.y, u.x, 0))
    lathe(m, "concrete", c, [(.2, -.3), (.2, 0), (.15, H * .9), (.135, H), (.0, H + .02)], 16, (.66, .65, .62))
    for k in range(12):                        # yellow/black guard sleeve
        z = .25 + k * .16
        tube(m, "paint", [c + V((0, 0, z)), c + V((0, 0, z + .16))], .208, 16, (.85, .68, .12) if k % 2 == 0 else (.06, .06, .06))
    box(m, "paint", Frame(c + V((0, 0, 2.2)), w, (0, 0, 1), u), -.09, .09, 0, .26, .19, .2, col=(.2, .3, .6))      # number plate
    for k in range(14):                        # step bolts
        z = 2.6 + k * .45; d = u if k % 2 else -u
        tube(m, "steel", [c + V((0, 0, z)) + d * .17, c + V((0, 0, z)) + d * .38], .012, 4, (.4, .4, .4))
    pts = {"hv": [], "lv": [], "tel": []}
    for z, L, kind in ((H - .45, 1.0, "hv"), (H - 1.6, .8, "lv")):
        fr = Frame(c + V((0, 0, z)), u, (0, 0, 1), w)
        box(m, "steel", fr, -L, L, -.05, .05, -.05, .05, ch=.005, col=(.35, .35, .34))
        tube(m, "steel", [c + V((0, 0, z - .65)) - u * .02, c + V((0, 0, z)) + u * (L * .7)], .015, 4, (.35, .35, .34))
        for s in ((-L * .9, 0, L * .9) if kind == "hv" else (-L * .8, L * .8)):
            p = c + V((0, 0, z + .05)) + u * s
            lathe(m, "paint", p, [(.04, 0), (.07, .05), (.05, .1), (.07, .15), (.04, .22), (.02, .26)], 10, (.88, .86, .82))
            pts[kind].append(p + V((0, 0, .24)))
    for k, z in enumerate((6.8, 7.3)):         # telecom lines on brackets toward the street
        fr = Frame(c + V((0, 0, z)), w, (0, 0, 1), u)
        box(m, "steel", fr, -.03, .03, -.03, .03, 0, .45, col=(.35, .35, .34))
        pts["tel"].append(c + V((0, 0, z)) + w * .45)
    if xfmr:
        p = c + w * .48 + V((0, 0, H - 3.0))
        tube(m, "paint", [p, p + V((0, 0, 1.05))], .3, 16, (.6, .62, .62))
        lathe(m, "paint", p + V((0, 0, 1.05)), [(.31, 0), (.2, .1), (.05, .14)], 16, (.55, .57, .57))
        for k in range(2): lathe(m, "paint", p + V((0, 0, 1.15)) + u * (.12 * (1 - 2 * k)), [(.03, 0), (.05, .06), (.03, .14)], 8, (.85, .83, .8))
        box(m, "steel", Frame(c + V((0, 0, H - 3.1)), w, (0, 0, 1), u), 0, .5, -.04, .04, -.1, .1, col=(.35, .35, .34))
    return pts


def holes_clear(b, i, a0, a1, y0, y1, pad=.15):
    return not any(h[0] - pad < a1 and h[2] + pad > a0 and h[1] - pad < y1 and h[3] + pad > y0 for h in b.holes[i])


def equip_house(b, R, density=1.0):
    """Anchor-driven fixtures plus a scatter of AC units, meters and pots on rear/side walls."""
    m = b.m
    for an in b.anchors:
        i = min(range(4), key=lambda k: (b.nside[k].x - an["outward_enu"][0]) ** 2 + (b.nside[k].y - an["outward_enu"][1]) ** 2)
        f = b.frames[i]; d = V((an["center_enu"][0], an["center_enu"][1], 0)) - V((f.o.x, f.o.y, 0)); a = d.dot(f.u)
        if an["type"] == "ac_outdoor":
            pa = ac_unit(m, f, a, .14, R); pipe_cover(m, f, pa[0], pa[1], pa[0] - .3, min(b.fh * .8, 2.3))
        elif an["type"] == "gas_meter": gas_meter(m, f, a, 1.0, R)
        elif an["type"] == "planter":
            for k in range(R.randint(2, 4)): potted(m, f.p(a + k * .45, 0, .35), R, R.uniform(.8, 1.25))
    for i in range(4):
        role = b.role(i); w = b.len[i]; f = b.frames[i]
        if w < 2.6: continue
        if role != "front" and R.random() < .8 * density:          # ground unit under a window
            for _ in range(4):
                a = R.uniform(.7, w - .7)
                if holes_clear(b, i, a - .45, a + .45, 0, .8):
                    pa = ac_unit(m, f, a, .14, R); y1 = min(b.fh - .4, 2.4)
                    if holes_clear(b, i, pa[0] - .45, pa[0] - .15, .2, y1): pipe_cover(m, f, pa[0], pa[1], pa[0] - .3, y1)
                    break
        for fl in range(1, b.st):                                  # bracket units on upper floors
            if role == "front" and R.random() > .3 * density: continue
            if R.random() > .55 * density: continue
            y = fl * b.fh + .25
            for _ in range(4):
                a = R.uniform(.7, w - .7)
                if holes_clear(b, i, a - .45, a + .45, y - .4, y + .7):
                    pa = ac_unit(m, f, a, y, R, mount="bracket"); pipe_cover(m, f, pa[0], pa[1], pa[0] - .25, y + .95)
                    break
        if role == "front":
            for (h0, hy0, h1, hy1) in b.holes[i]:
                if hy0 < .3 and h1 - h0 < 2.2 and R.random() < .8:        # door: intercom, nameplate, meter nearby
                    if holes_clear(b, i, h1 + .1, h1 + .5, 1.2, 1.6, .05): intercom(m, f, h1 + .2, 1.25)
                    if holes_clear(b, i, h0 - .5, h0 - .1, 1.4, 1.9, .05) and R.random() < .6: elec_meter(m, f, h0 - .3, 1.45)
                    break
        if role in ("back", "left", "right") and R.random() < .35 * density and w > 3:
            a = R.uniform(.6, w - .6)
            if holes_clear(b, i, a - .25, a + .25, .7, 1.5): gas_meter(m, f, a, .9, R)
        if role == "back" and R.random() < .18 * density and w > 4:
            a = R.uniform(1.0, w - 2.2)
            if holes_clear(b, i, a - .4, a + 1.6, 0, 2.0): water_heater(m, f, a, R)
