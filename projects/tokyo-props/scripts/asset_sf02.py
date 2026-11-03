# sf02: two-storey shop front at PLATEAU proportions (frontage 5.4 m, 7.4 m tall). Photos: Tokyo Yanaka 2/4, Japan - Tokyo (Yanaka) 9982647795.
# Wall line y=0, street -Y, centre x=0. Pieces share one origin: shell / front / tent / goods
import sys, os, math, random
sys.path.insert(0, r'D:\Cijian\scripts')
from cj_lib import *
which = sys.argv[sys.argv.index('--') + 1]
reset()
random.seed(31)
D = DECAL + os.sep
W, H, F1 = 5.4, 7.4, 2.9
V = math.pi / 2
REFS = ['ref:Commons Tokyo Yanaka 2 (CC BY-SA 4.0)', 'ref:Commons Tokyo Yanaka 4 (CC BY-SA 4.0)', 'ref:Commons Japan - Tokyo (Yanaka) 9982647795 (CC BY 2.0)', 'map:PLATEAU 13106 taito-ku 2025 bldg 53394671 (CC BY 4.0 compatible, see LICENSES)']
FONTS = ['font:ShipporiMincho(OFL)', 'font:YujiSyuku(OFL)', 'font:ZenKakuGothicNew(OFL)', 'decals:original']
def planar(ob, x0, x1, z0, z1):
    me = ob.data
    uv = me.uv_layers['tex']
    for l in me.loops:
        v = ob.matrix_world @ me.vertices[l.vertex_index].co
        uv.data[l.index].uv = ((v.x - x0) / (x1 - x0), (v.z - z0) / (z1 - z0))
    return ob
wood = pbr('wood', 'japanese_cedar_planks', 1.0, hsv=(.49, .62, .5), tex_rot=True, nor=1.0, wear=.32, grime=.8, streak=.5, edge_col=(.3, .24, .17))
wooddk = pbr('wooddk', 'dark_wooden_planks', 1.1, hsv=(.5, .7, 1.0), nor=1.0, wear=.34, grime=.8, streak=.5, edge_col=(.26, .2, .14))
iron = pbr('iron', 'painted_metal_shutter', 3, flat_color=(.05, .055, .06), tint_amt=.15, rough=.5, nor=.2, wear=.4, grime=.7, streak=.3, rust=.5, rust_scale=20, edge_col=(.3, .26, .22))
galv = pbr('galv', 'metal_plate', 2.5, flat_color=(.42, .43, .42), tint_amt=.2, rough=.42, metal=1, nor=.25, wear=.1, grime=.8, streak=.4, rust=.34, rust_scale=14)
pvc = pbr('pvc', None, flat_color=(.5, .5, .47), rough=.42, wear=.08, grime=.7, streak=.6)
if which == 'shell':
    src = [(.1, 5.5, 7.42, 2.6, .85),  # parapet run-off
           (1.2, 4.2, 4.55, 1.6, .9),  # under the window grille
           (.1, 5.5, 3.02, .1, .1), (.5, 1.1, 5.6, 2.4, .5), (4.4, 5.2, 5.2, 2.2, .7)]
    rain = stain_image('rain', 5.6, 7.6, src, splash=0, seed=5, base=.03, cracks=26, crack_w=1.2, crack_v=.75, res=2200)
    st = (rain, -2.8, 2.8, 0, 7.6)
    plaster = pbr('plaster', 'white_plaster_rough_01', .75, hsv=(.5, .4, .98), nor=1.1, wear=.3, grime=.8, streak=.35, stain=st, stain_col=(.14, .12, .095), stain_amt=.95, edge_col=(.5, .47, .42))
    plaster2 = pbr('plaster2', 'painted_plaster_wall', .6, hsv=(.5, .35, .9), nor=1.2, wear=.25, grime=.8, streak=.3, stain=st, stain_col=(.075, .065, .05), stain_amt=.8)
    letter = pbr('letter', 'painted_metal_shutter', 3, flat_color=(.13, .075, .04), tint_amt=.2, rough=.6, nor=.3, wear=.5, grime=.8, streak=.5, edge_col=(.42, .36, .3))
    conc = pbr('conc', 'concrete_floor_worn_001', .8, hsv=(.5, .5, .72), nor=1.3, wear=.4, grime=1.0, streak=.6, stain=st, stain_col=(.06, .05, .04), stain_amt=.8)
    curtain = pbr('curtain', 'rough_linen', 3, flat_color=(.42, .16, .13), tint_amt=.3, rough=.85, nor=.6, wear=0, grime=.3, streak=0)
    frame = pbr('frame', 'metal_plate', 2, flat_color=(.25, .24, .21), tint_amt=.2, rough=.4, metal=.6, nor=.2, wear=.2, grime=.7, streak=.3, rust=.1)
    P, G = [], []
    A = P.append
    wz0, wz1, wx = 4.5, 5.75, 1.4
    # wall in pieces round the window opening, thick enough to read a real reveal
    A(box('w_low', (W, .22, wz0 - F1), (0, .11, (F1 + wz0) / 2), plaster, bv=.006))
    A(box('w_top', (W, .22, H - wz1), (0, .11, (H + wz1) / 2), plaster, bv=.006))
    A(box('w_l', (W / 2 - wx, .22, wz1 - wz0), (-(W / 2 + wx) / 2, .11, (wz0 + wz1) / 2), plaster, bv=.004))
    A(box('w_r', (W / 2 - wx, .22, wz1 - wz0), ((W / 2 + wx) / 2, .11, (wz0 + wz1) / 2), plaster, bv=.004))
    A(box('patch', (.86, .012, 1.05), (1.72, -.006, 3.72), plaster2, bv=.002))
    A(box('patch2', (.5, .01, .34), (-2.1, -.005, 6.5), plaster2, bv=.002))
    A(box('ledge', (W + .08, .34, .17), (0, -.06, F1 + .08), conc, bv=.012, segs=3))
    A(box('ledge2', (W + .02, .24, .07), (0, -.02, F1 + .2), conc, bv=.008, segs=3))
    A(box('cap', (W + .06, .32, .09), (0, .1, H + .03), conc, bv=.012, segs=3))
    A(box('flash', (W + .08, .34, .02), (0, .1, H + .085), galv, bv=.004))
    A(box('sill', (wx * 2 + .3, .2, .07), (0, -.04, wz0 - .03), conc, bv=.012, segs=3))
    A(box('lint', (wx * 2 + .2, .1, .1), (0, -.03, wz1 + .05), conc, bv=.01, segs=3))
    # relief lettering, fictional name
    for i, c in enumerate('三径茶舗'):
        A(text3d('t%d' % i, c, 'ShipporiMincho-ExtraBold.ttf', .66, depth=.05, bv=.006, mat=letter, loc=((i - 1.5) * .92, -.03, 3.72)))
    for i, c in enumerate('電話 〇三 〇〇〇〇 三四一二'):
        if c.strip():
            A(text3d('p%d' % i, c, 'ShipporiMincho-ExtraBold.ttf', .16, depth=.022, bv=.003, mat=letter, loc=((i - 6.5) * .205, -.012, 3.32)))
    for sx in (-1, 1):
        A(lathe('rose', [(0, 0), (.27, 0), (.28, .018), (.24, .03), (.2, .022), (.0, .03)], plaster2, verts=48, loc=(sx * 2.1, -.03, 5.18), axis='Y'))
        for k in range(6):
            a = k * math.pi / 3 + .26
            A(box('rp', (.2, .03, .06), (sx * 2.1 + .13 * math.cos(a), -.05, 5.18 + .13 * math.sin(a)), letter, bv=.008, rot=(0, -a, 0)))
    # window: aluminium sash, curtain behind, iron grille out front with rust runs below it
    for x_ in (-wx + .02, 0, wx - .02):
        A(box('fv', (.05, .07, wz1 - wz0), (x_, .05, (wz0 + wz1) / 2), frame, bv=.004))
    for z_ in (wz0 + .03, wz1 - .03):
        A(box('fh', (wx * 2, .07, .05), (0, .05, z_), frame, bv=.004))
    A(box('curt', (wx * 2, .03, wz1 - wz0), (0, .15, (wz0 + wz1) / 2), curtain, bv=0))
    G.append(pane('g1', wx - .05, wz1 - wz0 - .08, (-wx / 2, .06, (wz0 + wz1) / 2), None))
    G.append(pane('g2', wx - .05, wz1 - wz0 - .08, (wx / 2, .06, (wz0 + wz1) / 2), None))
    gy = -.1
    x = -wx - .08
    while x <= wx + .09:
        A(tube('gv', [(x, gy, wz0 + .02), (x, gy, wz1 - .05)], .0075, iron, 8))
        x += .13
    for z_ in (wz0 + .06, wz0 + .62, wz1 - .1):
        A(tube('gh', [(-wx - .1, gy, z_), (wx + .1, gy, z_)], .009, iron, 8))
    for sx in (-1, 1):
        for z_ in (wz0 + .06, wz1 - .1):
            A(box('gb', (.03, .12, .02), (sx * (wx + .1), gy / 2, z_), iron, bv=.003))
    # downpipe, cables, meter conduit
    pts = fillet([(2.55, -.07, H - .1), (2.55, -.07, F1 + .3), (2.55, -.12, F1 + .15), (2.55, -.12, .06)], .05)
    A(tube('down', pts, .038, pvc, 14))
    for z_ in (6.6, 5.2, 3.9):
        A(box('clip', (.1, .03, .03), (2.55, -.02, z_), galv, bv=.003))
    A(tube('hopper', [(2.55, -.07, H - .1), (2.55, -.07, H - .03)], .06, pvc, 14, True, lambda t: 1 + t * .5))
    for x_, r_ in ((-2.45, .012), (-2.4, .009)):
        A(tube('cond', fillet([(x_, -.015, 2.95), (x_, -.015, 6.9), (x_ + .9, -.015, 7.05), (x_ + .9, -.45, 7.3)], .08), r_, galv if r_ > .01 else iron, 8))
    # air-con on a bracket beside the window
    au = load_model('exterior_aircon_unit', (0, 0, 0))
    bb = [o.matrix_world @ Vector(c) for o in au for c in o.bound_box]
    cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
    cy = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
    z0 = min(v.z for v in bb)
    dep = max(v.y for v in bb) - min(v.y for v in bb)
    for o in au:
        o.data.transform(Matrix.Translation((-2.1 - cx, -.05 - dep / 2 - cy, 3.42 - z0)))
    P += au
    for sx in (-.3, .3):
        A(box('ab', (.03, .42, .03), (-2.1 + sx, -.22, 3.4), iron, bv=.004))
        A(tube('as', [(-2.1 + sx, -.42, 3.4), (-2.1 + sx, -.02, 3.1)], .009, iron, 6))
    A(tube('ad', fillet([(-1.8, -.2, 3.8), (-1.65, -.04, 3.86), (-1.5, -.04, 4.2), (-1.5, -.04, 4.42)], .05), .03, pvc, 10))
    g = glass('shell_g', alpha=.45, tint=(.02, .025, .03), rough=.05)
    for o in G:
        o.data.materials.clear()
        o.data.materials.append(g)
    finish(P, 'sf02_shell', 4096, transparent=G, origin=(0, 0), lods=(.4, .12), uv_keep=(), boost={'curtain': .3, 'letter': 1.5},
           col=[(0, .1, (F1 + H) / 2, W, .3, H - F1)], sources=['polyhaven:worn_cracked_plaster', 'polyhaven:peeling_painted_wall', 'polyhaven:concrete_floor_worn_001', 'polyhaven:exterior_aircon_unit', 'polyhaven:painted_metal_shutter', 'polyhaven:metal_plate', 'polyhaven:rusty_metal_02'] + REFS + FONTS,
           notes='二层立面：浮雕字、铁窗栏、雨痕按真实流向放置')
elif which == 'front':
    conc = pbr('conc', 'concrete_floor_worn_001', .8, hsv=(.5, .5, .7), nor=1.3, wear=.35, grime=1.0, streak=.3)
    tile = pbr('tile', 'rectangular_facade_tiles', 1.3, hsv=(.5, .55, .55), nor=1.2, wear=.15, grime=.9, streak=.5)
    white = pbr('white', 'white_plaster_rough_01', .8, hsv=(.5, .3, 1.0), nor=.6, wear=.1, grime=.5, streak=.2, emit=0)
    inw = pbr('inwall', 'white_plaster_rough_01', .8, base_img=D + 'sf02_inwall.png', rough=.7, nor=.4, wear=0, grime=.4, streak=0, emit_img=D + 'sf02_inwall.png', emit=1.0)
    tubeL = pbr('tubeL', None, flat_color=(.95, .95, .9), rough=.3, wear=0, grime=0, streak=0, emit=1.0, emit_col=(1, .97, .9))
    shelf = pbr('shelf', 'hinoki_planks', .9, hsv=(.5, .7, .72), nor=.8, wear=.25, grime=.6, streak=.1)
    tins = [pbr('tin%d' % i, None, base_img=D + 'tin_%d.png' % i, rough=.33, wear=.15, grime=.3, streak=0, spec=.6) for i in range(3)]
    lid = pbr('lid', 'metal_plate', 6, flat_color=(.6, .55, .4), tint_amt=.2, rough=.3, metal=1, nor=.1, wear=.1, grime=.4, streak=0)
    paper = pbr('paper', 'rough_linen', 3, base_img=D + 'sf01_paper1.png', rough=.8, nor=.2, wear=.05, grime=.3, streak=.3)
    P, G = [], []
    A = P.append
    FH = 2.9
    A(box('step', (W, .24, .09), (0, -.02, .045), conc, bv=.015, segs=3))
    for x in (-2.62, -.42, 2.62):
        A(box('post', (.14, .14, FH), (x, .0, FH / 2), wooddk, bv=.01, segs=3, uvrot=V))
    A(box('head', (W, .16, .3), (0, 0, FH - .15), wooddk, bv=.01, segs=3))
    A(box('rail', (3.04, .1, .012), (1.1, .05, .1), galv, bv=.002))
    # left bay: tile dado, wooden shop window
    A(box('dado', (2.1, .06, .68), (-1.52, -.02, .43), tile, bv=.004))
    A(box('sillw', (2.14, .13, .035), (-1.52, -.03, .79), wooddk, bv=.008, segs=3))
    z0, z1 = .81, 2.56
    for x in (-2.54, -1.52, -.5):
        A(box('wv', (.06, .06, z1 - z0), (x, -.02, (z0 + z1) / 2), wood, bv=.005, uvrot=V))
    for z_ in (z1 - .03, 1.95):
        A(box('wh', (2.1, .05, .045), (-1.52, -.02, z_), wood, bv=.004))
    G.append(pane('gw', 2.04, z1 - z0, (-1.52, -.015, (z0 + z1) / 2), None))
    # sliding sashes pushed left, leaving the right of the bay open
    def sash(cx, y):
        dw, dh = 1.06, 2.42
        z = .11
        for sx in (-1, 1):
            A(box('ss', (.055, .035, dh), (cx + sx * (dw / 2 - .027), y, z + dh / 2), wood, bv=.003, uvrot=V))
        for zz in (.03, .78, dh - .03):
            A(box('st', (dw - .1, .035, .055), (cx, y, z + zz), wood, bv=.003))
        for k in range(6):
            A(box('sp', ((dw - .1) / 6 - .002, .012, .68), (cx - (dw - .1) / 2 + (k + .5) * (dw - .1) / 6, y, z + .4), wooddk, bv=.002, uvrot=V))
        for k in (1, 2, 3):
            A(box('sg', (dw - .1, .018, .012), (cx, y, z + .78 + k * .4), wood, bv=.0015))
        G.append(pane('gs', dw - .1, 1.58, (cx, y, z + 1.6), None))
    sash(.15, .035)
    sash(.93, .07)
    # bright interior seen through the open bay and the glass
    A(planar(box('backw', (5.1, .02, 2.56), (0, 2.1, 1.28), inw, bv=0), -2.55, 2.55, 0, 2.56))
    A(box('floor', (5.1, 2.2, .02), (0, 1.05, .08), conc, bv=0))
    A(box('ceil', (5.1, 2.2, .02), (0, 1.05, 2.62), white, bv=0))
    A(box('side_l', (.02, 2.2, 2.56), (-2.56, 1.05, 1.28), white, bv=0))
    A(box('side_r', (.02, 2.2, 2.56), (2.56, 1.05, 1.28), white, bv=0))
    for x, y in ((-1.5, .8), (1.1, .8), (1.1, 1.6), (-1.5, 1.6)):
        A(box('tubeF', (1.2, .05, .03), (x, y, 2.58), tubeL, bv=.004))
    def stock(x0, x1, y, z):
        x = x0
        while x < x1:
            r, h = random.choice((.04, .05, .06)), random.choice((.1, .14, .19))
            t = lathe('tn', [(0, 0), (r, 0), (r, h), (r - .002, h)], random.choice(tins), verts=16, loc=(x, y + random.uniform(-.05, .05), z), uv_h=(0, h))
            t.rotation_euler[2] = random.uniform(1.2, 1.9)
            A(t)
            A(cyl('tl', r + .001, .02, (x, t.location.y, z + h + .01), lid, verts=16))
            x += r * 2 + random.uniform(.015, .08)
    for z in (.5, .95, 1.4, 1.85):
        A(box('sh', (4.6, .32, .025), (0, 1.9, z), shelf, bv=.003))
        stock(-2.2, 2.2, 1.9, z + .013)
    for x in (-2.0, -.7, .7, 2.0):
        A(box('up', (.04, .34, 2.0), (x, 1.9, 1.05), shelf, bv=.003, uvrot=V))
    A(box('cnt', (1.5, .6, .84), (1.5, 1.05, .5), wooddk, bv=.006, uvrot=V))
    A(box('cntt', (1.56, .66, .03), (1.5, 1.05, .935), shelf, bv=.004))
    stock(.9, 2.1, 1.05, .95)
    # stock in the show window
    for z in (.84, 1.32):
        A(box('ws', (1.94, .34, .02), (-1.52, .24, z), shelf, bv=.003))
        stock(-2.4, -.62, .24, z + .011)
    A(planar(box('paper1', (.3, .001, .45), (-2.05, -.02, 1.75), paper, bv=0), -2.2, -1.9, 1.525, 1.975))
    # meter box and door bell on the post
    pb = load_model('power_box_01', (0, 0, 0))
    bb = [o.matrix_world @ Vector(c) for o in pb for c in o.bound_box]
    sx = max(v.x for v in bb) - min(v.x for v in bb)
    sz = max(v.z for v in bb) - min(v.z for v in bb)
    k = .32 / max(sx, sz)
    cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
    cy = min(v.y for v in bb)
    cz = (min(v.z for v in bb) + max(v.z for v in bb)) / 2
    for o in pb:
        o.data.transform(Matrix.Translation((2.42, -.09, 2.1)) @ Matrix.Scale(k, 4) @ Matrix.Translation((-cx, -cy, -cz)))
    P += pb
    A(tube('mc', fillet([(2.42, -.1, 2.26), (2.42, -.1, 2.7), (2.5, -.1, 2.85)], .04), .011, galv, 8))
    g = glass('front_g', alpha=.08)
    for o in G:
        o.data.materials.clear()
        o.data.materials.append(g)
    finish(P, 'sf02_front', 4096, transparent=G, origin=(0, 0), lods=(.4, .12), want_emit=True,
           boost={'inwall': .35, 'conc': .5, 'white': .2, 'tubeL': .2, 'tin': 1.2, 'paper': 2.5},
           col=[(-1.52, .02, 1.45, 2.3, .2, 2.9), (0, .0, 2.75, W, .2, .3), (.15, .02, 1.3, 1.1, .2, 2.6), (2.62, 0, 1.45, .14, .14, 2.9)],
           sources=['polyhaven:japanese_cedar_planks', 'polyhaven:dark_wooden_planks', 'polyhaven:rectangular_facade_tiles', 'polyhaven:concrete_floor_worn_001', 'polyhaven:white_plaster_rough_01', 'polyhaven:hinoki_planks', 'polyhaven:power_box_01', 'polyhaven:metal_plate'] + REFS + FONTS,
           notes='一层店面：门半开可见亮店内；右侧 1.1 米开口可走进')
elif which == 'tent':
    P = []
    TOTW = 5.2
    Y0, Z0, Y1, Z1 = .0, 3.0, -1.35, 2.36
    L1 = math.hypot(Y1 - Y0, Z1 - Z0)
    DROP = .27
    TOT = L1 + DROP
    rain = stain_image('trn', 5.2, TOT, [(.1, 5.1, TOT, TOT * .75, .55)], splash=0, seed=9)
    can = pbr('canvas', 'rough_linen', 5, base_img=D + 'sf02_tent.png', img_map=(1 / TOTW, 1 / TOT), rough=.3, nor=.12, wear=0, grime=.5, streak=.5, coat=.5, spec=.6)
    RIBS = 5
    def fn(x, y):
        s = y
        ten = abs(math.sin(math.pi * x / (TOTW / RIBS)))
        sag = .016 * ten ** .8 * math.sin(min(s / L1, 1) * math.pi)
        pull = .004 * math.sin(x * 26 + s * 3) * (1 - ten) + .0025 * math.sin(x * 61 - s * 9) * ten
        if s <= L1:
            k = s / L1
            return (x - TOTW / 2, Y0 + (Y1 - Y0) * k, Z0 + (Z1 - Z0) * k - sag - pull)
        k = (s - L1) / DROP
        return (x - TOTW / 2, Y1 - .003 - .012 * k * math.sin(x * 2 + 1), Z1 - (s - L1) + pull * .3)
    c = grid('canvas', TOTW, TOT, 260, 80, fn, can)
    uv = c.data.uv_layers['tex']
    for d_ in uv.data:
        d_.uv = (d_.uv[0], TOT - d_.uv[1])
    solidify(c, .0014)
    P.append(c)
    for sx in (-1, 1):
        P.append(prism('side%d' % sx, [(Y0, Z0), (Y1, Z1), (Y1, Z1 - DROP), (Y0, Z1 - DROP + .1)], .002, pbr('side%d' % sx, 'rough_linen', 5, flat_color=(.03, .14, .36), tint_amt=.1, rough=.32, nor=.1, wear=.05, grime=.6, streak=.7, coat=.4), bv=0, plane='YZ', loc=(sx * TOTW / 2, 0, 0)))
    P.append(tube('bar', [(-TOTW / 2, Y1 + .008, Z1 - .012), (TOTW / 2, Y1 + .008, Z1 - .012)], .017, galv, 12))
    P.append(tube('wbar', [(-TOTW / 2, Y0 - .012, Z0 - .03), (TOTW / 2, Y0 - .012, Z0 - .03)], .017, galv, 12))
    for k in range(RIBS + 1):
        x = -TOTW / 2 + .01 + k * (TOTW - .02) / RIBS
        P.append(tube('rib', [(x, Y0 - .012, Z0 - .03), (x, Y1 + .008, Z1 - .012)], .0125, galv, 10))
        P.append(tube('str', [(x, -.75, 2.62), (x, -.02, 2.44)], .0095, galv, 8))
    # bulbs on a slack line, as on the Yanaka rice shop
    wire = pbr('wire', None, flat_color=(.02, .02, .02), rough=.5, wear=0, grime=.2, streak=0)
    bulb = pbr('bulb', None, flat_color=(.9, .86, .74), rough=.15, wear=0, grime=.3, streak=0, emit=1.0, emit_col=(1, .8, .52))
    pts = [(-2.5 + i * 5.0 / 40, -1.28, 2.32 - .05 * abs(math.sin((i % 8) / 8 * math.pi))) for i in range(41)]
    P.append(tube('line', pts, .003, wire, 6))
    for i in range(4, 40, 4):
        p = pts[i]
        P.append(cyl('hold', .012, .03, (p[0], p[1], p[2] - .02), wire, verts=10))
        P.append(lathe('b', [(0, -.08), (.018, -.074), (.03, -.05), (.03, -.04), (.016, -.012), (.014, 0)], bulb, verts=14, loc=p))
    finish(P, 'sf02_tent', 4096, origin=(0, 0), lods=(.3, .08), uv_keep=('canvas',), keep_top=.78, boost={'galv': .5, 'wire': .3}, want_emit=True, col=[(0, -.68, 2.68, TOTW, 1.4, .6)],
           sources=['polyhaven:rough_linen', 'polyhaven:metal_plate'] + REFS + FONTS, notes='绷紧的 PVC 雨棚，带灯泡线')
elif which == 'goods':
    P = []
    A = P.append
    foam = pbr('foam', 'white_plaster_rough_01', 6, hsv=(.5, .1, 1.3), rough=.72, nor=.5, wear=.3, grime=.6, streak=.1, edge_col=(.82, .82, .78))
    packs = [pbr('pack%d' % i, 'rough_linen', 6, base_img=D + 'pack_%d.png' % i, rough=.62, nor=.15, wear=.1, grime=.2, streak=0) for i in range(4)]
    frameW = pbr('tablew', 'weathered_planks', 1.0, hsv=(.5, .5, .85), tex_rot=True, nor=1, wear=.3, grime=.8, streak=.3)
    # trestle table with paper packs leaning, like the rice sacks on the Yanaka shop
    tx, ty, tz = -1.4, -.62, .62
    A(box('ttop', (1.9, .62, .03), (tx, ty, tz), frameW, bv=.005, uvrot=None))
    for sx in (-1, 1):
        for sy in (-1, 1):
            A(box('tleg', (.05, .05, tz), (tx + sx * .86, ty + sy * .25, tz / 2), frameW, bv=.004, rot=(sy * .1, 0, 0), uvrot=math.pi / 2))
    A(box('tbar', (1.75, .04, .05), (tx, ty - .22, .22), frameW, bv=.004))
    A(box('tbar2', (1.75, .04, .05), (tx, ty + .22, .22), frameW, bv=.004))
    for row, (yy, tilt) in enumerate(((ty + .17, -.32), (ty - .06, -.3))):
        for i in range(9 - row):
            pw, ph = .19, .27
            x = tx - .82 + i * .2 + row * .1
            b = box('pk', (pw, .05, ph), (x, yy, tz + ph / 2 + .01), packs[(i * 3 + row) % 4], bv=.008, rot=(tilt, 0, random.uniform(-.05, .05)))
            me = b.data
            uv = me.uv_layers['tex']
            for l in me.loops:
                v = me.vertices[l.vertex_index].co
                uv.data[l.index].uv = (v.x / pw + .5, v.z / ph + .5)
            A(b)
    # foam fish boxes, cardboard, crates: scanned where Poly Haven has them
    def place(name, loc, rz=0.0, k=1.0):
        ms = load_model(name, (0, 0, 0), rz, k)
        bb = [Vector(c) for o in ms for c in o.bound_box]
        cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
        cy = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
        z0 = min(v.z for v in bb)
        for o in ms:
            o.data.transform(Matrix.Translation((loc[0] - cx, loc[1] - cy, loc[2] - z0)))
        P.extend(ms)
        return (max(v.z for v in bb) - z0)
    for i, (x, y, z) in enumerate(((1.75, -.42, 0), (2.32, -.38, 0), (2.0, -.4, .26))):
        A(box('fb', (.5, .34, .25), (x, y, z + .125), foam, bv=.012, segs=2, rot=(0, 0, random.uniform(-.05, .05))))
        A(box('fl', (.52, .36, .03), (x, y, z + .265), foam, bv=.008))
    place('cardboard_box_01', (.22, -.34, 0), .2)
    place('plastic_crate_01', (2.42, -.34, .55), .1, .8)
    place('potted_plant_01', (2.5, -.9, 0), 0, .7)
    place('potted_plant_02', (-2.5, -.34, 0), 1.2, .75)
    place('planter_pot_clay', (-.22, -.32, 0), 0, .5)
    place('metal_trash_can', (1.1, -.32, 0), .4, .62)
    # standing board on the street
    bd = pbr('board', None, base_img=D + 'sf02_board.png', rough=.5, wear=.25, grime=.6, streak=.4)
    bf = box('aboard', (.45, .014, .68), (.72, -1.05, .44), bd, bv=.002, rot=(.14, 0, .1))
    me = bf.data
    uv = me.uv_layers['tex']
    for l in me.loops:
        v = me.vertices[l.vertex_index].co
        uv.data[l.index].uv = (v.x / .45 + .5, v.z / .68 + .5)
    A(bf)
    A(box('abb', (.45, .014, .68), (.72, -.93, .44), frameW, bv=.002, rot=(-.14, 0, .1)))
    finish(P, 'sf02_goods', 4096, origin=(0, 0), lods=(.4, .12), boost={'pack': 2.2, 'board': 2},
           col=[(-1.4, -.62, .35, 1.95, .66, .7), (2.0, -.4, .28, 1.2, .4, .56), (.72, -1.0, .4, .5, .3, .8)],
           sources=['polyhaven:cardboard_box_01', 'polyhaven:plastic_crate_01', 'polyhaven:potted_plant_01', 'polyhaven:potted_plant_02', 'polyhaven:planter_pot_clay', 'polyhaven:metal_trash_can', 'polyhaven:weathered_planks', 'polyhaven:rough_linen'] + REFS + FONTS,
           notes='门前货摊和杂物，含 Poly Haven 扫描模型')
sys.stdout.flush()
os._exit(0)
