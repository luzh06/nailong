# Shared kit for the 80x80 fill blocks (C/D/E): real terrain, exclusion of existing geometry, PLATEAU roads, ground, export, preview.
# Coordinates are ENU metres (origin = real stair top), flushed to qs_h1 model space by blk_core.flush.
import sys, os, json, time, random, argparse
import bpy
from blk_core import *
from blk_arch import *


def args(cams):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="r1"); ap.add_argument("--cams", default=cams)
    ap.add_argument("--res", type=int, default=1280); ap.add_argument("--spp", type=int, default=96)
    ap.add_argument("--export", type=int, default=0); ap.add_argument("--render", type=int, default=1)
    ap.add_argument("--ctx", type=int, default=1)     # 1: import blocks A/B and qs_h1 frontage as render context
    return ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


DATA = json.load(open(ROOT + r"\data\plateau_near.json"))
_DEM = json.load(open(ROOT + r"\data\dem_enu.json"))
H1 = json.load(open(ROOT + r"\data\h1_rects.json"))

# ---------- terrain ----------
# Blocks A/B fitted PLATEAU LOD2 GroundSurface along the street (east-west). Keep it so seams match, add the GSI 5 m DEM
# cross-street relief where it is real (east of E=-54), and ramp onto the flat qs_h1 street.
GZ = [(-135, 7.47), (-118, 7.5), (-100, 7.6), (-92, 7.78), (-84, 8.0), (-76, 8.28), (-67, 8.36), (-50, 8.5)]
Z_DATUM = 7.95
H1_WEST = -94.5          # qs_h1 street ends here (model y=-62)


def ss(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def gab(E):
    for i in range(len(GZ) - 1):
        if E <= GZ[i + 1][0]:
            t = (E - GZ[i][0]) / (GZ[i + 1][0] - GZ[i][0])
            return lerp(GZ[i][1], GZ[i + 1][1], max(0, t)) - Z_DATUM
    return GZ[-1][1] - Z_DATUM


def dem(E, N):
    x = min(max((E - _DEM["E0"]) / _DEM["step"], 0), _DEM["nE"] - 2.001); y = min(max((N - _DEM["N0"]) / _DEM["step"], 0), _DEM["nN"] - 2.001)
    i = int(floor(x)); j = int(floor(y)); fx = x - i; fy = y - j
    h = _DEM["h"]
    q = [[h[j + b][i + a] for a in (0, 1)] for b in (0, 1)]
    return q[0][0] * (1 - fx) * (1 - fy) + q[0][1] * fx * (1 - fy) + q[1][0] * (1 - fx) * fy + q[1][1] * fx * fy


def street_edges(E):
    """South / north kerb lines of the main street. qs_h1 is straight; west of it the real street drifts north."""
    t = ss((H1_WEST - E) / 24)
    return lerp(-.8, 1.6, t), lerp(4.4, 7.4, t)


def street_z(E):
    return 0.0 if E >= H1_WEST else gab(E) * ss((H1_WEST - E) / 10)


def cross(E, N):
    w = ss((E + 54) / 8)
    if w <= 0: return 0.0
    d = sum(dem(E + a, N + b) for a in (-2, 0, 2) for b in (-2, 0, 2)) / 9 - dem(E, 1.8)
    return w * max(-.3, min(.9, d))


def G(E, N):
    s, n = street_edges(E)
    dN = s - N if N < s else (N - n if N > n else 0.0)
    z0 = street_z(E)
    return z0 + (gab(E) + cross(E, N) - z0) * ss((dN - .5) / 7)


# ---------- occupancy ----------
BLOCK_A = (-124.0, -54.0, -55.0, -15.5)        # ground rects of delivered blocks (E0,E1,N0,N1)
BLOCK_B = (-116.0, -50.0, 12.9, 48.0)
REMOVED_H1 = {"h_G-14", "h_G15"}                # frontage houses removed to open the real crossing at E~-58
CROSSING = (-61.2, -52.6, -8.7, 12.3)           # anything of these kinds centred here goes with them (awnings, eaves, walls)
CROSSING_KINDS = ("h_G-14", "h_G15", "aw", "block", "side", "closures")


def h1_removed(name, center_enu):
    if any(name.startswith(k) for k in REMOVED_H1): return True
    return name.startswith(CROSSING_KINDS) and in_rect(center_enu[0], center_enu[1], CROSSING)


def in_rect(E, N, r, pad=0.0):
    return r[0] - pad <= E <= r[1] + pad and r[2] - pad <= N <= r[3] + pad


def h1_occupied(E, N, pad=.0):
    if E >= H1_WEST and -.8 <= N <= 4.4 and E <= -31.1: return True     # qs_h1 street surface
    for k, d in H1.items():
        if k in REMOVED_H1: continue
        if d["E"][0] - pad <= E <= d["E"][1] + pad and d["N"][0] - pad <= N <= d["N"][1] + pad: return True
    return False


def foreign(E, N):
    return in_rect(E, N, BLOCK_A) or in_rect(E, N, BLOCK_B) or h1_occupied(E, N)


A_LANE_N = [(-124, -17.3), (-106.6, -17.3), (-94.2, -17.6), (-86.4, -18.1), (-60.3, -20.6)]     # north kerb of block A's lane


def a_lane_n(E):
    for (x0, y0), (x1, y1) in zip(A_LANE_N, A_LANE_N[1:]):
        if E <= x1: return lerp(y0, y1, max(0, (E - x0) / (x1 - x0)))
    return A_LANE_N[-1][1]


B_ROAD_E = [(6.3, -54.0), (23.8, -53.2), (32.7, -53.2), (39.1, -54.1), (45.0, -55.2), (49.0, -56.6)]     # east kerb of block B's road (N, E)


def b_road_e(N):
    for (y0, x0), (y1, x1) in zip(B_ROAD_E, B_ROAD_E[1:]):
        if N <= y1: return lerp(x0, x1, max(0, (N - y0) / (y1 - y0)))
    return B_ROAD_E[-1][1]


def foreign_bld(E, N):
    """Buildings may stand on block A's lot strip north of its lane and on block B's strip east of its road, nothing else."""
    inA = BLOCK_A[0] <= E <= BLOCK_A[1] and BLOCK_A[2] <= N <= a_lane_n(E) + .1
    inB = BLOCK_B[0] <= E <= b_road_e(N) + .1 and BLOCK_B[2] <= N <= BLOCK_B[3]
    return inA or inB or h1_occupied(E, N)


# PLATEAU road polygons (one city copy), bbox-indexed
ROADPOLYS = []
for r in DATA["roads"]:
    if not r["src"].startswith("taito"): continue
    for p in r["polys"]:
        if len(p) < 4: continue
        pts = [(q[0], q[1]) for q in p[:-1]]
        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
        ROADPOLYS.append((min(xs), max(xs), min(ys), max(ys), pts))


def plateau_road(E, N):
    for x0, x1, y0, y1, pts in ROADPOLYS:
        if x0 <= E <= x1 and y0 <= N <= y1 and pip((E, N), pts): return True
    return False


def fp_at(cx, cy):
    best = None
    for b in DATA["buildings"]:
        fp = b["lod"].get("lod0", [[]])[0]
        if len(fp) < 3: continue
        ccx = sum(p[0] for p in fp) / len(fp); ccy = sum(p[1] for p in fp) / len(fp)
        d = (ccx - cx) ** 2 + (ccy - cy) ** 2
        if best is None or d < best[0]: best = (d, b, fp)
    return [(p[0], p[1]) for p in best[2][:-1]], best[1]


def rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ---------- materials ----------
MDEF = {
    "mortar": dict(texid="mortar_n", nor_k=.7), "plaster": dict(texid="plastered_wall_04", nor_k=1.0), "beige": dict(texid="mortar_n", nor_k=.55),
    "mossy": dict(texid="worn_mossy_plasterwall", nor_k=.9), "whitetile": dict(texid="long_white_tiles", nor_k=1.0), "darkface": dict(texid="concrete_tile_facade", nor_k=1.0),
    "siding": dict(texid="exterior_wall_cladding", nor_k=1.2), "siding2": dict(texid="exterior_wall_cladding_03", nor_k=1.2),
    "facetile": dict(texid="facade_tiles_n", nor_k=1.1), "tin": dict(texid="corrugated_iron_02", nor_k=1.3),
    "rustytin": dict(texid="rusty_corrugated_iron", nor_k=1.3), "galva": dict(texid="box_grey"),
    "blackplank": dict(texid="black_painted_planks"), "cedar": dict(texid="cedar_muted"), "soffit": dict(texid="cedar_muted"),
    "fasciaw": dict(texid="weathered_plank_siding"), "plank": dict(texid="weathered_plank_siding"), "blockwall": dict(texid="block_n"), "concrete": dict(texid="lot_n"),
    "asphalt": dict(texid="asphalt_02", nor_k=1.0), "lot": dict(texid="lot_n"), "gravel": dict(texid="gravel_concrete_03"), "pave": dict(texid="concrete_floor_worn_001", nor_k=.8),
    "slate": dict(texid="grey_roof_01"), "shutter": dict(texid="painted_metal_shutter"), "steel": dict(texid="steel_muted"),
    "kawara": dict(solid=(1, 1, 1), rough=.46, spec=.38), "roofbase": dict(solid=(.1, .1, .1), rough=.9),
    "alu": dict(solid=(.85, .84, .82), metal=.9, rough=.38), "pvc": dict(solid=(1, 1, 1), rough=.42), "paint": dict(solid=(1, 1, 1), rough=.46),
    "plinth_top": dict(solid=(1, 1, 1), rough=.4, metal=.6), "glass": dict(solid=(.03, .04, .045), rough=.04, alpha=.62, spec=.9),
    "frost": dict(solid=(.42, .47, .46), rough=.28, spec=.7), "dark": dict(solid=(1, 1, 1), rough=.9), "polyc": dict(solid=(.85, .88, .85), rough=.25, alpha=.72),
    "decal": {}, "curtain": {},
    # wall variety (neutralised Poly Haven CC0 plasters, tinted per house)
    "plaster5": dict(texid="plaster5_n", nor_k=.8), "rough3": dict(texid="rough3_n", nor_k=.9), "cracked": dict(texid="cracked_n", nor_k=.9), "damaged": dict(texid="damaged_n", nor_k=.9),
}


SIGNS = json.load(open(GEN + r"\signs.json"))


def tex_mat(name, img, rough=.6, emit=None):
    mt = bpy.data.materials.new(name); mt.use_nodes = True
    nt = mt.node_tree; bs = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(img)
    va = nt.nodes.new("ShaderNodeVertexColor"); va.layer_name = "Col"
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
    nt.links.new(t.outputs["Color"], mx.inputs["A"]); nt.links.new(va.outputs["Color"], mx.inputs["B"]); nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    return mt


def lit_mat():
    """Shop interior card: warm, self-lit so open shops read at dusk."""
    mt = bpy.data.materials.new("shoplit"); mt.use_nodes = True
    bs = mt.node_tree.nodes["Principled BSDF"]
    va = mt.node_tree.nodes.new("ShaderNodeVertexColor"); va.layer_name = "Col"
    mt.node_tree.links.new(va.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Emission Color"].default_value = (1, .78, .52, 1); bs.inputs["Emission Strength"].default_value = .9
    bs.inputs["Roughness"].default_value = .8
    return mt


def uvcell(c, flip=False):
    u0, v0, u1, v1 = c
    if flip: u0, u1 = u1, u0
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


GOODS = ((.72, .2, .16), (.86, .7, .3), (.3, .45, .26), (.85, .82, .74), (.25, .3, .5), (.6, .42, .26), (.9, .55, .2), (.5, .16, .2))


def goods(m, f, a, y, R, kind):
    """One shelf item at wall coords (a along, y shelf top), set back inside the shop."""
    from blk_temple import lathe
    c = f.p(a + .05, y, -.42); cc = tint(R.choice(GOODS), R.uniform(.75, 1.05))
    if kind == "jars":           # ceramic or glass jars with lids (sweets, pickles, tea)
        h = R.uniform(.12, .22); r = R.uniform(.035, .055)
        lathe(m, "paint" if R.random() < .6 else "glass", c, [(.01, 0), (r, .005), (r * 1.1, h * .6), (r * .8, h * .9), (r * .8, h)], 10, cc if R.random() < .6 else (.9, .9, .88))
        lathe(m, "paint", c + V((0, 0, h)), [(r * .85, 0), (r * .9, .02), (.01, .03)], 10, tint(cc, .6))
    elif kind == "bottles":      # sake / soy bottles
        h = R.uniform(.18, .3); r = R.uniform(.025, .04)
        lathe(m, "glass" if R.random() < .5 else "paint", c, [(.01, 0), (r, .005), (r, h * .65), (r * .4, h * .8), (r * .35, h)], 10, R.choice(((.25, .4, .2), (.35, .2, .1), (.85, .85, .8))))
        box(m, "paint", f, a + .05 - r * .9, a + .05 + r * .9, y + h * .25, y + h * .5, -.42 + r + .001, -.42 + r + .003, col=R.choice(GOODS))
    elif kind == "boxes":        # wrapped gift boxes, stacked
        for k in range(R.randint(1, 3)):
            bw = R.uniform(.08, .12); bh = R.uniform(.04, .07); z0 = y + k * bh
            box(m, "paint", f, a, a + bw, z0, z0 + bh, -.48, -.36, ch=.004, col=tint(cc, 1 - .1 * k))
            box(m, "paint", f, a + bw * .45, a + bw * .55, z0, z0 + bh + .001, -.481, -.359, col=(.9, .85, .7))
    else:                        # paper bags and small baskets
        lathe(m, "plank", c, [(.01, 0), (.06, .005), (.065, .05), (.06, .06)], 8, (.62, .5, .32))
        tube(m, "paint", [c + V((0, 0, .05)), c + V((0, 0, .12))], .04, 7, cc)


def shopfront(b, i, x, w, h=2.6, style="glass", sign=None, vsign=None, noren=None, awning="tent", awncol=(.62, .16, .12), sub=False):
    """Cut a storefront and register its fit-out; geometry is added after the shell is built."""
    b.add_shop(i, x, w, h)
    b.sp.setdefault("_fit", []).append(dict(i=i, x=x, w=w, h=h, style=style, sign=sign, vsign=vsign, noren=noren, awning=awning, awncol=awncol))


def build_fitout(b):
    for d in b.sp.get("_fit", []):
        _fit(b, **d)


def _fit(b, i, x, w, h, style, sign, vsign, noren, awning, awncol):
    m = b.m; f = b.frames[i]; R = b.rng; fc = b.sp.get("framecol", (.55, .54, .5))
    y0 = .02; full = (x, w)
    # lit interior, shelves and goods
    P = [f.p(x + .05, y0, -.52), f.p(x + w - .05, y0, -.52), f.p(x + w - .05, h, -.52), f.p(x + .05, h, -.52)]
    m.poly("shoplit", P, None, (.95, .86, .72) if style != "shutter" else (.25, .22, .2))
    if style in ("glass", "open", "lattice"):
        kind = R.choice(("jars", "bottles", "boxes", "mixed"))
        for k in range(int(w / .9)):
            a = x + .15 + k * .9
            for yy in (.45, 1.0, 1.55):
                box(m, "plank", f, a, a + .8, yy - .03, yy, -.5, -.3, ch=.004, col=(.55, .45, .35), sc=1.9)
                q = a + .05
                while q < a + .72:
                    goods(m, f, q, yy, R, kind if kind != "mixed" else R.choice(("jars", "bottles", "boxes", "bags")))
                    q += R.uniform(.11, .17)
    if style == "glass":
        n = max(2, int(round(w / .95))); sw = w / n
        for k in range(n + 1):
            a = x + k * sw
            box(m, "alu", f, a - .025, a + .025, y0, h, -.2, -.12, ch=.004, col=fc)
        for yy in (y0, 2.05, h - .04):
            box(m, "alu", f, x, x + w, yy, yy + .045, -.2, -.12, ch=.004, col=fc)
        P = [f.p(x, y0, -.16), f.p(x + w, y0, -.16), f.p(x + w, h, -.16), f.p(x, h, -.16)]
        m.poly("glass", P, [(0, 0), (1, 0), (1, 1), (0, 1)], (1, 1, 1))
        box(m, "steel", f, x + .05, x + w - .05, y0, y0 + .12, -.22, -.1, col=(.3, .3, .3))          # door rail
    elif style == "open":
        box(m, "alu", f, x - .05, x + w + .05, h - .02, h + .3, -.05, .14, ch=.01, col=(.55, .54, .52))     # rolled shutter box
        for k in range(max(1, int(w / 1.3))):    # sloped display stands spilling onto the street
            a = x + .2 + k * 1.3
            if a + 1.1 > x + w: break
            box(m, "plank", f, a, a + 1.1, .7, .75, -.1, .65, ch=.006, col=(.5, .4, .3), sc=1.9)
            for lx in (a + .05, a + 1.0):
                for c_ in (.0, .58):
                    box(m, "plank", f, lx, lx + .05, 0, .7, c_, c_ + .05, col=(.4, .32, .24), sc=1.9)
            for q in frange(a + .05, a + 1.0, .21):
                for c_ in (.05, .3):
                    cc = R.choice(GOODS); box(m, "plank", f, q, q + .19, .75, .86, c_, c_ + .22, ch=.006, col=(.62, .5, .36), sc=1.9)
                    box(m, "paint", f, q + .02, q + .17, .86, .86 + R.uniform(.05, .12), c_ + .02, c_ + .2, ch=.02, col=tint(cc, R.uniform(.75, 1.05)))
    elif style == "lattice":
        dw = min(1.5, w * .4); dx = x + (w - dw) / 2
        for a in frange(x + .04, x + w - .02, .055):
            if dx - .02 < a < dx + dw: continue
            box(m, "soffit", f, a, a + .025, y0, h, -.14, -.1, col=(.32, .22, .14), sc=1.9)
        for yy in (y0, 1.0, h - .06):
            box(m, "soffit", f, x, x + w, yy, yy + .06, -.15, -.08, ch=.004, col=(.3, .21, .13), sc=1.9)
        P = [f.p(x, y0, -.16), f.p(x + w, y0, -.16), f.p(x + w, h, -.16), f.p(x, h, -.16)]
        m.poly("frost", P, None, (.85, .82, .74))
        noren = noren if noren is not None else R.randrange(4)
        x, w = dx, dw
    elif style == "shutter":
        P = [f.p(x, y0, -.12), f.p(x + w, y0, -.12), f.p(x + w, h, -.12), f.p(x, h, -.12)]
        m.poly("shutter", P, [(0, 0), (w / 2, 0), (w / 2, h / 2), (0, h / 2)], (.75, .74, .7))
        box(m, "alu", f, x - .04, x + w + .04, h - .02, h + .3, -.05, .14, ch=.01, col=(.55, .54, .52))
    # noren on a rod across the door
    if noren is not None:
        nw = min(1.4, w - .1); nx = x + (w - nw) / 2; top = h - .02 if style != "lattice" else h - .06
        tube(m, "steel", [f.p(nx - .08, top, .06), f.p(nx + nw + .08, top, .06)], .012, 6, (.2, .2, .2))
        cell = SIGNS["noren"][noren % 4]; k = 3; pw = (nw - .04 * (k - 1)) / k
        for j in range(k):
            a = nx + j * (pw + .04); u0 = cell[0] + (cell[2] - cell[0]) * j / k; u1 = cell[0] + (cell[2] - cell[0]) * (j + 1) / k
            PP = []; UV = []
            for ii in range(5):
                t = ii / 4; col = []; uv = []
                for yy in (top, top - .9):
                    wave = .015 * sin(t * pi * 2 + j) * (1 if yy < top else 0)
                    col.append(f.p(a + pw * t, yy, .06 + wave)); uv.append((lerp(u0, u1, t), cell[3] if yy == top else cell[1]))
                PP.append(col); UV.append(uv)
            m.grid("noren", PP, UV, [[(1, 1, 1)] * 2 for _ in PP], smooth=True)
            PP2 = [list(reversed(r)) for r in PP]; UV2 = [list(reversed(r)) for r in UV]      # back face
            m.grid("noren", [[q + f.n * -.002 for q in r] for r in PP2], UV2, [[(.6, .6, .6)] * 2 for _ in PP2], smooth=True)
    x, w = full     # awning and board span the whole front, the noren only the door
    # awning
    a0 = x - .15; a1 = x + w + .15; ztop = h + .38; zlow = h - .12; dep = .95
    if awning == "tent":
        nu = max(2, int((a1 - a0) / .25)); PP = []; UV = []; CC = []
        for ii in range(nu + 1):
            t = ii / nu; a = lerp(a0, a1, t); r = []; q = []; c = []
            for jj in range(5):
                v = jj / 4; sag = .03 * sin(v * pi)
                r.append(f.p(a, lerp(ztop, zlow, v) - sag, lerp(.02, dep, v))); q.append((a / 1.5, v)); c.append(wall_col(f.p(a, 2, 0), -3, 99, awncol, .6))
            PP.append(r); UV.append(q); CC.append(c)
        m.grid("cloth", PP, UV, CC, smooth=True)
        m.grid("cloth", [[q - f.v * .004 for q in r[::-1]] for r in PP], [r[::-1] for r in UV], [[tint(x_, .6) for x_ in r] for r in CC], smooth=True)
        VP = [[f.p(a, zlow, dep), f.p(a, zlow - .24, dep)] for a in (a0, a1)]
        m.grid("cloth", VP, [[(0, 0), (0, .2)], [(1, 0), (1, .2)]], [[tint(awncol, .95)] * 2] * 2, smooth=False)
        for a in (a0 + .05, a1 - .05):
            tube(m, "steel", [f.p(a, ztop - .5, 0), f.p(a, zlow, dep - .02)], .012, 6, (.25, .25, .25))
    elif awning == "tin":
        Pa = f.p(a0, ztop, 0); Pb = f.p(a1, ztop, 0); Pc = f.p(a1, zlow + .05, dep); Pd = f.p(a0, zlow + .05, dep)
        seam_slope(m, Pd, Pc, Pb, Pa, "galva", "galva", awncol, pitch=.2, sc=1.9, rib_h=.018)
        box(m, "galva", f, a0, a1, zlow - .02, zlow + .1, dep - .02, dep + .02, ch=.006, col=tint(awncol, .8), sc=1.9)
        for a in (a0 + .1, a1 - .1):
            tube(m, "steel", [f.p(a, ztop - .45, 0), f.p(a, zlow + .05, dep - .05)], .014, 6, (.3, .3, .3))
    # kanban board over the awning
    if sign is not None:
        bw = min(w + .2, 3.4); bh = bw / 4; bx = x + (w - bw) / 2; by = ztop + .08
        if by + bh < b.fh + .9 or b.st == 1:
            box(m, "paint", f, bx - .04, bx + bw + .04, by - .04, by + bh + .04, 0, .07, ch=.008, col=(.18, .16, .14))
            P = [f.p(bx, by, .072), f.p(bx + bw, by, .072), f.p(bx + bw, by + bh, .072), f.p(bx, by + bh, .072)]
            m.poly("signs", P, uvcell(SIGNS["h"][sign % len(SIGNS["h"])]), (.92, .92, .92))
    if vsign is not None:
        a = x + w + .25 if (x + w + .6) < b.len[i] else x - .25
        y1 = b.fh + .2 if b.st > 1 else h + .5; vh = 1.4; vw = vh / 4
        fr = Frame(f.p(a, y1, 0), f.n, f.v, -f.u)
        box(m, "paint", fr, .12, .14 + vw + .04, -.02, vh + .02, -.04, .04, ch=.006, col=(.2, .18, .16))
        for s_ in (1, -1):
            P = [fr.p(.14, 0, s_ * .041), fr.p(.14 + vw, 0, s_ * .041), fr.p(.14 + vw, vh, s_ * .041), fr.p(.14, vh, s_ * .041)]
            if s_ < 0: P = [P[1], P[0], P[3], P[2]]
            m.poly("signs", P, uvcell(SIGNS["v"][vsign % len(SIGNS["v"])], flip=False), (.92, .92, .92))
        for yy in (.15, vh - .15):
            box(m, "steel", fr, 0, .14, yy - .015, yy + .015, -.015, .015, col=(.25, .25, .25))


class Block:
    def __init__(s, name, seed):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        s.t0 = time.time(); s.name = name
        s.mats = build_materials(MDEF)
        s.mats["signs"] = tex_mat("signs", GEN + r"\signs.jpg", .5); s.mats["noren"] = tex_mat("noren", GEN + r"\noren.jpg", .95)
        s.mats["shoplit"] = lit_mat(); s.mats["cloth"] = pbr("cloth", solid=(1, 1, 1), rough=.85)
        s.mats["manhole"] = tex_mat("manhole", GEN + r"\manhole.jpg", .55)
        s.mats["manhole"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = .6
        rm = tex_mat("roadmark", GEN + r"\roadmark.png", .6); nt = rm.node_tree
        img = [n_ for n_ in nt.nodes if n_.bl_idname == "ShaderNodeTexImage"][0]
        nt.links.new(img.outputs["Alpha"], nt.nodes["Principled BSDF"].inputs["Alpha"]); rm.surface_render_method = "BLENDED"
        s.mats["roadmark"] = rm
        s.coll = bpy.data.collections.new("block_" + name); bpy.context.scene.collection.children.link(s.coll)
        s.ctx = bpy.data.collections.new("context"); bpy.context.scene.collection.children.link(s.ctx)
        s.S = {}; s.objs = []; s.R = random.Random(seed)
        s.extra_roads = []; s.gravel = []; s.pave = []; s.default_cls = 0      # 0 lot, 1 asphalt for open ground
        s.equip = 1.0                                                          # AC units, meters, pots per house (0 = off)

    def mk(s, name, fp, H, st, **spec):
        b = Bld(name, fp, H, st, G, random.Random(sum(map(ord, name)) * 211), **spec); s.S[name] = b; return b

    def check_overlaps(s):
        """Footprints must not overlap each other or existing geometry; fail fast."""
        bad = []
        L = [b for b in s.S.values() if not b.noplinth]
        for i, a in enumerate(L):
            for b in L[i + 1:]:
                if _obb_hit(a, b, -.05): bad.append((a.name, b.name))
            for k in range(25):
                u = (k % 5) / 4 * 1.6 - .8; v = (k // 5) / 4 * 1.6 - .8
                p = a.c + a.ax * (a.a * u) + a.ay * (a.b * v)
                if foreign_bld(p.x, p.y) and not a.sp.get("over_ok"): bad.append((a.name, "existing@%.1f,%.1f" % (p.x, p.y))); break
        if bad:
            print("OVERLAP", bad, flush=True)
        return bad

    # ---- ground ----
    def classify(s, E, N, inside):
        for c, ax, ay, ha, hb in inside:
            d = V((E, N, 0)) - c
            if abs(d.dot(ax)) < ha and abs(d.dot(ay)) < hb: return 2
        if any(pip((E, N), p) for p in s.pave): return 4
        if any(pip((E, N), p) for p in s.extra_roads) or plateau_road(E, N): return 1
        if any(pip((E, N), p) for p in s.gravel): return 3
        return s.default_cls

    def ground(s, E0, E1, N0, N1, cell=.3, keep=None):
        gm = M(s.name + "_ground"); s.gm = gm
        inside = [(b.c, b.ax, b.ay, b.a - .35, b.b - .35) for b in s.S.values() if not b.noplinth]
        nx = int(round((E1 - E0) / cell)); ny = int(round((N1 - N0) / cell))
        cls = []
        for i in range(nx):
            col = []
            for j in range(ny):
                E = E0 + (i + .5) * cell; N = N0 + (j + .5) * cell
                if foreign(E, N) or (keep and not keep(E, N)): col.append(-1)
                else: col.append(s.classify(E, N, inside))
            cls.append(col)
        s.cls = cls; s.gext = (E0, N0, cell, nx, ny)
        for c_, mat, sc, base in ((1, "asphalt", 3.4, (.82, .82, .84)), (0, "lot", 2.4, (.7, .69, .66)), (3, "gravel", 2.6, (1.0, .97, .9)), (4, "pave", 2.0, (.78, .77, .74))):
            PP = [[V((E0 + i * cell, N0 + j * cell, s.gz(E0 + i * cell, N0 + j * cell, c_))) for j in range(ny + 1)] for i in range(nx + 1)]
            UV = [[(p.x / sc, p.y / sc) for p in r] for r in PP]; CC = [[s.gcol(p.x, p.y, base) for p in r] for r in PP]
            gm.grid(mat, PP, UV, CC, smooth=True, skip=lambda i, j, r=c_: cls[i][j] != r)
        return gm

    def cls_at(s, E, N):
        E0, N0, cell, nx, ny = s.gext
        i = int((E - E0) / cell); j = int((N - N0) / cell)
        return s.cls[i][j] if 0 <= i < nx and 0 <= j < ny else -1

    @staticmethod
    def gz(x, y, c):
        z = G(x, y) + (-.018 if c == 1 else .0)       # small step: 0.3 m cell edges between classes stay invisible at eye height
        return z + .008 * nz((x, y, 0), .6) + .004 * nz((x, y, 0), 2.1) + (.012 * nz((x, y, 7), .25) if c == 1 else 0) + (.02 * nz((x, y, 3), 1.3) if c == 3 else 0)

    @staticmethod
    def gcol(x, y, base):
        return tint(base, max(.4, 1 + .16 * nz((x, y, 3), .22) + .1 * nz((x, y, 9), .9) + .05 * nz((x, y, 1), 3.3)))

    def on_ground(s, cx, cy, w, h, cell_, rot=0, c=1):
        u = V((cos(rot), sin(rot), 0)); v = V((-sin(rot), cos(rot), 0)); nu = 8; nv = max(2, int(8 * h / w)); P = []; UV = []
        cu0 = (cell_ % 4) / 4; cv1 = 1 - (cell_ // 4) / 4
        for i in range(nu + 1):
            r = []; q = []
            for j in range(nv + 1):
                p = V((cx, cy, 0)) + u * (w * (i / nu - .5)) + v * (h * (j / nv - .5))
                r.append(V((p.x, p.y, s.gz(p.x, p.y, c) + .004))); q.append((cu0 + i / nu / 4, cv1 - .25 + j / nv / 4))
            P.append(r); UV.append(q)
        s.gm.grid("decal", P, UV, [[(1, 1, 1)] * (nv + 1) for _ in range(nu + 1)], smooth=True)

    def scatter_stains(s, n, E0, E1, N0, N1):
        for k in range(n):
            x = s.R.uniform(E0, E1); y = s.R.uniform(N0, N1); c = s.cls_at(x, y)
            if c in (-1, 2): continue
            z = s.R.uniform(.8, 3.0)
            cell = s.R.choice((14, 6, 7, 9, 10, 14) if c == 1 else (14, 6, 7, 8))       # oil, grime, cracks on asphalt; moss on lots
            s.on_ground(x, y, z, z * s.R.uniform(.5, 1), cell, s.R.random() * 3, c)

    def disc_on_ground(s, mat, x, y, r, rot=0, lift=.006, uvs=(0, 0, 1, 1), w=None, h=None):
        """Ground-conforming quad grid (manhole r>0 as disc mapped square; road text w x h)."""
        w = w or 2 * r; h = h or 2 * r; u = V((cos(rot), sin(rot), 0)); v = V((-sin(rot), cos(rot), 0)); n_ = 8; P = []; UV = []
        c = s.cls_at(x, y)
        for i in range(n_ + 1):
            row = []; q = []
            for j in range(n_ + 1):
                p = V((x, y, 0)) + u * (w * (i / n_ - .5)) + v * (h * (j / n_ - .5))
                row.append(V((p.x, p.y, s.gz(p.x, p.y, 1 if c == 1 else 0) + lift))); q.append((lerp(uvs[0], uvs[2], i / n_), lerp(uvs[1], uvs[3], j / n_)))
            P.append(row); UV.append(q)
        s.gm.grid(mat, P, UV, [[(1, 1, 1)] * (n_ + 1) for _ in range(n_ + 1)], smooth=True)

    def manhole(s, x, y, rot=0):
        """Polar disc so only the cast-iron circle shows; frame ring proud by 6 mm."""
        r = .33; c = s.cls_at(x, y); P = []; UV = []
        for i in range(33):
            th = 2 * pi * i / 32 + rot; row = []; q = []
            for rr in (0, .5, 1.0):
                p = (x + r * rr * cos(th), y + r * rr * sin(th))
                row.append(V((p[0], p[1], s.gz(p[0], p[1], 1 if c == 1 else 0) + .014))); q.append((.5 + .485 * rr * cos(th - rot), .5 + .485 * rr * sin(th - rot)))
            P.append(row); UV.append(q)
        s.gm.grid("manhole", P, UV, [[(1, 1, 1)] * 3 for _ in P], smooth=True)
        s.on_ground(x, y, .9, .9, 14, rot, s.cls_at(x, y))                      # dark ring of seepage around it

    def road_text(s, x, y, rot, w=1.3, h=2.6):
        s.disc_on_ground("roadmark", x, y, 0, rot, .007, w=w, h=h)

    def patch(s, x, y, w, h, rot=0):
        """Asphalt repair with tar seams, as blocks A/B."""
        s.on_ground(x, y, w, h, 12, rot)
        u = V((-sin(rot), cos(rot), 0)) * (h * .5)
        s.on_ground(x + u.x, y + u.y, w * 1.02, .22, 13, rot); s.on_ground(x - u.x, y - u.y, w * 1.02, .22, 13, rot)

    # ---- output ----
    def flush_all(s, extra=()):
        s.objs = []
        from blk_equip import equip_house
        for b in s.S.values():
            b.build(); build_fitout(b)
            if s.equip: equip_house(b, random.Random(sum(map(ord, b.name)) * 7), s.equip)
            s.objs.append(flush(b.m, s.mats, s.coll))
        for m in extra: s.objs.append(flush(m, s.mats, s.coll))
        s.instance_props()

    def instance_props(s):
        """CC0 plant models from the 5070 asset folder, one mesh per asset shared by every instance."""
        import blk_equip, mathutils
        src = {}
        for asset, pos, rot, sc in blk_equip.PROPS:
            if asset not in src:
                before = set(bpy.data.objects)
                bpy.ops.import_scene.gltf(filepath=rf"D:\Cijian\assets\models\{asset}\{asset}_2k.gltf")
                new = [o for o in set(bpy.data.objects) - before if o.type == "MESH"]
                src[asset] = [(o.data, o.matrix_world.copy()) for o in new]
                for o in set(bpy.data.objects) - before: bpy.data.objects.remove(o, do_unlink=True)
            T = mathutils.Matrix.Translation(V(to_model(pos))) @ mathutils.Matrix.Rotation(rot, 4, "Z") @ mathutils.Matrix.Scale(sc, 4)
            for me, mw in src[asset]:
                ob = bpy.data.objects.new(f"prop_{asset}", me); ob.matrix_world = T @ mw; s.coll.objects.link(ob)
        print("PROPS", len(blk_equip.PROPS), {k: len(v) for k, v in src.items()}, flush=True)

    def context(s, own_box):
        """Preview-only: PLATEAU masses beyond own_box, plus delivered blocks A/B and the qs_h1 frontage when available."""
        cm = M("context_mass"); s.mats["ctx"] = pbr("ctx", solid=(.2, .19, .18), rough=.8)
        own = [b.c for b in s.S.values()]
        for b in DATA["buildings"]:
            fp = b["lod"].get("lod0", [[]])[0]
            if len(fp) < 4 or not b["src"].startswith("taito"): continue
            cx = sum(p[0] for p in fp) / len(fp); cy = sum(p[1] for p in fp) / len(fp)
            if any(abs(cx - c.x) < 5 and abs(cy - c.y) < 5 for c in own) or in_rect(cx, cy, own_box) or foreign(cx, cy): continue
            h = float(b["attrs"].get("measuredHeight", 7)); z = G(cx, cy); n = len(fp) - 1
            for i in range(n):
                p, q = fp[i], fp[i + 1]; cm.poly("ctx", [(p[0], p[1], z - 1), (q[0], q[1], z - 1), (q[0], q[1], z + h), (p[0], p[1], z + h)])
            cm.poly("ctx", [(p[0], p[1], z + h) for p in fp[:-1]])
        cm.poly("ctx", [(-400, -400, -.6), (400, -400, -.6), (400, 400, -.6), (-400, 400, -.6)], None, (.28, .28, .28))
        flush(cm, s.mats, s.ctx)
        for B in ("A", "B"):
            p = ROOT + rf"\ref\block_{B}.glb"
            if os.path.exists(p):
                before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
                for o in set(bpy.data.objects) - before:
                    for c in o.users_collection: c.objects.unlink(o)
                    s.ctx.objects.link(o)
        p = ROOT + r"\ref\h1_frontage.blend"
        if os.path.exists(p):
            with bpy.data.libraries.load(p) as (src, dst):
                dst.objects = list(src.objects)
            for o in dst.objects:
                if o is None: continue
                c = sum((o.matrix_world @ V(b) for b in o.bound_box), V()) / 8
                if h1_removed(o.name, (c.y - ALIGN_E, ALIGN_N - c.x)): continue
                s.ctx.objects.link(o)

    def finish(s, a, cams, meta=None):
        tot = sum(len(p.vertices) - 2 for o in s.objs for p in o.data.polygons)
        tm = {}
        for o in s.objs:
            names = [x.name for x in o.data.materials]
            for p in o.data.polygons:
                n = names[p.material_index]; tm[n] = tm.get(n, 0) + len(p.vertices) - 2
        print("TRIS", tot, sorted(tm.items(), key=lambda kv: -kv[1])[:12], "objs", len(s.objs), "build_s", round(time.time() - s.t0), flush=True)
        OUTD = ROOT + r"\output\blocks"; EXP = ROOT + rf"\export\blocks\block_{s.name}"; os.makedirs(EXP, exist_ok=True); os.makedirs(OUTD, exist_ok=True)
        anchors = [x for b in s.S.values() for x in b.anchors]
        json.dump(dict(block=s.name, tris=tot, tris_by_material=tm, anchors=anchors, **(meta or {}),
                       buildings={k: dict(center=[round(b.c.x, 2), round(b.c.y, 2)], size=[round(b.a * 2, 2), round(b.b * 2, 2)], H=b.H, storeys=b.st, base_z=round(b.base, 3), roof=b.roofkind) for k, b in s.S.items()}),
                  open(EXP + rf"\block_{s.name}_meta.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
        if a.export:
            export_glb(s.coll, EXP + rf"\block_{s.name}.glb"); print("GLB", os.path.getsize(EXP + rf"\block_{s.name}.glb") / 1e6, flush=True)
            bpy.ops.wm.save_as_mainfile(filepath=ROOT + rf"\blend\block_{s.name}.blend", compress=True)
        if a.render:
            if a.ctx: s.context(cams.get("_own", (0, 0, 0, 0)))
            setup_render(a.res, a.spp); lighting()
            for n in a.cams.split(","):
                pos, look, lens = cams[n]
                if pos[2] < 3: pos = (pos[0], pos[1], pos[2] + G(pos[0], pos[1]))        # eye height above the real ground
                cam = add_cam(n, pos, look, lens); bpy.context.scene.camera = cam
                bpy.context.scene.render.filepath = OUTD + f"\\{s.name}_{a.tag}_{n}.jpg"
                t1 = time.time(); bpy.ops.render.render(write_still=True); print("RENDER", n, round(time.time() - t1), flush=True)
        print("ALLDONE", round(time.time() - s.t0), flush=True)
        sys.stdout.flush(); os._exit(0)


def _obb_hit(a, b, pad=0.0):
    for ax in (a.ax, a.ay, b.ax, b.ay):
        def span(o):
            c = o.c.dot(ax); r = abs(o.ax.dot(ax)) * o.a + abs(o.ay.dot(ax)) * o.b
            return c - r, c + r
        a0, a1 = span(a); b0, b1 = span(b)
        if a1 + pad <= b0 or b1 + pad <= a0: return False
    return True
