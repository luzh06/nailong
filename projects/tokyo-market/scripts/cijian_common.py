"""Blender 脚本共用函数。单位米, Z 朝上。"""
import math
import os

import bmesh
import bpy
from mathutils import Euler, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")


def collection(name, parent=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in (parent or bpy.context.scene.collection).children:
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def fresh_bsdf(mat):
    """Blender 5 的新材质不带默认节点, 这里显式建好 BSDF 和输出。"""
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return bsdf


def fresh_world(name, rgb, strength=1.0):
    world = bpy.data.worlds.new(name)
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*rgb, 1)
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return world


def clay(name, rgb, rough=0.85):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = fresh_bsdf(mat)
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def mesh_object(name, verts, faces, mat, col):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def wb_box(name, mn, mx, mat, col):
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh_object(name, v, f, mat, col)


def wb_gable(name, x_eave_a, x_eave_b, y0, y1, z_base, z_eave, z_ridge, mat, col):
    """沿 Y 方向的两坡屋顶体量, 屋脊平行于街道。"""
    xa, xb = x_eave_a, x_eave_b
    xm = (xa + xb) / 2
    v = [(xa, y0, z_base), (xb, y0, z_base), (xb, y0, z_eave), (xm, y0, z_ridge), (xa, y0, z_eave),
         (xa, y1, z_base), (xb, y1, z_base), (xb, y1, z_eave), (xm, y1, z_ridge), (xa, y1, z_eave)]
    f = [(0, 1, 2, 3, 4), (9, 8, 7, 6, 5), (0, 5, 6, 1), (1, 6, 7, 2), (2, 7, 8, 3), (3, 8, 9, 4), (4, 9, 5, 0)]
    return mesh_object(name, v, f, mat, col)


def point_camera(cam, location, target, roll_deg=0.0):
    loc = Vector(location)
    direction = Vector(target) - loc
    quat = direction.to_track_quat("-Z", "Y")
    cam.location = loc
    cam.rotation_euler = quat.to_euler()
    if roll_deg:
        cam.rotation_euler.rotate_axis("Z", math.radians(roll_deg))


def setup_gpu(samples, denoise=True):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    scene.cycles.device = "GPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = denoise
    if denoise:
        scene.cycles.denoiser = "OPTIX"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def count_tris(objs):
    total = 0
    for ob in objs:
        if ob.type != "MESH":
            continue
        ob.data.calc_loop_triangles()
        total += len(ob.data.loop_triangles)
    return total
