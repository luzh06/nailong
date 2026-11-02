# vm02: 自動販売機, proportions taken from Commons photos (see refs_used.json). Faces -Y. W 1.1, D .72, H 1.83
import sys, os, math, random
sys.path.insert(0, r'D:\Cijian\scripts')
from cj_lib import *
RES = 4096
reset()
random.seed(11)
D = DECAL + os.sep
W, Dp, H = 1.1, .66, 1.83
foot = .05
rain = stain_image('vmrain', 1.2, 1.9, [(.05, 1.15, 1.83, 1.2, .55), (.08, .5, .92, .5, .5), (.86, 1.1, .92, .4, .6), (.2, .95, .34, .2, .6)], splash=.5, seed=3)
stain = (rain, -.6, .6, 0, 1.9)
paint = pbr('paint', 'metal_plate', 1.3, flat_color=(.03, .25, .10), tint_amt=.10, rough=.36, nor=.08, wear=.34, grime=.8, streak=.2, rust=.16, rust_scale=16, rust_tex='rusty_metal_02', edge_col=(.5, .5, .46), coat=.5, stain=stain, stain_col=(.10, .09, .07), stain_amt=.85)
trim = pbr('trim', 'metal_plate', 1.6, flat_color=(.72, .72, .69), tint_amt=.1, rough=.34, nor=.08, wear=.2, grime=.7, streak=.2, stain=stain, stain_col=(.12, .1, .08), stain_amt=.6)
dark = pbr('dark', None, flat_color=(.022, .022, .025), rough=.5, wear=.25, grime=.4, streak=.1, edge_col=(.2, .2, .2))
inner = pbr('inner', None, flat_color=(.86, .87, .88), rough=.5, wear=0, grime=.2, streak=0)
chrome = pbr('chrome', 'metal_plate', 2.0, flat_color=(.72, .72, .72), tint_amt=.2, rough=.26, metal=1.0, nor=.3, wear=.12, grime=.5, streak=.1, rust=.1)
rubber = pbr('rubber', None, flat_color=(.02, .02, .02), rough=.8, wear=.1, grime=.2, streak=0)
panel = pbr('panel', 'metal_plate', 1.3, base_img=D + 'vm2_panel.png', rough=.3, nor=.06, wear=.3, grime=.6, streak=.2, rust=.08, rust_scale=16, coat=.4, stain=stain, stain_col=(.10, .09, .07), stain_amt=.7)
side = pbr('side', 'metal_plate', 1.3, base_img=D + 'vm2_side.png', rough=.34, nor=.06, wear=.2, grime=.6, streak=.3, rust=.08, rust_scale=16, coat=.4)
takeout = pbr('takeout', None, base_img=D + 'vm_takeout.png', rough=.4, wear=.2, grime=.6, streak=.1)
coin = pbr('coin', None, base_img=D + 'vm_coin.png', rough=.4, wear=.2, grime=.4, streak=0)
notice = pbr('notice', None, base_img=D + 'vm_notice.png', rough=.55, wear=.1, grime=.2, streak=.2)
led = pbr('led', None, base_img=D + 'vm_led.png', rough=.2, wear=0, grime=0, streak=0, emit_img=D + 'vm_led.png', emit=1.0)
lamp = pbr('lamp', None, flat_color=(.95, .95, .9), rough=.4, wear=0, grime=0, streak=0, emit=1.0, emit_col=(1, .98, .92))
btn_c = pbr('btn_c', None, flat_color=(.04, .25, .85), rough=.25, wear=0, grime=.1, streak=0, emit=1.0, emit_col=(.006, .05, .42))
btn_h = pbr('btn_h', None, flat_color=(.8, .08, .05), rough=.25, wear=0, grime=.1, streak=0, emit=1.0, emit_col=(.5, .018, .008))
parts = []
A = parts.append
yf = -Dp / 2
dy = yf - .03
def planar_uv(ob, x0, x1, z0, z1):
    me = ob.data
    uv = me.uv_layers['tex']
    for l in me.loops:
        v = ob.matrix_world @ me.vertices[l.vertex_index].co
        uv.data[l.index].uv = ((v.x - x0) / (x1 - x0), (v.z - z0) / (z1 - z0))
# carcass: rear box, front bay hollow
A(box('body', (W, Dp - .26, H - foot - .03), (0, .13, foot + (H - foot - .03) / 2), paint, bv=.012, segs=3))
for sx in (-1, 1):
    A(box('jamb%d' % sx, (.045, .27, H - foot - .03), (sx * (W / 2 - .0225), -.195, foot + (H - foot - .03) / 2), paint, bv=.012, segs=3))
A(box('top', (W + .012, Dp + .03, .035), (0, -.012, H - .0175), trim, bv=.008, segs=3))
wx0, wx1 = -W / 2 + .05, W / 2 - .05
wz0, wz1 = .96, 1.74
A(box('cab_low', (W - .09, .27, wz0 - foot), (0, -.195, foot + (wz0 - foot) / 2), paint, bv=.006))
A(box('cab_top', (W - .09, .27, H - .03 - wz1), (0, -.195, (H - .03 + wz1) / 2), paint, bv=.006))
# door frame round the window, rounded outer corners
A(box('fr_l', (.05, .05, wz1 - wz0 + .1), (-W / 2 + .025, dy, (wz0 + wz1) / 2), paint, bv=.012, segs=3))
A(box('fr_r', (.05, .05, wz1 - wz0 + .1), (W / 2 - .025, dy, (wz0 + wz1) / 2), paint, bv=.012, segs=3))
A(box('fr_t', (W, .05, .07), (0, dy, wz1 + .035), paint, bv=.012, segs=3))
A(box('door_low', (W, .05, wz0 - foot - .05), (0, dy, foot + .05 + (wz0 - foot - .05) / 2), paint, bv=.012, segs=3))
lp = box('low_face', (W - .05, .003, .50), (0, dy - .027, .68), panel, bv=0)
planar_uv(lp, -W / 2 + .025, W / 2 - .025, .43, .93)
A(lp)
# side wrap graphic
for sx in (-1, 1):
    sd = box('sidep%d' % sx, (.003, Dp - .06, 1.5), (sx * (W / 2 + .0016), -.01, .98), side, bv=0)
    me = sd.data
    uv = me.uv_layers['tex']
    for l in me.loops:
        v = sd.matrix_world @ me.vertices[l.vertex_index].co
        u = (v.y + .31) / .62
        uv.data[l.index].uv = (u if sx > 0 else 1 - u, (v.z - .23) / 1.5)
    A(sd)
    for k in range(7):
        A(box('vent', (.006, .2, .007), (sx * (W / 2 + .004), Dp / 2 - .15, .1 + k * .02), dark, bv=.0015))
# plinth + feet + kick damage zone
A(box('plinth', (W - .02, .04, .08), (0, dy - .004, foot + .04), dark, bv=.004))
for sx in (-1, 1):
    for sy in (-1, 1):
        A(cyl('foot', .03, .05, (sx * .47, sy * .26, foot / 2), chrome, verts=16))
# wide take-out, low
A(box('flap_fr', (.70, .03, .17), (-.08, dy - .03, .26), dark, bv=.008, segs=3))
fp = box('flap', (.64, .008, .115), (-.08, dy - .048, .262), takeout, bv=.003, rot=(math.radians(4), 0, 0))
planar_uv(fp, -.40, .24, .2045, .3195)
A(fp)
A(box('flap_grip', (.14, .016, .016), (-.08, dy - .058, .22), rubber, bv=.005, segs=3))
# control cluster: right of the window base
ccx = .405
A(box('cp', (.17, .012, .33), (ccx, dy - .030, .775), dark, bv=.005, segs=3))
cl = box('cp_label', (.14, .002, .07), (ccx, dy - .037, .895), coin, bv=0)
planar_uv(cl, ccx - .07, ccx + .07, .86, .93)
A(cl)
A(box('slot_plate', (.07, .014, .05), (ccx - .035, dy - .037, .815), chrome, bv=.004, segs=3))
A(box('slot', (.004, .006, .03), (ccx - .035, dy - .045, .815), rubber, bv=0))
A(box('bill', (.08, .018, .036), (ccx + .03, dy - .04, .76), dark, bv=.003))
A(box('bill2', (.066, .004, .003), (ccx + .03, dy - .05, .762), rubber, bv=0))
A(box('led_bezel', (.085, .012, .028), (ccx + .02, dy - .037, .852), chrome, bv=.003))
lf = box('led', (.072, .004, .019), (ccx + .02, dy - .044, .852), led, bv=0)
planar_uv(lf, ccx - .016, ccx + .056, .8425, .8615)
A(lf)
A(cyl('ret', .016, .02, (ccx - .05, dy - .043, .72), chrome, verts=20, axis='Y'))
A(box('ret_l', (.011, .011, .036), (ccx - .05, dy - .058, .72), chrome, bv=.004))
A(box('change', (.085, .028, .055), (ccx + .025, dy - .045, .69), dark, bv=.006, segs=3))
# bright display bay
back_y = dy + .20
A(box('in_back', (wx1 - wx0, .01, wz1 - wz0), (0, back_y, (wz0 + wz1) / 2), inner, bv=0))
A(box('in_top', (wx1 - wx0, .22, .01), (0, dy + .10, wz1 + .005), lamp, bv=0))
for sx in (wx0 + .001, wx1 - .001):
    A(box('in_side', (.004, .22, wz1 - wz0), (sx, dy + .10, (wz0 + wz1) / 2), inner, bv=0))
def can(nm, x, y, z, tex):
    b = lathe(nm, [(0, 0), (.0255, 0), (.0275, .004), (.033, .012), (.033, .108), (.0285, .118), (.0265, .122), (.0275, .1235), (.0255, .124), (.0235, .121), (0, .121)], tex, verts=20, loc=(x, y, z), uv_h=(.012, .108))
    b.rotation_euler[2] = random.uniform(-.14, .14)
    return b
def pet(nm, x, y, z, tex):
    p = [(0, 0), (.028, 0), (.0325, .006), (.0325, .03), (.031, .036), (.0325, .042), (.0325, .10), (.031, .118), (.024, .146), (.0155, .160), (.0145, .164)]
    b = lathe(nm, p, tex, verts=20, loc=(x, y, z), uv_h=(.042, .10))
    b.rotation_euler[2] = random.uniform(-.14, .14)
    A(cyl(nm + 'cap', .0165, .016, (x, y, z + .172), caps[random.randrange(4)], verts=14))
    return b
caps = [pbr('cap%d' % i, None, flat_color=c, rough=.4, wear=0, grime=.1, streak=0) for i, c in enumerate([(.75, .75, .72), (.1, .35, .15), (.7, .15, .1), (.1, .2, .6)])]
wraps = [pbr('drink%d' % i, None, base_img=D + 'drink_%02d.png' % i, rough=.26, wear=.04, grime=0, streak=0, spec=.7) for i in range(8)]
rows = [(wz0 + .0, 'pet', 0), (wz0 + .26, 'can', 1), (wz0 + .52, 'can', 2)]
nx = 10
pitch = (wx1 - wx0 - .04) / nx
for rz, kind, ri in rows:
    A(box('shelf%d' % ri, (wx1 - wx0, .17, .006), (0, dy + .105, rz + .058), inner, bv=.0015))
    st = box('strip%d' % ri, (wx1 - wx0 - .005, .004, .024), (0, dy + .02, rz + .045), pbr('price%d' % ri, None, base_img=D + 'price_%d.png' % ri, rough=.3, wear=.03, grime=.1, streak=0), bv=0)
    planar_uv(st, wx0, wx1, rz + .033, rz + .057)
    A(st)
    A(box('stripb%d' % ri, (wx1 - wx0, .018, .048), (0, dy + .03, rz + .02), inner, bv=.002))
    for k in range(nx):
        x = wx0 + .02 + pitch * (k + .5)
        cold = not (ri == 2 and k in (1, 2, 5))
        A(box('b%d%d' % (ri, k), (.042, .012, .013), (x, dy + .017, rz + .016), btn_c if cold else btn_h, bv=.004))
        w = wraps[(k * 3 + ri * 5 + (k // 2)) % 8]
        f = can if kind == 'can' else pet
        A(f('i%d%d' % (ri, k), x, dy + .10, rz + .061, w))
nt_ = box('notice', (.15, .001, .10), (-.42, dy - .0275, .50), notice, bv=0)
planar_uv(nt_, -.495, -.345, .45, .55)
parts.append(nt_)
parts.append(tube('cord', fillet([(.42, Dp / 2 + .01, .12), (.42, Dp / 2 + .1, .05), (.30, Dp / 2 + .22, .012), (-.4, Dp / 2 + .26, .012), (-.62, Dp / 2 + .1, .012)], .05), .0045, rubber, verts=8))
g = glass('vm_glass', alpha=.05, rough=.03)
gp = pane('glass', wx1 - wx0 + .06, wz1 - wz0 + .03, (0, dy - .027, (wz0 + wz1) / 2), g, amp=.0003)
meta = finish(parts, 'vm02', RES, want_emit=True, transparent=[gp], col=[(0, 0, .915, W, .72, 1.83)], origin=(0, 0),
              boost={'led': 3, 'drink': 2.4, 'price': 3, 'panel': 1.3, 'side': .8, 'coin': 3, 'takeout': 1.5, 'notice': 3, 'inner': .3, 'lamp': .2, 'cap': .4},
              sources=['ref:Commons Random vending machine Hakone (CC BY-SA 2.0)', 'ref:Commons Vending Machines in Japan 43679427685 (CC BY 2.0)', 'polyhaven:metal_plate', 'polyhaven:rusty_metal_02', 'font:ZenKakuGothicNew(OFL)', 'font:ReggaeOne(OFL)', 'font:ShipporiMincho(OFL)', 'decals:original'],
              notes='按实拍比例重做；虚构品牌 そよかぜ；原点在机身中心地面')
sys.stdout.flush()
os._exit(0)
