# 《此间》性能测试导出：把 qs_r8 导成 GLB。
# blender -b D:\Cijian\blend\qs_r8.blend -P qs_export.py -- --mode raw|opt
# Cycles 节点材质导不出去，这里换成同名空材质，Three.js 端按名字挂贴图。
import bpy, sys, os, time, json
argv = sys.argv[sys.argv.index('--') + 1:]
MODE = argv[argv.index('--mode') + 1]
OUT = r'D:\Cijian\web\data'
os.makedirs(OUT, exist_ok=True)
PLANT = ('nettle_plant', 'dandelion_01', 'grass_bermuda_01', 'moss_01', 'shrub_01', 'fern_02')
t0 = time.time()

def is_plant(o):
    return o.name.startswith(PLANT)

def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)

for o in list(bpy.data.objects):
    if o.type == 'LIGHT' or o.type == 'CAMERA':
        bpy.data.objects.remove(o)
    elif o.type == 'EMPTY':
        pass

for m in bpy.data.materials:
    if any(m.name.lower().startswith(p[:5]) for p in PLANT) or not m.use_nodes:
        continue
    names = {n.bl_idname for n in m.node_tree.nodes}
    if 'ShaderNodeTexImage' in names and 'ShaderNodeBsdfPrincipled' in names and len(m.node_tree.nodes) < 12:
        continue
    m.node_tree.nodes.clear()
    p = m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    o = m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(p.outputs[0], o.inputs[0])

for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.uv_layers.get('UV0') and is_plant(o) is False:
        o.data.uv_layers.active = o.data.uv_layers['UV0']

if MODE == 'opt':
    # 植物：共享网格减到每株 1500 面以内
    seen = {}
    for o in [x for x in bpy.data.objects if x.type == 'MESH' and x.hide_render]:
        n = tris(o)
        if n <= 1500:
            continue
        o.hide_viewport = False
        d = o.modifiers.new('dec', 'DECIMATE')
        d.ratio = 1500 / n
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        new = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        seen[o.data.name] = new
        o.modifiers.remove(d)
        o.hide_viewport = True
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.data.name in seen:
            o.data = seen[o.data.name]
    # 路面：置换密网格减到约 2%
    r = bpy.data.objects['road']
    d = r.modifiers.new('dec', 'DECIMATE')
    d.ratio = .02
    bpy.context.view_layer.update()
    r.data = bpy.data.meshes.new_from_object(r.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    r.modifiers.clear()
    # 静态件按材质合并
    groups = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render or is_plant(o) or not o.data.materials:
            continue
        o.modifiers.clear()
        o.data = o.data.copy() if o.data.users > 1 else o.data
        groups.setdefault(o.data.materials[0].name, []).append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for k, obs in groups.items():
        if len(obs) < 2:
            continue
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.object.join()
        bpy.ops.object.select_all(action='DESELECT')
    print('GROUPS', len(groups))

vis = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
print('EXPORT', MODE, 'objects', len(vis), 'tris', sum(tris(o) for o in vis))
path = os.path.join(OUT, f'{MODE}.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_renderable=True, export_apply=True,
                          export_texcoords=True, export_normals=True, export_materials='EXPORT',
                          export_gpu_instances=(MODE == 'opt'), export_animations=False, export_yup=True,
                          export_cameras=False, export_lights=False)
print('DONE', MODE, round(os.path.getsize(path) / 1e6, 1), 'MB', round(time.time() - t0, 1), 's')

sys.stdout.flush()
os._exit(0)
