# Block S: Senso-ji landmarks spliced into Yanaka as a fictional composite (user request 2026-11-02): Kaminarimon, Hozomon, five-storey pagoda.
# Sited on the temple-cemetery land south of block D's parking (outside the 80x80 m square, no modelled real lot touched). Separate GLB, removable.
import sys
sys.path.insert(0, r"D:\project\cijian\work\src")
import blk_fill
from blk_fill import *
from blk_temple import *

a = args("km_front,km_lantern,sando,pagoda_low,hz_detail,eaves_close,aerial,from_yanaka")
K = Block("S", 20261105)
for k, kw in {"shu": dict(texid="shu_n", nor_k=.3), "tplaster": dict(texid="white_plaster_02", nor_k=.6), "granite": dict(texid="granite_wall", nor_k=1.0),
              "lacq": dict(solid=(1, 1, 1), rough=.22, spec=.6), "gold": dict(solid=(1, 1, 1), metal=1.0, rough=.3), "bronze": dict(texid="green_metal_rust", nor_k=.6)}.items():
    K.mats[k] = pbr(k, **kw)
K.mats["bronze"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = .55
K.mats["pave"] = pbr("stonepave", texid="granite_tile_02", nor_k=.9)
K.mats["kawara"] = pbr("kawara_temple", solid=(1, 1, 1), rough=.64, spec=.28)      # matte fired tiles, no sky mirror
K.mats["chochin_km"] = tex_mat("chochin_km", GEN + r"\chochin_kaminarimon.jpg", .55); K.mats["chochin_kb"] = tex_mat("chochin_kb", GEN + r"\chochin_kobunacho.jpg", .55)
for k in ("chochin_km", "chochin_kb"):
    nt = K.mats[k].node_tree; bs = nt.nodes["Principled BSDF"]; img = [n for n in nt.nodes if n.bl_idname == "ShaderNodeTexImage"][0]
    nt.links.new(img.outputs["Color"], bs.inputs["Emission Color"]); bs.inputs["Emission Strength"].default_value = .35       # paper glows faintly from the lamp inside
K.mats["relief"] = tex_mat("relief", GEN + r"\bronze_relief.jpg", .45); K.mats["relief"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = .8

AX = -42.0                                  # approach axis (E)
ZP = G(AX, -40.6)                           # one level precinct, meets the parking kerb
blk_fill.G = lambda E, N, _g=blk_fill.G: ZP if (-53.6 <= E <= -16.9 and -82.1 <= N <= -40.25) else _g(E, N)
R = K.R
m_km = M("S_kaminarimon"); m_hz = M("S_hozomon"); m_pg = M("S_pagoda"); m_site = M("S_site")


def frame_xy(E0, N0, z): return Frame((E0, N0, z), (1, 0, 0), (0, 1, 0), (0, 0, 1))
def wallf(E0, N0, z, axis, out):        # vertical wall frame: axis along wall ('x' or 'y'), outward sign
    if axis == "x": return Frame((E0, N0, z), (1, 0, 0) if out > 0 else (-1, 0, 0), (0, 0, 1), (0, out, 0))
    return Frame((E0, N0, z), (0, -1, 0) if out > 0 else (0, 1, 0), (0, 0, 1), (out, 0, 0))


def gate_base(m, E0, N0, hw, hd, h=.35):
    f = frame_xy(E0, N0, ZP); box(m, "granite", f, -hw, hw, -hd, hd, 0, h, ch=.05, col=(.7, .69, .66), sc=1.5)


def perimeter_beams(m, E0, N0, xs, ys, z, h=.5, w=.32):
    for y in ys: beam(m, (E0 + xs[0], N0 + y), (E0 + xs[-1], N0 + y), h, w, z)
    for x in xs: beam(m, (E0 + x, N0 + ys[0]), (E0 + x, N0 + ys[-1]), h, w, z)


def gable_infill(m, F_front, F_back, xw, Le, tw, zc, sg):
    """Vertical plaster gable under a kirizuma roof at plan x=xw (local), with a lacquered frame."""
    sv = sg * xw / Le
    pts = [F_front.P(sv, tw + (1 - tw) * k / 8) - V((0, 0, .44)) for k in range(9)] + [F_back.P(-sv, tw + (1 - tw) * k / 8) - V((0, 0, .44)) for k in range(8, -1, -1)]
    base = [V((pts[-1].x, pts[-1].y, zc)), V((pts[0].x, pts[0].y, zc))]
    poly = base[::-1] + pts if sg > 0 else pts[::-1] + base
    m.poly("tplaster", poly, [(p.y / 2.2, p.z / 2.2) for p in poly], (.95, .94, .9))
    for p, q in zip(pts, pts[1:]): beam(m, (p.x, p.y), (q.x, q.y), .18, .26, (p.z + q.z) / 2 - .1)


def barge(m, F, sg):
    pts = [F.P(sg, k / 10) for k in range(11)]
    for p, q in zip(pts, pts[1:]):
        dv = (q - p); fr = Frame(p, dv.normalized(), (0, 0, 1))
        box(m, "shu", fr, 0, dv.length, -.42, .05, -.09, .09, col=SHU_D)
    tube(m, "gold", [pts[0] + V((0, 0, -.2)), pts[0] + V((0, 0, -.05))], .09, 10, GOLD)


# ======================= Kaminarimon (kirizuma hakkyakumon) =======================
KE, KN = AX, -44.2
zf = ZP + .35; xs = [-5.6, -2.2, 2.2, 5.6]; ys = [-2.4, 0, 2.4]; zc = zf + 6.4
gate_base(m_site, KE, KN, 6.4, 3.2)
for x in xs:
    for y in ys: column(m_km, KE + x, KN + y, zf - .02, zc, r=.36)
perimeter_beams(m_km, KE, KN, xs, ys, zc - .55)
beam(m_km, (KE + xs[0], KN), (KE + xs[-1], KN), .6, .34, zc - .15)          # tie beam carrying the lantern
ztop = zc
for x in xs:
    for y, sg in ((ys[0], -1), (ys[-1], 1)): ztop = bracket(m_km, (KE + x, KN + y, zc), (0, sg, 0), (1, 0, 0), tiers=2, sc=.85) + zc
for y in ys:
    for x, sg in ((xs[0], -1), (xs[-1], 1)): bracket(m_km, (KE + x, KN + y, zc), (sg, 0, 0), (0, 1, 0), tiers=1, sc=.85)
ze = ztop + .12; zr = ze + 4.3; Te = 5.1; Le = 7.3
Ff = RoofFace((KE, KN), (0, 1, 0), (1, 0, 0), Te, 0, Le, Le, ze, zr, conc=1.5, lift=.32)
Fb = RoofFace((KE, KN), (0, -1, 0), (-1, 0, 0), Te, 0, Le, Le, ze, zr, conc=1.5, lift=.32)
tw = (Te - 2.55) / Te
for F in (Ff, Fb):
    roof_face(m_km, F, R); eave_under(m_km, F, tw, R); barge(m_km, F, 1); barge(m_km, F, -1)
ridge_main(m_km, (KE - Le - .1, KN, zr + .06), (KE + Le + .1, KN, zr + .06), R, h=.85)
for sg in (1, -1): gable_infill(m_km, Ff, Fb, 5.75, Le, tw, zc - .05, sg)
# side bays: niches with grilles front (Fujin west, Raijin east) and back (Tenryu, Kinryu), plaster walls
for sx in (-1, 1):
    x0, x1 = (2.2, 5.6) if sx > 0 else (-5.6, -2.2)
    for sy in (1, -1):
        f = wallf(KE + x0 if sy > 0 else KE + x1, KN + sy * 2.4, zf, "x", sy)
        w = x1 - x0
        plaster_wall(m_km, f, 0, w, 0, 6.35 - 5.75, holes=()) if False else None
        plaster_wall(m_km, Frame(f.p(0, 5.0, 0), f.u, f.v, f.n), 0, w, 0, 1.38)
        plaster_wall(m_km, f, 0, w, 0, .55)
        grille(m_km, f, .25, .55, w - .5, 4.45)
        body = {(-1, 1): (.28, .46, .36), (1, 1): (.62, .2, .14), (-1, -1): (.52, .44, .26), (1, -1): (.5, .42, .24)}[(sx, sy)]
        statue(m_km, (KE + (x0 + x1) / 2, KN + sy * 1.05, zf), (0, sy, 0), .82, body, R, attr={(-1, 1): "bag", (1, 1): "drums"}.get((sx, sy)))
    fo = wallf(KE + sx * 5.6, KN + 2.4 if sx > 0 else KN - 2.4, zf, "y", sx)
    plaster_wall(m_km, fo, 0, 4.8, 0, 6.35)
    fi = wallf(KE + sx * 2.2, KN - 2.4 if sx > 0 else KN + 2.4, zf, "y", -sx)
    plaster_wall(m_km, fi, 0, 4.8, 0, 6.35)
    beam(m_km, (KE + sx * 2.2, KN), (KE + sx * 5.6, KN), 6.35, .3, zf, col=(.95, .94, .9), mat="tplaster")
P_ = [(KE - 2.2, KN - 2.4, zc - .05), (KE + 2.2, KN - 2.4, zc - .05), (KE + 2.2, KN + 2.4, zc - .05), (KE - 2.2, KN + 2.4, zc - .05)]
m_km.poly("soffit", P_[::-1], [(p[0] / 1.5, p[1] / 1.5) for p in P_[::-1]], (.55, .42, .3))
for x in frange(-2.1, 2.2, .45): beam(m_km, (KE + x, KN - 2.4), (KE + x, KN + 2.4), .12, .1, zc - .17, col=SHU_D)
chochin(m_km, (KE, KN, zc - .2), 3.9, 3.3, "chochin_km")

# ======================= Hozomon (irimoya nijumon) =======================
HE, HN = AX, -73.5
zf = ZP + .45; xs = [-10.25, -6.15, -2.05, 2.05, 6.15, 10.25]; ys = [-4.2, 0, 4.2]; zc1 = zf + 6.3
gate_base(m_site, HE, HN, 11.4, 5.4, h=.45)
for x in xs:
    for y in ys: column(m_hz, HE + x, HN + y, zf - .02, zc1, r=.42)
perimeter_beams(m_hz, HE, HN, xs, ys, zc1 - .6, h=.55, w=.36)
for x in xs:
    for y, sg in ((ys[0], -1), (ys[-1], 1)): zt1 = bracket(m_hz, (HE + x, HN + y, zc1), (0, sg, 0), (1, 0, 0), tiers=2, sc=.95) + zc1
for y in ys:
    for x, sg in ((xs[0], -1), (xs[-1], 1)): bracket(m_hz, (HE + x, HN + y, zc1), (sg, 0, 0), (0, 1, 0), tiers=2, sc=.95)
ze1 = zt1 + .1; Le1, Te1, Lt1, Tt1 = 12.85, 6.8, 9.95, 3.9; zs1 = ze1 + 1.55
skirt = [RoofFace((HE, HN), (0, sg, 0), (sg, 0, 0), Te1, Tt1, Le1, Lt1, ze1, zs1, conc=1.3, lift=.5) for sg in (1, -1)] + \
        [RoofFace((HE, HN), (sg, 0, 0), (0, -sg, 0), Le1, Lt1, Te1, Tt1, ze1, zs1, conc=1.3, lift=.5) for sg in (1, -1)]
for k, F in enumerate(skirt):
    roof_face(m_hz, F, R); eave_under(m_hz, F, min(1, ((F.d0 - (4.3 if k < 2 else 10.35)) / (F.d0 - F.d1))), R)
for sx in (1, -1):
    for sy in (1, -1):
        hip_ridge(m_hz, [skirt[0 if sy > 0 else 1].P(sx * sy, t / 6) for t in range(7)], R)
# upper storey
zu = zs1 + .05; xu = [-9.6, -5.76, -1.92, 1.92, 5.76, 9.6]; yu = [-3.6, 3.6]; zc2 = zu + 4.6
fdeck = frame_xy(HE, HN, zu); box(m_hz, "soffit", fdeck, -10.6, 10.6, -4.6, 4.6, -.2, 0, ch=.02, col=(.5, .4, .3), sc=1.9)
railing(m_hz, [(HE - 10.5, HN - 4.5), (HE + 10.5, HN - 4.5), (HE + 10.5, HN + 4.5), (HE - 10.5, HN + 4.5), (HE - 10.5, HN - 4.5)], zu)
for x in xu:
    for y in yu: tube(m_hz, "shu", [(HE + x, HN + y, zu), (HE + x, HN + y, zc2)], .34, 16, SHU)
for y in (-3.6, 0, 3.6):
    if y: pass
perimeter_beams(m_hz, HE, HN, xu, yu, zc2 - .5, h=.5, w=.32)
for sy in (1, -1):
    f = wallf(HE - 9.6 if sy > 0 else HE + 9.6, HN + sy * 3.6, zu, "x", sy)
    holes = []
    for k in range(5):
        a0 = k * 3.84 + .25; a1 = (k + 1) * 3.84 - .25
        if k in (1, 2, 3): holes.append((a0 + .3, .15, a1 - .3, 3.4)); plank_door(m_hz, f, a0 + .3, .15, a1 - a0 - .6, 3.25)
        else: holes.append((a0 + .4, 1.0, a1 - .4, 3.0)); renji(m_hz, f, a0 + .4, 1.0, a1 - a0 - .8, 2.0)
    plaster_wall(m_hz, f, 0, 19.2, 0, 4.1, holes=holes)
for sx in (1, -1):
    f = wallf(HE + sx * 9.6, HN + 3.6 if sx > 0 else HN - 3.6, zu, "y", sx)
    renji(m_hz, f, 2.3, 1.0, 2.6, 2.0); plaster_wall(m_hz, f, 0, 7.2, 0, 4.1, holes=[(2.3, 1.0, 4.9, 3.0)])
for x in xu:
    for y, sg in ((yu[0], -1), (yu[1], 1)): zt2 = bracket(m_hz, (HE + x, HN + y, zc2), (0, sg, 0), (1, 0, 0), tiers=3, sc=.95) + zc2
for y in yu:
    for x, sg in ((xu[0], -1), (xu[-1], 1)): bracket(m_hz, (HE + x, HN + y, zc2), (sg, 0, 0), (0, 1, 0), tiers=3, sc=.95)
ze2 = zt2 + .1; Le2, Te2 = 12.7, 6.7; tm = .55; Lg = 7.2; Tm = Te2 * (1 - tm); zm2 = ze2 + 2.4; zr2 = zm2 + 2.5
low = [RoofFace((HE, HN), (0, sg, 0), (sg, 0, 0), Te2, Tm, Le2, Lg, ze2, zm2, conc=1.3, lift=.6) for sg in (1, -1)] + \
      [RoofFace((HE, HN), (sg, 0, 0), (0, -sg, 0), Le2, Lg, Te2, Tm, ze2, zm2, conc=1.3, lift=.6) for sg in (1, -1)]
for k, F in enumerate(low):
    roof_face(m_hz, F, R); eave_under(m_hz, F, min(1, (F.d0 - (3.7 if k < 2 else 9.7)) / (F.d0 - F.d1)), R, tiers=2)
for sx in (1, -1):
    for sy in (1, -1): hip_ridge(m_hz, [low[0 if sy > 0 else 1].P(sx * sy, t / 6) for t in range(7)], R)
up = [RoofFace((HE, HN), (0, sg, 0), (sg, 0, 0), Tm, 0, Lg, Lg, zm2, zr2, conc=1.4, lift=.0) for sg in (1, -1)]
for F in up: roof_face(m_hz, F, R); barge(m_hz, F, 1); barge(m_hz, F, -1)
ridge_main(m_hz, (HE - Lg - .1, HN, zr2 + .06), (HE + Lg + .1, HN, zr2 + .06), R, h=1.0)
for sg in (1, -1):         # irimoya gable screens
    xg = sg * (Lg - .25)
    pts = [up[0].P(sg * (Lg - .25) / Lg, k / 8) - V((0, 0, .3)) for k in range(9)] + [up[1].P(-sg * (Lg - .25) / Lg, k / 8) - V((0, 0, .3)) for k in range(8, -1, -1)]
    m_hz.poly("tplaster", pts if sg < 0 else pts[::-1], None, (.95, .94, .9))
    for p, q in zip(pts, pts[1:]): beam(m_hz, (p.x, p.y), (q.x, q.y), .2, .3, (p.z + q.z) / 2 - .12)
    fr = Frame((HE + xg, HN, zr2 - .9), (0, 1, 0), (0, 0, 1)); box(m_hz, "gold", fr, -.35, .35, -.5, .2, -.06, .14 * sg, ch=.03, col=GOLD)   # gegyo ornament
# lower storey: Nio niches in the end bays (front), plaster backs, lanterns in the passages
for sx in (1, -1):
    x0, x1 = (6.15, 10.25) if sx > 0 else (-10.25, -6.15)
    f = wallf(HE + x0, HN + 4.2, zf, "x", 1)
    plaster_wall(m_hz, Frame(f.p(0, 5.1, 0), f.u, f.v, f.n), 0, 4.1, 0, 1.15); plaster_wall(m_hz, f, 0, 4.1, 0, .55)
    grille(m_hz, f, .25, .55, 3.6, 4.55)
    statue(m_hz, (HE + (x0 + x1) / 2, HN + 1.4, zf), (0, 1, 0), 1.38, (.5, .2, .14) if sx < 0 else (.42, .2, .16), R)
    fb = wallf(HE + x1, HN - 4.2, zf, "x", -1); plaster_wall(m_hz, fb, 0, 4.1, 0, 6.25)
    # giant straw sandals (waraji) hung on the back wall
    for k in (-.8, .8):
        c = fb.p(2.05 + k, 3.3, .08)
        lathe(m_hz, "plank", c, [(.01, -2.2), (.55, -2.0), (.62, -1.0), (.58, 1.0), (.45, 1.9), (.01, 2.05)], 16, (.78, .66, .42))
    fo = wallf(HE + sx * 10.25, HN + 4.2 if sx > 0 else HN - 4.2, zf, "y", sx); plaster_wall(m_hz, fo, 0, 8.4, 0, 6.25)
    beam(m_hz, (HE + sx * 6.15, HN), (HE + sx * 10.25, HN), 6.25, .3, zf, col=(.95, .94, .9), mat="tplaster")
    fi = wallf(HE + sx * 6.15, HN - 4.2 if sx > 0 else HN + 4.2, zf, "y", -sx); plaster_wall(m_hz, fi, 0, 8.4, 0, 6.25)
    bronze_lantern(m_hz, (HE + sx * 4.1, HN, zc1 - .3), 3.0, 1.45)
P_ = [(HE - 6.15, HN - 4.2, zc1 - .1), (HE + 6.15, HN - 4.2, zc1 - .1), (HE + 6.15, HN + 4.2, zc1 - .1), (HE - 6.15, HN + 4.2, zc1 - .1)]
m_hz.poly("soffit", P_[::-1], [(p[0] / 1.5, p[1] / 1.5) for p in P_[::-1]], (.55, .42, .3))
chochin(m_hz, (HE, HN, zc1 - .25), 3.75, 3.3, "chochin_kb")

# ======================= Five-storey pagoda =======================
PE, PN = -26.0, -54.0
f = frame_xy(PE, PN, ZP); hb = 3.0
box(m_pg, "granite", f, -6.4, 6.4, -6.4, 6.4, 0, hb, ch=.05, col=(.72, .7, .67), sc=2.0)
box(m_pg, "granite", f, -6.6, 6.6, -6.6, 6.6, hb - .25, hb, ch=.04, col=(.62, .61, .58), sc=2.0)
for k in range(18):         # west stair up the base
    zz = (k + 1) * hb / 18; x0 = -6.4 - (18 - k) * .32
    box(m_pg, "granite", f, x0, -6.4, -1.6, 1.6, 0, zz, ch=.012, col=tint((.72, .71, .68), 1 + (R.random() - .5) * .06), sc=1.6)
for y in (-1.7, 1.7): railing(m_pg, [(PE - 6.4 - 18 * .32, PN + y), (PE - 6.4, PN + y)], ZP + .5, h=.8, col=(.32, .25, .15), post_sp=1.5)
box(m_pg, "tplaster", f, -4.6, 4.6, -4.6, 4.6, hb, hb + .45, ch=.18, col=(.94, .93, .9), sc=2.2)       # kamebara plinth
widths = [4.0, 3.75, 3.5, 3.25, 3.0]; zb = ZP + hb + .45
for i, A in enumerate(widths):
    hwall = 4.0 if i == 0 else 3.1
    cols = [-A, -A / 3, A / 3, A]
    for x in cols:
        for y in cols:
            if abs(x) == A or abs(y) == A: tube(m_pg, "shu", [(PE + x, PN + y, zb), (PE + x, PN + y, zb + hwall)], .26, 12, SHU)
    perimeter_beams(m_pg, PE, PN, cols, cols, zb + hwall - .45, h=.45, w=.3)
    for sx, sy, ax_ in ((0, 1, "x"), (0, -1, "x"), (1, 0, "y"), (-1, 0, "y")):
        if ax_ == "x": fw = wallf(PE - A if sy > 0 else PE + A, PN + sy * A, zb, "x", sy)
        else: fw = wallf(PE + sx * A, PN + A if sx > 0 else PN - A, zb, "y", sx)
        bw = 2 * A / 3; holes = []
        dh = min(2.9, hwall - .7)
        holes.append((bw + .3, .1, 2 * bw - .3, .1 + dh)); plank_door(m_pg, fw, bw + .3, .1, bw - .6, dh)
        for kk in (0, 2):
            holes.append((kk * bw + .35, 1.0, (kk + 1) * bw - .35, min(hwall - .55, 2.6))); renji(m_pg, fw, kk * bw + .35, 1.0, bw - .7, min(hwall - .55, 2.6) - 1.0)
        plaster_wall(m_pg, fw, 0, 2 * A, 0, hwall - .45, holes=holes)
    zt = zb + hwall
    for x in cols:
        for y in cols:
            if abs(x) == A or abs(y) == A:
                if abs(y) == A: zt_ = bracket(m_pg, (PE + x, PN + y, zb + hwall), (0, 1 if y > 0 else -1, 0), (1, 0, 0), tiers=3, sc=.82) + zb + hwall
                if abs(x) == A: zt_ = bracket(m_pg, (PE + x, PN + y, zb + hwall), (1 if x > 0 else -1, 0, 0), (0, 1, 0), tiers=3, sc=.82) + zb + hwall
    ze = zt_ + .08; E_ = A + 2.9
    top = i == len(widths) - 1
    At = 0 if top else widths[i + 1] + .3
    rise = (E_ * .62) if top else 1.45
    faces = [RoofFace((PE, PN), (0, sg, 0), (sg, 0, 0), E_, At, E_, At, ze, ze + rise, conc=1.25 if not top else 1.15, lift=.7) for sg in (1, -1)] + \
            [RoofFace((PE, PN), (sg, 0, 0), (0, -sg, 0), E_, At, E_, At, ze, ze + rise, conc=1.25 if not top else 1.15, lift=.7) for sg in (1, -1)]
    for F in faces:
        roof_face(m_pg, F, R, col=(.2, .21, .22), pitch=.3)
        eave_under(m_pg, F, min(1, (E_ - (A + .1)) / (E_ - At)), R, tiers=2)
    for sx in (1, -1):
        for sy in (1, -1):
            hip_ridge(m_pg, [faces[0 if sy > 0 else 1].P(sx * sy, t / 6) for t in range(7)], R, col=(.2, .21, .22))
            c = faces[0 if sy > 0 else 1].P(sx * sy, 0) - V((0, 0, .5))          # wind bell (futaku) at each eave corner
            tube(m_pg, "bronze", [c + V((0, 0, .45)), c + V((0, 0, .05))], .012, 4, (.3, .24, .15))
            lathe(m_pg, "bronze", c, [(.02, 0), (.16, -.05), (.2, -.45), (.24, -.5), (.02, -.52)], 10, (.32, .26, .16))
    if top:
        sorin(m_pg, (PE, PN, ze + rise - .25), 14.0)
    else:
        zb = ze + rise + .02
        An = widths[i + 1]
        box(m_pg, "soffit", frame_xy(PE, PN, zb), -An - .9, An + .9, -An - .9, An + .9, -.18, 0, ch=.02, col=(.5, .4, .3), sc=1.9)
        railing(m_pg, [(PE - An - .85, PN - An - .85), (PE + An + .85, PN - An - .85), (PE + An + .85, PN + An + .85), (PE - An - .85, PN + An + .85), (PE - An - .85, PN - An - .85)], zb, h=.75, post_sp=1.2)

# ======================= precinct =======================
def tamagaki(m, pts, h=1.0):
    """Stone fence: square posts and two rails."""
    for a_, b_ in zip(pts, pts[1:]):
        p, q = V((*a_, ZP)), V((*b_, ZP)); L = (q - p).length; u = (q - p).normalized(); fr = Frame(p, u, (0, 0, 1))
        for x in frange(0, L + .01, 1.25):
            box(m, "granite", fr, x - .1, x + .1, 0, h, -.1, .1, ch=.02, col=tint((.7, .69, .66), 1 + (R.random() - .5) * .08), sc=1.2)
            lathe(m, "granite", fr.p(x, h, 0), [(.12, 0), (.1, .08), (.02, .14)], 4, (.68, .67, .64))
        for z in (.3, h - .18): box(m, "granite", fr, 0, L, z, z + .1, -.06, .06, ch=.015, col=(.66, .65, .62), sc=1.6)


def toro(m, x, y, s=1.35):
    z = ZP; g = (.62, .61, .58)
    for r, z0, z1, c in ((.3, 0, .16, g), (.1, .16, .95, g), (.23, .95, 1.07, g), (.17, 1.07, 1.33, g), (.38, 1.33, 1.39, tint(g, .9)), (.3, 1.39, 1.46, tint(g, .9)),
                         (.2, 1.46, 1.52, tint(g, .9)), (.07, 1.52, 1.64, g), (.045, 1.64, 1.72, g)):
        tube(m, "granite", [(x, y, z + z0 * s), (x, y, z + z1 * s)], r * s, 6, c, sc=.8)
        m.poly("granite", [(x + r * s * cos(k * pi / 3), y + r * s * sin(k * pi / 3), z + z1 * s) for k in range(6)], None, c)
    for k in range(3):
        a_ = k * 2 * pi / 3; lf = Frame((x + .172 * s * cos(a_), y + .172 * s * sin(a_), z + 1.12 * s), (-sin(a_), cos(a_), 0), (0, 0, 1), (cos(a_), sin(a_), 0))
        box(m, "dark", lf, -.06 * s, .06 * s, 0, .16 * s, -.01, .002, col=(.04, .04, .04))


def jokoro(m, x, y):
    """Bronze incense burner on three legs under a small roof."""
    c = V((x, y, ZP))
    box(m, "granite", Frame(c, (1, 0, 0), (0, 1, 0), (0, 0, 1)), -1.2, 1.2, -1.2, 1.2, 0, .45, ch=.05, col=(.66, .65, .62), sc=1.5)
    for k in range(3):
        a_ = k * 2 * pi / 3; tube(m, "bronze", [c + V((.65 * cos(a_), .65 * sin(a_), .45)), c + V((.55 * cos(a_), .55 * sin(a_), 1.0))], .09, 8, (.25, .2, .12))
    lathe(m, "bronze", c + V((0, 0, .95)), [(.55, 0), (.95, .25), (1.05, .6), (.95, .75), (.6, .8)], 24, (.28, .22, .13))
    for k in range(4):
        a_ = k * pi / 2 + pi / 4; tube(m, "bronze", [c + V((.7 * cos(a_), .7 * sin(a_), 1.7)), c + V((.7 * cos(a_), .7 * sin(a_), 2.6))], .06, 8, (.25, .2, .12))
    lathe(m, "bronze", c + V((0, 0, 2.55)), [(1.15, 0), (1.1, .12), (.6, .55), (.15, .8), (.05, 1.0)], 4, (.26, .21, .13))
    lathe(m, "bronze", c + V((0, 0, 3.55)), [(.02, 0), (.18, .1), (.2, .25), (.02, .42)], 12, (.3, .24, .14))


tamagaki(m_site, [(-53.4, -40.6), (-53.4, -82.0), (-17.0, -82.0), (-17.0, -40.6)])
tamagaki(m_site, [(-53.4, -40.6), (-48.5, -40.6)]); tamagaki(m_site, [(-35.5, -40.6), (-17.0, -40.6)])
for y in (-50, -56, -62):
    for x in (AX - 4.2, AX + 4.2): toro(m_site, x, y)
jokoro(m_site, AX, -63.8)
import blk_equip                     # precinct greenery: CC0 shrub instanced as clipped garden trees
for x, y, s_ in ((-50.5, -44.0, 2.6), (-50.8, -52.0, 2.2), (-50.5, -79.0, 2.8), (-19.5, -44.5, 2.4), (-19.0, -68.0, 2.9), (-19.5, -79.0, 2.5), (-34.5, -79.5, 2.2), (-49.0, -64.0, 2.0)):
    blk_equip.PROPS.append(("shrub_01", (x, y, ZP), R.random() * 6.28, s_))
K.default_cls = 4
K.pave = []
gm = K.ground(-53.4, -16.9, -82.0, -40.3)
for k in range(46):        # sando: long granite slabs down the axis, laid a few cm proud
    y0 = -47.6 - k * .56
    if -69.2 < y0 < -58.6 and False: continue
    fr = frame_xy(AX, y0, ZP); w = 3.2 + (R.random() - .5) * .02
    box(m_site, "granite", fr, -w / 2, w / 2, -.53, 0, -.03, .025, ch=.012, col=tint((.74, .73, .7), 1 + (R.random() - .5) * .1), sc=2.0, off=(R.random(), R.random()))
K.scatter_stains(40, -53, -17.5, -81.5, -41)
K.objs = []
K.flush_all(extra=(m_km, m_hz, m_pg, m_site, gm))
CAMS = {"km_front": ((-40.5, -27.5, 1.65), (-41.0, -46, 8.5), 24), "km_lantern": ((-40.6, -41.6, 1.65), (-42.0, -44.2, 3.6), 20),
        "sando": ((-42.6, -48.4, 1.65), (-42.0, -73, 9.0), 24), "pagoda_low": ((-36.5, -46.0, 1.65), (-26.0, -54, 26), 18),
        "hz_detail": ((-36.0, -65.8, 1.65), (-40.5, -70.5, 6.5), 22), "eaves_close": ((-50.5, -67.0, 1.65), (-51.0, -69.8, 9.0), 20),
        "aerial": ((2, -18, 52), (-38, -62, 10), 30), "from_yanaka": ((-57.8, -1.5, 1.65), (-36, -60, 22), 26), "_own": (-53.5, -16.9, -82.1, -40.25)}
K.finish(a, CAMS, dict(note="Fictional composite: Senso-ji landmarks placed on Yanaka temple-cemetery land. Not real geography.", precinct_z=ZP))
