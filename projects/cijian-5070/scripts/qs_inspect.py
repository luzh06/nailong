import bpy, os, json, collections
mats = {}
for m in bpy.data.materials:
    if not m.use_nodes:
        mats[m.name] = 'nonodes'; continue
    t = m.node_tree
    c = collections.Counter(n.bl_idname for n in t.nodes)
    o = [n for n in t.nodes if n.bl_idname == 'ShaderNodeOutputMaterial']
    d = None
    for x in o:
        s = x.inputs['Surface'].links
        d = dict(surf=s[0].from_node.bl_idname if s else None, disp=bool(x.inputs['Displacement'].links), vol=bool(x.inputs['Volume'].links))
    mats[m.name] = dict(bsdf=c.get('ShaderNodeBsdfPrincipled', 0), mix=c.get('ShaderNodeMixShader', 0), emis=c.get('ShaderNodeEmission', 0), glass=c.get('ShaderNodeBsdfGlass', 0), transp=c.get('ShaderNodeBsdfTransparent', 0), groups=c.get('ShaderNodeGroup', 0), out=d, dm=getattr(m, 'displacement_method', None) or m.cycles.displacement_method, nmats=m.users)
rows = {}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.hide_render:
        continue
    me = o.data
    a = sum(p.area for p in me.polygons) * (o.matrix_world.to_scale()[0] ** 2)
    k = o.material_slots[0].material.name if o.material_slots and o.material_slots[0].material else '-'
    r = rows.setdefault(k, dict(n=0, area=0, multi=0, tris=0, mn=[1e9] * 3, mx=[-1e9] * 3))
    r['n'] += 1; r['area'] += a; r['multi'] += len(o.material_slots) > 1; r['tris'] += sum(len(p.vertices) - 2 for p in me.polygons)
    for c in o.bound_box:
        w = o.matrix_world @ __import__('mathutils').Vector(c)
        for i in range(3):
            r['mn'][i] = min(r['mn'][i], w[i]); r['mx'][i] = max(r['mx'][i], w[i])
hid = collections.Counter(o.name.rstrip('0123456789') for o in bpy.data.objects if o.type == 'MESH' and o.hide_render)
json.dump(dict(mats=mats, rows=rows, hidden=hid, world=bpy.context.scene.world.name if bpy.context.scene.world else None), open(r'D:\Cijian\output\inspect.json', 'w'), ensure_ascii=False, indent=0)
print('INSPECT', len(rows))
os._exit(0)
