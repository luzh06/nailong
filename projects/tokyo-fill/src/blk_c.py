# Block C: north-east lots between the qs_h1 frontage and the lane at N~27, east of block B. PLATEAU footprints, trimmed to the frontage backs.
import sys
sys.path.insert(0, r"D:\project\cijian\work\src")
from blk_fill import *

a = args("lane,yard,stairs,road,roof")
K = Block("C", 20261103)
mk = K.mk
def F(b, role): return {"front": b.fi, "right": (b.fi + 1) % 4, "back": (b.fi + 2) % 4, "left": (b.fi + 3) % 4}[role]


# ---- south of the lane ----
c1 = mk("C01_five_storey_rc", rect(-41.9, 13.0, -32.1, 22.2), 16.8, 5, clad=["darkface", "whitetile", "whitetile", "whitetile", "whitetile"],
        tcs={"darkface": (1.15, 1.1, 1.0), "whitetile": (.9, .88, .82)}, roof="flat", front=(0, -1), framecol=(.5, .5, .48), capcol=(.5, .5, .48), tank=True, hoodp=0, weather=1.3)
c2 = mk("C02_craft_workshop", rect(-52.6, 13.2, -47.1, 24.6), 8.4, 2, clad=["blackplank", "plaster"], tcs={"blackplank": (.85, .85, .85), "plaster": (.92, .9, .84)}, roof="gable",
        pitch=.5, over=.55, rax=1, front=(-1, 0), moss=True, fasciacol=(.22, .17, .13), soffitcol=(.4, .3, .22), framecol=(.3, .22, .15))
c2b = mk("C02b_workshop_annex", rect(-46.7, 18.4, -43.9, 24.4), 4.2, 1, clad=["tin"], tc=(.66, .7, .68), roof="mono", pitch=.14, over=.25, gover=.1, rax=0, roofmat="galva",
         roofcol=(.44, .4, .36), front=(1, 0), rust=True, gutter=False, framecol=(.5, .48, .44))
c3 = mk("C03_pencil_building", rect(-46.9, 13.0, -42.3, 17.9), 13.5, 4, clad=["facetile"], tc=(.66, .56, .46), roof="flat", front=(0, 1), framecol=(.36, .34, .32), capcol=(.42, .4, .38), hoodp=0)
# ---- north of the lane ----
c4 = mk("C04_lane_house", rect(-52.2, 28.95, -41.4, 33.5), 6.1, 2, clad=["siding"], tc=(.84, .82, .76), roof="gable", pitch=.4, over=.4, gover=.25, rax=0, front=(0, -1),
        roofmat="slate", slatetc=(.48, .46, .48), metalfascia=True, fasciacol=(.3, .3, .3), framecol=(.36, .34, .32))
c5 = mk("C05_corner_kawara", rect(-41.2, 28.9, -36.6, 35.8), 7.0, 2, clad=["mortar"], tc=(.88, .8, .66), roof="hip", pitch=.46, over=.5, front=(0, -1), moss=True,
        fasciacol=(.3, .24, .18), soffitcol=(.5, .4, .3), framecol=(.45, .4, .34))
c6 = mk("C06_long_tin_house", rect(-52.4, 33.8, -41.6, 40.0), 7.0, 2, clad=["tin", "siding2"], tcs={"tin": (.7, .76, .8), "siding2": (.62, .58, .52)}, roof="gable", pitch=.36,
        over=.35, gover=.2, rax=0, roofmat="galva", roofcol=(.36, .38, .42), front=(-1, 0), rust=True, framecol=(.5, .48, .44))
c6b = mk("C06b_back_house", rect(-41.1, 36.1, -37.6, 40.1), 6.5, 2, clad=["plaster"], tc=(.86, .86, .82), roof="gable", pitch=.42, over=.35, rax=1, front=(0, 1),
         fasciacol=(.3, .26, .2), framecol=(.42, .4, .36))
c7 = mk("C07_wood_row", rect(-53.0, 40.3, -40.4, 44.6), 7.5, 2, clad=["cedar", "plank"], tcs={"cedar": (.92, .8, .64), "plank": (.62, .54, .44)}, roof="gable", pitch=.44, over=.5,
        rax=0, front=(-1, 0), moss=True, palette=((.075, .08, .09), (.06, .062, .07), (.1, .1, .11)), fasciacol=(.26, .2, .16), framecol=(.34, .26, .2))
c8 = mk("C08_three_storey_mortar", rect(-54.4, 44.9, -41.2, 49.0), 9.3, 3, clad=["mortar", "mortar", "siding2"], tcs={"mortar": (.78, .8, .76), "siding2": (.5, .52, .54)},
        roof="mono", pitch=.1, over=.3, gover=.12, rax=0, roofmat="galva", roofcol=(.38, .4, .42), front=(0, 1), metalfascia=True, fasciacol=(.28, .28, .28), framecol=(.32, .32, .32))

# ---- openings ----
f = F(c1, "front"); L = c1.len[f]
for fl in range(1, 5):
    for x in frange(.6, L - 1.6, 2.4):
        c1.add_win(f, x, fl * c1.fh + .25, 1.65, 1.95, "sash") if fl < 4 or x > 2 else c1.add_win(f, x, fl * c1.fh + .85, 1.65, 1.1, "curtain")
r = F(c1, "right"); shopfront(c1, r, .5, 4.0, style="lattice", sign=None, noren=2, awning=None)       # restaurant at the SE corner, faces the stair foot
c1.add_win(r, 5.2, .9, 1.65, 1.1, "guard")
for fl in range(1, 5):
    for x in frange(.8, c1.len[r] - 1.4, 2.6): c1.add_win(r, x, fl * c1.fh + .85, 1.2, 1.15, "sash" if fl % 2 else "frost")
c1.fenestrate(skip=(f, r), widths={"back": [.9, .75], "left": [.75, .6]}, sparse={"back": .2, "left": .35})
f = F(c2, "front"); L = c2.len[f]; shopfront(c2, f, .6, 4.2, style="lattice", sign=4, vsign=4, noren=1, awning=None)
c2.add_door(f, 5.6, 1.7, 2.02, "slide"); c2.add_win(f, 8.2, 1.0, 1.75, 1.05, "lattice")
for x in (1.0, 4.0, 7.2): c2.add_win(f, x, c2.fh + .8, 1.75, 1.1, "lattice" if x < 6 else "sash", amado=x > 6)
c2.fenestrate(skip=(f,))
f = F(c2b, "front"); c2b.add_garage(f, .6, 3.0, 2.5, kind="open"); c2b.fenestrate(skip=(f,), sparse={"left": .7, "right": .7, "back": .8})
f = F(c3, "front"); c3.add_door(f, .5, .9, 2.1, "steel", tc=(.3, .3, .32))
for fl in range(1, 4): c3.add_win(f, .6, fl * c3.fh + .5, 1.65, 1.6, "sash")
c3.fenestrate(skip=(f,), sparse={"left": .5, "right": .6, "back": .2}, widths={"back": [1.65, 1.2], "left": [.6, .9]})
for b in (c4, c5, c6, c6b, c7, c8):
    f = F(b, "front"); L = b.len[f]
    b.add_door(f, .8, .9 if b is not c7 else 1.7, 2.03, "steel" if b is not c7 else "slide", tc=b.rng.choice(((.32, .27, .22), (.44, .42, .38), (.26, .3, .34))))
    if L > 7: b.add_garage(f, L - 3.3, 2.6, 2.2)
    b.fenestrate(skip=())


def attach():
    f = F(c1, "front"); L = c1.len[f]
    for fl in range(1, 5): c1.balcony(f, .3, L - .3, fl, depth=1.05, style="conc" if fl % 2 else "panel")
    f = F(c1, "right")
    for fl in range(1, 5): c1.balcony(f, .5, 3.6, fl, depth=.6, style="bars")
    f = F(c1, "right"); c1.lean(f, .2, 4.8, 2.75, depth=.9, drop=.3)
    f = F(c2, "front"); c2.lean(f, .2, c2.len[f] - .2, c2.fh + .3, depth=1.0, drop=.42)
    f = F(c3, "front")
    for fl in range(1, 4): c3.balcony(f, .3, c3.len[f] - .3, fl, depth=.55, style="bars")
    f = F(c7, "front"); c7.lean(f, .2, c7.len[f] - .2, c7.fh + .3, depth=.9, drop=.38)
    f = F(c4, "front"); c4.balcony(f, .5, 4.2, 1, depth=.7, style="panel")
    f = F(c8, "front"); c8.balcony(f, .4, c8.len[f] - .4, 2, depth=.8, style="bars")
    for b in (c2, c5, c7): b.antenna(b.Q(0, 0, b.e + b.rise - .02), 2.1)


attach()
for b, side, x, kind in ((c1, "back", 2.0, "ac_outdoor"), (c1, "back", 5.0, "ac_outdoor"), (c1, "left", 3.0, "gas_meter"), (c4, "front", 6.5, "bicycle"),
                         (c5, "front", 1.5, "planter"), (c2, "front", 9.6, "planter"), (c6, "right", 2.0, "ac_outdoor"), (c3, "left", 1.5, "ac_outdoor")):
    b.anchor(kind, F(b, side), x, .1 if kind != "gas_meter" else 1.1)
if K.check_overlaps() and not os.environ.get("ALLOW_OVERLAP"):
    print("ABORT overlaps", flush=True); sys.stdout.flush(); os._exit(3)

K.gravel = [[(-46.8, 18.0), (-42.1, 18.0), (-42.1, 25.4), (-46.8, 25.4)]]           # yard and parking behind the pencil building
K.pave = [[(-41.9, 22.4), (-32.6, 22.4), (-32.6, 25.4), (-41.9, 25.4)]]               # concrete apron behind the RC block
gm = K.ground(-50.0, -32.5, 12.9, 49.5)
K.patch(-44, 27.1, 5.0, 1.2, .01); K.patch(-37, 27.0, 2.2, 1.0, .02)
K.scatter_stains(30, -50, -33, 13, 49)
ribbon_lids(gm, [(-50.0, 25.85), (-33.8, 25.55)], G, K.R, width=.3, grate_every=6, tc=(.5, .5, .48))
ribbon_lids(gm, [(-50.0, 28.75), (-33.8, 28.4)], G, K.R, width=.3, grate_every=6, tc=(.5, .5, .48))
wm = M("C_walls")
block_wall(wm, [(-46.8, 25.3), (-42.1, 25.3)], G, K.R, h=1.0); block_wall(wm, [(-33.6, 25.4), (-33.6, 28.5)], G, K.R, h=1.8, tc=(.66, .66, .62))
block_wall(wm, [(-40.4, 41.0), (-36.0, 41.0), (-36.0, 36.0)], G, K.R, h=1.2)
block_wall(wm, [(-36.4, 29.0), (-33.0, 29.0), (-33.0, 47.0)], G, K.R, h=1.5, tc=(.7, .7, .66))
K.flush_all(extra=(gm, wm))

CAMS = {"lane": ((-52.0, 27.2, 1.65), (-34, 26.8, 3.2), 26), "yard": ((-43.0, 24.8, 1.65), (-37, 14, 6.0), 24), "stairs": ((-12, 1.8, 6.2), (-45, 18, 6), 30),
        "road": ((-55.4, 30.0, 1.65), (-53, 14.5, 3.5), 26), "roof": ((-20, 60, 24), (-45, 25, 4), 30), "_own": (-53.5, -32.5, 12.9, 49.5)}
K.finish(a, CAMS)
