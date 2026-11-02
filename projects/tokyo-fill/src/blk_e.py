# Block E: main-street west extension (E<-94.5), the lot row between the street and block A's lane, and the real crossing at E~-58.
# Lots follow PLATEAU 53394671 footprints, trimmed to the kerb and to existing geometry. Shop names are fictional.
import sys
sys.path.insert(0, r"D:\project\cijian\work\src")
from blk_fill import *

a = args("west,east,lane,temple,junction,path,roof")
K = Block("E", 20261102)
mk = K.mk


def F(b, role): return {"front": b.fi, "right": (b.fi + 1) % 4, "back": (b.fi + 2) % 4, "left": (b.fi + 3) % 4}[role]
def kerb_n(E0, E1): return max(street_edges(e)[1] for e in (E0, (E0 + E1) / 2, E1)) + .05
def kerb_s(E0, E1): return min(street_edges(e)[0] for e in (E0, (E0 + E1) / 2, E1)) - .05


# ---- north frontage, facing the street (south) ----
n1 = mk("E_n1_zakka", rect(-124.0, kerb_n(-124, -120.3), -120.3, 15.8), 7.6, 2, clad=["plaster", "siding"], tcs={"plaster": (.9, .88, .82), "siding": (.62, .64, .62)},
        roof="gable", pitch=.42, over=.4, gover=.2, rax=1, front=(0, -1), roofmat="slate", slatetc=(.45, .44, .46), metalfascia=True, fasciacol=(.3, .3, .3), framecol=(.4, .4, .38), hoodp=.2)
n2 = mk("E_n2_greengrocer", rect(-120.1, kerb_n(-120.1, -114.1), -114.1, 12.6), 7.0, 2, clad=["damaged"], tc=(.9, .9, .84), roof="gable", pitch=.32, over=.35, gover=.2, rax=1, front=(0, -1),
        roofmat="galva", roofcol=(.34, .52, .4), framecol=(.5, .5, .46), moss=True, hoodp=.3)
n3 = mk("E_n3_senbei", rect(-113.9, kerb_n(-113.9, -110.6), -110.6, 12.6), 7.0, 2, clad=["blackplank", "plank"], tcs={"plank": (.6, .52, .42), "blackplank": (.8, .8, .8)}, roof="gable",
        pitch=.48, over=.45, gover=.25, rax=0, front=(0, -1), fasciacol=(.26, .2, .16), framecol=(.34, .26, .2), moss=True)
n4 = mk("E_n4_tea_machiya", rect(-110.4, kerb_n(-110.4, -100.4), -100.4, 12.6), 7.2, 2, clad=["plaster", "cedar"], tcs={"plaster": (.94, .92, .86), "cedar": (1.0, .86, .7)},
        roof="irimoya", pitch=.5, over=.65, rax=0, front=(0, -1), moss=True, fasciacol=(.24, .18, .13), soffitcol=(.42, .32, .24), framecol=(.32, .24, .17))
# ---- south frontage, facing the street (north) ----
s1 = mk("E_s1_books_rc", rect(-124.0, -5.8, -117.4, kerb_s(-124, -117.4)), 9.4, 3, clad=["facetile", "plaster", "plaster"], tcs={"facetile": (.7, .6, .5), "plaster": (.86, .84, .8)},
        roof="flat", front=(0, 1), framecol=(.45, .44, .42), capcol=(.48, .48, .46), tank=True, hoodp=0)
s2 = mk("E_s2_coffee", rect(-116.6, -5.3, -110.4, kerb_s(-116.6, -110.4)), 6.6, 2, clad=["siding2", "rough3"], tcs={"siding2": (.46, .52, .5), "rough3": (.92, .86, .76)},
        roof="mono", pitch=.12, over=.3, gover=.12, rax=0, roofmat="galva", roofcol=(.4, .42, .44), front=(0, 1), metalfascia=True, fasciacol=(.28, .28, .28), framecol=(.3, .3, .3), hoodp=.1)
s3 = mk("E_s3_deli_double", rect(-110.1, -7.8, -100.6, kerb_s(-110.1, -100.6)), 8.1, 2, clad=["mortar"], tc=(.9, .84, .72), roof="gable", pitch=.42, over=.5, rax=0, front=(0, 1),
        moss=True, fasciacol=(.3, .24, .18), soffitcol=(.5, .4, .3), framecol=(.45, .4, .34))
s4 = mk("E_s4_bakery_narrow", rect(-99.8, -8.6, -95.3, kerb_s(-99.8, -95.3)), 7.5, 2, clad=["tin", "siding"], tcs={"tin": (.82, .74, .62), "siding": (.86, .84, .8)}, roof="mono", pitch=.14,
        over=.3, gover=.1, rax=1, roofmat="galva", roofcol=(.5, .46, .4), front=(0, 1), rust=True, framecol=(.5, .48, .44))
# ---- rear row, facing block A's lane (south) ----
r1 = mk("E_r1_long_house", rect(-124.0, -11.6, -110.6, -6.1), 7.6, 2, clad=["cracked"], tc=(.95, .92, .86), roof="hip", pitch=.45, over=.55, front=(0, -1), moss=True,
        fasciacol=(.3, .25, .2), soffitcol=(.48, .4, .3), framecol=(.42, .4, .36), weather=1.2)
g1 = mk("E_g1_tile_house", rect(-118.3, -17.2, -110.6, -11.9), 7.5, 2, clad=["facetile", "siding"], tcs={"facetile": (.66, .6, .54), "siding": (.78, .76, .7)}, roof="gable", pitch=.36,
        over=.3, gover=.18, rax=0, roofmat="slate", slatetc=(.5, .48, .5), front=(0, -1), metalfascia=True, fasciacol=(.3, .28, .26), framecol=(.3, .28, .26))
g2 = mk("E_g2_corner_mortar", rect(-109.8, -17.2, -100.2, -8.1), 7.4, 2, clad=["plaster5"], tc=(.96, .88, .74), roof="hip", pitch=.46, over=.5, front=(0, -1), moss=True,
        fasciacol=(.32, .26, .2), framecol=(.5, .46, .4), hoodp=.4)
g3 = mk("E_g3_mokuchin_apartment", rect(-99.7, -15.9, -87.3, -11.6), 7.8, 2, clad=["siding2"], tc=(.78, .74, .66), roof="gable", pitch=.3, over=.4, gover=.25, rax=0,
        roofmat="slate", slatetc=(.4, .38, .4), front=(0, -1), metalfascia=True, fasciacol=(.36, .34, .3), framecol=(.6, .58, .54), hoodp=0)
g4 = mk("E_g4_shed", rect(-87.1, -13.4, -83.8, -9.2), 5.2, 1, clad=["rustytin"], tc=(.6, .62, .6), roof="mono", pitch=.16, over=.25, gover=.1, rax=1, roofmat="galva",
        roofcol=(.4, .36, .32), front=(0, -1), rust=True, gutter=False, framecol=(.5, .48, .44))
tp = mk("E_temple_hondo", rect(-83.4, -17.2, -69.7, -12.1), 8.2, 1, clad=["plaster"], tc=(.95, .93, .88), roof="irimoya", pitch=.62, over=1.1, rax=0, front=(0, -1),
        palette=((.13, .135, .14), (.1, .105, .11), (.16, .165, .17)), roofcol=(.12, .125, .13), fasciacol=(.2, .15, .1), soffitcol=(.36, .26, .17), framecol=(.3, .22, .14),
        sideclad={"front": "cedar"}, tcs={"cedar": (.9, .72, .52)}, weather=.6, hoodp=0)
g5 = mk("E_g5_rear_annex", rect(-68.8, -13.6, -64.4, -9.2), 6.4, 2, clad=["mortar"], tc=(.76, .78, .74), roof="flat", front=(0, -1), framecol=(.5, .5, .48), capcol=(.5, .5, .5), hoodp=.3)

# ---- openings ----
f = F(n1, "front"); L = n1.len[f]; shopfront(n1, f, .4, L - .8, sign=9, vsign=9, awning="tent", awncol=(.72, .66, .52))
n1.add_win(f, .6, n1.fh + .85, 1.65, 1.1, "sash"); n1.fenestrate(skip=(f,))
f = F(n2, "front"); L = n2.len[f]; shopfront(n2, f, .3, L - .6, style="open", sign=6, vsign=6, awning="tin", awncol=(.48, .6, .5))
n2.add_win(f, .8, n2.fh + .85, 1.65, 1.1, "sash", amado=True); n2.add_win(f, L - 2.2, n2.fh + .85, 1.2, 1.1, "curtain"); n2.fenestrate(skip=(f,))
f = F(n3, "front"); L = n3.len[f]; shopfront(n3, f, .25, L - .5, style="lattice", sign=10, noren=2, awning=None)
n3.add_win(f, .5, n3.fh + .8, L - 1.0, 1.05, "lattice"); n3.fenestrate(skip=(f,))
f = F(n4, "front"); L = n4.len[f]; shopfront(n4, f, .5, 5.2, style="lattice", sign=7, vsign=7, noren=1, awning=None); n4.add_door(f, 6.3, 1.7, 2.02, "slide")
n4.add_win(f, 8.3, 1.0, 1.2, 1.05, "lattice")
for x in (.9, 3.4, 6.2): n4.add_win(f, x, n4.fh + .75, 1.75, 1.05, "lattice" if x < 5 else "sash", amado=x > 5)
n4.fenestrate(skip=(f,), kinds={"back": ["sash", "frost"], "left": ["lattice", "frost"], "right": ["lattice", "frost"]})
f = F(s1, "front"); L = s1.len[f]; shopfront(s1, f, .4, L - .8, sign=2, vsign=2, awning="tent", awncol=(.3, .26, .22))
for fl in (1, 2):
    for x in frange(.7, L - 1.6, 2.2): s1.add_win(f, x, fl * s1.fh + .85, 1.65, 1.15, "sash" if fl == 1 else "curtain")
s1.fenestrate(skip=(f,), sparse={"left": .5, "right": .5, "back": .3})
f = F(s2, "front"); L = s2.len[f]; shopfront(s2, f, .35, L - .7, sign=3, vsign=3, awning="tent", awncol=(.2, .34, .26))
s2.add_win(f, .7, s2.fh + .4, 1.65, 1.75, "sash"); s2.fenestrate(skip=(f,))
f = F(s3, "front"); L = s3.len[f]; shopfront(s3, f, .35, L / 2 - .55, style="open", sign=1, vsign=1, awning="tent", awncol=(.16, .22, .4))
shopfront(s3, f, L / 2 + .2, L / 2 - .55, sign=0, noren=0, awning="tent", awncol=(.5, .3, .18))
for x in (.8, 3.2, L / 2 + .8, L - 2.4): s3.add_win(f, x, s3.fh + .8, 1.65, 1.1, "sash", amado=x > L / 2)
s3.fenestrate(skip=(f,))
f = F(s4, "front"); L = s4.len[f]; shopfront(s4, f, .3, L - .6, sign=8, vsign=8, awning="tin", awncol=(.72, .62, .48))
s4.add_win(f, .6, s4.fh + .85, 1.2, 1.1, "curtain"); s4.add_win(f, 2.4, s4.fh + .85, 1.2, 1.1, "sash", hood=True); s4.fenestrate(skip=(f,))
for b in (r1, g1, g2, g5):
    f = F(b, "front"); b.add_door(f, .8, .85, 2.03, "steel", tc=b.rng.choice(((.3, .26, .22), (.42, .4, .36), (.26, .3, .34)))); b.fenestrate(skip=())
f = F(g4, "front"); g4.add_garage(f, .4, 2.5, 2.4); g4.fenestrate(skip=(f,), sparse={"left": .7, "right": .7, "back": .7})
# mokuchin: four doors per floor on the lane side, gallery and steel stair added after build
f = F(g3, "front"); L = g3.len[f]
for fl in range(2):
    n_ = 3 if fl == 0 else 4; span = (L - 4.4) if fl == 0 else (L - 1.2)       # ground floor keeps clear of the stair at the east end
    for k in range(n_):
        x = .7 + k * span / n_
        g3.add_door(f, x, .8, 1.95, "steel", tc=(.62, .6, .55)) if fl == 0 else g3.holes[f].append((x, g3.fh + .18, x + .8, g3.fh + 2.1))
        if fl: g3.ops.append(("door", f, x, g3.fh + .18, .8, 1.92, "steel", {"tc": (.62, .6, .55)}))
        g3.add_win(f, x + 1.1, fl * g3.fh + 1.1, .75, .6, "frost")
g3.fenestrate(skip=(f,), widths={"back": [1.65, 1.2]}, kinds={"back": ["sash", "curtain", "sash"]}, sparse={"back": .1})
# temple: wide hinoki doors and lattice under deep eaves
f = F(tp, "front"); L = tp.len[f]
tp.add_door(f, L / 2 - 1.5, 3.0, 2.4, "slide")
for x in (1.0, L - 3.0): tp.add_win(f, x, .9, 2.0, 1.5, "lattice")
tp.fenestrate(skip=(f,), kinds={"left": ["lattice"], "right": ["lattice"], "back": ["frost", "lattice"]}, widths={"left": [1.2], "right": [1.2], "back": [1.2, .9]}, sparse={"back": .5})


def attach():
    f = F(n4, "front"); n4.lean(f, .2, n4.len[f] - .2, n4.fh + .3, depth=1.1, drop=.45)
    f = F(n3, "front"); n3.lean(f, .1, n3.len[f] - .1, n3.fh + .25, depth=.9, drop=.36)
    f = F(r1, "back"); r1.lean(f, .4, 5.0, r1.fh + .2, depth=.9, drop=.3)
    f = F(g2, "front"); g2.balcony(f, .5, 4.0, 1, depth=.8, style="bars")
    f = F(s1, "back"); s1.balcony(f, .4, s1.len[f] - .4, 2, depth=.7, style="conc")
    f = F(s3, "back"); s3.balcony(f, .8, 5.0, 1, depth=.8, style="bars")
    f = F(g1, "front"); g1.balcony(f, .3, g1.len[f] - .3, 1, depth=.6, style="panel")
    f = F(tp, "front"); tp.lean(f, -.6, tp.len[f] + .6, 3.15, depth=1.15, drop=.5)      # kohai-style front eave
    # mokuchin gallery, rail and stair
    f = F(g3, "front"); L = g3.len[f]; fr = g3.frames[f]; y = g3.fh
    box(g3.m, "steel", fr, -.2, L, y - .16, y + .02, 0, 1.1, ch=.01, col=(.42, .42, .4), sc=1.2)
    box(g3.m, "steel", fr, -.2, L, y + .02, y + .05, .02, 1.08, col=(.3, .3, .3))
    for x in frange(-.15, L, .12):
        box(g3.m, "steel", fr, x, x + .016, y + .05, y + 1.0, 1.06, 1.08, col=(.62, .6, .55))
    box(g3.m, "steel", fr, -.2, L, y + .98, y + 1.04, 1.04, 1.1, ch=.006, col=(.6, .58, .53))
    for x in (.0, L / 2, L - .1):
        box(g3.m, "steel", fr, x, x + .1, -.4, y - .16, .95, 1.05, ch=.006, col=(.5, .5, .48))
    # stair runs along the facade under the gallery, top at the east end (x=L-.2), foot at x=L-3.6
    n = 15; x_top = L - .25; run = 3.3
    for i in range(n):
        xa = x_top - (i + 1) / n * run; yy = y - (i + 1) * y / n
        box(g3.m, "steel", fr, xa, xa + run / n + .02, yy - .03, yy, .12, .95, ch=.003, col=(.45, .45, .43), sc=1.2)
    for c in (.1, .95):
        P = [fr.p(x_top - run, 0, c), fr.p(x_top, y, c), fr.p(x_top, y + .22, c), fr.p(x_top - run, .22, c)]
        g3.m.poly("steel", P, [(0, 0), (1, 0), (1, .1), (0, .1)], (.4, .4, .38))
    tube(g3.m, "steel", [fr.p(x_top - run, .95, 1.0), fr.p(x_top, y + .95, 1.0)], .02, 6, (.55, .53, .5))
    for b in (n4, s3, r1, g2):
        c = b.Q(0, 0, b.e + b.rise - .02); b.antenna(c, 2.0)


attach()
for b, side, x, kind in ((g3, "back", 3.0, "ac_outdoor"), (g3, "back", 8.0, "ac_outdoor"), (r1, "back", 2.0, "ac_outdoor"), (g2, "left", 2.5, "ac_outdoor"),
                         (n2, "front", 1.2, "vending_or_bin"), (s4, "left", 1.5, "gas_meter"), (g1, "front", 3.5, "bicycle"), (tp, "front", 1.5, "planter")):
    b.anchor(kind, F(b, side), x, .1 if kind != "gas_meter" else 1.1)

if K.check_overlaps() and not os.environ.get("ALLOW_OVERLAP"):
    print("ABORT overlaps", flush=True); sys.stdout.flush(); os._exit(3)

# ---- ground ----
st_s = [(e, street_edges(e)[0]) for e in frange(-124.0, -94.4, 1.0)] + [(-94.4, -.8)]
st_n = [(e, street_edges(e)[1]) for e in frange(-124.0, -94.4, 1.0)] + [(-94.4, 4.4)]
K.extra_roads = [st_s + st_n[::-1],
                 [(-60.0, -18.9), (-55.7, -18.9), (-55.7, -8.7), (-61.95, -8.7), (-61.95, -.7), (-60.0, -.7)],    # crossing, south leg (+ removed house plot)
                 [(-61.25, 4.3), (-53.5, 4.3), (-53.6, 13.0), (-61.25, 13.0)]]                                     # crossing, north leg (+ removed house plot)
K.pave = [[(-100.2, kerb_n(-100.2, -96.6) - .05), (-96.6, 4.9), (-96.6, 13.0), (-100.2, 13.0)],            # gated footpath to block B
          [(-64.1, -18.0), (-60.0, -18.0), (-60.0, -8.8), (-64.1, -8.8)]]                                   # footway beside the annex
K.gravel = [[(-86.9, -17.6), (-83.5, -17.6), (-83.5, -13.6), (-86.9, -13.6)], [(-69.6, -17.6), (-64.2, -17.6), (-64.2, -13.8), (-69.6, -13.8)]]
gm = K.ground(-124.0, -53.4, -17.6, 15.9, keep=lambda E, N: not (E > -55.7 and N < -.8))
for p_, sz, r_ in (((-110, 3.4), (5.0, 1.3), .02), ((-121, 4.4), (3.5, 1.1), .05), ((-58, -9.5), (1.4, 4.0), 0), ((-56, 8.8), (1.5, 3.4), 0)):
    K.patch(p_[0], p_[1], sz[0], sz[1], r_)
K.scatter_stains(110, -124, -54, -17.5, 15)
for x, y in ((-101.5, 3.0), (-116.0, 4.4), (-57.9, -9.0), (-56.2, 9.5)): K.manhole(x, y, K.R.random() * 3)
K.road_text(-57.9, -4.6, 0, 1.3, 2.6); K.road_text(-56.1, 8.0, pi, 1.2, 2.4)        # 止まれ on both minor legs; 止 sits on the junction side, read by drivers approaching the main street
ribbon_lids(gm, [(e, n - .2) for e, n in st_n], G, K.R); ribbon_lids(gm, [(e, s + .2) for e, s in st_s], G, K.R)
ribbon_lids(gm, [(-55.95, -18.6), (-55.95, -1.0)], G, K.R, width=.4); ribbon_lids(gm, [(-59.8, -18.6), (-59.8, -1.0)], G, K.R, width=.4)
ribbon_lids(gm, [(-58.2, 6.4), (-57.3, 12.9)], G, K.R)
# stop line and crossing paint at the junction mouth
road_paint(gm, [(-59.9, -2.2), (-55.8, -2.2)], G, width=.3); road_paint(gm, [(-58.3, 5.6), (-54.0, 5.6)], G, width=.3)
wm = M("E_walls")
block_wall(wm, [(-100.25, 5.4), (-100.25, 12.9)], G, K.R, h=1.6); block_wall(wm, [(-96.55, 5.4), (-96.55, 12.9)], G, K.R, h=1.4, tc=(.66, .66, .62))
block_wall(wm, [(-124.0, -17.35), (-118.4, -17.35)], G, K.R, h=1.1)
block_wall(wm, [(-99.9, -17.15), (-99.9, -11.0)], G, K.R, h=1.3); block_wall(wm, [(-87.2, -17.6), (-84.0, -17.6)], G, K.R, h=1.0)
block_wall(wm, [(-69.5, -17.4), (-64.2, -17.4)], G, K.R, h=1.0, tc=(.6, .6, .56))
# steel gate across the footpath (real gate in OSM at E-98.2 N9.5)
gf = Frame((-100.15, 9.5, G(-98.4, 9.5)), (1, 0, 0), (0, 0, 1), (0, 1, 0))
for x in frange(.05, 3.5, .11): box(wm, "steel", gf, x, x + .018, .05, 1.35, -.01, .01, col=(.22, .26, .24))
for yy in (.12, 1.3): box(wm, "steel", gf, 0, 3.55, yy - .02, yy + .02, -.02, .02, ch=.004, col=(.22, .26, .24))
# temple: stone lantern pair and a granite step at the approach
def lantern(m, x, y):
    """Granite toro: hexagonal kiso, sao, nakadai, hibukuro, stepped kasa and hoju."""
    z = G(x, y); g = (.6, .6, .57)
    for r, z0, z1, c in ((.3, 0, .16, g), (.1, .16, .95, g), (.23, .95, 1.07, g), (.17, 1.07, 1.33, g), (.38, 1.33, 1.39, tint(g, .9)), (.3, 1.39, 1.46, tint(g, .9)),
                         (.2, 1.46, 1.52, tint(g, .9)), (.07, 1.52, 1.64, g), (.045, 1.64, 1.72, g)):
        tube(m, "concrete", [(x, y, z + z0), (x, y, z + z1)], r, 6, c, sc=.6)
        m.poly("concrete", [(x + r * cos(k * pi / 3), y + r * sin(k * pi / 3), z + z1) for k in range(6)], None, c)
    for k in range(3):          # fire-box windows
        a = k * 2 * pi / 3; lf = Frame((x + .172 * cos(a), y + .172 * sin(a), z + 1.12), (-sin(a), cos(a), 0), (0, 0, 1), (cos(a), sin(a), 0))
        box(m, "dark", lf, -.06, .06, 0, .16, -.01, .002, col=(.04, .04, .04))


for xx in (-80.2, -72.8): lantern(wm, xx, -17.85)
# utility poles continuing qs_h1's line west from pole_Y0 (E-84.5, N-1.15): spans of ~26 m on the south kerb
from blk_equip import utility_pole, cable
pm = M("E_poles")
Y0 = {"hv": [V((-84.5, n, 11.6)) for n in (-2.0, -1.15, -.3)], "lv": [V((-84.5, n, 10.2)) for n in (-1.8, -.5)], "tel": [V((-84.5, -.7, 6.8)), V((-84.5, -.7, 7.3))]}
prev = Y0
for k, E_ in enumerate((-110.2, -123.6)):
    N_ = street_edges(E_)[0] - .35
    cur = utility_pole(pm, E_, N_, G(E_, N_), (0, 1), K.R, xfmr=(k == 0))
    for kind, sag in (("hv", .45), ("lv", .55), ("tel", .7)):
        for a_, b_ in zip(prev[kind], cur[kind]):
            cable(pm, a_, b_, sag, r=.009 if kind == "hv" else (.012 if kind == "lv" else .018))
    prev = cur
for kind in ("hv", "lv", "tel"):        # lines leave the area westward
    for a_ in prev[kind]: cable(pm, a_, a_ + V((-9.0, .6, -.3)), .2, r=.01)
# service drops from the transformer pole to shopfronts on both sides
for (hx, hy, hz) in ((-106.0, kerb_n(-110.4, -100.4) + .02, 5.2), (-113.0, kerb_n(-113.9, -110.6) + .02, 5.0), (-105.5, kerb_s(-110.1, -100.6) - .02, 5.3)):
    p = V((-110.2, street_edges(-110.2)[0] - .35, G(-110.2, 0) + 9.6)); q = V((hx, hy, G(hx, hy) + hz))
    cable(pm, p, q, .35, r=.007); tube(pm, "paint", [q, q + V((0, 0, -.12))], .03, 6, (.85, .85, .82))
K.flush_all(extra=(gm, wm, pm))

CAMS = {"west": ((-88, 1.6, 1.65), (-124, 4.0, 2.6), 26), "east": ((-121, 4.2, 1.65), (-90, 1.8, 2.8), 26), "lane": ((-121.5, -18.6, 1.65), (-95, -15.0, 3.0), 26),
        "temple": ((-65.5, -20.4, 1.65), (-79, -15.6, 3.2), 26), "mokuchin": ((-84.5, -19.2, 1.65), (-97, -15.2, 3.0), 26), "junction": ((-57.8, -14.5, 1.65), (-57.3, 14, 3.2), 26),
        "path": ((-98.4, 4.4, 1.65), (-98.6, 16, 2.0), 24), "roof": ((-62, -48, 26), (-100, -2, 3), 32), "_own": (-124, -53.4, -17.6, 15.9)}
K.finish(a, CAMS, dict(street_south_kerb_enu=st_s, street_north_kerb_enu=st_n, crossing_enu=K.extra_roads[1:], removed_h1=sorted(REMOVED_H1)))
