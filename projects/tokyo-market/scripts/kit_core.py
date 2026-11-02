"""积木共用: 网格构建器, PBR 材质, 光照贴图 UV。局部坐标单位米, Z 朝上。"""
import math
import os

import bpy
from mathutils import Vector

from cijian_common import TEX, fresh_bsdf

# 每种可平铺材质一张贴图覆盖多少米
TILE = {"vermilion": 1.6, "roof": 1.5, "cedar": 1.13, "shutter": 2.0, "plaster": 2.23, "corrugated": 2.7,
        "paving": 2.0, "facade": 9.0, "wall": 2.4, "lit": 1.6, "roof_red": 1.5}

MAT_KEYS = ["vermilion", "roof", "cedar", "shutter", "plaster", "corrugated", "signs", "noren", "props", "lantern",
            "metal", "glow", "glass", "grime", "leaf", "concrete", "gold", "paving", "stain", "facade", "plastic",
            "rubber", "chrome", "lit", "roof_red", "citysign", "people", "trim", "shutter_art", "plaque", "blossom", "bronze", "globe", "wall", "window", "bulb", "skyline", "goods"]
ATLAS = 2048.0
TRIM_SIZE = 2048.0


def rect_uv(rect, size=ATLAS):
    """图集像素框 -> 四角 UV (左下, 右下, 右上, 左上)。"""
    x0, y0, x1, y1 = rect
    u0, u1 = x0 / size, x1 / size
    v0, v1 = 1 - y1 / size, 1 - y0 / size
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def trim_uv(row, u0, u1, v0=0.0, v1=1.0):
    """Trim Sheet 的四角 UV。row 是 (y0, y1) 像素; u 可以超过 1, 水平连续; v0/v1 取这一条的一部分, 0 是下沿。"""
    y0, y1 = row
    vb = 1 - y1 / TRIM_SIZE
    vt = 1 - y0 / TRIM_SIZE
    a, c = vb + (vt - vb) * v0, vb + (vt - vb) * v1
    return [(u0, a), (u1, a), (u1, c), (u0, c)]


def goods_uv(row, u0, u1):
    """货品图集第 row 行 (共 8 行), u 可超过 1, 在这一行里水平重复。"""
    return [(u0, 1 - (row % 8 + 1) / 8 + 0.002), (u1, 1 - (row % 8 + 1) / 8 + 0.002), (u1, 1 - (row % 8) / 8 - 0.002), (u0, 1 - (row % 8) / 8 - 0.002)]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Builder:
    def __init__(self):
        self.mats = {n: i for i, n in enumerate(MAT_KEYS)}
        self.verts = []
        self.faces = []  # (顶点索引, 材质号, UV, 是否平滑)

    def _planar_uv(self, pts, mat):
        tile = TILE.get(mat, 1.0)
        n = _cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0]))
        ax = max(range(3), key=lambda i: abs(n[i]))
        if ax == 0:
            return [(p[1] / tile, p[2] / tile) for p in pts]
        if ax == 1:
            return [(p[0] / tile, p[2] / tile) for p in pts]
        return [(p[0] / tile, p[1] / tile) for p in pts]

    def poly(self, pts, mat, facing=None, uv=None):
        if facing is not None:
            n = _cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0]))
            if _dot(n, facing) < 0:
                pts = list(reversed(pts))
                if uv:
                    uv = list(reversed(uv))
        base = len(self.verts)
        self.verts.extend(pts)
        self.faces.append((list(range(base, base + len(pts))), self.mats[mat],
                           uv or self._planar_uv(pts, mat), False))

    def box(self, mn, mx, mat, skip=""):
        """skip 里写要省掉的面: x- x+ y- y+ z- z+。"""
        x0, y0, z0 = mn
        x1, y1, z1 = mx
        sides = {
            "x-": ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)),
            "x+": ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)),
            "y-": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
            "y+": ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0)),
            "z-": ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0, 0, -1)),
            "z+": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)),
        }
        for key, (pts, facing) in sides.items():
            if key not in skip:
                self.poly(pts, mat, facing)

    def chamfer_post(self, cx, cy, hx, hy, c, z0, z1, mat):
        ring = [(cx - hx + c, cy - hy), (cx + hx - c, cy - hy), (cx + hx, cy - hy + c), (cx + hx, cy + hy - c),
                (cx + hx - c, cy + hy), (cx - hx + c, cy + hy), (cx - hx, cy + hy - c), (cx - hx, cy - hy + c)]
        for i in range(8):
            a, b = ring[i], ring[(i + 1) % 8]
            mid = ((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy, 0)
            self.poly([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], mat, mid)

    def pipe(self, p0, p1, r, mat, sides=6, r1=None, smooth=True):
        """任意方向的圆管, 顶点共享。r1 给了就是锥管。"""
        a, b = Vector(p0), Vector(p1)
        d = (b - a).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
        e1 = d.cross(up).normalized()
        e2 = d.cross(e1).normalized()
        base = len(self.verts)
        rr = (r, r if r1 is None else r1)
        for k, c in enumerate((a, b)):
            for i in range(sides):
                t = 2 * math.pi * i / sides
                v = c + e1 * math.cos(t) * rr[k] + e2 * math.sin(t) * rr[k]
                self.verts.append((v.x, v.y, v.z))
        m = self.mats[mat]
        for i in range(sides):
            j = (i + 1) % sides
            self.faces.append(([base + i, base + sides + i, base + sides + j, base + j], m,
                               [(0, 0), (0, 1), (1, 1), (1, 0)], smooth))
        # 判断朝向: 法线应朝外
        n = _cross(_sub(self.verts[base + sides], self.verts[base]), _sub(self.verts[base + sides + 1], self.verts[base]))
        out = _sub(self.verts[base], (a.x, a.y, a.z))
        if _dot(n, out) < 0:
            for f in range(len(self.faces) - sides, len(self.faces)):
                idx, mm, uv, s = self.faces[f]
                self.faces[f] = (list(reversed(idx)), mm, list(reversed(uv)), s)

    def lathe(self, cx, cy, profile, mat, sides=8, smooth=True):
        """profile: [(半径, z)...] 自下而上。"""
        base = len(self.verts)
        cols = sides + 1
        for r, z in profile:
            for i in range(cols):
                a = 2 * math.pi * i / sides
                self.verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        m = self.mats[mat]
        for j in range(len(profile) - 1):
            for i in range(sides):
                a = base + j * cols + i
                v0, v1 = j / (len(profile) - 1), (j + 1) / (len(profile) - 1)
                u0, u1 = i / sides, (i + 1) / sides
                self.faces.append(([a, a + 1, a + cols + 1, a + cols], m,
                                   [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], smooth))

    def torus_y(self, cy_axis_center, R, r, mat, seg=14, sides=4):
        """轮子: 环面在 YZ 平面。cy_axis_center=(x, y, z)。"""
        cx, cy, cz = cy_axis_center
        base = len(self.verts)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            for j in range(sides):
                b = 2 * math.pi * j / sides
                rad = R + r * math.cos(b)
                self.verts.append((cx + r * math.sin(b), cy + rad * math.cos(a), cz + rad * math.sin(a)))
        m = self.mats[mat]
        for i in range(seg):
            ni = (i + 1) % seg
            for j in range(sides):
                nj = (j + 1) % sides
                self.faces.append(([base + i * sides + j, base + ni * sides + j, base + ni * sides + nj,
                                    base + i * sides + nj], m, [(0, 0), (1, 0), (1, 1), (0, 1)], True))

    def to_mesh(self, name, materials):
        """materials: {key: 材质}, 缺的键用默认。"""
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], [f[0] for f in self.faces])
        for key in MAT_KEYS:
            me.materials.append(materials[key])
        me.update()
        uv0 = me.uv_layers.new(name="UV0")
        for poly, (idx, m, uvs, smooth) in zip(me.polygons, self.faces):
            poly.material_index = m
            poly.use_smooth = smooth
            for k in range(poly.loop_total):
                uv0.data[poly.loop_start + k].uv = uvs[k]
        return me


def _output_group():
    """glTF 导出器靠这个节点组识别 AO 贴图。"""
    name = "glTF Material Output"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    g = bpy.data.node_groups.new(name, "ShaderNodeTree")
    g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return g


def pbr(name, base=None, normal=None, orm=None, rough=0.7, metal=0.0, rgb=None, emission=None, emission_strength=0.0,
        double_sided=False, tint=None, alpha_tex=False):
    mat = bpy.data.materials.new(name)
    bsdf = fresh_bsdf(mat)
    nt = mat.node_tree
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal

    def image(file, non_color=False):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(os.path.join(TEX, file), check_existing=True)
        if non_color:
            node.image.colorspace_settings.name = "Non-Color"
        return node

    if base:
        tex = image(base)
        if tint:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 1.0
            nt.links.new(tex.outputs["Color"], mix.inputs[6])
            mix.inputs[7].default_value = (*tint, 1)
            nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        else:
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if alpha_tex:
            nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
            mat.surface_render_method = "BLENDED"
    elif rgb:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    if normal:
        tex = image(normal, True)
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    if orm:
        tex = image(orm, True)
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(tex.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
        grp = nt.nodes.new("ShaderNodeGroup")
        grp.node_tree = _output_group()
        nt.links.new(sep.outputs["Red"], grp.inputs["Occlusion"])
    if emission is not None:
        if isinstance(emission, str):
            tex = image(emission)
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        else:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    mat.use_backface_culling = not double_sided
    return mat


def tiling(name, role, res, **kw):
    r = f"{res}k"
    return pbr(name, f"yn_{role}_basecolor_{r}.jpg", f"yn_{role}_normal_{r}.jpg", f"yn_{role}_orm_{r}.jpg", **kw)


def wall_material(name, role, tint):
    """Poly Haven 扫描墙面。"""
    return pbr(name, f"wall_{role}_diff_2k.jpg", f"wall_{role}_nor_gl_2k.jpg", f"wall_{role}_arm_2k.jpg", tint=tint)


def weather(mat, amount=0.6, scale=1.0, rough_mul=None):
    """离线渲染用的世界坐标做旧: 竖向雨痕 + 大块污斑。导出 GLB 之后才加, 不影响 glTF 导出。"""
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    socket = bsdf.inputs["Base Color"]
    src = socket.links[0].from_socket if socket.is_linked else None
    base_value = tuple(socket.default_value)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.3 * scale, 1.3 * scale, 0.1 * scale)
    nt.links.new(geo.outputs["Position"], mapping.inputs["Vector"])
    streak = nt.nodes.new("ShaderNodeTexNoise")
    streak.inputs["Scale"].default_value = 2.2
    streak.inputs["Detail"].default_value = 9.0
    streak.inputs["Roughness"].default_value = 0.62
    nt.links.new(mapping.outputs["Vector"], streak.inputs["Vector"])
    patchy = nt.nodes.new("ShaderNodeTexNoise")
    patchy.inputs["Scale"].default_value = 0.55 * scale
    patchy.inputs["Detail"].default_value = 7.0
    nt.links.new(geo.outputs["Position"], patchy.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    add.inputs[1].default_value = 0.6
    nt.links.new(streak.outputs[0], add.inputs[0])
    nt.links.new(patchy.outputs[0], add.inputs[2])
    remap = nt.nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value = 0.62
    remap.inputs["From Max"].default_value = 0.98
    remap.inputs["To Max"].default_value = amount
    nt.links.new(add.outputs[0], remap.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    nt.links.new(remap.outputs[0], mix.inputs[0])
    if src is not None:
        nt.links.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = base_value
    mix.inputs[7].default_value = (0.32, 0.28, 0.24, 1)
    nt.links.new(mix.outputs[2], socket)
    if rough_mul is not None:
        rs = bsdf.inputs["Roughness"]
        if rs.is_linked:
            m = nt.nodes.new("ShaderNodeMath")
            m.operation = "MULTIPLY"
            m.inputs[1].default_value = rough_mul
            nt.links.new(rs.links[0].from_socket, m.inputs[0])
            nt.links.new(m.outputs[0], rs)
        else:
            rs.default_value *= rough_mul


def damp(mat):
    """地面潮湿度: 大块水渍处粗糙度更低。返回控制节点, 每版光线调 To Min。"""
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    rs = bsdf.inputs["Roughness"]
    src = rs.links[0].from_socket
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.42
    noise.inputs["Detail"].default_value = 8.0
    nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
    remap = nt.nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value = 0.42
    remap.inputs["From Max"].default_value = 0.56
    remap.inputs["To Min"].default_value = 0.6
    remap.inputs["To Max"].default_value = 1.0
    nt.links.new(noise.outputs[0], remap.inputs["Value"])
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = "MULTIPLY"
    nt.links.new(src, m.inputs[0])
    nt.links.new(remap.outputs[0], m.inputs[1])
    nt.links.new(m.outputs[0], rs)
    return remap


def all_materials():
    """共用材质库。朱红三种深浅共用同一套贴图, 只差 baseColorFactor。"""
    m = {
        "vermilion_a": tiling("yn_mat_vermilion_a", "vermilion", 2),
        "vermilion_b": tiling("yn_mat_vermilion_b", "vermilion", 2, tint=(0.62, 0.56, 0.56)),
        "vermilion_c": tiling("yn_mat_vermilion_c", "vermilion", 2, tint=(1.0, 0.86, 0.72)),
        "roof": tiling("yn_mat_roof", "kawara", 2),
        "cedar": tiling("yn_mat_cedar", "cedar", 2),
        "shutter": tiling("yn_mat_shutter", "shutter", 1),
        "plaster": tiling("yn_mat_plaster", "plaster", 1),
        "corrugated": tiling("yn_mat_corrugated", "corrugated", 1),
        "paving": tiling("yn_mat_paving", "paving", 2),
        "signs": pbr("yn_mat_signs", "yn_signs_basecolor_2k.png", rough=0.75, double_sided=True,
                     emission="yn_signs_basecolor_2k.png", emission_strength=0.0),
        "noren": pbr("yn_mat_noren", "yn_noren_basecolor_2k.png", rough=0.9, double_sided=True),
        "props": pbr("yn_mat_props", "yn_props_basecolor_1k.png", rough=0.6, double_sided=True),
        "lantern": pbr("yn_mat_lantern", "yn_lantern_basecolor_512.png", rough=0.8,
                       emission="yn_lantern_basecolor_512.png", emission_strength=1.6),
        "metal": pbr("yn_mat_metal_dark", rgb=(0.025, 0.026, 0.028), rough=0.5, metal=0.7),
        "glow": pbr("yn_mat_glow", rgb=(1.0, 0.9, 0.75), rough=0.5, emission=(1.0, 0.82, 0.58), emission_strength=7.0),
        "glass": pbr("yn_mat_glass_dark", rgb=(0.05, 0.05, 0.05), rough=0.15, emission=(1.0, 0.72, 0.42),
                     emission_strength=0.1),
        "grime": pbr("yn_mat_grime", "yn_grime_1k.png", rough=0.9, alpha_tex=True),
        "stain": pbr("yn_mat_ground_stain", "yn_ground_stain_1k.png", rough=0.35, alpha_tex=True),
        "leaf": pbr("yn_mat_leaf", rgb=(0.05, 0.13, 0.04), rough=0.6, double_sided=True),
        "concrete": pbr("yn_mat_concrete", rgb=(0.2, 0.195, 0.185), rough=0.9),
        "gold": pbr("yn_mat_gold", rgb=(0.85, 0.62, 0.22), rough=0.35, metal=1.0),
        "plastic": pbr("yn_mat_plastic_blue", rgb=(0.06, 0.2, 0.42), rough=0.55),
        "rubber": pbr("yn_mat_rubber", rgb=(0.012, 0.012, 0.013), rough=0.85),
        "chrome": pbr("yn_mat_steel", rgb=(0.62, 0.63, 0.64), rough=0.3, metal=1.0),
        "facade": pbr("yn_mat_city_a", "yn_city_facade_basecolor_1k.jpg", rough=0.8,
                      emission="yn_city_facade_emissive_1k.jpg", emission_strength=0.0),
    }
    m["lit"] = tiling("yn_mat_landmark_lit", "vermilion", 2, tint=(0.9, 0.75, 0.62), emission=(1.0, 0.36, 0.1), emission_strength=0.0)
    m["roof_red"] = pbr("yn_mat_roof_red", "yn_roof_red_basecolor_2k.jpg", "yn_kawara_normal_2k.jpg", "yn_kawara_orm_2k.jpg")
    m["trim"] = pbr("yn_mat_trim", "yn_trim_basecolor_2k.jpg", "yn_trim_normal_2k.jpg", "yn_trim_orm_2k.jpg",
                    emission="yn_trim_emissive_1k.jpg", emission_strength=0.0)
    m["shutter_art"] = pbr("yn_mat_shutter_art", "yn_shutter_art_2k.jpg", "yn_shutter_normal_1k.jpg", "yn_shutter_orm_1k.jpg")
    m["plaque"] = pbr("yn_mat_plaque", "yn_plaque_1k.png", rough=0.6, double_sided=True, emission="yn_plaque_1k.png", emission_strength=0.0)
    m["blossom"] = pbr("yn_mat_blossom", rgb=(0.9, 0.62, 0.66), rough=0.7, double_sided=True, emission=(1.0, 0.62, 0.66), emission_strength=0.0)
    m["wall"] = wall_material("yn_mat_wall_default", "plaster", (0.8, 0.78, 0.72))
    m["window"] = pbr("yn_mat_window", "yn_window_basecolor_1k.jpg", rough=0.06, emission="yn_window_emissive_1k.jpg", emission_strength=0.0)
    m["skyline"] = pbr("yn_mat_skyline", "yn_skyline_sunset_2k.png", rough=1.0, double_sided=True, alpha_tex=True,
                       emission="yn_skyline_sunset_2k.png", emission_strength=0.0)
    m["goods"] = pbr("yn_mat_goods_photo", "yn_goods_photo_2k.jpg", rough=0.45, emission="yn_goods_photo_2k.jpg", emission_strength=0.0)
    m["bulb"] = pbr("yn_mat_bulb", rgb=(1.0, 0.92, 0.8), rough=0.4, emission=(1.0, 0.8, 0.55), emission_strength=0.0)
    m["globe"] = pbr("yn_mat_globe", rgb=(0.86, 0.84, 0.78), rough=0.35, emission=(1.0, 0.9, 0.74), emission_strength=0.0)
    m["bronze"] = pbr("yn_mat_bronze", rgb=(0.24, 0.42, 0.34), rough=0.5, metal=0.6)
    m["citysign"] = pbr("yn_mat_citysigns", "yn_citysigns_1k.png", rough=0.6, double_sided=True,
                        emission="yn_citysigns_1k.png", emission_strength=0.0)
    m["people"] = pbr("yn_mat_people", "yn_people_palette.png", rough=0.8)
    return m


def slot_map(mats, paint="a"):
    """Builder 的材质键 -> 材质。paint 选朱红深浅。"""
    out = dict(mats)
    out["vermilion"] = mats[f"vermilion_{paint}"]
    return out


def add_lightmap_uv(me):
    """UV1: 不重叠的光照贴图 UV。同一个 mesh 只做一次。"""
    if "UV1" in me.uv_layers:
        return
    ob = bpy.data.objects.new("_tmp_uv", me)
    bpy.context.scene.collection.objects.link(ob)
    uv1 = me.uv_layers.new(name="UV1")
    me.uv_layers.active = uv1
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION", margin=0.004, shape_method="AABB")
    bpy.ops.object.mode_set(mode="OBJECT")
    me.uv_layers.active = me.uv_layers["UV0"]
    me.uv_layers["UV0"].active_render = True
    bpy.data.objects.remove(ob)


def uv1_check(me, grid=1024):
    """实测 UV1: 全部落在 0-1 内, 且没有两个三角形盖住同一像素中心。"""
    me.calc_loop_triangles()
    uv = me.uv_layers["UV1"].data
    owner = {}
    overlaps = 0
    outside = 0
    for tri in me.loop_triangles:
        pts = [uv[i].uv for i in tri.loops]
        for p in pts:
            if p.x < -1e-5 or p.x > 1 + 1e-5 or p.y < -1e-5 or p.y > 1 + 1e-5:
                outside += 1
        xs = [p.x * grid for p in pts]
        ys = [p.y * grid for p in pts]
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        for gy in range(max(0, int(min(ys))), min(grid, int(max(ys)) + 1)):
            for gx in range(max(0, int(min(xs))), min(grid, int(max(xs)) + 1)):
                cx, cy = gx + 0.5, gy + 0.5
                a = ((ys[1] - ys[2]) * (cx - xs[2]) + (xs[2] - xs[1]) * (cy - ys[2])) / d
                b = ((ys[2] - ys[0]) * (cx - xs[2]) + (xs[0] - xs[2]) * (cy - ys[2])) / d
                if a < 0 or b < 0 or a + b > 1:
                    continue
                if (gx, gy) in owner and owner[(gx, gy)] != tri.index:
                    overlaps += 1
                owner[(gx, gy)] = tri.index
    return {"overlap_pixels": overlaps, "outside": outside, "coverage": round(len(owner) / (grid * grid), 3)}
