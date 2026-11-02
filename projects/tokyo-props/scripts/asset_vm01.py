# vm01: 自動販売機 (fictional brand). Faces -Y. W 1.0, D .72, H 1.83
import sys, os, math, random
sys.path.insert(0, r'D:\Cijian\scripts')
import importlib, cj_lib
importlib.reload(cj_lib)
from cj_lib import *
RES = 4096
reset()
random.seed(11)
D = DECAL + os.sep
paint = pbr('paint', 'metal_plate', 1.3, flat_color=(.80, .80, .76), tint_amt=.10, rough=.40, nor=.10, wear=.3, grime=.85, streak=.42, rust=.2, rust_scale=11, rust_tex='rusty_metal_02', edge_col=(.45, .42, .38), coat=.3)
paint2 = pbr('paint2', 'metal_plate', 1.3, flat_color=(.05, .19, .36), tint_amt=.25, rough=.38, nor=.2, wear=.22, grime=.5, streak=.3, rust=.12, rust_scale=11, coat=.3)
dark = pbr('dark', None, flat_color=(.03, .03, .035), rough=.55, wear=.25, grime=.3, streak=.1, edge_col=(.2, .2, .2))
inner = pbr('inner', None, flat_color=(.78, .80, .82), rough=.55, wear=0, grime=.25, streak=0)
chrome = pbr('chrome', 'metal_plate', 2.0, flat_color=(.72, .72, .72), tint_amt=.2, rough=.3, metal=1.0, nor=.3, wear=.12, grime=.5, streak=.1, rust=.12)
rubber = pbr('rubber', None, flat_color=(.02, .02, .02), rough=.8, wear=.1, grime=.2, streak=0)
panel = pbr('panel', 'metal_plate', 1.3, base_img=D + 'vm_panel.png', rough=.35, nor=.08, wear=.28, grime=.5, streak=.3, rust=.12, rust_scale=11, coat=.2)
header = pbr('header', None, base_img=D + 'vm_header.png', rough=.3, wear=.08, grime=.3, streak=.25, emit_img=D + 'vm_header.png', emit=1.0)
takeout = pbr('takeout', None, base_img=D + 'vm_takeout.png', rough=.45, wear=.2, grime=.5, streak=.1)
coin = pbr('coin', None, base_img=D + 'vm_coin.png', rough=.4, wear=.2, grime=.4, streak=0)
notice = pbr('notice', None, base_img=D + 'vm_notice.png', rough=.55, wear=.1, grime=.2, streak=.2)
led = pbr('led', None, base_img=D + 'vm_led.png', rough=.2, wear=0, grime=0, streak=0, emit_img=D + 'vm_led.png', emit=1.0)
lamp = pbr('lamp', None, flat_color=(.95, .95, .9), rough=.4, wear=0, grime=0, streak=0, emit=5.0, emit_col=(1, .97, .9))
btn_c = pbr('btn_c', None, flat_color=(.04, .25, .85), rough=.25, wear=0, grime=.1, streak=0, emit=1.0, emit_col=(.006, .05, .42))
btn_h = pbr('btn_h', None, flat_color=(.8, .08, .05), rough=.25, wear=0, grime=.1, streak=0, emit=1.0, emit_col=(.5, .018, .008))
parts, glassy = [], []
A = parts.append
W, Dp, H = 1.0, .66, 1.83
foot = .05
yf = -Dp / 2  # front plane of the cabinet
# cabinet shell
# rear cabinet only; the display bay in front of it is left hollow
A(box('body', (W, Dp - .26, H - foot - .03), (0, .13, foot + (H - foot - .03) / 2), paint, bv=.008, segs=3))
for sx in (-1, 1):
    A(box('jamb%d' % sx, (.05, .27, H - foot - .03), (sx * (W / 2 - .025), -.195, foot + (H - foot - .03) / 2), paint, bv=.008, segs=3))
A(box('cab_low', (W - .1, .27, .68), (0, -.195, foot + .34), paint, bv=.006))
A(box('cab_top', (W - .1, .27, .12), (0, -.195, H - .09), paint, bv=.006))
A(box('top', (W + .012, Dp + .012, .03), (0, 0, H - .015), paint, bv=.006, segs=3))
# ribbed side skins
for sx in (-1, 1):
    A(box('skin%d' % sx, (.004, Dp - .08, H - .25), (sx * (W / 2 + .002), 0, foot + (H - .2) / 2 + .02), paint, bv=.0015))
    for k in range(9):
        z = .16 + k * .022
        A(box('vent%d%d' % (sx, k), (.006, .24, .008), (sx * (W / 2 + .005), Dp / 2 - .17, z), dark, bv=.0015))
# back corner ribs, hinge
for z in (.45, 1.0, 1.55):
    A(cyl('hinge%d' % z, .011, .09, (W / 2 + .004, yf - .012, z), chrome, verts=12))
# front door frame around the window, proud of the cabinet
dy = yf - .03
wx0, wx1 = -W / 2 + .05, W / 2 - .05
wz0, wz1 = .72, 1.70
A(box('fr_l', (wx0 + W / 2, .06, wz1 - wz0 + .1), ((wx0 - W / 2) / 2, dy, (wz0 + wz1) / 2), paint, bv=.006, segs=3))
A(box('fr_r', (W / 2 - wx1, .06, wz1 - wz0 + .1), ((wx1 + W / 2) / 2, dy, (wz0 + wz1) / 2), paint, bv=.006, segs=3))
hd = box('hdr', (W, .07, .10), (0, dy - .005, 1.76), paint2, bv=.008, segs=3)
A(hd)
hp = box('hdr_face', (W - .05, .004, .082), (0, dy - .042, 1.76), header, bv=0)
A(hp)
def planar_uv(ob, x0, x1, z0, z1):
    me = ob.data
    uv = me.uv_layers['tex']
    for l in me.loops:
        v = ob.matrix_world @ me.vertices[l.vertex_index].co
        uv.data[l.index].uv = ((v.x - x0) / (x1 - x0), (v.z - z0) / (z1 - z0))
planar_uv(hp, -.475, .475, 1.719, 1.801)
# lower door with graphic
A(box('door_low', (W, .06, wz0 - .07 - foot), (0, dy, (wz0 - .05 + foot) / 2 + .0), paint, bv=.007, segs=3))
lp = box('low_face', (W - .05, .003, .42), (0, dy - .032, .49), panel, bv=0)
A(lp)
planar_uv(lp, -.475, .475, .28, .70)
# plinth / kick plate, feet
A(box('plinth', (W - .02, .04, .10), (0, dy - .006, foot + .05), dark, bv=.004))
for sx in (-1, 1):
    for sy in (-1, 1):
        A(cyl('foot', .03, .05, (sx * .42, sy * .26, foot / 2), chrome, verts=16))
        A(cyl('foot2', .016, .03, (sx * .42, sy * .26, foot + .01), chrome, verts=10))
# take-out flap
A(box('flap_fr', (.62, .05, .19), (-.1, dy - .012, .235), dark, bv=.006, segs=3))
fp = box('flap', (.56, .008, .135), (-.1, dy - .04, .237), takeout, bv=.003, rot=(math.radians(4), 0, 0))
A(fp)
planar_uv(fp, -.38, .18, .1695, .3045)
A(box('flap_grip', (.16, .018, .018), (-.1, dy - .05, .205), rubber, bv=.006, segs=3))
# control cluster on lower door right
ccx = .36
A(box('cp', (.18, .012, .30), (ccx, dy - .036, .50), dark, bv=.005, segs=3))
cl = box('cp_label', (.15, .002, .075), (ccx, dy - .043, .60), coin, bv=0)
A(cl)
planar_uv(cl, ccx - .075, ccx + .075, .5625, .6375)
A(box('slot_plate', (.075, .014, .05), (ccx - .035, dy - .043, .515), chrome, bv=.004, segs=3))
A(box('slot', (.004, .006, .03), (ccx - .035, dy - .051, .515), rubber, bv=0))
A(box('bill', (.085, .018, .038), (ccx + .03, dy - .045, .46), dark, bv=.003))
A(box('bill2', (.07, .004, .003), (ccx + .03, dy - .055, .462), rubber, bv=0))
A(box('led_bezel', (.09, .012, .03), (ccx + .02, dy - .043, .55), chrome, bv=.003))
lf = box('led', (.075, .004, .02), (ccx + .02, dy - .05, .55), led, bv=0)
planar_uv(lf, ccx - .0175, ccx + .0575, .54, .56)
A(lf)
A(cyl('ret', .017, .022, (ccx - .05, dy - .05, .42), chrome, verts=20, axis='Y'))
A(box('ret_l', (.012, .012, .04), (ccx - .05, dy - .066, .42), chrome, bv=.004))
A(box('change', (.09, .03, .06), (ccx + .02, dy - .05, .39), dark, bv=.006, segs=3))
# interior of the display: back, top lamp, shelves
back_y = dy + .22
A(box('in_back', (wx1 - wx0, .01, wz1 - wz0), (0, back_y, (wz0 + wz1) / 2), inner, bv=0))
A(box('in_top', (wx1 - wx0, .24, .012), (0, dy + .11, wz1 + .006), inner, bv=0))
A(box('in_bot', (wx1 - wx0, .24, .012), (0, dy + .11, wz0 - .006), inner, bv=0))
for sx in (wx0 + .001, wx1 - .001):
    A(box('in_side', (.004, .24, wz1 - wz0), (sx, dy + .11, (wz0 + wz1) / 2), inner, bv=0))
A(box('lamp1', (.86, .03, .012), (0, dy + .06, wz1 - .012), lamp, bv=.003))
rows = [(.745, 'pet', 0), (1.07, 'can', 1), (1.385, 'can', 2)]
def can(nm, x, y, z, tex):
    b = lathe(nm, [(0, 0), (.0255, 0), (.0275, .004), (.033, .012), (.033, .108), (.0285, .118), (.0265, .122), (.0275, .1235), (.0255, .124), (.0235, .121), (0, .121)], tex, verts=24, loc=(x, y, z), uv_h=(.012, .108))
    b.rotation_euler[2] = random.uniform(-.18, .18)
    return b
def pet(nm, x, y, z, tex):
    p = [(0, 0), (.028, 0), (.0325, .006), (.0325, .03), (.031, .036), (.0325, .042), (.0325, .13), (.031, .15), (.024, .178), (.0155, .192), (.0145, .196)]
    b = lathe(nm, p, tex, verts=24, loc=(x, y, z), uv_h=(.042, .13))
    b.rotation_euler[2] = random.uniform(-.18, .18)
    A(cyl(nm + 'cap', .0165, .018, (x, y, z + .204), pbr('cap' + nm, None, flat_color=random.choice([(.75, .75, .72), (.1, .35, .15), (.7, .15, .1), (.1, .2, .6)]), rough=.4, wear=0, grime=.1, streak=0), verts=16))
    return b
wraps = []
for i in range(8):
    wraps.append(pbr('drink%d' % i, None, base_img=D + 'drink_%02d.png' % i, rough=.28, metal=.0, wear=.04, grime=0, streak=0, spec=.7))
nx = 10
pitch = (wx1 - wx0 - .02) / nx
for rz, kind, ri in rows:
    A(box('shelf%d' % ri, (wx1 - wx0, .19, .008), (0, dy + .115, rz + .085), inner, bv=.002))
    strip = box('strip%d' % ri, (wx1 - wx0 - .005, .005, .03), (0, dy + .02, rz + .070), pbr('price%d' % ri, None, base_img=D + 'price_%d.png' % ri, rough=.3, wear=.03, grime=.1, streak=0), bv=0)
    A(strip)
    planar_uv(strip, wx0, wx1, rz + .055, rz + .085)
    A(box('stripb%d' % ri, (wx1 - wx0, .02, .06), (0, dy + .03, rz + .03), inner, bv=.002))
    for k in range(nx):
        x = wx0 + .01 + pitch * (k + .5)
        cold = not (ri == 2 and k in (1, 2, 5))
        A(box('b%d%d' % (ri, k), (.05, .014, .016), (x, dy + .017, rz + .032), btn_c if cold else btn_h, bv=.004, segs=2))
        w = wraps[(k * 3 + ri * 5 + (k // 2)) % 8]
        if kind == 'can':
            A(can('c%d%d' % (ri, k), x, dy + .11, rz + .089, w))
        else:
            A(pet('p%d%d' % (ri, k), x, dy + .11, rz + .089, w))
# upper row of tall bottles sits under the top lamp
for k in range(nx):
    x = wx0 + .01 + pitch * (k + .5)
    w = wraps[(k * 5 + 2) % 8]
    A(pet('t%d' % k, x, dy + .11, 1.48, w) if False else None)
parts = [p for p in parts if p]
# sticker, conduit + plug
nt_ = box('notice', (.16, .001, .107), (-.38, dy - .0305 - .002, .625), notice, bv=0)
parts.append(nt_)
planar_uv(nt_, -.46, -.30, .5715, .6785)
parts.append(tube('cord', fillet([(.42, Dp / 2 + .01, .12), (.42, Dp / 2 + .1, .05), (.30, Dp / 2 + .22, .012), (-.4, Dp / 2 + .26, .012), (-.62, Dp / 2 + .1, .012)], .05), .0045, rubber, verts=8))
# window glass
g = glass('vm_glass', alpha=.07, rough=.03)
gp = pane('glass', wx1 - wx0, wz1 - wz0, (0, dy - .012, (wz0 + wz1) / 2), g, amp=.0004)
meta = finish(parts, 'vm01', RES, want_emit=True, transparent=[gp], col=[(0, 0, .915, 1.0, .72, 1.83)], boost={'led': 3, 'drink': 2.2, 'price': 3, 'header': 2, 'panel': 1.4, 'coin': 3, 'takeout': 2, 'notice': 3, 'inner': .35, 'cap': .5},
              sources=['polyhaven:painted_metal_shutter', 'polyhaven:metal_plate', 'polyhaven:rusty_metal_02', 'font:ZenKakuGothicNew(OFL)', 'font:ReggaeOne(OFL)', 'font:ShipporiMincho(OFL)', 'decals:original'],
              notes='虚构品牌 そよかぜ；发光图单独给出（Emissive），玻璃为 alpha 材质')
import os as _o
sys.stdout.flush()
_o._exit(0)
