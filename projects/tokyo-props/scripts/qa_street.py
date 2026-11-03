# qa_street.py: acceptance render inside a real-proportion street, low sun + aerial haze, like the 5070 sample.
# blender -b -P qa_street.py -- <cfg key> <tag> [--spp 200] [--w 1600] [--cams a,b] [--light sunset|noon]
import bpy, sys, os, math, json, random
from mathutils import Vector
ROOT = r'D:\Cijian'
PH = os.path.join(ROOT, 'assets', 'polyhaven')
argv = sys.argv[sys.argv.index('--') + 1:]
key, tag = argv[0], argv[1]
def opt(k, d):
    return argv[argv.index(k) + 1] if k in argv else d
spp, W = int(opt('--spp', 200)), int(opt('--w', 1600))
light = opt('--light', 'sunset')
cfg = json.load(open(os.path.join(ROOT, 'scripts', 'street_cfg.json'), encoding='utf8'))[key]
STW = cfg.get('street_w', 4.6)  # kerb to kerb, y from -STW..0, shop wall at y=0
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'
p = bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type = 'OPTIX'
p.get_devices()
for d in p.devices:
    d.use = d.type == 'OPTIX'
c = s.cycles
c.device, c.samples, c.use_denoising, c.denoiser = 'GPU', spp, True, 'OPTIX'
c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.volume_bounces = 8, 4, 4, 1
c.volume_step_rate = 2.0
# whole-street scenes exceed 8 GB with 4K maps: cap textures for the acceptance render only
s.render.use_simplify = True
c.texture_limit_render = opt('--tex', '2048')
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'AgX - Base Contrast' if light == 'sunset' else 'None'
s.view_settings.exposure = float(opt('--ev', cfg.get('ev', 0.3)))
s.render.resolution_x, s.render.resolution_y = W, int(W * 9 / 16)
s.render.image_settings.file_format = 'JPEG'
s.render.image_settings.quality = 90

def tex(nt, tid, key_, cs='sRGB'):
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = bpy.data.images.get(tid + key_) or bpy.data.images.load(os.path.join(PH, tid, key_ + '.jpg'))
    n.image.name = tid + key_
    n.image.colorspace_settings.name = cs
    return n

def mat(name, tid, scale=1.0, val=1.0, sat=1.0, nor=1.0, rough=1.0, tint=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    P = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    d = tex(nt, tid, 'diff')
    d.projection = 'BOX'
    d.projection_blend = .15
    nt.links.new(mp.outputs[0], d.inputs[0])
    h = nt.nodes.new('ShaderNodeHueSaturation')
    h.inputs['Saturation'].default_value, h.inputs['Value'].default_value = sat, val
    nt.links.new(d.outputs[0], h.inputs['Color'])
    col = h.outputs[0]
    if tint:
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        mx.blend_type = 'MULTIPLY'
        mx.inputs[0].default_value = 1
        mx.inputs[7].default_value = (*tint, 1)
        nt.links.new(col, mx.inputs[6])
        col = mx.outputs[2]
    nt.links.new(col, P.inputs['Base Color'])
    r = tex(nt, tid, 'rough', 'Non-Color')
    r.projection = 'BOX'
    r.projection_blend = .15
    nt.links.new(mp.outputs[0], r.inputs[0])
    ma = nt.nodes.new('ShaderNodeMath')
    ma.operation = 'MULTIPLY'
    ma.inputs[1].default_value = rough
    nt.links.new(r.outputs[0], ma.inputs[0])
    nt.links.new(ma.outputs[0], P.inputs['Roughness'])
    # scanned height detail through the bump path works with box projection
    n = tex(nt, tid, 'nor', 'Non-Color')
    n.projection = 'BOX'
    n.projection_blend = .15
    nt.links.new(mp.outputs[0], n.inputs[0])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value = nor
    nt.links.new(n.outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], P.inputs['Normal'])
    return m

def box(name, size, loc, m):
    me = bpy.data.meshes.new(name)
    x, y, z = [v / 2 for v in size]
    vs = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(vs, [], fs)
    ob = bpy.data.objects.new(name, me)
    s.collection.objects.link(ob)
    me.materials.append(m)
    ob.location = loc
    return ob

asph = mat('asph', 'asphalt_02', .6, val=.85, sat=.7, nor=1.2)
conc = mat('conc', 'concrete_floor_worn_001', .7, val=.85, sat=.6, nor=1.2)
patch = mat('patch', 'worn_asphalt', .55, val=.6, sat=.5, nor=1.3)
line = mat('line', 'concrete_floor_worn_001', 1.2, val=1.6, sat=.1, nor=1.0)
walls = [mat('w0', 'white_plaster_rough_01', .5, val=.72, sat=.55, nor=1.3),
         mat('w1', 'worn_cracked_plaster', .45, val=.7, sat=.7, nor=1.4),
         mat('w2', 'painted_plaster_wall', .5, val=.6, sat=.7, nor=1.2),
         mat('w3', 'long_white_tiles', .8, val=.65, sat=.5, nor=1.0),
         mat('w4', 'weathered_plank_siding', .5, val=.55, sat=.7, nor=1.2)]
shut = mat('shut', 'painted_metal_shutter', .9, val=.7, sat=.5, nor=1.2)
win = bpy.data.materials.new('win')
win.use_nodes = True
Pw = win.node_tree.nodes['Principled BSDF']
Pw.inputs['Base Color'].default_value = (.01, .012, .014, 1)
Pw.inputs['Roughness'].default_value = .06
Pw.inputs['Specular IOR Level'].default_value = .8
lit = bpy.data.materials.new('lit')
lit.use_nodes = True
Pl = lit.node_tree.nodes['Principled BSDF']
Pl.inputs['Base Color'].default_value = (.1, .08, .05, 1)
Pl.inputs['Emission Color'].default_value = (1, .68, .36, 1)
Pl.inputs['Emission Strength'].default_value = .55
L = cfg.get('len', 70)
random.seed(4)
# ground: repeated road asset when available, mirrored every other tile to hide repeats
box('under', (L + 40, STW + 40, .4), (0, -STW / 2, -.32), asph)
# both street walls: buildings at PLATEAU frontage widths/heights (see street_cfg.json)
def row(y0, sgn, spec):
    x = spec[0]
    i = 0
    for w_, h_, k in spec[1:]:
        cx = x + w_ / 2
        b = box('bld', (w_, 8, h_), (cx, y0 + sgn * 4, h_ / 2), walls[k % len(walls)])
        for fl in range(1, int(h_ / 3)):
            for wx in (-w_ * .22, w_ * .22):
                g = box('wg', (1.3, .03, 1.15), (cx + wx, y0 - sgn * .015 + 0, fl * 2.95 + 1.1), lit if random.random() < .12 else win)
                box('wf', (1.42, .02, 1.27), (cx + wx, y0 - sgn * .004, fl * 2.95 + 1.1), walls[2])
        # shop level band
        gs = box('sh', (w_ - .5, .04, 2.3), (cx, y0 - sgn * .02, 1.15), shut)
        box('awn', (w_ - .2, .55, .03), (cx, y0 - sgn * .275, 2.6), shut)
        x += w_
        i += 1
for spec_ in cfg['south']:
    row(0.0, 1, spec_)
row(-STW, -1, cfg['north'])
# poles and sagging cables down the street
wire = bpy.data.materials.new('wire')
wire.use_nodes = True
wire.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.01, .01, .01, 1)
wire.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .5
def cable(a, b, sag, r=.012):
    cu = bpy.data.curves.new('c', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 1
    sp = cu.splines.new('POLY')
    sp.points.add(23)
    for i in range(24):
        t = i / 23
        pt = Vector(a).lerp(Vector(b), t)
        pt.z -= sag * 4 * t * (1 - t)
        sp.points[i].co = (*pt, 1)
    ob = bpy.data.objects.new('c', cu)
    s.collection.objects.link(ob)
    cu.materials.append(wire)
poles = [(-30 + i * 19, -STW + .28) for i in range(4)]
polem = mat('pole', 'concrete_floor_worn_001', 1.2, val=.75, sat=.4, nor=1.2)
for px, py in poles:
    o = box('pole', (.3, .3, 11), (px, py, 5.5), polem)
    box('arm', (.1, .9, .1), (px, py + .3, 9.8), wire)
    box('arm', (.1, 1.2, .1), (px, py + .3, 8.9), wire)
for a, b in zip(poles, poles[1:]):
    for dy, z, sg, r in ((.7, 9.8, .32, .011), (.25, 9.8, .3, .011), (.7, 8.9, .42, .017), (.1, 8.9, .45, .017), (.4, 7.9, .55, .02)):
        cable((a[0], a[1] + dy, z), (b[0], b[1] + dy, z), sg, r)
    cable((a[0], a[1] + .4, 7.9), (a[0] + 7, -.1, 5.2), .5, .009)
# assets
for a in cfg['assets']:
    n, loc, rz = a[0], a[1], a[2]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'export', 'props', n, n + '.glb'))
    new = set(bpy.data.objects) - before
    keep = []
    for o in list(new):
        if '_COL' in o.name or '_LOD1' in o.name or '_LOD2' in o.name:
            bpy.data.objects.remove(o)
        else:
            keep.append(o)
    for o in [o for o in keep if o.parent is None]:
        o.location = loc
        o.rotation_mode = 'XYZ'  # glTF import uses quaternions; euler edits would be ignored
        o.rotation_euler[2] += math.radians(rz)
        if len(a) > 3:  # repeat along the street, flipping every other tile
            step, n = a[3], a[4]
            for k in range(1, n):
                c2 = o.copy()
                s.collection.objects.link(c2)
                c2.location = (loc[0] + k * step, loc[1], loc[2])
                if k % 2:
                    c2.scale[0] = -1
# extra lights the engine must also place: warm fill inside open shops
for l_ in cfg.get('lights', []):
    ld = bpy.data.lights.new('fill', 'POINT')
    ld.energy = l_[3]
    ld.color = (1, .86, .66)
    ld.shadow_soft_size = .6
    lo = bpy.data.objects.new('fill', ld)
    s.collection.objects.link(lo)
    lo.location = l_[:3]
# light: low sun down the street axis, aerial haze, sky
w = bpy.data.worlds.new('w')
w.use_nodes = True
nt = w.node_tree
bg = nt.nodes['Background']
env = nt.nodes.new('ShaderNodeTexEnvironment')
hd = 'industrial_sunset_02_puresky' if light == 'sunset' else 'german_town_street'
env.image = bpy.data.images.load(os.path.join(PH, 'hdri', hd + '.hdr'))
nt.links.new(env.outputs[0], bg.inputs['Color'])
bg.inputs['Strength'].default_value = .55 if light == 'sunset' else .8
s.world = w
sun = bpy.data.lights.new('sun', 'SUN')
sun.energy = float(opt('--sun', cfg.get('sun', 5.0)))
sun.color = (1, .6, .32) if light == 'sunset' else (1, .95, .88)
sun.angle = math.radians(1.2)
so = bpy.data.objects.new('sun', sun)
s.collection.objects.link(so)
el, az = (math.radians(cfg.get('sun_el', 9)), math.radians(cfg.get('sun_az', 12))) if light == 'sunset' else (math.radians(58), math.radians(35))
# points from -X (street axis) slightly toward the shop side
so.rotation_euler = (Vector((-math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)))).to_track_quat('Z', 'Y').to_euler()
# haze box
if light == 'sunset':
    vm = bpy.data.materials.new('haze')
    vm.use_nodes = True
    vt = vm.node_tree
    vt.nodes.remove(vt.nodes['Principled BSDF'])
    v = vt.nodes.new('ShaderNodeVolumePrincipled') if False else vt.nodes.new('ShaderNodeVolumeScatter')
    v.inputs['Color'].default_value = (1, .86, .72, 1)
    v.inputs['Density'].default_value = float(opt('--haze', cfg.get('haze', .012)))
    v.inputs['Anisotropy'].default_value = .62
    vt.links.new(v.outputs[0], vt.nodes['Material Output'].inputs['Volume'])
    box('haze', (L + 60, 60, 26), (0, -2, 12.9), vm)
out = os.path.join(ROOT, 'output', 'previews', tag)
os.makedirs(out, exist_ok=True)
for name in opt('--cams', ','.join(cfg['cams'])).split(','):
    cc = cfg['cams'][name]
    cam = bpy.data.cameras.new(name)
    cam.lens = cc.get('lens', 28)
    ob = bpy.data.objects.new(name, cam)
    s.collection.objects.link(ob)
    ob.location = cc['pos']
    ob.rotation_euler = (Vector(cc['at']) - Vector(cc['pos'])).to_track_quat('-Z', 'Y').to_euler()
    s.camera = ob
    s.render.filepath = os.path.join(out, '%s_%s_%s.jpg' % (key, name, light))
    bpy.ops.render.render(write_still=True)
    print('[qa] wrote', s.render.filepath, flush=True)
sys.stdout.flush()
os._exit(0)
