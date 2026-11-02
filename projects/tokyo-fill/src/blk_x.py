# Block X: context ring. Every PLATEAU building within ~250 m that no detailed block covers, as a textured mass with a simple roof,
# plus the real Yanaka cemetery south of the Senso-ji splice as rows of gravestones. Replaces qs_h1's far skyline cards.
import sys
sys.path.insert(0, r"D:\project\cijian\work\src")
from blk_fill import *

a = args("ring")
K = Block("X", 20261106); K.equip = 0
for k in ("plaster", "tile", "siding", "concrete"):
    K.mats["ctx_" + k] = tex_mat("ctx_" + k, GEN + rf"\ctx_{k}.jpg", .75)
K.mats["granite"] = pbr("granite", texid="granite_wall", nor_k=1.0)
R = K.R
OWN = [(-124.5, -16.5, -82.5, 49.6), (-125, -50, 12.5, 50), (-125, -53, -56, -15)]     # A..E and the splice precinct, padded
def covered(cx, cy):
    return foreign(cx, cy) or any(in_rect(cx, cy, r) for r in OWN) or (-53.6 <= cx <= -16.5 and -83 <= cy <= -40) or h1_occupied(cx, cy, 1.0) \
        or (-35 <= cx <= 30 and -15 <= cy <= 16)        # qs_h1 stairs and top landing frontage
m = M("X_ring"); n_b = 0
for b in DATA["buildings"]:
    if not b["src"].startswith("taito"): continue
    fp = b["lod"].get("lod0", [[]])[0]
    if len(fp) < 4: continue
    pts = [(p[0], p[1]) for p in fp[:-1]]
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    if covered(cx, cy) or abs(cx) > 230 or abs(cy) > 230: continue
    H = float(b["attrs"].get("measuredHeight", 7) or 7); st = int(b["attrs"].get("storeysAboveGround", 2) or 2)
    if st > 60: st = 1                                  # PLATEAU 9999 = unknown (sheds, small structures)
    if H <= 0 or H > 80: H = 3 * max(1, st)
    z0 = G(cx, cy) - .3; zt = z0 + .3 + H
    if sum((pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]) for i in range(len(pts))) < 0: pts = pts[::-1]
    mat = "ctx_" + (("siding" if R.random() < .4 else "plaster") if st <= 2 else ("tile" if R.random() < .5 else "concrete"))
    tc = tint((1, 1, 1), R.uniform(.82, 1.08)); acc = R.random() * 3
    pitched = st <= 2 and H < 10
    ze = zt - (1.3 if pitched else 0)
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]; L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L < .05: continue
        u0 = acc / 3.0; u1 = (acc + L) / 3.0; acc += L
        m.poly(mat, [(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], ze), (p[0], p[1], ze)],
               [(u0, -.3 / 2.9), (u1, -.3 / 2.9), (u1, (ze - z0 - .3) / 2.9), (u0, (ze - z0 - .3) / 2.9)], tc)
    if pitched:              # gable over the footprint's oriented box, ridge along the long side
        c, ax, ay, ha, hb = obb(pts)
        if hb > ha: ax, ay, ha, hb = ay, -ax, hb, ha
        o = .35; rc = tint((.16, .17, .18), R.uniform(.8, 1.3)) if R.random() < .7 else tint((.3, .22, .18), R.uniform(.8, 1.2))
        Q = lambda s_, t_, z_: (c.x + ax.x * s_ + ay.x * t_, c.y + ax.y * s_ + ay.y * t_, z_)
        for sg in (1, -1):
            P_ = [Q(-ha - o, sg * (hb + o), ze - .1), Q(ha + o, sg * (hb + o), ze - .1), Q(ha + o, 0, zt), Q(-ha - o, 0, zt)]
            if sg < 0: P_ = [P_[1], P_[0], P_[3], P_[2]]
            m.poly("kawara", P_, None, rc)
        for sg in (1, -1):
            m.poly("ctx_plaster", [Q(sg * ha, -hb, ze), Q(sg * ha, hb, ze), Q(sg * ha, 0, zt)][::sg], [(0, 0), (1, 0), (.5, .4)], tc)
    else:
        m.poly("concrete", [(p[0], p[1], zt) for p in pts], [(p[0] / 3, p[1] / 3) for p in pts], (.55, .55, .53))
        for i in range(len(pts)):            # parapet
            p, q = pts[i], pts[(i + 1) % len(pts)]
            m.poly("concrete", [(p[0], p[1], zt), (q[0], q[1], zt), (q[0], q[1], zt + .6), (p[0], p[1], zt + .6)], None, (.6, .6, .58))
        if R.random() < .25:
            tube(m, "steel", [(cx, cy, zt), (cx, cy, zt + 2.2)], .6, 10, (.55, .56, .58))          # water tank
    n_b += 1
# Yanaka cemetery (real, OSM landuse=cemetery) south of the precinct: rows of family graves
cm = M("X_cemetery")
for i, E_ in enumerate(frange(-50.0, -12.0, 1.55)):
    for j, N_ in enumerate(frange(-85.0, -118.0, -1.0) if False else [-85.0 - k * 1.6 for k in range(20)]):
        if j % 6 == 5: continue                        # cross paths
        if R.random() < .12: continue
        z = G(E_, N_); f = Frame((E_ + R.uniform(-.1, .1), N_, z), (1, 0, 0), (0, 1, 0), (0, 0, 1))
        g = tint((.5, .5, .49), R.uniform(.6, 1.25)); dark = R.random() < .35
        box(cm, "granite", f, -.55, .55, -.5, .5, 0, .28, ch=.02, col=tint(g, .95), sc=1.2)
        box(cm, "granite", f, -.32, .32, -.28, .28, .28, .48, ch=.015, col=g, sc=1.2)
        hgt = R.uniform(.75, 1.15)
        box(cm, "granite", f, -.17, .17, -.16, .16, .48, .48 + hgt, ch=.015, col=(.12, .12, .13) if dark else g, sc=1.0)
        if R.random() < .45:                           # sotoba boards behind the stone
            for k in range(R.randint(1, 4)):
                box(cm, "plank", f, -.42 + k * .1, -.36 + k * .1, -.45, -.43, .1, R.uniform(1.4, 1.9), col=(.78, .72, .6), sc=1.9)
        if R.random() < .5:
            tube(cm, "steel", [f.p(-.25, .3, .28), f.p(-.25, .3, .5)], .035, 8, (.35, .35, .33))   # flower holders
            tube(cm, "steel", [f.p(.25, .3, .28), f.p(.25, .3, .5)], .035, 8, (.35, .35, .33))
import blk_equip
for k in range(14):                  # cemetery trees
    x, y = R.uniform(-50, -12), R.uniform(-86, -116)
    blk_equip.PROPS.append(("shrub_01", (x, y, G(x, y)), R.random() * 6.28, R.uniform(2.2, 3.4)))
gm = M("X_ground")
gm.poly("gravel", [(-52, -84, G(-40, -95) - .02), (-10, -84, G(-40, -95) - .02), (-10, -118, G(-40, -95) - .02), (-52, -118, G(-40, -95) - .02)],
        [(-52 / 2.6, -84 / 2.6), (-10 / 2.6, -84 / 2.6), (-10 / 2.6, -118 / 2.6), (-52 / 2.6, -118 / 2.6)], (.9, .88, .82))
print("RING", n_b, flush=True)
K.objs = [flush(m, K.mats, K.coll), flush(cm, K.mats, K.coll), flush(gm, K.mats, K.coll)]
K.instance_props()
CAMS = {"ring": ((10, -120, 80), (-60, -10, 0), 30), "_own": (0, 0, 0, 0)}
K.finish(a, CAMS)
