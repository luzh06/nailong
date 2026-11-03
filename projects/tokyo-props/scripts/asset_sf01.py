# sf01: 店面模块（茶舗）. Wall line y=0, street at -Y, centre x=0, width 3.6.
# Four GLBs that snap together with one origin: sf01_front / sf01_awning / sf01_sign / sf01_sign_side
import sys, os, math, random
sys.path.insert(0, r'D:\Cijian\scripts')
from cj_lib import *
which = sys.argv[sys.argv.index('--') + 1]
RES = 4096 if which in ('front', 'awning') else 2048
reset()
random.seed(hash(which) & 255 if False else 23)
D = DECAL + os.sep
SRC = ['font:ShipporiMincho(OFL)', 'font:YujiSyuku(OFL)', 'decals:original']
def planar(ob, x0, x1, z0, z1):
    me = ob.data
    uv = me.uv_layers['tex']
    for l in me.loops:
        v = ob.matrix_world @ me.vertices[l.vertex_index].co
        uv.data[l.index].uv = ((v.x - x0) / (x1 - x0), (v.z - z0) / (z1 - z0))
    return ob
V = math.pi / 2  # planks: grain along Z
cedar = pbr('cedar', 'japanese_cedar_planks', .9, hsv=(.49, .62, .36), tex_rot=True, rough_mul=1.05, nor=1.0, wear=.3, grime=.7, streak=.6, edge_col=(.26, .2, .14))
post_w = pbr('post', 'dark_wooden_planks', 1.1, hsv=(.5, .7, .75), rough_mul=1.0, nor=1.0, wear=.32, grime=.7, streak=.5, edge_col=(.24, .18, .12))
board = pbr('board', 'weathered_planks', .8, hsv=(.5, .75, .8), tex_rot=True, rough_mul=1.0, nor=1.0, wear=.3, grime=.8, streak=.7, edge_col=(.25, .2, .15))

if which == 'front':
    P, G = [], []
    A = P.append
    W = 3.6
    H = 2.56
    concrete = pbr('conc', 'concrete_floor_worn_001', .8, hsv=(.5, .8, .85), wear=.3, grime=.9, streak=.4)
    steel = pbr('steel', 'metal_plate', 3, flat_color=(.5, .5, .48), tint_amt=.2, rough=.4, metal=1, nor=.2, wear=.1, grime=.6, streak=.2, rust=.4)
    brass = pbr('brass', 'metal_plate', 3, flat_color=(.55, .42, .2), tint_amt=.2, rough=.32, metal=1, nor=.2, wear=.2, grime=.7, streak=.1, rust=.15, rust_tex='green_metal_rust')
    dark_in = pbr('dark_in', 'dark_wooden_planks', .8, hsv=(.5, .6, .35), nor=.8, wear=.1, grime=.6, streak=.2)
    shelf_m = pbr('shelf', 'hinoki_planks', .8, hsv=(.5, .7, .6), nor=.7, wear=.2, grime=.5, streak=.1)
    tiles = pbr('tile', 'rectangular_facade_tiles', 1.2, hsv=(.5, .6, .62), nor=1, wear=.15, grime=.8, streak=.5)
    # sill stone and threshold
    A(box('plinth', (W, .22, .10), (0, -.03, .05), concrete, bv=.012, segs=3))
    A(box('rail', (1.96, .036, .012), (.76, -.05, .106), steel, bv=.002))
    # structure
    for x in (-1.75, -.22, 1.75):
        A(box('post%.1f' % x, (.105, .105, H - .1), (x, 0, .1 + (H - .1) / 2), post_w, bv=.008, segs=3, uvrot=V))
    A(box('lintel', (W, .11, .16), (0, 0, 2.18), post_w, bv=.008, segs=3))
    A(box('header', (W, .12, .10), (0, 0, H - .05), post_w, bv=.008, segs=3))
    # transom: thin lattice over frosted glass
    x = -1.68
    while x < 1.7:
        A(box('tr%.2f' % x, (.016, .02, .16), (x, -.02, 2.36), cedar, bv=.002, uvrot=V))
        x += .075
    A(box('tr_h', (W, .022, .014), (0, -.02, 2.36), cedar, bv=.002))
    G.append(pane('g_tr', W, .17, (0, .0, 2.36), None, ny=4))
    # left bay: tiled wainscot and display window
    A(box('wain', (1.43, .05, .66), (-.985, -.02, .43), tiles, bv=.003))
    A(box('wain_cap', (1.46, .10, .03), (-.985, -.03, .775), post_w, bv=.006, segs=3))
    z0, z1 = .79, 2.10
    A(box('wf_l', (.05, .05, z1 - z0), (-1.67, -.02, (z0 + z1) / 2), cedar, bv=.004, uvrot=V))
    A(box('wf_r', (.05, .05, z1 - z0), (-.30, -.02, (z0 + z1) / 2), cedar, bv=.004, uvrot=V))
    A(box('wf_m', (.038, .04, z1 - z0), (-.985, -.02, (z0 + z1) / 2), cedar, bv=.003, uvrot=V))
    A(box('wf_h', (1.40, .036, .03), (-.985, -.02, 1.62), cedar, bv=.003))
    for xx in (-1.325, -.645):
        for k in (1, 2, 3):
            A(box('wf_gr%.2f%d' % (xx, k), (.012, .018, .46), (xx - .15 * 2 + .15 * k * 1.0, -.02, 1.86), cedar, bv=.0015, uvrot=V))
    G.append(pane('g_win', 1.36, z1 - z0, (-.985, -.012, (z0 + z1) / 2), None))
    # interior behind glass
    A(box('in_back', (W - .2, .02, 2.42), (0, .70, 1.31), dark_in, bv=0, uvrot=V))
    A(box('in_floor', (1.5, .7, .02), (-.985, .35, .78), shelf_m, bv=0))
    A(box('in_ceil', (W - .1, .76, .02), (0, .34, 2.47), dark_in, bv=0))
    A(box('in_sl', (.02, .72, 2.42), (-1.72, .35, 1.31), dark_in, bv=0))
    A(box('in_sr', (.02, .72, 2.42), (1.72, .35, 1.31), dark_in, bv=0))
    A(box('in_floor2', (1.9, .72, .02), (.76, .35, .11), concrete, bv=0))
    A(box('in_mid', (.04, .72, 2.3), (-.22, .35, 1.25), dark_in, bv=0))
    # shelves with tins and bags
    tins = [pbr('tin%d' % i, None, base_img=D + 'tin_%d.png' % i, rough=.35, wear=.15, grime=.3, streak=0, spec=.6) for i in range(3)]
    tin_lid = pbr('lid', 'metal_plate', 6, flat_color=(.6, .55, .4), tint_amt=.2, rough=.3, metal=1, nor=.1, wear=.1, grime=.4, streak=0)
    for sz in (.80, 1.20, 1.62):
        A(box('sh%.1f' % sz, (1.32, .30, .022), (-.985, .24, sz + .02), shelf_m, bv=.003))
        x = -1.58
        while x < -.42:
            r = random.choice((.042, .05, .058))
            h = random.choice((.13, .17, .21))
            tn = lathe('tin', [(0, 0), (r, 0), (r, h), (r - .002, h)], random.choice(tins), verts=24, loc=(x, .2 + random.uniform(-.05, .05), sz + .031), uv_h=(0, h))
            tn.rotation_euler[2] = random.uniform(1.2, 1.9)
            A(tn)
            A(cyl('tl', r + .001, .022, (tn.location.x, tn.location.y, sz + .031 + h + .011), tin_lid, verts=24))
            x += r * 2 + random.uniform(.03, .11)
    for sz, xx in ((.80, -.5), (1.20, -1.5)):
        pass
    # shop interior behind the doors: counter, wall shelf, warm pendant
    lampm = pbr('lampm', None, flat_color=(1, .82, .55), rough=.4, wear=0, grime=0, streak=0, emit=1.0, emit_col=(1, .76, .46))
    wallg = pbr('wallg', None, base_img=D + 'sf01_glow.png', rough=.7, wear=0, grime=.3, streak=0, emit_img=D + 'sf01_glow.png', emit=1.0)
    A(planar(box('in_glow', (1.86, .01, 2.1), (.76, .68, 1.2), wallg, bv=0), -.17, 1.69, .15, 2.25))
    A(box('wains', (1.86, .012, .9), (.76, .665, .6), post_w, bv=.002))
    A(box('counter', (1.5, .42, .86), (.84, .42, .54), post_w, bv=.006))
    A(box('countertop', (1.56, .46, .03), (.84, .42, .985), shelf_m, bv=.004))
    for sz in (1.12, 1.45, 1.8):
        A(box('wsh', (1.7, .16, .02), (.76, .59, sz), shelf_m, bv=.003))
        x = .05
        while x < 1.5:
            r = random.choice((.04, .05, .06))
            h = random.choice((.12, .16, .2))
            tn = lathe('wtin', [(0, 0), (r, 0), (r, h), (r - .002, h)], random.choice(tins), verts=16, loc=(x, .59, sz + .011), uv_h=(0, h))
            tn.rotation_euler[2] = random.uniform(1.2, 1.9)
            A(tn)
            x += r * 2 + random.uniform(.03, .14)
    # things on the counter: paper tea bags, a caddy row, a hand scale
    x = .3
    while x < 1.45:
        if abs(x - .98) > .16:
            r = random.choice((.038, .045, .052))
            h = random.choice((.09, .12, .15))
            yy = .38 + random.uniform(-.09, .09)
            tn = lathe('ctin', [(0, 0), (r, 0), (r, h), (r - .002, h)], random.choice(tins), verts=16, loc=(x, yy, 1.0), uv_h=(0, h))
            tn.rotation_euler[2] = random.uniform(1.2, 1.9)
            A(tn)
            A(cyl('tl2', r + .001, .018, (x, yy, 1.0 + h + .009), tin_lid, verts=16))
        x += random.uniform(.1, .2)
    A(cyl('scale', .09, .012, (.98, .36, 1.17), brass, verts=24))
    A(box('scalebase', (.2, .14, .16), (.98, .36, 1.08), steel, bv=.008, segs=3))
    for lx in (.32, 1.2):
        A(tube('wire', [(lx, .3, 2.31), (lx, .3, 2.02)], .0025, steel, 6))
        A(lathe('shade', [(.0, 2.02), (.03, 2.02), (.13, 1.92), (.135, 1.915)], post_w, verts=24, loc=(lx, .3, 0)))
        A(cyl('bulb', .04, .05, (lx, .3, 1.93), lampm, verts=14))
    # paper notices stuck on glass
    p1 = planar(box('paper1', (.26, .001, .39), (-1.42, -.018, 1.18), pbr('p1', 'rough_linen', 3, base_img=D + 'sf01_paper1.png', rough=.8, nor=.2, wear=.05, grime=.2, streak=.25), bv=0), -1.55, -1.29, .985, 1.375)
    A(p1)
    p2 = planar(box('paper2', (.20, .001, .28), (-.56, -.018, 1.08), pbr('p2', 'rough_linen', 3, base_img=D + 'sf01_paper2.png', rough=.8, nor=.2, wear=.05, grime=.2, streak=.25), bv=0), -.66, -.46, .94, 1.22)
    A(p2)
    # right bay: two sliding doors
    def door(cx, y, nm):
        dw, dh = .96, 1.99
        z = .11
        A(box(nm + 'sl', (.05, .036, dh), (cx - dw / 2 + .025, y, z + dh / 2), cedar, bv=.003, uvrot=V))
        A(box(nm + 'sr', (.05, .036, dh), (cx + dw / 2 - .025, y, z + dh / 2), cedar, bv=.003, uvrot=V))
        A(box(nm + 'tp', (dw - .1, .036, .05), (cx, y, z + dh - .025), cedar, bv=.003))
        A(box(nm + 'lk', (dw - .1, .036, .06), (cx, y, z + .03), cedar, bv=.003))
        A(box(nm + 'mid', (dw - .1, .036, .04), (cx, y, z + .66), cedar, bv=.003))
        for k in range(7):
            A(box(nm + 'pan%d' % k, ((dw - .1) / 7 - .002, .012, .58), (cx - (dw - .1) / 2 + (k + .5) * (dw - .1) / 7, y, z + .35), board, bv=.002, uvrot=V))
        # kumiko bars over the glass
        for k in range(1, 4):
            A(box(nm + 'gv%d' % k, (.012, .02, 1.26), (cx - dw / 2 + .05 + k * (dw - .1) / 4, y, z + 1.31), cedar, bv=.0015, uvrot=V))
        for k in range(1, 5):
            A(box(nm + 'gh%d' % k, (dw - .1, .02, .012), (cx, y, z + .68 + k * 1.26 / 5), cedar, bv=.0015))
        G.append(pane(nm + 'gl', dw - .1, 1.27, (cx, y, z + 1.31), None))
        return cx
    door(.26, -.045, 'd1')
    door(1.21, -.012, 'd2')
    # recessed pull
    A(box('pull', (.03, .012, .15), (.69, -.066, 1.05), brass, bv=.004, segs=3))
    A(box('pull2', (.03, .012, .15), (.74, -.033, 1.05), brass, bv=.004, segs=3))
    # noren rod and cloth
    rod_z = 2.07
    A(cyl('rod', .011, 2.0, (.74, -.13, rod_z), cedar, verts=14, axis='X'))
    for sx in (-1, 1):
        A(box('rodb%d' % sx, (.02, .09, .02), (.74 + sx * .96, -.09, rod_z), steel, bv=.003))
    nmat = pbr('noren', 'rough_linen', 2.5, base_img=D + 'sf01_noren.png', img_map=(1 / 1.8, 1 / .62), rough=.85, nor=.6, wear=.05, grime=.35, streak=.5)
    for i, sx in enumerate((-.60, 0, .60)):
        def fn(x, y, x0=sx, i_=i):
            w = .58
            amp = .012 + .022 * (1 - y / .62)
            ripple = amp * math.sin(x * 11 + i_ * 2 + y * 1.5) + .006 * math.sin(x * 29 + y * 4)
            return (.74 + x0 - w / 2 + x, -.14 + ripple, rod_z - .62 + y)
        c = grid('noren%d' % i, .58, .62, 40, 26, fn, nmat)
        uv = c.data.uv_layers['tex']
        for d in uv.data:
            d.uv = (d.uv[0] + (i * .6 + .01), d.uv[1])
        solidify(c, .0012)
        A(c)
        # loops around the rod
        for k in range(3):
            lx = .74 + sx - .24 + k * .24
            A(box('loop', (.05, .03, .05), (lx, -.135, rod_z + .004), nmat, bv=.004))
    g = glass('glass_s', alpha=.08)
    for o in G:
        o.data.materials.clear()
        o.data.materials.append(g)
    finish(P, 'sf01_front', RES, transparent=G, origin=(0, 0), lods=(.4, .12), want_emit=True,
           boost={'wains': .4, 'p1': 3.5, 'p2': 3.5, 'noren': 1.6, 'tin': 1.4, 'dark_in': .3, 'wallg': .3, 'lampm': .3, 'conc': .5},
           col=[(0, .02, H / 2, W, .14, H)],
           sources=['polyhaven:japanese_cedar_planks', 'polyhaven:dark_wooden_planks', 'polyhaven:weathered_planks', 'polyhaven:rectangular_facade_tiles', 'polyhaven:concrete_floor_worn_001', 'polyhaven:hinoki_planks', 'polyhaven:rough_linen', 'polyhaven:metal_plate'] + SRC,
           notes='虚构店名 三径茶舗；门窗+暖帘+橱窗；与 awning/sign 共用原点')

elif which == 'awning':
    P = []
    W = 3.6
    Y0, Z0 = .02, 2.92
    Y1, Z1 = -1.05, 2.50
    L1 = math.hypot(Y1 - Y0, Z1 - Z0)
    DROP = .24
    TOT = L1 + DROP
    frame = pbr('frame', 'metal_plate', 2.5, flat_color=(.14, .15, .14), tint_amt=.2, rough=.5, metal=.0, nor=.2, wear=.35, grime=.7, streak=.3, rust=.5, edge_col=(.3, .28, .26))
    can = pbr('canvas', 'rough_linen', 2.4, base_img=D + 'sf01_awning.png', img_map=(1 / W, 1 / TOT), rough=.82, nor=.9, wear=.0, grime=.65, streak=.9)
    # single sheet from wall to valance hem; sag between the ribs, and a soft fold at the front bar
    RIBS = 4
    def fn(x, y):
        t = y / TOT
        s = t * TOT
        sag = .022 * abs(math.sin(math.pi * x / (W / RIBS))) ** .7 * math.sin(min(s / L1, 1) * math.pi)
        wr = .0028 * math.sin(x * 37 + s * 4) * math.sin(x * 9 + s * 13) + .002 * math.sin(s * 23 + x * 3)
        if s <= L1:
            k = s / L1
            yy = Y0 + (Y1 - Y0) * k
            zz = Z0 + (Z1 - Z0) * k - sag - wr
            return (x - W / 2, yy, zz)
        k = (s - L1) / DROP
        flap = .018 * k * k * math.sin(x * 2.4 + 1) + .005 * math.sin(x * 19) * k
        return (x - W / 2, Y1 - .002 - flap, Z1 - (s - L1) + wr * .3)
    c = grid('canvas', W, TOT, 180, 72, fn, can)
    uv = c.data.uv_layers['tex']
    for d in uv.data:
        d.uv = (d.uv[0], TOT - d.uv[1])  # image top = wall end
    solidify(c, .0016)
    P.append(c)
    # triangular side skirts in the same cloth
    for sx in (-1, 1):
        s = prism('side%d' % sx, [(Y0, Z0), (Y1, Z1), (Y1, Z1 - DROP), (Y0, Z1 - DROP + .1)], .003, pbr('side%d' % sx, 'rough_linen', 2.4, flat_color=(.05, .09, .07), tint_amt=.25, rough=.85, nor=.8, wear=.1, grime=.7, streak=.8), bv=0, plane='YZ', loc=(sx * W / 2, 0, 0))
        P.append(s)
    # steel frame under the cloth
    P.append(tube('front_bar', [(-W / 2, Y1 + .006, Z1 - .012), (W / 2, Y1 + .006, Z1 - .012)], .0135, frame, 12))
    P.append(tube('wall_bar', [(-W / 2, Y0 - .01, Z0 - .03), (W / 2, Y0 - .01, Z0 - .03)], .0135, frame, 12))
    for k in range(RIBS + 1):
        x = -W / 2 + .01 + k * (W - .02) / RIBS
        P.append(tube('rib%d' % k, [(x, Y0 - .01, Z0 - .03), (x, Y1 + .006, Z1 - .012)], .0105, frame, 10))
        P.append(tube('strut%d' % k, [(x, -.55, Z0 - .24), (x, Y0, Z0 - .50)], .0085, frame, 8))
        P.append(box('wplate%d' % k, (.05, .006, .10), (x, .012, Z0 - .50), frame, bv=.002))
        for zz in (-.035, .035):
            P.append(cyl('wbolt', .0065, .006, (x, .007, Z0 - .50 + zz), frame, verts=6, axis='Y', bv=.0006))
    finish(P, 'sf01_awning', RES, origin=(0, 0), lods=(.3, .08), uv_keep=('canvas',), boost={'frame': .5}, col=[(0, -.52, 2.62, W, 1.08, .55)],
           sources=['polyhaven:rough_linen', 'polyhaven:metal_plate', 'polyhaven:rusty_metal_02'] + SRC,
           notes='帆布雨棚，顶到檐口一张布，雨痕和下垂都烘进贴图')

elif which == 'sign':
    P = []
    gold = pbr('gold', 'metal_plate', 5, flat_color=(.70, .50, .18), tint_amt=.2, rough=.34, metal=1, nor=.3, wear=.3, grime=.8, streak=.4, rust=.06, rust_scale=20, rust_tex='green_metal_rust', edge_col=(.2, .15, .1))
    iron = pbr('iron', 'rusty_metal_02', 3, hsv=(.5, .9, .8), rough_mul=1, nor=.8, metal=.0, wear=.1, grime=.5, streak=.3)
    W, H = 3.0, .56
    cz = 3.28
    P.append(box('back', (W, .03, H), (0, -.03, cz), board, bv=.004, segs=2))
    # stacked boards with small gaps
    n = 5
    for k in range(n):
        bh = H / n - .004
        z = cz - H / 2 + (k + .5) * H / n
        off = random.uniform(-.002, .002)
        P.append(box('bd%d' % k, (W - .05, .022, bh), (off, -.054, z), cedar, bv=.003, segs=2))
    for z in (cz + H / 2 + .012, cz - H / 2 - .012):
        P.append(box('fh', (W + .08, .05, .04), (0, -.05, z), post_w, bv=.006, segs=3))
    for sx in (-1, 1):
        P.append(box('fv', (.05, .05, H + .03), (sx * (W / 2 + .015), -.05, cz), post_w, bv=.006, segs=3, uvrot=V))
    txt = '三径茶舗'
    for i, c in enumerate(txt):
        x = (i - 1.5) * .62
        P.append(text3d('t%d' % i, c, 'ShipporiMincho-ExtraBold.ttf', .50, depth=.016, bv=.0018, mat=gold, loc=(x, -.076, cz - .02)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.append(cyl('bolt', .012, .012, (sx * 1.46, -.082, cz + sz * .22), iron, verts=8, axis='Y', bv=.0012))
        for z_ in (.0,):
            P.append(tube('strap%d' % sx, [(sx * 1.2, -.082, cz + H / 2 + .03), (sx * 1.2, -.082, cz + H / 2 + .09), (sx * 1.2, .0, cz + H / 2 + .10)], .004, iron, 6))
    finish(P, 'sf01_sign', RES, origin=(0, 0), lods=(.45, .15), col=[(0, -.04, cz, W + .1, .09, H + .1)],
           sources=['polyhaven:japanese_cedar_planks', 'polyhaven:dark_wooden_planks', 'polyhaven:weathered_planks', 'polyhaven:metal_plate', 'polyhaven:rusty_metal_02', 'polyhaven:green_metal_rust'] + SRC,
           notes='木招牌，字是立体铸字（虚构店名）')

elif which == 'sign_side':
    P = []
    frame = pbr('frame', 'painted_metal_shutter', 2, flat_color=(.04, .04, .045), tint_amt=.2, rough=.45, nor=.2, wear=.35, grime=.7, streak=.5, rust=.5, edge_col=(.3, .28, .26))
    face = pbr('face', None, base_img=D + 'sf01_side.png', img_map=None, rough=.3, wear=.04, grime=.5, streak=.5, emit_img=D + 'sf01_side.png', emit=1.1, spec=.6)
    w, h, t = .36, 1.04, .13
    cx, cz, cy = 1.72, 3.05, -.40
    P.append(box('bx', (t, w, h), (cx, cy, cz), frame, bv=.008, segs=3))
    for sx in (-1, 1):
        f = box('face%d' % sx, (.004, w - .04, h - .04), (cx + sx * (t / 2 + .001), cy, cz), face, bv=0)
        me = f.data
        uv = me.uv_layers['tex']
        for l in me.loops:
            v = f.matrix_world @ me.vertices[l.vertex_index].co
            u = (v.y - (cy - (w - .04) / 2)) / (w - .04)
            uv.data[l.index].uv = (1 - u if sx < 0 else u, (v.z - (cz - (h - .04) / 2)) / (h - .04))
        P.append(f)
    for z in (cz + .34, cz - .34):
        P.append(tube('arm', [(cx, cy + w / 2, z), (cx, .0, z)], .012, frame, 10))
        P.append(box('wp', (.10, .008, .14), (cx, .004, z), frame, bv=.003))
        for k in (-1, 1):
            P.append(cyl('wb', .006, .006, (cx + k * .035, -.002, z + k * .045), frame, verts=6, axis='Y', bv=.0005))
    P.append(tube('conduit', fillet([(cx - .02, cy + w / 2 - .02, cz + h / 2), (cx - .02, cy + w / 2 - .02, cz + h / 2 + .06), (cx - .02, -.01, cz + h / 2 + .06), (cx - .02, -.01, cz + 1.0)], .03), .0065, frame, 8))
    finish(P, 'sf01_sign_side', RES, origin=(0, 0), want_emit=True, boost={'face': 3}, lods=(.45, .15), col=[(cx, cy + .1, cz, t, w + .25, h)],
           sources=['polyhaven:painted_metal_shutter', 'polyhaven:rusty_metal_02'] + SRC,
           notes='灯箱袖看板，双面，Emissive 单独给出')
sys.stdout.flush()
os._exit(0)
