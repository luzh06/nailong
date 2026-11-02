# gr01_road: 8 x 4.6 m street slab. Concrete aprons + cast gutter both sides, patched asphalt crown, tar-sealed cracks, worn edge lines.
# Faithful to Commons photos of Yanaka side streets. Tiles along X (flip every other).
import sys, os, math, random
sys.path.insert(0, r'D:\Cijian\scripts')
from cj_lib import *
reset()
random.seed(17)
LX, LY = 8.0, 4.6
tar = stain_image('tar', LX, LY, [], splash=0, seed=21, res=2600, cracks=11, crack_w=1.6, crack_v=.9, blobs=0)
dirt = stain_image('dirt', LX, LY, [], splash=0, seed=22, res=1600, cracks=10, crack_w=.8, crack_v=.5, blobs=22)
asph = pbr('asph', 'worn_asphalt', 1.0, hsv=(.5, .55, 1.0), nor=1.4, wear=0, grime=0, streak=0, stain=(tar, -LX / 2, LX / 2, -LY / 2, LY / 2), stain_col=(.016, .016, .017), stain_amt=1.0, stain_plane='XY', stain_rough=.5)
apron = pbr('apron', 'concrete_floor_worn_001', 1.1, hsv=(.5, .45, .92), nor=1.5, wear=.2, grime=.4, streak=0, stain=(dirt, -LX / 2, LX / 2, -LY / 2, LY / 2), stain_col=(.05, .045, .04), stain_amt=.8, stain_plane='XY')
patchm = pbr('patchm', 'asphalt_02', 1.0, hsv=(.5, .5, .78), nor=1.4, wear=.25, grime=.5, streak=0, edge_col=(.03, .03, .03))
patch2 = pbr('patch2', 'concrete_floor_worn_001', 1.3, hsv=(.5, .35, .78), nor=1.4, wear=.3, grime=.6, streak=0)
paint = pbr('paintl', 'concrete_floor_worn_001', 1.6, flat_color=(.78, .77, .72), tint_amt=.25, rough=.6, nor=1.0, wear=.2, grime=.5, streak=0)
iron = pbr('ironc', 'metal_plate', 3, flat_color=(.05, .045, .04), tint_amt=.3, rough=.55, metal=.5, nor=.6, wear=.3, grime=.8, streak=0, rust=.38, rust_scale=18, edge_col=(.3, .28, .25))
wet = pbr('wet', None, flat_color=(.012, .013, .016), rough=.06, wear=0, grime=0, streak=0, coat=1.0, spec=.8)
P = []
A = P.append
crown = lambda x, y: -.05 * (y / 2.3) ** 2 + .004 * math.sin(1.7 * x + .9 * y) + .003 * math.sin(2.3 * y - x)
# asphalt mid-strip with crown
ax0 = 1.62
def fn(x, y):
    xx, yy = x - LX / 2, y - ax0
    return (xx, yy, crown(xx, yy))
ag = grid('asph', LX, ax0 * 2, 200, 80, fn, asph)
A(ag)
# aprons in cast bays with joints
for sy in (-1, 1):
    n = 5
    bay = LX / n
    for i in range(n):
        x = -LX / 2 + (i + .5) * bay
        b = box('bay', (bay - .012, .54, .05), (x, sy * 1.93, -.035 + random.uniform(-.002, .002)), apron, bv=.006, segs=2, rot=(sy * .02, 0, 0))
        A(b)
    # cast gutter channel with slot covers
    A(box('gut', (LX, .18, .03), (0, sy * 2.2, -.03), patch2, bv=.005))
    x = -LX / 2 + .25
    while x < LX / 2:
        A(box('cov', (.48, .17, .012), (x, sy * 2.21, -.012), iron, bv=.002))
        for k in range(9):
            A(box('slot', (.03, .13, .004), (x - .2 + k * .05, sy * 2.21, -.005), wet, bv=0))
        x += .5
# worn edge lines: broken, not continuous
for sy in (-1, 1):
    x = -LX / 2
    while x < LX / 2:
        w = random.uniform(.5, 1.9)
        y0 = sy * 1.56
        A(box('ln', (min(w, LX / 2 - x), .09, .003), (x + min(w, LX / 2 - x) / 2, y0 + random.uniform(-.004, .004), crown(x, y0) + .002), paint, bv=0, rot=(sy * .045, 0, 0)))
        x += w + random.uniform(.02, .3)
# irregular utility trench patches
def blob(n, rx, ry, jit):
    return [(rx * math.cos(i * 6.283 / n) * random.uniform(1 - jit, 1 + jit), ry * math.sin(i * 6.283 / n) * random.uniform(1 - jit, 1 + jit)) for i in range(n)]
def poly(pts, loc, m, t=.008):
    o = prism('pt', pts, t, m, bv=.0035, plane='XY', loc=loc)
    return o
A(poly([(-1.9, -.32), (1.3, -.36), (1.36, .29), (.2, .33), (.16, .08), (-1.92, .05)], (-1.1, .55, -.012), patchm))
A(poly([(-.5, -.45), (.52, -.43), (.5, .47), (-.48, .44)], (2.4, -.7, -.016), patchm))
A(poly([(-.9, -.36), (.86, -.4), (.9, .37), (-.88, .4)], (-2.3, -.85, -.018), patch2, .012))
A(poly([(-.42, -.22), (.4, -.25), (.43, .24), (-.4, .22)], (1.2, .85, -.014), patchm, .01))
# manhole: iron ring, chequer, in a poured collar
A(lathe('collar', [(0, 0), (.42, 0), (.46, -.02)], patch2, verts=48, loc=(-.5, -.5, -.005)))
A(lathe('ring', [(0, .012), (.325, .012), (.335, .016), (.36, .012), (.36, -.01)], iron, verts=48, loc=(-.5, -.5, 0)))
for r_, n_ in ((.09, 8), (.16, 14), (.23, 22), (.30, 30)):
    for i in range(n_):
        a = i * 6.283 / n_
        A(box('mh', (.05, .022, .007), (-.5 + r_ * math.cos(a), -.5 + r_ * math.sin(a), .0165), iron, bv=.002, rot=(0, 0, a + .6)))
# drain puddles, thin and irregular
A(poly(blob(14, .55, .19, .25), (3.0, 1.34, -.031), wet, .002))
A(poly(blob(12, .32, .12, .3), (-1.0, -1.41, -.03), wet, .002))
A(poly(blob(10, .22, .1, .3), (1.9, .12, -.034), wet, .002))
finish(P, 'gr01_road', 4096, origin=(0, 0), lods=(.4, .12), uv_keep=('asph',), boost={'ironc': .45, 'wet': .2, 'paintl': .8},
       col=[(0, 0, -.1, LX, LY, .2)],
       sources=['polyhaven:worn_asphalt', 'polyhaven:asphalt_02', 'polyhaven:concrete_floor_worn_001', 'polyhaven:metal_plate', 'polyhaven:rusty_metal_02'],
       notes='8×4.6 米路面段，沿 X 平铺，隔段镜像；顶面略低于 z=0')
sys.stdout.flush()
os._exit(0)
