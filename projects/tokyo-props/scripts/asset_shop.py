# asset_shop.py -- <shop id> <piece shell|front|tent|goods>
# Batch shop builder. Same rules as sf02: wall line y=0, street -Y, centre x=0, all pieces share one origin.
# Styles follow Commons photos of Yanaka shops and PLATEAU frontage widths (4-7 m) and heights (7-10 m).
import sys, os, math, random
sys.path.insert(0, r'D:\Cijian\scripts')
from cj_lib import *
sid, piece = sys.argv[sys.argv.index('--') + 1:][:2]
reset()
random.seed(hash(sid + piece) % 999)
D = DECAL + os.sep
V = math.pi / 2
F1 = 2.9
REFS = ['ref:Commons Tokyo Yanaka 2/4, Yanaka Ginza 2, Japan - Tokyo (Yanaka) 9982647795 (CC BY / BY-SA)', 'map:PLATEAU 13106 taito-ku 2025 bldg 53394671']
FONTS = ['font:ShipporiMincho(OFL)', 'font:YujiSyuku(OFL)', 'font:ZenKakuGothicNew(OFL)', 'decals:original']
S = {
 'sf03': dict(W=5.0, H=7.2, shell='tin', tin='sf03_tin', front='stall', tent=('sf03_tent', (.64, .2, .32)), goods='fish', name='鮮魚 魚辰'),
 'sf04': dict(W=4.5, H=6.6, shell='wood', front='lattice', tent=None, goods='hardware', name='荒物 木村', sign='荒物 木村'),
 'sf05': dict(W=5.8, H=9.2, shell='tiles', front='cafe', tent=('sf05_tent', (.42, .07, .07)), goods='cafe', name='喫茶 ひより'),
 'sf06': dict(W=4.2, H=7.0, shell='balcony', front='shutter', tent=None, goods='closed', name='（空き店舗）'),
 'sf07': dict(W=4.0, H=6.8, shell='wood_dark', front='izakaya', tent=None, goods='izakaya', name='やきとり とり源', sign='とり源'),
 'sf08': dict(W=6.0, H=7.4, shell='tin', tin='sf08_tin', front='stall', tent=('sf08_tent', (.13, .4, .23)), goods='veg', name='青果 八百政'),
}[sid]
W, H = S['W'], S['H']
NAME = sid + '_' + piece
def planar(ob, x0, x1, z0, z1):
    me = ob.data
    uv = me.uv_layers['tex']
    for l in me.loops:
        v = ob.matrix_world @ me.vertices[l.vertex_index].co
        uv.data[l.index].uv = ((v.x - x0) / (x1 - x0), (v.z - z0) / (z1 - z0))
    return ob
def place(P, name, loc, rz=0.0, k=1.0):
    ms = load_model(name, (0, 0, 0), rz, k)
    bb = [Vector(c) for o in ms for c in o.bound_box]
    cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
    cy = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
    z0 = min(v.z for v in bb)
    for o in ms:
        o.data.transform(Matrix.Translation((loc[0] - cx, loc[1] - cy, loc[2] - z0)))
    P.extend(ms)
wood = pbr('wood', 'japanese_cedar_planks', 1.0, hsv=(.49, .62, .5), tex_rot=True, nor=1.0, wear=.32, grime=.8, streak=.5, edge_col=(.3, .24, .17))
wooddk = pbr('wooddk', 'dark_wooden_planks', 1.1, hsv=(.5, .7, 1.0), nor=1.0, wear=.34, grime=.8, streak=.5, edge_col=(.26, .2, .14))
iron = pbr('iron', 'painted_metal_shutter', 3, flat_color=(.05, .055, .06), tint_amt=.15, rough=.5, nor=.2, wear=.4, grime=.7, streak=.3, rust=.5, rust_scale=20, edge_col=(.3, .26, .22))
galv = pbr('galv', 'metal_plate', 2.5, flat_color=(.42, .43, .42), tint_amt=.2, rough=.42, metal=1, nor=.25, wear=.1, grime=.8, streak=.4, rust=.34, rust_scale=14)
alu = pbr('alu', 'metal_plate', 3, flat_color=(.55, .55, .52), tint_amt=.15, rough=.38, metal=.8, nor=.15, wear=.1, grime=.8, streak=.4)
pvc = pbr('pvc', None, flat_color=(.5, .5, .47), rough=.42, wear=.08, grime=.7, streak=.6)
conc = pbr('conc', 'concrete_floor_worn_001', .8, hsv=(.5, .45, .78), nor=1.3, wear=.4, grime=1.0, streak=.5)
curtain = pbr('curtain', 'rough_linen', 3, flat_color=random.choice([(.42, .16, .13), (.55, .5, .38), (.2, .26, .34)]), tint_amt=.3, rough=.85, nor=.6, wear=0, grime=.3, streak=0)
def window(P, G, cx, z0, z1, w, depth=.05, grille=False, cur=True, frame=alu):
    for x_ in (cx - w / 2 + .02, cx, cx + w / 2 - .02):
        P.append(box('fv', (.045, .06, z1 - z0), (x_, depth, (z0 + z1) / 2), frame, bv=.004))
    for z_ in (z0 + .025, z1 - .025):
        P.append(box('fh', (w, .06, .045), (cx, depth, z_), frame, bv=.004))
    if cur:
        P.append(box('curt', (w, .02, z1 - z0), (cx, depth + .12, (z0 + z1) / 2), curtain, bv=0))
    for sx in (-1, 1):
        G.append(pane('g', w / 2 - .05, z1 - z0 - .07, (cx + sx * w / 4, depth + .01, (z0 + z1) / 2), None))
    P.append(box('sill', (w + .14, .14, .05), (cx, depth - .07, z0 - .03), conc, bv=.01, segs=3))
    if grille:
        x = cx - w / 2 - .05
        while x <= cx + w / 2 + .06:
            P.append(tube('gv', [(x, depth - .14, z0 + .02), (x, depth - .14, z1 - .04)], .0065, iron, 8))
            x += .12
        for z_ in (z0 + .05, z1 - .08):
            P.append(tube('gh', [(cx - w / 2 - .08, depth - .14, z_), (cx + w / 2 + .08, depth - .14, z_)], .008, iron, 8))
def wall_stain(cracks=22, extra=()):
    return stain_image('rain', W + .2, H + .2, [(.1, W + .1, H + .2, H * .35, .8)] + list(extra), splash=0, seed=hash(sid) % 97, base=.03, cracks=cracks, crack_w=1.1, crack_v=.7, res=2000)
def finish_glass(P, G, mat=None, **kw):
    g = mat or glass(NAME + '_g', alpha=.35, tint=(.02, .025, .03), rough=.05)
    for o in G:
        o.data.materials.clear()
        o.data.materials.append(g)
    finish(P, NAME, 4096, transparent=G or None, origin=(0, 0), **kw)

# ------------------------------------------------------------------ shells
if piece == 'shell':
    P, G = [], []
    A = P.append
    kind = S['shell']
    st = (wall_stain(), -W / 2 - .1, W / 2 + .1, 0, H + .2)
    src = ['polyhaven:white_plaster_rough_01', 'polyhaven:concrete_floor_worn_001', 'polyhaven:metal_plate', 'polyhaven:painted_metal_shutter']
    if kind == 'tin':
        plaster = pbr('plaster', 'white_plaster_rough_01', .75, hsv=(.5, .35, .9), nor=1.1, wear=.3, grime=.8, streak=.35, stain=st, stain_col=(.14, .12, .095), stain_amt=.95)
        A(box('wall', (W, .22, H - F1), (0, .11, (F1 + H) / 2), plaster, bv=.006))
        # corrugated sign panel nailed over the whole upper floor; two windows punched through
        z0, z1 = F1 + .2, F1 + 2.2
        tinm = pbr('tin', 'painted_metal_shutter', 1.0, base_img=D + S['tin'] + '.png', img_map=(1 / W, 1 / (z1 - z0)), rough=.4, nor=.25, wear=.3, grime=.8, streak=.7, rust=.35, rust_scale=12, coat=.3,
                   stain=st, stain_col=(.22, .12, .06), stain_amt=.7, edge_col=(.5, .46, .4))
        def corr(x, y):
            return (x - W / 2, -.04 - .011 * math.sin(x * 2 * math.pi / .076), y + z0)
        pn = grid('tin', W, z1 - z0, int(W / .019), 24, corr, tinm)
        solidify(pn, .0012)
        A(pn)
        for zz in (z0 - .02, z1 + .02):
            A(box('tedge', (W + .04, .07, .04), (0, -.04, zz), galv, bv=.004))
        for x_ in [(-W / 2 + .3 + i * (W - .6) / 7) for i in range(8)]:
            for zz in (z0 + .1, z1 - .1):
                A(cyl('nail', .007, .006, (x_, -.058, zz), galv, verts=8, axis='Y', bv=.0008))
        window(P, G, -W * .22, z1 + .45, H - .45, 1.5, grille=True)
        window(P, G, W * .25, z1 + .45, H - .45, 1.1)
        A(box('cap', (W + .06, .3, .08), (0, .1, H + .02), conc, bv=.012, segs=3))
        A(box('ledge', (W + .06, .32, .15), (0, -.05, F1 + .07), conc, bv=.012, segs=3))
        src += ['polyhaven:painted_metal_shutter (corrugated tin)']
    elif kind in ('wood', 'wood_dark'):
        dk = kind == 'wood_dark'
        siding = pbr('siding', 'weathered_plank_siding', .8, hsv=(.5, .55, .55 if dk else .85), nor=1.3, wear=.3, grime=.9, streak=.7, stain=st, stain_col=(.05, .04, .03), stain_amt=.8, edge_col=(.3, .26, .2))
        tile = pbr('rooft', 'grey_roof_tiles', .9, hsv=(.5, .4, .7), nor=1.4, wear=.2, grime=.8, streak=.6)
        A(box('wall', (W, .2, H - F1), (0, .1, (F1 + H) / 2), siding, bv=.006, uvrot=V))
        for x_ in (-W / 2 + .06, W / 2 - .06):
            A(box('pil', (.12, .14, H - F1), (x_, -.02, (F1 + H) / 2), wooddk, bv=.008, segs=3, uvrot=V))
        # small tiled pent roof (hisashi) over the shop front, and the main eave
        for zb, dep in ((F1 + .25, .62), (H - .15, .75)):
            r = box('hisashi', (W + .2, dep, .06), (0, -dep / 2 + .08, zb), tile, bv=.006, rot=(math.radians(-16), 0, 0))
            A(r)
            A(box('fascia', (W + .22, .03, .1), (0, -dep + .1, zb - .17), wooddk, bv=.004))
            for x_ in [(-W / 2 + .2 + i * (W - .4) / 6) for i in range(7)]:
                A(box('rafter', (.06, dep, .06), (x_, -dep / 2 + .08, zb - .09), wooddk, bv=.004, rot=(math.radians(-16), 0, 0)))
        # mushiko-style slatted window
        zc0, zc1 = F1 + .8, H - .75
        A(box('frame', (W * .62, .08, zc1 - zc0 + .1), (0, -.01, (zc0 + zc1) / 2), wooddk, bv=.006))
        A(box('back', (W * .6, .02, zc1 - zc0), (0, .05, (zc0 + zc1) / 2), pbr('plw', 'white_plaster_rough_01', .8, hsv=(.5, .3, .55), nor=.8, wear=0, grime=.9, streak=.4), bv=0))
        x = -W * .3 + .05
        while x < W * .3:
            A(box('slat', (.035, .05, zc1 - zc0), (x, -.04, (zc0 + zc1) / 2), wooddk, bv=.004, uvrot=V))
            x += .09
        if S.get('sign'):
            bd = box('sboard', (min(2.4, W * .6), .05, .48), (0, -.13, F1 + .62), wooddk, bv=.008, segs=3)
            A(bd)
            pnt = pbr('spaint', 'painted_metal_shutter', 4, flat_color=(.86, .84, .78), tint_amt=.15, rough=.6, nor=.2, wear=.5, grime=.7, streak=.4)
            txt = S['sign']
            for i, c in enumerate(txt):
                if c.strip():
                    A(text3d('st', c, 'ShipporiMincho-ExtraBold.ttf', .32, depth=.006, bv=.0012, mat=pnt, loc=((i - (len(txt) - 1) / 2) * .38, -.158, F1 + .6)))
        src += ['polyhaven:weathered_plank_siding', 'polyhaven:grey_roof_tiles', 'polyhaven:dark_wooden_planks']
    elif kind == 'tiles':
        tiles = pbr('tiles', 'long_white_tiles', .9, hsv=(.5, .35, .82), nor=1.2, wear=.15, grime=.8, streak=.6, stain=st, stain_col=(.16, .13, .1), stain_amt=.9)
        A(box('wall', (W, .22, H - F1), (0, .11, (F1 + H) / 2), tiles, bv=.006))
        for fl in range(2):
            zb = F1 + .9 + fl * 3.0
            window(P, G, -W * .22, zb, zb + 1.35, 1.6)
            window(P, G, W * .26, zb, zb + 1.35, 1.2, grille=(fl == 0))
            A(box('band', (W + .04, .08, .14), (0, -.03, zb - .55), conc, bv=.01, segs=3))
        # projecting vertical lightbox on a bracket
        bx = pbr('boxface', None, base_img=D + 'sf05_box.png', rough=.3, wear=.04, grime=.5, streak=.5, emit_img=D + 'sf05_box.png', emit=1.0, spec=.6)
        cx, cz, cy, w, h, t = W / 2 - .35, F1 + 2.6, -.42, .36, 1.5, .13
        A(box('bx', (t, w, h), (cx, cy, cz), iron, bv=.008, segs=3))
        for sx in (-1, 1):
            f = box('bxf', (.004, w - .04, h - .04), (cx + sx * (t / 2 + .001), cy, cz), bx, bv=0)
            me = f.data
            uv = me.uv_layers['tex']
            for l in me.loops:
                v = f.matrix_world @ me.vertices[l.vertex_index].co
                u = (v.y - (cy - (w - .04) / 2)) / (w - .04)
                uv.data[l.index].uv = (u if sx > 0 else 1 - u, (v.z - (cz - (h - .04) / 2)) / (h - .04))
            A(f)
        for z_ in (cz + .5, cz - .5):
            A(tube('arm', [(cx, cy + w / 2, z_), (cx, 0, z_)], .012, iron, 10))
        A(box('cap', (W + .06, .3, .08), (0, .1, H + .02), conc, bv=.012, segs=3))
        A(box('ledge', (W + .06, .32, .15), (0, -.05, F1 + .07), conc, bv=.012, segs=3))
        src += ['polyhaven:long_white_tiles']
    elif kind == 'balcony':
        plaster = pbr('plaster', 'painted_plaster_wall', .65, hsv=(.5, .45, .85), nor=1.2, wear=.3, grime=.85, streak=.4, stain=st, stain_col=(.13, .11, .09), stain_amt=.95)
        A(box('wall', (W, .22, H - F1), (0, .11, (F1 + H) / 2), plaster, bv=.006))
        window(P, G, 0, F1 + 1.0, F1 + 3.0, 2.2, cur=True)
        # steel balcony with laundry pole and hanging washing
        bz = F1 + .95
        A(box('slab', (W - .3, .75, .1), (0, -.37, bz - .05), conc, bv=.01, segs=3))
        for x in [(-W / 2 + .2 + i * .11) for i in range(int((W - .4) / .11) + 1)]:
            A(tube('bal', [(x, -.72, bz), (x, -.72, bz + 1.0)], .007, iron, 6))
        A(tube('rail', [(-W / 2 + .15, -.72, bz + 1.0), (W / 2 - .15, -.72, bz + 1.0)], .016, iron, 8))
        for sx in (-1, 1):
            A(tube('rails', [(sx * (W / 2 - .15), -.72, bz + 1.0), (sx * (W / 2 - .15), 0, bz + 1.0)], .016, iron, 8))
        A(tube('pole', [(-W / 2 + .3, -.45, bz + 1.6), (W / 2 - .3, -.45, bz + 1.6)], .014, alu, 10))
        cloths = [pbr('cloth%d' % i, 'rough_linen', 4, base_img=D + 'cloth_%d.png' % i, rough=.85, nor=.6, wear=0, grime=.2, streak=.1) for i in range(4)]
        x = -W / 2 + .5
        while x < W / 2 - .6:
            cw, ch = random.uniform(.35, .6), random.uniform(.45, .8)
            ph = random.random() * 6
            def fn(u, v, cw=cw, ch=ch, x=x, ph=ph):
                return (x + u, -.45 + .015 * math.sin(u * 9 + ph) + .02 * (v / ch - 1) ** 2, bz + 1.6 - ch + v)
            c = grid('cl', cw, ch, 10, 12, fn, random.choice(cloths))
            solidify(c, .003)
            A(c)
            A(box('peg', (.012, .02, .04), (x + .05, -.45, bz + 1.6), pvc, bv=.003))
            x += cw + random.uniform(.06, .2)
        au = load_model('exterior_aircon_unit')
        bb = [o.matrix_world @ Vector(c) for o in au for c in o.bound_box]
        cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
        cy = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
        for o in au:
            o.data.transform(Matrix.Translation((W / 2 - .65 - cx, -.36 - cy, bz - min(v.z for v in bb))))
        P += au
        A(box('cap', (W + .06, .3, .08), (0, .1, H + .02), conc, bv=.012, segs=3))
        src += ['polyhaven:painted_plaster_wall', 'polyhaven:exterior_aircon_unit', 'polyhaven:rough_linen']
    # common: downpipe and conduit
    A(tube('down', fillet([(W / 2 - .12, -.07, H - .05), (W / 2 - .12, -.07, F1 + .3), (W / 2 - .12, -.12, F1 + .15), (W / 2 - .12, -.12, .06)], .05), .036, pvc, 14))
    A(tube('cond', fillet([(-W / 2 + .1, -.015, F1 + .1), (-W / 2 + .1, -.015, H - .3), (-W / 2 + .6, -.015, H - .2), (-W / 2 + .6, -.4, H + .1)], .08), .011, galv, 8))
    finish_glass(P, G, lods=(.4, .12), boost={'curtain': .3, 'cloth': 1.2, 'boxface': 2.0, 'tin': 1.3},
                 col=[(0, .1, (F1 + H) / 2, W, .3, H - F1)], sources=src + REFS + FONTS, notes=S['name'] + '：二层立面')

# ------------------------------------------------------------------ fronts
elif piece == 'front':
    P, G = [], []
    A = P.append
    kind = S['front']
    white = pbr('white', 'white_plaster_rough_01', .8, hsv=(.5, .3, 1.0), nor=.6, wear=.1, grime=.5, streak=.2)
    tubeL = pbr('tubeL', None, flat_color=(.95, .95, .9), rough=.3, wear=0, grime=0, streak=0, emit=1.0, emit_col=(1, .97, .9))
    shelf = pbr('shelf', 'hinoki_planks', .9, hsv=(.5, .7, .72), nor=.8, wear=.25, grime=.6, streak=.1)
    A(box('step', (W, .24, .09), (0, -.02, .045), conc, bv=.015, segs=3))
    for x in (-W / 2 + .07, W / 2 - .07):
        A(box('post', (.14, .14, F1), (x, 0, F1 / 2), wooddk, bv=.01, segs=3, uvrot=V))
    A(box('head', (W, .16, .3), (0, 0, F1 - .15), wooddk, bv=.01, segs=3))
    # every shop gets a lit interior box behind its front
    inside = (pbr('inw', 'white_plaster_rough_01', .8, hsv=(.5, .3, .62), nor=.4, wear=0, grime=.5, streak=0))
    A(box('backw', (W - .2, .02, F1 - .3), (0, 2.0, (F1 - .3) / 2), inside, bv=0))
    A(box('floor', (W - .2, 2.0, .02), (0, 1.0, .08), conc, bv=0))
    A(box('ceil', (W - .2, 2.0, .02), (0, 1.0, F1 - .3), white, bv=0))
    for sx in (-1, 1):
        A(box('side', (.02, 2.0, F1 - .3), (sx * (W / 2 - .1), 1.0, (F1 - .3) / 2), inside, bv=0))
    src = ['polyhaven:dark_wooden_planks', 'polyhaven:concrete_floor_worn_001', 'polyhaven:white_plaster_rough_01', 'polyhaven:hinoki_planks']
    if kind == 'stall':
        # open stall: no glazing, tiered display boards stepping up toward the back, tubes overhead
        foam = pbr('foam', 'white_plaster_rough_01', 6, hsv=(.5, .1, 1.3), rough=.72, nor=.5, wear=.3, grime=.6, streak=.1, edge_col=(.82, .82, .78))
        for i, (dy, dz) in enumerate(((-.1, .55), (.35, .78), (.8, 1.0))):
            A(box('tier', (W - .5, .48, .04), (0, dy, dz), shelf, bv=.004))
            A(box('tierf', (W - .5, .03, dz), (0, dy - .24, dz / 2), wooddk, bv=.004))
            x = -W / 2 + .45
            while x < W / 2 - .45:
                A(box('fb', (.42, .3, .13), (x, dy, dz + .085), foam, bv=.01, rot=(0, 0, random.uniform(-.04, .04))))
                x += .46
        for x in (-W / 4, W / 4):
            A(box('tube', (1.2, .05, .03), (x, .6, F1 - .34), tubeL, bv=.004))
        # reed screens rolled half down at both ends
        sud = pbr('sudare', 'bamboo_wall' if os.path.exists(os.path.join(PH, 'bamboo_wall')) else 'weathered_planks', 2.5, hsv=(.5, .6, 1.1), tex_rot=True, rough=.8, nor=.8, wear=.1, grime=.6, streak=.4)
        for sx in (-1, 1):
            def fn(u, v, sx=sx):
                return (sx * (W / 2 - .2) - sx * u, -.12 + .012 * math.sin(u * 30), F1 - .4 - v)
            s_ = grid('sud', .9, 1.5, 30, 10, fn, sud)
            solidify(s_, .004)
            A(s_)
            A(cyl('roll', .03, .92, (sx * (W / 2 - .65), -.12, F1 - .36), sud, verts=12, axis='X'))
        src += ['polyhaven:weathered_planks']
    elif kind == 'lattice':
        # fixed kōshi lattice on the left, sliding glazed door on the right with a short noren
        lx0, lx1 = -W / 2 + .14, .2
        A(box('kbase', (lx1 - lx0, .08, .45), ((lx0 + lx1) / 2, -.01, .32), wooddk, bv=.006))
        x = lx0 + .03
        while x < lx1:
            A(box('ks', (.03, .05, 1.95), (x, -.03, 1.52), wood, bv=.003, uvrot=V))
            x += .065
        for z_ in (.55, 1.5, 2.48):
            A(box('kr', (lx1 - lx0, .05, .04), ((lx0 + lx1) / 2, -.01, z_), wood, bv=.003))
        A(box('kback', (lx1 - lx0, .02, 2.0), ((lx0 + lx1) / 2, .2, 1.5), white, bv=0))
        dx0, dx1 = lx1 + .06, W / 2 - .14
        for sx in (dx0 + .03, dx1 - .03):
            A(box('ds', (.05, .04, 2.4), (sx, .02, 1.3), wood, bv=.003, uvrot=V))
        for z_ in (.13, 1.0, 2.48):
            A(box('dr', (dx1 - dx0, .04, .05), ((dx0 + dx1) / 2, .02, z_), wood, bv=.003))
        G.append(pane('dg', dx1 - dx0 - .08, 1.42, ((dx0 + dx1) / 2, .02, 1.75), None))
        A(box('dpan', (dx1 - dx0 - .06, .015, .82), ((dx0 + dx1) / 2, .02, .57), wooddk, bv=.002, uvrot=V))
        nm = pbr('noren', 'rough_linen', 2.5, flat_color=(.08, .12, .24), tint_amt=.3, rough=.85, nor=.6, wear=.05, grime=.4, streak=.4)
        def fn(u, v):
            return ((dx0 + dx1) / 2 - .5 + u, -.1 + .01 * math.sin(u * 12) * (1 - v / .55), F1 - .3 - .55 + v)
        n_ = grid('noren', 1.0, .55, 30, 14, fn, nm)
        solidify(n_, .0012)
        A(n_)
        A(cyl('rod', .01, 1.1, ((dx0 + dx1) / 2, -.1, F1 - .28), wooddk, verts=10, axis='X'))
    elif kind == 'cafe':
        # wood-framed shop window and a glazed door with gilt lettering, deep reveal
        brick = pbr('brick', 'brick_wall_001', 1.2, hsv=(.5, .7, .75), nor=1.2, wear=.2, grime=.8, streak=.4)
        A(box('dado', (W - .3, .1, .7), (0, -.03, .35), brick, bv=.006))
        wx0, wx1 = -W / 2 + .2, W / 2 - 1.35
        A(box('wf', (wx1 - wx0, .1, .08), ((wx0 + wx1) / 2, -.03, .74), wooddk, bv=.008, segs=3))
        for x in (wx0, (wx0 + wx1) / 2, wx1):
            A(box('wv', (.07, .08, F1 - 1.1), (x, -.02, .74 + (F1 - 1.1) / 2), wooddk, bv=.006, uvrot=V))
        A(box('wt', (wx1 - wx0, .08, .07), ((wx0 + wx1) / 2, -.02, F1 - .37), wooddk, bv=.006))
        G.append(pane('wg', wx1 - wx0 - .06, F1 - 1.2, ((wx0 + wx1) / 2, -.01, .74 + (F1 - 1.1) / 2), None))
        gold = pbr('gold', 'metal_plate', 6, flat_color=(.8, .62, .3), tint_amt=.2, rough=.3, metal=1, nor=.1, wear=.3, grime=.3, streak=0)
        for i, c in enumerate('珈琲 ひより'):
            if c.strip():
                A(text3d('gl', c, 'ShipporiMincho-ExtraBold.ttf', .16, depth=.002, bv=0, mat=gold, loc=((wx0 + wx1) / 2 + (i - 2.5) * .2, -.025, 1.85)))
        dx0, dx1 = W / 2 - 1.25, W / 2 - .2
        for x in (dx0, dx1):
            A(box('df', (.07, .1, 2.35), (x, .1, 1.18), wooddk, bv=.006, uvrot=V))
        A(box('dtop', (dx1 - dx0, .1, .07), ((dx0 + dx1) / 2, .1, 2.35), wooddk, bv=.006))
        G.append(pane('dg', dx1 - dx0 - .1, 1.5, ((dx0 + dx1) / 2, .12, 1.4), None))
        A(box('dkick', (dx1 - dx0 - .08, .04, .55), ((dx0 + dx1) / 2, .12, .38), wooddk, bv=.004, uvrot=V))
        A(tube('dhandle', [(dx0 + .15, .06, 1.0), (dx0 + .15, .06, 1.35)], .012, gold, 8))
        warm = pbr('warm', None, flat_color=(1, .8, .55), rough=.4, wear=0, grime=0, streak=0, emit=1.0, emit_col=(1, .72, .42))
        for x in (-W / 4, W / 6):
            A(lathe('shade', [(0, 2.3), (.03, 2.3), (.16, 2.14), (.165, 2.13)], wooddk, verts=20, loc=(x, .8, 0)))
            A(cyl('bulb', .05, .06, (x, .8, 2.15), warm, verts=12))
        for x in (-W / 3, 0):
            A(box('table', (.6, .6, .03), (x, .9, .72), wooddk, bv=.005))
            A(cyl('tleg', .03, .7, (x, .9, .36), iron, verts=10))
        src += ['polyhaven:brick_wall_001']
    elif kind == 'shutter':
        # roll shutter two thirds down, slots and dents; dark interior below
        sh = pbr('shut', 'painted_metal_shutter', .9, hsv=(.5, .4, .9), nor=1.2, wear=.4, grime=.9, streak=.8, rust=.4, rust_scale=10)
        zb = .95
        def fn(u, v):
            return (u - (W - .3) / 2, -.07 - .006 * math.sin(v * 2 * math.pi / .065) + .004 * math.sin(u * 3.1), zb + v)
        g_ = grid('shut', W - .3, F1 - .3 - zb, 60, int((F1 - .3 - zb) / .016), fn, sh)
        solidify(g_, .002)
        A(g_)
        A(box('slat_b', (W - .3, .06, .05), (0, -.07, zb), galv, bv=.006))
        A(box('box_top', (W, .35, .32), (0, -.1, F1 - .16), sh, bv=.01))
        for sx in (-1, 1):
            A(box('guide', (.06, .08, F1 - .3), (sx * (W / 2 - .17), -.07, (F1 - .3) / 2), galv, bv=.004))
        for nm_, xx, zz, w_, h_ in (('sf06_notice', -.7, 1.65, .42, .6), ('sf06_closed', .6, 1.4, .36, .25)):
            m_ = pbr(nm_, 'rough_linen', 3, base_img=D + nm_ + '.png', rough=.8, nor=.2, wear=.08, grime=.4, streak=.4)
            A(planar(box('paper', (w_, .001, h_), (xx, -.082, zz), m_, bv=0), xx - w_ / 2, xx + w_ / 2, zz - h_ / 2, zz + h_ / 2))
        src += ['polyhaven:painted_metal_shutter']
    elif kind == 'izakaya':
        # dark board front, small hatch window, sliding door with red noren, lanterns either side
        dx0, dx1 = .1, W / 2 - .3
        # boarded wall only left of the doorway, plus the strip above it
        A(box('board', (dx0 + W / 2 - .15, .06, F1 - .3), ((dx0 - W / 2 + .15) / 2, .0, (F1 - .3) / 2), wooddk, bv=.006, uvrot=V))
        A(box('board_r', (W / 2 - .15 - dx1, .06, F1 - .3), ((dx1 + W / 2 - .15) / 2, .0, (F1 - .3) / 2), wooddk, bv=.006, uvrot=V))
        A(box('board_t', (dx1 - dx0, .06, F1 - .3 - 2.3), ((dx0 + dx1) / 2, .0, 2.3 + (F1 - .3 - 2.3) / 2), wooddk, bv=.006, uvrot=V))
        A(box('hatch', (1.0, .08, .7), (-W / 4, -.03, 1.35), wood, bv=.008))
        G.append(pane('hg', .9, .6, (-W / 4, -.07, 1.35), None))
        # open doorway: real depth behind it, a counter and a warm pendant instead of a flat glowing card
        warm = pbr('warm', None, flat_color=(1, .8, .55), rough=.4, wear=0, grime=0, streak=0, emit=1.0, emit_col=(1, .62, .3))
        A(box('cnt', (dx1 - dx0 - .1, .5, 1.0), ((dx0 + dx1) / 2, 1.3, .55), wooddk, bv=.006, uvrot=V))
        A(box('cntt', (dx1 - dx0, .56, .04), ((dx0 + dx1) / 2, 1.3, 1.07), wood, bv=.004))
        A(lathe('shade', [(0, 2.45), (.03, 2.45), (.14, 2.3), (.145, 2.29)], wooddk, verts=20, loc=((dx0 + dx1) / 2, .9, 0)))
        A(cyl('bulb', .05, .06, ((dx0 + dx1) / 2, .9, 2.3), warm, verts=12))
        for k in range(5):
            A(cyl('stool', .14, .04, (dx0 + .25 + k * .32, .85, .66), wooddk, verts=16))
            A(cyl('sleg', .02, .64, (dx0 + .25 + k * .32, .85, .32), iron, verts=8))
        for x in (dx0, dx1):
            A(box('df', (.06, .06, 2.3), (x, -.04, 1.15), wood, bv=.004, uvrot=V))
        nm = pbr('noren', 'rough_linen', 2.5, base_img=D + 'sf07_noren.png', img_map=(1 / (dx1 - dx0 + .1), 1 / .75), rough=.85, nor=.6, wear=.05, grime=.4, streak=.4)
        def fn(u, v):
            return (dx0 - .05 + u, -.12 + .012 * math.sin(u * 14) * (1 - v / .75), F1 - .32 - .75 + v)
        n_ = grid('noren', dx1 - dx0 + .1, .75, 36, 16, fn, nm)
        solidify(n_, .0012)
        A(n_)
        lan = pbr('lantern', 'rough_linen', 4, base_img=D + 'sf07_lantern.png', rough=.6, nor=.3, wear=0, grime=.3, streak=.2, emit_img=D + 'sf07_lantern.png', emit=1.0)
        for x in (-W / 2 + .4, dx0 - .2):
            prof = [(.0, -.30), (.08, -.30), (.15, -.25), (.18, -.15), (.19, 0), (.18, .15), (.15, .25), (.08, .30), (0, .30)]
            A(lathe('lan', prof, lan, verts=24, loc=(x, -.3, F1 - .75), uv_h=(-.30, .30)))
            A(cyl('lcap', .085, .04, (x, -.3, F1 - .43), iron, verts=16))
            A(cyl('lcap2', .085, .04, (x, -.3, F1 - 1.07), iron, verts=16))
            A(tube('lh', [(x, -.3, F1 - .41), (x, -.3, F1 - .3), (x, 0, F1 - .3)], .006, iron, 6))
    finish_glass(P, G, mat=glass(NAME + '_g', alpha=.08), lods=(.4, .12), want_emit=True,
                 boost={'inw': .3, 'white': .2, 'conc': .5, 'tubeL': .2, 'shut': 1.2, 'noren': 1.4, 'lantern': 1.5, 'sf06': 3, 'gold': 1.5},
                 col=[(0, 0, F1 / 2, W, .3, F1)], sources=src + REFS + FONTS, notes=S['name'] + '：一层店面（' + kind + '）')

# ------------------------------------------------------------------ tent
elif piece == 'tent':
    if not S['tent']:
        print('[cj] no tent for', sid, flush=True)
        os._exit(0)
    tex, sidec = S['tent']
    P = []
    TW = W - .2
    Y0, Z0, Y1, Z1 = .0, 3.0, -1.3, 2.38
    L1 = math.hypot(Y1 - Y0, Z1 - Z0)
    DROP = .27
    TOT = L1 + DROP
    can = pbr('canvas', 'rough_linen', 5, base_img=D + tex + '.png', img_map=(1 / TW, 1 / TOT), rough=.32, nor=.12, wear=0, grime=.55, streak=.6, coat=.5, spec=.6)
    RIBS = max(3, int(TW / 1.05))
    def fn(x, s):
        ten = abs(math.sin(math.pi * x / (TW / RIBS)))
        sag = .018 * ten ** .8 * math.sin(min(s / L1, 1) * math.pi)
        pull = .004 * math.sin(x * 26 + s * 3) * (1 - ten) + .0025 * math.sin(x * 61 - s * 9) * ten
        if s <= L1:
            k = s / L1
            return (x - TW / 2, Y0 + (Y1 - Y0) * k, Z0 + (Z1 - Z0) * k - sag - pull)
        k = (s - L1) / DROP
        return (x - TW / 2, Y1 - .003 - .012 * k * math.sin(x * 2 + 1), Z1 - (s - L1) + pull * .3)
    c = grid('canvas', TW, TOT, int(TW * 50), 80, fn, can)
    for d_ in c.data.uv_layers['tex'].data:
        d_.uv = (d_.uv[0], TOT - d_.uv[1])
    solidify(c, .0014)
    P.append(c)
    for sx in (-1, 1):
        P.append(prism('side', [(Y0, Z0), (Y1, Z1), (Y1, Z1 - DROP), (Y0, Z1 - DROP + .1)], .002, pbr('side%d' % sx, 'rough_linen', 5, flat_color=sidec, tint_amt=.1, rough=.32, nor=.1, wear=.05, grime=.6, streak=.7, coat=.4), bv=0, plane='YZ', loc=(sx * TW / 2, 0, 0)))
    P.append(tube('bar', [(-TW / 2, Y1 + .008, Z1 - .012), (TW / 2, Y1 + .008, Z1 - .012)], .017, galv, 12))
    P.append(tube('wbar', [(-TW / 2, Y0 - .012, Z0 - .03), (TW / 2, Y0 - .012, Z0 - .03)], .017, galv, 12))
    for k in range(RIBS + 1):
        x = -TW / 2 + .01 + k * (TW - .02) / RIBS
        P.append(tube('rib', [(x, Y0 - .012, Z0 - .03), (x, Y1 + .008, Z1 - .012)], .0125, galv, 10))
        P.append(tube('str', [(x, -.75, 2.62), (x, -.02, 2.44)], .0095, galv, 8))
    finish(P, NAME, 4096, origin=(0, 0), lods=(.3, .08), uv_keep=('canvas',), keep_top=.78, boost={'galv': .5}, col=[(0, -.66, 2.68, TW, 1.35, .6)],
           sources=['polyhaven:rough_linen', 'polyhaven:metal_plate'] + REFS + FONTS, notes=S['name'] + '：PVC 雨棚')

# ------------------------------------------------------------------ goods
elif piece == 'goods':
    P = []
    A = P.append
    kind = S['goods']
    src = []
    if kind in ('fish', 'veg'):
        # produce / fish trays on the tiers, priced with paper tags
        cols = [(.85, .32, .1), (.2, .45, .12), (.75, .12, .08), (.9, .7, .2), (.35, .2, .4)] if kind == 'veg' else [(.55, .58, .62), (.7, .35, .3), (.82, .82, .8), (.45, .5, .55)]
        mats = [pbr('pr%d' % i, None, flat_color=c, rough=.35 if kind == 'fish' else .5, wear=0, grime=.15, streak=0, coat=.6 if kind == 'fish' else .2, spec=.6) for i, c in enumerate(cols)]
        ice = pbr('ice', 'white_plaster_rough_01', 8, hsv=(.5, .1, 1.4), rough=.15, nor=.4, wear=0, grime=0, streak=0, coat=1)
        eye = pbr('eye', None, flat_color=(.02, .02, .02), rough=.05, wear=0, grime=0, streak=0, coat=1)
        if kind == 'fish':
            mats = [pbr('pr%d' % i, None, flat_color=c, rough=.22, metal=.55, wear=0, grime=.1, streak=0, coat=.8, spec=.7) for i, c in enumerate([(.62, .66, .7), (.5, .55, .6), (.72, .5, .45), (.58, .6, .56)])]
        for (dy, dz) in ((-.1, .55), (.35, .78), (.8, 1.0)):
            x = -W / 2 + .45
            while x < W / 2 - .45:
                m = random.choice(mats)
                if kind == 'veg':
                    for k in range(random.randint(5, 9)):
                        r = random.uniform(.035, .055)
                        b = lathe('fruit', [(0, -r), (r * .7, -r * .7), (r, 0), (r * .7, r * .7), (0, r)], m, verts=12, loc=(x + random.uniform(-.16, .16), dy + random.uniform(-.1, .1), dz + .15 + r))
                        A(b)
                else:
                    A(box('icebed', (.38, .26, .02), (x, dy, dz + .16), ice, bv=.004))
                    for k in range(3):
                        # fish lying on its side on crushed ice: flattened body, tail fin, eye
                        fl = random.uniform(.22, .3)
                        fx, fy, fz = x - .1 + k * .1, dy + random.uniform(-.03, .03), dz + .185
                        bd = lathe('fish', [(0, -fl / 2), (.02, -fl * .42), (.036, -fl * .2), (.038, 0), (.03, fl * .22), (.012, fl * .42), (.006, fl / 2)], m, verts=14, loc=(fx, fy, fz), axis='Y')
                        bd.rotation_euler = (math.pi / 2, 0, random.uniform(-.25, .25))
                        bd.scale = (1, 1, 1)
                        bd.data.transform(Matrix.Scale(.42, 4, (1, 0, 0)))
                        A(bd)
                        A(prism('tail', [(-.035, 0), (.035, 0), (0, -.055)], .004, m, bv=0, plane='XY', loc=(fx, fy + fl / 2 + .02, fz)))
                        A(cyl('eye', .006, .004, (fx + .014, fy - fl * .38, fz + .004), eye, verts=8, axis='X', bv=0))
                tag = pbr('tag', None, flat_color=(.95, .93, .86), rough=.8, wear=0, grime=.2, streak=0)
                A(box('tag', (.08, .004, .05), (x + .12, dy - .16, dz + .19), tag, bv=0, rot=(-.3, 0, 0)))
                x += .46
        place(P, 'plastic_crate_02', (-W / 2 + .45, -.55, 0), .2, .9)
        place(P, 'plastic_crate_01', (-W / 2 + .45, -.55, .3), .1, .9)
        place(P, 'cardboard_box_01', (W / 2 - .5, -.5, 0), .3)
        src += ['polyhaven:plastic_crate_01', 'polyhaven:plastic_crate_02', 'polyhaven:cardboard_box_01']
    elif kind == 'hardware':
        place(P, 'plastic_broom', (-W / 2 + .35, -.22, 0), 0, 1.0)
        place(P, 'plastic_broom', (-W / 2 + .5, -.2, 0), .4, 1.0)
        place(P, 'plastic_bottle_gallon', (.0, -.4, 0), .3)
        place(P, 'plastic_crate_01', (.7, -.45, 0), .1, .9)
        place(P, 'cardboard_box_01', (1.25, -.4, 0), .5, .9)
        bucket = pbr('bucket', 'metal_plate', 4, flat_color=(.55, .56, .55), tint_amt=.2, rough=.35, metal=1, nor=.2, wear=.2, grime=.6, streak=.1, rust=.2)
        for k in range(3):
            A(lathe('bucket', [(0, 0), (.12, 0), (.15, .26), (.155, .265)], bucket, verts=24, loc=(.65 + k * .05, -.42, .3 + k * .05)))
        src += ['polyhaven:plastic_broom', 'polyhaven:plastic_bottle_gallon', 'polyhaven:plastic_crate_01', 'polyhaven:cardboard_box_01']
    elif kind == 'cafe':
        place(P, 'planter_pot_clay', (-W / 2 + .4, -.3, 0), 0, .6)
        place(P, 'planter_pot_clay', (W / 2 - 1.45, -.3, 0), .5, .5)
        place(P, 'standing_chalkboard_01', (-.4, -.75, 0), .3, .9)
        bench = pbr('bench', 'weathered_planks', 1.0, hsv=(.5, .5, .85), tex_rot=True, nor=1, wear=.3, grime=.8, streak=.3)
        A(box('bench', (1.4, .32, .04), (-1.0, -.35, .44), bench, bv=.005))
        for sx in (-1, 1):
            A(box('bleg', (.05, .28, .42), (-1.0 + sx * .6, -.35, .21), bench, bv=.004, uvrot=V))
        src += ['polyhaven:planter_pot_clay', 'polyhaven:standing_chalkboard_01', 'polyhaven:weathered_planks']
    elif kind == 'closed':
        place(P, 'trashbag', (-W / 2 + .5, -.3, 0), .5)
        place(P, 'trashbag', (-W / 2 + .9, -.28, 0), 2.0, .85)
        place(P, 'planter_pot_clay', (W / 2 - .5, -.28, 0), .2, .45)
        place(P, 'plastic_crate_02', (W / 2 - .95, -.3, 0), .1, .85)
        src += ['polyhaven:trashbag', 'polyhaven:planter_pot_clay', 'polyhaven:plastic_crate_02']
    elif kind == 'izakaya':
        place(P, 'plastic_crate_02', (-W / 2 + .45, -.3, 0), 0, .9)
        place(P, 'plastic_crate_02', (-W / 2 + .45, -.3, .3), .1, .9)
        place(P, 'plastic_crate_01', (-W / 2 + .95, -.32, 0), .05, .9)
        place(P, 'planter_pot_clay', (W / 2 - .35, -.28, 0), 0, .5)
        src += ['polyhaven:plastic_crate_01', 'polyhaven:plastic_crate_02', 'polyhaven:planter_pot_clay']
    finish(P, NAME, 2048, origin=(0, 0), lods=(.4, .12), col=[(0, -.5, .5, W, .8, 1.0)], sources=src + REFS, notes=S['name'] + '：门前货物与杂物')
sys.stdout.flush()
os._exit(0)
