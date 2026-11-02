# Block A: real block south of the lane behind the existing street. Coordinates are ENU metres.
import sys, os, json, time, random, argparse
sys.path.insert(0, r"D:\project\cijian\work\src")
import bpy
import importlib, blk_core, blk_arch
from blk_core import *
from blk_arch import *

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="r1"); ap.add_argument("--cams", default="lane,alley,south,diag,roof,close")
ap.add_argument("--res", type=int, default=1280); ap.add_argument("--spp", type=int, default=96)
ap.add_argument("--export", type=int, default=0); ap.add_argument("--render", type=int, default=1)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
DATA = json.load(open(ROOT + r"\data\plateau_near.json"))

GZ = [(-135, 7.47), (-118, 7.5), (-100, 7.6), (-92, 7.78), (-84, 8.0), (-76, 8.28), (-67, 8.36), (-50, 8.5)]
Z_DATUM = 7.95    # PLATEAU height that maps to model street level z=0

def G(x, y):
    for i in range(len(GZ) - 1):
        if x <= GZ[i + 1][0]:
            t = (x - GZ[i][0]) / (GZ[i + 1][0] - GZ[i][0])
            return lerp(GZ[i][1], GZ[i + 1][1], max(0, t)) - Z_DATUM
    return GZ[-1][1] - Z_DATUM

def fp_at(cx, cy):
    best = None
    for b in DATA["buildings"]:
        fp = b["lod"].get("lod0", [[]])[0]
        if len(fp) < 3: continue
        ccx = sum(p[0] for p in fp) / len(fp); ccy = sum(p[1] for p in fp) / len(fp)
        d = (ccx - cx) ** 2 + (ccy - cy) ** 2
        if best is None or d < best[0]: best = (d, b, fp)
    return [(p[0], p[1]) for p in best[2][:-1]], best[1]

MDEF = {
    "mortar": dict(texid="mortar_n", nor_k=.7), "plaster": dict(texid="plastered_wall_04", nor_k=1.0), "beige": dict(texid="mortar_n", nor_k=.55),
    "siding": dict(texid="exterior_wall_cladding", nor_k=1.2), "siding2": dict(texid="exterior_wall_cladding_03", nor_k=1.2),
    "facetile": dict(texid="facade_tiles_n", nor_k=1.1), "tin": dict(texid="corrugated_iron_02", nor_k=1.3),
    "rustytin": dict(texid="rusty_corrugated_iron", nor_k=1.3), "galva": dict(texid="box_grey"),
    "blackplank": dict(texid="black_painted_planks"), "cedar": dict(texid="cedar_muted"), "soffit": dict(texid="cedar_muted"),
    "fasciaw": dict(texid="weathered_plank_siding"), "plank": dict(texid="weathered_plank_siding"), "blockwall": dict(texid="block_n"), "concrete": dict(texid="lot_n"),
    "asphalt": dict(texid="asphalt_02", nor_k=1.0), "lot": dict(texid="lot_n"), "gravel": dict(texid="gravel_concrete_03"),
    "slate": dict(texid="grey_roof_01"), "shutter": dict(texid="painted_metal_shutter"), "steel": dict(texid="steel_muted"),
    "kawara": dict(solid=(1, 1, 1), rough=.46, spec=.38), "roofbase": dict(solid=(.1, .1, .1), rough=.9),
    "alu": dict(solid=(.85, .84, .82), metal=.9, rough=.38), "pvc": dict(solid=(1, 1, 1), rough=.42), "paint": dict(solid=(1, 1, 1), rough=.46),
    "plinth_top": dict(solid=(1, 1, 1), rough=.4, metal=.6), "glass": dict(solid=(.03, .04, .045), rough=.04, alpha=.62, spec=.9),
    "frost": dict(solid=(.42, .47, .46), rough=.28, spec=.7), "dark": dict(solid=(1, 1, 1), rough=.9), "polyc": dict(solid=(.85, .88, .85), rough=.25, alpha=.72),
    "decal": {}, "curtain": {},
}
mats = build_materials(MDEF)
coll = bpy.data.collections.new("block_A"); bpy.context.scene.collection.children.link(coll)
ctx = bpy.data.collections.new("context"); bpy.context.scene.collection.children.link(ctx)

R = random.Random(20261102)
S = {}
def mk(name, cx, cy, **spec):
    fp, src = fp_at(cx, cy)
    h = float(src["attrs"].get("measuredHeight", 7)); st = int(src["attrs"].get("storeysAboveGround", 2))
    h = spec.pop("H", h); st = spec.pop("st", st)
    b = Bld(name, fp, h, st, G, random.Random(hash(name) % 99991 if False else sum(map(ord, name)) * 131), **spec)
    S[name] = b
    return b

# --- north row, facing the lane (+N) ---
a1 = mk("A01_apartment", -110.5, -26.9, clad=["facetile"], tc=(.86, .78, .68), roof="flat", front=(0, 1), framecol=(.42, .4, .37), tank=True, weather=.8,
        railcol=(.32, .33, .34), hoodp=.0, trim=[((0, 1), 1.2)])
a2 = mk("A02_old_mortar", -97.7, -25.0, clad=["mortar"], tc=(.83, .78, .68), roof="hip", pitch=.46, over=.6, front=(0, 1), moss=True, hoodp=.4, gutter=True,
        fasciacol=(.34, .28, .22), soffitcol=(.5, .42, .32), framecol=(.5, .47, .42))
a3 = mk("A03_tin_shed", -88.2, -28.2, clad=["tin"], tc=(.78, .8, .78), roof="gable", roofmat="galva", roofcol=(.42, .36, .32), pitch=.3, over=.25, gover=.18, front=(0, -1), rust=True,
        gutter=False, framecol=(.55, .52, .48), weather=1.2)
a4 = mk("A04_low_plank", -87.1, -24.6, clad=["blackplank", "plank"], tc=(.7, .7, .7), tcs={"plank": (.62, .55, .46)}, roof="mono", pitch=.14, over=.32, gover=.15, roofmat="galva", roofcol=(.5, .52, .55),
        front=(0, 1), H=6.0, framecol=(.35, .28, .22), hoodp=.5, moss=True)
a5 = mk("A05_siding_house", -80.0, -26.9, clad=["siding"], tc=(.86, .85, .8), roof="gable", roofmat="slate", slatetc=(.62, .6, .6), pitch=.5, over=.4, front=(0, 1), metalfascia=True,
        fasciacol=(.3, .3, .3), framecol=(.35, .33, .3), guttercol=(.34, .34, .33), hoodp=.1, weather=.75, rax=1)
# --- corner and diagonal road shop-houses ---
a7 = mk("A07_corner_tile", -67.3, -24.8, clad=["plaster", "facetile"], tcs={"plaster": (.8, .8, .76), "facetile": (.72, .68, .62)}, roof="flat", front=(0, 1), framecol=(.55, .54, .5), H=8.6, st=2, hoodp=.0,
        capcol=(.45, .44, .42), trim=[((1, 0), .3)])
a6 = mk("A06_gable_shop", -69.0, -30.5, clad=["beige"], tc=(.82, .76, .64), roof="gable", pitch=.4, over=.5, front=(1, -.45), moss=True, fasciacol=(.3, .25, .2), hoodp=.3)
a8 = mk("A08_kanban_front", -74.1, -37.3, clad=["mortar"], tc=(.66, .7, .68), roof="kanban", pitch=.36, over=.25, front=(1, -.45), rax=1, parapet=7.6, roofmat="galva", roofcol=(.46, .42, .4),
        fasciacol=(.45, .42, .4), framecol=(.42, .4, .36), hoodp=.0, H=7.1)
# --- south road houses ---
a9 = mk("A09_small_kawara", -82.6, -39.9, clad=["plank", "plaster"], tcs={"plank": (.52, .42, .32), "plaster": (.9, .87, .8)}, roof="gable", pitch=.44, over=.42, front=(-.3, -1), rax=1, moss=True, palette=((.2, .15, .12), (.16, .12, .1), (.25, .19, .15)), roofcol=(.15, .12, .1), framecol=(.3, .24, .18))
a10 = mk("A10_green_tin", -78.4, -42.5, clad=["tin"], tc=(.72, .88, .78), roof="gable", roofmat="galva", roofcol=(.34, .4, .42), pitch=.4, over=.3, front=(-.3, -1), rax=1, rust=True, framecol=(.58, .56, .5))
a11 = mk("A11_old_L_house", -88.9, -37.1, clad=["plaster", "cedar"], tcs={"plaster": (.86, .83, .76), "cedar": (1.05, .92, .76)}, roof="hip", pitch=.5, over=.7, front=(0, -1), moss=True, fasciacol=(.3, .24, .18), soffitcol=(.45, .36, .26), framecol=(.42, .34, .26), trim=[((0, 1), .3)])
# --- west townhouse row, each built differently ---
a12 = mk("A12_townhouse_slit", -98.4, -35.5, clad=["siding2"], tc=(.34, .35, .37), roof="mono", pitch=.09, over=.12, gover=.08, roofmat="galva", roofcol=(.34, .35, .37), front=(0, -1), rax=0, metalfascia=True, fasciacol=(.24, .24, .25), framecol=(.22, .22, .22), guttercol=(.2, .2, .2), hoodp=0, weather=.55)
a13 = mk("A13_townhouse_white", -103.1, -36.3, clad=["plaster"], tc=(.93, .92, .88), roof="flat", front=(0, -1), framecol=(.65, .64, .6), hoodp=0, weather=.7, capcol=(.6, .6, .6))
a14 = mk("A14_townhouse_tile", -107.1, -36.6, clad=["facetile", "siding"], tcs={"facetile": (.62, .5, .42), "siding": (.8, .76, .68)}, roof="gable", pitch=.36, over=.25, gover=.15, roofmat="slate", slatetc=(.45, .43, .46), front=(0, -1), metalfascia=True, fasciacol=(.33, .3, .27), framecol=(.3, .28, .26), hoodp=.1)
a15 = mk("A15_townhouse_galva", -113.0, -36.2, clad=["galva", "galva", "siding"], tcs={"galva": (.62, .64, .66), "siding": (.72, .6, .46)}, roof="mono", pitch=.16, over=.3, gover=.1, roofmat="galva", roofcol=(.55, .57, .6), front=(0, -1), rax=0, metalfascia=True, fasciacol=(.3, .3, .3), framecol=(.3, .3, .3), hoodp=.2)
a16 = mk("A16_townhouse_beige", -115.9, -34.9, clad=["beige"], tc=(.88, .8, .68), roof="gable", pitch=.4, over=.2, gover=.12, front=(0, -1), rax=0, palette=((.06, .058, .06), (.045, .045, .05)), framecol=(.5, .48, .42), hoodp=.3, trim=[((1, 0), .2)])

# ---- openings per building ----
def F(b, role):
    return {"front": b.fi, "right": (b.fi + 1) % 4, "back": (b.fi + 2) % 4, "left": (b.fi + 3) % 4}[role]

# A01 gallery apartment: doors and kitchen windows on lane side
f = F(a1, "front"); L = a1.len[f]
for fl in range(3):
    y = fl * a1.fh + (.12 if fl == 0 else 0)
    n = 3
    for k in range(n):
        x = .9 + k * (L - 1.5) / n
        a1.holes[f].append((x, y + .1, x + .85, y + 2.1)); a1.ops.append(("door", f, x, y + .1, .85, 2.0, "steel", {"tc": (.42, .5, .54)}))
        a1.add_win(f, x + 1.25, y + .95, .9, .9, "guard")
a1.fenestrate(skip=(f,), kinds={"back": ["sash", "sash", "curtain"]}, widths={"back": [1.65, 1.2]}, sparse={"back": .05})
# A02 old house: lean-to front, sliding entrance, lattice
f = F(a2, "front"); L = a2.len[f]
a2.add_door(f, 1.1, 1.65, 2.02, "slide")
a2.add_win(f, 3.4, 1.0, 1.75, 1.05, "lattice")
a2.add_win(f, 5.6, 1.0, 1.3, 1.05, "guard")
a2.add_win(f, .9, a2.fh + .85, 1.75, 1.1, "sash", amado=True)
a2.add_win(f, 4.3, a2.fh + .85, 1.75, 1.1, "curtain")
a2.fenestrate(skip=(f,))
# A03 tin shed: faces the alley, few openings
f = F(a3, "front"); a3.add_door(f, 1.2, .85, 2.0, "steel", tc=(.4, .42, .4)); a3.add_win(f, 3.0, 1.0, 1.2, 1.0, "guard")
a3.add_win(f, 1.0, a3.fh + .8, 1.65, 1.0, "sash")
a3.fenestrate(skip=(f,), sparse={"left": .6, "right": .6, "back": .7})
# A04 narrow low
f = F(a4, "front"); L = a4.len[f]
a4.add_door(f, .6, .85, 2.0, "steel", tc=(.36, .3, .25)); a4.add_win(f, 2.0, .95, 1.2, 1.0, "lattice"); a4.add_win(f, 1.0, a4.fh + .7, 1.65, 1.0, "sash", hood=True)
a4.fenestrate(skip=(f,), sparse={"back": .6})
# A05 siding house with balcony
f = F(a5, "front"); L = a5.len[f]
a5.add_door(f, .8, .9, 2.05, "steel", tc=(.3, .26, .22)); a5.add_garage(f, L - 3.2, 2.7, 2.2)
a5.add_win(f, .9, a5.fh + .35, 1.75, 1.8, "sash"); a5.add_win(f, L - 2.6, a5.fh + .85, 1.2, 1.1, "curtain")
a5.fenestrate(skip=(f,))
# A06 gable shop: storefront slot on diagonal road
f = F(a6, "front"); L = a6.len[f]
a6.add_shop(f, .7, min(4.8, L - 1.4)); a6.add_win(f, 1.0, a6.fh + .8, 1.75, 1.1, "sash"); a6.add_win(f, L - 2.3, a6.fh + .8, 1.2, 1.1, "curtain")
a6.fenestrate(skip=(f,), sparse={"left": .35, "right": .35})
# A07 corner: slots on two faces
f = F(a7, "front"); L = a7.len[f]
a7.add_shop(f, .6, L - 1.2, 2.75)
r = F(a7, "right"); a7.add_shop(r, .5, a7.len[r] - 1.4, 2.75)
for x in frange(.7, L - 1.8, 2.4): a7.add_win(f, x, a7.fh + .9, 1.65, 1.2, "sash")
for x in frange(.6, a7.len[r] - 1.6, 2.1): a7.add_win(r, x, a7.fh + .9, 1.2, 1.2, "curtain")
a7.fenestrate(skip=(f, r))
# A08 kanban front
f = F(a8, "front"); L = a8.len[f]
a8.add_shop(f, .6, L - 1.2, 2.5); a8.add_win(f, 1.1, 3.75, 1.3, 1.25, "sash"); a8.add_win(f, L - 2.6, 3.75, 1.3, 1.25, "sash")
a8.fenestrate(skip=(f,), sparse={"left": .5, "right": .5, "back": .4})
# south road houses
f = F(a9, "front"); a9.add_door(f, .7, 1.65, 2.0, "slide"); a9.add_win(f, 2.9, .95, .9, 1.05, "lattice"); a9.add_win(f, .9, a9.fh + .8, 1.65, 1.1, "sash", amado=True); a9.fenestrate(skip=(f,))
f = F(a10, "front"); a10.add_door(f, .6, .85, 2.0, "steel", tc=(.5, .46, .38)); a10.add_win(f, 1.7, .95, .9, 1.0, "guard"); a10.add_win(f, .7, a10.fh + .75, 1.2, 1.05, "sash", hood=True); a10.fenestrate(skip=(f,))
f = F(a11, "front"); L = a11.len[f]
a11.add_door(f, 2.3, 1.7, 2.02, "slide"); a11.add_win(f, 4.6, 1.0, 1.75, 1.05, "lattice"); a11.add_win(f, .7, 1.0, 1.2, 1.05, "lattice")
a11.add_win(f, 1.2, a11.fh + .8, 1.75, 1.1, "sash", amado=True); a11.add_win(f, 5.0, a11.fh + .8, 1.75, 1.1, "sash", amado=True)
a11.fenestrate(skip=(f,))
# townhouses: garage or door at ground, unique upper storeys
f = F(a12, "front"); L = a12.len[f]
a12.add_garage(f, .25, min(2.55, L - .5)); a12.add_door(f, 2.95, .85, 2.05, "steel", tc=(.16, .16, .17)) if L > 4 else None
a12.add_win(f, L * .5 - .35, a12.fh + .2, .7, 4.8, "sash")
a12.add_win(f, .5, a12.fh * 2 + .85, .45, 1.2, "sash")
a12.fenestrate(skip=(f,), sparse={"left": .75, "right": .75, "back": .4})
f = F(a13, "front"); L = a13.len[f]
a13.add_door(f, .4, .9, 2.05, "steel", tc=(.28, .22, .16)); a13.add_garage(f, 1.6, max(1.6, L - 1.9), 2.2) if L > 3.5 else None
a13.add_win(f, .5, a13.fh + .35, L - 1.0, 1.75, "sash"); a13.add_win(f, 1.0, a13.fh * 2 + .85, 1.2, 1.1, "curtain")
a13.fenestrate(skip=(f,), sparse={"left": .7, "right": .7, "back": .3})
f = F(a14, "front"); L = a14.len[f]
a14.add_door(f, .55, .85, 2.05, "steel", tc=(.33, .22, .15)); a14.add_win(f, 1.8, .95, 1.2, 1.1, "guard")
a14.add_win(f, .6, a14.fh + .35, 1.65, 1.8, "sash"); a14.add_win(f, 1.0, a14.fh * 2 + .8, 1.2, 1.1, "sash")
a14.fenestrate(skip=(f,), sparse={"left": .7, "right": .7, "back": .4})
f = F(a15, "front"); L = a15.len[f]
a15.add_garage(f, .3, min(2.4, L - .6), kind="open"); a15.add_win(f, .6, a15.fh + .85, 1.2, 1.1, "sash", hood=True); a15.add_win(f, .9, a15.fh * 2 + .35, 1.65, 1.8, "sash")
a15.fenestrate(skip=(f,), sparse={"left": .8, "right": .8, "back": .35})
f = F(a16, "front"); L = a16.len[f]
a16.add_door(f, 1.4, .85, 2.0, "steel", tc=(.4, .3, .2)); a16.add_win(f, .3, 1.0, .75, 1.0, "guard")
a16.add_win(f, .9, a16.fh + .8, 1.65, 1.1, "sash"); a16.add_win(f, .9, a16.fh * 2 + .8, 1.2, 1.1, "curtain")
a16.fenestrate(skip=(f,), sparse={"left": .7, "right": .7, "back": .3})

objs = []
for b in S.values():
    pass
# attachments that need finished dimensions, added before build so walls know nothing about them
def attach():
    f = F(a2, "front"); a2.lean(f, .2, a2.len[f] - .2, a2.fh + .3, depth=1.0, drop=.42)
    f = F(a11, "front"); a11.lean(f, .3, a11.len[f] - .3, a11.fh + .34, depth=1.1, drop=.46)
    f = F(a9, "front"); a9.lean(f, .1, a9.len[f] - .1, a9.fh + .28, depth=.8, drop=.36)
    f = F(a6, "front"); a6.lean(f, .1, a6.len[f] - .1, a6.fh + .1, depth=.7, drop=.22, mat="galva")
    f = F(a5, "front"); a5.balcony(f, .5, 3.0, 1, style="panel")
    f = F(a14, "front"); a14.balcony(f, .3, a14.len[f] - .3, 1, depth=.6, style="bars")
    f = F(a15, "front"); a15.balcony(f, .3, a15.len[f] - .3, 2, depth=.55, style="bars")
    f = F(a13, "front"); a13.balcony(f, .3, a13.len[f] - .3, 1, depth=.7, style="conc")
    a2_ = F(a2, "back"); a2.balcony(a2_, 1.0, 4.5, 1, depth=.8, style="bars")
    a11b = F(a11, "back"); a11.lean(a11b, .5, min(4.6, a11.len[a11b] - .5), a11.fh + .1, depth=.9, drop=.3, mat="galva")
    a3f = F(a3, "left"); a3.lean(a3f, .3, a3.len[a3f] - .3, 2.5, depth=1.1, drop=.25, mat="galva")
    # kanban: moulded cornice bands on the false front
    f = F(a8, "front"); L = a8.len[f]; P_ = a8.sp["parapet"]
    fr = a8.frames[f]
    for y, ht, dp in ((P_ - .06, .1, .1), (P_ - .3, .05, .05), (3.3, .1, .08), (2.65, .2, .06)):
        box(a8.m, "mortar", fr, -.02, L + .02, y, y + ht, 0, dp, ch=.012, col=(.6, .64, .62), sc=2.3)
    for x in (0.25, L - .55):
        box(a8.m, "mortar", fr, x, x + .3, 2.85, P_ - .3, 0, .05, ch=.01, col=(.62, .66, .64), sc=2.3)
    box(a8.m, "alu", fr, 1.0, L - 1.0, 5.45, 6.75, 0, .012, ch=.003, col=(.32, .4, .36))
    # A01 gallery and stair
    f = F(a1, "front"); L = a1.len[f]; fr = a1.frames[f]
    for fl in (1, 2):
        y = fl * a1.fh
        box(a1.m, "concrete", fr, -.0, L, y - .22, y + .08, 0, 1.2, ch=.012, col=(.74, .72, .68), sc=2.2)
        box(a1.m, "facetile", fr, -.0, L, y + .08, y + .98, 1.08, 1.2, ch=.01, col=(.86, .78, .68), sc=1.6)
        box(a1.m, "alu", fr, -.0, L, y + .98, y + 1.03, 1.05, 1.22, ch=.008, col=(.4, .4, .4))
        for x in frange(1.5, L, 1.6):
            tube(a1.m, "pvc", [fr.p(x, y - .22, 1.14), fr.p(x, y - 1.2, 1.14)], .02, 6, (.5, .5, .48))
    for x in (.1, L / 2, L - .2):
        box(a1.m, "concrete", fr, x, x + .24, -.3, a1.fh * 2, .95, 1.19, ch=.012, col=(.72, .71, .67), sc=2.2)
    # steel stair at the west end of the gallery
    W = L + .1; sf = fr
    def stair(y0, y1, x0, x1, c0, c1):
        n = max(3, int((y1 - y0) / .19)); run = (x1 - x0) / n
        for i in range(n):
            x_ = x0 + i * run; y_ = y0 + (i + 1) * (y1 - y0) / n
            box(a1.m, "steel", sf, min(x_, x_ + run), max(x_, x_ + run), y_ - .02, y_, c0, c1, ch=.003, col=(.32, .33, .34), sc=1.2)
        for c in (c0, c1 - .012):
            P = [sf.p(x0, y0, c), sf.p(x1, y1, c), sf.p(x1, y1 + .2, c), sf.p(x0, y0 + .2, c)]
            a1.m.poly("steel", P, [(0, 0), (1, 0), (1, .1), (0, .1)], (.3, .3, .31))
    stair(0, a1.fh, L + 3.0, L + .3, .2, 1.1)
    stair(a1.fh, a1.fh * 2, L + .3, L + 3.0, 1.15, 2.05)
    # A07 awning rail for the storefront, left bare
    # rooftop extras and ridge antennas on pitched houses
    for b in (a2, a9, a5, a16):
        a = b.Q(0, 0, b.e + b.rise - .02); b.antenna(a, 1.9)

attach()

alley = [(-119.5, -29.15), (-108, -29.95), (-100.5, -31.0), (-92, -32.7), (-84, -34.3), (-77.6, -34.85), (-75.7, -33.5), (-74.4, -29), (-73.4, -23.4)]
# prop anchors for the 5060 team, on the alley and lane walls
a3.anchor("ac_outdoor", F(a3, "front"), 2.4, .1)
a2.anchor("ac_outdoor", F(a2, "back"), 2.4, .1)
a11.anchor("gas_meter", F(a11, "back"), 1.2, 1.1)
a1.anchor("ac_outdoor", F(a1, "back"), 4.2, .1)
a1.anchor("ac_outdoor", F(a1, "back"), 9.1, .1)
a12.anchor("ac_outdoor", F(a12, "back"), 1.8, .1)
a14.anchor("ac_outdoor", F(a14, "back"), 1.2, .1)
a5.anchor("ac_outdoor", F(a5, "left"), 3.0, .1)
a2.anchor("planter", F(a2, "front"), 2.9, .1)
a11.anchor("planter", F(a11, "front"), 4.2, .1)
a9.anchor("bicycle", F(a9, "front"), 2.5, .0)
a4.anchor("vending_or_bin", F(a4, "front"), 3.0, .0)

for b in S.values():
    objs.append(flush(b.build(), mats, coll))

# ---- ground ----
gm = M("A_ground")
ROADS = [
    [(-60.3, -20.6), (-86.4, -18.1), (-94.2, -17.6), (-106.6, -17.3), (-124, -17.3), (-124, -19.7), (-106.7, -19.7), (-94.3, -20.0), (-86.6, -20.5), (-61.1, -23.0)],
    [(-55.5, -29.2), (-60.2, -24.5), (-63.9, -34.0), (-66.5, -39.7), (-67.5, -41.6), (-71.4, -49.1), (-72.5, -51.3), (-67.0, -54.1), (-65.8, -51.9), (-60.1, -39.3)],
    [(-71.4, -49.1), (-80.0, -45.7), (-84.0, -44.5), (-90.8, -43.4), (-102.7, -41.4), (-108.4, -40.9), (-112.3, -40.8), (-118.7, -40.3), (-124, -40.0), (-124, -44.0), (-119.1, -44.3), (-110.8, -43.9), (-100.8, -44.7), (-91.1, -45.8), (-84.5, -46.9), (-80.8, -48.0), (-72.5, -51.3)],
    [(-52.6, -28.1), (-56.8, -18.7), (-60.3, -20.6), (-61.1, -23.0), (-60.2, -24.5), (-55.5, -29.2)],
]
EDGE_S = [(-119.1, -19.75), (-106.7, -19.75), (-94.3, -20.05), (-86.6, -20.55), (-61.1, -23.05)]
EDGE_D = [(-60.2, -24.5), (-63.9, -34.0), (-66.5, -39.7), (-67.5, -41.6), (-71.4, -49.1)]
EDGE_R = [(-71.4, -49.1), (-80.0, -45.7), (-84.0, -44.5), (-90.8, -43.4), (-102.7, -41.4), (-108.4, -40.9), (-112.3, -40.8), (-119.0, -40.3)]

E0, E1, N0, N1 = -124.0, -54.0, -55.0, -15.5
cell = .3
nx = int((E1 - E0) / cell); ny = int((N1 - N0) / cell)
inside = [(b.c, b.ax, b.ay, b.a - .35, b.b - .35) for b in S.values()]
def classify(x, y):
    for c, ax, ay, ha, hb in inside:
        d = V((x, y, 0)) - c
        if abs(d.dot(ax)) < ha and abs(d.dot(ay)) < hb: return 2
    for r in ROADS:
        if pip((x, y), r): return 1
    return 0
cls = [[classify(E0 + (i + .5) * cell, N0 + (j + .5) * cell) for j in range(ny)] for i in range(nx)]
def gz(x, y, road):
    z = G(x, y) + (-.05 if road else .012)
    z += .008 * nz((x, y, 0), .6) + .004 * nz((x, y, 0), 2.1) + (.012 * nz((x, y, 7), .25) if road else 0)
    return z
def gcol(x, y, base, amt=1.0):
    k = 1 + amt * (.16 * nz((x, y, 3), .22) + .1 * nz((x, y, 9), .9) + .05 * nz((x, y, 1), 3.3))
    return tint(base, max(.4, k))
for road, mat, sc, base in ((1, "asphalt", 3.4, (.82, .82, .84)), (0, "lot", 2.4, (.72, .71, .68))):
    PP = [[V((E0 + i * cell, N0 + j * cell, gz(E0 + i * cell, N0 + j * cell, road))) for j in range(ny + 1)] for i in range(nx + 1)]
    UV = [[(p.x / sc, p.y / sc) for p in r] for r in PP]
    CC = [[gcol(p.x, p.y, base) for p in r] for r in PP]
    gm.grid(mat, PP, UV, CC, smooth=True, skip=lambda i, j, r=road: cls[i][j] != r)

gf = Frame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
RG = random.Random(77)
def on_ground(cx, cy, w, h, cell_, rot=0, lift=.0, road=True):
    u = V((cos(rot), sin(rot), 0)); v = V((-sin(rot), cos(rot), 0))
    # conform decal to the road with a small grid
    nu = 8; nv = max(2, int(8 * h / w)); P = []; UV = []
    cu0 = (cell_ % 4) / 4; cv1 = 1 - (cell_ // 4) / 4
    for i in range(nu + 1):
        r = []; q = []
        for j in range(nv + 1):
            a = i / nu; b = j / nv
            p = V((cx, cy, 0)) + u * (w * (a - .5)) + v * (h * (b - .5))
            r.append(V((p.x, p.y, gz(p.x, p.y, road) + .004 + lift)))
            q.append((cu0 + a / 4, cv1 - .25 + b / 4))
        P.append(r); UV.append(q)
    gm.grid("decal", P, UV, [[(1, 1, 1)] * (nv + 1) for _ in range(nu + 1)], smooth=True)
# repairs and tar seams following real traffic wear
for pos, size, rot in (((-103, -18.6), (5.5, 1.3), 0), ((-88, -19.2), (3.0, 1.1), .06), ((-72, -21.1), (6.0, 1.2), .1), ((-112, -42.3), (6.5, 1.5), .03), ((-92, -44.6), (4.2, 1.3), .15), ((-68, -44.6), (1.4, 3.2), 1.1)):
    on_ground(pos[0], pos[1], size[0], size[1], 12, rot)
    on_ground(pos[0] + .2, pos[1] + size[1] * .5, size[0] * 1.02, .22, 13, rot, .001)
    on_ground(pos[0] + .2, pos[1] - size[1] * .5, size[0] * 1.02, .22, 13, rot, .001)
for k in range(46):
    x = RG.uniform(-122, -58); y = RG.uniform(-52, -16)
    cl = classify(x, y)
    if cl == 2: continue
    s_ = RG.uniform(.8, 3.2)
    on_ground(x, y, s_, s_ * RG.uniform(.5, 1), RG.choice((14, 6, 7)), RG.random() * 3, road=cl == 1)
# lane edge lines
road_paint(gm, [(p[0], p[1] + .42) for p in EDGE_S], G)
road_paint(gm, [(p[0] + .1, p[1] - .38) for p in EDGE_R], G)
ribbon_lids(gm, EDGE_S, G, RG)
ribbon_lids(gm, [(-124, -17.3), (-106.6, -17.3), (-94.2, -17.6), (-86.4, -18.1), (-60.3, -20.6)], G, RG, width=.5)
ribbon_lids(gm, [(-124, -44.0), (-119.1, -44.3), (-110.8, -43.9), (-100.8, -44.7), (-91.1, -45.8), (-84.5, -46.9), (-80.8, -48.0), (-72.5, -51.3)], G, RG, width=.5)
ribbon_lids(gm, [(-55.5, -29.2), (-60.1, -39.3), (-65.8, -51.9), (-67.0, -54.1)], G, RG, width=.5)
ribbon_lids(gm, [(-119.0, -40.3), (-124, -40.0)], G, RG, width=.5)
ribbon_lids(gm, EDGE_D, G, RG)
ribbon_lids(gm, EDGE_R, G, RG)
ribbon_lids(gm, alley, G, RG, width=.3, grate_every=6, tc=(.5, .5, .48))
# boundary walls where lots open to the alley and roads
wm = M("A_walls")
block_wall(wm, [(-101.0, -22.1), (-100.8, -29.0)], G, RG)
block_wall(wm, [(-91.6, -30.4), (-96.2, -33.5)], G, RG, h=1.0)
block_wall(wm, [(-110.1, -39.7), (-110.3, -40.6), (-105.7, -40.2)], G, RG, h=.9)
block_wall(wm, [(-96.4, -41.0), (-101.3, -40.8)], G, RG)
block_wall(wm, [(-85.8, -43.9), (-85.7, -43.0)], G, RG, h=1.4)
block_wall(wm, [(-82.4, -33.5), (-78.0, -35.6)], G, RG, h=1.5)
block_wall(wm, [(-74.6, -23.9), (-72.4, -25.3)], G, RG, h=1.5, tc=(.6, .6, .56))
objs.append(flush(gm, mats, coll)); objs.append(flush(wm, mats, coll))

# ---- preview-only context: LOD0 neighbours and an extended plane ----
cm = M("context_mass")
cp = pbr("ctx", solid=(.2, .19, .18), rough=.8); mats["ctx"] = cp
own = [b.c for b in S.values()]
for b in DATA["buildings"]:
    fp = b["lod"].get("lod0", [[]])[0]
    if len(fp) < 4: continue
    cx = sum(p[0] for p in fp) / len(fp); cy = sum(p[1] for p in fp) / len(fp)
    if any(abs(cx - c.x) < 4 and abs(cy - c.y) < 4 for c in own): continue
    if -119 < cx < -60 and -44 < cy < -21: continue
    h = float(b["attrs"].get("measuredHeight", 7)); z = G(cx, cy)
    n = len(fp) - 1
    for i in range(n):
        p, q = fp[i], fp[i + 1]
        cm.poly("ctx", [(p[0], p[1], z - 1), (q[0], q[1], z - 1), (q[0], q[1], z + h), (p[0], p[1], z + h)])
    cm.poly("ctx", [(p[0], p[1], z + h) for p in fp[:-1]])
cm.poly("ctx", [(-400, -400, -.2), (400, -400, -.2), (400, 400, -.2), (-400, 400, -.2)], None, (.28, .28, .28))
ctxob = flush(cm, mats, ctx)

# ---- stats ----
tot = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
tm = {}
for o in objs:
    names = [s.name for s in o.data.materials]
    for p in o.data.polygons:
        n = names[p.material_index]; tm[n] = tm.get(n, 0) + len(p.vertices) - 2
print("TRIS", tot, sorted(tm.items(), key=lambda kv: -kv[1])[:14], "objs", len(objs), "build_s", round(time.time() - t0), flush=True)

anchors = [x for b in S.values() for x in b.anchors]
OUTD = ROOT + r"\output\blocks"; os.makedirs(OUTD, exist_ok=True)
EXP = ROOT + r"\export\blocks\block_A"; os.makedirs(EXP, exist_ok=True)
json.dump(dict(block="A", tris=tot, tris_by_material=tm, anchors=anchors, alley_centerline_enu=alley, edges_enu=dict(lane_south=EDGE_S, diagonal_west=EDGE_D, south_road_north=EDGE_R),
               buildings={k: dict(center=[round(b.c.x, 2), round(b.c.y, 2)], size=[round(b.a * 2, 2), round(b.b * 2, 2)], H=b.H, storeys=b.st, base_z=round(b.base, 3), roof=b.roofkind) for k, b in S.items()}),
          open(EXP + r"\block_A_meta.json", "w"), indent=1, ensure_ascii=False)

CAMS = {
    "lane": ((-101, -18.6, 1.75), (-74, -22, 3.2), 26), "alley": ((-96.5, -32.0, 1.75), (-80, -34.6, 2.4), 24), "south": ((-120, -42.4, 1.75), (-98, -36.5, 4.6), 26),
    "diag": ((-59.6, -41.0, 1.75), (-71, -30.6, 4.2), 26), "roof": ((-52, -66, 22), (-90, -32, 5), 32), "close": ((-93.8, -19.4, 1.75), (-97.8, -21.2, 1.6), 30),
}
if a.export:
    export_glb(coll, EXP + r"\block_A.glb")
    print("GLB", os.path.getsize(EXP + r"\block_A.glb") / 1e6, flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=ROOT + r"\blend\block_A.blend", compress=True)
if a.render:
    setup_render(a.res, a.spp)
    lighting()
    for n in a.cams.split(","):
        pos, look, lens = CAMS[n]
        cam = add_cam(n, pos, look, lens); bpy.context.scene.camera = cam
        bpy.context.scene.render.filepath = OUTD + f"\\A_{a.tag}_{n}.jpg"
        t1 = time.time(); bpy.ops.render.render(write_still=True)
        print("RENDER", n, round(time.time() - t1), flush=True)
print("ALLDONE", round(time.time() - t0), flush=True)
sys.stdout.flush()
os._exit(0)
