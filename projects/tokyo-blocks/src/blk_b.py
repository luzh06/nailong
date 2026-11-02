# Block B: real lots north of the street, behind the existing frontage. Coordinates are ENU metres.
import sys, os, json, time, random, argparse
sys.path.insert(0, r"D:\Cijian\src")
import bpy
from blk_core import *
from blk_arch import *

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="r1"); ap.add_argument("--cams", default="back,road,yard,roof,side,close")
ap.add_argument("--res", type=int, default=1280); ap.add_argument("--spp", type=int, default=96)
ap.add_argument("--export", type=int, default=0); ap.add_argument("--render", type=int, default=1)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
DATA = json.load(open(ROOT + r"\data\plateau_near.json"))

GZ = [(-135, 7.47), (-118, 7.5), (-100, 7.6), (-92, 7.78), (-84, 8.0), (-76, 8.28), (-67, 8.36), (-50, 8.5)]
Z_DATUM = 7.95
def G(x, y):
    for i in range(len(GZ) - 1):
        if x <= GZ[i + 1][0]:
            t = (x - GZ[i][0]) / (GZ[i + 1][0] - GZ[i][0])
            return lerp(GZ[i][1], GZ[i + 1][1], max(0, t)) - Z_DATUM
    return GZ[-1][1] - Z_DATUM

MDEF = {
    "mortar": dict(texid="mortar_n", nor_k=.7), "plaster": dict(texid="plastered_wall_04", nor_k=1.0), "mossy": dict(texid="worn_mossy_plasterwall", nor_k=.9),
    "whitetile": dict(texid="long_white_tiles", nor_k=1.0), "darkface": dict(texid="concrete_tile_facade", nor_k=1.0), "siding2": dict(texid="exterior_wall_cladding_03", nor_k=1.2),
    "tin": dict(texid="corrugated_iron_02", nor_k=1.3), "rustytin": dict(texid="rusty_corrugated_iron", nor_k=1.3), "galva": dict(texid="box_grey"),
    "blackplank": dict(texid="black_painted_planks"), "cedar": dict(texid="cedar_muted"), "soffit": dict(texid="cedar_muted"), "plank": dict(texid="weathered_plank_siding"), "fasciaw": dict(texid="weathered_plank_siding"),
    "blockwall": dict(texid="block_n"), "concrete": dict(texid="lot_n"), "asphalt": dict(texid="asphalt_02", nor_k=1.0), "lot": dict(texid="lot_n"), "gravel": dict(texid="gravel_concrete_03"),
    "slate": dict(texid="grey_roof_tiles_02"), "shutter": dict(texid="painted_metal_shutter"), "steel": dict(texid="steel_muted"),
    "kawara": dict(solid=(1, 1, 1), rough=.46, spec=.38), "roofbase": dict(solid=(.1, .1, .1), rough=.9), "alu": dict(solid=(.85, .84, .82), metal=.9, rough=.38), "pvc": dict(solid=(1, 1, 1), rough=.42),
    "paint": dict(solid=(1, 1, 1), rough=.46), "plinth_top": dict(solid=(1, 1, 1), rough=.4, metal=.6), "glass": dict(solid=(.03, .04, .045), rough=.04, alpha=.62, spec=.9), "frost": dict(solid=(.42, .47, .46), rough=.28, spec=.7),
    "dark": dict(solid=(1, 1, 1), rough=.9), "polyc": dict(solid=(.85, .88, .85), rough=.25, alpha=.72), "decal": {}, "curtain": {},
}
mats = build_materials(MDEF)
coll = bpy.data.collections.new("block_B"); bpy.context.scene.collection.children.link(coll)
ctx = bpy.data.collections.new("context"); bpy.context.scene.collection.children.link(ctx)
S = {}
def rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def mk(name, fp, H, st, **spec):
    b = Bld(name, fp, H, st, G, random.Random(sum(map(ord, name)) * 173), **spec); S[name] = b; return b
def F(b, role): return {"front": b.fi, "right": (b.fi + 1) % 4, "back": (b.fi + 2) % 4, "left": (b.fi + 3) % 4}[role]

BACK = 15.2     # keeps a 2.2 m rear alley north of the existing frontage (model x<-11)
b1 = mk("B01_white_tile_rc", rect(-98.4, BACK, -93.0, 31.6), 9.7, 3, clad=["whitetile"], tc=(.92, .9, .84), roof="flat", front=(1, 0), framecol=(.5, .5, .48), capcol=(.5, .5, .5), tank=False, hoodp=0, weather=1.5)
b1p = mk("B01b_penthouse", rect(-97.6, 22.5, -93.8, 30.6), 2.5, 1, zoff=9.7 - .62, noplinth=True, clad=["galva"], tcs={"galva": (.5, .54, .58)}, roof="mono", pitch=.12, over=.3, gover=.12, roofmat="galva", roofcol=(.5, .52, .55), front=(1, 0), rax=1, framecol=(.4, .4, .4), hoodp=.4, metalfascia=True, fasciacol=(.3, .3, .3))
b2 = mk("B02_east_wing", rect(-92.8, 23.0, -87.2, 32.2), 7.4, 2, clad=["siding2", "plank"], tcs={"siding2": (.52, .6, .62), "plank": (.68, .6, .5)}, roof="gable", pitch=.48, over=.5, rax=1, front=(0, 1), roofmat="slate", slatetc=(.5, .52, .56), fasciacol=(.25, .22, .2), hoodp=.3, framecol=(.3, .28, .25))
b3 = mk("B03_merchant_irimoya", rect(-110.6, 17.6, -105.0, 31.4), 8.8, 2, clad=["plaster", "blackplank"], tcs={"plaster": (.95, .93, .86), "blackplank": (.8, .8, .8)}, roof="irimoya", pitch=.56, over=.75, front=(1, 0), moss=True, fasciacol=(.22, .17, .13), soffitcol=(.4, .3, .22), framecol=(.3, .22, .15))
b4 = mk("B04_annex_tin", rect(-104.8, 25.6, -99.8, 31.6), 6.2, 2, clad=["rustytin"], tc=(.55, .6, .62), roof="mono", pitch=.16, over=.3, gover=.14, rax=0, roofmat="galva", roofcol=(.38, .33, .3), front=(0, -1), rust=True, gutter=False, framecol=(.5, .48, .44))
b5 = mk("B05_workshop", rect(-87.0, 19.5, -83.4, 26.6), 6.4, 1, clad=["tin"], tc=(.62, .72, .78), roof="gable", pitch=.32, over=.2, gover=.3, rax=1, roofmat="galva", roofcol=(.56, .57, .6), front=(0, -1), rust=True, gutter=False, framecol=(.5, .5, .5))
b6 = mk("B06_cross_house_main", rect(-83.0, 27.2, -72.2, 33.6), 7.1, 2, clad=["mortar"], tc=(.95, .82, .6), roof="gable", pitch=.46, over=.55, front=(0, -1), moss=True, fasciacol=(.3, .24, .18), soffitcol=(.5, .4, .3), framecol=(.45, .4, .34))
b6x = mk("B06b_cross_wing", rect(-79.8, 25.0, -75.2, 27.2), 6.6, 2, clad=["cedar"], tc=(1.0, .86, .68), roof="gable", pitch=.46, over=.4, rax=1, front=(0, -1), fasciacol=(.3, .24, .18), framecol=(.4, .32, .24))
b7 = mk("B07_three_storey_shop", rect(-70.9, 26.2, -59.6, 34.5), 9.4, 3, clad=["darkface", "plaster", "plaster"], tcs={"darkface": (1.3, 1.25, 1.15), "plaster": (.86, .82, .74)}, roof="flat", front=(1, 0), framecol=(.42, .4, .38), capcol=(.4, .4, .4), tank=True, hoodp=0)
b8 = mk("B08_long_wood_shop", rect(-72.7, 35.0, -61.0, 41.6), 8.4, 2, clad=["plank", "mortar"], tcs={"plank": (.6, .5, .4), "mortar": (.78, .84, .72)}, roof="gable", pitch=.42, over=.6, front=(1, 0), rax=1, moss=True, palette=((.075, .08, .09), (.06, .062, .07), (.1, .1, .11)), fasciacol=(.26, .2, .16), framecol=(.36, .28, .22))
b9 = mk("B09_three_storey_wood", rect(-103.6, 35.5, -96.9, 44.0), 9.7, 3, clad=["siding2", "mossy", "mossy"], tcs={"siding2": (.72, .62, .5), "mossy": (.9, .88, .82)}, roof="gable", pitch=.34, over=.35, front=(-.2, -1), rax=1, roofmat="galva", roofcol=(.3, .34, .4), framecol=(.5, .48, .44), moss=True)
b10 = mk("B10_rear_shed", rect(-80.6, BACK, -76.2, 19.0), 4.6, 1, clad=["blackplank"], tc=(.9, .9, .9), roof="gable", pitch=.3, over=.25, gover=.2, rax=0, roofmat="galva", roofcol=(.48, .46, .44), front=(0, -1), framecol=(.3, .25, .2), gutter=False)

f = F(b1, "front"); L = b1.len[f]
for fl in range(3):
    y0 = fl * b1.fh
    for k, x in enumerate(frange(1.0, L - 2.0, 3.1)):
        b1.add_win(f, x, y0 + .9 + (.1 if fl == 0 else 0), 1.65, 1.15 if fl else 1.05, "guard" if fl == 0 else "sash")
b1.add_door(F(b1, "right"), 1.2, .9, 2.05, "steel", tc=(.3, .36, .4))
b1.fenestrate(skip=(f, F(b1, "right")), widths={"back": [.9, 1.2], "left": [.75, .9]}, sparse={"left": .25, "back": .25})
b1p.fenestrate(sparse={"left": .6, "right": .6, "back": .6, "front": .2})
f = F(b2, "front"); b2.add_door(f, .7, 1.7, 2.02, "slide"); b2.add_win(f, 2.9, .95, 1.2, 1.05, "lattice"); b2.add_win(f, 1.3, b2.fh + .8, 1.65, 1.1, "sash", amado=True); b2.fenestrate(skip=(f,))
f = F(b3, "front"); L = b3.len[f]
b3.add_door(f, 5.6, 2.4, 2.1, "slide"); b3.add_win(f, 1.0, .9, 2.2, 1.2, "lattice"); b3.add_win(f, 9.2, .9, 2.6, 1.2, "lattice")
b3.add_win(f, 1.4, b3.fh + .75, 1.75, 1.1, "lattice"); b3.add_win(f, 5.7, b3.fh + .75, 1.75, 1.1, "sash", amado=True); b3.add_win(f, 9.8, b3.fh + .75, 1.75, 1.1, "lattice")
b3.fenestrate(skip=(f,), kinds={"left": ["lattice", "sash"], "back": ["sash", "frost"], "right": ["lattice", "frost"]})
f = F(b4, "front"); b4.add_door(f, .7, .85, 2.0, "steel", tc=(.36, .38, .36)); b4.add_win(f, 2.4, 1.0, 1.2, 1.0, "guard"); b4.add_win(f, 1.2, b4.fh + .75, 1.65, 1.0, "sash", hood=True); b4.fenestrate(skip=(f,), sparse={"left": .7, "right": .7, "back": .5})
f = F(b5, "front"); b5.add_garage(f, .5, 2.6, 2.7); b5.add_win(b5.fi + 1 & 3, 1.2, 2.5, 3.2, 1.0, "frost"); b5.add_win(b5.fi + 3 & 3, 2.2, 1.1, 1.65, 1.0, "guard")
f = F(b6, "front"); b6.add_win(f, .9, 1.0, 1.65, 1.05, "lattice"); b6.add_win(f, 8.2, 1.0, 1.65, 1.05, "guard"); b6.add_win(f, .9, b6.fh + .85, 1.65, 1.1, "curtain"); b6.add_win(f, 8.2, b6.fh + .85, 1.65, 1.1, "sash", amado=True); b6.fenestrate(skip=(f,))
f = F(b6x, "front"); b6x.add_door(f, 1.2, 1.7, 2.02, "slide"); b6x.add_win(f, 1.3, b6x.fh + .75, 1.65, 1.05, "lattice")
f = F(b7, "front"); L = b7.len[f]
b7.add_shop(f, .5, L - 1.0, 2.7)
for fl in (1, 2):
    for x in frange(.8, L - 2.0, 2.5):
        b7.add_win(f, x, fl * b7.fh + .85, 1.65, 1.15, "sash" if fl == 1 else "curtain")
b7.fenestrate(skip=(f,), sparse={"left": .4, "right": .35, "back": .3})
f = F(b8, "front"); L = b8.len[f]
b8.add_shop(f, .6, 3.1, 2.55); b8.add_door(f, 4.1, 1.7, 2.02, "slide")
b8.add_win(f, 1.0, b8.fh + .85, 1.65, 1.05, "lattice"); b8.add_win(f, 3.8, b8.fh + .85, 1.2, 1.05, "sash", amado=True)
b8.fenestrate(skip=(f,))
f = F(b9, "front"); b9.add_door(f, .6, .85, 2.05, "steel", tc=(.26, .3, .3)); b9.add_win(f, 2.2, 1.0, 1.65, 1.05, "guard"); b9.fenestrate(skip=(f,))
f = F(b10, "front"); b10.add_door(f, 1.6, .85, 1.95, "steel", tc=(.3, .26, .2)); b10.add_win(F(b10, "right"), 1.0, 1.2, .9, .8, "frost")

def attach():
    f = F(b3, "front"); b3.lean(f, .3, b3.len[f] - .3, b3.fh + .34, depth=1.15, drop=.5)
    f = F(b6, "back"); b6.lean(f, .4, 5.0, 2.9, depth=1.0, drop=.3, mat="galva")
    f = F(b8, "front"); b8.lean(f, .2, b8.len[f] - .2, b8.fh + .22, depth=.9, drop=.3)
    f = F(b2, "front"); b2.balcony(f, .3, b2.len[f] - .3, 1, depth=.7, style="panel")
    f = F(b9, "back"); b9.balcony(f, .6, 5.6, 2, depth=.8, style="bars")
    f = F(b7, "back"); b7.balcony(f, 2.0, 8.5, 2, depth=.9, style="conc")
    # external concrete stair up the white RC block
    fr = b1.frames[F(b1, "right")]; H1 = b1.fh
    for fl in range(2):
        n = 15; x0, x1 = (8.6, 12.0) if fl == 0 else (12.0, 8.6)
        c0, c1 = .05, 1.0
        for i in range(n):
            xa = lerp(x0, x1, i / n); xb = lerp(x0, x1, (i + 1) / n); y = (fl + (i + 1) / n) * H1
            box(b1.m, "concrete", fr, min(xa, xb), max(xa, xb), y - .17, y, c0 + (fl and 1.0), c1 + (fl and 1.0), ch=.006, col=(.7, .69, .65), sc=2.2)
        tube(b1.m, "alu", [fr.p(x0, (fl) * H1 + .95, (c1 + (fl and 1.0)) + .03), fr.p(x1, (fl + 1) * H1 + .95, (c1 + (fl and 1.0)) + .03)], .018, 6, (.5, .5, .5))
    box(b1.m, "concrete", fr, 12.0, 13.2, H1 - .16, H1, .05, 2.05, ch=.01, col=(.7, .69, .65), sc=2.2)
    for b in (b6, b3, b8):
        c = b.Q(0, 0, b.e + b.rise - .02); b.antenna(c, 2.1)
attach()
b5.anchor("ac_outdoor", F(b5, "left"), 1.0, .1); b1.anchor("ac_outdoor", F(b1, "back"), 2.0, .1); b1.anchor("ac_outdoor", F(b1, "back"), 3.6, .1)
b3.anchor("ac_outdoor", F(b3, "back"), 3.0, .1); b6.anchor("planter", F(b6, "front"), 5.0, .1); b2.anchor("bicycle", F(b2, "front"), 3.8, .0)
b8.anchor("planter", F(b8, "front"), 6.8, .0); b10.anchor("gas_meter", F(b10, "front"), .7, 1.1); b9.anchor("ac_outdoor", F(b9, "left"), 2.6, .1)

objs = [flush(b.build(), mats, coll) for b in S.values()]

gm = M("B_ground"); wm = M("B_walls")
RG = random.Random(88)
ROADS = [[(-54.0, 6.3), (-53.2, 23.8), (-53.2, 32.7), (-54.1, 39.1), (-55.2, 45.0), (-56.6, 49.0), (-60.3, 48.0), (-59.6, 47.1), (-58.9, 44.9), (-57.8, 39.7), (-57.4, 34.4), (-57.3, 28.7), (-57.3, 19.0), (-57.3, 11.7), (-58.4, 4.9)],
         [(-107.1, 33.0), (-103.7, 33.8), (-106.3, 44.2), (-108.5, 52.6), (-111.4, 61.4), (-113.8, 60.5), (-109.7, 43.4)]]
GRAVEL = [(-75.0, 19.5), (-58.0, 19.5), (-58.0, 25.8), (-75.0, 25.2)]
EDGE_E = [(-57.3, 13.0), (-57.3, 19.0), (-57.3, 28.7), (-57.4, 34.4), (-57.8, 39.7), (-58.9, 44.9), (-59.6, 47.1)]
EDGE_E2 = [(-54.0, 6.3), (-53.2, 23.8), (-53.2, 32.7), (-54.1, 39.1), (-55.2, 45.0), (-56.6, 49.0)]
EDGE_W = [(-107.1, 33.0), (-109.7, 43.4)]; EDGE_W2 = [(-103.7, 33.8), (-106.3, 44.2)]
ALLEY = [(-111.5, 14.15), (-90, 14.15), (-70, 14.15), (-57.6, 14.15)]
ALLEY2 = [(-99.25, 14.4), (-99.15, 25.2)]
ALLEY3 = [(-86.0, 14.4), (-85.7, 18.9)]

E0, E1, N0, N1 = -116.0, -50.0, 12.9, 48.0     # N0 stays clear of frontage eaves (model x<-11)
cell = .3
nx = int((E1 - E0) / cell); ny = int((N1 - N0) / cell)
inside = [(b.c, b.ax, b.ay, b.a - .35, b.b - .35) for b in S.values() if not b.noplinth]
def classify(x, y):
    for c, ax, ay, ha, hb in inside:
        d = V((x, y, 0)) - c
        if abs(d.dot(ax)) < ha and abs(d.dot(ay)) < hb: return 2
    for r in ROADS:
        if pip((x, y), r): return 1
    if pip((x, y), GRAVEL): return 3
    return 0
cls = [[classify(E0 + (i + .5) * cell, N0 + (j + .5) * cell) for j in range(ny)] for i in range(nx)]
def gz(x, y, c):
    z = G(x, y) + (-.05 if c == 1 else .012)
    return z + .008 * nz((x, y, 0), .6) + .004 * nz((x, y, 0), 2.1) + (.012 * nz((x, y, 7), .25) if c == 1 else 0) + (.02 * nz((x, y, 3), 1.3) if c == 3 else 0)
def gcol(x, y, base):
    return tint(base, max(.4, 1 + .16 * nz((x, y, 3), .22) + .1 * nz((x, y, 9), .9) + .05 * nz((x, y, 1), 3.3)))
for c_, mat, sc, base in ((1, "asphalt", 3.4, (.82, .82, .84)), (0, "lot", 2.4, (.7, .69, .66)), (3, "gravel", 2.6, (1.0, .97, .9))):
    PP = [[V((E0 + i * cell, N0 + j * cell, gz(E0 + i * cell, N0 + j * cell, c_))) for j in range(ny + 1)] for i in range(nx + 1)]
    UV = [[(p.x / sc, p.y / sc) for p in r] for r in PP]; CC = [[gcol(p.x, p.y, base) for p in r] for r in PP]
    gm.grid(mat, PP, UV, CC, smooth=True, skip=lambda i, j, r=c_: cls[i][j] != r)
def on_ground(cx, cy, w, h, cell_, rot=0, c=1):
    u = V((cos(rot), sin(rot), 0)); v = V((-sin(rot), cos(rot), 0)); nu = 8; nv = max(2, int(8 * h / w)); P = []; UV = []
    cu0 = (cell_ % 4) / 4; cv1 = 1 - (cell_ // 4) / 4
    for i in range(nu + 1):
        r = []; q = []
        for j in range(nv + 1):
            p = V((cx, cy, 0)) + u * (w * (i / nu - .5)) + v * (h * (j / nv - .5))
            r.append(V((p.x, p.y, gz(p.x, p.y, c) + .004))); q.append((cu0 + i / nu / 4, cv1 - .25 + j / nv / 4))
        P.append(r); UV.append(q)
    gm.grid("decal", P, UV, [[(1, 1, 1)] * (nv + 1) for _ in range(nu + 1)], smooth=True)
for pos, size, rot in (((-55.4, 22), (1.4, 6.5), 0), ((-55.8, 37), (5.0, 1.4), 1.5)):
    on_ground(pos[0], pos[1], size[0], size[1], 12, rot)
for k in range(40):
    x = RG.uniform(-114, -52); y = RG.uniform(14.5, 47); c = classify(x, y)
    if c == 2: continue
    s_ = RG.uniform(.8, 3.0); on_ground(x, y, s_, s_ * RG.uniform(.5, 1), RG.choice((14, 6, 7)), RG.random() * 3, c)
road_paint(gm, [(p[0] + .32, p[1]) for p in EDGE_E], G)
ribbon_lids(gm, EDGE_E[1:], G, RG); ribbon_lids(gm, [(-53.7, 13.0)] + EDGE_E2[1:], G, RG, width=.5); ribbon_lids(gm, EDGE_W, G, RG); ribbon_lids(gm, EDGE_W2, G, RG)
ribbon_lids(gm, ALLEY, G, RG, width=.3, grate_every=5, tc=(.48, .48, .46)); ribbon_lids(gm, ALLEY2, G, RG, width=.26, grate_every=7, tc=(.46, .46, .44)); ribbon_lids(gm, ALLEY3, G, RG, width=.26, grate_every=7, tc=(.46, .46, .44))
block_wall(wm, [(-75.0, 19.4), (-58.3, 19.4)], G, RG, h=.9, tc=(.8, .79, .75))
block_wall(wm, [(-75.0, 19.4), (-75.0, 25.0)], G, RG, h=1.3)
block_wall(wm, [(-111.5, 17.0), (-105.0, 17.0), (-105.0, 25.2)], G, RG, h=1.5)
block_wall(wm, [(-99.9, 31.8), (-99.9, 35.2), (-104.0, 35.2)], G, RG, h=1.1)
block_wall(wm, [(-92.7, 22.8), (-87.2, 22.8), (-87.2, 19.4)], G, RG, h=1.4, tc=(.62, .62, .58))
block_wall(wm, [(-83.2, 19.2), (-83.2, 25.0)], G, RG, h=1.0)
objs.append(flush(gm, mats, coll)); objs.append(flush(wm, mats, coll))

cm = M("context_mass"); mats["ctx"] = pbr("ctx", solid=(.2, .19, .18), rough=.8)
own = [b.c for b in S.values()]
for b in DATA["buildings"]:
    fp = b["lod"].get("lod0", [[]])[0]
    if len(fp) < 4: continue
    cx = sum(p[0] for p in fp) / len(fp); cy = sum(p[1] for p in fp) / len(fp)
    if any(abs(cx - c.x) < 5 and abs(cy - c.y) < 5 for c in own): continue
    if -114 < cx < -58 and 5 < cy < 46: continue
    h = float(b["attrs"].get("measuredHeight", 7)); z = G(cx, cy); n = len(fp) - 1
    for i in range(n):
        p, q = fp[i], fp[i + 1]; cm.poly("ctx", [(p[0], p[1], z - 1), (q[0], q[1], z - 1), (q[0], q[1], z + h), (p[0], p[1], z + h)])
    cm.poly("ctx", [(p[0], p[1], z + h) for p in fp[:-1]])
for x0, x1 in ((-114, -96), (-96, -82), (-82, -68), (-68, -58)):       # stand-in for the existing frontage backs
    hh = {-114: 7.6, -96: 8.4, -82: 6.8, -68: 7.4}[x0]; yy = 12.6
    for p, q in (((x0, yy), (x1, yy)), ((x1, yy), (x1, 3)), ((x0, 3), (x0, yy))):
        cm.poly("ctx", [(p[0], p[1], -1), (q[0], q[1], -1), (q[0], q[1], hh), (p[0], p[1], hh)])
    cm.poly("ctx", [(x0, 3, hh), (x1, 3, hh), (x1, yy, hh), (x0, yy, hh)])
cm.poly("ctx", [(-400, -400, -.2), (400, -400, -.2), (400, 400, -.2), (-400, 400, -.2)], None, (.28, .28, .28))
flush(cm, mats, ctx)

tot = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
print("TRIS", tot, "objs", len(objs), flush=True)
anchors = [x for b in S.values() for x in b.anchors]
OUTD = ROOT + r"\output\blocks"; EXP = ROOT + r"\export\blocks\block_B"; os.makedirs(EXP, exist_ok=True)
json.dump(dict(block="B", tris=tot, anchors=anchors, rear_alley_centerline_enu=ALLEY, side_alleys_enu=[ALLEY2, ALLEY3], edges_enu=dict(east_road_west=EDGE_E),
               buildings={k: dict(center=[round(b.c.x, 2), round(b.c.y, 2)], size=[round(b.a * 2, 2), round(b.b * 2, 2)], H=b.H, storeys=b.st, base_z=round(b.base, 3), roof=b.roofkind) for k, b in S.items()}),
          open(EXP + r"\block_B_meta.json", "w"), indent=1, ensure_ascii=False)
CAMS = {"back": ((-92.6, 14.2, 1.75), (-70, 18.5, 3.0), 26), "road": ((-55.5, 46, 1.75), (-66, 31, 4.2), 26), "yard": ((-60, 21, 1.75), (-80, 31, 4.2), 26),
        "roof": ((-38, 62, 22), (-85, 27, 5), 32), "side": ((-99.2, 16.2, 1.75), (-99.6, 27, 3), 24), "close": ((-90.8, 18.0, 1.75), (-94.6, 19.6, 1.7), 30)}
if a.export:
    export_glb(coll, EXP + r"\block_B.glb"); print("GLB", os.path.getsize(EXP + r"\block_B.glb") / 1e6, flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=ROOT + r"\blend\block_B.blend", compress=True)
if a.render:
    setup_render(a.res, a.spp); lighting()
    for n in a.cams.split(","):
        pos, look, lens = CAMS[n]
        cam = add_cam(n, pos, look, lens); bpy.context.scene.camera = cam
        bpy.context.scene.render.filepath = OUTD + f"\\B_{a.tag}_{n}.jpg"
        t1 = time.time(); bpy.ops.render.render(write_still=True); print("RENDER", n, round(time.time() - t1), flush=True)
print("ALLDONE", round(time.time() - t0), flush=True)
sys.stdout.flush(); os._exit(0)
