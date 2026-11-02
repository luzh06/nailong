# 《此间》10×10 米质量样板：路面、石阶、电线杆与电线，早晨/日落两版光。
# 运行：blender -b -P qs_build.py -- --tag r1 --cams main,steps,road,pole --lights morning,sunset --res 1280 --spp 200
# 约定：单位米；+y 朝东（上台阶方向），+x 朝南；UV0 为米制平铺，UV1 留作光照贴图。
# 店面归 4060，这里的房屋只是遮光和挡背景的灰盒占位。
import bpy, bmesh, sys, os, math, json, time
import numpy as np
from mathutils import Vector

sys.path.insert(0, r'D:\Cijian\scripts')
import qs_masks
import qs_ext

ROOT = r'D:\Cijian'
TEX = ROOT + r'\assets\textures'
TEX4 = ROOT + r'\assets\textures4k'
PHOTO = ROOT + r'\assets\photo'
HDR = ROOT + r'\assets\hdri'
MASK = ROOT + r'\assets\masks'
OUT = ROOT + r'\output'

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d):
    return argv[argv.index('--' + k) + 1] if '--' + k in argv else d
TAG = arg('tag', 'r1')
CAMS = arg('cams', 'main,steps,road,pole').split(',')
LIGHTS = arg('lights', 'morning,sunset').split(',')
RES = int(arg('res', '1280'))
SPP = int(arg('spp', '200'))
rng = np.random.default_rng(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
os.makedirs(MASK, exist_ok=True)

# ---------- 图片 ----------
def load(path, data=True):
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    return img

def tex_path(name, kind):
    d = os.path.join(TEX4, name)
    if not (os.path.isdir(d) and any(f.startswith(f'{name}_{kind}.') for f in os.listdir(d))):
        d = os.path.join(TEX, name)
    for f in os.listdir(d):
        if f.startswith(f'{name}_{kind}.'):
            return os.path.join(d, f)
    return None

def save_rgb(name, r, g, b):
    path = os.path.join(MASK, name + '.png')
    h, w = r.shape
    px = np.ones((h, w, 4), 'f')
    px[..., 0], px[..., 1], px[..., 2] = r, g, b
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    return img

M = qs_masks.make()
IM1 = save_rgb('road_m1', M['age'], M['seam'], M['crack'])
IM2 = save_rgb('road_m2', M['paint'], M['wet'], M['puddle'])
IM3 = save_rgb('road_m3', M['grime'], M['height'], M['moss'])
IM4 = save_rgb('road_m4', M['tide'], M['fine'], M['patch'])
MB = qs_masks.make(21, hero=False)
IM1B = save_rgb('road_b1', MB['age'], MB['seam'], MB['crack'])
IM2B = save_rgb('road_b2', MB['paint'], MB['wet'], MB['puddle'])
IM3B = save_rgb('road_b3', MB['grime'], MB['height'], MB['moss'])
IM4B = save_rgb('road_b4', MB['tide'], MB['fine'], MB['patch'])
mh_h, mh_rim, mh_top = qs_masks.manhole_height()
IMH = save_rgb('manhole', mh_h, mh_rim, mh_top)

# ---------- 节点小工具 ----------
class G:
    def __init__(s, name):
        s.mat = bpy.data.materials.new(name)
        s.mat.use_nodes = True
        s.nt = s.mat.node_tree
        s.nt.nodes.clear()

    def add(s, t, **kw):
        n = s.nt.nodes.new(t)
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def put(s, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            s.nt.links.new(v, sock)
        elif isinstance(v, tuple) and len(v) == 3 and sock.type == "RGBA":
            sock.default_value = (*v, 1)
        else:
            sock.default_value = v

    def math(s, op, a, b=None, clamp=False):
        n = s.add('ShaderNodeMath', operation=op, use_clamp=clamp)
        s.put(n.inputs[0], a)
        if b is not None:
            s.put(n.inputs[1], b)
        return n.outputs[0]

    def mul(s, a, b): return s.math('MULTIPLY', a, b)
    def add_(s, a, b): return s.math('ADD', a, b)
    def sub(s, a, b): return s.math('SUBTRACT', a, b)
    def inv(s, a): return s.math('SUBTRACT', 1.0, a, True)
    def maxi(s, a, b): return s.math('MAXIMUM', a, b)

    def mix(s, fac, a, b, mode='MIX'):
        n = s.add('ShaderNodeMix', data_type='RGBA', blend_type=mode, clamp_factor=True)
        s.put(n.inputs[0], fac)
        s.put(n.inputs[6], a if isinstance(a, bpy.types.NodeSocket) else (*a, 1))
        s.put(n.inputs[7], b if isinstance(b, bpy.types.NodeSocket) else (*b, 1))
        return n.outputs[2]

    def mixf(s, fac, a, b):
        n = s.add('ShaderNodeMix', data_type='FLOAT', clamp_factor=True)
        s.put(n.inputs[0], fac)
        s.put(n.inputs[2], a)
        s.put(n.inputs[3], b)
        return n.outputs[0]

    def rng(s, v, a, b, c=0.0, d=1.0, smooth=True):
        n = s.add('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP' if smooth else 'LINEAR', clamp=True)
        s.put(n.inputs['Value'], v)
        n.inputs['From Min'].default_value = a
        n.inputs['From Max'].default_value = b
        n.inputs['To Min'].default_value = c
        n.inputs['To Max'].default_value = d
        return n.outputs[0]

    def uv(s, name='UV0'):
        return s.add('ShaderNodeUVMap', uv_map=name).outputs[0]

    def xform(s, vec, loc=(0, 0, 0), rot=0.0, scale=1.0):
        n = s.add('ShaderNodeMapping')
        s.put(n.inputs['Vector'], vec)
        n.inputs['Location'].default_value = loc
        n.inputs['Rotation'].default_value = (0, 0, rot)
        n.inputs['Scale'].default_value = (scale, scale, scale)
        return n.outputs[0]

    def img(s, image, vec, interp='Cubic', ext='REPEAT'):
        n = s.add('ShaderNodeTexImage', interpolation=interp, extension=ext)
        n.image = image
        s.put(n.inputs[0], vec)
        return n

    def noise(s, vec, scale, detail=5.0, rough=.55):
        n = s.add('ShaderNodeTexNoise')
        s.put(n.inputs['Vector'], vec)
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        return n.outputs[0]

    def sep(s, col):
        n = s.add('ShaderNodeSeparateColor')
        s.put(n.inputs[0], col)
        return n.outputs

    def pbr(s, uv, name, size, rot=0.0, off=(0, 0)):
        v = s.xform(uv, (off[0], off[1], 0), rot, 1 / size)
        out = dict(col=s.img(load(tex_path(name, 'Diffuse'), False), v).outputs[0],
                   rough=s.img(load(tex_path(name, 'Rough')), v).outputs[0],
                   disp=s.img(load(tex_path(name, 'Displacement')), v).outputs[0])
        return out

    def antitile(s, uv, name, size, seed=0.0):
        """同一贴图两次不同旋转和偏移采样，用低频噪声按高度切换，消除重复。"""
        a = s.pbr(uv, name, size, 0.0 + seed, (seed * .3, seed * .7))
        b = s.pbr(uv, name, size, 1.13 + seed, (.37 + seed, .71))
        c = s.pbr(uv, name, size * 1.37, 2.31 + seed, (.11, .53 + seed))
        n1 = s.noise(uv, .55 / size * 3, 4)
        n2 = s.noise(s.xform(uv, (7.3, 2.1, 0)), .4 / size * 3, 4)
        f1 = s.rng(s.add_(n1, s.mul(s.sub(a['disp'], .5), .45)), .46, .54)
        f2 = s.rng(s.add_(n2, s.mul(s.sub(b['disp'], .5), .45)), .50, .58)
        out = {}
        for k in ('col', 'rough', 'disp'):
            if k == 'col':
                out[k] = s.mix(f2, s.mix(f1, a[k], b[k]), c[k])
            else:
                out[k] = s.mixf(f2, s.mixf(f1, a[k], b[k]), c[k])
        return out

    def bump(s, h, dist, normal=None, strength=1.0):
        n = s.add('ShaderNodeBump')
        s.put(n.inputs['Height'], h)
        n.inputs['Distance'].default_value = dist
        n.inputs['Strength'].default_value = strength
        if normal is not None:
            s.put(n.inputs['Normal'], normal)
        return n.outputs[0]

    def ao(s, dist=.3, samples=6):
        n = s.add('ShaderNodeAmbientOcclusion', samples=samples, only_local=False)
        n.inputs['Distance'].default_value = dist
        return n.outputs['AO']

    def attr(s, name, out='Color'):
        return s.add('ShaderNodeAttribute', attribute_name=name).outputs[out]

    def finish(s, col, rough, normal=None, metal=0.0, spec=.5):
        p = s.add('ShaderNodeBsdfPrincipled')
        s.put(p.inputs['Base Color'], col)
        s.put(p.inputs['Roughness'], rough)
        s.put(p.inputs['Metallic'], metal)
        s.put(p.inputs['Specular IOR Level'], spec)
        if normal is not None:
            s.put(p.inputs['Normal'], normal)
        o = s.add('ShaderNodeOutputMaterial')
        s.nt.links.new(p.outputs[0], o.inputs[0])
        return s.mat

# ---------- 材质 ----------
def m_road():
    g = G('road')
    uv = g.uv()
    mv = g.xform(uv, (.5, .5, 0), 0, .1)
    m1 = g.sep(g.img(IM1, mv, 'Linear', 'EXTEND').outputs[0])
    m2 = g.sep(g.img(IM2, mv, 'Linear', 'EXTEND').outputs[0])
    m3 = g.sep(g.img(IM3, mv, 'Linear', 'EXTEND').outputs[0])
    m4 = g.sep(g.img(IM4, mv, 'Linear', 'EXTEND').outputs[0])
    # y<-5 换成 10 米循环的延伸段遮罩，避免边缘被拉成长条
    sy = g.add('ShaderNodeSeparateXYZ')
    g.put(sy.inputs[0], uv)
    hero = g.rng(sy.outputs[1], -5.03, -4.97)
    def both(a, img):
        b = g.sep(g.img(img, mv, 'Linear', 'REPEAT').outputs[0])
        return [g.mixf(hero, b[i], a[i]) for i in range(3)]
    age, seam, crack = both(m1, IM1B)
    paint, wet, puddle = both(m2, IM2B)
    grime, height, moss = both(m3, IM3B)
    tide, fine, patch = both(m4, IM4B)

    base = g.antitile(uv, 'asphalt_04', 3.4)
    coarse = g.antitile(uv, 'asphalt_02', 3.0, .9)
    macro = g.noise(uv, .35, 6, .6)
    pm = g.rng(g.add_(macro, g.mul(g.sub(coarse['disp'], .5), .5)), .46, .6)
    col = g.mix(pm, g.mix(.0, base['col'], base['col'], 'MULTIPLY'), g.mix(.55, coarse['col'], (.20, .19, .18)))
    col = g.mix(1.0, col, (.78, .77, .75), 'MULTIPLY')
    rough = g.mixf(pm, base['rough'], coarse['rough'])
    # 大尺度明暗起伏
    tone = g.mixf(g.noise(uv, .9, 4), .78, 1.18)
    col = g.mix(1.0, col, g.mix(g.rng(tone, .78, 1.18), (.78, .78, .78), (1.1, 1.08, 1.05)), 'MULTIPLY')

    # 补丁：越新越黑越细
    pcol = g.mix(g.rng(age, .5, 1.0), g.mix(.45, coarse['col'], (.13, .125, .12)), g.mix(.45, coarse['col'], (.06, .06, .06)))
    col = g.mix(g.rng(patch, .4, .6), col, pcol)
    rough = g.mixf(g.rng(patch, .4, .6), rough, g.add_(g.mul(coarse['rough'], .85), .1))

    # 污渍、裂缝、接缝
    col = g.mix(g.mul(grime, .5), col, (.06, .055, .05), 'MULTIPLY')
    col = g.mix(g.mul(g.rng(crack, .1, .75), .88), col, (.012, .012, .012))
    rough = g.mixf(crack, rough, .8)
    col = g.mix(g.mul(seam, .68), col, (.035, .034, .034))
    rough = g.mixf(seam, rough, .6)

    # 白线：漆有厚度，带脏
    pcol2 = g.mix(g.mul(grime, .7), (.60, .59, .55), (.2, .19, .17))
    col = g.mix(g.rng(paint, .25, .55), col, pcol2)
    rough = g.mixf(g.rng(paint, .25, .55), rough, .72)

    # 水痕盐边、青苔
    col = g.mix(g.mul(tide, .22), col, (.46, .44, .41))
    col = g.mix(g.rng(g.mul(moss, g.add_(fine, .3)), .25, .7), col, (.035, .055, .015))
    rough = g.mixf(moss, rough, .85)

    # 湿：变暗、粗糙下降；积水：几乎镜面
    col = g.mix(g.mul(wet, .6), col, (.48, .47, .46), 'MULTIPLY')
    rough = g.mixf(wet, rough, g.mul(rough, .42))
    col = g.mix(puddle, col, g.mix(.55, col, (.03, .03, .03)))
    rough = g.mixf(g.rng(puddle, .2, .75), rough, .04)

    h = g.mixf(pm, base['disp'], coarse['disp'])
    h = g.mixf(g.rng(patch, .4, .6), h, g.mul(coarse['disp'], .7))
    h = g.add_(h, g.mul(g.rng(paint, .25, .55), .018))
    h = g.mixf(g.mul(seam, .6), h, .52)
    h = g.sub(h, g.mul(crack, .55))
    h = g.mixf(puddle, h, .4)
    n = g.bump(h, .012)
    n = g.bump(height, .016, n)
    mat = g.finish(col, rough, n)
    d = g.add('ShaderNodeDisplacement')
    g.put(d.inputs['Height'], g.add_(h, g.mul(g.sub(height, .5), .8)))
    d.inputs['Midlevel'].default_value = .5
    d.inputs['Scale'].default_value = .014
    out = [x for x in g.nt.nodes if x.bl_idname == 'ShaderNodeOutputMaterial'][0]
    g.nt.links.new(d.outputs[0], out.inputs['Displacement'])
    mat.displacement_method = 'BOTH'
    return mat

def m_manhole():
    """实拍东京樱花井盖：照片当底色，亮度算高度，再叠路面灰和磨亮。"""
    g = G('manhole')
    uv = g.uv()
    alb = g.img(load(os.path.join(PHOTO, 'manhole_albedo.jpg'), False), uv, 'Cubic', 'EXTEND').outputs[0]
    h = g.img(load(os.path.join(PHOTO, 'manhole_height.png')), uv, 'Cubic', 'EXTEND').outputs[0]
    world = g.add('ShaderNodeTexCoord').outputs['Object']
    grain = g.noise(world, 38, 6, .6)
    recess = g.inv(g.rng(h, .42, .55))
    c = g.mix(1.0, alb, (.36, .34, .32), 'MULTIPLY')
    c = g.mix(.3, c, (.1, .095, .09))
    c = g.mix(g.mul(recess, g.rng(grain, .35, .62)), c, (.05, .045, .04), 'MULTIPLY')
    polish = g.rng(h, .56, .72)
    rough = g.mixf(polish, .68, .36)
    n = g.bump(h, .007)
    return g.finish(c, rough, n, g.mul(polish, .55))

def m_concrete(name, tex, size, tint=(1, 1, 1), bump=.006, ao_dirt=.75, seed=0.0, directional=False):
    g = G(name)
    uv = g.uv()
    # 砖、木板、瓦有方向，不能旋转采样
    s = g.pbr(uv, tex, size, 0.0, (seed, seed * .6)) if directional else g.antitile(uv, tex, size, seed)
    rand = g.add('ShaderNodeObjectInfo').outputs['Random']
    c = g.mix(1.0, s['col'], tint, 'MULTIPLY')
    c = g.mix(g.mul(rand, .22), c, (.52, .50, .47), 'MULTIPLY')
    ao = g.ao(.22)
    grain = g.noise(uv, 3.2, 6, .6)
    dirt = g.rng(g.add_(g.mul(g.inv(ao), 1.25), g.mul(g.sub(grain, .5), .7)), .1, .6)
    c = g.mix(g.mul(dirt, ao_dirt), c, (.04, .036, .03), 'MULTIPLY')
    streak = g.noise(g.xform(uv, scale=1.0), 2.0, 5)
    c = g.mix(g.mul(g.rng(streak, .45, .68), .28), c, (.42, .40, .36), 'MULTIPLY')
    n = g.bump(s['disp'], bump)
    return g.finish(c, g.add_(g.mul(s['rough'], .9), .06), n)

def stair_tile_image():
    """夕焼けだんだん踏板：每块四道深色防滑槽。R=槽，G=槽内胶条老化。"""
    # 四种版式上下排：槽数、位置、长度都不同，部分槽中断
    N = 1024
    H = N // 2
    r2 = np.random.default_rng(5)
    u = (np.arange(N) + .5) / N
    v = (np.arange(H) + .5) / H
    uu, vv = np.meshgrid(u, v)
    rows = []
    for var in ((.22, .40, .58, .76), (.26, .46, .66), (.20, .36, .52, .68, .82), (.24, .42, .60, .78)):
        m = np.zeros((H, N))
        for j, c in enumerate(var):
            c = c + float(r2.uniform(-.014, .014))
            hw = .40 + float(r2.uniform(-.035, .015))
            cx = .5 + float(r2.uniform(-.018, .018))
            th = .034 + float(r2.uniform(-.006, .008))
            wob = (r2.normal(0, 1, 9) * .0035)
            yy = vv - c - np.interp(uu, np.linspace(0, 1, 9), wob)
            d = np.maximum(np.abs(yy) - th, np.abs(uu - cx) - hw)
            g = np.clip(1 - d / .006, 0, 1) * (d < .006)
            if r2.random() < .35:
                # 槽里胶条缺一段
                a = float(r2.uniform(.2, .7))
                g *= 1 - np.clip(1 - (np.abs(uu - a) - float(r2.uniform(.02, .09))) / .01, 0, 1)
            m = np.maximum(m, g)
        rows.append(m)
    m = np.vstack(rows)
    return save_rgb('stair_tile', np.clip(m, 0, 1), np.clip(r2.random(m.shape), 0, 1), np.zeros(m.shape))

IMT = stair_tile_image()

def m_stone():
    g = G('stone')
    uv = g.uv()
    s = g.antitile(uv, 'concrete_floor_worn_001', 1.5, .4)
    s2 = g.antitile(uv, 'granular_concrete', 1.1, .7)
    v = g.sep(g.attr('vcol'))
    blk, wear, dirt = v
    t = g.sep(g.img(IMT, g.uv('UVT'), 'Linear', 'REPEAT').outputs[0])
    # 胶条按低频噪声和人流磨损断续，不是每块都完整
    gw = g.rng(g.add_(g.noise(uv, 3.2, 4, .55), g.mul(wear, .38)), .62, .78)
    groove = g.mul(g.rng(t[0], .35, .75), g.sub(1.0, gw))
    base = g.mix(.45, s['col'], s2['col'])
    c = g.mix(1.0, base, g.mix(g.rng(blk, .1, .9), (.92, .91, .89), (1.28, 1.25, 1.2)), 'MULTIPLY')
    fine = g.noise(uv, 5.0, 6, .6)
    n18 = g.noise(uv, 19, 5, .6)
    grain = g.noise(uv, 300, 3, .5)
    pits = g.rng(g.noise(uv, 62, 4, .55), .64, .70)
    c = g.mix(g.mul(g.rng(grain, .55, .6), .34), c, (.13, .125, .12))
    c = g.mix(g.mul(pits, .55), c, (.08, .075, .07))
    dm = g.rng(g.add_(g.add_(dirt, g.mul(g.sub(fine, .5), .9)), g.mul(g.sub(n18, .5), .9)), .3, .76)
    c = g.mix(g.mul(dm, .62), c, (.13, .12, .10), 'MULTIPLY')
    # 防滑槽：深色胶条，边缘磨损露灰
    worn = g.rng(g.add_(g.mul(wear, .7), g.mul(n18, .55)), .55, .9)
    gc = g.mix(worn, (.02, .02, .021), (.09, .085, .08))
    c = g.mix(groove, c, gc)
    wm = g.rng(g.add_(wear, g.mul(g.sub(fine, .5), .55)), .35, .85)
    rough = g.mixf(wm, g.add_(g.mul(s['rough'], .7), .24), .44)
    rough = g.mixf(groove, rough, .62)
    h = g.add_(g.add_(g.mul(s['disp'], .55), g.mul(s2['disp'], .55)), g.mul(fine, .25))
    n = g.bump(g.sub(g.sub(h, g.mul(pits, .4)), g.mul(groove, 1.1)), .0046)
    return g.finish(c, rough, n)

def m_img(name, path, data=False, rough=.55):
    g = G(name)
    uv = g.uv()
    c = g.img(load(os.path.join(PHOTO, path), False), uv, 'Linear', 'EXTEND').outputs[0]
    nz = g.noise(uv, 8, 6, .62)
    c = g.mix(g.mul(g.rng(nz, .42, .68), .55), c, (.42, .39, .32), 'MULTIPLY')
    return g.finish(c, rough)

def m_tile4(name, tex, size, tint=(1, 1, 1), bump=.008, ao_dirt=.7, seed=.0, disp_scale=None):
    return m_concrete(name, tex, size, tint, bump, ao_dirt, seed)

def m_rail(name, col, peel=.5):
    """油漆钢管：大块剥落，露底锈。"""
    g = G(name)
    uv = g.uv()
    r = g.pbr(uv, 'rusty_metal_02', .55)
    nz = g.noise(uv, 5, 7, .62)
    nf = g.noise(uv, 40, 5, .6)
    pm = g.rng(g.add_(nz, g.mul(g.sub(nf, .5), .4)), .62 - peel * .2, .68 - peel * .2)
    fade = g.mix(g.rng(g.noise(uv, 2, 5), .35, .7), col, tuple(x * 1.5 + .02 for x in col))
    c = g.mix(pm, fade, r['col'])
    n = g.bump(g.add_(g.mul(pm, -.5), g.mul(r['disp'], .4)), .0012)
    return g.finish(c, g.mixf(pm, .42, .8), n)

def m_glass():
    g = G('glass')
    return g.finish((.015, .018, .022), .06, spec=.8)

def m_lens():
    g = G('lens')
    return g.finish((.5, .5, .48), .28, spec=.7)

def m_mortar():
    g = G('mortar')
    return g.finish((.15, .14, .125), .9)

def m_wall_stone():
    g = G('wall_stone')
    uv = g.uv()
    s = g.antitile(uv, 'japanese_stone_wall', 1.7, .2)
    streak = g.noise(g.xform(uv, scale=1.0), 3.0, 6, .6)
    ao = g.ao(.16, 4)
    c = g.mix(1.0, s['col'], (.95, .94, .9), 'MULTIPLY')
    c = g.mix(g.mul(g.inv(g.rng(s['disp'], .04, .2)), .9), c, (.04, .04, .035), 'MULTIPLY')
    moss = g.rng(g.mul(g.sub(streak, .5), 3.0), .25, .7)
    c = g.mix(g.mul(moss, .72), c, (.045, .07, .02))
    c = g.mix(g.mul(g.inv(ao), .7), c, (.1, .09, .08), 'MULTIPLY')
    n = g.bump(s['disp'], .012)
    return g.finish(c, g.mixf(moss, s['rough'], .9), n)

def m_block_wall():
    """ブロック塀：390×190 砌块，砂浆缝，顶部雨痕。"""
    g = G('block_wall')
    uv = g.uv()
    s = g.antitile(uv, 'dirty_concrete', 1.6, .6)
    b = g.add('ShaderNodeTexBrick')
    g.put(b.inputs['Vector'], uv)
    b.inputs['Scale'].default_value = 1.0
    b.inputs['Mortar Size'].default_value = .006
    b.inputs['Mortar Smooth'].default_value = .4
    b.inputs['Brick Width'].default_value = .40
    b.inputs['Row Height'].default_value = .20
    b.inputs['Color1'].default_value = (1, 1, 1, 1)
    b.inputs['Color2'].default_value = (.82, .82, .82, 1)
    b.inputs['Mortar'].default_value = (0, 0, 0, 1)
    mort = g.inv(b.outputs['Fac'])
    c = g.mix(1.0, s['col'], g.mix(1.0, b.outputs['Color'], (.74, .73, .70), 'MULTIPLY'), 'MULTIPLY')
    sep = g.add('ShaderNodeSeparateXYZ')
    g.put(sep.inputs[0], uv)
    n1 = g.add('ShaderNodeTexNoise')
    tcn = g.add('ShaderNodeCombineXYZ')
    g.put(tcn.inputs[0], g.mul(sep.outputs[0], 7.0))
    g.put(tcn.inputs[1], g.mul(sep.outputs[1], .35))
    g.put(n1.inputs['Vector'], tcn.outputs[0])
    n1.inputs['Detail'].default_value = 6
    n1.inputs['Scale'].default_value = 1.0
    top = g.rng(sep.outputs[1], .1, 1.65)
    st = g.mul(g.rng(n1.outputs[0], .42, .62), top)
    c = g.mix(g.mul(st, .7), c, (.09, .08, .06), 'MULTIPLY')
    low = g.inv(g.rng(sep.outputs[1], -.05, .4))
    c = g.mix(g.mul(low, .6), c, (.14, .13, .1), 'MULTIPLY')
    c = g.mix(mort, c, (.1, .095, .09))
    n = g.bump(g.sub(s['disp'], g.mul(mort, .9)), .008)
    return g.finish(c, g.add_(g.mul(s['rough'], .85), .1), n)

def m_pole():
    g = G('pole')
    uv = g.uv()
    s = g.antitile(uv, 'brushed_concrete', 1.8, .3)
    sep = g.add('ShaderNodeSeparateXYZ')
    g.put(sep.inputs[0], uv)
    u, v = sep.outputs[0], sep.outputs[1]
    cb = g.add('ShaderNodeCombineXYZ')
    g.put(cb.inputs[0], g.mul(u, 11.0))
    g.put(cb.inputs[1], g.mul(v, .28))
    streaks = g.noise(cb.outputs[0], 1.0, 7, .6)
    c = g.mix(1.0, s['col'], (.58, .6, .61), 'MULTIPLY')
    # 雨痕竖向变暗，煤烟随高度减弱
    c = g.mix(g.mul(g.rng(streaks, .40, .66), .7), c, (.2, .185, .16), 'MULTIPLY')
    rust = g.rng(g.noise(cb.outputs[0], 2.6, 5, .6), .6, .72)
    c = g.mix(g.mul(rust, .48), c, (.32, .15, .06))
    # 根部泥水溅痕和青苔
    low = g.inv(g.rng(g.add_(v, g.mul(g.sub(streaks, .5), .9)), .05, .7))
    c = g.mix(g.mul(low, .72), c, (.075, .07, .055), 'MULTIPLY')
    moss = g.mul(g.inv(g.rng(v, .0, .28)), g.rng(g.noise(uv, 8, 5, .6), .5, .66))
    c = g.mix(g.mul(moss, .7), c, (.035, .055, .015))
    # 虎纹标示贴：z 0.4–2.0 米，有撕破和褪色
    ang = g.add_(g.mul(v, 4.6), g.mul(u, 1.99))
    stripe = g.rng(g.math('SINE', g.mul(ang, 3.1416)), -.08, .08)
    band = g.mul(g.rng(v, .42, .44), g.inv(g.rng(v, 1.76, 1.78)))
    torn = g.rng(g.add_(g.noise(uv, 9, 6, .62), g.mul(g.inv(g.rng(v, .4, 1.0)), .12)), .63, .69)
    label = g.mul(band, g.inv(g.mul(torn, 1.0)))
    lc = g.mix(stripe, (.47, .33, .06), (.03, .03, .03))
    scuff = g.rng(g.noise(uv, 34, 7, .7), .5, .72)
    lc = g.mix(g.mul(scuff, .5), lc, (.2, .19, .16))
    lc = g.mix(g.mul(g.rng(streaks, .3, .68), .78), lc, (.3, .28, .23), 'MULTIPLY')
    c = g.mix(label, c, lc)
    rough = g.mixf(label, g.add_(g.mul(s['rough'], .85), .1), .58)
    n = g.bump(g.add_(s['disp'], g.mul(label, .08)), .004)
    return g.finish(c, rough, n)

def m_steel(name='steel', paint=None, rust_amt=.8):
    g = G(name)
    uv = g.uv()
    r = g.pbr(uv, 'rusty_metal_02', .6)
    ao = g.ao(.08, 4)
    nz = g.noise(uv, 9, 7, .6)
    mask = g.rng(g.add_(g.mul(g.sub(nz, .5), 2.2), g.mul(g.inv(ao), 1.1)), .05, .36)
    mask = g.mul(mask, rust_amt)
    base = paint or (.2, .205, .21)
    c = g.mix(.25, base, g.mix(.5, r['col'], base))
    c = g.mix(mask, c, r['col'])
    c = g.mix(g.mul(g.rng(nz, .3, .7), .4), c, (.3, .28, .24), 'MULTIPLY')
    metal = g.mixf(mask, 0.25 if paint else .85, .1)
    rough = g.mixf(mask, .48, .82)
    n = g.bump(g.add_(g.mul(r['disp'], .5), g.mul(mask, .25)), .002)
    return g.finish(c, rough, n, metal)

def m_simple(name, col, rough, spec=.5):
    g = G(name)
    uv = g.uv()
    n = g.noise(uv, 18, 5)
    c = g.mix(g.mul(g.rng(n, .35, .75), .5), col, (.45, .43, .38), 'MULTIPLY')
    return g.finish(c, rough, spec=spec)

def m_weed():
    g = G('weed')
    uv = g.uv()
    rand = g.add('ShaderNodeObjectInfo').outputs['Random']
    n = g.noise(uv, 7, 4)
    c = g.mix(g.rng(n, .38, .62), (.035, .075, .018), (.13, .14, .035))
    c = g.mix(g.rng(g.noise(uv, 23, 4), .6, .72), c, (.2, .15, .06))
    p = g.add('ShaderNodeBsdfPrincipled')
    g.put(p.inputs['Base Color'], c)
    p.inputs['Roughness'].default_value = .45
    t = g.add('ShaderNodeBsdfTranslucent')
    g.put(t.inputs['Color'], g.mix(.5, c, (.2, .3, .05)))
    m = g.add('ShaderNodeMixShader')
    m.inputs[0].default_value = .35
    g.nt.links.new(p.outputs[0], m.inputs[1])
    g.nt.links.new(t.outputs[0], m.inputs[2])
    o = g.add('ShaderNodeOutputMaterial')
    g.nt.links.new(m.outputs[0], o.inputs[0])
    return g.mat

def m_far():
    # 远景楼：砖纹节点当窗格，一层薄雾盖住细节
    g = G('far')
    v = g.add('ShaderNodeTexCoord').outputs['Object']
    sp_ = g.add('ShaderNodeSeparateXYZ')
    g.put(sp_.inputs[0], v)
    cb_ = g.add('ShaderNodeCombineXYZ')
    g.put(cb_.inputs[0], g.add_(sp_.outputs[0], sp_.outputs[1]))
    g.put(cb_.inputs[1], sp_.outputs[2])
    b = g.add('ShaderNodeTexBrick', offset=0.0)
    g.put(b.inputs['Vector'], cb_.outputs[0])
    b.inputs['Scale'].default_value = 1.0
    b.inputs['Mortar Size'].default_value = .6
    b.inputs['Brick Width'].default_value = 3.0
    b.inputs['Row Height'].default_value = 3.2
    b.inputs['Color1'].default_value = (.03, .035, .045, 1)
    b.inputs['Color2'].default_value = (.05, .05, .055, 1)
    b.inputs['Mortar'].default_value = (.27, .26, .24, 1)
    return g.finish(b.outputs['Color'], .5)

GLOW = []

def m_glow():
    g = G('glass_warm')
    p = g.add('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = (.02, .02, .02, 1)
    p.inputs['Roughness'].default_value = .1
    p.inputs['Emission Color'].default_value = (1, .58, .26, 1)
    # 窗帘后的灯：有明有暗，不是一块白板
    val = g.add('ShaderNodeValue')
    GLOW.append(val)
    uv = g.uv()
    cur = g.rng(g.noise(uv, .9, 1, .3), .3, .7, .6, 1.0)
    g.put(p.inputs['Emission Strength'], g.mul(val.outputs[0], cur))
    o = g.add('ShaderNodeOutputMaterial')
    g.nt.links.new(p.outputs[0], o.inputs[0])
    return g.mat

MATS = dict(weed=m_weed(), road=m_road(), far=m_far(),
            awn_a=m_simple('awn_a', (.2, .05, .04), .6), awn_b=m_simple('awn_b', (.05, .14, .09), .6), awn_c=m_simple('awn_c', (.42, .4, .35), .6),
            pavers=m_concrete('pavers', 'red_brick_pavers', .95, (.86, .8, .78), .01, .8, .1, True),
            brick=m_concrete('brick', 'red_brick', 1.5, (.92, .86, .8), .008, .65, .2, True),
            soil=m_concrete('soil', 'dirty_concrete', 1.0, (.2, .16, .12), .006, .5, .3),
            apt=m_concrete('apt', 'painted_plaster_wall', 3.2, (.86, .85, .82), .002, .6, .4),
            apt2=m_concrete('apt2', 'painted_plaster_wall', 2.6, (.74, .76, .77), .0015, .5, .5),
            plaster=m_concrete('plaster', 'painted_plaster_wall', 3.4, (.95, .9, .8), .002, .65, .6),
            siding=m_concrete('siding', 'weathered_plank_siding', 2.4, (.72, .68, .64), .006, .6, .7, True),
            roof=m_concrete('roof', 'grey_roof_tiles', 2.2, (.66, .66, .68), .016, .55, .1, True),
            shutter=m_concrete('shutter', 'wood_shutter', 1.4, (.7, .62, .54), .004, .5, .2, True),
            wood=m_simple('wood', (.05, .035, .025), .6),
            ac=G('ac').finish((.5, .5, .48), .42),
            glass_warm=m_glow(),
            glass=m_glass(), lens=m_lens(),
            ad=m_img('ad', 'pole_ad.png', rough=.35), tag=m_img('tag', 'pole_tag.png', rough=.4),
            rail_green=m_rail('rail_green', (.035, .10, .055)), rail_top=m_rail('rail_top', (.13, .06, .03), .35), manhole=m_manhole(),
            cover=m_concrete('cover', 'concrete_floor_worn_001', 2.2, (.72, .71, .68), .004, .85),
            apron=m_concrete('apron', 'dirty_concrete', 2.6, (.66, .65, .62), .004, .8, .5),
            house=m_concrete('house', 'dirty_concrete', 6.5, (.82, .80, .76), .0015, .35, .8),
            stone=m_stone(), mortar=m_mortar(), wall_stone=m_wall_stone(), block_wall=m_block_wall(),
            pole=m_pole(), steel=m_steel(), rusty=m_steel('rusty', None, 1.0),
            xfmr=m_steel('xfmr', (.17, .18, .185), .45),
            porcelain=m_simple('porcelain', (.48, .45, .40), .2, .6),
            wire=m_simple('wire', (.016, .016, .017), .46),
            cable=m_simple('cable', (.012, .012, .012), .62),
            pipe=m_simple('pipe', (.34, .35, .33), .5))

# ---------- 网格小工具 ----------
ALL = []

def mesh(name, verts, faces, mat, uvf=None, smooth=False, vcol=None, wn=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    me.materials.append(MATS[mat])
    if uvf:
        uvl = me.uv_layers.new(name='UV0')
        co = np.array(verts)
        for lp in me.loops:
            uvl.data[lp.index].uv = uvf(co[lp.vertex_index])
    if smooth:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(smooth if smooth is not True else 45))
    if vcol is not None:
        a = me.color_attributes.new('vcol', 'FLOAT_COLOR', 'POINT')
        a.data.foreach_set('color', np.array(vcol, 'f').ravel())
    ALL.append(ob)
    return ob

def box_uv(me, off=(0, 0), name='UV0'):
    uvl = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    for p in me.polygons:
        ax = int(np.argmax(np.abs(p.normal)))
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a, b = {0: (co.y, co.z), 1: (co.x, co.z), 2: (co.x, co.y)}[ax]
            uvl.data[li].uv = (a + off[0], b + off[1])

def bbox(name, mn, mx, mat, r=.008, seg=2, tilt=None, off=None, drop_bottom=True):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    mn, mx = np.array(mn, float), np.array(mx, float)
    for v in bm.verts:
        v.co = Vector((mn + mx) / 2 + (np.array(v.co) * (mx - mn)))
    if r > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=r, segments=seg, profile=.5,
                        affect='EDGES', clamp_overlap=True)
    if drop_bottom:
        low = [f for f in bm.faces if f.normal.z < -.9]
        bmesh.ops.delete(bm, geom=low, context='FACES_ONLY')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    me.materials.append(MATS[mat])
    box_uv(me, off if off is not None else tuple(rng.uniform(0, 5, 2)))
    if r > 0:
        me.shade_smooth()
        m = ob.modifiers.new('wn', 'WEIGHTED_NORMAL')
        m.keep_sharp = True
    if tilt is not None:
        c = (mn + mx) / 2
        ob.matrix_world = __import__('mathutils').Matrix.Translation(Vector(c)) @ \
            __import__('mathutils').Euler(tilt).to_matrix().to_4x4() @ \
            __import__('mathutils').Matrix.Translation(-Vector(c))
    ALL.append(ob)
    return ob

def road_z(x, y):
    return -.06 * ((x + .2) / 2.4) ** 2 + .004 * math.sin(x * 1.7 + y * .9) + .003 * math.sin(y * 2.3 - x)

# ---------- 路面 ----------
def build_road():
    # 密网格承接真实置换
    xs = np.arange(-2.6, 2.2001, .012)
    ys = np.arange(-5.0, 1.4001, .012)
    ys = np.concatenate([np.arange(-62, -5, .05), ys])
    nx, ny = len(xs), len(ys)
    gx, gy = np.meshgrid(xs, ys)
    gz = -.06 * ((gx + .2) / 2.4) ** 2 + .004 * np.sin(gx * 1.7 + gy * .9) + .003 * np.sin(gy * 2.3 - gx)
    co = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], 1).astype('f')
    idx = np.arange(nx * ny).reshape(ny, nx)
    q = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new('road')
    me.vertices.add(len(co))
    me.vertices.foreach_set('co', co.ravel())
    me.loops.add(q.size)
    me.loops.foreach_set('vertex_index', q.ravel())
    me.polygons.add(len(q))
    me.polygons.foreach_set('loop_start', np.arange(len(q)) * 4)
    me.update(calc_edges=True)
    uvl = me.uv_layers.new(name='UV0')
    uvl.data.foreach_set('uv', co[q.ravel()][:, :2].ravel())
    uv1 = me.uv_layers.new(name='UV1')
    b0 = np.array([-2.6, -62.0], 'f')
    uv1.data.foreach_set('uv', ((co[q.ravel()][:, :2] - b0) / np.array([4.8, 63.4], 'f')).ravel())
    me.shade_smooth()
    me.materials.append(MATS['road'])
    ob = bpy.data.objects.new('road', me)
    scene.collection.objects.link(ob)
    ALL.append(ob)

def build_manhole(cx=1.15, cy=-2.1, R=.375):
    rings = [0, .1, .16, .30, .34, .365, R, R + .012]
    zs = [.0, 0, 0, 0, 0, 0, 0, -.006]
    segs = 48
    v = [(0, 0, .0)]
    for r, z in zip(rings[1:], zs[1:]):
        v += [(r * math.cos(a), r * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, segs, endpoint=False)]
    f = [(0, 1 + i, 1 + (i + 1) % segs) for i in range(segs)]
    for k in range(len(rings) - 2):
        b = 1 + k * segs
        f += [(b + i, b + segs + i, b + segs + (i + 1) % segs, b + (i + 1) % segs) for i in range(segs)]
    ob = mesh('manhole', v, f, 'manhole', uvf=lambda c: (c[0] / (2 * R) + .5, c[1] / (2 * R) + .5), smooth=70)
    ob.location = (cx, cy, road_z(cx, cy) + .0012)
    ob.rotation_euler = (math.atan((road_z(cx, cy + .3) - road_z(cx, cy - .3)) / .6) * 1.0,
                        -math.atan((road_z(cx + .3, cy) - road_z(cx - .3, cy)) / .6), 0)

def build_gutters():
    # 水沟暗底
    bbox('gutter_R_base', (2.2, -62, -.3), (2.62, 1.4, -.2), 'mortar', 0)
    bbox('gutter_L_base', (-3.02, -62, -.3), (-2.6, 1.4, -.2), 'mortar', 0)
    for side, x0, x1 in (('R', 2.205, 2.6), ('L', -3.0, -2.605)):
        y = -62.0
        k = 0
        while y < 1.3:
            ln = .6
            jz = float(rng.uniform(-.004, .004))
            top = -.052 + jz
            grate = k % 17 in (5, 8) if side == 'R' else k % 23 == 6
            yy = min(y + ln - .008, 1.39)
            if grate:
                build_grate(f'grate_{side}{k}', x0, x1, y, yy, top)
            else:
                bbox(f'cover_{side}{k}', (x0, y, top - .09), (x1, yy, top), 'cover', .009,
                     tilt=(float(rng.uniform(-.004, .004)), float(rng.uniform(-.006, .006)), float(rng.uniform(-.004, .004))))
            y += ln
            k += 1

def build_grate(name, x0, x1, y0, y1, top):
    # 钢格栅：外框 + 12 根扁钢，真实几何
    bbox(name + '_f1', (x0, y0, top - .03), (x1, y0 + .025, top), 'rusty', .002, 1)
    bbox(name + '_f2', (x0, y1 - .025, top - .03), (x1, y1, top), 'rusty', .002, 1)
    bbox(name + '_f3', (x0, y0, top - .03), (x0 + .025, y1, top), 'rusty', .002, 1)
    bbox(name + '_f4', (x1 - .025, y0, top - .03), (x1, y1, top), 'rusty', .002, 1)
    for i in range(1, 15):
        y = y0 + (y1 - y0) * i / 15
        bbox(f'{name}_b{i}', (x0 + .02, y - .004, top - .03), (x1 - .02, y + .004, top - .002), 'rusty', 0)

def build_ext():
    # 路外的混凝土地面（右侧）和远处地坪
    bbox('apron', (2.6, -62, -.25), (3.3, 1.42, -.04), 'apron', .012)
    bbox('ground_far', (-520, -520, -.5), (520, 520, -.32), 'apron', 0)

def stair_profile(y, z, tread, rise, r, dip, first):
    # 踢面根部插进下一级踏面，错缝时不露黑缝
    b = -.08 if first else -.03
    return [(y, z + b), (y, z + rise - r), (y + r * .3, z + rise - r * .3), (y + r, z + rise - dip * .2),
            (y + tread * .5, z + rise - dip), (y + tread + .012, z + rise)]

def build_stairs(n=36, X0=-2.4, X1=2.6, Y0=1.4, Z0=.02, tread=.40, rise=.122):
    v, f, c, ut = [], [], [], []
    rs = np.random.default_rng(36)
    for i in range(n):
        y0 = Y0 + i * tread
        z0 = Z0 + i * rise
        x = X0
        while x < X1:
            L = .625
            x1 = min(x + L, X1 + .1)
            xa = max(x, X0 - .1) + .0015
            xb = x1 - .0015
            stn = np.linspace(xa, xb, 16)
            blk = float(rng.random())
            dz = float(rng.uniform(-.005, .005))
            dy = float(rng.uniform(-.006, .006))
            tz = float(rng.uniform(-.005, .005))
            mid = (xa + xb) / 2
            base = len(v)
            lay = int(rs.integers(4))
            fl = rs.random() < .5
            # 前缘缺角：连续的小崩口，不是逐点随机
            chips = np.zeros(len(stn))
            for _ in range(int(rs.integers(0, 4))):
                ca, cw, cd = rs.uniform(xa, xb), rs.uniform(.015, .07), rs.uniform(.004, .013)
                chips += cd * np.exp(-((stn - ca) / cw) ** 2)
            for si, sx in enumerate(stn):
                # 中间人流磨损：边缘更圆、踏面下凹
                w = math.exp(-((sx + .3) / 1.25) ** 2) * (.8 + .2 * rng.random())
                rng.random()
                chip = float(min(chips[si], .013))
                # 头尾留一点毛边
                r = .008 + .012 * w + float(rng.uniform(0, .004))
                rows = stair_profile(y0 + dy, z0 + dz + (sx - mid) * tz, tread, rise, r, .0035 * w, i == 0)
                for k, (py, pz) in enumerate(rows):
                    # 缺角只吃掉踏步前缘，不动踢面根部
                    py += chip * {0: 0, 1: .5, 2: 1, 3: .12, 4: 0, 5: 0}[k]
                    pz -= chip * {0: 0, 1: 0, 2: .5, 3: .08, 4: 0, 5: 0}[k]
                    wall = max(math.exp(-((sx - X0) / .35) ** 2), math.exp(-((sx - X1) / .35) ** 2))
                    d = {0: .9, 1: .42, 2: .12, 3: .1, 4: .3, 5: .78}[k]
                    d = min(1, d + wall * .45 + .1 * (1 - w))
                    wr = {0: 0, 1: .1, 2: 1, 3: 1, 4: .7, 5: .1}[k] * w
                    v.append((sx, py, pz))
                    c.append((blk, wr, d, 1))
                    us_ = (sx - xa) / (xb - xa)
                    ut.append((1 - us_ if fl else us_, (lay + {3: .11, 4: .58, 5: .98}.get(k, .02)) / 4))
            m = len(stn)
            for a in range(m - 1):
                for k in range(5):
                    p = base + a * 6 + k
                    f.append((p, p + 6, p + 7, p + 1))
            x = x1
    def stuv(co):
        return (co[0], co[1] + co[2] * 1.4)
    ob = mesh('stairs', v, f, 'stone', uvf=stuv, smooth=48, vcol=c)
    ul = ob.data.uv_layers.new(name='UVT')
    for lp in ob.data.loops:
        ul.data[lp.index].uv = ut[lp.vertex_index]
    for i in range(n):
        y0 = Y0 + i * tread
        z0 = Z0 + i * rise
        bbox(f'stair_grout_{i}', (X0 - .1, y0 + .016, z0 - .1), (X1 + .1, y0 + tread + .02, z0 + rise - .012), 'mortar', 0)
    # 平台：台阶顶延伸
    ytop = Y0 + n * tread
    ztop = Z0 + n * rise
    bbox('landing_grout', (X0 - .1, ytop, ztop - .3), (X1 + .1, 60, ztop - .012), 'mortar', 0)
    for j in range(46):
        y = ytop + .01 + j * .92
        x = X0 - (j % 2) * .45
        k = 0
        while x < X1:
            xn = min(x + float(rng.uniform(.9, 1.3)), X1 + .1)
            bbox(f'landing_{j}_{k}', (max(x, X0 - .1) + .003, y, ztop - .1), (xn - .003, y + .9, ztop + float(rng.uniform(-.0015, .0015))), 'apron', .006, 1)
            x = xn
            k += 1
    return ytop, ztop

def slope_wall(name, x0, x1, ya, yb, zb, top_fn, mat, n=12):
    # 沿 y 方向的矮墙，顶线由 top_fn(y) 给出，墙面略带外倾
    ys = np.linspace(ya, yb, n + 1)
    v = []
    for y in ys:
        zt = top_fn(y)
        v += [(x0, y, zb), (x0 + .02 * np.sign(x1 - x0), y, zt), (x1, y, zt), (x1, y, zb)]
    f = []
    for j in range(n):
        p = j * 4
        f += [(p, p + 1, p + 5, p + 4), (p + 1, p + 2, p + 6, p + 5), (p + 2, p + 3, p + 7, p + 6)]
    me = mesh(name, v, f, mat).data
    box_uv(me, tuple(rng.uniform(0, 3, 2)))
    bpy.context.view_layer.objects.active = None
    return me

def build_walls(ytop, ztop, Y0=1.4, tread=.33, rise=.122):
    def stair_h(y):
        return .02 + max(0, min((y - Y0) / tread, 10)) * rise
    slope_wall('retain_L', -3.0, -3.4, 1.0, 16, -.2, lambda y: stair_h(y) + 1.55, 'wall_stone', 16)
    slope_wall('retain_R', 2.6, 2.95, 1.42, 16, -.2, lambda y: stair_h(y) + .72, 'wall_stone', 16)
    # 墙端方柱，收住矮墙的断头
    bbox('pier_R', (2.56, 1.32, -.1), (3.02, 1.74, 1.02), 'cover', .022)
    bbox('pier_R_cap', (2.52, 1.28, 1.02), (3.06, 1.78, 1.1), 'cover', .018)
    # 砌块墙：沿路左侧
    bbox('block_wall', (-3.14, -16, -.05), (-3.02, 1.0, 1.6), 'block_wall', .004, 1, off=(0, 0))
    bbox('block_cap', (-3.17, -16, 1.6), (-2.99, 1.0, 1.66), 'cover', .01)
    # 灰盒占位房屋
    def house(name, mn, mx):
        bbox(name, mn, mx, 'house', 0)
        bbox(name + '_eave', (mn[0] - .5, mn[1] - .5, mx[2]), (mx[0] + .5, mx[1] + .5, mx[2] + .18), 'house', .01)
    house('ph_R1', (3.9, -16, 0), (9, -5, 5.6))
    house('ph_R2', (3.9, -4.5, 0), (9, 1.0, 5.2))
    house('ph_R3', (4.5, 2.2, 0), (10, 10, 6.6))
    house('ph_L1', (-10, -16, 0), (-4.1, -4.5, 6.4))
    house('ph_L2', (-10, -3.8, 0), (-4.1, 1.0, 5.2))
    house('ph_L3', (-11, 2, 0), (-4.6, 10, 7.0))
    house('ph_top1', (-14, 12, 1.2), (-5.5, 24, 8.5))
    house('ph_top2', (4, 12, 1.2), (13, 26, 9))
    house('ph_far1', (-30, 30, 1.2), (-3, 38, 7.5))
    house('ph_far2', (-1, 32, 1.2), (30, 42, 8.8))
    bbox('ground_top', (-30, 14, .9), (30, 60, 1.2), 'apron', 0)

# ---------- 电线杆 ----------
def tube(name, pts, radii, sides, mat, uv_scale=1.0, smooth=True, cap=False):
    """沿折线生成圆管；radii 可为常数或列表。"""
    pts = [Vector(p) for p in pts]
    if not hasattr(radii, '__len__'):
        radii = [radii] * len(pts)
    v, f = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.orthogonal().normalized()
        b = t.cross(a).normalized()
        for s in range(sides):
            th = 2 * math.pi * s / sides
            v.append(tuple(p + (a * math.cos(th) + b * math.sin(th)) * radii[i]))
    for i in range(len(pts) - 1):
        for s in range(sides):
            n = (s + 1) % sides
            f.append((i * sides + s, i * sides + n, (i + 1) * sides + n, (i + 1) * sides + s))
    if cap:
        last = len(pts) - 1
        f.append(tuple(last * sides + s for s in range(sides)))
    return v, f

def merge_mesh(name, parts, mat, smooth=48):
    V, F = [], []
    for v, f in parts:
        o = len(V)
        V += v
        F += [tuple(i + o for i in p) for p in f]
    ob = mesh(name, V, F, mat, smooth=smooth)
    return ob

def cuv(me, sides_r=.16):
    """圆杆 UV：u=绕轴米数，v=高度米数。"""
    uvl = me.uv_layers.get('UV0') or me.uv_layers.new(name='UV0')
    for p in me.polygons:
        # 闭合处避免整圈回绕
        angs = [math.atan2(me.vertices[me.loops[l].vertex_index].co.y, me.vertices[me.loops[l].vertex_index].co.x) for l in p.loop_indices]
        hi = max(angs) - min(angs) > math.pi
        for li, a in zip(p.loop_indices, angs):
            co = me.vertices[me.loops[li].vertex_index].co
            if hi and a < 0:
                a += 2 * math.pi
            uvl.data[li].uv = (a * sides_r, co.z)

def bx(c, size, rot=0.0):
    """返回一个绕 z 旋转的小盒子（v, f），用于金具。"""
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    cr, sr = math.cos(rot), math.sin(rot)
    v = []
    for dx, dy, dz in [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]:
        x, y = dx * sx, dy * sy
        v.append((c[0] + x * cr - y * sr, c[1] + x * sr + y * cr, c[2] + dz * sz))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f

def lathe(c, prof, sides=8):
    v, f = [], []
    for r, z in prof:
        for s in range(sides):
            a = 2 * math.pi * s / sides
            v.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2] + z))
    for i in range(len(prof) - 1):
        for s in range(sides):
            n = (s + 1) % sides
            f.append((i * sides + s, i * sides + n, (i + 1) * sides + n, (i + 1) * sides + s))
    f.append(tuple((len(prof) - 1) * sides + s for s in range(sides)))
    return v, f

def build_pole(name, x, y, z0, H=12.0, xfmr=False, seed=0):
    r0 = .178
    rt = .095
    zs = [-.3, .45, 2.0, 4, 6, 8, 10, H - .1, H]
    prof = []
    for z in zs:
        t = (z + .3) / (H + .3)
        prof.append((r0 + (rt - r0) * t, z))
    prof[-1] = (rt * .55, H)
    sides = 12
    v, f = lathe((0, 0, 0), prof, sides)
    shaft = mesh(name, v, f, 'pole', smooth=70)
    cuv(shaft.data)
    shaft.location = (x, y, z0)
    tris = [shaft]

    armz = H - .55
    armz2 = H - 2.1
    parts = []
    # 腕金（横跨马路方向）与斜撑
    parts.append(bx((0, 0, armz), (1.9, .075, .075)))
    parts.append(bx((0, 0, armz - .30), (1.3, .05, .05)))
    parts.append(bx((0, 0, armz2), (1.5, .07, .07)))
    parts.append(tube('b', [(-.5, .05, armz), (0, .05, armz - .55)], .012, 4, '', cap=True)[:2])
    parts.append(tube('b', [(.5, .05, armz), (0, .05, armz - .55)], .012, 4, '', cap=True)[:2])
    # 抱箍
    for z in (armz, armz - .3, armz2, H - 3.2, 6.0, 5.4):
        t = (z + .3) / (H + .3)
        r = r0 + (rt - r0) * t + .007
        parts.append(lathe((0, 0, z - .03), [(r, 0), (r + .001, .06)], 12))
    # 足场螺栓：交替两侧
    for i, z in enumerate(np.arange(2.6, H - 1.4, .45)):
        t = (z + .3) / (H + .3)
        r = r0 + (rt - r0) * t
        a = math.pi / 2 * (1 if i % 2 else -1) + float(rng.uniform(-.06, .06))
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = d * (r - .01) + Vector((0, 0, z))
        p1 = d * (r + .13) + Vector((0, 0, z + .012))
        parts.append(tube('b', [p0, p1], .0095, 5, '', cap=True)[:2])
        parts.append(bx(tuple(p0 + d * .022), (.03, .03, .03), a))
    steel = merge_mesh(name + '_steel', parts, 'steel', 30)
    box_uv(steel.data, (seed * .7, 0))
    steel.location = (x, y, z0)

    ins = []
    tops = []
    for dx in (-.8, 0, .8):
        ins.append(lathe((dx, 0, armz + .04), [(.022, 0), (.052, .03), (.058, .05), (.03, .07), (.046, .10), (.05, .12), (.024, .14), (.016, .17)], 8))
        tops.append(Vector((x + dx, y, z0 + armz + .205)))
    lows = []
    for dx in (-.62, -.2, .2, .62):
        ins.append(lathe((dx, 0, armz2 + .04), [(.02, 0), (.04, .015), (.04, .07), (.02, .085)], 8))
        lows.append(Vector((x + dx, y, z0 + armz2 + .11)))
    pc = merge_mesh(name + '_ins', ins, 'porcelain', 35)
    box_uv(pc.data)
    pc.location = (x, y, z0)

    if xfmr:
        ox = -.36
        xp = [lathe((ox, .0, H - 4.15), [(.0, 0), (.19, .0), (.205, .025), (.205, .70), (.195, .73), (.17, .755), (.14, .77), (.0, .775)], 16)]
        xp.append(bx((ox + .2, 0, H - 3.85), (.3, .07, .06)))
        xp.append(bx((ox + .2, 0, H - 3.5), (.3, .07, .06)))
        for dx in (-.14, 0, .14):
            xp.append(lathe((ox + dx * .8, 0, H - 3.385), [(.018, 0), (.03, .018), (.018, .04), (.027, .06), (.015, .095)], 6))
        for a in range(16):
            th = a / 16 * 2 * math.pi
            if abs(th) < .35 or abs(th - 2 * math.pi) < .35:
                continue
            xp.append(bx((ox + .218 * math.cos(th), .218 * math.sin(th), H - 3.78), (.03, .007, .52), th))
        t = merge_mesh(name + '_xfmr', xp, 'xfmr', 30)
        box_uv(t.data)
        t.location = (x, y, z0)
    # 接地线护管
    gp = tube('g', [(-.02, r0 + .018, .0), (-.02, r0 + .002, 3.5), (-.02, rt + .03, H - 4.2)], .019, 5, '', cap=True)[:2]
    pip = merge_mesh(name + '_pipe', [gp], 'pipe', 60)
    box_uv(pip.data)
    pip.location = (x, y, z0)
    return tops, lows, Vector((x, y, z0))

def catenary(a, b, sag, n=20, side=.0):
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        s = 4 * sag * t * (1 - t)
        # 轻微不对称，看起来不是完美抛物线
        s *= 1 + .08 * math.sin(t * math.pi * 2)
        pts.append((p.x + side * math.sin(t * math.pi), p.y, p.z - s))
    return pts

def build_wires():
    tA, lA, a = build_pole('pole_A', 2.95, .55, -.04, xfmr=True, seed=0)
    tB, lB, b = build_pole('pole_B', 3.02, 24.0, 1.24 + .02 + .12 * 0, 12.0, seed=1)
    tZ, lZ, c = build_pole('pole_Z', 2.95, -26.0, -.04, 12.0, seed=2)
    parts = []
    sags = [.34, .36, .33]
    for i in range(3):
        parts.append(tube('w', catenary(tA[i], tB[i], sags[i], 18, .03 * (i - 1)), .0072, 5, '')[:2])
        parts.append(tube('w', catenary(tZ[i], tA[i], sags[i] * .95, 14), .0072, 5, '')[:2])
    for i in range(4):
        s = .55 + i * .06
        parts.append(tube('w', catenary(lA[i], lB[i], s, 18, .05), .0105, 5, '')[:2])
        parts.append(tube('w', catenary(lZ[i], lA[i], s, 14), .0105, 5, '')[:2])
    # 通信电缆：更粗更垂，一根吊线加一根光缆
    for dz, s, dx, r in ((6.05, .85, .23, .0135), (5.45, 1.05, .25, .0165), (5.2, 1.2, -.24, .011)):
        p0 = Vector((a.x + dx, a.y, a.z + dz))
        p1 = Vector((b.x + dx, b.y, b.z + dz - 1.2))
        p2 = Vector((c.x + dx, c.y, c.z + dz))
        parts.append(tube('w', catenary(p0, p1, s, 18, -.04), r, 6, '')[:2])
        parts.append(tube('w', catenary(p2, p0, s, 14), r, 6, '')[:2])
    # 接户线：过街到左边房子、到右边房子
    src = lA[0]
    parts.append(tube('w', catenary(src, Vector((-4.1, -2.0, 4.8)), .3, 12), .0065, 5, '')[:2])
    parts.append(tube('w', catenary(lA[1], Vector((-4.1, -1.2, 4.55)), .34, 12), .0065, 5, '')[:2])
    parts.append(tube('w', catenary(lA[3], Vector((3.9, -1.9, 4.6)), .05, 6), .0065, 5, '')[:2])
    parts.append(tube('w', catenary(lA[2], Vector((3.6, 2.8, 5.3)), .12, 8), .0065, 5, '')[:2])
    # 通信检修盘线：电缆旁一圈余线
    cx, cy, cz = a.x + .34, a.y + 1.4, a.z + 5.05
    coil = [(cx + .03 * math.sin(t * 3), cy + .2 * math.cos(t), cz + .2 * math.sin(t)) for t in np.linspace(0, 2 * math.pi * 1.9, 26)]
    parts.append(tube('w', coil, .0085, 5, '')[:2])
    # 变压器引下线
    for i in range(3):
        p = Vector((a.x - .36 + (i - 1) * .11, a.y, a.z + 8.71))
        parts.append(tube('w', catenary(tA[i] - Vector((0, 0, .12)), p, .04, 6), .005, 4, '')[:2])
    ob = merge_mesh('wires', parts, 'wire', 60)
    box_uv(ob.data)
    # 接头盒：挂在通信缆上的黑色长圆筒
    q = Vector((a.x + .25, a.y + 3.0, a.z + 5.45 - .2))
    cl = [lathe((0, 0, 0), [(0, -.3), (.05, -.27), (.06, -.2), (.06, .2), (.05, .27), (0, .3)], 8)]
    o2 = merge_mesh('closure', cl, 'cable', 50)
    box_uv(o2.data)
    o2.location = q
    o2.rotation_euler = (math.pi / 2, 0, 0)

# ---------- 缝隙杂草 ----------
def blade(cx, cy, cz, az, h, w, lean):
    d = np.array([math.cos(az), math.sin(az), 0])
    side = np.array([-d[1], d[0], 0])
    v = []
    for i, t in enumerate((0, .4, .75, 1)):
        p = np.array([cx, cy, cz]) + d * lean * h * t * t + np.array([0, 0, h * (t - .35 * lean * t * t)])
        wt = w * (1 - t ** 2.2)
        v += [tuple(p + side * wt / 2), tuple(p - side * wt / 2)] if i < 3 else [tuple(p)]
    return v, [(0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 6)]

def build_weeds():
    parts = []
    def tuft(cx, cy, cz, n, grass=True):
        for _ in range(n):
            a = float(rng.uniform(0, 2 * math.pi))
            ox, oy = rng.normal(0, .022, 2)
            if grass:
                parts.append(blade(cx + ox, cy + oy, cz, a, float(rng.uniform(.06, .2)), float(rng.uniform(.004, .008)), float(rng.uniform(.3, .95))))
            else:
                parts.append(blade(cx + ox * .4, cy + oy * .4, cz, a, float(rng.uniform(.05, .1)), float(rng.uniform(.016, .03)), float(rng.uniform(1.1, 1.5))))
    def sh(y):
        return .02 + max(0, min((y - 1.4) / .33, 10)) * .122
    for k, (x, y) in enumerate([(2.2, -4.2), (2.2, -3.05), (2.21, -.7), (2.2, .25), (-2.6, -2.4), (-2.6, -.3), (-2.6, .85), (2.58, -1.6)]):
        tuft(x, y, road_z(max(min(x, 2.2), -2.6), y), 16, k % 3 != 1)
    for i, x in ((1, -2.97), (3, -2.96), (6, -2.97), (2, 2.56), (5, 2.55), (8, 2.56)):
        y = 1.4 + i * .33 + .29
        tuft(x, y, sh(y - .04) + .0, 14, i % 2 == 0)
    tuft(2.72, .32, -.04, 12)
    tuft(3.1, .75, -.04, 14)
    tuft(2.62, 1.2, -.04, 10, False)
    tuft(-2.3, 1.36, .0, 10)
    ob = merge_mesh('weeds', parts, 'weed', 80)
    box_uv(ob.data)

# ---------- 组装 ----------
t0 = time.time()
build_road()
build_manhole()
for cx_, cy_ in ((.4, -15.5), (-.6, -33.0), (.7, -48.0)):
    build_manhole(cx_, cy_)
build_gutters()
build_ext()
ytop, ztop = build_stairs()
qs_ext.build_all(globals(), ytop, ztop, .40, .122, 1.4, .02, 36)
qs_ext.build_plants(globals(), 1.4, .02, .40, .122, 36, ROOT + r'\assets\models')
print('BUILD', round(time.time() - t0, 1), 's objs', len(ALL))

# UV1 光照贴图层，只给会进游戏的件；占位盒不用
def add_uv1():
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.name.startswith(('ph_', 'ground', 'h_', 'apt', 'road')) or len(ob.data.polygons) > 40000 or not ob.data.is_editable or ob.hide_render or '_i' in ob.name:
            continue
        me = ob.data
        if 'UV0' not in me.uv_layers:
            box_uv(me)
        if 'UV1' in me.uv_layers:
            continue
        uv1 = me.uv_layers.new(name='UV1')
        me.uv_layers.active = uv1
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.004)
        bpy.ops.object.mode_set(mode='OBJECT')
        me.uv_layers.active = me.uv_layers['UV0']
        me.uv_layers['UV0'].active_render = True

add_uv1()

# 统计
stats = {}
dg = bpy.context.evaluated_depsgraph_get()
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        me = ob.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        stats[ob.name] = len(me.loop_triangles)
        ob.evaluated_get(dg).to_mesh_clear()
groups = {}
for k, v in stats.items():
    g = k.split('_')[0] + ('_' + k.split('_')[1] if k.startswith('pole_') else '')
    groups[g] = groups.get(g, 0) + v
print('TRIS', json.dumps(groups))
no_uv1 = []
imgs = {i.name: tuple(i.size) for i in bpy.data.images if i.size[0] and not i.name.endswith('.hdr')}
over = {k: v for k, v in imgs.items() if max(v) > 2048}
print('CHECK no_uv1', no_uv1, 'images', len(imgs), 'over2k', over, 'max_tri_obj', max((v, k) for k, v in stats.items() if not k.startswith(('ph_', 'ground'))))

# ---------- 机位 ----------
def camera(name, loc, target, lens):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = 36
    ob = bpy.data.objects.new(name, cam)
    scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob

CAM = dict(west=camera('cam_west', (1.2, 15.2, ztop + 1.6), (-.2, -40, 3.4), 27),
           street=camera('cam_street', (-.5, -34, 1.6), (.3, 14, 3.4), 27),
           mid=camera('cam_mid', (-1.4, 9.0, .02 + (9.0 - 1.4) / .4 * .122 + 1.6), (.4, -30, 3.5), 30),
           main=camera('cam_main', (-1.1, -4.7, 1.6), (1.0, 6.0, 2.0), 24),
           steps=camera('cam_steps', (-1.1, .3, 1.6), (-1.1, 2.3, .32), 32),
           road=camera('cam_road', (.2, -3.45, 1.6), (1.1, -1.9, -.02), 32),
           sky=camera('cam_sky', (.2, -3.0, 1.6), (2.95, 1.2, 9.0), 30),
           pole=camera('cam_pole', (1.3, -.75, 1.6), (2.95, .55, 1.15), 32))

# ---------- 光 ----------
def hdri_sun(path):
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, 'f')
    img.pixels.foreach_get(px)
    lum = px.reshape(h, w, 4)[..., :3].sum(2)
    lum[:h // 2] = 0
    i = int(np.argmax(lum))
    r, c = i // w, i % w
    return (.5 - (c + .5) / w) * 2 * math.pi, ((r + .5) / h - .5) * math.pi, float(lum[r, c] / 3)

LIGHT = dict(morning=dict(hdr='kloofendal_48d_partly_cloudy_puresky_4k.hdr', az=100, el=38, sun=4.0, col=(1, .92, .8), angle=1.0, strength=1.9, cap=8, exposure=.5, fog=.0010, look='AgX - Base Contrast', glow=0, fogc=(1, 1, 1)),
             sunset=dict(hdr='qwantani_sunset_puresky_4k.hdr', az=268, el=6.1, sun=7.5, col=(1, .58, .3), angle=1.6, strength=.85, cap=9, exposure=.3, fog=.0010, glow=.38, fogc=(1, .8, .58), look='AgX - Medium High Contrast'))

def set_light(k):
    L = LIGHT[k]
    path = os.path.join(HDR, L['hdr'])
    phi, el, peak = hdri_sun(path)
    a = math.radians(L['az'])
    # +x=南，+y=东：罗盘角转数学角
    target = math.atan2(math.sin(a), -math.cos(a))
    rot = phi - target
    print('SUN', k, 'hdri_az', round(math.degrees(phi), 1), 'elev', round(math.degrees(el), 1), 'peak', round(peak, 1), 'rot', round(math.degrees(rot), 1))
    w = bpy.data.worlds.new(k)
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, rot)
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(path, check_existing=True)
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = L['strength']
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs[0], env.inputs['Vector'])
    # 压掉 HDRI 里的太阳，太阳高度和颜色交给太阳灯
    cap = nt.nodes.new('ShaderNodeVectorMath')
    cap.operation = 'MINIMUM'
    cap.inputs[1].default_value = (L['cap'], L['cap'], L['cap'])
    nt.links.new(env.outputs[0], cap.inputs[0])
    nt.links.new(cap.outputs[0], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w
    scene.view_settings.exposure = L['exposure']
    sd = bpy.data.objects.get('sun') or bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    if sd.name not in scene.collection.objects:
        scene.collection.objects.link(sd)
    sd.data.energy = L['sun']
    sd.data.color = L['col']
    sd.data.angle = math.radians(L['angle'])
    e = math.radians(L['el'])
    d = Vector((-math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
    sd.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    FOG.inputs['Density'].default_value = L['fog']
    FOG.inputs['Color'].default_value = (*L['fogc'], 1)
    scene.view_settings.look = L['look']
    for p_ in GLOW:
        p_.outputs[0].default_value = L['glow']

# 薄雾：空气透视和逆光光束
fm = bpy.data.materials.new('fog')
fm.use_nodes = True
fm.node_tree.nodes.clear()
FOG = fm.node_tree.nodes.new('ShaderNodeVolumeScatter')
FOG.inputs['Anisotropy'].default_value = .55
fo = fm.node_tree.nodes.new('ShaderNodeOutputMaterial')
fm.node_tree.links.new(FOG.outputs[0], fo.inputs['Volume'])
bm_ = bmesh.new()
bmesh.ops.create_cube(bm_, size=1.0)
for v_ in bm_.verts:
    v_.co = Vector((v_.co.x * 960, v_.co.y * 960 - 40, v_.co.z * 90 + 44))
fme = bpy.data.meshes.new('fog_box')
bm_.to_mesh(fme)
bm_.free()
fme.materials.append(fm)
fob = bpy.data.objects.new('fog_box', fme)
scene.collection.objects.link(fob)

# ---------- 渲染 ----------
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
print('DEVICES', [(d.name, d.type) for d in prefs.devices])
for d in prefs.devices:
    d.use = d.type == 'OPTIX'

scene.render.engine = 'CYCLES'
c = scene.cycles
c.device = 'GPU'
c.samples = SPP
c.use_adaptive_sampling = True
c.adaptive_threshold = .012
c.use_denoising = True
c.denoiser = 'OPTIX'
c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
c.max_bounces = 6
c.volume_bounces = 1
c.volume_max_steps = 256
c.diffuse_bounces = 3
c.glossy_bounces = 3
c.caustics_reflective = False
c.caustics_refractive = False
c.sample_clamp_indirect = 8
scene.render.use_persistent_data = True
scene.render.resolution_x = RES
scene.render.resolution_y = int(RES * 9 / 16)
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 90
scene.display_settings.display_device = 'sRGB'
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception as e:
    print('LOOK', e)

try:
    # 轻微泛光，太阳和高光边缘更像照片
    ng = bpy.data.node_groups.new('post', 'CompositorNodeTree')
    scene.compositing_node_group = ng
    rl = ng.nodes.new('CompositorNodeRLayers')
    gl = ng.nodes.new('CompositorNodeGlare')
    for k_, v_ in (('Type', 'Bloom'), ('Strength', .35), ('Threshold', 1.6), ('Size', .55)):
        if k_ in gl.inputs:
            gl.inputs[k_].default_value = v_
    if hasattr(gl, 'glare_type'):
        gl.glare_type = 'BLOOM'
    out_ = ng.nodes.new('NodeGroupOutput')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    ng.links.new(rl.outputs['Image'], gl.inputs['Image'])
    ng.links.new(gl.outputs[0], out_.inputs[0])
    scene.render.use_compositing = True
    print('BLOOM ok')
except Exception as e:
    print('BLOOM skipped', e)
blend = os.path.join(ROOT, 'blend', f'qs_{TAG}.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
print('SAVED', blend)

report = dict(tag=TAG, tris=groups, renders=[])
for k in LIGHTS:
    set_light(k)
    for cn in CAMS:
        scene.camera = CAM[cn]
        t = time.time()
        path = os.path.join(OUT, f'qs_{TAG}_{k}_{cn}.jpg')
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        dt = round(time.time() - t, 1)
        print('RENDERED', os.path.basename(path), dt, 's', flush=True)
        report['renders'].append(dict(file=path, sec=dt))
with open(os.path.join(OUT, f'qs_{TAG}_report.json'), 'w', encoding='utf-8') as fo:
    json.dump(report, fo, ensure_ascii=False, indent=1)
print('ALLDONE', flush=True)
# 跳过退出流程：Intel NPU 驱动在退出时会崩或卡住
os._exit(0)
