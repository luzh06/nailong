"""bmesh helpers shared by the scene builders: faces, prisms, beams and boxes with metric UVs.

UVs are in metres so the web shaders can lay out windows, tiles and textures at real-world scale.
"""
import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient


def material(name, rgb, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def new_object(name, bm, materials, collection):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for mat in materials:
        mesh.materials.append(mat)
    if mesh.color_attributes:
        mesh.color_attributes.active_color_index = 0
        mesh.color_attributes.render_color_index = 0
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def new_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def oriented_rings(poly):
    poly = orient(poly, 1.0)
    return [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]


def rings_to_polygon(rings):
    return Polygon(rings["outer"], rings["holes"]).buffer(0)


def add_face(bm, verts, mat_index=0, uvs=None, color=None):
    face = bm.faces.new(verts)
    face.material_index = mat_index
    if uvs is not None:
        layer = bm.loops.layers.uv.verify()
        for loop, uv in zip(face.loops, uvs):
            loop[layer].uv = uv
    if color is not None:
        layer = bm.loops.layers.float_color.verify()
        for loop in face.loops:
            loop[layer] = color
    return face


def box_uv(bm, faces, scale=1.0):
    """Project each face onto the plane its normal faces most (box mapping), in metres / scale."""
    layer = bm.loops.layers.uv.verify()
    bm.normal_update()  # new faces have no normal until this runs
    for face in faces:
        n = face.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in face.loops:
            c = loop.vert.co
            if az >= ax and az >= ay:
                loop[layer].uv = (c.x / scale, c.y / scale)
            elif ax >= ay:
                loop[layer].uv = (c.y / scale, c.z / scale)
            else:
                loop[layer].uv = (c.x / scale, c.z / scale)


def add_prism(bm, rings, z0, z1, mat_index=0, cap_bottom=False, color=None):
    """Extrude a polygon (outer ring + holes, CCW outer / CW holes) between z0 and z1.

    Walls get U = distance along the ring and V = height, so façade grids run continuously
    around corners; the roof gets world X/Y.
    """
    flat = [Vector((x, y)) for ring in rings for x, y in ring]
    top = [bm.verts.new((v.x, v.y, z1)) for v in flat]
    bottom = [bm.verts.new((v.x, v.y, z0)) for v in flat]
    offset = 0
    for ring in rings:
        n = len(ring)
        run = 0.0
        for i in range(n):
            a, b = offset + i, offset + (i + 1) % n
            length = (flat[b] - flat[a]).length
            uvs = ((run, z0), (run + length, z0), (run + length, z1), (run, z1))
            add_face(bm, (bottom[a], bottom[b], top[b], top[a]), mat_index, uvs, color)
            run += length
        offset += n
    tri_input = [[Vector((x, y, 0.0)) for x, y in ring] for ring in rings]
    for tri in tessellate_polygon(tri_input):
        verts = [top[i] for i in tri]
        if (verts[1].co - verts[0].co).cross(verts[2].co - verts[0].co).z < 0:
            verts.reverse()
        try:
            add_face(bm, verts, mat_index, [(v.co.x, v.co.y) for v in verts], color)
            if cap_bottom:
                verts = [bottom[i] for i in reversed(tri)]
                add_face(bm, verts, mat_index, [(v.co.x, v.co.y) for v in verts], color)
        except ValueError:
            pass  # degenerate triangle from duplicated points


def add_beam(bm, p0, p1, width, depth, mat_index=0):
    """Box beam from p0 to p1 with a width x depth cross-section. UVs: U along the beam."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    length = axis.length
    if length < 1e-3:
        return
    fwd = axis / length
    ref = Vector((0, 0, 1)) if abs(fwd.z) < 0.95 else Vector((1, 0, 0))
    side = fwd.cross(ref).normalized()
    up = side.cross(fwd).normalized()
    hw, hd = width / 2, depth / 2
    corners = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    ring0 = [bm.verts.new(p0 + side * a + up * b) for a, b in corners]
    ring1 = [bm.verts.new(p1 + side * a + up * b) for a, b in corners]
    perimeter = [0.0, width, width + depth, 2 * width + depth, 2 * (width + depth)]
    for i in range(4):
        j = (i + 1) % 4
        v0, v1 = perimeter[i], perimeter[i + 1]
        add_face(bm, (ring0[i], ring0[j], ring1[j], ring1[i]), mat_index,
                 ((0.0, v0), (0.0, v1), (length, v1), (length, v0)))
    end_uv = [(a, b) for a, b in corners]
    add_face(bm, list(reversed(ring0)), mat_index, list(reversed(end_uv)))
    add_face(bm, ring1, mat_index, end_uv)


def add_box(bm, center, size, frame, mat_index=0):
    """Axis-aligned box in a local frame (3x3 Matrix whose columns are the local axes); box-mapped UVs."""
    c = Vector(center)
    hx, hy, hz = (s / 2 for s in size)
    pts = [Vector((sx * hx, sy * hy, sz * hz)) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    v = [bm.verts.new(c + frame @ p) for p in pts]
    faces = []
    for idx in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        local = [pts[i] for i in idx]
        normal = (local[1] - local[0]).cross(local[2] - local[0])
        axis = max(range(3), key=lambda k: abs(normal[k]))
        if axis == 2:  # top / bottom
            uvs = [(p.x, p.y) for p in local]
        else:          # sides: U along the other horizontal axis, V = height above the box base
            uvs = [(p[1 - axis], p.z + hz) for p in local]
        faces.append(add_face(bm, [v[i] for i in idx], mat_index, uvs))
    return faces
