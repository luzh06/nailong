# Building archetypes assembled from real footprints; nothing is copied between buildings
from blk_core import *

Z = V((0, 0, 1))
ALU = (1, 1, 1)
UP = Z


def obb(fp):
    """Minimum-area rectangle of a 2D footprint."""
    best = None
    n = len(fp)
    for i in range(n):
        ex = fp[(i + 1) % n][0] - fp[i][0]; ey = fp[(i + 1) % n][1] - fp[i][1]
        L = math.hypot(ex, ey)
        if L < .5: continue
        ux, uy = ex / L, ey / L
        xs = [p[0] * ux + p[1] * uy for p in fp]; ys = [-p[0] * uy + p[1] * ux for p in fp]
        a = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if best is None or a < best[0]:
            cx = (max(xs) + min(xs)) / 2; cy = (max(ys) + min(ys)) / 2
            best = (a, ux, uy, cx, cy, (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2)
    _, ux, uy, cx, cy, ha, hb = best
    c = V((cx * ux - cy * uy, cx * uy + cy * ux, 0))
    return c, V((ux, uy, 0)), V((-uy, ux, 0)), ha, hb


class Bld:
    def __init__(s, name, fp, H, st, G, rng, **spec):
        s.name = name; s.H = H; s.st = st; s.G = G; s.rng = rng; s.sp = spec
        s.c, s.ax, s.ay, s.a, s.b = obb(fp)
        for vec, amt in spec.get("trim", []):
            d = V((vec[0], vec[1], 0)).normalized()
            if abs(d.dot(s.ax)) > abs(d.dot(s.ay)):
                sg = 1 if d.dot(s.ax) > 0 else -1; s.a -= amt / 2; s.c -= s.ax * (sg * amt / 2)
            else:
                sg = 1 if d.dot(s.ay) > 0 else -1; s.b -= amt / 2; s.c -= s.ay * (sg * amt / 2)
        s.base = G(s.c.x, s.c.y) + spec.get("zoff", 0)
        s.noplinth = spec.get("noplinth", False)
        s.m = M(name)
        s.anchors = []
        s.tc = spec.get("tc", (1, 1, 1))
        s.clad = spec.get("clad", ["mortar"])
        if isinstance(s.clad, str): s.clad = [s.clad]
        s.sc = spec.get("cladsc", 2.6)
        s.off = (rng.random() * 3, rng.random() * 3)
        front = spec.get("front", (0, 1))
        s.nside = [-s.ay, s.ax, s.ay, -s.ax]
        fv = V((front[0], front[1], 0)).normalized()
        s.fi = max(range(4), key=lambda i: s.nside[i].dot(fv))
        s.frames = []
        cs = [s.c - s.ax * s.a - s.ay * s.b, s.c + s.ax * s.a - s.ay * s.b, s.c + s.ax * s.a + s.ay * s.b, s.c - s.ax * s.a + s.ay * s.b]
        s.corners = [V((p.x, p.y, s.base)) for p in cs]
        s.len = [2 * s.a, 2 * s.b, 2 * s.a, 2 * s.b]
        for i in range(4):
            p0 = s.corners[i]; p1 = s.corners[(i + 1) % 4]
            s.frames.append(Frame(p0, (p1 - p0).normalized(), Z, s.nside[i]))
        s.roofkind = spec.get("roof", "gable")
        s.over = spec.get("over", .45)
        s.pitch = spec.get("pitch", .42)
        # ridge axis: 0 along ax (eaves on sides 0,2), 1 along ay
        s.rax = spec.get("rax", 0 if s.a >= s.b else 1)
        s.La, s.Tb = (s.a, s.b) if s.rax == 0 else (s.b, s.a)
        s.axL, s.axT = (s.ax, s.ay) if s.rax == 0 else (s.ay, -s.ax)
        rise = (s.Tb + s.over) * s.pitch if s.roofkind in ("gable", "hip", "kanban", "irimoya") else ((2 * s.Tb + 2 * s.over) * s.pitch if s.roofkind == "mono" else 0)
        s.rise = rise
        s.e = max(st * 2.35, H - rise) if s.roofkind != "flat" else H     # eave height above base
        s.fh = min(3.1, s.e / st) if s.roofkind != "flat" else min(3.2, (H - .7) / st)
        s.holes = [[], [], [], []]     # per side (x0,y0,x1,y1)
        s.ops = []                     # deferred opening builders

    def role(s, i): return {0: "front", 2: "back", 1: "right", 3: "left"}[(i - s.fi) % 4]

    def is_eave_side(s, i): return (i % 2 == 0) == (s.rax == 0)

    def wall_top(s):
        return s.e - .14

    # ---- openings ----
    def add_win(s, i, x, y, w, h, kind="sash", **kw):
        s.holes[i].append((x, y, x + w, y + h)); s.ops.append(("win", i, x, y, w, h, kind, kw))

    def add_door(s, i, x, w=.85, h=2.02, kind="steel", tc=(1, 1, 1)):
        y = .18
        s.holes[i].append((x, y, x + w, y + h)); s.ops.append(("door", i, x, y, w, h, kind, {"tc": tc}))

    def add_garage(s, i, x, w, h=2.25, kind="shutter"):
        s.holes[i].append((x, .02, x + w, h)); s.ops.append(("garage", i, x, .02, w, h - .02, kind, {}))

    def add_shop(s, i, x, w, h=2.6):
        s.holes[i].append((x, .02, x + w, h)); s.ops.append(("shop", i, x, .02, w, h - .02, "", {}))

    def fenestrate(s, skip=(), widths=None, kinds=None, sparse=None):
        """Bays differ by side and floor but stack loosely, as in-fill houses do."""
        R = s.rng
        for i in range(4):
            if i in skip: continue
            role = s.role(i); w = s.len[i]
            WS = (widths or {}).get(role) or {"front": [1.65, 1.2, .9, 1.65], "back": [.6, .9, .75, 1.2], "left": [.6, .75, .9], "right": [.6, .9, .75]}[role]
            KS = (kinds or {}).get(role) or {"front": ["sash", "sash", "guard", "curtain"], "back": ["frost", "frost", "sash", "guard"], "left": ["frost", "sash", "frost"], "right": ["frost", "sash", "frost"]}[role]
            sp = (sparse or {}).get(role, {"front": .1, "back": .3, "left": .45, "right": .45}[role])
            prev = []
            for fl in range(s.st):
                y0 = fl * s.fh
                bays = []
                x = .55 + R.random() * .35
                while x < w - 1.0:
                    W = R.choice(WS)
                    if x + W > w - .5:
                        W = w - .5 - x
                        if W < .55: break
                    if R.random() > sp:
                        bays.append((x, W))
                    x += W + R.uniform(.55, 1.3)
                if prev and R.random() < .55:      # second floor roughly stacks over the first
                    bays = [(b[0] + R.choice((0, 0, .12, -.1)), b[1]) for b in prev if R.random() > .15]
                prev = bays
                for x_, W in bays:
                    k = R.choice(KS)
                    if W <= .65: H_, sill = .6, 1.3; k = "frost" if R.random() < .7 else k
                    elif k == "frost": H_, sill = .9, 1.05
                    elif W >= 1.6 and R.random() < .4 and fl > 0: H_, sill = 1.75, .35
                    else: H_, sill = 1.1, .9
                    yy = y0 + sill + (.12 if fl == 0 else 0)
                    if yy + H_ > s.wall_top() - .2: continue
                    if any(not (x_ + W < h[0] - .1 or x_ > h[2] + .1 or yy + H_ < h[1] - .1 or yy > h[3] + .1) for h in s.holes[i]): continue
                    s.add_win(i, x_, yy, W, H_, k)

    # ---- walls ----
    def build_walls(s):
        C = .03
        for i in range(4):
            f = s.frames[i]; w = s.len[i]
            bands = []
            nb = len(s.clad)
            top = s.wall_top() if s.roofkind != "flat" else s.H + .0
            if s.roofkind == "kanban" and i == s.fi: top = s.sp.get("parapet", s.e + 1.4)
            for k in range(nb):
                y0 = k * s.fh if k else (-.6 if not s.noplinth else 0)
                y1 = (k + 1) * s.fh if k < nb - 1 else top
                bands.append((s.clad[k], y0, y1))
            # side-specific cladding wins
            sc = s.sp.get("sideclad", {}).get(s.role(i))
            if sc: bands = [(sc, -.6, top)]
            for mat, y0, y1 in bands:
                hs = [(h[0], h[1] - y0, h[2], h[3] - y0) for h in s.holes[i] if h[1] < y1 and h[3] > y0]
                hs = [(h[0], max(h[1], 0), h[2], min(h[3], y1 - y0)) for h in hs]
                ff = Frame(f.p(0, y0, 0), f.u, f.v, f.n)
                wall(s.m, mat, ff, w - 2 * C, y1 - y0, hs, a0=C, tc=s.tc_for(mat), off=(s.off[0] + i * 1.3, y0 + s.off[1]), sc=s.sc_for(mat),
                     top=top - y0 if False else top, base_z=s.base, bump=s.bump_for(mat), amt=s.sp.get("weather", 1.0))
                if y0 > 0:  # storey band trim where cladding changes
                    box(s.m, "alu", f, C, w - C, y0 - .03, y0 + .03, 0, .022, ch=.006, col=(.6, .58, .55))
            # plinth
            if s.noplinth:
                n0 = s.nside[i]; n1 = s.nside[(i + 1) % 4]; mat = bands[-1][0]
                corner_strip(s.m, s.corner_mat(mat), s.corners[(i + 1) % 4], n0, n1, C, top, 1.0, s.tc_for(mat), s.base, top)
                continue
            segs = []; x = 0
            for h in sorted(s.holes[i]):
                if h[1] < .36:
                    if h[0] > x: segs.append((x, h[0]))
                    x = h[2]
            if x < w: segs.append((x, w))
            for a, b in segs:
                if b - a < .02: continue
                ff = Frame(f.p(0, -.5, .016), f.u, f.v, f.n)
                wall(s.m, "concrete", ff, b - a, .84, (), a0=a, seg=.42, tc=(.78, .77, .74), off=(s.off[0], 0), sc=2.2, top=.84, base_z=s.base, bump=0, amt=.9)
                box(s.m, "plinth_top", f, a, b, .33, .345, 0, .038, ch=.004, col=(.42, .41, .4))
            # rounded corners
            n0 = s.nside[i]; n1 = s.nside[(i + 1) % 4]
            mat = bands[-1][0]
            p = s.corners[(i + 1) % 4]
            corner_strip(s.m, s.corner_mat(mat), p, n0, n1, C, top, 1.0, s.tc_for(mat), s.base, top)

    def tc_for(s, mat):
        c = s.sp.get("tcs", {}).get(mat, s.tc)
        if mat in ("mortar", "beige", "plaster"):      # grey base maps: lift and saturate the tint
            g = sum(c) / 3
            return tuple(max(.05, (g + (x - g) * 1.5) * 1.22) for x in c)
        return c

    def sc_for(s, mat):
        return {"facetile": 1.6, "whitetile": 1.15, "tin": 1.6, "rustytin": 1.9, "galva": 1.9, "blackplank": 2.2, "cedar": 1.9, "plank": 1.9,
                "siding": 1.7, "siding2": 1.7, "beige": 3.1, "mortar": 3.4, "plaster": 2.6, "mossy": 3.0, "darkface": .95,
                "plaster5": 2.2, "rough3": 1.2, "cracked": 2.0, "damaged": 2.2}.get(mat, s.sc)

    def bump_for(s, mat):
        return .006 if mat in ("mortar", "plaster", "beige", "greyplaster") else .0015

    def corner_mat(s, mat):
        return "alu" if mat in ("tin", "rustytin", "galva", "siding", "siding2") else mat

    # ---- gable infill / sloped tops ----
    def top_fill(s, i, h_of):
        """Wall above the eave line up to h_of(a)."""
        f = s.frames[i]; w = s.len[i]; y0 = s.wall_top()
        nu = max(2, int(w / .4)); nv = 4
        P = []; UV = []; C = []
        mat = s.sp.get("gableclad") or s.clad[-1]
        sc = s.sc_for(mat); tc = s.tc_for(mat)
        for iu in range(nu + 1):
            a = w * iu / nu; top = max(h_of(a), y0)
            r = []; q = []; c = []
            for j in range(nv + 1):
                y = lerp(y0, top, j / nv); p = f.p(a, y, 0)
                r.append(p); q.append(((a + s.off[0] + i * 1.3) / sc, (y + s.off[1]) / sc))
                c.append(wall_col(p, s.base, top + .2, tc, s.sp.get("weather", 1.0)))
            P.append(r); UV.append(q); C.append(c)
        s.m.grid(mat, P, UV, C, smooth=False)

    # ---- roofs ----
    def Q(s, l, t, z):
        p = s.c + s.axL * l + s.axT * t
        return V((p.x, p.y, s.base + z))

    def build_roof(s):
        k = s.roofkind; rm = s.sp.get("roofmat", "kawara")
        R = s.rng; o = s.over; L = s.La; T = s.Tb; e = s.e
        pal = s.sp.get("palette", ((.105, .11, .12), (.08, .085, .095), (.14, .145, .155)))
        g = s.sp.get("gover", .32)
        rcol = s.sp.get("roofcol", (.09, .095, .105))
        if k in ("gable", "kanban"):
            zr = e + (T + o) * s.pitch
            if k == "kanban": g = .05
            for sg in (1, -1):
                A, B = s.Q(-L - g, sg * (T + o), e), s.Q(L + g, sg * (T + o), e)
                Cc, D = s.Q(L + g, 0, zr), s.Q(-L - g, 0, zr)
                if sg < 0: A, B, Cc, D = B, A, D, Cc
                s.slope(rm, A, B, Cc, D, pal, rcol)
            s.fascia(s.Q(-L - g, T + o, e), s.Q(L + g, T + o, e), s.axT)
            s.fascia(s.Q(L + g, -T - o, e), s.Q(-L - g, -T - o, e), -s.axT)
            if rm == "kawara": ridge(s.m, s.Q(-L - g - .05, 0, zr + .02), s.Q(L + g + .05, 0, zr + .02), R, col=rcol)
            else: s.metal_cap(s.Q(-L - g, 0, zr + .01), s.Q(L + g, 0, zr + .01))
            for sg in (1, -1):        # verge boards and gable infill
                for t_ in (1, -1):
                    s.verge(s.Q(sg * (L + g), t_ * (T + o), e), s.Q(sg * (L + g), 0, zr), rm, rcol, s.axL * sg)
            for i in range(4):
                if not s.is_eave_side(i):
                    # gable top: height as function of distance along wall
                    s.top_fill(i, lambda a, w=s.len[i]: s.wall_top() + (T - abs(a - w / 2)) * s.pitch + (o * s.pitch) + .14 - .05)
        elif k == "hip":
            r = max(0, L - T - o + .0)
            zr = e + (T + o) * s.pitch
            for sg in (1, -1):
                A, B = s.Q(-L - o, sg * (T + o), e), s.Q(L + o, sg * (T + o), e)
                Cc, D = s.Q(r, 0, zr), s.Q(-r, 0, zr)
                if sg < 0: A, B, Cc, D = B, A, D, Cc
                s.slope(rm, A, B, Cc, D, pal, rcol)
                A, B = s.Q(sg * (L + o), -sg * (T + o), e), s.Q(sg * (L + o), sg * (T + o), e)
                Pk = s.Q(sg * r, 0, zr)
                s.slope(rm, A, B, Pk, Pk.copy(), pal, rcol)
                for t_ in (1, -1):
                    ridge(s.m, s.Q(sg * (L + o), t_ * (T + o), e + .02), s.Q(sg * r, 0, zr + .02), R, col=rcol, layers=2, cap=.07)
            if r > .05: ridge(s.m, s.Q(-r, 0, zr + .02), s.Q(r, 0, zr + .02), R, col=rcol)
            s.fascia(s.Q(-L - o, T + o, e), s.Q(L + o, T + o, e), s.axT)
            s.fascia(s.Q(L + o, -T - o, e), s.Q(-L - o, -T - o, e), -s.axT)
            s.fascia(s.Q(L + o, T + o, e), s.Q(L + o, -T - o, e), s.axL, gutter=False)
            s.fascia(s.Q(-L - o, -T - o, e), s.Q(-L - o, T + o, e), -s.axL, gutter=False)
        elif k == "irimoya":
            zr = e + (T + o) * s.pitch
            lg = max(.6, L - .35)                 # gable plane
            ht = (T + o) * .42; zm = zr - ht * s.pitch
            for sg in (1, -1):
                A, B = s.Q(-L - o, sg * (T + o), e), s.Q(L + o, sg * (T + o), e)
                Cc, D = s.Q(lg, 0, zr), s.Q(-lg, 0, zr)
                if sg < 0: A, B, Cc, D = B, A, D, Cc
                s.slope(rm, A, B, Cc, D, pal, rcol)
                A, B = s.Q(sg * (L + o), -sg * (T + o), e), s.Q(sg * (L + o), sg * (T + o), e)
                Cc, D = s.Q(sg * lg, sg * ht, zm), s.Q(sg * lg, -sg * ht, zm)
                s.slope(rm, A, B, Cc, D, pal, rcol)
                # vertical gable screen with lattice boards
                P = [s.Q(sg * lg, -ht, zm), s.Q(sg * lg, ht, zm), s.Q(sg * lg, 0, zr)]
                c = (.42, .34, .26)
                s.m.poly("soffit", P, [(p.x * .5 + p.y * .5, p.z * .5) for p in P], c)
                for t_ in (1, -1):
                    ridge(s.m, s.Q(sg * (L + o), t_ * (T + o), e + .02), s.Q(sg * lg, t_ * ht, zm + .02), R, col=rcol, layers=2, cap=.07)
                    ridge(s.m, s.Q(sg * lg, t_ * ht, zm + .03), s.Q(sg * lg, 0, zr + .02), R, col=rcol, layers=2, cap=.07)
            ridge(s.m, s.Q(-lg, 0, zr + .02), s.Q(lg, 0, zr + .02), R, col=rcol)
            s.fascia(s.Q(-L - o, T + o, e), s.Q(L + o, T + o, e), s.axT)
            s.fascia(s.Q(L + o, -T - o, e), s.Q(-L - o, -T - o, e), -s.axT)
            s.fascia(s.Q(L + o, T + o, e), s.Q(L + o, -T - o, e), s.axL, gutter=False)
            s.fascia(s.Q(-L - o, -T - o, e), s.Q(-L - o, T + o, e), -s.axL, gutter=False)
        elif k == "mono":
            # high side at -T; drains to +T
            zh = e + 2 * (T + o) * s.pitch
            A, B = s.Q(-L - g, T + o, e), s.Q(L + g, T + o, e)
            Cc, D = s.Q(L + g, -T - o, zh), s.Q(-L - g, -T - o, zh)
            s.slope(rm, A, B, Cc, D, pal, rcol)
            s.fascia(A, B, s.axT)
            s.fascia(s.Q(L + g, -T - o, zh), s.Q(-L - g, -T - o, zh), -s.axT, gutter=False)
            for sg in (1, -1):
                s.verge(s.Q(sg * (L + g), T + o, e), s.Q(sg * (L + g), -T - o, zh), rm, rcol, s.axL * sg)
            for i in range(4):
                n = s.nside[i]
                if not s.is_eave_side(i):
                    f = s.frames[i]; w = s.len[i]
                    def hf(a, f=f):
                        p = f.p(a); t = (V((p.x, p.y, 0)) - s.c).dot(s.axT)
                        return e + (T + o - t) * s.pitch - .05
                    s.top_fill(i, hf)
                elif n.dot(s.axT) < 0:
                    h = e + (T + o + T) * s.pitch - .05
                    s.top_fill(i, lambda a, h=h: h)
        elif k == "flat":
            s.flat_roof()
        s.soffit(k)

    def slope(s, rm, A, B, Cc, D, pal, rcol):
        if rm == "kawara":
            tile_slope(s.m, A, B, Cc, D, s.rng, pal)
        elif rm == "slate":
            seam_slope(s.m, A, B, Cc, D, "slate", None, s.sp.get("slatetc", (.8, .8, .82)), sc=2.0, pitch=99)
        else:
            seam_slope(s.m, A, B, Cc, D, rm, rm, s.sp.get("roofcol", (.8, .8, .82)), pitch=s.sp.get("ribp", .455), sc=1.9)

    def metal_cap(s, a, b):
        f = Frame(a, (b - a).normalized(), Z)
        box(s.m, "galva", f, 0, (b - a).length, -.02, .03, -.12, .12, ch=.012, col=s.sp.get("roofcol", (.75, .75, .77)), sc=1.9)

    def fascia(s, a, b, out, gutter=True):
        """Fascia board plus optional hanging half-round gutter."""
        u = (b - a).normalized(); L = (b - a).length
        f = Frame(a, u, Z, out)
        c = s.sp.get("fasciacol", (.55, .52, .48))
        box(s.m, "alu" if s.sp.get("metalfascia") else "fasciaw", f, -.0, L, -.16, -.005, -.03, .0, ch=.006, col=c, sc=1.5)
        if gutter and s.sp.get("gutter", True):
            col = s.sp.get("guttercol", (.56, .54, .5))
            r = .056; n = 7
            P = []; UV = []
            for i in range(n + 1):
                th = pi * i / n
                x = cos(th) * r; y = -sin(th) * r
                P.append([f.p(0, -.075 + y, .07 + x), f.p(L, -.075 + y, .07 + x)])
                UV.append([(i / n, 0), (i / n, L)])
            s.m.grid("pvc", P, UV, [[col, col] for _ in P], smooth=True)
            for j in range(int(L / .75) + 1):
                box(s.m, "alu", f, j * .75 + .1, j * .75 + .125, -.14, -.07, -.0, .13, col=(.45, .45, .45))
            s.gutters = getattr(s, "gutters", []) + [(f, L)]

    def downpipes(s):
        """One or two rain leaders dropping from gutter ends; offset so they read hand-installed."""
        col = s.sp.get("guttercol", (.56, .54, .5))
        for f, L in getattr(s, "gutters", []):
            a = .22 if s.rng.random() < .5 else L - .22
            top = f.p(a, -.1, .07)
            # find wall offset: fascia lies over.overhang beyond wall
            back = f.p(a, -.5, -s.over + .06)
            G_ = V((back.x, back.y, s.base - .05))
            tube(s.m, "pvc", [top, f.p(a, -.26, .07), back + Z * .05, back - Z * 1.0, G_], .03, 8, col)
            for z in frange(s.base + .8, back.z - .4, 1.35):
                pt = V((back.x, back.y, z))
                box(s.m, "alu", Frame(pt, f.u, Z, f.n), -.04, .04, -.015, .015, -.05, .036, col=(.5, .5, .5))

    def verge(s, a, b, rm, col, out):
        u = (b - a).normalized(); L = (b - a).length
        vup = out.cross(u).normalized()
        if vup.z < 0: vup = -vup
        f = Frame(a, u, vup, out)
        box(s.m, "fasciaw", f, 0, L, -.17, -.02, -.03, .0, ch=.006, col=s.sp.get("fasciacol", (.55, .52, .48)), sc=1.5)
        if rm == "kawara":
            box(s.m, "kawara", f, 0, L, 0, .05, -.1, .015, ch=.012, col=col, sc=.8)
            tube(s.m, "kawara", [f.p(0, .05, -.02), f.p(L, .05, -.02)], .05, 8, col, sc=1.)
        else:
            box(s.m, "alu", f, 0, L, -.02, .05, -.03, .012, ch=.004, col=(.5, .5, .5))

    def soffit(s, k):
        if k == "flat": return
        o = s.over; y = s.e - .14
        c = s.sp.get("soffitcol", (.72, .68, .6))
        for i in range(4):
            eave = s.is_eave_side(i) or k in ("hip", "irimoya")
            if not eave: continue
            if k == "mono" and s.nside[i].dot(s.axT) < 0: continue
            if k == "kanban" and i == s.fi: continue
            f = s.frames[i]; w = s.len[i]
            ex = o if k in ("hip", "irimoya") else s.sp.get("gover", .32)
            P = [f.p(-ex, y, o), f.p(w + ex, y, o), f.p(w + ex, y, 0), f.p(-ex, y, 0)]
            s.m.poly("soffit", P, [(p[0] / 1.9, p[1] / 1.9) for p in P], c)
            # rafter tails break the flat soffit
            n = int(w / .91)
            for j in range(n + 1):
                a = j * w / max(n, 1)
                box(s.m, "soffit", f, a - .03, a + .03, y - .07, y, 0, o, ch=.004, col=tint(c, .85), sc=1.9)

    def flat_roof(s):
        H = s.H; ph = .62
        c = s.sp.get("capcol", (.62, .6, .58))
        L = s.a; T = s.b
        for i in range(4):
            f = s.frames[i]; w = s.len[i]
            box(s.m, "alu", f, -.04, w + .04, H, H + .035, -.2, .03, ch=.008, col=c)
            # inner parapet
            P = [f.p(.15, H, -.15), f.p(w - .15, H, -.15), f.p(w - .15, H - ph, -.15), f.p(.15, H - ph, -.15)]
            s.m.poly("concrete", P, [(p[0] / 2.2, p[2] / 2.2) for p in P], (.6, .6, .58))
        g = s.corners
        p = [g[0] + s.ax * .15 + s.ay * .15, g[1] - s.ax * .15 + s.ay * .15, g[2] - s.ax * .15 - s.ay * .15, g[3] + s.ax * .15 - s.ay * .15]
        P = [[lerp(lerp(p[0], p[1], a / 6), lerp(p[3], p[2], a / 6), b / 6) + Z * (H - ph) for b in range(7)] for a in range(7)]
        UV = [[(q.x / 2.5, q.y / 2.5) for q in r] for r in P]
        CC = [[wall_col(q, 0, 999, (.62, .6, .57), 1.5) for q in r] for r in P]
        s.m.grid("concrete", P, UV, CC, smooth=False)
        s.rooftop_clutter(p, H - ph)

    def rooftop_clutter(s, p, z):
        """Skyline: antennas, parapet-mounted mast, water tank; these are parts of the building, not street props."""
        R = s.rng
        c = (p[0] + p[2]) / 2 + Z * z
        if s.sp.get("tank"):
            tube(s.m, "steel", [c + V((0, 0, .9)), c + V((0, 0, 2.1))], .62, 16, (.55, .55, .52), sc=2.)
            tube(s.m, "steel", [c + V((0, 0, 2.08)), c + V((0, 0, 2.14))], .4, 16, (.5, .5, .48), sc=2.)
            for dx, dy in ((-.45, -.45), (.45, -.45), (.45, .45), (-.45, .45)):
                tube(s.m, "steel", [c + V((dx, dy, 0)), c + V((dx, dy, 1))], .03, 6, (.35, .34, .32))
        s.antenna(p[1].lerp(p[2], .3) + Z * z)

    def antenna(s, base, h=2.8):
        col = (.55, .55, .56)
        tube(s.m, "alu", [base, base + Z * h], .02, 6, col)
        R = s.rng; yaw = R.random() * pi
        d = V((cos(yaw), sin(yaw), 0)); e = V((-sin(yaw), cos(yaw), 0))
        for z_, L in ((h - .05, 1.3), (h - .5, 1.0)):
            tube(s.m, "alu", [base + Z * z_ - d * L * .5, base + Z * z_ + d * L * .5], .008, 4, col)
            for k in range(9):
                t = -.45 + k * .11; w = .42 - k * .022
                pp = base + Z * z_ + d * (L * t)
                tube(s.m, "alu", [pp - e * w * .5, pp + e * w * .5], .004, 4, col)
        if s.sp.get("dish"):
            pass

    # ---- detail attachments ----
    def lean(s, i, x0, x1, z, depth=.95, drop=.34, mat="kawara"):
        """Lean-to pentroof between floors, a strong silhouette breaker."""
        f = s.frames[i]; R = s.rng
        pal = s.sp.get("palette", ((.105, .11, .12), (.08, .085, .095), (.14, .145, .155)))
        rcol = s.sp.get("roofcol", (.09, .095, .105))
        A = f.p(x0, z - drop, depth); B = f.p(x1, z - drop, depth); Cc = f.p(x1, z, .0); D = f.p(x0, z, 0)
        # wall-side order keeps nn up
        if mat == "kawara":
            tile_slope(s.m, B, A, D, Cc, R, pal) if (B - A).cross(D - A).z < 0 and False else tile_slope(s.m, A, B, Cc, D, R, pal)
        else:
            seam_slope(s.m, A, B, Cc, D, mat, mat, s.sp.get("roofcol", (.7, .7, .72)), sc=1.9)
        fo = Frame(A, (B - A).normalized(), Z, f.n)
        L = (B - A).length
        box(s.m, "fasciaw", fo, 0, L, -.15, -.01, -.03, .0, ch=.006, col=s.sp.get("fasciacol", (.5, .47, .43)), sc=1.5)
        s.fascia(A, B, f.n) if s.sp.get("lean_gutter") else None
        # flashing against wall
        box(s.m, "alu", f, x0, x1, z - .02, z + .1, 0, .014, ch=.003, col=(.45, .45, .45))
        for a in frange(x0 + .15, x1, .91):   # brackets
            box(s.m, "soffit", f, a - .035, a + .035, z - drop - .22, z - drop - .12, 0, depth, ch=.006, col=(.5, .46, .4), sc=1.9)
        P = [f.p(x0, z - drop - .14, depth), f.p(x1, z - drop - .14, depth), f.p(x1, z - drop - .14, 0), f.p(x0, z - drop - .14, 0)]
        s.m.poly("soffit", P, [(p[0] / 1.9, p[1] / 1.9) for p in P], (.62, .58, .5))

    def balcony(s, i, x0, x1, fl, depth=.88, style="bars"):
        f = s.frames[i]; y = fl * s.fh + .02
        R = s.rng
        scol = s.sp.get("railcol", (.6, .6, .6))
        if style == "conc":
            box(s.m, "concrete", f, x0, x1, y - .16, y, 0, depth, ch=.01, col=(.72, .71, .68), sc=2.2)
        else:
            box(s.m, "steel", f, x0, x1, y - .1, y, 0, depth, ch=.006, col=(.55, .55, .55), sc=1.2)
            for a in frange(x0 + .03, x1, (x1 - x0) / max(1, round((x1 - x0) / 1.2))):
                box(s.m, "steel", f, a - .03, a + .03, y - .4, y, depth - .1, depth - .04, col=(.45, .44, .42), sc=1.2)
        # rail
        h = 1.08
        for a in (x0 + .02, x1 - .02):
            for c in (depth - .03,):
                tube(s.m, "alu", [f.p(a, y, c), f.p(a, y + h, c)], .018, 6, scol)
            tube(s.m, "alu", [f.p(a, y + h, depth - .03), f.p(a, y + h, .02)], .016, 6, scol)
            tube(s.m, "alu", [f.p(a, y + .5, depth - .03), f.p(a, y + .5, .02)], .012, 6, scol)
        tube(s.m, "alu", [f.p(x0, y + h, depth - .03), f.p(x1, y + h, depth - .03)], .02, 6, scol)
        if style in ("bars", "conc"):
            tube(s.m, "alu", [f.p(x0, y + .08, depth - .03), f.p(x1, y + .08, depth - .03)], .012, 6, scol)
            for a in frange(x0 + .1, x1 - .05, .11):
                tube(s.m, "alu", [f.p(a, y + .08, depth - .03), f.p(a, y + h, depth - .03)], .0075, 4, scol)
        elif style == "panel":
            P = [f.p(x0 + .03, y + .1, depth - .03), f.p(x1 - .03, y + .1, depth - .03), f.p(x1 - .03, y + h - .06, depth - .03), f.p(x0 + .03, y + h - .06, depth - .03)]
            s.m.poly("polyc", P, [((p[0] + p[1]) / 1.6, p[2] / 1.6) for p in P], (.92, .92, .88))
        # laundry brackets and poles (fixed to the balcony)
        for a in (x0 + .18, x1 - .18):
            tube(s.m, "alu", [f.p(a, y + 2.0, .0), f.p(a, y + 1.92, .55)], .012, 5, (.5, .5, .5))
        tube(s.m, "alu", [f.p(x0 + .05, y + 1.92, .55), f.p(x1 - .05, y + 1.92, .55)], .014, 6, (.72, .72, .7))
        tube(s.m, "alu", [f.p(x0 + .05, y + 1.93, .34), f.p(x1 - .05, y + 1.93, .34)], .012, 6, (.6, .62, .68))

    def hisashi(s, i, x, y, w, depth=.42):
        """Small steel window hood, slightly bent."""
        f = s.frames[i]
        a = f.p(x - .08, y + .1, 0); b = f.p(x + w + .08, y + .1, 0); c = f.p(x + w + .08, y - .02, depth); d = f.p(x - .08, y - .02, depth)
        n = int(w / .1)
        P = []; UV = []
        for k in range(n + 1):
            t = k / max(n, 1); j = .003 * sin(k * 2.1)
            P.append([lerp(d, c, t) + Z * j, lerp(a, b, t) + Z * j]); UV.append([(t * w / 1.6, 0), (t * w / 1.6, depth / 1.6)])
        col = s.sp.get("hisashicol", (.5, .5, .5))
        s.m.grid("galva", P, UV, [[col, col] for _ in P], smooth=False)
        box(s.m, "alu", f, x - .08, x + w + .08, y - .05, y - .02, depth - .01, depth + .01, col=(.45, .45, .45))

    # ---- deferred openings ----
    def build_openings(s):
        for op in s.ops:
            t, i, x, y, w, h, kind, kw = op
            f = s.frames[i]
            if t == "win": s.window(f, i, x, y, w, h, kind, **kw)
            elif t == "door": s.door(f, x, y, w, h, kind, **kw)
            elif t == "garage": s.garage(f, x, y, w, h, kind)
            elif t == "shop": s.shop(f, i, x, y, w, h)

    def reveal(s, f, x, y, w, h, d, mat, tc):
        sc = 1.5
        for pts in (
            [(x, y, 0), (x + w, y, 0), (x + w, y, -d), (x, y, -d)],
            [(x + w, y + h, 0), (x, y + h, 0), (x, y + h, -d), (x + w, y + h, -d)],
            [(x, y + h, 0), (x, y, 0), (x, y, -d), (x, y + h, -d)],
            [(x + w, y, 0), (x + w, y + h, 0), (x + w, y + h, -d), (x + w, y, -d)]):
            P = [f.p(*p) for p in pts]
            s.m.poly(mat, P, [((p[0] + p[2]) / sc, (p[1] + p[2]) / sc) for p in pts], tint(tc, .75))

    def window(s, f, i, x, y, w, h, kind="sash", **kw):
        R = s.rng; m = s.m
        d = .1 if kind != "lattice" else .06
        wm = s.band_mat(y)
        s.reveal(f, x, y, w, h, d, wm, s.tc_for(wm))
        fc = s.sp.get("framecol", (.62, .6, .57))
        if kind == "lattice": fc = (.3, .22, .15)
        fm = "alu" if kind != "lattice" else "soffit"
        fw = .042; c1 = -.02; c0 = -.095
        # outer frame
        box(m, fm, f, x, x + w, y, y + fw, c0, c1, ch=.004, col=fc)
        box(m, fm, f, x, x + w, y + h - fw, y + h, c0, c1, ch=.004, col=fc)
        box(m, fm, f, x, x + fw, y + fw, y + h - fw, c0, c1, ch=.004, col=fc)
        box(m, fm, f, x + w - fw, x + w, y + fw, y + h - fw, c0, c1, ch=.004, col=fc)
        # sill flashing
        box(m, "alu", f, x - .03, x + w + .03, y - .03, y, -.02, .035, ch=.005, col=tint(fc, .82))
        # sashes
        n = 2 if w > .8 else 1
        if w > 2.4: n = 4
        sw = (w - 2 * fw) / n
        for k in range(n):
            a = x + fw + k * sw
            dz = -.05 if k % 2 == 0 else -.078
            box(m, fm, f, a, a + .034, y + fw, y + h - fw, dz - .012, dz + .012, ch=.003, col=fc)
            box(m, fm, f, a + sw - .034, a + sw, y + fw, y + h - fw, dz - .012, dz + .012, ch=.003, col=fc)
            box(m, fm, f, a, a + sw, y + fw, y + fw + .034, dz - .012, dz + .012, ch=.003, col=fc)
            box(m, fm, f, a, a + sw, y + h - fw - .034, y + h - fw, dz - .012, dz + .012, ch=.003, col=fc)
            if kind in ("lattice",) and k >= 0:
                for t in frange(a + .05, a + sw - .03, .09):
                    box(m, "soffit", f, t - .012, t + .012, y + fw, y + h - fw, dz - .005, dz + .012, col=(.28, .2, .13), sc=1.9)
                box(m, "soffit", f, a, a + sw, y + h * .5 - .012, y + h * .5 + .012, dz - .005, dz + .012, col=(.28, .2, .13), sc=1.9)
        P = [f.p(x + fw, y + fw, -.062), f.p(x + w - fw, y + fw, -.062), f.p(x + w - fw, y + h - fw, -.062), f.p(x + fw, y + h - fw, -.062)]
        frost = kind in ("frost", "guard_f") or (kind == "lattice" and R.random() < .6)
        if frost:
            m.poly("frost", P, [(0, 0), (1, 0), (1, 1), (0, 1)], (.92, .95, .94))
        else:
            m.poly("glass", P, [(0, 0), (1, 0), (1, 1), (0, 1)], (1, 1, 1))
            # interior read: back dark, curtain partly drawn
            B = [f.p(x, y, -.32), f.p(x + w, y, -.32), f.p(x + w, y + h, -.32), f.p(x, y + h, -.32)]
            m.poly("dark", B, None, (.04, .04, .045))
            cc = R.choice(((.86, .84, .78), (.8, .78, .7), (.72, .74, .72), (.78, .66, .55)))
            fr = R.choice((.35, .5, .62, 1.0)) if kind != "curtain" else 1.0
            side = R.random() < .5
            a0 = x if side else x + w * (1 - fr); a1 = a0 + w * fr
            Cc = [f.p(a0, y, -.25), f.p(a1, y, -.25), f.p(a1, y + h, -.25), f.p(a0, y + h, -.25)]
            sh = R.random()
            m.poly("curtain", Cc, [(sh, 0), (sh + (a1 - a0) / 1.3, 0), (sh + (a1 - a0) / 1.3, h / 1.3), (sh, h / 1.3)], cc)
        if kind == "guard":     # aluminium security bars
            gc = (.6, .59, .56)
            for t in frange(x + .08, x + w - .05, .115):
                box(m, "alu", f, t - .009, t + .009, y - .02, y + h + .02, .03, .05, col=gc)
            for yy in (y + .02, y + h - .02):
                box(m, "alu", f, x - .03, x + w + .03, yy - .015, yy + .015, .018, .055, ch=.003, col=gc)
            for a_, b_ in ((x - .03, y), (x + w + .01, y), (x - .03, y + h), (x + w + .01, y + h)):
                box(m, "alu", f, a_, a_ + .02, b_ - .02, b_ + .02, 0, .03, col=gc)
        if kw.get("hood") or (kind != "frost" and R.random() < s.sp.get("hoodp", .28) and h < 1.6):
            s.hisashi(i, x, y + h, w)
        if kw.get("amado"):
            s.tobukuro(f, x + w, y, h)
        # weather streaks hang from both sill ends
        for a in (x - .08, x + w - .2):
            if R.random() < .85:
                L = R.uniform(.5, 1.25)
                decal(m, f, a, y - .03 - L, R.uniform(.26, .4), L, R.randrange(3), flip=R.random() < .5)
        if R.random() < .5:
            L = R.uniform(.5, .9)
            decal(m, f, x + w * R.random() * .6, y - .03 - L, R.uniform(.5, .9), L, R.randrange(3))

    def tobukuro(s, f, x, y, h):
        """Shutter box beside a window."""
        c = s.sp.get("tobucol", (.52, .5, .46))
        box(s.m, "tin" if "tin" in s.sp.get("mats_ok", ("tin",)) else "alu", f, x + .02, x + .58, y - .02, y + h + .02, 0, .1, ch=.006, col=c, sc=1.6)

    def band_mat(s, y):
        k = min(len(s.clad) - 1, int(y // s.fh)) if len(s.clad) > 1 else 0
        return s.clad[k]

    def door(s, f, x, y, w, h, kind, tc=(1, 1, 1)):
        m = s.m; R = s.rng
        wm = s.band_mat(.5)
        s.reveal(f, x, y, w, h, .1, wm, s.tc_for(wm))
        fc = s.sp.get("framecol", (.62, .6, .57))
        for a0, a1, b0, b1 in ((x, x + .05, y, y + h), (x + w - .05, x + w, y, y + h), (x, x + w, y + h - .05, y + h)):
            box(m, "alu", f, a0, a1, b0, b1, -.09, -.015, ch=.004, col=fc)
        if kind == "steel":
            box(m, "paint", f, x + .05, x + w - .05, y, y + h - .05, -.1, -.045, ch=.004, col=tc, sc=1.)
            box(m, "paint", f, x + .13, x + w - .13, y + 1.25, y + h - .22, -.05, -.038, ch=.004, col=tint(tc, .92), sc=1.)
            box(m, "paint", f, x + .13, x + w - .13, y + .22, y + 1.05, -.05, -.038, ch=.004, col=tint(tc, .92), sc=1.)
            hx = x + w - .14
            tube(m, "alu", [f.p(hx, y + 1.0, -.04), f.p(hx, y + 1.0, .012)], .012, 6, (.7, .7, .7))
            tube(m, "alu", [f.p(hx, y + 1.0, .012), f.p(hx - .1, y + 1.0, .012)], .01, 6, (.7, .7, .7))
        else:   # sliding glazed genkan door
            n = 2
            sw = (w - .1) / n
            for k in range(n):
                a = x + .05 + k * sw; dz = -.06 if k else -.08
                for a0, a1, b0, b1 in ((a, a + .05, y, y + h - .05), (a + sw - .05, a + sw, y, y + h - .05), (a, a + sw, y, y + .12), (a, a + sw, y + h - .1, y + h - .05), (a, a + sw, y + .95, y + .98)):
                    box(m, "alu", f, a0, a1, b0, b1, dz - .014, dz + .014, ch=.003, col=fc)
                P = [f.p(a, y, dz), f.p(a + sw, y, dz), f.p(a + sw, y + h, dz), f.p(a, y + h, dz)]
                m.poly("frost", P, None, (.9, .93, .92))
        # step
        box(m, "concrete", f, x - .08, x + w + .08, -.3, y, 0, .38, ch=.012, col=(.7, .7, .67), sc=2.2)

    def garage(s, f, x, y, w, h, kind):
        m = s.m
        wm = s.band_mat(.5)
        s.reveal(f, x, y, w, h, .22, wm, s.tc_for(wm))
        box(m, "alu", f, x - .03, x + w + .03, y + h - .02, y + h + .22, 0, .08, ch=.01, col=(.55, .54, .52))   # shutter box
        for a in (x, x + w - .05):
            box(m, "alu", f, a, a + .05, y, y + h, -.2, -.1, col=(.5, .5, .48))
        P = [f.p(x, y, -.18), f.p(x + w, y, -.18), f.p(x + w, y + h, -.18), f.p(x, y + h, -.18)]
        m.poly("shutter", P, [(p, 0) for p in (0, w / 2)] + [(w / 2, h / 2), (0, h / 2)], (.8, .8, .78))
        decal(m, f, x + .1, y, w - .2, .9, 4, off=-.17)

    def shop(s, f, i, x, y, w, h):
        """Empty shell for the storefront team: reveal, floor, dark back wall and an anchor record."""
        m = s.m; d = .55
        wm = s.band_mat(.5)
        s.reveal(f, x, y, w, h, d, wm, s.tc_for(wm))
        P = [f.p(x, y, -d), f.p(x + w, y, -d), f.p(x + w, y + h, -d), f.p(x, y + h, -d)]
        m.poly("dark", P, None, (.09, .09, .09))
        P = [f.p(x, y + .01, 0), f.p(x + w, y + .01, 0), f.p(x + w, y + .01, -d), f.p(x, y + .01, -d)]
        m.poly("concrete", P, [(p[0] / 2.2, p[1] / 2.2) for p in P], (.5, .5, .5))
        box(m, "alu", f, x - .04, x + w + .04, y + h, y + h + .12, 0, .06, ch=.01, col=(.5, .49, .47))  # lintel flashing
        c = f.p(x + w / 2, y, 0)
        s.anchors.append(dict(type="storefront", building=s.name, center_enu=[round(c.x, 3), round(c.y, 3), round(c.z, 3)],
                              outward_enu=[round(f.n.x, 4), round(f.n.y, 4)], width=round(w, 2), height=round(h, 2), depth=d))

    def anchor(s, kind, i, a, b):
        f = s.frames[i]; c = f.p(a, b, 0)
        s.anchors.append(dict(type=kind, building=s.name, center_enu=[round(c.x, 3), round(c.y, 3), round(c.z, 3)], outward_enu=[round(f.n.x, 4), round(f.n.y, 4)]))

    def services(s):
        """Things bolted on walls by trades over decades: bath vents, conduit, patched joints."""
        R = s.rng; m = s.m
        for i in range(4):
            f = s.frames[i]; w = s.len[i]; role = s.role(i)
            top = s.wall_top()
            if role != "front" and w > 2.5:
                for k in range(R.randint(1, 3) if role == "back" else R.randint(0, 2)):
                    a = R.uniform(.5, w - .5); y = R.uniform(1.9, max(2.0, top - .6))
                    if any(h[0] - .25 < a < h[2] + .25 and h[1] - .25 < y < h[3] + .25 for h in s.holes[i]): continue
                    c = R.choice(((.72, .72, .68), (.6, .58, .52), (.3, .3, .3)))
                    tube(m, "pvc", [f.p(a, y, .0), f.p(a, y, .07)], .085, 14, c, sc=1.)
                    box(m, "pvc", f, a - .1, a + .1, y - .02, y + .1, .06, .11, ch=.012, col=c, sc=1.)     # weather hood
                    L = R.uniform(.4, .9); decal(m, f, a - .14, y - .1 - L, .28, L, R.randrange(3))
                # conduit riser
                if R.random() < .75:
                    a = R.uniform(.25, w - .25)
                    if not any(h[0] - .1 < a < h[2] + .1 for h in s.holes[i]):
                        y0 = R.uniform(.7, 1.3); y1 = top - .15
                        tube(m, "pvc", [f.p(a, y0, .02), f.p(a, y1, .02)], .013, 6, (.6, .6, .57))
                        for y in frange(y0 + .1, y1, .7):
                            box(m, "alu", f, a - .022, a + .022, y - .012, y + .012, 0, .036, col=(.5, .5, .5))
                        box(m, "alu", f, a - .09, a + .09, y0 - .17, y0, 0, .06, ch=.008, col=(.62, .62, .6))
            mt = s.band_mat(.5)
            if mt in ("mortar", "beige", "plaster") and s.st >= 2:      # horizontal crack-control joint at floor line
                for fl in range(1, s.st):
                    y = fl * s.fh + .02
                    box(m, "dark", f, .03, w - .03, y, y + .012, -.002, .001, col=(.1, .1, .1))
                    box(m, "alu", f, .03, w - .03, y - .055, y - .005, 0, .012, ch=.003, col=(.55, .55, .53)) if R.random() < .4 else None

    def surface_decals(s):
        """Ground damp bands, wall cracks and rust keyed to cladding."""
        R = s.rng; m = s.m
        for i in range(4):
            f = s.frames[i]; w = s.len[i]
            x = R.random() * .6
            while x < w - .3:
                L = R.uniform(1.0, 2.2); hgt = R.uniform(.55, 1.2)
                if s.clad[0] in ("darkface", "plank", "blackplank", "cedar") or s.band_mat(.5) in ("darkface", "plank", "blackplank", "cedar"):
                    x += L; continue
                if s.clad[0] in ("whitetile", "facetile"): hgt *= .55
                if any(h[1] < .4 and not (x + min(L, w - x) < h[0] or x > h[2]) for h in s.holes[i]):
                    x += L * .6; continue
                decal(m, f, x, .3, min(L, w - x), hgt, R.choice((4, 5, 4, 8) if s.sp.get("moss") and s.role(i) != "front" else (4, 5)), off=.0065)
                x += L * R.uniform(.7, 1.2)
            # eave staining
            top = s.wall_top()
            for k in range(int(w / (.75 if s.clad[0] == "whitetile" else 1.6))):
                a = R.random() * (w - .6); L = R.uniform(.9, 2.0 if s.clad[0] != "whitetile" else 3.6)
                decal(m, f, a, top - L, R.uniform(.35, .7), L, R.randrange(3), off=.005)
            mt = s.clad[0]
            if mt in ("mortar", "plaster", "beige", "greyplaster", "mossy"):
                for k in range(R.randint(0, 1)):
                    sz = R.uniform(.7, 1.3)
                    decal(m, f, R.random() * max(.1, w - sz), R.uniform(.6, top - sz), sz, sz, R.choice((9, 10)), off=.0055)
                for k in range(R.randint(0, 1)):
                    sz = R.uniform(.5, 1.0)
                    decal(m, f, R.random() * max(.1, w - sz), R.uniform(.5, top - sz), sz, sz * .8, R.choice((6, 7)), off=.0045)
            if mt in ("tin", "rustytin", "galva") or s.sp.get("rust"):
                for k in range(int(w / 1.2)):
                    L = R.uniform(.9, 2.2)
                    decal(m, f, R.random() * (w - .5), R.uniform(.3, top - L), R.uniform(.25, .5), L, 3, off=.006)

    def build(s):
        s.build_walls()
        s.build_roof()
        s.build_openings()
        s.downpipes()
        s.services()
        s.surface_decals()
        return s.m


def frange(a, b, st):
    out = []; x = a
    while x < b:
        out.append(x); x += st
    return out


# ---- ground ----
def pip(pt, poly):
    x, y = pt; c = False; n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0: c = not c
    return c


def ribbon_lids(m, pts, G, R, width=.36, mat="concrete", seg=.6, grate_every=9, h=.018, tc=(.62, .62, .6)):
    """Precast gutter lids along a polyline, the common edge of Tokyo lanes."""
    acc = 0; n = 0
    for k in range(len(pts) - 1):
        a = V((*pts[k], 0)); b = V((*pts[k + 1], 0)); L = (b - a).length
        if L < .02: continue
        u = (b - a).normalized()
        c = int(L / seg)
        for i in range(max(1, c)):
            t0 = i * L / max(1, c); t1 = (i + 1) * L / max(1, c) - .007
            p = a + u * t0
            z = G(p.x, p.y)
            f = Frame((p.x, p.y, z), u, Z, u.cross(Z))
            n += 1
            j = (R.random() - .5) * .01
            if n % grate_every == 0:
                box(m, "steel", f, 0, t1 - t0, h - .05 + j, h - .004 + j, -width / 2, width / 2, ch=.005, col=(.18, .17, .16), sc=1.2)
                for q in frange(-width / 2 + .03, width / 2 - .02, .05):
                    box(m, "dark", f, .03, t1 - t0 - .03, h - .004 + j, h - .002 + j, q, q + .018, col=(.02, .02, .02))
            else:
                box(m, mat, f, 0, t1 - t0, h - .06 + j, h + j, -width / 2, width / 2, ch=.008, col=tint(tc, 1 + (R.random() - .5) * .22), sc=2.2, off=(R.random(), R.random()))
                # hand slot
                box(m, "dark", f, (t1 - t0) / 2 - .05, (t1 - t0) / 2 + .05, h + j, h + .001 + j, -.012, .012, col=(.03, .03, .03))


def block_wall(m, pts, G, R, h=1.2, cap=True, tc=(.72, .71, .68)):
    """Concrete block boundary wall that steps with the ground."""
    for k in range(len(pts) - 1):
        a = V((*pts[k], 0)); b = V((*pts[k + 1], 0)); L = (b - a).length; u = (b - a).normalized()
        n = u.cross(Z)
        s = 1.8; cnt = max(1, int(L / s))
        for i in range(cnt):
            t0 = i * L / cnt; t1 = (i + 1) * L / cnt
            p = a + u * t0
            z = G(p.x, p.y)
            f = Frame((p.x, p.y, z), u, Z, n)
            box(m, "blockwall", f, 0, t1 - t0, -.3, h, -.06, .06, ch=.006, col=tint(tc, 1 + (R.random() - .5) * .15), sc=1.6, off=(t0, z))
            box(m, "concrete", f, -.005, t1 - t0 + .005, h, h + .04, -.075, .075, ch=.01, col=(.6, .6, .58), sc=2.2)
            ff = Frame(f.p(0, 0, .061), u, Z, n)
            decal(m, ff, R.random() * .2, .0, 1.4, R.uniform(.4, .9), R.choice((4, 5, 8)), off=.003)
            ff2 = Frame(f.p(t1 - t0, 0, -.061), -u, Z, -n)
            decal(m, ff2, R.random() * .2, .0, 1.4, R.uniform(.4, .9), R.choice((4, 5, 8)), off=.003)


def road_paint(m, pts, G, width=.13, tc=(.78, .78, .74), lift=.006):
    for k in range(len(pts) - 1):
        a = V((*pts[k], 0)); b = V((*pts[k + 1], 0)); L = (b - a).length; u = (b - a).normalized(); n = u.cross(Z)
        c = max(1, int(L / .8))
        for i in range(c):
            p0 = a + u * (i * L / c); p1 = a + u * ((i + 1) * L / c)
            Q = [p0 - n * width / 2, p1 - n * width / 2, p1 + n * width / 2, p0 + n * width / 2]
            P = [V((q.x, q.y, G(q.x, q.y) + lift)) for q in Q]
            kk = 1 + .25 * nz(p0, .4)
            m.poly("paint", P, [(q.x / 3, q.y / 3) for q in Q], tint(tc, kk))
