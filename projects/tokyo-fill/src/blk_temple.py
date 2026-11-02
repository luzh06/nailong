# Temple architecture kit (Senso-ji splice): curved roofs with tile rolls, brackets, rafters, columns, lanterns, finial.
# All coordinates ENU metres; frames as in blk_core.
from blk_core import *
from blk_arch import frange

SHU = (.74, .13, .07)          # vermilion lacquer
SHU_D = (.5, .09, .05)
TILE = (.105, .11, .115)
GOLD = (1.0, .78, .4)
END = (.9, .82, .55)            # painted rafter and bracket ends


def lerpv(a, b, t): return a + (b - a) * t


class RoofFace:
    """Face of a Japanese roof. n: outward unit (plan), u: lateral unit; d(t), hw(t) plan distance / half-width; z(s,t)."""
    def __init__(s, c, n, u, d0, d1, w0, w1, ze, zt, conc=1.45, lift=.55, t1=1.0):
        s.c = V((c[0], c[1], 0)); s.n = V(n); s.u = V(u); s.d0, s.d1, s.w0, s.w1 = d0, d1, w0, w1; s.ze, s.zt = ze, zt; s.conc, s.lift, s.t1 = conc, lift, t1

    def P(s, sv, t):
        d = lerp(s.d0, s.d1, t); w = lerp(s.w0, s.w1, t)
        z = s.ze + (s.zt - s.ze) * t ** s.conc + s.lift * abs(sv) ** 3 * (1 - t) ** 2
        p = s.c + s.n * d + s.u * (sv * w)
        return V((p.x, p.y, z))

    def N(s, sv, t):
        e = 1e-3
        a = s.P(min(1, sv + e), t) - s.P(max(-1, sv - e), t); b = s.P(sv, min(1, t + e)) - s.P(sv, max(0, t - e))
        n = a.cross(b).normalized()
        return n if n.z > 0 else -n


def roof_face(m, F, R, tiles=True, pitch=.31, nu=18, nv=10, col=TILE, mat="kawara", roll_r=.065, rolls=True):
    P = [[F.P(-1 + 2 * i / nu, j / nv) for j in range(nv + 1)] for i in range(nu + 1)]
    m.grid("roofbase", [[q - V((0, 0, .02)) for q in r] for r in P], None, [[(.3, .3, .3)] * (nv + 1)] * (nu + 1), smooth=True)
    if not rolls: return
    W = 2 * F.w0; k = max(2, int(W / pitch))
    for i in range(k + 1):
        sv = -1 + 2 * i / k
        cc = tint(col, 1 + (R.random() - .5) * .14)
        pts = [F.P(sv, j / 8) + F.N(sv, j / 8) * .045 for j in range(9)]
        tube(m, mat, pts, roll_r, 6, cc, sc=.6)
        # round eave-end tile (nokimarugawara)
        a = F.P(sv, 0) + F.N(sv, 0) * .045; dv = (F.P(sv, .03) - F.P(sv, 0)).normalized()
        tube(m, mat, [a - dv * .03, a + dv * .04], .09, 10, tint(cc, .9), sc=.6)
        # pan tile between rolls
        if i < k:
            s2 = -1 + 2 * (i + .5) / k
            pts2 = [F.P(s2, j / 8) + F.N(s2, j / 8) * .012 for j in range(9)]
            tube(m, mat, pts2, .11, 4, tint(cc, .85), sc=.6)
    # flat eave lip tiles under the round ends
    pts = [F.P(-1 + 2 * i / 24, 0) - V((0, 0, .05)) for i in range(25)]
    for a, b in zip(pts, pts[1:]):
        fr = Frame(a, (b - a).normalized(), (0, 0, 1)); box(m, mat, fr, 0, (b - a).length, -.07, .07, -.09, .05, ch=.01, col=tint(col, .8), sc=.8)


def eave_under(m, F, tw, R, rafter_sp=.32, drop=.42, tiers=2, col=SHU, endcol=END):
    """Soffit boards and rafters from the eave edge (t=0) back to the wall line (t=tw)."""
    nv = 6; nu = 16
    P = [[F.P(-1 + 2 * i / nu, tw * j / nv) - V((0, 0, drop)) for j in range(nv + 1)] for i in range(nu + 1)]
    m.grid("soffit", [r[::-1] for r in P], None, [[(.62, .5, .38)] * (nv + 1)] * (nu + 1), smooth=True)
    W = 2 * F.w0; k = max(2, int(W / rafter_sp))
    for tier in range(tiers):
        t0 = 0 if tier == 0 else .0; t_end = tw if tier else tw * .45
        for i in range(k + 1):
            sv = -1 + 2 * i / k
            if tier == 0 and abs(sv) > .97: continue
            pts = [F.P(sv, t0 + (t_end - t0) * j / 4) - V((0, 0, drop + .02 + tier * .16)) for j in range(5)]
            if tier == 1: pts = [p - (F.P(sv, 0) - F.P(sv, .05)).normalized() * 0 for p in pts]
            for a, b in zip(pts, pts[1:]):
                dv = (b - a); L = dv.length
                if L < .01: continue
                fr = Frame(a, dv.normalized(), F.u.cross(dv.normalized()).normalized() if F.u.cross(dv.normalized()).z > 0 else -F.u.cross(dv.normalized()).normalized())
                box(m, "paint", fr, 0, L, -.05, .05, -.06, .06, col=tint(col, .9))
            a = pts[0]; dv = (pts[1] - pts[0]).normalized()
            fr = Frame(a - dv * .01, dv, (0, 0, 1)); box(m, "paint", fr, -.012, .004, -.055, .055, -.065, .065, col=endcol)


def ridge_main(m, a, b, R, h=.9, col=TILE, oni=True):
    a, b = V(a), V(b); L = (b - a).length; u = (b - a).normalized()
    fr = Frame(a, u, (0, 0, 1))
    n = int(L / .3)
    for k in range(int(h / .09)):
        z = k * .09; w = .3 - k * .012
        box(m, "kawara", fr, -.05 + (k % 2) * .04, L + .05 - (k % 2) * .04, z, z + .085, -w, w, ch=.008, col=tint(col, 1 + (R.random() - .5) * .12), sc=.8)
    tube(m, "kawara", [a + V((0, 0, h + .08)) - u * .1, b + V((0, 0, h + .08)) + u * .1], .13, 10, col, sc=.8)
    if oni:
        for p, sg in ((a, -1), (b, 1)):
            f2 = Frame(p + u * (sg * .25), u, (0, 0, 1))
            box(m, "kawara", f2, -.18, .18, -.1, h + .75, -.62, .62, ch=.06, col=tint(col, .9), sc=.8)
            box(m, "kawara", f2, -.2, .2, h + .55, h + .95, -.42, .42, ch=.08, col=tint(col, .9), sc=.8)
            tube(m, "kawara", [f2.p(0, h + .95, -.7), f2.p(0, h + 1.2, -.85)], .05, 6, col)
            tube(m, "kawara", [f2.p(0, h + .95, .7), f2.p(0, h + 1.2, .85)], .05, 6, col)


def hip_ridge(m, pts, R, col=TILE):
    for a, b in zip(pts, pts[1:]):
        ridge(m, V(a) + V((0, 0, .05)), V(b) + V((0, 0, .05)), R, mat="kawara", layers=3, cap=.1, col=col)


def column(m, x, y, z0, z1, r=.36, col=SHU):
    tube(m, "shu", [(x, y, z0 + .25), (x, y, z1)], r, 16, col, sc=1.)
    fr = Frame((x, y, z0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    box(m, "granite", fr, -r - .14, r + .14, -r - .14, r + .14, 0, .28, ch=.04, col=(.72, .71, .68), sc=1.5)      # foundation stone
    tube(m, "bronze", [(x, y, z0 + .25), (x, y, z0 + .42)], r + .02, 16, (.3, .22, .13))                           # metal foot band


def beam(m, a, b, h, w, z, col=SHU, mat="shu"):
    a, b = V((a[0], a[1], 0)), V((b[0], b[1], 0)); u = (b - a).normalized(); fr = Frame((a.x, a.y, z), u, (0, 0, 1))
    box(m, mat, fr, 0, (b - a).length, 0, h, -w / 2, w / 2, ch=.015, col=col, sc=1.5)


def bracket(m, p, n, u, tiers=2, sc=1.0, col=SHU, endcol=END):
    """Kumimono: dai-to, crossed arms, small to blocks; steps outward per tier."""
    p = V(p); n = V(n).normalized(); u = V(u).normalized()
    fr = Frame(p, u, n, (0, 0, 1))      # a: along wall, b: outward, c: up
    box(m, "shu", fr, -.3 * sc, .3 * sc, -.3 * sc, .3 * sc, 0, .3 * sc, ch=.02, col=tint(col, .9), sc=1.5)
    for k in range(tiers):
        z = .3 * sc + k * .34 * sc; o = k * .5 * sc
        box(m, "shu", fr, -.11 * sc, .11 * sc, o - .35 * sc, o + .62 * sc, z, z + .22 * sc, ch=.015, col=col, sc=1.5)           # projecting arm
        box(m, "shu", fr, -.75 * sc, .75 * sc, o - .1 * sc, o + .1 * sc, z, z + .22 * sc, ch=.015, col=col, sc=1.5)             # lateral arm
        for a_ in (-.62, 0, .62):
            box(m, "shu", fr, a_ * sc - .16 * sc, a_ * sc + .16 * sc, o - .16 * sc, o + .16 * sc, z + .22 * sc, z + .34 * sc, ch=.012, col=tint(col, .88), sc=1.5)
        box(m, "paint", fr, -.12 * sc, .12 * sc, o + .62 * sc, o + .63 * sc, z, z + .22 * sc, col=endcol)                       # painted arm end
    zt = .3 * sc + tiers * .34 * sc
    box(m, "shu", fr, -.9 * sc, .9 * sc, (tiers - 1) * .5 * sc - .12 * sc, (tiers - 1) * .5 * sc + .12 * sc, zt, zt + .24 * sc, ch=.015, col=col, sc=1.5)
    return zt + .24 * sc


def lathe(m, mat, c, prof, n=24, col=(1, 1, 1), uv=None, close=False):
    """prof: [(r, z)] bottom to top. uv: None -> (u around, v=z) scaled; 'unwrap' -> 0..1 both."""
    c = V(c); P = []; UV = []
    zs = [z for _, z in prof]; z0, z1 = min(zs), max(zs)
    for i in range(n + 1):
        th = 2 * pi * i / n; row = []; q = []
        for r, z in prof:
            row.append(c + V((r * sin(th), -r * cos(th), z)))     # u=0.5 faces +N (front of a gate facing north)
            q.append((i / n, (z - z0) / max(1e-6, z1 - z0)) if uv == "unwrap" else (i / n * 4, z))
        P.append(row); UV.append(q)
    m.grid(mat, P, UV, [[col] * len(prof)] * (n + 1), smooth=True)


def chochin(m, c, H, D, mat):
    """Giant paper lantern hanging with its top at c (centre top). Ribbed barrel, lacquered rims, bronze base with relief."""
    c = V(c); R = D / 2; prof = []
    for k in range(41):
        t = k / 40; z = -H + .32 + (H - .64) * t
        r = R * (.86 + .14 * sin(pi * t) ** .8) * (1 + .006 * abs(sin(t * pi * 46)))
        prof.append((r, z))
    lathe(m, mat, c, prof, 48, (1, 1, 1), uv="unwrap")
    for z, r in ((-.32, R * .86 + .03), (-H + .32, R * .86 + .03)):
        tube(m, "lacq", [c + V((0, 0, z - .16)), c + V((0, 0, z + .16))], r, 48, (.04, .035, .03))
    # bronze bottom ring with dragon relief disc and top cap with hanger
    lathe(m, "bronze", c, [(R * .86 + .06, -H + .16), (R * .86 + .08, -H + .02), (R * .7, -H - .05), (.01, -H - .07)], 48, (.36, .26, .15))
    P = []; UV = []
    for i in range(33):
        th = 2 * pi * i / 32; P.append([c + V((0, 0, -H - .069)), c + V((R * .7 * sin(th), R * .7 * cos(th), -H - .069))])
        UV.append([(.5, .5), (.5 + .5 * sin(th), .5 + .5 * cos(th))])
    m.grid("relief", [r[::-1] for r in P], [u[::-1] for u in UV], [[(1, 1, 1)] * 2] * 33, smooth=False)
    lathe(m, "bronze", c, [(R * .86 + .05, -.16), (R * .6, .08), (.25, .2), (.08, .45)], 32, (.36, .26, .15))
    tube(m, "bronze", [c + V((0, -.18, .55)), c + V((0, 0, .72)), c + V((0, .18, .55))], .04, 8, (.3, .22, .13))


def bronze_lantern(m, c, H=3.0, D=1.4):
    """Hexagonal bronze tsuri-doro (hanging lantern) as at Hozomon's side bays."""
    c = V(c); R = D / 2
    lathe(m, "bronze", c, [(.04, .3), (.12, .18), (R * 1.15, -.35), (R * 1.25, -.5), (R * .9, -.55)], 6, (.3, .24, .15))     # roof
    lathe(m, "bronze", c, [(R * .8, -.55), (R * .82, -1.9), (R * .7, -2.0)], 6, (.27, .22, .14))
    for k in range(6):
        a = k * pi / 3 + pi / 6; p = c + V((R * .81 * cos(a), R * .81 * sin(a), -1.25))
        fr = Frame(p, (-sin(a), cos(a), 0), (0, 0, 1), (cos(a), sin(a), 0))
        box(m, "dark", fr, -.18, .18, -.45, .45, -.01, .003, col=(.05, .04, .03))
    lathe(m, "bronze", c, [(R * .7, -2.0), (R * .9, -2.15), (R * .5, -2.45), (.15, -H + .2), (.02, -H)], 6, (.28, .22, .14))
    tube(m, "bronze", [c + V((0, 0, .3)), c + V((0, 0, .9))], .03, 6, (.25, .2, .12))


def railing(m, pts, z, h=.9, col=SHU, post_sp=1.4, giboshi=True):
    """Koran balustrade along a polyline at floor height z."""
    for a, b in zip(pts, pts[1:]):
        a, b = V((a[0], a[1], z)), V((b[0], b[1], z)); L = (b - a).length; u = (b - a).normalized(); fr = Frame(a, u, (0, 0, 1))
        for x in frange(0, L + .01, post_sp):
            box(m, "shu", fr, x - .07, x + .07, 0, h, -.07, .07, ch=.01, col=col, sc=1.5)
        box(m, "shu", fr, 0, L, .12, .2, -.05, .05, col=col, sc=1.5)
        box(m, "shu", fr, 0, L, h * .55, h * .55 + .07, -.04, .04, col=col, sc=1.5)
        tube(m, "shu", [fr.p(0, h - .02, 0), fr.p(L, h - .02, 0)], .055, 8, col)
    if giboshi:
        for p in pts:
            lathe(m, "bronze", (p[0], p[1], z + h), [(.09, 0), (.1, .1), (.07, .16), (.11, .26), (.08, .34), (.01, .44)], 12, (.33, .25, .14))


def renji(m, f, x, y, w, h, col=SHU):
    """Renji-mado: vertical lattice bars in a lacquered frame, dark behind."""
    P = [f.p(x, y, -.14), f.p(x + w, y, -.14), f.p(x + w, y + h, -.14), f.p(x, y + h, -.14)]
    m.poly("dark", P, None, (.03, .025, .02))
    for a0, a1, b0, b1 in ((x - .08, x + w + .08, y - .1, y), (x - .08, x + w + .08, y + h, y + h + .1), (x - .08, x, y, y + h), (x + w, x + w + .08, y, y + h)):
        box(m, "shu", f, a0, a1, b0, b1, -.02, .06, ch=.01, col=col, sc=1.5)
    for a in frange(x + .06, x + w - .03, .13):
        box(m, "shu", f, a, a + .055, y, y + h, -.1, -.03, ch=.008, col=tint(col, .92), sc=1.5)


def plank_door(m, f, x, y, w, h, col=SHU):
    """Lacquered double leaf door with gold studs."""
    for k, x0 in enumerate((x, x + w / 2)):
        box(m, "shu", f, x0 + .01, x0 + w / 2 - .01, y, y + h, -.12, -.04, ch=.01, col=tint(col, .95), sc=1.5)
        for yy in frange(y + .3, y + h - .2, (h - .4) / 5):
            for xx in frange(x0 + .2, x0 + w / 2 - .15, (w / 2 - .3) / 3):
                tube(m, "gold", [f.p(xx, yy, -.04), f.p(xx, yy, .0)], .035, 8, GOLD)


def grille(m, f, x, y, w, h):
    """Wire-mesh guard in front of a statue niche."""
    P = [f.p(x, y, -1.6), f.p(x + w, y, -1.6), f.p(x + w, y + h, -1.6), f.p(x, y + h, -1.6)]
    m.poly("dark", P, None, (.02, .018, .016))
    for a in frange(x + .05, x + w, .075): box(m, "steel", f, a, a + .012, y, y + h, -.03, -.018, col=(.16, .17, .17))
    for b in frange(y + .05, y + h, .075): box(m, "steel", f, x, x + w, b, b + .012, -.045, -.033, col=(.16, .17, .17))
    for a0, a1, b0, b1 in ((x, x + w, y - .06, y), (x, x + w, y + h, y + h + .06)):
        box(m, "shu", f, a0, a1, b0, b1, -.05, .02, col=SHU)


def statue(m, base, face, scale, body, R, attr=None):
    """Guardian silhouette behind a grille: plinth, cloud base, torso, raised arm, head with flame halo.
    attr: 'drums' = Raijin's ring of taiko drums, 'bag' = Fujin's wind bag over the shoulders."""
    b = V(base); n = V(face).normalized(); u = V((-n.y, n.x, 0)); S = scale
    if attr == "drums":
        c = b + V((0, 0, 2.55 * S)) - n * .35 * S
        for k in range(9):
            th = pi * (.1 + .8 * k / 8); p = c + u * (1.05 * S * cos(th)) + V((0, 0, 1.05 * S * sin(th) - .25 * S))
            tube(m, "paint", [p - n * .09 * S, p + n * .09 * S], .17 * S, 12, (.42, .16, .1))
            tube(m, "gold", [p + n * .09 * S, p + n * .1 * S], .17 * S, 12, (.75, .58, .3))
        tube(m, "gold", [c + u * (1.05 * S * cos(pi * (.1 + .8 * k / 16))) + V((0, 0, 1.05 * S * sin(pi * (.1 + .8 * k / 16)) - .25 * S)) for k in range(17)], .03 * S, 6, (.7, .55, .3))
    elif attr == "bag":
        c = b + V((0, 0, 2.6 * S)) - n * .3 * S
        tube(m, "paint", [c + u * (1.0 * S * cos(pi * k / 12)) + V((0, 0, .7 * S * sin(pi * k / 12))) for k in range(13)], .18 * S, 10, (.5, .52, .5))
    box(m, "granite", Frame(b, u, n, (0, 0, 1)), -.8 * S, .8 * S, -.6 * S, .6 * S, 0, .35 * S, ch=.05, col=(.4, .38, .35))
    for sg in (1, -1):              # wide fighting stance and a flowing tenne scarf arcing over the head
        tube(m, "paint", [b + V((0, 0, .75 * S)) + u * .55 * S * sg, b + V((0, 0, 1.25 * S)) + u * .38 * S * sg + n * .1 * S, b + V((0, 0, 1.6 * S)) + u * .2 * S * sg], .17 * S, 10, tint(body, .9))
    tube(m, "paint", [b + V((0, 0, 1.6 * S)) + u * (1.05 * S * cos(pi * k / 14)) - n * .45 * S + V((0, 0, (1.7 + .9 * sin(pi * k / 14)) * S)) for k in range(15)], .06 * S, 8, (.55, .5, .32))
    lathe(m, "paint", b + V((0, 0, .35 * S)), [(.7 * S, 0), (.75 * S, .2 * S), (.45 * S, .45 * S)], 12, tint(body, .7))
    lathe(m, "paint", b + V((0, 0, .8 * S)), [(.32 * S, 0), (.42 * S, .5 * S), (.46 * S, 1.1 * S), (.38 * S, 1.6 * S), (.18 * S, 1.75 * S)], 14, body)
    lathe(m, "paint", b + V((0, 0, 2.55 * S)) + n * .05, [(.05, 0), (.22 * S, .1 * S), (.24 * S, .35 * S), (.15 * S, .52 * S), (.02, .56 * S)], 12, tint(body, .9))
    tube(m, "paint", [b + V((0, 0, 2.2 * S)) + u * .4 * S, b + V((0, 0, 2.5 * S)) + u * .9 * S + n * .2 * S, b + V((0, 0, 3.0 * S)) + u * .8 * S + n * .3 * S], .12 * S, 8, body)
    tube(m, "paint", [b + V((0, 0, 2.2 * S)) - u * .4 * S, b + V((0, 0, 1.8 * S)) - u * .8 * S + n * .3 * S, b + V((0, 0, 1.55 * S)) - u * .6 * S + n * .45 * S], .12 * S, 8, body)
    tube(m, "gold", [b + V((0, 0, 2.6 * S)) - n * .25 * S, b + V((0, 0, 2.6 * S)) - n * .3 * S], .55 * S, 16, (.55, .35, .12))


def sorin(m, c, H=14.0):
    """Finial: roban, fukubachi, ukebana, nine rings, suien, ryusha, hoju. Gilt."""
    c = V(c); g = GOLD
    box(m, "gold", Frame(c, (1, 0, 0), (0, 1, 0), (0, 0, 1)), -.8, .8, -.8, .8, 0, .55, ch=.05, col=tint(g, .8))
    lathe(m, "gold", c + V((0, 0, .55)), [(.75, 0), (.72, .35), (.5, .65), (.2, .75)], 20, g)
    lathe(m, "gold", c + V((0, 0, 1.3)), [(.2, 0), (.6, .25), (.75, .4), (.3, .45)], 16, g)
    tube(m, "gold", [c + V((0, 0, 1.6)), c + V((0, 0, H - .9))], .12, 12, g)
    for k in range(9):
        z = 2.2 + k * .62
        lathe(m, "gold", c + V((0, 0, z)), [(.18, 0), (.62 - k * .012, .03), (.64 - k * .012, .14), (.18, .18)], 24, tint(g, 1 + (k % 2) * .05))
    zs = 2.2 + 9 * .62 + .3
    for a in (0, pi / 2, pi / 4, 3 * pi / 4):
        fr = Frame(c + V((0, 0, zs)), (cos(a), sin(a), 0), (0, 0, 1))
        P = [fr.p(-.7, 0), fr.p(.7, 0), fr.p(.9, .7), fr.p(.55, 1.4), fr.p(.2, 1.9), fr.p(-.2, 1.9), fr.p(-.55, 1.4), fr.p(-.9, .7)]
        m.poly("gold", P, None, tint(g, .95)); m.poly("gold", P[::-1], None, tint(g, .95))
    lathe(m, "gold", c + V((0, 0, zs + 2.0)), [(.05, 0), (.38, .1), (.4, .2), (.05, .3)], 16, g)
    lathe(m, "gold", c + V((0, 0, zs + 2.35)), [(.02, 0), (.25, .1), (.32, .3), (.22, .52), (.02, .7)], 16, g)


def plaster_wall(m, f, x0, x1, y0, y1, tc=(.96, .95, .92), holes=()):
    wall(m, "tplaster", Frame(f.p(x0, y0, 0), f.u, f.v, f.n), x1 - x0, y1 - y0, [(h[0] - x0, h[1] - y0, h[2] - x0, h[3] - y0) for h in holes],
         tc=tc, sc=2.2, base_z=f.p(0, y0, 0).z, bump=.002, amt=.5)
