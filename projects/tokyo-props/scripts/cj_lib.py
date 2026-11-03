# cj_lib.py - shared Blender helpers for 《此间》 props (geometry, weathered PBR, bake, LOD, GLB export)
import bpy, bmesh, math, os, json, random, sys, time
from mathutils import Vector, Matrix, noise

ROOT = r'D:\Cijian'
PH = os.path.join(ROOT, 'assets', 'polyhaven')
DECAL = os.path.join(ROOT, 'assets', 'decals')
FONT = os.path.join(ROOT, 'assets', 'fonts')
EXPORT = os.path.join(ROOT, 'export', 'props')


def log(*a):
    print('[cj]', *a, flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    p = bpy.context.preferences.addons['cycles'].preferences
    p.compute_device_type = 'OPTIX'
    p.get_devices()
    for d in p.devices:
        d.use = d.type == 'OPTIX'
    s.cycles.device = 'GPU'
    return s


# ---------------------------------------------------------------- geometry
def _obj(me, name, mat=None):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


def apply_all(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


def smooth(ob, angle=35):
    me = ob.data
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(angle)
    for e in bm.edges:
        e.smooth = (not e.is_manifold) or e.calc_face_angle(0) <= lim
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob


def box_uv(ob, uvname='tex', rot=None, offset=None, keep=False):
    """World-metre box projection per face. Random offset per part so tiling never lines up."""
    me = ob.data
    if keep and uvname in me.uv_layers:
        return ob
    uv = me.uv_layers.get(uvname) or me.uv_layers.new(name=uvname)
    off = offset if offset is not None else (random.random() * 7, random.random() * 7)
    rot = rot if rot is not None else 0.0
    c, s = math.cos(rot), math.sin(rot)
    mw = ob.matrix_world
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                a, b = v.y, v.z
            elif ax == 1:
                a, b = v.x, v.z
            else:
                a, b = v.x, v.y
            uv.data[li].uv = (a * c - b * s + off[0], a * s + b * c + off[1])
    return ob


def bevel(ob, width=0.004, segs=2, angle=30):
    m = ob.modifiers.new('bv', 'BEVEL')
    m.width = width
    m.segments = segs
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.miter_outer = 'MITER_ARC'
    m.profile = 0.6
    apply_all(ob)
    return ob


def box(name, size, loc=(0, 0, 0), mat=None, bv=0.003, segs=2, rot=(0, 0, 0), uvrot=None, subdiv=0):
    """size=(x,y,z) metres, loc = centre."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = _obj(me, name, mat)
    if bv > 0:
        bevel(ob, bv, segs)
    ob.rotation_euler = rot
    ob.location = loc
    bpy.context.view_layer.update()
    smooth(ob)
    box_uv(ob, rot=uvrot)
    return ob


def cyl(name, r, h, loc=(0, 0, 0), mat=None, verts=24, bv=0.0015, axis='Z', r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=r, radius2=r2 if r2 is not None else r, depth=h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = _obj(me, name, mat)
    if bv > 0:
        bevel(ob, bv, 2)
    if axis == 'X':
        ob.rotation_euler = (0, math.pi / 2, 0)
    elif axis == 'Y':
        ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = loc
    bpy.context.view_layer.update()
    smooth(ob, 40)
    box_uv(ob)
    return ob


def fillet(pts, r):
    """Round the corners of a polyline with arcs of radius r (r may be list per interior point)."""
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        rr = r[i - 1] if isinstance(r, (list, tuple)) else r
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        u, v = (a - b).normalized(), (c - b).normalized()
        ang = u.angle(v) if (u - v).length > 1e-6 else 0
        if rr <= 0 or ang > 3.13:
            out.append(b)
            continue
        d = min(rr / math.tan(ang / 2), (a - b).length * .49, (c - b).length * .49)
        p0, p1 = b + u * d, b + v * d
        n = 8
        for k in range(n + 1):
            t = k / n
            out.append(((1 - t) ** 2) * p0 + 2 * (1 - t) * t * b + t * t * p1)
    out.append(pts[-1])
    return out


def tube(name, pts, r, mat=None, verts=12, cap=True, r_fn=None):
    """Sweep circle along polyline. r_fn(t)->radius multiplier; returns mesh with own UV (u around, v metres along)."""
    pts = [Vector(p) for p in pts]
    # parallel transport frames
    tang = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tang.append((b - a).normalized())
    up = Vector((0, 0, 1)) if abs(tang[0].z) < .9 else Vector((1, 0, 0))
    nrm = tang[0].cross(up).normalized()
    rings = []
    L = [0.0]
    for i in range(1, len(pts)):
        L.append(L[-1] + (pts[i] - pts[i - 1]).length)
    bm = bmesh.new()
    for i, p in enumerate(pts):
        if i:
            q = tang[i - 1].rotation_difference(tang[i])
            nrm = (q @ nrm).normalized()
        b2 = tang[i].cross(nrm)
        rr = r * (r_fn(L[i] / max(L[-1], 1e-6)) if r_fn else 1)
        ring = []
        for k in range(verts):
            a = 2 * math.pi * k / verts
            ring.append(bm.verts.new(p + (nrm * math.cos(a) + b2 * math.sin(a)) * rr))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    uvl = bm.loops.layers.uv.new('tex')
    for i in range(len(rings) - 1):
        for k in range(verts):
            k2 = (k + 1) % verts
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            f.smooth = True
            circ = 2 * math.pi * r
            uu = [(k / verts) * circ, ((k + 1) / verts) * circ, ((k + 1) / verts) * circ, (k / verts) * circ]
            vv = [L[i], L[i], L[i + 1], L[i + 1]]
            for lo, u_, v_ in zip(f.loops, uu, vv):
                lo[uvl].uv = (u_, v_)
    if cap:
        for ring, rev in ((rings[0], False), (rings[-1], True)):
            f = bm.faces.new(list(reversed(ring)) if rev is False else ring)
            f.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = _obj(me, name, mat)
    return ob


def lathe(name, prof, mat=None, verts=32, loc=(0, 0, 0), axis='Z', uv_h=None):
    """prof = [(radius,height)...] revolve about Z. UV: u 0..1 around, v 0..1 along height (labels) ."""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / verts), r * math.sin(2 * math.pi * k / verts), z)) for k in range(verts)])
    uvl = bm.loops.layers.uv.new('tex')
    zmin, zmax = (uv_h or (min(p[1] for p in prof), max(p[1] for p in prof)))
    for i in range(len(rings) - 1):
        for k in range(verts):
            k2 = (k + 1) % verts
            if prof[i][0] < 1e-5 and prof[i + 1][0] < 1e-5:
                continue
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            f.smooth = True
            uu = [k / verts, (k + 1) / verts, (k + 1) / verts, k / verts]
            vv = [(prof[i][1] - zmin) / (zmax - zmin)] * 2 + [(prof[i + 1][1] - zmin) / (zmax - zmin)] * 2
            for lo, a, b in zip(f.loops, uu, vv):
                lo[uvl].uv = (a, b)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = _obj(me, name, mat)
    if axis == 'X':
        ob.rotation_euler = (0, math.pi / 2, 0)
    elif axis == 'Y':
        ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = loc
    bpy.context.view_layer.update()
    return ob


def prism(name, poly, depth, mat=None, bv=0.002, loc=(0, 0, 0), plane='XZ', uvrot=None):
    """Extrude a 2D polygon. plane XZ: poly in (x,z), extruded along +Y (depth, centred)."""
    bm = bmesh.new()
    vs = []
    for (a, b) in poly:
        vs.append(bm.verts.new((a, -depth / 2, b) if plane == 'XZ' else (a, b, -depth / 2) if plane == 'XY' else (-depth / 2, a, b)))
    f = bm.faces.new(vs)
    bm.normal_update()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    d = (0, depth, 0) if plane == 'XZ' else (0, 0, depth) if plane == 'XY' else (depth, 0, 0)
    bmesh.ops.translate(bm, vec=d, verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[x for x in bm.faces if len(x.verts) > 4], quad_method='BEAUTY', ngon_method='BEAUTY')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = _obj(me, name, mat)
    if bv > 0:
        bevel(ob, bv, 2)
    ob.location = loc
    bpy.context.view_layer.update()
    smooth(ob)
    box_uv(ob, rot=uvrot)
    return ob


def grid(name, sx, sy, nx, ny, fn, mat=None):
    """Displaced sheet. x,y local; fn(x,y)->(x,y,z). UV metres."""
    bm = bmesh.new()
    vs = []
    uvs = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, y = sx * i / nx, sy * j / ny
            vs.append(bm.verts.new(fn(x, y)))
            uvs.append((x, y))
    uvl = bm.loops.layers.uv.new('tex')
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            ids = (a, a + 1, a + nx + 2, a + nx + 1)
            f = bm.faces.new([vs[k] for k in ids])
            f.smooth = True
            for lo, k in zip(f.loops, ids):
                lo[uvl].uv = uvs[k]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return _obj(me, name, mat)


def pane(name, w, h, loc, mat, nx=16, ny=22, amp=.0011):
    """Old float glass: a flat pane with a faint wave so reflections wobble."""
    ph = random.random() * 9
    def fn(x, y):
        z = amp * (math.sin(x * 9 + ph + y * 3) + .6 * math.sin(y * 13 + ph * 2 + x * 5))
        return (x - w / 2 + loc[0], z + loc[1], y - h / 2 + loc[2])
    o = grid(name, w, h, nx, ny, fn, mat)
    return o


def solidify(ob, t=0.002):
    m = ob.modifiers.new('sol', 'SOLIDIFY')
    m.thickness = t
    m.offset = 0
    apply_all(ob)
    return ob


def text3d(name, s, fontfile, size, depth=0.004, bv=0.0008, mat=None, loc=(0, 0, 0), align='CENTER', plane_xz=True, spacing=1.0):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = s
    cu.font = bpy.data.fonts.load(os.path.join(FONT, fontfile), check_existing=True)
    cu.size = size
    cu.extrude = depth / 2
    cu.bevel_depth = bv
    cu.bevel_resolution = 1
    cu.resolution_u = 4
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.space_character = spacing
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    ob = _obj(me, name, mat)
    if plane_xz:
        ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = loc
    bpy.context.view_layer.update()
    smooth(ob, 40)
    box_uv(ob)
    return ob


def bake_xform(ob):
    me = ob.data
    me.transform(ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)
    me.update()
    return ob


def join(obs, name):
    """Join meshes (materials and UV 'tex' preserved)."""
    obs = [o for o in obs if o and o.type == 'MESH']
    for o in obs:
        bake_xform(o)
        if 'tex' not in o.data.uv_layers:
            box_uv(o)
        for n in [u.name for u in o.data.uv_layers if u.name != 'tex' and not u.name.startswith('.')]:
            o.data.uv_layers.remove(o.data.uv_layers[n])
    ctx = {'selected_editable_objects': obs, 'active_object': obs[0], 'selected_objects': obs}
    with bpy.context.temp_override(**ctx):
        bpy.ops.object.join()
    o = obs[0]
    o.name = name
    o.data.name = name
    return o


# ---------------------------------------------------------------- materials
_imgs = {}


def img(path, colorspace='sRGB'):
    k = path
    if k not in _imgs:
        _imgs[k] = bpy.data.images.load(path)
        _imgs[k].colorspace_settings.name = colorspace
    return _imgs[k]


def phmap(tid, key):
    d = os.path.join(PH, tid)
    for e in ('jpg', 'png', 'exr'):
        p = os.path.join(d, key + '.' + e)
        if os.path.exists(p):
            return p
    return None


def _ramp(nt, inp, a, b, ca=(0, 0, 0, 1), cb=(1, 1, 1, 1)):
    n = nt.nodes.new('ShaderNodeValToRGB')
    r = n.color_ramp
    r.elements[0].position, r.elements[1].position = a, b
    r.elements[0].color, r.elements[1].color = ca, cb
    nt.links.new(inp, n.inputs[0])
    return n.outputs[0]


def _math(nt, op, a, b=None, clamp=True):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _mix(nt, fac, a, b, mode='MIX'):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    n.blend_type = mode
    n.clamp_factor = True
    if isinstance(fac, (int, float)):
        n.inputs['Factor'].default_value = fac
    else:
        nt.links.new(fac, n.inputs['Factor'])
    for k, v in (('A', a), ('B', b)):
        i = [s for s in n.inputs if s.name == k and s.type == 'RGBA'][0]
        if isinstance(v, (tuple, list)):
            i.default_value = (*v[:3], 1)
        else:
            nt.links.new(v, i)
    return [s for s in n.outputs if s.type == 'RGBA'][0]


def _noise(nt, coord, scale, detail=6, rough=.55, stretch=None):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    c = coord
    if stretch:
        m = nt.nodes.new('ShaderNodeMapping')
        m.inputs['Scale'].default_value = stretch
        nt.links.new(coord, m.inputs['Vector'])
        c = m.outputs[0]
    nt.links.new(c, n.inputs['Vector'])
    return n.outputs[0]


def pbr(name, tid=None, scale=1.0, tint=None, tint_amt=0.0, hsv=None, rough=None, rough_mul=1.0, metal=0.0,
        nor=1.0, flat_color=None, wear=0.35, grime=0.5, streak=0.4, rust=0.0, rust_tex='rusty_metal_02', edge_col=None,
        base_img=None, img_map=None, emit_img=None, emit=0.0, emit_col=None, spec=0.5, uv='tex', coat=0.0, tex_rot=False, rust_scale=7.0,
        stain=None, stain_col=(.045, .036, .026), stain_amt=.85, stain_plane='XZ', stain_rough=.82):
    """Layered weathered PBR. Everything stays bakeable: base -> tint -> grime (AO) -> streak -> edge wear -> rust."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    P = nt.nodes['Principled BSDF']
    uvn = nt.nodes.new('ShaderNodeUVMap')
    uvn.uv_map = uv
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, 1)
    if tex_rot:
        mp.inputs['Rotation'].default_value = (0, 0, math.pi / 2)
    nt.links.new(uvn.outputs[0], mp.inputs['Vector'])
    tex = mp.outputs[0]
    base = None
    if base_img:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = img(base_img)
        t.extension = 'EXTEND'
        v = uvn.outputs[0]
        if img_map:
            im = nt.nodes.new('ShaderNodeMapping')
            im.inputs['Scale'].default_value = (img_map[0], img_map[1], 1)
            nt.links.new(v, im.inputs['Vector'])
            v = im.outputs[0]
        nt.links.new(v, t.inputs[0])
        base = t.outputs[0]
    elif tid:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = img(phmap(tid, 'diff'))
        nt.links.new(tex, t.inputs[0])
        base = t.outputs[0]
    if flat_color:
        if base is None:
            r = nt.nodes.new('ShaderNodeRGB')
            r.outputs[0].default_value = (*flat_color, 1)
            base = r.outputs[0]
        else:
            # paint over a scanned surface: keep its luminance variation
            base = _mix(nt, tint_amt, flat_color, base, 'MULTIPLY')
    elif tint and base is not None:
        base = _mix(nt, tint_amt, base, tint, 'MULTIPLY')
    if hsv and base is not None:
        h = nt.nodes.new('ShaderNodeHueSaturation')
        h.inputs['Hue'].default_value, h.inputs['Saturation'].default_value, h.inputs['Value'].default_value = hsv
        nt.links.new(base, h.inputs['Color'])
        base = h.outputs[0]
    # roughness
    rr = None
    rp = phmap(tid, 'rough') if tid else None
    if rp and rough is None:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = img(rp, 'Non-Color')
        nt.links.new(tex, t.inputs[0])
        rr = _math(nt, 'MULTIPLY', t.outputs[0], rough_mul)
    else:
        v = nt.nodes.new('ShaderNodeValue')
        v.outputs[0].default_value = rough if rough is not None else .5
        rr = v.outputs[0]
    # normal
    Nsock = None
    np_ = phmap(tid, 'nor') if tid else None
    if np_ and nor > 0:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = img(np_, 'Non-Color')
        nt.links.new(tex, t.inputs[0])
        n = nt.nodes.new('ShaderNodeNormalMap')
        n.uv_map = uv
        n.inputs['Strength'].default_value = nor
        nt.links.new(t.outputs[0], n.inputs['Color'])
        Nsock = n.outputs[0]
    metal_sock = None
    tc = nt.nodes.new('ShaderNodeTexCoord').outputs['Object']
    # grime in crevices (AO) plus broken noise
    if grime > 0:
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
        ao.samples = 12
        ao.inputs['Distance'].default_value = .18
        cav = _ramp(nt, ao.outputs['AO'], .35, .95, (1, 1, 1, 1), (0, 0, 0, 1))
        nz = _ramp(nt, _noise(nt, tc, 14, 7, .6), .35, .62)
        g = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', cav, _math(nt, 'ADD', nz, .35)), grime)
        base = _mix(nt, g, base, (.055, .042, .03), 'MIX')
        rr = _mix(nt, g, rr, (.85, .85, .85))
    # vertical rain streaks
    if streak > 0:
        s = _ramp(nt, _noise(nt, tc, 9, 6, .62, stretch=(9, 9, .28)), .50, .68)
        s2 = _ramp(nt, _noise(nt, tc, 2.2, 3, .5), .4, .65)
        k = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', s, s2), streak)
        base = _mix(nt, k, base, (.10, .085, .065), 'MULTIPLY')
    # edge wear: compare bevelled vs true normal
    edge = None
    if wear > 0 or rust > 0:
        bvn = nt.nodes.new('ShaderNodeBevel')
        bvn.samples = 6
        bvn.inputs['Radius'].default_value = .012
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        d = nt.nodes.new('ShaderNodeVectorMath')
        d.operation = 'DOT_PRODUCT'
        nt.links.new(bvn.outputs[0], d.inputs[0])
        nt.links.new(geo.outputs['Normal'], d.inputs[1])
        edge = _ramp(nt, d.outputs['Value'], .90, .995, (1, 1, 1, 1), (0, 0, 0, 1))
    if wear > 0:
        nz = _ramp(nt, _noise(nt, tc, 55, 8, .62), .42, .60)
        w = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', edge, nz), wear * 2.2)
        col = edge_col or (.34, .30, .26)
        base = _mix(nt, w, base, col)
        rr = _mix(nt, w, rr, (.62, .62, .62))
    # rust blotches on metal, favouring edges and lower parts
    if rust > 0:
        rt = nt.nodes.new('ShaderNodeTexImage')
        rt.image = img(phmap(rust_tex, 'diff'))
        nt.links.new(tex, rt.inputs[0])
        nz = _noise(nt, tc, rust_scale, 8, .6)
        mask = _math(nt, 'ADD', _math(nt, 'MULTIPLY', nz, 1.0), _math(nt, 'MULTIPLY', edge, .22))
        lo = 0.70 - rust * .28
        rm = _ramp(nt, mask, lo, lo + .07)
        base = _mix(nt, rm, base, rt.outputs[0])
        rr = _mix(nt, rm, rr, (.88, .88, .88))
        ms = _mix(nt, rm, (metal, metal, metal), (0, 0, 0))
        metal_sock = ms
    # placed stains: rain runs and splash painted where they physically happen, projected on the XZ facade plane
    if stain:
        im, x0, x1, z0, z1 = stain
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc, sx.inputs[0])
        cb = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(_math(nt, 'DIVIDE', _math(nt, 'SUBTRACT', sx.outputs[0], x0, clamp=False), x1 - x0, clamp=False), cb.inputs[0])
        nt.links.new(_math(nt, 'DIVIDE', _math(nt, 'SUBTRACT', sx.outputs[2 if stain_plane == 'XZ' else 1], z0, clamp=False), z1 - z0, clamp=False), cb.inputs[1])
        ti = nt.nodes.new('ShaderNodeTexImage')
        ti.image = im
        ti.extension = 'EXTEND'
        nt.links.new(cb.outputs[0], ti.inputs[0])
        k = _math(nt, 'MULTIPLY', ti.outputs[0], stain_amt)
        base = _mix(nt, k, base, stain_col, 'MIX')
        rr = _mix(nt, k, rr, (stain_rough, stain_rough, stain_rough))
    nt.links.new(base, P.inputs['Base Color'])
    nt.links.new(rr, P.inputs['Roughness'])
    if metal_sock is not None:
        nt.links.new(metal_sock, P.inputs['Metallic'])
    else:
        P.inputs['Metallic'].default_value = metal
    if Nsock is not None:
        nt.links.new(Nsock, P.inputs['Normal'])
    P.inputs['Specular IOR Level'].default_value = spec
    if coat > 0:
        P.inputs['Coat Weight'].default_value = coat
        P.inputs['Coat Roughness'].default_value = .12
    if emit_img:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = img(emit_img)
        nt.links.new(uvn.outputs[0], t.inputs[0])
        nt.links.new(t.outputs[0], P.inputs['Emission Color'])
        P.inputs['Emission Strength'].default_value = emit
    elif emit > 0:
        P.inputs['Emission Color'].default_value = (*(emit_col or (1, 1, 1)), 1)
        P.inputs['Emission Strength'].default_value = emit
    return m


def glass(name='glass', tint=(.03, .04, .04), alpha=.10, rough=.05):
    """Thin window glass: alpha-blended on export, keeps a real reflection."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    P = m.node_tree.nodes['Principled BSDF']
    P.inputs['Base Color'].default_value = (*tint, 1)
    P.inputs['Roughness'].default_value = rough
    P.inputs['Metallic'].default_value = 0
    P.inputs['Alpha'].default_value = alpha
    P.inputs['Specular IOR Level'].default_value = .6
    m.surface_render_method = 'BLENDED'
    return m


def stain_image(name, w_m, h_m, sources, splash=.3, res=1400, seed=1, base=.0, cracks=0, crack_w=1, crack_v=.8, blobs=0):
    """Grey mask for a facade w_m x h_m. sources=[(x0,x1,ztop,length,strength)] run down from fixings; splash rises from the ground."""
    import numpy as np
    rng = np.random.default_rng(seed)
    W_, H_ = res, int(res * h_m / w_m)
    a = np.zeros((H_, W_), dtype=np.float32) + base
    px = W_ / w_m
    for x0, x1, zt, ln, st in sources:
        n = max(3, int((x1 - x0) * 46))
        for _ in range(n):
            x = int(rng.uniform(x0, x1) * px)
            hw = int(rng.integers(1, 5))
            l = ln * rng.uniform(.25, 1.0)
            yt = int(zt / h_m * H_)
            yb = max(0, int((zt - l) / h_m * H_))
            if yt <= yb or x <= hw or x >= W_ - hw:
                continue
            t = np.linspace(0, 1, yt - yb)
            v = st * rng.uniform(.25, 1) * (t ** 1.3)  # strongest at the source (top, t=1)
            jit = np.interp(np.linspace(0, 1, yt - yb), np.linspace(0, 1, (yt - yb) // 40 + 2), rng.uniform(.55, 1, (yt - yb) // 40 + 2))
            a[yb:yt, x - hw:x + hw] = np.maximum(a[yb:yt, x - hw:x + hw], (v * jit)[:, None])
    for _ in range(3):
        a = (np.roll(a, 1, 1) + a * 2 + np.roll(a, -1, 1)) / 4
    # wandering hairline cracks, thickest near the start
    for c_ in range(cracks):
        x, y = rng.uniform(0, W_), rng.uniform(0, H_)
        ang = rng.uniform(0, 6.28)
        steps = int(rng.uniform(.25, 1) * res * .5)
        for t_ in range(steps):
            ang += rng.normal(0, .07)
            if rng.random() < .006:
                ang += rng.choice((-1, 1)) * rng.uniform(.5, 1.1)
            x += math.cos(ang) * 1.6
            y += math.sin(ang) * 1.6
            ix, iy = int(x), int(y)
            if 2 < ix < W_ - 3 and 2 < iy < H_ - 3:
                r = max(0, int(crack_w * (1 - t_ / steps) + rng.random() * .9))
                a[iy - r:iy + r + 1, ix - r:ix + r + 1] = np.maximum(a[iy - r:iy + r + 1, ix - r:ix + r + 1], crack_v)
    # soft blots: oil drips, damp
    yy, xx = np.mgrid[0:H_, 0:W_]
    for b_ in range(blobs):
        cx, cy = rng.uniform(0, W_), rng.uniform(0, H_)
        r = rng.uniform(.03, .16) * px
        m_ = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))
        a = np.maximum(a, m_.astype(np.float32) * rng.uniform(.2, .6))
    if splash > 0:
        n1 = np.interp(np.linspace(0, 1, W_), np.linspace(0, 1, W_ // 60 + 2), rng.uniform(.4, 1, W_ // 60 + 2))
        for y in range(int(splash / h_m * H_)):
            k = (1 - y / (splash / h_m * H_)) ** 1.6
            spk = rng.uniform(.5, 1, W_)
            a[y] = np.maximum(a[y], k * n1 * spk * .85)
    a = np.clip(a, 0, 1)
    im = bpy.data.images.new(name, W_, H_, alpha=False, float_buffer=True)
    im.colorspace_settings.name = 'Non-Color'
    px4 = np.dstack((a, a, a, np.ones_like(a))).ravel()
    im.pixels.foreach_set(px4)
    im.pack()
    return im


def load_model(name, loc=(0, 0, 0), rz=0.0, scale=1.0):
    """Import a Poly Haven glTF; flatten to world meshes whose first UV is 'tex' so finish() can atlas them."""
    p = os.path.join(ROOT, 'assets', 'polyhaven_models', name, name + '.gltf')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    M = Matrix.Translation(loc) @ Matrix.Rotation(rz, 4, 'Z') @ Matrix.Scale(scale, 4)
    bpy.context.view_layer.update()
    out = []
    for o in new:
        if o.type == 'MESH':
            o.data = o.data.copy()
            o.data.transform(M @ o.matrix_world)
            o.parent = None
            o.matrix_world = Matrix.Identity(4)
            names = [u.name for u in o.data.uv_layers if not u.name.startswith('.')]
            if names:
                o.data.uv_layers[names[0]].name = 'tex'
            else:
                o.data.uv_layers.new(name='tex')
            out.append(o)
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
    return out


# ---------------------------------------------------------------- bake + LOD + export
def uv_for_bake(ob, margin=0.004, angle=40, boost=None, keep=(), keep_top=0.0):
    """Smart UV per density group. boost = {material name prefix: texel density factor}; text gets more, hidden parts less."""
    me = ob.data
    uv = me.uv_layers.get('bake') or me.uv_layers.new(name='bake')
    me.uv_layers.active = uv
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    boost = boost or {}
    def fac(i):
        n = me.materials[i].name
        for k, v in boost.items():
            if n.startswith(k):
                return v
        return 1.0
    mf = {i: fac(i) for i in range(len(me.materials))}
    kept = {i for i in mf if me.materials[i].name.startswith(tuple(keep))} if keep else set()
    for g in sorted(set(mf.values())):
        for p in me.polygons:
            p.select = mf[p.material_index] == g and p.material_index not in kept
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    # sheets laid out by hand: reuse their flat metre UVs, no projection squash
    if kept:
        tex = me.uv_layers['tex'].data
        bake = me.uv_layers['bake'].data
        for p in me.polygons:
            if p.material_index in kept:
                for li in p.loop_indices:
                    bake[li].uv = tex[li].uv
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    # area scale goes with the square of texel density
    data = me.uv_layers['bake'].data
    for p in me.polygons:
        f = mf[p.material_index]
        if f != 1.0:
            for li in p.loop_indices:
                data[li].uv = (data[li].uv[0] * f, data[li].uv[1] * f)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(margin=margin, rotate=True, shape_method='AABB')
    bpy.ops.object.mode_set(mode='OBJECT')
    # Blender's packer squashes one long printed sheet into a sliver; give kept sheets the top of the map by hand
    if keep_top > 0 and kept:
        tex = me.uv_layers['tex'].data
        bake = me.uv_layers['bake'].data
        ks = [li for p in me.polygons if p.material_index in kept for li in p.loop_indices]
        us = [tex[li].uv[0] for li in ks]
        vs = [tex[li].uv[1] for li in ks]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        lo = 1 - keep_top
        for p in me.polygons:
            for li in p.loop_indices:
                if p.material_index in kept:
                    bake[li].uv = (.004 + .992 * (tex[li].uv[0] - u0) / (u1 - u0), lo + .004 + (keep_top - .008) * (tex[li].uv[1] - v0) / (v1 - v0))
                else:
                    bake[li].uv = (bake[li].uv[0] * (lo - .01), bake[li].uv[1] * (lo - .01))


def _emit_swap(ob, sockname, is_color):
    """Rewire each material's output to an emission of a Principled input; return restore list."""
    restore = []
    for m in ob.data.materials:
        nt = m.node_tree
        P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        e = nt.nodes.new('ShaderNodeEmission')
        e.inputs['Strength'].default_value = 1
        i = P.inputs[sockname]
        if sockname == 'Emission Color' and P.inputs['Emission Strength'].default_value <= 0:
            e.inputs['Color'].default_value = (0, 0, 0, 1)
        elif i.is_linked:
            nt.links.new(i.links[0].from_socket, e.inputs['Color'])
        else:
            v = i.default_value
            e.inputs['Color'].default_value = tuple(v) if is_color else (v, v, v, 1)
        old = out.inputs['Surface'].links[0].from_socket
        nt.links.new(e.outputs[0], out.inputs['Surface'])
        restore.append((nt, out, old, e))
    return restore


def _emit_restore(restore):
    for nt, out, old, e in restore:
        nt.links.new(old, out.inputs['Surface'])
        nt.nodes.remove(e)


def bake_set(ob, name, res=2048, samples=16, ao_samples=96, margin=16, want_emit=False):
    """Bake BaseColor / Normal / ORM(+Emissive) from layered materials into 'bake' UV. Returns dict of paths."""
    s = bpy.context.scene
    s.render.bake.margin = margin
    s.render.bake.use_clear = True
    s.render.bake.target = 'IMAGE_TEXTURES'
    s.cycles.use_denoising = False
    d = os.path.join(EXPORT, name, 'textures')
    os.makedirs(d, exist_ok=True)
    def newimg(tag, cs, alpha=False):
        im = bpy.data.images.new(name + '_' + tag, res, res, alpha=alpha, float_buffer=True)
        im.colorspace_settings.name = cs
        return im
    def bind(im):
        for m in ob.data.materials:
            nt = m.node_tree
            n = nt.nodes.get('__bake') or nt.nodes.new('ShaderNodeTexImage')
            n.name = '__bake'
            n.image = im
            nt.nodes.active = n
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    ob.data.uv_layers.active = ob.data.uv_layers['bake']
    res_out = {}
    def do(tag, cs, sock=None, is_color=True, kind='EMIT', spp=samples):
        t0 = time.time()
        s.cycles.samples = spp
        im = newimg(tag, cs)
        bind(im)
        rst = _emit_swap(ob, sock, is_color) if sock else None
        if kind == 'NORMAL':
            bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=margin)
        elif kind == 'AO':
            s.world = s.world or bpy.data.worlds.new('w')
            bpy.ops.object.bake(type='AO', margin=margin)
        else:
            bpy.ops.object.bake(type='EMIT', margin=margin)
        if rst:
            _emit_restore(rst)
        log('bake', tag, round(time.time() - t0, 1), 's')
        return im
    base = do('BaseColor', 'sRGB', 'Base Color', True)
    nor = do('Normal', 'Non-Color', kind='NORMAL', spp=8)
    rough = do('Rough', 'Non-Color', 'Roughness', False)
    metal = do('Metal', 'Non-Color', 'Metallic', False)
    ao = do('AO', 'Non-Color', kind='AO', spp=ao_samples)
    emis = do('Emissive', 'sRGB', 'Emission Color', True) if want_emit else None
    # assemble ORM
    import numpy as np
    def arr(i):
        a = np.empty(res * res * 4, dtype=np.float32)
        i.pixels.foreach_get(a)
        return a.reshape(res, res, 4)
    o = arr(ao)[:, :, 0]
    r = arr(rough)[:, :, 0]
    mm = arr(metal)[:, :, 0]
    orm = np.dstack((o, r, mm, np.ones_like(o)))
    oi = newimg('ORM', 'Non-Color')
    oi.pixels.foreach_set(orm.astype(np.float32).ravel())
    def save(im, tag, png=True):
        p = os.path.join(d, '%s_%s.png' % (name, tag))
        s.render.image_settings.file_format = 'PNG'
        s.render.image_settings.color_depth = '8'
        s.render.image_settings.color_mode = 'RGB'
        s.render.image_settings.compression = 60
        s.view_settings.view_transform = 'Standard'
        s.view_settings.look = 'None'
        im.save_render(p, scene=s)
        res_out[tag] = p
        if res > 2048:
            d2 = os.path.join(EXPORT, name, 'textures_2k')
            os.makedirs(d2, exist_ok=True)
            im2 = im.copy()
            im2.scale(2048, 2048)
            im2.save_render(os.path.join(d2, '%s_%s.png' % (name, tag)), scene=s)
            bpy.data.images.remove(im2)
        return p
    save(base, 'BaseColor')
    save(nor, 'Normal')
    save(oi, 'ORM')
    if emis:
        save(emis, 'Emissive')
    # drop temp bake nodes
    for m in ob.data.materials:
        n = m.node_tree.nodes.get('__bake')
        if n:
            m.node_tree.nodes.remove(n)
    for im in (base, nor, rough, metal, ao, oi, emis):
        if im:
            bpy.data.images.remove(im)
    return res_out


def baked_material(name, maps):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    P = nt.nodes['Principled BSDF']
    def tex(p, cs):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(p)
        t.image.colorspace_settings.name = cs
        return t
    b = tex(maps['BaseColor'], 'sRGB')
    nt.links.new(b.outputs[0], P.inputs['Base Color'])
    o = tex(maps['ORM'], 'Non-Color')
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(o.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], P.inputs['Roughness'])
    nt.links.new(sep.outputs[2], P.inputs['Metallic'])
    n = tex(maps['Normal'], 'Non-Color')
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(n.outputs[0], nm.inputs['Color'])
    nt.links.new(nm.outputs[0], P.inputs['Normal'])
    # glTF exporter reads occlusion from a node group named 'glTF Material Output'
    g = bpy.data.node_groups.get('glTF Material Output')
    if g is None:
        g = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
        g.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    gn = nt.nodes.new('ShaderNodeGroup')
    gn.node_tree = g
    nt.links.new(sep.outputs[0], gn.inputs[0])
    if 'Emissive' in maps:
        e = tex(maps['Emissive'], 'sRGB')
        nt.links.new(e.outputs[0], P.inputs['Emission Color'])
        P.inputs['Emission Strength'].default_value = 1.0
    return m


def make_lod(ob, ratio, name):
    me = ob.data.copy()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = o.modifiers.new('dec', 'DECIMATE')
    m.decimate_type = 'COLLAPSE'
    m.ratio = ratio
    m.use_collapse_triangulate = True
    apply_all(o)
    o.data.name = name
    return o


def collision(boxes, name):
    """boxes = [(cx,cy,cz, sx,sy,sz, rz?)...]. No materials, no UV."""
    bm = bmesh.new()
    for b in boxes:
        r = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=b[3:6], verts=r['verts'])
        if len(b) > 6:
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(b[6], 3, 'Z'), verts=r['verts'])
        bmesh.ops.translate(bm, vec=b[:3], verts=r['verts'])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return _obj(me, name)


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def finish(obs, name, res=2048, col=None, want_emit=False, transparent=None, lods=(.4, .12), uv_margin=.004, sources=(), notes='', origin=None, boost=None, uv_angle=40, uv_keep=(), keep_top=0.0):
    """obs -> joined atlas mesh -> baked -> LOD0/1/2 + COL -> GLB + JSON sidecar. transparent = list of parts kept apart (glass)."""
    d = os.path.join(EXPORT, name)
    os.makedirs(d, exist_ok=True)
    ob = join(obs, name + '_LOD0')
    # centre XY on footprint, floor at z=0
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    minz = min(v.z for v in bb)
    cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
    cy = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
    if origin is not None:
        # module pieces share one origin on the ground so they snap together
        cx, cy = origin
        minz = 0.0
    shift = Matrix.Translation((-cx, -cy, -minz))
    ob.data.transform(shift)
    gl = None
    if transparent:
        for t in transparent:
            bake_xform(t)
        gl = join(transparent, name + '_glass_LOD0') if len(transparent) > 1 else transparent[0]
        gl.name = name + '_glass_LOD0'
        gl.data.transform(shift)
        for n in [u.name for u in gl.data.uv_layers if not u.name.startswith('.')]:
            gl.data.uv_layers.remove(gl.data.uv_layers[n])
        gl.data.uv_layers.new(name='bake')
    t0 = time.time()
    uv_for_bake(ob, uv_margin, uv_angle, boost, uv_keep, keep_top)
    log('uv', round(time.time() - t0, 1), 's tris', tris(ob))
    maps = bake_set(ob, name, res, want_emit=want_emit)
    mat = baked_material(name + '_mat', maps)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    ob.data.uv_layers.remove(ob.data.uv_layers['tex'])
    objs = [ob]
    stat = {'LOD0': tris(ob)}
    prev = ob
    for i, r in enumerate(lods, 1):
        lo = make_lod(ob, r, '%s_LOD%d' % (name, i))
        objs.append(lo)
        stat['LOD%d' % i] = tris(lo)
    bb = [Vector(c) for c in ob.bound_box]
    size = [max(v[i] for v in bb) - min(v[i] for v in bb) for i in range(3)]
    if col is None:
        col = [(0, 0, size[2] / 2, size[0], size[1], size[2])]
    co = collision(col, name + '_COL')
    objs.append(co)
    stat['COL'] = tris(co)
    if gl:
        objs.append(gl)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ob
    glb = os.path.join(d, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=True, export_image_format='JPEG',
                              export_jpeg_quality=92, export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials='EXPORT', export_extras=False)
    meta = {'name': name, 'tris': stat, 'size_m': [round(x, 3) for x in size], 'texture': [res, res], 'sources': list(sources), 'notes': notes,
            'maps': {k: os.path.basename(v) for k, v in maps.items()}, 'glb_mb': round(os.path.getsize(glb) / 1e6, 2)}
    json.dump(meta, open(os.path.join(d, name + '.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    log('DONE', name, meta)
    return meta
