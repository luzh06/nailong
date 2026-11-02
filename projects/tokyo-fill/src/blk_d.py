# Block D: south-east corner. PLATEAU misses the two real condos here; outlines come from OSM (コージーコート谷中 6F, ウィルローズ谷中銀座 7F),
# built only where qs_h1's frontage leaves room. Roads are PLATEAU's diagonal and the crossing's south leg.
import sys
sys.path.insert(0, r"D:\project\cijian\work\src")
from blk_fill import *

a = args("diag,fork,leg,roof")
K = Block("D", 20261104)
mk = K.mk
def F(b, role): return {"front": b.fi, "right": (b.fi + 1) % 4, "back": (b.fi + 2) % 4, "left": (b.fi + 3) % 4}[role]


k1 = mk("D01_condo_six_south", rect(-55.6, -18.4, -45.6, -12.0), 18.6, 6, clad=["darkface", "whitetile", "whitetile", "whitetile", "whitetile", "whitetile"],
        tcs={"darkface": (1.05, 1.0, .92), "whitetile": (.94, .92, .88)}, roof="flat", front=(0, -1), framecol=(.6, .6, .58), capcol=(.62, .62, .6), hoodp=0, weather=.8)
k2 = mk("D02_condo_six_core", rect(-55.6, -11.9, -53.35, -.95), 18.6, 6, clad=["whitetile"], tc=(.9, .88, .84), roof="flat", front=(-1, 0), framecol=(.6, .6, .58),
        capcol=(.62, .62, .6), hoodp=0, weather=.8, noplinth=False)
w1 = mk("D03_condo_seven_wing", rect(-41.0, -22.6, -32.6, -9.2), 21.4, 7, clad=["darkface", "facetile", "facetile", "facetile", "facetile", "facetile", "facetile"],
        tcs={"darkface": (.9, .86, .8), "facetile": (.78, .7, .6)}, roof="flat", front=(0, -1), framecol=(.4, .4, .4), capcol=(.5, .5, .48), tank=False, hoodp=0, weather=.7)
w2 = mk("D04_condo_seven_link", rect(-45.2, -21.6, -41.2, -15.2), 6.4, 2, clad=["darkface", "facetile"], tcs={"darkface": (.9, .86, .8), "facetile": (.78, .7, .6)}, roof="flat",
        front=(0, -1), framecol=(.4, .4, .4), capcol=(.5, .5, .48), hoodp=0)

# condos: sliding doors to deep balconies on the sunny side, small windows on the gallery side
for b, side in ((k1, "front"), (w1, "front")):
    f = F(b, side); L = b.len[f]
    for fl in range(1, b.st):
        for x in frange(.5, L - 1.9, 3.0): b.add_win(f, x, fl * b.fh + .1, 1.8, 2.0, "curtain" if (x + fl) % 2 else "sash")
k1.add_door(F(k1, "front"), 1.0, 1.6, 2.2, "slide"); k1.add_garage(F(k1, "front"), 3.4, 5.6, 2.4, kind="open")
k1.fenestrate(skip=(F(k1, "front"),), sparse={"back": .5, "left": .4, "right": .5}, widths={"left": [.9, .6]})
f = F(k2, "front")
for fl in range(1, 6): k2.add_win(f, 1.0, fl * k2.fh + .9, .9, .9, "frost"); k2.add_win(f, 4.5, fl * k2.fh + .9, .9, .9, "frost"); k2.add_win(f, 8.2, fl * k2.fh + .9, .9, .9, "guard")
k2.add_door(f, 3.6, 1.8, 2.3, "slide")
f = F(w1, "front"); L = w1.len[f]; w1.add_door(f, 1.0, 1.8, 2.3, "slide"); w1.add_garage(f, 4.0, 5.0, 2.4, kind="open")
f = F(w1, "right")       # west face over the link block: living-room windows on every floor
for fl in range(1, w1.st):
    for x in frange(.8, w1.len[f] - 1.8, 3.2): w1.add_win(f, x, fl * w1.fh + .8, 1.65, 1.2, "sash" if (fl + int(x)) % 3 else "curtain")
w1.fenestrate(skip=(F(w1, "front"), f), widths={"left": [.9, .6], "back": [.9]}, sparse={"left": .3, "back": .4})
f = F(w2, "front"); shopfront(w2, f, .3, w2.len[f] - .6, style="shutter", awning=None)
w2.fenestrate(skip=(f,), sparse={"left": .6, "right": .6, "back": .6})


def attach():
    for b, side, x0, x1 in ((k1, "front", .2, None), (w1, "front", .2, None)):
        f = F(b, side); L = b.len[f]
        for fl in range(1, b.st): b.balcony(f, x0, L - .2, fl, depth=1.2, style="panel" if b is k1 else "conc")
    # open stair core on the crossing side of the slender wing
    f = F(k2, "front"); fr = k2.frames[f]
    for fl in range(1, 6):
        y = fl * k2.fh
        box(k2.m, "concrete", fr, .0, k2.len[f], y - .2, y + .02, 0, .9, ch=.01, col=(.82, .8, .76), sc=2.2)
        box(k2.m, "alu", fr, .0, k2.len[f], y + .95, y + 1.0, .86, .92, ch=.004, col=(.6, .6, .58))
        for x in frange(.1, k2.len[f], .12): box(k2.m, "alu", fr, x, x + .018, y + .02, y + .95, .87, .9, col=(.62, .62, .6))
    for b in (k1, w1):
        for k in range(b.st - 1):
            f = F(b, "front"); fr = b.frames[f]
            for x in frange(2.6, b.len[f] - 1.0, 3.0):      # balcony partition boards with the emergency hatch print
                y = (k + 1) * b.fh
                box(b.m, "frost", fr, x, x + .03, y + .02, y + 1.95, .05, 1.15, col=(.82, .84, .82))


attach()
for b, side, x, kind in ((k1, "front", 7.2, "bicycle"), (k1, "front", 8.4, "bicycle"), (w1, "front", 9.6, "vending_or_bin"), (k2, "front", 7.0, "planter"), (w2, "front", .2, "vending_or_bin")):
    b.anchor(kind, F(b, side), x, .0)
if K.check_overlaps() and not os.environ.get("ALLOW_OVERLAP"):
    print("ABORT overlaps", flush=True); sys.stdout.flush(); os._exit(3)

# crossing south leg continues to the fork; small paved plaza with bench where OSM records one (E-54.5 N-38.2)
PARK = [(-52.0, -29.2), (-47.0, -30.6), (-33.0, -35.5), (-33.0, -40.0), (-52.6, -40.0)]          # coin parking south of the diagonal (aerial: uniform grey, stall marks)
K.extra_roads = [[(-60.0, -18.9), (-55.7, -18.9), (-55.7, -.7), (-60.0, -.7)], PARK]
K.pave = [[(-55.4, -29.4), (-52.1, -29.1), (-52.7, -40.0), (-58.6, -40.0)]]                   # fork plaza between block A's road and the lot (bench in OSM)
K.gravel = [[(-47.0, -12.0), (-45.6, -12.0), (-45.6, -9.0), (-47.0, -9.0)]]
K.default_cls = 1          # everything open here is road or parking asphalt; avoids lot slivers along PLATEAU's road edge
gm = K.ground(-55.7, -32.5, -40.0, -.8)
K.patch(-48, -24.5, 6.0, 1.4, -.29); K.patch(-40, -27.0, 4.0, 1.2, -.29); K.patch(-56, -30, 1.6, 4.5, .4)
K.scatter_stains(40, -55, -33, -39, -9)
ribbon_lids(gm, [(-45.4, -22.6), (-32.6, -26.4)], G, K.R, width=.4); ribbon_lids(gm, [(-55.4, -18.8), (-45.8, -22.1)], G, K.R, width=.4)
road_paint(gm, [(-51.0, -24.0), (-36.0, -28.6)], G, width=.15); road_paint(gm, [(-55.2, -21.4), (-55.2, -19.4)], G, width=.3)
wm = M("D_walls")
block_wall(wm, [(-47.0, -12.0), (-45.6, -12.0)], G, K.R, h=1.2)
# parking: kerb along the road, stall lines and wheel stops, pay station slot
pd = V((14.0, -4.9, 0)).normalized(); pn = V((-pd.y, pd.x, 0))        # along the lot's north kerb, and into the road
for k in range(9):
    o = V((-49.6, -30.3, 0)) + pd * (k * 2.5)
    a0 = o - pn * .4; a1 = o - pn * 5.4
    road_paint(gm, [(a0.x, a0.y), (a1.x, a1.y)], G, width=.12, tc=(.86, .86, .82))
    if k < 8:
        c = o + pd * 1.25 - pn * 4.7; sf = Frame((c.x, c.y, G(c.x, c.y)), pd, (0, 0, 1), -pn)
        box(wm, "concrete", sf, -.75, .75, -.02, .12, -.08, .08, ch=.02, col=(.74, .72, .66), sc=2.2)
        box(wm, "paint", sf, -.5, -.35, .12, .121, -.081, .081, col=(.9, .8, .2)); box(wm, "paint", sf, .35, .5, .12, .121, -.081, .081, col=(.9, .8, .2))
ribbon_lids(gm, [(-51.8, -29.4), (-47.0, -30.85), (-33.0, -35.75)], G, K.R, width=.3, tc=(.66, .66, .62))
K.S["D01_condo_six_south"].anchors.append(dict(type="parking_pay_station", building="lot", center_enu=[-34.5, -36.2, round(G(-34.5, -36.2), 3)], outward_enu=[.33, .94]))
# bench and two bollards on the plaza
bf = Frame((-52.2, -37.0, G(-52.2, -37.0)), (cos(-.6), sin(-.6), 0), (0, 0, 1), (-sin(-.6), cos(-.6), 0))
for x in (.1, 1.5): box(wm, "steel", bf, x, x + .06, 0, .42, -.2, .2, col=(.25, .25, .25))
for k in range(4): box(wm, "plank", bf, 0, 1.7, .42, .46, -.2 + k * .1, -.12 + k * .1, ch=.006, col=(.55, .42, .3), sc=1.9)
for p_ in ((-54.6, -35.2), (-49.0, -35.5)):
    tube(wm, "steel", [(p_[0], p_[1], G(*p_)), (p_[0], p_[1], G(*p_) + .8)], .05, 10, (.62, .6, .55))
K.flush_all(extra=(gm, wm))

CAMS = {"diag": ((-34.5, -30.0, 1.65), (-55, -21, 5.0), 24), "fork": ((-58.5, -30.5, 1.65), (-40, -18, 8.0), 24), "leg": ((-57.8, -2.2, 1.65), (-57.5, -30, 3.0), 26),
        "roof": ((-20, -55, 30), (-48, -14, 6), 30), "_own": (-55.7, -32.5, -40, -.8)}
K.finish(a, CAMS)
