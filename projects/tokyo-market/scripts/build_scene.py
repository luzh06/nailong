"""第 4 步总装: 积木库 + 摆放 + 早晨/日落光线 + 导出 + 预览。
用法: blender -b --python build_scene.py -- [--quick] [--no-render]
"""
import json
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_whitebox
import camera_match
import kit_atlas as K
import kit_core
import kit_props
import kit_shops
import kit_city
import kit_landmarks
from cijian_common import ROOT, collection, fresh_world, point_camera, setup_gpu
from kit_core import Builder, add_lightmap_uv, all_materials, pbr, slot_map, uv1_check, wall_material, weather, damp

PREVIEW = os.path.join(ROOT, "previews")
EXPORT = os.path.join(ROOT, "exports")
SEGMENTS = [(0.0, 29.4), (31.0, 60.4)]              # 精做的 60 米
LOD_SEGMENTS = [(-31.0, -1.6)] + [(62.0 + i * 31.0, 91.4 + i * 31.0) for i in range(6)]  # 只为主机位构图
SEED = 20261101
wet_node = None
LOOKS_TO_RENDER = ("morning", "sunset", "dusk")
HALF = build_whitebox.STREET_HALF
MODULE_LIMIT = 8000


class Kit:
    """按需生成并缓存 mesh, 同一部件只存一份。"""

    def __init__(self, mats):
        self.mats = mats
        self.meshes = {}
        self.kind = {}

    def get(self, name, build, paint="a", kind="part"):
        if name not in self.meshes:
            b = build()
            if isinstance(b, tuple):
                b, kind = b
            self.meshes[name] = b.to_mesh(name, slot_map(self.mats, paint))
            self.kind[name] = kind
            add_lightmap_uv(self.meshes[name])
        return self.meshes[name]

    def body(self, spec):
        key, w, front, upper, paint = spec
        return self.get(f"YN_shop_{key}_01", lambda: kit_shops.build_body(key, w, front, upper), paint, "body")

    def sign(self, i, w):
        return self.get(f"YN_sign_{i:02d}_w{int(w * 10)}", lambda: kit_shops.build_sign(i, w), kind="sign")

    def noren(self, i, w):
        return self.get(f"YN_noren_{i:02d}", lambda: kit_shops.build_noren(i, w), kind="noren")

    def shutter(self, w, art, y=0.04, tag=""):
        return self.get(f"YN_shutter_art{art}_w{int(w * 10)}{tag}", lambda: kit_shops.build_closed_shutter(w, art, y), kind="shutter")

    def plum(self, w, lite=False):
        return self.get(f"YN_prop_plum_branch_w{int(w * 10)}{'_lite' if lite else ''}", lambda: kit_shops.build_plum(w, lite), kind="plum")

    def awning(self, kind_name, w):
        return self.get(f"YN_awning_{kind_name}_w{int(w * 10)}", lambda: kit_shops.build_awning(kind_name, w),
                        kind="awning")

    def end(self, s):
        name = "YN_shop_end_01" if s < 0 else "YN_shop_end_02"
        return self.get(name, lambda: kit_shops.build_end(s), kind="end")

    def lod(self, i):
        return self.get(f"YN_shop_lod_{i:02d}", lambda: kit_shops.build_lod(i), kind="lod")


def place(me, name, loc, rot_z, col):
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    col.objects.link(ob)
    return ob


def side_xform(side, y):
    """side=-1 西侧, +1 东侧。局部 -Y 朝街。"""
    return (side * HALF, y, 0.0), (math.radians(90) if side < 0 else math.radians(-90))


def fill_widths(rng):
    widths = [3.6] * 5 + [5.4] * 2  # 合计 28.8, 加两头山墙各 0.3 正好一段 29.4
    rng.shuffle(widths)
    return widths


def layout_shops(kit, col, lights_col, closed_col, open_col):
    """28 个店位。不让相邻的店用同样的店身或雨棚, 同一店名至少隔 25 米或在街对面。"""
    rng = random.Random(SEED)
    bodies_by_w = {3.6: [s for s in kit_shops.BODIES if s[1] == 3.6], 5.4: [s for s in kit_shops.BODIES if s[1] == 5.4]}
    names_by_front = {}
    for i, shop in enumerate(K.SHOPS):
        names_by_front.setdefault(shop[4], []).append(i)
    placed = []
    report = []
    for side in (-1, 1):
        for y0, y1 in SEGMENTS:
            # 山墙: 西侧 -> 局部 +X 朝北; 东侧反过来
            # 山墙占段内最外 0.3 米, 原点贴着店铺那一面
            loc, rot = side_xform(side, y0 + 0.3)
            place(kit.end(-1 if side < 0 else 1), f"s_end_{side}_{int(y0)}a", loc, rot, col)
            loc, rot = side_xform(side, y1 - 0.3)
            place(kit.end(1 if side < 0 else -1), f"s_end_{side}_{int(y0)}b", loc, rot, col)
            y = y0 + 0.3
            prev_body = prev_awning = None
            for w in fill_widths(rng):
                yc = y + w / 2
                options = [b for b in bodies_by_w[w] if b[0] != prev_body]
                # 优先用现在用得少的店身
                options.sort(key=lambda b: (sum(1 for p in placed if p["body"] == b[0]), rng.random()))
                spec = options[0]
                names = names_by_front[spec[2]]

                def nearest_same_name(i):
                    dists = [abs(p["y"] - yc) for p in placed if p["sign"] == i]
                    return min(dists) if dists else 1e9

                # 优先选离同名店最远的; 街对面正对着同样算近
                sign = max(names, key=lambda i: (nearest_same_name(i), rng.random()))
                # 真实的仲见世整条街店头统一, 变化靠招牌和货品; 另外三种雨棚留在积木库里
                awning = "nakamise"
                loc, rot = side_xform(side, yc)
                tag = f"s_{'w' if side < 0 else 'e'}{len(placed):02d}"
                place(kit.body(spec), f"{tag}_body", loc, rot, col)
                place(kit.sign(sign, w), f"{tag}_sign", loc, rot, col)
                place(kit.awning(awning, w), f"{tag}_awning", loc, rot, col)
                if len(placed) % 2 == 0:
                    place(kit.plum(w), f"{tag}_plum", loc, rot, col)
                # 早晨八成的店还没开: 放下彩绘卷帘, 收起暖帘
                closed = rng.random() < 0.8
                place(kit.noren(sign, w), f"{tag}_noren", loc, rot, open_col if closed else col)
                if closed:
                    place(kit.shutter(w, rng.randrange(8)), f"{tag}_shutter", loc, rot, closed_col)
                for bx in kit_shops.bulb_xs(w):
                    bulb = bpy.data.lights.new(f"preview_bulb_{len(placed)}_{bx:.1f}", "POINT")
                    bulb.color = (1.0, 0.76, 0.5)
                    bulb.shadow_soft_size = 0.05
                    bulb["full"] = 9.0
                    bob = bpy.data.objects.new(bulb.name, bulb)
                    # 局部 (x, y) 转到世界: 西侧店 -Y 朝 +X, 东侧相反
                    wx, wy = (-kit_shops.BULB_Y, bx) if side < 0 else (kit_shops.BULB_Y, -bx)
                    bob.location = (loc[0] + wx, loc[1] + wy, kit_shops.BULB_Z - 0.02)
                    lights_col.objects.link(bob)
                # 预览用的店内灯, 不导出
                light = bpy.data.lights.new(f"preview_light_{tag}", "AREA")
                light.size = w * 0.6
                light.color = (1.0, 0.72, 0.45)
                light["full"] = 13.0 * w
                lob = bpy.data.objects.new(f"preview_light_{tag}", light)
                lob.location = (side * (HALF + 1.0), yc, 2.5)
                lights_col.objects.link(lob)
                placed.append({"side": side, "y": yc, "w": w, "body": spec[0], "sign": sign, "awning": awning})
                report.append(f"{tag} y={yc:5.1f} w={w} body={spec[0]} sign={K.SHOPS[sign][0]} awning={awning}")
                prev_body, prev_awning = spec[0], awning
                y += w
    return placed, report


def layout_lod(kit, col, closed_col):
    rng = random.Random(SEED + 1)
    for side in (-1, 1):
        for y0, y1 in LOD_SEGMENTS:
            loc, rot = side_xform(side, y0 + 0.3)
            place(kit.end(-1 if side < 0 else 1), f"lod_end_{side}_{int(y0)}a", loc, rot, col)
            loc, rot = side_xform(side, y1 - 0.3)
            place(kit.end(1 if side < 0 else -1), f"lod_end_{side}_{int(y0)}b", loc, rot, col)
            for i in range(8):
                loc, rot = side_xform(side, y0 + 0.3 + 3.6 * (i + 0.5))
                # 偶数位才有吊牌
                place(kit.lod(rng.randrange(4) + (0 if i % 2 == 0 else 4)), f"lod_{side}_{int(y0)}_{i}", loc, rot, col)
                if rng.random() < 0.85:
                    place(kit.shutter(3.6, rng.randrange(8), y=-0.11, tag="_lod"), f"lod_{side}_{int(y0)}_{i}_shutter", loc, rot, closed_col)


def layout_props(kit, col, lights_col):
    rng = random.Random(SEED + 2)
    meshes = {name: kit.get(name, fn) for name, fn in kit_props.PROPS.items()}
    east, west = math.radians(-90), math.radians(90)

    poles = [(11.7, 6.0), (11.7, 31.0), (11.7, 56.0), (-11.7, 18.0), (-11.7, 46.0)]
    for i, (x, y) in enumerate(poles):
        place(meshes["YN_prop_utility_pole_01"], f"p_pole_{i}", (x, y, 0), rng.uniform(-0.15, 0.15) + math.pi / 2, col)

    def lines(run):
        spans = []
        for (x0, y0), (x1, y1) in zip(run, run[1:]):
            for z, off in ((9.56, -0.84), (9.56, 0.84), (8.86, -0.69), (8.86, 0.69), (7.55, 0.0)):
                sag = 0.28 + 0.07 * (hash((z, off)) % 3)
                spans.append(((x0 + off, y0, z), (x1 + off, y1, z), sag))
        return spans

    spans = lines(poles[:3]) + lines(poles[3:])
    # 伸出可步行段外的两头, 免得电线突然断掉
    spans += [((11.7, 56.0, 8.86), (11.9, 92.0, 8.86), 0.35), ((11.7, 6.0, 8.86), (11.9, -30.0, 8.86), 0.35),
              ((-11.7, 46.0, 8.86), (-11.9, 82.0, 8.86), 0.35), ((-11.7, 18.0, 8.86), (-11.9, -20.0, 8.86), 0.35),
              # 过街到背巷外的楼
              ((11.7, 31.0, 7.55), (14.0, 28.0, 6.8), 0.12), ((-11.7, 46.0, 7.55), (-13.0, 49.0, 6.6), 0.1)]
    place(kit.get("YN_prop_wires_01", lambda: kit_props.wires(spans)), "p_wires", (0, 0, 0), 0, col)

    for i, (x, y, rot) in enumerate(((11.65, 16.0, east), (11.65, 42.0, east), (-11.65, 6.0, west), (-11.65, 34.0, west))):
        place(meshes["YN_prop_street_lamp_01"], f"p_lamp_{i}", (x, y, 0), rot, col)
        light = bpy.data.lights.new(f"preview_lamp_{i}", "POINT")
        light.color = (1.0, 0.84, 0.66)
        light.shadow_soft_size = 0.12
        light["full"] = 190.0
        lob = bpy.data.objects.new(f"preview_lamp_{i}", light)
        lob.location = (x + (-0.88 if x > 0 else 0.88), y, 4.18)
        lights_col.objects.link(lob)

    place(meshes["YN_prop_vending_machine_01"], "p_vending_0", (11.25, 24.5, 0), east, col)
    place(meshes["YN_prop_vending_machine_01"], "p_vending_1", (-11.25, 39.0, 0), west, col)

    for i, (x, y, r) in enumerate(((11.55, 11.0, 0.05), (11.6, 12.3, -0.08), (-11.6, 25.0, 0.12), (10.55, 49.0, 3.1))):
        place(meshes["YN_prop_bicycle_01"], f"p_bicycle_{i}", (x, y, 0), r, col)

    pots = [(10.2, 3.0), (10.25, 3.45), (10.2, 19.5), (10.3, 36.0), (10.2, 53.0), (-10.2, 12.0), (-10.25, 12.5),
            (-10.2, 28.0), (-10.2, 52.0), (-2.35, 30.2), (2.35, 30.2)]
    for i, (x, y) in enumerate(pots):
        place(meshes[f"YN_prop_planter_0{1 + i % 2}"], f"p_planter_{i}", (x, y, 0), rng.uniform(0, 6.28), col)

    # 塑料箱成摞放, 每摞高度和转角都不同
    stacks = [(10.3, 7.4, 3), (10.32, 7.95, 2), (10.3, 27.0, 4), (-10.3, 15.0, 2), (-10.32, 15.55, 3), (-10.3, 41.0, 3),
              (10.3, 58.0, 2)]
    n = 0
    for x, y, h in stacks:
        base = rng.uniform(-0.1, 0.1) + math.pi / 2
        for k in range(h):
            place(meshes["YN_prop_plastic_crate_01"], f"p_crate_{n}", (x, y, k * 0.29), base + rng.uniform(-0.05, 0.05), col)
            n += 1

    signs = [(-2.1, 5.8, 0), (2.1, 12.4, 1), (-2.1, 22.9, 1), (2.1, 37.5, 0), (-2.1, 47.0, 0), (2.1, 55.2, 1)]
    for i, (x, y, kind) in enumerate(signs):
        place(meshes[f"YN_prop_standing_sign_0{kind + 1}"], f"p_sign_{i}", (x, y, 0), rng.uniform(-0.18, 0.18), col)

    place(meshes["YN_prop_nobori_01"], "p_nobori_0", (10.1, 46.0, 0), math.radians(95), col)
    place(meshes["YN_prop_nobori_01"], "p_nobori_1", (-10.1, 22.0, 0), math.radians(-80), col)


def ground(col, mats):
    b = Builder()
    y0, y1 = -31.0, build_whitebox.STREET_END_Y
    for xa, xb, tag in ((-HALF, HALF, "street"), (9.5, 12.2, "lane_e"), (-12.2, -9.5, "lane_w")):
        b.poly([(xa, y0, 0), (xb, y0, 0), (xb, y1, 0), (xa, y1, 0)], "paving", (0, 0, 1))
    # 段与段之间的小巷也铺一下
    for y in (29.4, 60.4):
        for xa, xb in ((-9.5, -HALF), (HALF, 9.5)):
            b.poly([(xa, y, 0), (xb, y, 0), (xb, y + 1.6, 0), (xa, y + 1.6, 0)], "paving", (0, 0, 1))
    # 排水沟和井盖
    for sx in (-1, 1):
        xa, xb = sorted((sx * 2.1, sx * 2.2))
        b.poly([(xa, y0, 0.004), (xb, y0, 0.004), (xb, y1, 0.004), (xa, y1, 0.004)], "metal", (0, 0, 1))
    for mx, my in ((0.6, 9.0), (-0.9, 27.5), (0.3, 44.0), (-0.4, 58.0), (10.9, 20.0), (-10.8, 41.0)):
        b.poly([(mx + 0.32 * math.cos(k * math.pi / 8), my + 0.32 * math.sin(k * math.pi / 8), 0.005) for k in range(16)], "metal", (0, 0, 1))
    # 水渍, 打散路面的平铺感
    rng = random.Random(SEED + 3)
    for _ in range(34):
        x = rng.choice((rng.uniform(-2.3, 2.3), rng.uniform(9.8, 11.9), rng.uniform(-11.9, -9.8)))
        y = rng.uniform(-3, 64)
        s = rng.uniform(0.6, 2.0)
        a = rng.uniform(0, 3.14)
        ca, sa = math.cos(a) * s, math.sin(a) * s
        uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
        b.poly([(x - ca + sa, y - sa - ca, 0.006), (x + ca + sa, y + sa - ca, 0.006), (x + ca - sa, y + sa + ca, 0.006),
                (x - ca - sa, y - sa + ca, 0.006)], "stain", (0, 0, 1), uv)
    me = b.to_mesh("YN_ground_street_01", slot_map(mats))
    ob = bpy.data.objects.new("YN_ground_street_01", me)
    col.objects.link(ob)
    return me


def layout_city(mats, col):
    """背景楼按外墙材质合并, 省 Draw Call。"""
    # 近处的楼用 Poly Haven 扫描墙面; 窗户是真实几何, 不再画在贴图上
    tints = {"plaster": [(0.92, 0.88, 0.8), (0.78, 0.72, 0.6), (0.68, 0.8, 0.76), (0.98, 0.82, 0.58), (0.9, 0.72, 0.66)], 
             "tile": [(0.95, 0.9, 0.82), (0.66, 0.68, 0.72)], "concrete": [(0.85, 0.85, 0.85), (0.62, 0.62, 0.64)],
             "brick": [(1.0, 0.92, 0.86), (0.72, 0.62, 0.58)]}
    near_mats = [wall_material(f"yn_mat_city_{role}_{i}", role, tint) for role, ts in tints.items() for i, tint in enumerate(ts)]
    far_tint = [(0.34, 0.35, 0.39), (0.24, 0.25, 0.29)]
    far_mats = [pbr(f"yn_mat_city_far_{i}", f"yn_facade_{'concrete' if i else 'tile'}_basecolor_1k.jpg", rough=0.5, tint=t,
                    emission=f"yn_facade_{'concrete' if i else 'tile'}_emissive_1k.jpg", emission_strength=0.0)
                for i, t in enumerate(far_tint)]
    all_mats = near_mats + far_mats
    builders = [Builder() for _ in all_mats]
    for b in builders[:len(near_mats)]:
        b.facade_key = "wall"
    rng = random.Random(SEED + 4)

    for x0, x1, y0, y1, floors, face in kit_city.city_rows(SEED + 5):
        # 红砖放在最后两种, 权重压低, 不让它占满画面
        weights = [3] * (len(near_mats) - 2) + [1, 1]
        idx = rng.choices(range(len(near_mats)), weights)[0]
        roof = None
        # 191 左侧的红色折面屋顶和前面那栋大坡顶, 大致放回原来的位置
        board = rng.random() < 0.015
        if x1 < -12 and 44 < y0 < 58 and x0 > -25:
            roof, floors = "gable", max(floors, 4)
        if -40 < x0 < -20 and 28 < y0 < 42:
            roof, floors = "mansard", 4
        if x1 < -20 and y0 > 150:
            floors = min(floors, 3)
        kit_city.building(builders[idx], x0, x1, y0, y1, floors, rng, street_face=face, roof=roof, billboard=board)

    # 远景: 门背后的中层楼和两栋塔楼, 位置由 191 的像素反算
    # 更远处交给 layout_skyline 的照片背景
    mids = []
    for cx, cy, hw, h in mids:
        i = len(near_mats) + rng.randrange(2)
        kit_city.building(builders[i], cx - hw, cx + hw, cy - hw, cy + hw, int(h / 3), rng, roof="flat")

    for i, (b, m) in enumerate(zip(builders, all_mats)):
        if not b.faces:
            continue
        slots = slot_map(mats)
        slots["facade"] = m
        slots["wall"] = m
        me = b.to_mesh(f"YN_bg_city_{i:02d}", slots)
        col.objects.link(bpy.data.objects.new(f"YN_bg_city_{i:02d}", me))
    return far_mats


def layout_skyline(mats, col):
    """两层环形背景, 贴照片抠出来的天际线。一圈重复 10 次, 每次 36 度, 和照片的实际视角接近。"""
    seg = 120
    for name, r, z0, z1, offset in (("far", 850.0, -20.0, 102.0, 0.2), ("near", 430.0, -10.0, 52.0, 0.37)):
        b = Builder()
        for i in range(seg):
            a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
            u0, u1 = 10 * i / seg + offset, 10 * (i + 1) / seg + offset
            p0 = (r * math.sin(a0), 100 + r * math.cos(a0))
            p1 = (r * math.sin(a1), 100 + r * math.cos(a1))
            mid = (a0 + a1) / 2
            b.poly([(p0[0], p0[1], z0), (p1[0], p1[1], z0), (p1[0], p1[1], z1), (p0[0], p0[1], z1)], "skyline",
                   (-math.sin(mid), -math.cos(mid), 0), [(u0, 0), (u1, 0), (u1, 1), (u0, 1)])
        ob = bpy.data.objects.new(f"YN_bg_skyline_{name}", b.to_mesh(f"YN_bg_skyline_{name}", slot_map(mats)))
        col.objects.link(ob)
        # 只是背景, 不投影也不照亮场景
        ob.visible_shadow = False
        ob.visible_diffuse = False
        ob.visible_glossy = False


def layout_crowd(mats, col):
    """行人: 12 种, 主街密, 背巷稀。单独导出, 不进主场景 GLB。"""
    meshes = [kit_city.person(i + 40).to_mesh(f"YN_person_{i:02d}", slot_map(mats)) for i in range(16)]
    rng = random.Random(SEED + 6)
    n = 0

    extra_col = collection("scene_crowd_main")

    def spawn(x, y, extra=False):
        nonlocal n
        away = rng.random() < 0.5
        rot = (0 if away else math.pi) + rng.uniform(-0.5, 0.5)
        ob = place(rng.choice(meshes), f"preview_crowd_{n:03d}" if extra else f"crowd_{n:03d}", (x, y, 0), rot, extra_col if extra else col)
        s = rng.uniform(0.96, 1.04)
        ob.scale = (s, s, s)
        n += 1

    # 行人只是低模, 走近看像人偶; 步行镜头前方留空, 人群从十几米外才开始
    keep_clear = [(-0.7, 8.0, 15.0), (1.5, 43.0, 10.0), (10.9, 10.0, 16.0)]

    def clear(x, y):
        return all(math.hypot(x - cx, y - cy) > r for cx, cy, r in keep_clear)

    placed_pts = []

    def try_add(x, y):
        if not clear(x, y):
            spawn(x, y, extra=True)
            return
        if any(math.hypot(x - a, y - c) < 0.55 for a, c in placed_pts[-60:]):
            return
        placed_pts.append((x, y))
        spawn(x, y)

    # 主街: 分团的人流。可步行段留得松一点, 远处和 191 一样密
    y = -3.0
    while y < 230:
        density = 0.32 if y < 62 else 0.72
        for _ in range(4):
            if rng.random() < density:
                try_add(rng.uniform(-2.1, 2.1), y + rng.uniform(-0.8, 0.8))
        y += 1.4
    # 主机位前景再加密, 接近 191 的人流
    y = 0.0
    while y < 66:
        for _ in range(4):
            if rng.random() < 0.55:
                spawn(rng.uniform(-2.2, 2.2), y + rng.uniform(-0.7, 0.7), extra=True)
        y += 1.3
    # 背巷
    for x_range in ((10.0, 11.9), (-11.9, -10.0)):
        y = -5.0
        while y < 228:
            y += rng.uniform(4.0, 16.0)
            try_add(rng.uniform(*x_range), y)
            if rng.random() < 0.4:
                try_add(rng.uniform(*x_range), y + 0.7)
    return n


def sky_world(name, elevation, azimuth_deg, strength, tint):
    world = fresh_world(name, (0, 0, 0), strength)
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    sky = nt.nodes.new("ShaderNodeTexSky")
    types = {i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items}
    for t in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        if t in types:
            sky.sky_type = t
            break
    sky.sun_disc = False
    sky.sun_elevation = math.radians(elevation)
    sky.sun_rotation = math.radians(azimuth_deg)
    if hasattr(sky, "altitude"):
        sky.altitude = 40.0
    # 乘一层色, 把物理天空发白的部分压回有层次的颜色
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(sky.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*tint, 1)
    nt.links.new(mix.outputs[2], bg.inputs["Color"])
    return world


def dusk_world(name):
    """蓝调天空: 太阳在地平线下, 物理天空太黑, 用手调渐变。"""
    world = fresh_world(name, (0.02, 0.04, 0.1), 1.0)
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(coord.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.13, 0.13, 0.2, 1)
    cr.elements[1].position = 0.55
    cr.elements[1].color = (0.012, 0.03, 0.085, 1)
    mid = cr.elements.new(0.1)
    mid.color = (0.04, 0.075, 0.17, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.9
    return world


HDRI_ELEV = {}
SKY_CLAMP = 6.0


def hdri_world(name, azimuth, strength, tint):
    """真实天空 HDRI: 找出最亮的方向, 转到想要的方位, 太阳和阴影都由它决定。"""
    img = bpy.data.images.load(os.path.join(ROOT, "hdri", f"{name}.hdr"), check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    lum = px.reshape(h, w, 4)[..., :3].mean(axis=2)
    small = lum[: h // 8 * 8, : w // 8 * 8].reshape(h // 8, 8, w // 8, 8).mean(axis=(1, 3))
    iy, ix = np.unravel_index(np.argmax(small), small.shape)
    u = (ix + 0.5) / small.shape[1]
    elev = ((iy + 0.5) / small.shape[0] - 0.5) * 180
    phi = (0.5 - u) * 2 * math.pi
    target = math.radians(90 - azimuth)
    print(f"HDRI {name}: peak elevation {elev:.1f} deg, value {small.max():.1f}")
    HDRI_ELEV[name] = elev
    world = fresh_world(f"world_{name}", (0, 0, 0), strength)
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0, 0, phi - target)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = img
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(env.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*tint, 1)
    clamp = nt.nodes.new("ShaderNodeVectorMath")
    clamp.operation = "MINIMUM"
    clamp.inputs[1].default_value = (SKY_CLAMP, SKY_CLAMP, SKY_CLAMP)
    nt.links.new(mix.outputs[2], clamp.inputs[0])
    nt.links.new(clamp.outputs[0], bg.inputs["Color"])
    return world


def sun_direction(elevation, azimuth_deg):
    e, a = math.radians(elevation), math.radians(azimuth_deg)
    return Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))


# 光线版本: 太阳高度和方位 (方位从北顺时针), 自发光和预览灯强度。
LOOKS = {
    # 早晨: 东南低角度的清冷阳光, 对应参考图 189 的通透感。店还没全开, 灯基本关着
    "morning": dict(elev=30.0, az=165.0, sun=4.2, sun_rgb=(1.0, 0.84, 0.64), sky=0.44, tint=(1, 1, 1), exposure=-0.1, walk_ev=0.4, hdri=1.0, wet=0.75, skyline=0.5, rays=0.004, ray_rgb=(1.0, 0.96, 0.9), haze_rgb=(0.8, 0.86, 0.95), bulbs=0.0, bulb_w=0.0, blossom=0.12, haze=0.0003,
                    glow=0.0, lantern=0.0, glass=0.0, city=0.0, lights=0.3, lamps=0.0, lit=0.0, citysign=0.0, strips=0.0, landmark=0.0, signs=0.0),
    # 日落: 西南方向贴地的暖光, 灯已经亮了, 往 191 的方向走
    # 蓝调: 太阳刚落下, 对应参考图 191 的时刻
    "dusk": dict(elev=-3.0, az=248.0, sun=0.0, sun_rgb=(1.0, 0.6, 0.4), sky=1.0, tint=(0.5, 0.68, 1.18), exposure=0.5, walk_ev=-0.3, hdri=0.2, wet=0.34, skyline=0.55, rays=0.005, ray_rgb=(0.9, 0.9, 0.95), haze_rgb=(0.7, 0.78, 0.95), bulbs=34.0, bulb_w=3.4, blossom=0.03, haze=0.00012,
                 glow=4.0, lantern=1.2, glass=0.07, city=0.75, lights=1.0, lamps=1.2, lit=1.5, citysign=0.9, strips=1.0, landmark=1.0, signs=0.3),
    "sunset": dict(elev=11.0, az=215.0, sun=6.5, sun_rgb=(1.0, 0.47, 0.2), sky=0.42, tint=(1.0, 0.8, 0.68), exposure=-0.8, walk_ev=0.75, hdri=1.0, wet=0.55, skyline=0.5, rays=0.005, ray_rgb=(1.0, 0.86, 0.72), haze_rgb=(1.0, 0.78, 0.62), bulbs=20.0, bulb_w=1.6, blossom=0.08, haze=0.0003,
                   glow=2.6, lantern=0.9, glass=0.04, city=0.55, lights=1.0, lamps=1.0, lit=0.8, citysign=0.5, strips=0.45, landmark=0.25, signs=0.08),
}


class Lighting:
    def __init__(self, mats, facade_mats):
        self.mats = mats
        self.facade = facade_mats
        self.worlds = {}
        data = bpy.data.lights.new("preview_sun", "SUN")
        self.sun = bpy.data.objects.new("preview_sun", data)
        collection("preview_only").objects.link(self.sun)

    def _emit(self, mat, value):
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Emission Strength"].default_value = value

    def apply(self, name):
        look = LOOKS[name]
        scene = bpy.context.scene
        if name not in self.worlds:
            self.worlds[name] = hdri_world(name, look["az"], look["hdri"], look["tint"])
        scene.world = self.worlds[name]
        d = sun_direction(look["elev"], look["az"])
        self.sun.rotation_mode = "QUATERNION"
        self.sun.rotation_quaternion = d.to_track_quat("Z", "Y")
        self.sun.data.energy = look["sun"]
        self.sun.data.color = look["sun_rgb"]
        self.sun.data.angle = math.radians(1.6)
        scene.view_settings.exposure = look["exposure"]
        scene.view_settings.look = "AgX - Medium High Contrast"
        self._emit(self.mats["glow"], look["glow"])
        self._emit(self.mats["bulb"], look["bulbs"])
        self._emit(self.mats["skyline"], look["skyline"])
        self._emit(self.mats["goods"], look["signs"] * 0.4)
        for n in self.mats["skyline"].node_tree.nodes:
            if n.type == "TEX_IMAGE":
                n.image = bpy.data.images.load(os.path.join(ROOT, "textures", f"yn_skyline_{name}_2k.png"), check_existing=True)
        self._emit(self.mats["window"], look["city"] * 1.15)
        if wet_node:
            wet_node.inputs["To Min"].default_value = look["wet"]
        self._emit(self.mats["lantern"], look["lantern"])
        self._emit(self.mats["glass"], look["glass"])
        self._emit(self.mats["lit"], look["lit"])
        self._emit(self.mats["citysign"], look["citysign"])
        self._emit(self.mats["signs"], look["signs"])
        self._emit(self.mats["trim"], look["lit"] * 1.1)
        self._emit(self.mats["plaque"], look["signs"] * 0.7)
        self._emit(self.mats["globe"], look["signs"] * 2.6)
        # 花瓣是薄的, 背光时会透一点光, 所以不能全黑
        self._emit(self.mats["blossom"], look["blossom"])
        # 只有早晨是关店状态
        bpy.data.collections["scene_shutters_closed"].hide_render = name != "morning"
        bpy.data.collections["scene_open_only"].hide_render = name == "morning"
        for m in self.facade:
            self._emit(m, look["city"])
        for ob in bpy.data.objects:
            if ob.type == "LIGHT" and ob.name.startswith("preview_light"):
                ob.data.energy = ob.data["full"] * look["lights"]
            elif ob.type == "LIGHT" and ob.name.startswith("preview_bulb"):
                ob.data.energy = ob.data["full"] * look["bulb_w"]
            elif ob.type == "LIGHT" and ob.name.startswith("preview_lamp"):
                ob.data.energy = ob.data["full"] * look["lamps"]
            elif ob.type == "LIGHT" and ob.name.startswith("preview_strip"):
                ob.data.energy = ob.data["full"] * look["strips"]
            elif ob.type == "LIGHT" and ob.name.startswith("preview_landmark"):
                ob.data.energy = ob.data["full"] * look["landmark"]


def tris_of(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def export_glb(path, objects, fmt="WEBP"):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                              export_cameras=False, export_lights=False, export_image_format=fmt,
                              export_materials="EXPORT")
    bpy.ops.object.select_all(action="DESELECT")


def export_library(kit):
    """每个店面模块和道具单独一个 GLB, 放在原点。"""
    scene_col = bpy.context.scene.collection
    out = {}
    temp = []

    def temp_ob(name, me):
        ob = bpy.data.objects.new(name, me)
        scene_col.objects.link(ob)
        temp.append(ob)
        return ob

    defaults = {"A": 0, "B": 1, "C": 6, "D": 7, "E": 9, "F": 10, "G": 13, "H": 5}
    awn = {k: "nakamise" for k in "ABCDEFGH"}
    bpy.context.view_layer.update()
    for spec in kit_shops.BODIES:
        key, w = spec[0], spec[1]
        parts = [temp_ob(f"YN_shop_{key}_01", kit.body(spec)),
                 temp_ob(f"YN_shop_{key}_01_sign", kit.sign(defaults[key], w)),
                 temp_ob(f"YN_shop_{key}_01_awning", kit.awning(awn[key], w)),
                 temp_ob(f"YN_shop_{key}_01_noren", kit.noren(defaults[key], w))]
        path = os.path.join(EXPORT, f"YN_shop_{key}_01.glb")
        export_glb(path, parts)
        out[f"YN_shop_{key}_01"] = sum(tris_of(p.data) for p in parts)
        for p in parts:
            scene_col.objects.unlink(p)
            bpy.data.objects.remove(p)
        temp.clear()
    for name in kit_props.PROPS:
        ob = temp_ob(name, kit.meshes[name])
        export_glb(os.path.join(EXPORT, f"{name}.glb"), [ob])
        out[name] = tris_of(kit.meshes[name])
        scene_col.objects.unlink(ob)
        bpy.data.objects.remove(ob)
        temp.clear()
    return out


def render(name, camera, x, y, samples):
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.resolution_x = x
    scene.render.resolution_y = y
    scene.cycles.samples = samples
    scene.render.filepath = os.path.join(PREVIEW, name)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)


def eye_camera(name, loc, target, lens):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_fit = "HORIZONTAL"
    data.dof.use_dof = True
    data.dof.focus_distance = 8.0
    data.dof.aperture_fstop = 2.8
    ob = bpy.data.objects.new(name, data)
    collection("cameras").objects.link(ob)
    point_camera(ob, loc, target)
    return ob


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    quick = "--quick" in argv

    camera_match.clear_scene()
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.lights,
                  bpy.data.worlds):
        for item in list(block):
            block.remove(item)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    mats = all_materials()

    kit = Kit(mats)
    play = collection("scene_play_60m")
    context = collection("scene_context")
    props_col = collection("scene_props")
    lights_col = collection("preview_only")
    crowd_col = collection("scene_crowd")
    facade_mats = layout_city(mats, context)
    layout_skyline(mats, context)
    crowd_n = layout_crowd(mats, crowd_col)

    closed_col = collection("scene_shutters_closed")
    open_col = collection("scene_open_only")
    placed, report = layout_shops(kit, play, lights_col, closed_col, open_col)
    layout_lod(kit, context, closed_col)
    layout_props(kit, props_col, lights_col)

    ground_me = ground(play, mats)
    ground_ob = bpy.data.objects["YN_ground_street_01"]
    b = Builder()
    b.poly([(-1000, -1000, -0.02), (1000, -1000, -0.02), (1000, 1100, -0.02), (-1000, 1100, -0.02)], "concrete", (0, 0, 1))
    context.objects.link(bpy.data.objects.new("YN_ground_base_01", b.to_mesh("YN_ground_base_01", slot_map(mats))))
    gate_me = kit_landmarks.build_gate().to_mesh("YN_bg_hozomon_standin", slot_map(mats))
    add_lightmap_uv(gate_me)
    place(gate_me, "YN_bg_hozomon_standin", (0, build_whitebox.GATE_Y, 0), 0, context)
    pagoda_me = kit_landmarks.build_pagoda().to_mesh("YN_bg_pagoda_standin", slot_map(mats))
    add_lightmap_uv(pagoda_me)
    place(pagoda_me, "YN_bg_pagoda_standin", (-62.0, 344.0, 0), 0, context)

    # 沿街的灯带补光: 主街在 191 里最亮, 靠的就是这个
    for side in (-1, 1):
        for y0, y1 in LOD_SEGMENTS:
            light = bpy.data.lights.new(f"preview_strip_{side}_{int(y0)}", "AREA")
            light.shape = "RECTANGLE"
            light.size = 0.6
            light.size_y = y1 - y0
            light.color = (1.0, 0.8, 0.58)
            light["full"] = 300.0
            lob = bpy.data.objects.new(light.name, light)
            lob.location = (side * (HALF - 0.55), (y0 + y1) / 2, 2.75)
            lights_col.objects.link(lob)
    # 门和塔的投光
    for name, loc, power in (("gate_a", (-7.0, build_whitebox.GATE_Y - 12.0, 2.0), 1500.0),
                             ("gate_b", (7.0, build_whitebox.GATE_Y - 12.0, 2.0), 1500.0),
                             ("pagoda", (-62.0, 344.0 - 24.0, 4.0), 5000.0)):
        light = bpy.data.lights.new(f"preview_landmark_{name}", "POINT")
        light.color = (1.0, 0.55, 0.28)
        light.shadow_soft_size = 1.0
        light["full"] = power
        lob = bpy.data.objects.new(light.name, light)
        lob.location = loc
        lights_col.objects.link(lob)

    lighting = Lighting(mats, facade_mats)
    lighting.apply("sunset")

    cam_main = camera_match.add_main_camera()
    collection("cameras").objects.link(cam_main)
    scene.collection.objects.unlink(cam_main)
    cam_street = eye_camera("cam_walk_street", (-0.7, 1.0, 1.6), (0.5, 40.0, 2.3), 26.0)
    cam_mid = eye_camera("cam_walk_mid", (1.5, 38.0, 1.6), (-3.2, 46.5, 2.0), 24.0)
    cam_lane = eye_camera("cam_walk_lane", (10.9, 2.0, 1.6), (10.6, 40.0, 3.0), 28.0)

    # 统计
    crowd_objs = list(crowd_col.objects)
    shutter_objs = list(closed_col.objects)
    exportable = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("preview")
                  and o not in crowd_objs and o not in shutter_objs]
    unique = {}
    for o in exportable:
        unique[o.data.name] = o.data
    total_instanced = sum(tris_of(o.data) for o in exportable)
    total_unique = sum(tris_of(m) for m in unique.values())
    play_objs = [o for o in exportable if o.users_collection[0].name in ("scene_play_60m", "scene_props")]

    modules = {}
    for spec in kit_shops.BODIES:
        w = spec[1]
        body = tris_of(kit.body(spec))
        worst_sign = max(tris_of(kit.meshes[n]) for n in kit.meshes if n.startswith("YN_sign_") and n.endswith(f"w{int(w * 10)}"))
        worst_awning = max(tris_of(kit.meshes[n]) for n in kit.meshes if n.startswith("YN_awning_") and n.endswith(f"w{int(w * 10)}"))
        modules[f"YN_shop_{spec[0]}_01"] = {"body": body, "worst_with_sign_awning": body + worst_sign + worst_awning, "limit": MODULE_LIMIT}
    props = {}
    for name, fn in kit_props.PROPS.items():
        props[name] = {"tris": tris_of(kit.meshes[name]), "kind": kit.kind[name], "limit": kit_props.PROP_LIMITS[kit.kind[name]]}

    uv = {name: uv1_check(me, grid=512) for name, me in kit.meshes.items() if not name.startswith("YN_prop_wires")}
    bad_uv = {k: v for k, v in uv.items() if v["overlap_pixels"] or v["outside"]}
    cov = [v["coverage"] for v in uv.values()]

    stats = {
        "total_tris_instanced": total_instanced,
        "total_tris_unique": total_unique,
        "play_60m_tris_instanced": sum(tris_of(o.data) for o in play_objs),
        "objects": len(exportable),
        "shop_slots": len(placed),
        "crowd_people": crowd_n,
        "crowd_tris_instanced": sum(tris_of(o.data) for o in crowd_objs),
        "person_tris_max": max(tris_of(o.data) for o in crowd_objs),
        "gate_tris": tris_of(gate_me),
        "pagoda_tris": tris_of(pagoda_me),
        "city_tris": sum(tris_of(m) for n, m in unique.items() if n.startswith("YN_bg_city")),
        "bodies_used": sorted({p["body"] for p in placed}),
        "signs_used": len({p["sign"] for p in placed}),
        "modules": modules,
        "props": props,
        "uv1_meshes_checked": len(uv),
        "uv1_problems": bad_uv,
        "uv1_coverage_min": min(cov),
        "uv1_coverage_mean": round(sum(cov) / len(cov), 3),
    }
    with open(os.path.join(EXPORT, "stats_blender.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    with open(os.path.join(EXPORT, "layout_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("STATS", json.dumps({k: v for k, v in stats.items() if k not in ("modules", "props")}, ensure_ascii=False))
    print("STATS_MODULES", json.dumps(modules))
    print("STATS_PROPS", json.dumps(props))

    if not quick:
        export_library(kit)
        export_glb(os.path.join(EXPORT, "master_tokyo_scene.glb"), exportable)
        export_glb(os.path.join(EXPORT, "master_tokyo_crowd.glb"), crowd_objs)
        export_glb(os.path.join(EXPORT, "master_tokyo_shutters_closed.glb"), shutter_objs)

    blend = os.path.join(ROOT, "master_tokyo.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()

    if "--no-render" in argv:
        return

    scale = 2 if quick else 1
    samples = 64 if quick else 240
    setup_gpu(samples)
    # 做旧只给离线渲染, 放在导出之后
    for key, amount, sc, rough in (("vermilion_a", 0.45, 1.0, None), ("vermilion_b", 0.45, 1.3, None), ("vermilion_c", 0.45, 0.8, None),
                                   ("cedar", 0.4, 1.0, None), ("plaster", 0.5, 1.0, None), ("corrugated", 0.55, 1.0, None),
                                   ("shutter", 0.35, 1.0, None), ("concrete", 0.5, 0.7, None), ("paving", 0.4, 1.6, 0.62), ("signs", 0.3, 1.5, None)):
        weather(mats[key], amount, sc, rough)
    global wet_node
    wet_node = damp(mats["paving"])
    for m in bpy.data.materials:
        if m.name.startswith("yn_mat_city_") and "far" not in m.name:
            weather(m, 0.6, 0.8)
    # 空气透视: 远处的楼和门变淡, 主机位才用
    hb = Builder()
    hz = bpy.data.meshes.new("preview_haze")
    hz.from_pydata([(-700, -200, 0), (700, -200, 0), (700, 1400, 0), (-700, 1400, 0), (-700, -200, 70), (700, -200, 70), (700, 1400, 70), (-700, 1400, 70)],
                   [], [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    haze_mat = bpy.data.materials.new("preview_haze_mat")
    nt = haze_mat.node_tree if haze_mat.use_nodes else None
    haze_mat.use_nodes = True
    nt = haze_mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs["Color"].default_value = (0.75, 0.82, 0.95, 1)
    vol.inputs["Density"].default_value = 0.0011
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    hz.materials.append(haze_mat)
    haze = bpy.data.objects.new("preview_haze", hz)
    collection("preview_only").objects.link(haze)
    # 街道里的薄雾, 只给步行机位: 光束和灯晕都靠它
    near = bpy.data.meshes.new("preview_street_air")
    near.from_pydata([(-15, -35, 0), (15, -35, 0), (15, 75, 0), (-15, 75, 0), (-15, -35, 13), (15, -35, 13), (15, 75, 13), (-15, 75, 13)],
                     [], [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    near_mat = bpy.data.materials.new("preview_street_air_mat")
    near_mat.use_nodes = True
    nn = near_mat.node_tree
    nn.nodes.clear()
    nout = nn.nodes.new("ShaderNodeOutputMaterial")
    nvol = nn.nodes.new("ShaderNodeVolumeScatter")
    nn.links.new(nvol.outputs[0], nout.inputs["Volume"])
    near.materials.append(near_mat)
    air = bpy.data.objects.new("preview_street_air", near)
    collection("preview_only").objects.link(air)
    extra = bpy.data.collections["scene_crowd_main"]
    for look in LOOKS_TO_RENDER:
        lighting.apply(look)
        nvol.inputs["Density"].default_value = LOOKS[look]["rays"]
        nvol.inputs["Color"].default_value = (*LOOKS[look]["ray_rgb"], 1)
        vol.inputs["Color"].default_value = (*LOOKS[look]["haze_rgb"], 1)
        air.hide_render = True
        extra.hide_render = False
        base_ev = LOOKS[look]["exposure"]
        haze.hide_render = False
        vol.inputs["Density"].default_value = LOOKS[look]["haze"]
        sky_map = next(n for n in scene.world.node_tree.nodes if n.type == "MAPPING")
        sky_map.inputs["Rotation"].default_value[0] = math.radians(20)
        bulbs = [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("preview_bulb")]
        for o in bulbs:
            o.data.energy *= 2.6
        render(f"main_{look}.png", cam_main, 1320 // scale, 1787 // scale, samples)
        sky_map.inputs["Rotation"].default_value[0] = 0.0
        for o in bulbs:
            o.data.energy /= 2.6
        haze.hide_render = True
        scene.view_settings.exposure = base_ev + LOOKS[look]["walk_ev"]
        air.hide_render = False
        extra.hide_render = True
        render(f"walk_street_{look}.png", cam_street, 1600 // scale, 1000 // scale, samples)
        render(f"walk_mid_{look}.png", cam_mid, 1600 // scale, 1000 // scale, samples)
        scene.view_settings.exposure = base_ev + LOOKS[look]["walk_ev"] + 1.1  # 背巷本来就暗, 单独提曝光
        render(f"walk_lane_{look}.png", cam_lane, 1600 // scale, 1000 // scale, samples)

    lighting.apply("dusk")
    scene.camera = cam_main
    scene.render.resolution_x = camera_match.REF_W
    scene.render.resolution_y = camera_match.REF_H
    bpy.ops.wm.save_mainfile()


if __name__ == "__main__":
    main()
