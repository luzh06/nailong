# bike01: ママチャリ (no brand). Long axis X, front +X. Wheel diameter .67, wheelbase 1.10
import sys, os, math, random
sys.path.insert(0, r'D:\Cijian\scripts')
import cj_lib
from cj_lib import *
RES = 2048
reset()
random.seed(5)
D = DECAL + os.sep
frame_m = pbr('frame', 'painted_metal_shutter', 3.0, flat_color=(.06, .13, .10), tint_amt=.12, rough=.34, nor=.12, wear=.45, grime=.7, streak=.15, rust=.14, rust_scale=26, rust_tex='rusty_metal_02', edge_col=(.33, .32, .30), coat=.4)
chrome = pbr('chrome', 'metal_plate', 4.0, flat_color=(.78, .78, .78), tint_amt=.1, rough=.2, metal=1.0, nor=.15, wear=.1, grime=.6, streak=.05, rust=.3, rust_scale=22, rust_tex='rusty_metal_02')
steel = pbr('steel', 'metal_plate', 6.0, flat_color=(.5, .5, .5), tint_amt=.2, rough=.42, metal=1.0, nor=.2, wear=.1, grime=.6, streak=.05, rust=.3, rust_scale=22)
rubber = pbr('tire', 'asphalt_02', 9, flat_color=(.03, .03, .03), tint_amt=.12, rough=.8, nor=1.0, wear=.3, grime=.3, streak=0, edge_col=(.09, .09, .085))
black = pbr('black', None, flat_color=(.025, .025, .028), rough=.5, wear=.3, grime=.3, streak=.1, edge_col=(.16, .16, .16))
guard = pbr('guard', 'metal_plate', 4.0, flat_color=(.62, .62, .6), tint_amt=.12, rough=.27, metal=1.0, nor=.15, wear=.1, grime=.9, streak=.35, rust=.22, rust_scale=20)
casem = pbr('casem', 'painted_metal_shutter', 3.0, flat_color=(.06, .13, .10), tint_amt=.12, rough=.36, nor=.12, wear=.4, grime=.8, streak=.3, rust=.1, rust_scale=26, edge_col=(.33, .32, .3), coat=.3)
vinyl = pbr('vinyl', 'fabric_pattern_07', 12.0, flat_color=(.035, .03, .026), tint_amt=.1, rough=.5, nor=.2, wear=.25, grime=.5, streak=.1, edge_col=(.1, .09, .08))
red = pbr('reflector', None, flat_color=(.5, .02, .015), rough=.2, wear=.05, grime=.3, streak=0)
reg = pbr('reg', None, base_img=D + 'bike_reg.png', rough=.5, wear=.3, grime=.3, streak=.2)
lens = pbr('lens', None, flat_color=(.85, .85, .78), rough=.1, wear=0, grime=.2, streak=0)
P = []
A = P.append
R = .335
RX, FX = -.56, .54
# wheels ------------------------------------------------------------------
def wheel(cx, y0=0.0, steer=None, name='w'):
    out = []
    # tyre: revolve about Y through hub, cross-section with tread ribs
    sec = []
    n = 44
    rt = .0185
    for i in range(n + 1):
        a = -math.pi * .95 + 2 * math.pi * .95 * i / n
        # centre ribs plus a raised sidewall line
        rib = .0016 * (1 if i % 2 == 0 and abs(i - n / 2) < 15 else 0) + .0009 * (1 if abs(abs(i - n / 2) - 18) < 1 else 0)
        sec.append((R - rt + (rt + rib) * math.cos(a), (rt + rib) * math.sin(a)))
    t = lathe(name + 'tyre', [(r, h) for r, h in sec], rubber, verts=96, axis='Y')
    out.append(t)
    rim_p = [(.296, -.012), (.300, -.0145), (.306, -.0135), (.307, -.009), (.303, -.007), (.303, .007), (.307, .009), (.306, .0135), (.300, .0145), (.296, .012), (.293, 0), (.296, -.012)]
    out.append(lathe(name + 'rim', rim_p, chrome, verts=72, axis='Y'))
    out.append(lathe(name + 'hub', [(.008, -.05), (.012, -.048), (.014, -.04), (.032, -.034), (.033, -.030), (.016, -.024), (.015, 0), (.016, .024), (.033, .03), (.032, .034), (.014, .04), (.012, .048), (.008, .05)], steel, verts=24, axis='Y'))
    out.append(cyl(name + 'axle', .0045, .135, (0, 0, 0), steel, verts=10, axis='Y'))
    for sgn in (-1, 1):
        out.append(cyl(name + 'nut', .0085, .008, (0, sgn * .067, 0), steel, verts=6, axis='Y', bv=.0006))
    # 36 spokes, 3-cross
    for i in range(36):
        side = 1 if i % 2 else -1
        a = 2 * math.pi * i / 36
        lead = 1 if (i // 2) % 2 else -1
        h = a + lead * math.radians(62)
        p0 = Vector((.031 * math.cos(h), side * .031, .031 * math.sin(h)))
        p1 = Vector((.293 * math.cos(a), side * .004, .293 * math.sin(a)))
        out.append(tube(name + 'sp%d' % i, [p0, p1], .00085, steel, verts=5, cap=False))
        out.append(tube(name + 'ni%d' % i, [p1 + (p0 - p1).normalized() * .0, p1 + (p0 - p1).normalized() * .012], .0016, chrome, verts=6, cap=False))
    return out
def place(parts, loc, rz=0, pivot=None):
    M = Matrix.Translation(loc)
    for o in parts:
        bake_xform(o)
        o.data.transform(M)
    return parts
rear = place(wheel(0, name='r'), (RX, 0, R))
front = wheel(0, name='f')
place(front, (FX, 0, R))
P += rear
frontset = list(front)
# frame --------------------------------------------------------------------
BB = Vector((-.125, 0, .285))
HT, HB = Vector((.285, 0, .84)), Vector((.335, 0, .69))
ST = Vector((-.285, 0, .73))
S = lambda *a: tube(*a)
A(S('down', fillet([HB + Vector((-.012, 0, .035)), (.14, 0, .56), (.0, 0, .33), BB], [.28, .22]), .0195, frame_m, 16))
A(S('down2', fillet([HT + Vector((-.012, 0, -.03)), (.12, 0, .635), (-.05, 0, .47), (-.205, 0, .50)], [.26, .22]), .0145, frame_m, 14))
A(S('seat', [BB, ST], .0143, frame_m, 16))
A(S('ht', [HT + Vector((.01, 0, -.0) ), HB], .0185, frame_m, 18))
A(cyl('bbshell', .0235, .07, BB, frame_m, verts=20, axis='Y'))
for sy in (-1, 1):
    A(S('cs%d' % sy, fillet([BB + Vector((-.02, sy * .024, 0)), (-.24, sy * .05, .30), (RX, sy * .058, R)], .1), .0095, frame_m, 12, True, lambda t: 1 - .28 * t))
    A(S('ss%d' % sy, fillet([ST + Vector((.01, sy * .018, -.05)), (-.31, sy * .036, .62), (RX, sy * .058, R)], .1), .0078, frame_m, 12, True, lambda t: 1 - .2 * t))
    A(box('dropout%d' % sy, (.05, .005, .03), (RX + .005, sy * .058, R), frame_m, bv=.002))
A(cyl('seatclamp', .0175, .022, ST + Vector((.003, 0, -.01)), steel, verts=16, axis='Z'))
A(cyl('seatbolt', .0045, .05, ST + Vector((-.021, 0, -.01)), steel, verts=8, axis='Y'))
# seatpost + saddle --------------------------------------------------------
post_top = ST + (ST - BB).normalized() * .05
A(S('post', [ST, post_top], .0122, chrome, 14))
SZ = post_top.z + .055
SX = post_top.x - .005
def sad(u, v):
    t = u / .27
    x = -.10 + u
    # plan shape: wide rounded rump tapering into a narrow nose
    half = .102 * math.sin(min(t / .1, 1) * math.pi / 2) ** .55 * (1 - t ** 1.6 * .58) if t < .62 else .102 * (1 - .62 ** 1.6 * .58) * (1 - ((t - .62) / .38) ** 2.2 * .42)
    half *= .32 + .68 * math.sin(min((1 - t) / .06, 1) * math.pi / 2) ** .5
    e = (v / .24 - .5) * 2
    y = e * half
    z = .026 * (1 - abs(e) ** 2.0) - .034 * abs(e) ** 6 + .024 * t - .018 * (1 - min(t / .12, 1)) ** 2
    return (SX + x, y, SZ + z)
sd = grid('saddle', .27, .24, 40, 24, sad, vinyl)
solidify(sd, .012)
box_uv(sd)
A(sd)
for sy in (-1, 1):
    coil = []
    for k in range(121):
        a = k / 120 * 2 * math.pi * 6
        coil.append((SX - .105 + .017 * math.cos(a), sy * .05 + .017 * math.sin(a), SZ - .075 + k / 120 * .058))
    A(S('spring%d' % sy, coil, .0024, black, 6))
    A(S('rail%d' % sy, fillet([(SX - .105, sy * .05, SZ - .018), (SX - .10, sy * .05, SZ - .004), (SX + .19, sy * .012, SZ - .006)], .02), .0035, steel, 8))
    A(S('rail2%d' % sy, [(SX - .105, sy * .05, SZ - .08), (SX + .01, sy * .012, SZ - .083)], .0035, steel, 8))
A(cyl('sclamp', .014, .03, (SX + .012, 0, SZ - .07), steel, verts=10, axis='Y'))
# crank + chain case --------------------------------------------------------
A(cyl('axle_bb', .010, .15, BB, steel, verts=12, axis='Y'))
ca = math.radians(-35)
for sy, a in ((1, ca), (-1, ca + math.pi)):
    tip = BB + Vector((.165 * math.cos(a), sy * .082, .165 * math.sin(a)))
    A(S('crank%d' % sy, [BB + Vector((0, sy * .07, 0)), tip], .0115, steel, 10, True, lambda t: 1 - .28 * t))
    py = tip.y + sy * .058
    A(cyl('ped_ax%d' % sy, .005, .11, (tip.x, tip.y + sy * .05, tip.z), steel, verts=8, axis='Y'))
    A(box('ped%d' % sy, (.058, .095, .017), (tip.x, py, tip.z), rubber, bv=.004, segs=2))
    for k in (-1, 1):
        A(box('pedb%d%d' % (sy, k), (.012, .10, .022), (tip.x + k * .019, py, tip.z), rubber, bv=.002))
    for k in (-1, 0, 1):
        A(box('peds%d%d' % (sy, k), (.066, .006, .012), (tip.x, py + k * .048, tip.z), steel, bv=.001))
def stadium(c0, r0, c1, r1, n=24):
    pts = []
    d = (c1 - c0).normalized()
    a0 = math.atan2(d.z, d.x) + math.pi / 2
    for k in range(n + 1):
        a = a0 + math.pi * k / n
        pts.append((c0.x + r0 * math.cos(a), c0.z + r0 * math.sin(a)))
    for k in range(n + 1):
        a = a0 + math.pi + math.pi * k / n
        pts.append((c1.x + r1 * math.cos(a), c1.z + r1 * math.sin(a)))
    return pts
rearv = Vector((RX, 0, R))
case = prism('chaincase', stadium(BB, .098, rearv, .058), .04, casem, bv=.009, loc=(0, -.066, 0))
A(case)
# pressed step and sprocket dome so the cover does not read as a flat slab
A(prism('casestep', stadium(BB, .082, rearv, .044), .006, casem, bv=.0025, loc=(0, -.0875, 0)))
A(lathe('casedome', [(.0, .0), (.078, .0), (.074, .004), (.03, .009), (.0, .009)], casem, verts=40, loc=(BB.x, -.090, BB.z), axis='Y'))
for i in range(5):
    k = (i + 1) / 6
    p = BB + (rearv - BB) * k
    A(cyl('casebolt', .0048, .004, (p.x, -.0918, p.z + .05 - .012 * k), steel, verts=8, axis='Y', bv=.0006))
# rear stand ----------------------------------------------------------------
sp = Vector((RX + .03, 0, R - .03))
for sy in (-1, 1):
    A(S('stand%d' % sy, fillet([(sp.x, sy * .062, sp.z + .03), (sp.x - .02, sy * .095, sp.z - .13), (sp.x - .05, sy * .14, .012)], .05), .0072, steel, 10))
A(S('standb', [(sp.x - .05, -.17, .010), (sp.x - .05, .17, .010)], .0078, rubber, 8))
# mudguards -----------------------------------------------------------------
def fender(nm, cx, a0, a1, mat, cz=R):
    rf = .362
    def fn(u, v):
        a = a0 + (a1 - a0) * u / 1.0
        hw = .029
        vv = (v / .1 - .5) * 2
        rr = rf - .015 * vv * vv
        return (cx + rr * math.cos(a), vv * hw, cz + rr * math.sin(a))
    f = grid(nm, 1.0, .1, 48, 8, fn, mat)
    solidify(f, .0014)
    box_uv(f)
    return f
A(fender('rfend', RX, math.radians(12), math.radians(190), guard))
ffen = fender('ffend', FX, math.radians(-8), math.radians(140), guard)
frontset.append(ffen)
for sy in (-1, 1):
    A(S('rstay%d' % sy, [(RX + .362 * math.cos(math.radians(155)), sy * .03, R + .362 * math.sin(math.radians(155))), (RX, sy * .062, R)], .0026, steel, 6))
    frontset.append(S('fstay%d' % sy, [(FX + .36 * math.cos(math.radians(25)), sy * .03, R + .36 * math.sin(math.radians(25))), (FX, sy * .058, R)], .0026, steel, 6))
A(box('refl', (.012, .034, .075), (RX - .353, 0, R + .13), red, bv=.003))
# rear rack -----------------------------------------------------------------
rz = R + .385
A(S('rackL', fillet([(RX - .2, -.07, rz), (RX + .26, -.07, rz), (RX + .26, .07, rz), (RX - .2, .07, rz), (RX - .2, -.07, rz)], .03), .0052, chrome, 8))
for k in range(5):
    x = RX - .15 + k * .085
    A(S('rackb%d' % k, [(x, -.07, rz), (x, .07, rz)], .0034, chrome, 6))
for sy in (-1, 1):
    A(S('rl%d' % sy, [(RX - .05, sy * .07, rz), (RX, sy * .058, R)], .0044, chrome, 8))
    A(S('rl2%d' % sy, [(RX + .14, sy * .07, rz), (RX, sy * .058, R)], .0044, chrome, 8))
    A(S('rs%d' % sy, [(RX + .26, sy * .07, rz), ST + Vector((.0, sy * .018, -.08))], .0038, chrome, 6))
# ring lock on seat stays
ringz = R + .155
ring = []
for k in range(41):
    a = math.radians(20) + k / 40 * math.radians(320)
    ring.append((RX + .0 + .10 * math.cos(a) + .0, .0, R + .10 * math.sin(a) + .0))
A(box('lock', (.075, .016, .05), (RX + .13, .07, R + .08), black, bv=.006, segs=3, rot=(0, math.radians(-32), 0)))
reg_s = box('reg', (.052, .001, .021), (-.285 + .17, -.0, .0), reg, bv=0)
bpy.data.objects.remove(reg_s)
# steering assembly (fork, stem, bar, lamp, basket) --------------------------
S2 = frontset
ax0, ax1 = HB, HT
AX = (ax1 - ax0).normalized()
crown = HB - AX * .025
for sy in (-1, 1):
    S2.append(S('fork%d' % sy, fillet([crown + Vector((0, sy * .036, 0)), crown + Vector((.03, sy * .05, -.09)), (FX - .035, sy * .054, R + .14), (FX, sy * .058, R)], [.08, .16]), .0115, frame_m, 12, True, lambda t: 1 - .42 * t))
S2.append(S('crown', [crown + Vector((0, -.04, 0)), crown + Vector((0, .04, 0))], .0135, frame_m, 12))
S2.append(S('steerer', [crown, HT + AX * .015], .0125, steel, 12))
stem_top = HT + AX * .11
S2.append(S('stem', [HT + AX * .01, stem_top], .0108, chrome, 12))
S2.append(cyl('hset', .0222, .012, HT + AX * .006, chrome, verts=20))
S2.append(cyl('hset2', .0222, .012, HB - AX * .006, chrome, verts=20))
barc = stem_top + Vector((.06, 0, .015))
S2.append(S('stemx', [stem_top, barc], .0122, chrome, 10))
for sy in (-1, 1):
    pts = fillet([barc, barc + Vector((.0, sy * .09, .03)), barc + Vector((-.13, sy * .23, .055)), barc + Vector((-.285, sy * .285, .03))], [.06, .12])
    S2.append(S('bar%d' % sy, pts, .0112, chrome, 12))
    gr0 = barc + Vector((-.185, sy * .262, .048))
    gr1 = barc + Vector((-.295, sy * .29, .028))
    S2.append(S('grip%d' % sy, [gr0, gr0 + (gr1 - gr0) * .08, gr1], .0165, rubber, 14))
    S2.append(cyl('gripend%d' % sy, .0185, .01, gr1, rubber, verts=14, axis='Y'))
    lv = barc + Vector((-.13, sy * .23, .04))
    S2.append(S('levb%d' % sy, [lv, lv + Vector((.035, 0, -.02))], .007, black, 8))
    S2.append(S('lev%d' % sy, fillet([lv + Vector((.035, 0, -.02)), lv + Vector((.06, sy * .03, -.022)), lv + Vector((.02, sy * .10, -.02))], .02), .0048, black, 8))
    # cables run to mid frame / front hub
    S2.append(S('cab%d' % sy, fillet([lv + Vector((.03, 0, -.015)), lv + Vector((.16, -sy * .06, .05)), barc + Vector((.1, sy * .02, -.05)), crown + Vector((.05, sy * .05, -.03))], .07), .0026, black, 6))
# bell on left bar
bl = barc + Vector((-.09, .15, .075))
S2.append(lathe('bell', [(0, .03), (.012, .029), (.024, .02), (.029, .008), (.03, 0), (.028, -.002), (.0, -.002)], chrome, verts=24, loc=bl))
# hub-dynamo lamp
lamp_c = crown + Vector((.10, 0, -.055))
S2.append(S('lampbr', [crown + Vector((.0, 0, .0)), lamp_c], .0045, steel, 8))
S2.append(lathe('lamp', [(0, -.04), (.018, -.04), (.03, -.015), (.034, .01), (.036, .03), (.0345, .034), (.0, .034)], black, verts=24, loc=lamp_c + Vector((.02, 0, 0)), axis='X'))
S2.append(lathe('lampg', [(0, 0), (.032, 0), (.03, .006), (.0, .012)], lens, verts=24, loc=lamp_c + Vector((.056, 0, 0)), axis='X'))
# basket: wire mesh
bz0, bz1 = crown.z + .075, crown.z + .295
bx0, bx1 = crown.x + .07, crown.x + .345
bw0, bw1 = .125, .165
def ring_pts(t):
    x0, x1 = bx0 - t * .03, bx1 + t * .03
    w = bw0 + (bw1 - bw0) * t
    z = bz0 + (bz1 - bz0) * t
    return [(x0, -w, z), (x1, -w, z), (x1, w, z), (x0, w, z), (x0, -w, z)], z
for k, t in enumerate((0, .25, .5, .75, 1)):
    pts, z = ring_pts(t)
    S2.append(S('bk%d' % k, fillet(pts, .03), .0036 if k in (0, 4) else .0017, black if False else chrome, 8 if k in (0, 4) else 5))
nv = 14
for i in range(nv + 1):
    f = i / nv
    y0 = -bw0 + 2 * bw0 * f
    y1 = -bw1 + 2 * bw1 * f
    S2.append(S('bv1%d' % i, [(bx1, y0, bz0), (bx1 + .03, y1, bz1)], .0017, chrome, 5, False))
    S2.append(S('bv2%d' % i, [(bx0, y0, bz0), (bx0 - .03, y1, bz1)], .0017, chrome, 5, False))
for i in range(1, 16):
    f = i / 16
    x0 = bx0 + (bx1 - bx0) * f
    x1 = bx0 - .03 + (bx1 - bx0 + .06) * f
    for sy in (-1, 1):
        S2.append(S('bs%d%d' % (i, sy), [(x0, sy * bw0, bz0), (x1, sy * bw1, bz1)], .0017, chrome, 5, False))
    S2.append(S('bf%d' % i, [(x0, -bw0, bz0), (x0, bw0, bz0)], .0017, chrome, 5, False))
S2.append(S('bkst', [crown + Vector((.03, 0, .02)), (bx0 + .1, 0, bz0)], .0042, steel, 8))
for sy in (-1, 1):
    S2.append(S('bkst2%d' % sy, [(FX + .0, sy * .058, R), (bx1 - .05, sy * .10, bz0)], .0034, chrome, 6))
# turn the bars a touch; rotate about the steering axis
ROT = Matrix.Translation(ax0) @ Matrix.Rotation(math.radians(-14), 4, AX) @ Matrix.Translation(-ax0)
for o in S2:
    bake_xform(o)
    o.data.transform(ROT)
P += S2
meta = finish(P, 'bike01', RES, col=[(0, 0, .35, 1.75, .12, .70), (.45, 0, .95, .5, .6, .4), (-.3, 0, .9, .35, .25, .4)], uv_margin=.002, lods=(.35, .1),
              sources=['polyhaven:painted_metal_shutter', 'polyhaven:metal_plate', 'polyhaven:rusty_metal_02', 'polyhaven:fabric_pattern_07', 'decals:original'],
              notes='无品牌ママチャリ；前轮转 14°，靠后撑站立')
sys.stdout.flush()
os._exit(0)
