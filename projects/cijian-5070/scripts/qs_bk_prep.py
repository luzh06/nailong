# 《此间》烘焙准备：把 qs_h1 按材质合并，切路面，做低模和光照 UV，存成 qs_bk.blend。
# blender -b qs_h1.blend -P qs_bk_prep.py
import bpy, bmesh, os, sys, json, math, time
import numpy as np
from mathutils import Vector

ROOT = r'D:\Cijian'
PLANT = ('nettle_plant', 'dandelion_01', 'grass_bermuda_01', 'moss_01', 'shrub_01', 'fern_02')
PLANT_KEEP = dict(shrub_01=.15, nettle_plant=.35, dandelion_01=.25, fern_02=1, grass_bermuda_01=1, moss_01=1)
ROAD_CUT = -20.0
YMIN, YMAX = -34.0, 32.0   # 小样范围：台阶顶到台阶下约 30 米，范围外只留作遮挡
FULL = ('far', 'ground')
MM = 3.0            # 目标贴图精度：毫米每像素
t0 = time.time()
scene = bpy.context.scene
vl = bpy.context.view_layer

def area(ob):
    s = ob.matrix_world.to_scale()[0]
    return sum(p.area for p in ob.data.polygons) * s * s

def sel(obs, act=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    vl.objects.active = act or obs[0]

bpy.data.objects['fog_box'].hide_render = True
bpy.data.objects['fog_box'].hide_viewport = True

# ---------- 按材质合并 ----------
groups = {}
plants = []
for o in list(bpy.data.objects):
    if o.type != 'MESH' or o.hide_render:
        continue
    if o.name.startswith(PLANT):
        plants.append(o)
        continue
    if o.name == 'road':
        continue
    k = o.material_slots[0].material.name
    if k == 'apron' and area(o) > 2000:
        k = 'ground'
    groups.setdefault(k, []).append(o)

for k, obs in groups.items():
    for o in obs:
        if o.data.users > 1:
            o.data = o.data.copy()
    sel(obs)
    bpy.ops.object.convert(target='MESH')
    if len(obs) > 1:
        bpy.ops.object.join()
    ob = vl.objects.active
    ob.name = 'bk_' + k
    ob.data.name = 'bk_' + k
    ob.data.uv_layers.get('UV0') or ob.data.uv_layers.new(name='UV0')
print('JOINED', len(groups), round(time.time() - t0, 1), flush=True)

# ---------- 裁到小样范围：范围外的面拆成遮挡体，日落的长影还要靠它们 ----------
for k in list(groups):
    if k in FULL:
        continue
    ob = bpy.data.objects['bk_' + k]
    me = ob.data
    ce = np.empty(len(me.polygons) * 3, 'f')
    me.polygons.foreach_get('center', ce)
    y = ce.reshape(-1, 3)[:, 1]
    out = (y < YMIN) | (y > YMAX)
    if not out.any():
        continue
    oc = ob.copy()
    oc.data = me.copy()
    oc.name = 'occ_' + k
    scene.collection.objects.link(oc)
    for src, drop in ((me, out), (oc.data, ~out)):
        bm = bmesh.new()
        bm.from_mesh(src)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(drop)[0]], context='FACES')
        bm.to_mesh(src)
        bm.free()
    if len(me.polygons) == 0:
        bpy.data.objects.remove(ob)
        del groups[k]
    print('CROP', k, len(me.polygons), int(out.sum()), flush=True)

# ---------- 路面：高模留作烘焙来源，低模进游戏 ----------
road = bpy.data.objects['road']
def road_lo(name, keep):
    me = road.data.copy()
    me.name = name
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.matrix_world = road.matrix_world
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(f.calc_center_median().y)], context='FACES')
    bm.to_mesh(me)
    bm.free()
    d = ob.modifiers.new('dec', 'DECIMATE')
    d.ratio = .05
    sel([ob])
    bpy.ops.object.modifier_apply(modifier='dec')
    for u in list(me.uv_layers):
        pass
    # 路面用俯视投影，没有接缝
    co = np.empty(len(me.vertices) * 3, 'f')
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    mn, mx = co.min(0), co.max(0)
    print('ROADLO', name, len(me.polygons), mn, mx, flush=True)
    uv = me.uv_layers.new(name='LM')
    idx = np.empty(len(me.loops), 'i')
    me.loops.foreach_get('vertex_index', idx)
    pad = .002
    u = (co[idx, 0] - mn[0]) / (mx[0] - mn[0]) * (1 - 2 * pad) + pad
    v = (co[idx, 1] - mn[1]) / (mx[1] - mn[1]) * (1 - 2 * pad) + pad
    uv.data.foreach_set('uv', np.stack([u, v], 1).ravel())
    # 射线不可见：高模才是真实表面
    ob.visible_camera = ob.visible_shadow = ob.visible_diffuse = ob.visible_glossy = ob.visible_transmission = ob.visible_volume_scatter = False
    return ob

road_lo('bk_road_a', lambda y: y >= ROAD_CUT)
road_lo('bk_road_b', lambda y: YMIN <= y < ROAD_CUT)

# ---------- 光照 UV ----------
info = {}
for k in list(groups):
    ob = bpy.data.objects['bk_' + k]
    me = ob.data
    uv = me.uv_layers.new(name='LM')
    me.uv_layers.active = uv
    sel([ob])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.0025, area_weight=1.0, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    # 渲染仍用原 UV，程序材质靠它
    if 'UV0' in me.uv_layers:
        me.uv_layers['UV0'].active_render = True
    print('UV', k, len(me.polygons), round(time.time() - t0, 1), flush=True)

# 贴图尺寸：按面积定，封顶 4096
def size(a, mm=MM, lo=256, hi=4096):
    s = math.sqrt(a) / (mm / 1000)
    return int(min(hi, max(lo, 2 ** round(math.log2(max(s, 1))))))

SIMPLE = dict(ac=1024, wood=1024, pipe=1024, wire=512, cable=256, porcelain=256, awn_a=256, awn_b=512, awn_c=256, glass=512)
HERO = ('stone', 'cover', 'apron', 'brick', 'block_wall', 'pole', 'manhole')
for ob in bpy.data.objects:
    if not ob.name.startswith('bk_'):
        continue
    a = area(ob)
    n = ob.name[3:]
    t = size(a)
    if n == 'far':
        t = 4096
    if n == 'ground':
        t = 2048
    lm = max(128, t // 2)
    if n in ('stone',):
        lm = t
    if n in SIMPLE:
        t, lm = 512, min(lm, SIMPLE[n])
    if n in ('far', 'ground'):
        lm = 1024
    info[n] = dict(area=round(a, 1), tris=sum(len(p.vertices) - 2 for p in ob.data.polygons), tex=t, lm=lm, nrm=t if n in HERO or n.startswith('road') else max(256, t // 2))

# ---------- 植物：减面后按种合并，进游戏时顶点光照 ----------
by = {}
for o in plants:
    k = next(p for p in PLANT if o.name.startswith(p))
    by.setdefault(k, []).append(o)
lo = {}
for k, obs in by.items():
    r = PLANT_KEEP[k]
    dup = []
    for o in obs:
        me = lo.get(o.data.name)
        if me is None:
            src = bpy.data.objects.new('tmp', o.data)
            scene.collection.objects.link(src)
            if r < 1:
                d = src.modifiers.new('dec', 'DECIMATE')
                d.ratio = r
                vl.update()
                me = bpy.data.meshes.new_from_object(src.evaluated_get(bpy.context.evaluated_depsgraph_get()))
            else:
                me = o.data.copy()
            bpy.data.objects.remove(src)
            lo[o.data.name] = me
        n = bpy.data.objects.new('bp', me.copy())
        scene.collection.objects.link(n)
        n.matrix_world = o.matrix_world
        dup.append(n)
    sel(dup)
    bpy.ops.object.join()
    ob = vl.objects.active
    ob.name = 'bkp_' + k
    ob.data.name = 'bkp_' + k
    ob.visible_camera = ob.visible_shadow = ob.visible_diffuse = ob.visible_glossy = ob.visible_transmission = ob.visible_volume_scatter = False
    info['p_' + k] = dict(tris=sum(len(p.vertices) - 2 for p in ob.data.polygons), mats=[s.material.name for s in ob.material_slots])
    print('PLANTLO', k, info['p_' + k], flush=True)

json.dump(info, open(os.path.join(ROOT, 'bake', 'groups.json'), 'w'), indent=0)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'blend', 'qs_bk.blend'))
print('PREPDONE', round(time.time() - t0, 1), 'objs', len(bpy.data.objects), flush=True)
os._exit(0)
