# asset_props.py -- <id> : back-alley props for the street. Origin on the ground under the prop centre; wall-mounted ones have the wall at y=0.
import sys, os, math, random
sys.path.insert(0, r'D:\Cijian\scripts')
from cj_lib import *
pid = sys.argv[sys.argv.index('--') + 1]
reset()
random.seed(hash(pid) % 991)
D = DECAL + os.sep
V = math.pi / 2
P = []
A = P.append
galv = pbr('galv', 'metal_plate', 2.5, flat_color=(.45, .46, .45), tint_amt=.2, rough=.42, metal=1, nor=.25, wear=.1, grime=.8, streak=.4, rust=.34, rust_scale=14)
iron = pbr('iron', 'painted_metal_shutter', 3, flat_color=(.05, .055, .06), tint_amt=.15, rough=.5, nor=.2, wear=.4, grime=.7, streak=.3, rust=.5, rust_scale=20, edge_col=(.3, .26, .22))
pvc = pbr('pvc', None, flat_color=(.6, .6, .57), rough=.42, wear=.08, grime=.7, streak=.6)
def place(name, loc, rz=0.0, k=1.0):
    ms = load_model(name, (0, 0, 0), rz, k)
    bb = [Vector(c) for o in ms for c in o.bound_box]
    cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
    cy = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
    z0 = min(v.z for v in bb)
    for o in ms:
        o.data.transform(Matrix.Translation((loc[0] - cx, loc[1] - cy, loc[2] - z0)))
    P.extend(ms)
    return ms
src, col, notes, origin = [], None, '', None
if pid == 'pr_cone':
    red = pbr('cone', None, flat_color=(.75, .1, .04), rough=.45, wear=.4, grime=.8, streak=.3, edge_col=(.4, .3, .25))
    wht = pbr('refl', None, flat_color=(.85, .85, .82), rough=.3, wear=.4, grime=.8, streak=.2)
    blk = pbr('base', None, flat_color=(.03, .03, .03), rough=.8, wear=.2, grime=.6, streak=0)
    for i in range(2):
        x = i * .5
        A(box('base', (.38, .38, .04), (x, 0, .02), blk, bv=.012, segs=3))
        A(lathe('cone', [(0, .04), (.15, .04), (.15, .06), (.13, .07), (.03, .7), (0, .7)], red, verts=32, loc=(x, 0, 0)))
        for z0, z1 in ((.3, .4), (.5, .58)):
            r0 = .13 - (z0 - .07) / .63 * .1
            r1 = .13 - (z1 - .07) / .63 * .1
            A(lathe('band', [(r0 + .002, z0), (r1 + .002, z1)], wht, verts=32, loc=(x, 0, 0)))
    bar = pbr('bar', None, base_img=D + 'barrier.png', rough=.4, wear=.4, grime=.8, streak=.4)
    b = box('cbar', (.62, .035, .07), (.25, 0, .62), bar, bv=.008)
    me = b.data
    for l in me.loops:
        v = me.vertices[l.vertex_index].co
        me.uv_layers['tex'].data[l.index].uv = (v.x / .62 + .5, v.z / .07 + .5)
    A(b)
    src, notes = [], '雪糕筒两只加横杆'
elif pid == 'pr_barrier':
    bar = pbr('bar', None, base_img=D + 'barrier.png', rough=.45, wear=.45, grime=.85, streak=.5, edge_col=(.6, .58, .52))
    for z in (.85, .45):
        b = box('board', (1.2, .03, .22), (0, 0, z), bar, bv=.01, segs=3)
        me = b.data
        for l in me.loops:
            v = me.vertices[l.vertex_index].co
            me.uv_layers['tex'].data[l.index].uv = (v.x / 1.2 + .5, v.z / .22 + .5)
        A(b)
    for sx in (-1, 1):
        A(tube('leg', [(sx * .55, -.3, 0), (sx * .55, 0, 1.0), (sx * .55, .3, 0)], .016, galv, 10))
        A(box('foot', (.06, .7, .03), (sx * .55, 0, .015), iron, bv=.006))
    notes = 'A 字路障'
elif pid == 'pr_bins':
    blue = pbr('binb', None, flat_color=(.05, .2, .55), rough=.5, wear=.3, grime=.9, streak=.5, edge_col=(.3, .4, .6))
    lid = pbr('lid', None, flat_color=(.85, .85, .8), rough=.5, wear=.2, grime=.8, streak=.3)
    lab = pbr('lab', None, base_img=D + 'vm_notice.png', rough=.6, wear=.1, grime=.5, streak=.3)
    for i in range(2):
        x = i * .52 - .26
        A(box('bin', (.46, .4, .78), (x, 0, .39), blue, bv=.03, segs=4))
        A(box('lid', (.48, .42, .06), (x, 0, .81), lid, bv=.02, segs=3))
        A(lathe('hole', [(0, .842), (.07, .842), (.075, .838)], pvc, verts=24, loc=(x, 0, 0)))
        lb = box('label', (.24, .002, .16), (x, -.201, .55), lab, bv=0)
        me = lb.data
        for l in me.loops:
            v = lb.matrix_world @ me.vertices[l.vertex_index].co
            me.uv_layers['tex'].data[l.index].uv = ((v.x - x) / .24 + .5, (v.z - .55) / .16 + .5)
        A(lb)
    notes = '回收箱一对（罐、瓶）'
elif pid == 'pr_plants':
    rack = pbr('rack', 'weathered_planks', 1.0, hsv=(.5, .5, .85), tex_rot=True, nor=1, wear=.3, grime=.9, streak=.4)
    for z in (.02, .42):
        A(box('rb', (1.1, .34, .03), (0, 0, z + .2), rack, bv=.004))
    for sx in (-1, 1):
        for sy in (-1, 1):
            A(box('rl', (.04, .04, .66), (sx * .52, sy * .15, .33), rack, bv=.004, uvrot=V))
    place('planter_pot_clay', (-.33, 0, .25), 0, .45)
    place('potted_plant_04', (.05, 0, .25), .3, .55)
    place('planter_pot_clay', (.36, .02, .65), .8, .38)
    place('potted_plant_02', (-.25, 0, .65), 1.1, .45)
    src, notes = ['polyhaven:planter_pot_clay', 'polyhaven:potted_plant_04', 'polyhaven:potted_plant_02', 'polyhaven:weathered_planks'], '盆栽架'
elif pid == 'pr_gasmeter':
    pb = place('power_box_01', (0, -.09, 1.15), 0, 1.0)
    bb = [Vector(c) for o in pb for c in o.bound_box]
    k = .34 / max(max(v.x for v in bb) - min(v.x for v in bb), max(v.z for v in bb) - min(v.z for v in bb))
    for o in pb:
        o.data.transform(Matrix.Translation((0, -.09, 1.15)) @ Matrix.Scale(k, 4) @ Matrix.Translation((0, .09, -1.15)))
    yel = pbr('gaspipe', 'metal_plate', 4, flat_color=(.8, .62, .1), tint_amt=.2, rough=.45, metal=.2, nor=.2, wear=.4, grime=.8, streak=.4, rust=.3)
    A(tube('g1', fillet([(-.1, -.05, 0), (-.1, -.05, .95), (-.04, -.05, 1.0)], .05), .016, yel, 10))
    A(tube('g2', fillet([(.1, -.05, 1.0), (.18, -.05, 1.0), (.18, -.05, 2.4)], .05), .016, yel, 10))
    for z in (.4, 1.6, 2.2):
        A(box('clip', (.06, .03, .03), (.18 if z > 1 else -.1, -.02, z), galv, bv=.003))
    A(tube('w', fillet([(-.3, -.02, 2.4), (-.3, -.02, 1.3), (-.12, -.02, 1.25)], .06), .009, pvc, 8))
    src, notes, origin = ['polyhaven:power_box_01'], '墙挂燃气表和管线（墙在 y=0）', (0, 0)
elif pid == 'pr_aircon':
    au = place('exterior_aircon_unit', (0, -.2, .22), 0, 1.0)
    for sx in (-.28, .28):
        A(box('stand', (.04, .45, .04), (sx, -.2, .2), galv, bv=.004))
        A(box('sleg', (.04, .04, .2), (sx, -.36, .1), galv, bv=.004))
        A(box('sleg2', (.04, .04, .2), (sx, -.04, .1), galv, bv=.004))
    A(tube('duct', fillet([(.33, -.15, .5), (.42, -.06, .55), (.42, -.04, 1.6), (.42, .0, 1.62)], .06), .035, pvc, 12))
    A(tube('drain', fillet([(.2, -.3, .22), (.25, -.42, .1), (.6, -.5, .01)], .05), .008, pbr('hose', None, flat_color=(.2, .2, .2), rough=.6, wear=0, grime=.6, streak=0), 8))
    src, notes, origin = ['polyhaven:exterior_aircon_unit'], '落地空调外机，配架子、管罩和排水管（墙在 y=0）', (0, 0)
elif pid == 'pr_laundry':
    cloths = [pbr('cloth%d' % i, 'rough_linen', 4, base_img=D + 'cloth_%d.png' % i, rough=.85, nor=.6, wear=0, grime=.2, streak=.1) for i in range(4)]
    for sx in (-1, 1):
        A(tube('st', [(sx * .9, 0, 0), (sx * .9, 0, 1.55)], .015, galv, 8))
        A(box('sb', (.06, .5, .04), (sx * .9, 0, .02), galv, bv=.004))
    A(tube('pole', [(-.95, 0, 1.55), (.95, 0, 1.55)], .014, pbr('blue', None, flat_color=(.2, .35, .7), rough=.4, wear=.2, grime=.5, streak=.2), 10))
    x = -.82
    while x < .7:
        cw, ch = random.uniform(.3, .5), random.uniform(.4, .75)
        ph = random.random() * 6
        def fn(u, v, x=x, ch=ch, ph=ph):
            return (x + u, .012 * math.sin(u * 9 + ph) + .02 * (v / ch - 1) ** 2, 1.55 - ch + v)
        c = grid('cl', cw, ch, 10, 12, fn, random.choice(cloths))
        solidify(c, .003)
        A(c)
        x += cw + random.uniform(.05, .14)
    notes = '落地晾衣架和衣物'
elif pid == 'pr_sign_side':
    face = pbr('face', None, base_img=D + 'sf01_side.png', rough=.3, wear=.04, grime=.5, streak=.5, emit_img=D + 'sf01_side.png', emit=1.0, spec=.6)
    w, h, t, cy, cz = .34, 1.0, .12, -.38, 3.3
    A(box('bx', (t, w, h), (0, cy, cz), iron, bv=.008, segs=3))
    for sx in (-1, 1):
        f = box('f', (.004, w - .04, h - .04), (sx * (t / 2 + .001), cy, cz), face, bv=0)
        me = f.data
        for l in me.loops:
            v = f.matrix_world @ me.vertices[l.vertex_index].co
            u = (v.y - (cy - (w - .04) / 2)) / (w - .04)
            me.uv_layers['tex'].data[l.index].uv = (u if sx > 0 else 1 - u, (v.z - (cz - (h - .04) / 2)) / (h - .04))
        A(f)
    for z in (cz + .3, cz - .3):
        A(tube('arm', [(0, cy + w / 2, z), (0, 0, z)], .012, iron, 10))
    src, notes, origin = [], '双面灯箱袖看板（墙在 y=0）', (0, 0)
want = pid in ('pr_sign_side',)
finish(P, pid, 2048, origin=origin, lods=(.4, .12), want_emit=want, col=col,
       sources=src + ['polyhaven:metal_plate', 'polyhaven:painted_metal_shutter', 'font:ZenKakuGothicNew(OFL)', 'decals:original'], notes=notes)
sys.stdout.flush()
os._exit(0)
