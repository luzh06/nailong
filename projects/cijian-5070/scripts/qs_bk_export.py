# 《此间》烘焙版导出：blender -b qs_bk.blend -P qs_bk_export.py -- --dir t2 --lights sunset,morning
import bpy, os, sys, json, glob
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
def arg(k, d):
    return argv[argv.index('--' + k) + 1] if '--' + k in argv else d
ROOT = r'D:\Cijian'
D = arg('dir', 't2')
LIGHTS = arg('lights', 'sunset').split(',')
DROP = {'bk_manhole'}
scene = bpy.context.scene
keep = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(('bk_', 'bkp_')) and o.name not in DROP]
for o in list(bpy.data.objects):
    if o not in keep:
        bpy.data.objects.remove(o)
tris = 0
for o in keep:
    me = o.data
    tris += sum(len(p.vertices) - 2 for p in me.polygons)
    plant = o.name.startswith('bkp_')
    o.hide_render = False
    if not plant:
        for u in list(me.uv_layers):
            if u.name != 'LM':
                me.uv_layers.remove(u)
    for a in list(me.color_attributes):
        me.color_attributes.remove(a)
    if plant:
        for k in LIGHTS:
            f = os.path.join(ROOT, 'bake', D, f'{o.name}_{k}.npy')
            if not os.path.exists(f):
                continue
            c = np.load(f)
            a = me.attributes.new('_LM_' + k.upper(), 'FLOAT_VECTOR', 'POINT')
            a.data.foreach_set('vector', c.ravel())
    # 程序节点不用导，同名空材质，网页端按名字挂贴图
    for s in me.materials:
        if s:
            s.node_tree.nodes.clear()
            p = s.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
            q = s.node_tree.nodes.new('ShaderNodeOutputMaterial')
            s.node_tree.links.new(p.outputs[0], q.inputs[0])
print('EXPORT objs', len(keep), 'tris', tris, flush=True)
path = os.path.join(ROOT, 'web', 'data', 'bk.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT',
                          export_animations=False, export_yup=True, export_cameras=False, export_lights=False, export_attributes=True, export_vertex_color='NONE')
print('GLB', round(os.path.getsize(path) / 1e6, 1), 'MB', flush=True)
names = [o.name for o in keep]
json.dump(dict(dir=D, lights=LIGHTS, groups={n[3:]: sorted(os.path.basename(f)[len(n) - 2:] for f in glob.glob(os.path.join(ROOT, 'bake', D, n[3:] + '_*'))) for n in names if not n.startswith('bkp_')}, plants=[n[4:] for n in names if n.startswith('bkp_')]), open(os.path.join(ROOT, 'web', 'data', 'bk.json'), 'w'))
print('EXPORTDONE', flush=True)
os._exit(0)
