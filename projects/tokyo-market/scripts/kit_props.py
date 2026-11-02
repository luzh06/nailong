"""道具: 原点都在底部中心。上限: 小道具 1500, 大道具 3000 三角面。"""
import math

import kit_atlas as K
from kit_core import Builder, rect_uv

# 名字 -> (构建函数, 三角面上限)
PROP_LIMITS = {"small": 1500, "large": 3000}


def bicycle():
    """买菜自行车: 前筐, 后架, 单脚撑。沿 Y 方向停放。"""
    b = Builder()
    wheel_r = 0.33
    fy, ry = 0.53, -0.53
    z = wheel_r + 0.01
    for y in (fy, ry):
        b.torus_y((0, y, z), wheel_r - 0.018, 0.018, "rubber", seg=20, sides=5)
        b.torus_y((0, y, z), wheel_r - 0.045, 0.008, "chrome", seg=20, sides=3)
        for i in range(10):
            a = 2 * math.pi * i / 10
            b.pipe((0, y, z), (0, y + (wheel_r - 0.045) * math.cos(a), z + (wheel_r - 0.045) * math.sin(a)), 0.0018,
                   "chrome", sides=3, smooth=False)
        b.pipe((-0.035, y, z), (0.035, y, z), 0.025, "chrome", sides=8)
    bb = (0, -0.05, 0.31)
    seat = (0, -0.26, 0.76)
    head = (0, 0.33, 0.8)
    head_low = (0, 0.36, 0.68)
    rear = (0, ry, z)
    front = (0, fy, z)
    frame = "metal"
    for p0, p1 in ((bb, seat), (bb, head_low), (seat, rear), (bb, rear), (head_low, front), (head, head_low)):
        b.pipe(p0, p1, 0.016, frame, sides=6)
    # 低跨下管
    b.pipe((0, -0.2, 0.62), head_low, 0.014, frame, sides=6)
    # 车把
    b.pipe(head, (0, 0.3, 0.98), 0.012, "chrome", sides=6)
    b.pipe((-0.25, 0.25, 1.0), (0.25, 0.25, 1.0), 0.011, "chrome", sides=6)
    for s in (-1, 1):
        b.pipe((s * 0.2, 0.25, 1.0), (s * 0.27, 0.2, 1.0), 0.016, "rubber", sides=6)
    # 车座
    b.lathe(seat[0], seat[1], [(0.0, 0.77), (0.1, 0.78), (0.11, 0.81), (0.07, 0.84), (0.0, 0.85)], "rubber", sides=8)
    b.pipe((0, -0.26, 0.74), (0, -0.26, 0.78), 0.012, "chrome", sides=4)
    # 前筐
    bx0, bx1, by0, by1, bz0, bz1 = -0.16, 0.16, 0.55, 0.85, 0.72, 0.94
    for x in (bx0, -0.05, 0.05, bx1):
        b.pipe((x, by0, bz0), (x, by0, bz1), 0.003, "chrome", sides=3, smooth=False)
        b.pipe((x, by1, bz0), (x, by1, bz1), 0.003, "chrome", sides=3, smooth=False)
    for y in (by0, 0.7, by1):
        b.pipe((bx0, y, bz0), (bx0, y, bz1), 0.003, "chrome", sides=3, smooth=False)
        b.pipe((bx1, y, bz0), (bx1, y, bz1), 0.003, "chrome", sides=3, smooth=False)
    for z2 in (bz0, (bz0 + bz1) / 2, bz1):
        for p0, p1 in (((bx0, by0, z2), (bx1, by0, z2)), ((bx0, by1, z2), (bx1, by1, z2)), ((bx0, by0, z2), (bx0, by1, z2)),
                       ((bx1, by0, z2), (bx1, by1, z2))):
            b.pipe(p0, p1, 0.004, "chrome", sides=3, smooth=False)
    b.pipe((0, 0.66, bz0), head_low, 0.006, "chrome", sides=3, smooth=False)
    # 后架和挡泥板
    b.box((-0.08, -0.72, 0.68), (0.08, -0.3, 0.695), "chrome", skip="")
    for s in (-1, 1):
        b.pipe((s * 0.07, -0.56, 0.68), (s * 0.06, ry, z), 0.005, "chrome", sides=3, smooth=False)
    for y in (ry, fy):
        for i in range(8):
            a0, a1 = math.radians(35 + i * 13), math.radians(35 + (i + 1) * 13)
            if y > 0:
                a0, a1 = math.pi - a1, math.pi - a0
            r = wheel_r + 0.012
            b.poly([(-0.028, y - r * math.cos(a0), z + r * math.sin(a0)), (0.028, y - r * math.cos(a0), z + r * math.sin(a0)),
                    (0.028, y - r * math.cos(a1), z + r * math.sin(a1)), (-0.028, y - r * math.cos(a1), z + r * math.sin(a1))],
                   "metal", (0, 0, 1))
    # 链罩, 脚踏, 单脚撑
    b.box((0.03, -0.53, 0.25), (0.05, 0.02, 0.38), "metal")
    b.pipe((-0.1, -0.05, 0.31), (0.1, -0.05, 0.31), 0.008, "chrome", sides=4)
    for x, dz in ((-0.14, 0.12), (0.14, -0.12)):
        b.box((x - 0.05, -0.09, 0.31 + dz - 0.01), (x + 0.05, -0.01, 0.31 + dz + 0.01), "rubber")
    b.pipe((-0.04, ry + 0.02, z), (-0.2, ry + 0.15, 0.01), 0.008, "chrome", sides=4)
    return b, "small"


def vending_machine():
    """无品牌贩卖机, 约 1 米宽, 1.83 米高。正面朝 -Y。"""
    b = Builder()
    w, d, h = 1.03, 0.72, 1.83
    hw = w / 2
    b.box((-hw, 0, 0.05), (hw, d, h), "plaster", skip="z-")
    b.box((-hw + 0.03, 0.03, 0), (hw - 0.03, d - 0.03, 0.05), "metal", skip="z- z+")
    f = rect_uv(K.VENDING_FRONT, size=1024.0)
    y = -0.005
    b.poly([(-hw + 0.02, y, 0.08), (hw - 0.02, y, 0.08), (hw - 0.02, y, h - 0.03), (-hw + 0.02, y, h - 0.03)], "props",
           (0, -1, 0), f)
    # 边框和顶灯
    b.box((-hw - 0.012, -0.02, 0.05), (-hw + 0.02, 0.0, h), "chrome", skip="y+ z-")
    b.box((hw - 0.02, -0.02, 0.05), (hw + 0.012, 0.0, h), "chrome", skip="y+ z-")
    b.box((-hw, -0.02, h - 0.03), (hw, 0.0, h), "chrome", skip="y+")
    b.box((-hw + 0.06, -0.024, h - 0.075), (hw - 0.06, -0.012, h - 0.05), "glow", skip="y+ z- x- x+")
    # 取物口的外框和投币口
    b.box((-hw + 0.08, -0.02, 0.17), (hw - 0.08, -0.002, 0.2), "metal", skip="y+")
    b.box((-hw + 0.08, -0.02, 0.36), (hw - 0.08, -0.002, 0.39), "metal", skip="y+")
    b.box((0.18, -0.03, 0.56), (0.42, -0.002, 0.66), "chrome", skip="y+ z-")
    # 地脚螺栓和散热口
    b.box((-hw + 0.1, d, 0.1), (hw - 0.1, d + 0.005, 0.5), "shutter", skip="y-")
    return b, "large"


def utility_pole():
    """水泥电杆, 高 10 米, 带横担、绝缘子和变压器。"""
    b = Builder()
    b.pipe((0, 0, 0), (0, 0, 10.0), 0.17, "concrete", sides=10, r1=0.095)
    # 踏脚钉
    for i in range(10):
        z = 2.2 + i * 0.55
        s = 1 if i % 2 else -1
        b.pipe((s * 0.06, 0, z), (s * 0.22, 0, z), 0.009, "metal", sides=4)
    # 横担
    arms = ((9.4, 0.9), (8.7, 0.75), (7.4, 0.5))
    for z, hw in arms:
        b.box((-hw, -0.04, z - 0.04), (hw, 0.04, z + 0.04), "metal")
        for x in (-hw + 0.06, 0.0 if hw > 0.6 else hw - 0.06, hw - 0.06):
            b.lathe(x, 0, [(0.03, z + 0.04), (0.055, z + 0.08), (0.04, z + 0.12), (0.055, z + 0.16), (0.02, z + 0.2)],
                    "plaster", sides=6, smooth=True)
    b.pipe((-0.6, 0, 8.3), (0, 0, 9.0), 0.012, "metal", sides=4)
    b.pipe((0.6, 0, 8.3), (0, 0, 9.0), 0.012, "metal", sides=4)
    # 变压器
    for x in (-0.3, 0.3):
        b.pipe((x, 0.25, 6.2), (x, 0.25, 7.2), 0.14, "concrete", sides=10)
        b.lathe(x, 0.25, [(0.14, 7.2), (0.14, 7.24), (0.0, 7.26)], "metal", sides=10, smooth=False)
        b.lathe(x, 0.25, [(0.015, 7.24), (0.04, 7.28), (0.015, 7.34)], "plaster", sides=5)
    b.box((-0.5, 0.08, 6.55), (0.5, 0.14, 6.63), "metal")
    # 线缆盒和黄色保护套
    b.box((-0.1, -0.24, 3.0), (0.1, -0.13, 3.42), "chrome", skip="y+")
    b.pipe((0, -0.16, 3.42), (0, -0.14, 6.1), 0.018, "metal", sides=5)
    b.pipe((0.1, -0.1, 0), (0.1, -0.1, 2.5), 0.028, "gold", sides=6)
    # 杆上小招牌位, 留空
    b.box((-0.16, -0.17, 1.9), (0.16, -0.15, 2.4), "plaster", skip="y+")
    return b, "large"


def street_lamp():
    """背巷路灯, 高 4.3 米。灯头朝 -Y。"""
    b = Builder()
    b.pipe((0, 0, 0), (0, 0, 3.9), 0.05, "metal", sides=8, r1=0.035)
    b.pipe((0, 0, 3.9), (0, -0.28, 4.3), 0.028, "metal", sides=6)
    b.pipe((0, -0.28, 4.3), (0, -0.75, 4.32), 0.024, "metal", sides=6)
    b.box((-0.09, -1.02, 4.27), (0.09, -0.7, 4.34), "metal", skip="z-")
    b.box((-0.075, -1.0, 4.255), (0.075, -0.72, 4.27), "glow", skip="z+")
    b.lathe(0, 0, [(0.075, 0), (0.07, 0.35), (0.05, 0.42)], "metal", sides=8)
    return b, "small"


def planter(seed=0):
    """陶盆和阔叶植物。叶子是折一下的菱形, 不用透明贴图。"""
    b = Builder()
    b.lathe(0, 0, [(0.0, 0.0), (0.13, 0.0), (0.16, 0.2), (0.19, 0.32), (0.18, 0.34), (0.15, 0.32), (0.0, 0.31)], "concrete",
            sides=12, smooth=False)
    n = 34
    for i in range(n):
        a = (i * 2.399963 + seed)
        spread = 0.04 + 0.33 * (i / n)
        z0 = 0.34 + 0.75 * (1 - i / n) ** 0.8
        length = 0.28 + 0.12 * ((i * 7) % 5) / 5
        dx, dy = math.cos(a), math.sin(a)
        p0 = (spread * dx, spread * dy, z0)
        mid = (p0[0] + dx * length * 0.5, p0[1] + dy * length * 0.5, z0 + 0.06)
        tip = (p0[0] + dx * length, p0[1] + dy * length, z0 - 0.08)
        sx, sy = -dy * 0.05, dx * 0.05
        drop = 0.015
        b.poly([p0, (mid[0] + sx, mid[1] + sy, mid[2] - drop), mid], "leaf", (0, 0, 1))
        b.poly([p0, mid, (mid[0] - sx, mid[1] - sy, mid[2] - drop)], "leaf", (0, 0, 1))
        b.poly([(mid[0] + sx, mid[1] + sy, mid[2] - drop), tip, mid], "leaf", (0, 0, 1))
        b.poly([mid, tip, (mid[0] - sx, mid[1] - sy, mid[2] - drop)], "leaf", (0, 0, 1))
        b.pipe((0, 0, 0.32), p0, 0.006, "leaf", sides=3, smooth=False)
    return b, "small"


def plastic_crate():
    """啤酒箱式塑料箱: 外框 + 网格。45x35x30 厘米。"""
    b = Builder()
    w, d, h = 0.45, 0.35, 0.3
    hw, hd = w / 2, d / 2
    t = 0.012
    for z0, z1 in ((0.0, 0.03), (0.13, 0.155), (h - 0.03, h)):
        b.box((-hw, -hd, z0), (hw, -hd + t, z1), "plastic")
        b.box((-hw, hd - t, z0), (hw, hd, z1), "plastic")
        b.box((-hw, -hd, z0), (-hw + t, hd, z1), "plastic")
        b.box((hw - t, -hd, z0), (hw, hd, z1), "plastic")
    for x in (-hw, -0.13, -0.045, 0.045, 0.13, hw - 0.015):
        for y0, y1 in ((-hd, -hd + t), (hd - t, hd)):
            b.box((x, y0, 0), (x + 0.015, y1, h), "plastic", skip="z- z+")
    for y in (-hd, -0.06, 0.06, hd - 0.015):
        for x0, x1 in ((-hw, -hw + t), (hw - t, hw)):
            b.box((x0, y, 0), (x1, y + 0.015, h), "plastic", skip="z- z+")
    # 箱底网格
    for x in (-0.15, -0.05, 0.05, 0.15):
        b.box((x - 0.006, -hd, 0.004), (x + 0.006, hd, 0.018), "plastic", skip="z- x- x+ y- y+".replace("x- x+ ", ""))
    for y in (-0.1, 0.0, 0.1):
        b.box((-hw, y - 0.006, 0.004), (hw, y + 0.006, 0.018), "plastic", skip="z-")
    return b, "small"


def standing_sign(kind=0):
    """A 字立式看板。"""
    b = Builder()
    w, h = 0.46, 0.86
    lean = 0.13
    rect = rect_uv(K.STAND_SIGN[kind], size=1024.0)
    rect2 = rect_uv(K.STAND_SIGN[1 - kind], size=1024.0)
    for s, uv in ((-1, rect), (1, rect2)):
        p = [(-w / 2, s * lean, 0.05), (w / 2, s * lean, 0.05), (w / 2, s * 0.01, h), (-w / 2, s * 0.01, h)]
        b.poly(p, "props", (0, s, 0.1), uv)
        # 木框
        for x0, x1 in ((-w / 2 - 0.025, -w / 2), (w / 2, w / 2 + 0.025)):
            b.poly([(x0, s * (lean + 0.012), 0.0), (x1, s * (lean + 0.012), 0.0), (x1, s * 0.022, h + 0.02), (x0, s * 0.022, h + 0.02)],
                   "cedar", (0, s, 0.1))
        b.poly([(-w / 2 - 0.025, s * 0.022, h), (w / 2 + 0.025, s * 0.022, h), (w / 2 + 0.025, s * 0.022, h + 0.03), (-w / 2 - 0.025, s * 0.022, h + 0.03)],
               "cedar", (0, s, 0))
    b.box((-w / 2 - 0.03, -0.04, h + 0.005), (w / 2 + 0.03, 0.04, h + 0.03), "cedar", skip="z-")
    return b, "small"


def nobori_banner():
    """红色旗幡, 191 背巷里有。无文字。"""
    b = Builder()
    b.pipe((0, 0, 0), (0, 0, 2.5), 0.014, "chrome", sides=5)
    b.pipe((0, 0, 2.42), (0.62, 0, 2.42), 0.008, "chrome", sides=4)
    b.lathe(0, 0, [(0.12, 0.0), (0.12, 0.05), (0.02, 0.07)], "metal", sides=8, smooth=False)
    uv_full = rect_uv(K.BANNER, size=1024.0)
    nz, nx = 3, 4
    base = len(b.verts)
    for k in range(nz + 1):
        for j in range(nx + 1):
            t = j / nx
            s = k / nz
            b.verts.append((0.02 + 0.58 * t, 0.018 * math.sin(t * 8 + s * 2), 0.7 + 1.72 * s))
    m = b.mats["props"]
    for k in range(nz):
        for j in range(nx):
            a = base + k * (nx + 1) + j
            b.faces.append(([a, a + 1, a + nx + 2, a + nx + 1], m, uv_full, True))
    return b, "small"


PROPS = {
    "YN_prop_bicycle_01": bicycle,
    "YN_prop_vending_machine_01": vending_machine,
    "YN_prop_utility_pole_01": utility_pole,
    "YN_prop_street_lamp_01": street_lamp,
    "YN_prop_planter_01": lambda: planter(0),
    "YN_prop_planter_02": lambda: planter(2.1),
    "YN_prop_plastic_crate_01": plastic_crate,
    "YN_prop_standing_sign_01": lambda: standing_sign(0),
    "YN_prop_standing_sign_02": lambda: standing_sign(1),
    "YN_prop_nobori_01": nobori_banner,
}


def wires(spans):
    """电线: spans = [(起点, 终点, 下垂量)], 整段一个网格。"""
    b = Builder()
    for p0, p1, sag in spans:
        seg = 8
        prev = None
        for i in range(seg + 1):
            t = i / seg
            pt = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t,
                  p0[2] + (p1[2] - p0[2]) * t - sag * 4 * t * (1 - t))
            if prev:
                b.pipe(prev, pt, 0.009, "rubber", sides=3, smooth=False)
            prev = pt
    return b
