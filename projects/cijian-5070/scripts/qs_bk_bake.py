# 《此间》烘焙：blender -b qs_bk.blend -P qs_bk_bake.py -- --groups stone,road_a --passes albedo,orm,normal,sunset --spp 256
# 产物在 D:\Cijian\bake：<组>_albedo.png  _orm.png  _normal.png  _<光>.exr  _<光>_vis.exr  _emit.png
import bpy, os, sys, json, math, time
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
def arg(k, d):
    return argv[argv.index('--' + k) + 1] if '--' + k in argv else d

ROOT = r'D:\Cijian'
OUT = os.path.join(ROOT, 'bake', arg('out', ''))
os.makedirs(OUT, exist_ok=True)
HDR = os.path.join(ROOT, 'assets', 'hdri')
INFO = json.load(open(os.path.join(ROOT, 'bake', 'groups.json')))
GROUPS = arg('groups', 'stone').split(',')
PASSES = arg('passes', 'albedo,orm,normal,sunset').split(',')
SPP = int(arg('spp', 256))
SCALE = float(arg('scale', 1))
scene = bpy.context.scene
vl = bpy.context.view_layer

LIGHT = dict(morning=dict(hdr='kloofendal_48d_partly_cloudy_puresky_4k.hdr', az=100, el=38, sun=4.0, col=(1, .92, .8), angle=1.0, strength=1.9, cap=8, glow=0),
             sunset=dict(hdr='qwantani_sunset_puresky_4k.hdr', az=268, el=6.1, sun=7.5, col=(1, .58, .3), angle=1.6, strength=.85, cap=9, glow=.38))

def hdri_sun(path):
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, 'f')
    img.pixels.foreach_get(px)
    lum = px.reshape(h, w, 4)[..., :3].sum(2)
    lum[:h // 2] = 0
    i = int(np.argmax(lum))
    r, c = i // w, i % w
    return (.5 - (c + .5) / w) * 2 * math.pi

def set_light(k, sun_on=True, sky_on=True):
    L = LIGHT[k]
    path = os.path.join(HDR, L['hdr'])
    phi = hdri_sun(path)
    a = math.radians(L['az'])
    target = math.atan2(math.sin(a), -math.cos(a))
    w = bpy.data.worlds.new(k)
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, phi - target)
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(path, check_existing=True)
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = L['strength'] if sky_on else 0
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs[0], env.inputs['Vector'])
    cap = nt.nodes.new('ShaderNodeVectorMath')
    cap.operation = 'MINIMUM'
    cap.inputs[1].default_value = (L['cap'], L['cap'], L['cap'])
    nt.links.new(env.outputs[0], cap.inputs[0])
    nt.links.new(cap.outputs[0], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w
    sd = bpy.data.objects.get('sun') or bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    if sd.name not in scene.collection.objects:
        scene.collection.objects.link(sd)
    sd.data.energy = L['sun'] if sun_on else 0
    sd.data.color = L['col'] if sun_on else (1, 1, 1)
    sd.data.angle = math.radians(L['angle'])
    e = math.radians(L['el'])
    d = Vector((-math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
    sd.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    gw = bpy.data.materials['glass_warm'].node_tree
    for n in gw.nodes:
        if n.bl_idname == 'ShaderNodeValue':
            n.outputs[0].default_value = L['glow'] if sky_on else 0

prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'OPTIX'
scene.render.engine = 'CYCLES'
c = scene.cycles
c.device = 'GPU'
c.use_adaptive_sampling = False
c.use_denoising = False
c.max_bounces = 6
c.diffuse_bounces = 4
c.glossy_bounces = 2
c.caustics_reflective = False
c.caustics_refractive = False
c.sample_clamp_indirect = 8
scene.render.bake.margin = 8
scene.render.bake.margin_type = 'EXTEND'
scene.render.use_persistent_data = True

def dims(v, k=1.0):
    w, h = v if isinstance(v, list) else (v, v)
    return max(16, int(w * k)), max(16, int(h * k))

def new_image(name, s, float_=False, data=False):
    im = bpy.data.images.new(name, s[0], s[1], alpha=False, float_buffer=float_)
    if data:
        im.colorspace_settings.name = 'Non-Color'
    return im

def src_of(p, name):
    return p.inputs[name]

class Swap:
    """把材质临时改成纯发光，直接取 Base Color 或 Metallic，保留程序节点。"""
    def __init__(s, mats, field):
        s.undo = []
        for m in mats:
            nt = m.node_tree
            p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
            out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial' and n.is_active_output)
            old = out.inputs['Surface'].links[0].from_socket
            e = nt.nodes.new('ShaderNodeEmission')
            inp = p.inputs[field]
            if inp.links:
                nt.links.new(inp.links[0].from_socket, e.inputs['Color'])
            else:
                v = inp.default_value
                e.inputs['Color'].default_value = tuple(v) if hasattr(v, '__len__') else (v, v, v, 1)
            nt.links.new(e.outputs[0], out.inputs['Surface'])
            s.undo.append((nt, old, out, e))

    def done(s):
        for nt, old, out, e in s.undo:
            nt.links.new(old, out.inputs['Surface'])
            nt.nodes.remove(e)

def holder(mats, img):
    """Cycles 烘到各材质当前激活的图片节点。"""
    add = []
    for m in mats:
        nt = m.node_tree
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        n.select = True
        nt.nodes.active = n
        add.append((nt, n))
    return add

def bake(ob, srcs, typ, img, spp, **kw):
    mats = [s.material for s in ob.material_slots]
    add = holder(mats, img) if img else []
    bpy.ops.object.select_all(action='DESELECT')
    for x in srcs:
        x.select_set(True)
    ob.select_set(True)
    vl.objects.active = ob
    c.samples = spp
    t = time.time()
    h2l = len(srcs) > 0
    if h2l:
        kw.update(use_selected_to_active=True, cage_extrusion=.04, max_ray_distance=.1)
    if img:
        kw.update(uv_layer='LM', target='IMAGE_TEXTURES', save_mode='INTERNAL')
    else:
        kw.update(target='VERTEX_COLORS')
    bpy.ops.object.bake(type=typ, margin=scene.render.bake.margin, **kw)
    for nt, n in add:
        nt.nodes.remove(n)
    print('BAKED', ob.name, typ, tuple(img.size) if img else 'vertex', spp, round(time.time() - t, 1), 's', flush=True)

def have(name):
    return os.path.exists(os.path.join(OUT, name))

def save(img, path):
    if path.endswith('.exr'):
        s = scene.render.image_settings
        s.file_format = 'OPEN_EXR'
        s.color_mode = 'RGB'
        s.color_depth = '16'
        s.exr_codec = 'ZIP'
        img.save_render(path, scene=scene)
    else:
        s = bpy.context.scene.render.image_settings
        s.file_format = 'PNG'
        s.color_mode = 'RGB'
        s.color_depth = '8'
        img.filepath_raw = path
        img.file_format = 'PNG'
        img.save()

def ray_vis(ob, on):
    ob.visible_camera = ob.visible_shadow = ob.visible_diffuse = ob.visible_glossy = ob.visible_transmission = ob.visible_volume_scatter = on

for g in GROUPS:
    if g == '' or g == 'none':
        continue
    I = INFO[g]
    ob = bpy.data.objects['bk_' + g]
    # 井盖画进路面，低模路面把井盖洞盖住了
    srcs = [bpy.data.objects['road'], bpy.data.objects['bk_manhole']] if g.startswith('road') else []
    ts = dims(I['tex'], SCALE)
    ns = dims(I.get('nrm', I['tex']), SCALE)
    ls = dims(I['lm'], SCALE)
    mats = [x.material_slots[0].material for x in (srcs or [ob])]
    t0 = time.time()
    if 'albedo' in PASSES and not have(g + '_albedo.png'):
        im = new_image(g + '_albedo', ts)
        sw = Swap(mats, 'Base Color')
        bake(ob, srcs, 'EMIT', im, 8)
        sw.done()
        save(im, os.path.join(OUT, g + '_albedo.png'))
    if 'orm' in PASSES and not have(g + '_orm.png'):
        r = new_image(g + '_r', ns, data=True)
        bake(ob, srcs, 'ROUGHNESS', r, 8)
        m = new_image(g + '_m', ns, data=True)
        sw = Swap(mats, 'Metallic')
        bake(ob, srcs, 'EMIT', m, 8)
        sw.done()
        pr = np.empty(ns[0] * ns[1] * 4, 'f')
        pm = np.empty(ns[0] * ns[1] * 4, 'f')
        r.pixels.foreach_get(pr)
        m.pixels.foreach_get(pm)
        o = new_image(g + '_orm', ns, data=True)
        pr[1::4] = pr[0::4]
        pr[2::4] = pm[0::4]
        pr[0::4] = 1
        o.pixels.foreach_set(pr)
        save(o, os.path.join(OUT, g + '_orm.png'))
    if 'normal' in PASSES and not have(g + '_normal.png'):
        im = new_image(g + '_normal', ns, data=True)
        bake(ob, srcs, 'NORMAL', im, 8, normal_space='TANGENT')
        save(im, os.path.join(OUT, g + '_normal.png'))
    if 'emit' in PASSES and g == 'glass_warm' and not have(g + '_emit.png'):
        im = new_image(g + '_emit', ts)
        set_light('sunset')
        bake(ob, srcs, 'EMIT', im, 8)
        save(im, os.path.join(OUT, g + '_emit.png'))
    for k in ('sunset', 'morning'):
        if k in PASSES and not have(f'{g}_{k}.exr'):
            set_light(k)
            im = new_image(f'{g}_{k}', ls, True, True)
            bake(ob, srcs, 'DIFFUSE', im, SPP, pass_filter={'DIRECT', 'INDIRECT'})
            save(im, os.path.join(OUT, f'{g}_{k}.exr'))
        if k + '_vis' in PASSES and not have(f'{g}_{k}_vis.exr'):
            # 太阳可见度：只留太阳灯，取直射，网页端用来决定太阳高光
            set_light(k, True, False)
            im = new_image(f'{g}_{k}_vis', dims(I['lm'], SCALE * .5), True, True)
            bake(ob, srcs, 'DIFFUSE', im, 32, pass_filter={'DIRECT'})
            save(im, os.path.join(OUT, f'{g}_{k}_vis.exr'))
    print('GROUP', g, round(time.time() - t0, 1), flush=True)
# 植物：低模参与自身遮挡，顶点存光照，存 npy 给导出脚本
if arg('plants', ''):
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.hide_render and o.name.startswith(('nettle_plant', 'dandelion_01', 'grass_bermuda_01', 'moss_01', 'shrub_01', 'fern_02')):
            ray_vis(o, False)
    los = [o for o in bpy.data.objects if o.name.startswith('bkp_')]
    for o in los:
        ray_vis(o, True)
    for k in arg('plants', '').split(','):
        set_light(k)
        for ob in los:
            me = ob.data
            a = me.color_attributes.new('_LM', 'FLOAT_COLOR', 'POINT')
            me.color_attributes.active_color = a
            me.attributes.active_color = a
            bake(ob, [], 'DIFFUSE', None, max(64, SPP // 2), pass_filter={'DIRECT', 'INDIRECT'})
            a = me.color_attributes['_LM']
            px = np.empty(len(me.vertices) * 4, 'f')
            a.data.foreach_get('color', px)
            np.save(os.path.join(OUT, f'{ob.name}_{k}.npy'), px.reshape(-1, 4)[:, :3].astype('f'))
            print('PLANT', ob.name, k, px[::4].mean(), px[::4].max(), flush=True)
            me.color_attributes.remove(a)
print('ALLDONE', flush=True)
sys.stdout.flush()
os._exit(0)
