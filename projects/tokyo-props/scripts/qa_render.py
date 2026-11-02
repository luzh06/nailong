# qa_render.py: render the *exported GLB* (not the source shaders) from fixed cameras.
# blender -b -P qa_render.py -- <asset> <tag> [--spp 128] [--w 1280] [--cams hero,close,detail] [--light dusk|day]
import bpy, sys, os, math, json
from mathutils import Vector
ROOT = r'D:\Cijian'
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
argv = sys.argv[sys.argv.index('--') + 1:]
assets = argv[0].split(',')
tag = argv[1]
def opt(k, d):
    return argv[argv.index(k) + 1] if k in argv else d
spp, W = int(opt('--spp', 128)), int(opt('--w', 1280))
light = opt('--light', 'dusk')
LOD = opt('--lod', '0')
outname = opt('--out', assets[0])
camcfg = json.load(open(os.path.join(ROOT, 'scripts', 'qa_cams.json'), encoding='utf8'))[outname]
cams = opt('--cams', ','.join(camcfg['cams'].keys())).split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'
p = bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type = 'OPTIX'
p.get_devices()
for d in p.devices:
    d.use = d.type == 'OPTIX'
s.cycles.device = 'GPU'
s.cycles.samples = spp
s.cycles.use_denoising = True
s.cycles.denoiser = 'OPTIX'
s.cycles.max_bounces = 6
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'None'
s.render.resolution_x, s.render.resolution_y = W, int(W * 9 / 16)
s.render.image_settings.file_format = 'JPEG'
s.render.image_settings.quality = 88
place = camcfg.get('place', {})
for a in assets:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'export', 'props', a, a + '.glb'))
    new = set(bpy.data.objects) - before
    for o in new:
        if '_COL' in o.name or ('_LOD' in o.name and '_LOD' + LOD not in o.name):
            bpy.data.objects.remove(o)
    pl = place.get(a)
    if pl:
        for o in [o for o in new if o.name in bpy.data.objects]:
            if o.parent is None:
                o.location = pl[:3]
                if len(pl) > 3:
                    o.rotation_euler[2] = math.radians(pl[3])
# ground + backing wall
def pbrplane(name, tid, verts, sc):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for i, l in enumerate(me.loops):
        v = verts[l.vertex_index]
        uv.data[i].uv = ((v[0] + v[1]) * sc, v[2] * sc) if abs(verts[0][2] - verts[2][2]) > 1e-3 else (v[0] * sc, v[1] * sc)
    ob = bpy.data.objects.new(name, me)
    s.collection.objects.link(ob)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    P = nt.nodes['Principled BSDF']
    base = os.path.join(ROOT, 'assets', 'polyhaven', tid)
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(base, 'diff.jpg'))
    nt.links.new(t.outputs[0], P.inputs['Base Color'])
    r = nt.nodes.new('ShaderNodeTexImage')
    r.image = bpy.data.images.load(os.path.join(base, 'rough.jpg'))
    r.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(r.outputs[0], P.inputs['Roughness'])
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = bpy.data.images.load(os.path.join(base, 'nor.jpg'))
    n.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(n.outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], P.inputs['Normal'])
    me.materials.append(m)
    return ob
pbrplane('ground', 'asphalt_02', [(-15, -15, 0), (15, -15, 0), (15, 15, 0), (-15, 15, 0)], .35)
wy = camcfg.get('wall_y')
PL = next(t for t in ('white_plaster_rough_01', 'painted_plaster_wall', 'worn_plaster_wall') if os.path.exists(os.path.join(ROOT, 'assets', 'polyhaven', t, 'nor.jpg')))
if wy is not None:
    wall_h = camcfg.get('wall_h', 6)
    zm = camcfg.get('wall_zmin')
    if zm is None:
        pbrplane('wall', PL, [(-8, wy, 0), (8, wy, 0), (8, wy, wall_h), (-8, wy, wall_h)], .4)
    else:
        # wall with an opening for a storefront module
        pbrplane('wall_t', PL, [(-1.8, wy, zm), (1.8, wy, zm), (1.8, wy, wall_h), (-1.8, wy, wall_h)], .4)
        pbrplane('wall_l', PL, [(-8, wy, 0), (-1.8, wy, 0), (-1.8, wy, wall_h), (-8, wy, wall_h)], .4)
        pbrplane('wall_r', PL, [(1.8, wy, 0), (8, wy, 0), (8, wy, wall_h), (1.8, wy, wall_h)], .4)
# light
w = bpy.data.worlds.new('w')
w.use_nodes = True
nt = w.node_tree
bg = nt.nodes['Background']
env = nt.nodes.new('ShaderNodeTexEnvironment')
hd = 'industrial_sunset_02_puresky' if light == 'dusk' else 'german_town_street'
env.image = bpy.data.images.load(os.path.join(ROOT, 'assets', 'polyhaven', 'hdri', hd + '.hdr'))
nt.links.new(env.outputs[0], bg.inputs['Color'])
bg.inputs['Strength'].default_value = .8 if light == 'dusk' else .9
s.world = w
sun = bpy.data.lights.new('sun', 'SUN')
sun.energy = 3.2 if light == 'dusk' else 2.2
sun.color = (1, .72, .46) if light == 'dusk' else (1, .96, .9)
sun.angle = math.radians(2.5)
so = bpy.data.objects.new('sun', sun)
s.collection.objects.link(so)
so.rotation_euler = (math.radians(72), 0, math.radians(-52)) if light == 'dusk' else (math.radians(45), 0, math.radians(-30))
out = os.path.join(ROOT, 'output', 'previews', tag)
os.makedirs(out, exist_ok=True)
for c in cams:
    cfg = camcfg['cams'][c]
    cam = bpy.data.cameras.new(c)
    cam.lens = cfg.get('lens', 35)
    ob = bpy.data.objects.new(c, cam)
    s.collection.objects.link(ob)
    ob.location = cfg['pos']
    ob.rotation_euler = (Vector(cfg['at']) - Vector(cfg['pos'])).to_track_quat('-Z', 'Y').to_euler()
    s.camera = ob
    s.render.filepath = os.path.join(out, '%s_%s.jpg' % (outname, c))
    bpy.ops.render.render(write_still=True)
    print('[qa] wrote', s.render.filepath, flush=True)
sys.stdout.flush()
os._exit(0)
