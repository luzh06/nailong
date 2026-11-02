"""背景: 杂居楼生成器, 宝藏门和五重塔替身, 人群。

杂居楼用世界坐标建模并按材质合并, 主要给主机位看; 位置是按 191 的感觉排的, 不是测绘。
门和塔是替身, 只为构图和气氛, 不是文物复原。
"""
import math
import random

import kit_atlas as K
from kit_core import goods_uv
from kit_core import Builder, rect_uv

FLOOR = 3.0


def fk(b):
    """这个 Builder 的外墙材质键: 近处楼用扫描墙面 wall, 远处楼用带窗的贴图 facade。"""
    return getattr(b, "facade_key", "facade")


def _window_face(b, o, u, n, length, height, floors, rng, skip_ground=False):
    """一面有真实窗洞的墙: 窗台, 窗侧, 退进去的玻璃, 窗下雨痕。o 是左下角, u 沿墙, n 朝外。"""
    key = fk(b)
    depth = 0.13

    def P(s, z, d=0.0):
        return (o[0] + u[0] * s - n[0] * d, o[1] + u[1] * s - n[1] * d, z)

    face = (n[0], n[1], 0)
    # 每面墙窗型不同: 开间, 窗高都随机
    bays = max(1, int(length / rng.uniform(1.8, 4.2)))
    sill_off, head_off = rng.choice(((0.7, 2.3), (0.95, 2.3), (1.1, 2.4), (0.25, 2.5), (1.3, 2.2)))
    bw = length / bays
    for fl in range(floors):
        z0, z1 = fl * FLOOR, (fl + 1) * FLOOR if fl < floors - 1 else height
        if fl == 0 and skip_ground:
            b.poly([P(0, z0), P(length, z0), P(length, z1), P(0, z1)], key, face)
            continue
        sill, head = z0 + sill_off, z0 + head_off
        b.poly([P(0, z0), P(length, z0), P(length, sill), P(0, sill)], key, face)
        b.poly([P(0, head), P(length, head), P(length, z1), P(0, z1)], key, face)
        for i in range(bays):
            s0, s1 = i * bw, (i + 1) * bw
            if rng.random() < 0.14:
                b.poly([P(s0, sill), P(s1, sill), P(s1, head), P(s0, head)], key, face)
                continue
            m = bw * rng.uniform(0.15, 0.24)
            a, c = s0 + m, s1 - m
            b.poly([P(s0, sill), P(a, sill), P(a, head), P(s0, head)], key, face)
            b.poly([P(c, sill), P(s1, sill), P(s1, head), P(c, head)], key, face)
            # 窗洞四边
            b.poly([P(a, sill), P(a, sill, depth), P(a, head, depth), P(a, head)], key, (u[0], u[1], 0))
            b.poly([P(c, sill, depth), P(c, sill), P(c, head), P(c, head, depth)], key, (-u[0], -u[1], 0))
            b.poly([P(a, head), P(c, head), P(c, head, depth), P(a, head, depth)], key, (0, 0, -1))
            b.poly([P(a, sill, depth), P(c, sill, depth), P(c, sill), P(a, sill)], key, (0, 0, 1))
            cell = rng.randrange(64)
            cx, cy = cell % 8, cell // 8
            b.poly([P(a, sill, depth), P(c, sill, depth), P(c, head, depth), P(a, head, depth)], "window", face,
                   rect_uv((cx * 128, cy * 128, cx * 128 + 128, cy * 128 + 128), size=1024.0))
            # 窗台板和窗下雨痕
            b.poly([P(a - 0.05, sill - 0.07, -0.05), P(c + 0.05, sill - 0.07, -0.05), P(c + 0.05, sill, -0.05), P(a - 0.05, sill, -0.05)], "concrete", face)
            b.poly([P(a - 0.05, sill, -0.05), P(c + 0.05, sill, -0.05), P(c + 0.05, sill, 0), P(a - 0.05, sill, 0)], "concrete", (0, 0, 1))
            # 窗下的室外机, 窗外的小招牌
            if rng.random() < 0.16 and sill - z0 > 0.75:
                q0, q1 = P(a + 0.05, sill - 0.72, 0), P(a + 0.8, sill - 0.12, -0.32)
                b.box((min(q0[0], q1[0]), min(q0[1], q1[1]), q0[2]), (max(q0[0], q1[0]), max(q0[1], q1[1]), q1[2]), "plaster", skip="z-")
            if rng.random() < 0.07:
                i_sign = rng.randrange(8)
                b.poly([P(a, head + 0.03, -0.03), P(c, head + 0.03, -0.03), P(c, head + 0.33, -0.03), P(a, head + 0.33, -0.03)], "citysign", face,
                       [(i_sign * 0.125, 0.5), (i_sign * 0.125 + 0.125, 0.5), (i_sign * 0.125 + 0.125, 0.56), (i_sign * 0.125, 0.56)])
            r = rng.random()
            b.poly([P(a - 0.02, max(z0, sill - 1.15), -0.004), P(c + 0.02, max(z0, sill - 1.15), -0.004), P(c + 0.02, sill - 0.07, -0.004), P(a - 0.02, sill - 0.07, -0.004)],
                   "grime", face, [(r, 0), (r + 0.3, 0), (r + 0.3, 1), (r, 1)])


def _flat_roof_clutter(b, x0, x1, y0, y1, h, rng):
    w, d = x1 - x0, y1 - y0
    # 水箱架
    if rng.random() < 0.55 and min(w, d) > 4:
        cx, cy = rng.uniform(x0 + 1.5, x1 - 1.5), rng.uniform(y0 + 1.5, y1 - 1.5)
        hs = 0.7
        for sx in (-1, 1):
            for sy in (-1, 1):
                b.pipe((cx + sx * hs, cy + sy * hs, h), (cx + sx * hs, cy + sy * hs, h + 1.6), 0.05, "metal", sides=4, smooth=False)
        b.box((cx - hs - 0.1, cy - hs - 0.1, h + 1.6), (cx + hs + 0.1, cy + hs + 0.1, h + 2.9), "plaster", skip="z-")
    # 电梯间
    if rng.random() < 0.6 and min(w, d) > 5:
        px, py = rng.uniform(x0 + 0.5, x1 - 3.2), rng.uniform(y0 + 0.5, y1 - 3.2)
        b.box((px, py, h), (px + 2.6, py + 2.6, h + 2.5), fk(b), skip="z-")
    # 室外机成排
    for _ in range(rng.randint(1, 4)):
        ax, ay = rng.uniform(x0 + 0.4, x1 - 1.0), rng.uniform(y0 + 0.4, y1 - 0.8)
        b.box((ax, ay, h), (ax + 0.8, ay + 0.35, h + 0.65), "plaster", skip="z-")
    # 栏杆
    if rng.random() < 0.5:
        z = h + 1.1
        for p0, p1 in (((x0 + 0.2, y0 + 0.2, z), (x1 - 0.2, y0 + 0.2, z)), ((x1 - 0.2, y0 + 0.2, z), (x1 - 0.2, y1 - 0.2, z)),
                       ((x1 - 0.2, y1 - 0.2, z), (x0 + 0.2, y1 - 0.2, z)), ((x0 + 0.2, y1 - 0.2, z), (x0 + 0.2, y0 + 0.2, z))):
            b.pipe(p0, p1, 0.025, "metal", sides=3, smooth=False)
        for t in range(int(w // 2) + 1):
            x = x0 + 0.2 + t * (w - 0.4) / max(1, int(w // 2))
            b.pipe((x, y0 + 0.2, h), (x, y0 + 0.2, z), 0.02, "metal", sides=3, smooth=False)
    if rng.random() < 0.2:
        ax, ay = rng.uniform(x0 + 1, x1 - 1), rng.uniform(y0 + 1, y1 - 1)
        b.pipe((ax, ay, h), (ax, ay, h + 3.5), 0.025, "metal", sides=3, smooth=False)
        b.pipe((ax - 0.5, ay, h + 3.0), (ax + 0.5, ay, h + 3.0), 0.012, "metal", sides=3, smooth=False)


def _parapet(b, x0, x1, y0, y1, h):
    t = 0.18
    for mn, mx in (((x0, y0, h), (x1, y0 + t, h + 0.45)), ((x0, y1 - t, h), (x1, y1, h + 0.45)),
                   ((x0, y0, h), (x0 + t, y1, h + 0.45)), ((x1 - t, y0, h), (x1, y1, h + 0.45))):
        b.box(mn, mx, "concrete", skip="z-")


def _gable_roof(b, x0, x1, y0, y1, h, key, along_y):
    ov = 0.45
    rise = 0.32 * (min(x1 - x0, y1 - y0))
    if along_y:
        xm = (x0 + x1) / 2
        for ya, yb in ((y0, y1),):
            b.poly([(x0 - ov, ya - ov, h - 0.1), (xm, ya - ov, h + rise), (xm, yb + ov, h + rise), (x0 - ov, yb + ov, h - 0.1)], key, (-1, 0, 1))
            b.poly([(x1 + ov, ya - ov, h - 0.1), (x1 + ov, yb + ov, h - 0.1), (xm, yb + ov, h + rise), (xm, ya - ov, h + rise)], key, (1, 0, 1))
        for y, f in ((y0, -1), (y1, 1)):
            b.poly([(x0, y, h), (x1, y, h), (xm, y, h + rise)], fk(b), (0, f, 0))
    else:
        ym = (y0 + y1) / 2
        b.poly([(x0 - ov, y0 - ov, h - 0.1), (x1 + ov, y0 - ov, h - 0.1), (x1 + ov, ym, h + rise), (x0 - ov, ym, h + rise)], key, (0, -1, 1))
        b.poly([(x1 + ov, y1 + ov, h - 0.1), (x0 - ov, y1 + ov, h - 0.1), (x0 - ov, ym, h + rise), (x1 + ov, ym, h + rise)], key, (0, 1, 1))
        for x, f in ((x0, -1), (x1, 1)):
            b.poly([(x, y0, h), (x, y1, h), (x, ym, h + rise)], fk(b), (f, 0, 0))


def _mansard(b, x0, x1, y0, y1, h, key, rng):
    """191 左侧那种红色折面屋顶, 带老虎窗。"""
    inset, rise = 1.4, 3.4
    p = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    q = [(x0 + inset, y0 + inset), (x1 - inset, y0 + inset), (x1 - inset, y1 - inset), (x0 + inset, y1 - inset)]
    faces = ((0, -1), (1, 0), (0, 1), (-1, 0))
    for i in range(4):
        a, c = p[i], p[(i + 1) % 4]
        d, e = q[i], q[(i + 1) % 4]
        b.poly([(a[0], a[1], h), (c[0], c[1], h), (e[0], e[1], h + rise), (d[0], d[1], h + rise)], key, (faces[i][0], faces[i][1], 0.4))
    b.poly([(q[0][0], q[0][1], h + rise), (q[1][0], q[1][1], h + rise), (q[2][0], q[2][1], h + rise), (q[3][0], q[3][1], h + rise)], "concrete", (0, 0, 1))
    # 南面和东西面的老虎窗
    n = max(1, int((x1 - x0) / 4))
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        b.box((x - 0.55, y0 + 0.2, h + 0.8), (x + 0.55, y0 + 1.1, h + 2.1), "plaster", skip="y+ z-")
        b.poly([(x - 0.4, y0 + 0.195, h + 1.0), (x + 0.4, y0 + 0.195, h + 1.0), (x + 0.4, y0 + 0.195, h + 1.9), (x - 0.4, y0 + 0.195, h + 1.9)], "glass", (0, -1, 0))


def _balconies(b, x0, x1, y0, y1, floors, face, rng):
    """face: 'x+' 'x-' 'y-'。每层一条阳台, 带栏杆和室外机。"""
    depth = 0.95
    for fl in range(1, floors):
        if rng.random() < 0.25:
            continue
        z = fl * FLOOR
        if face == "y-":
            a0, a1 = x0 + 0.5, x1 - 0.5
            b.box((a0, y0 - depth, z), (a1, y0, z + 0.14), "concrete", skip="y+")
            b.box((a0, y0 - depth, z + 0.14), (a1, y0 - depth + 0.04, z + 1.15), "metal", skip="z- y+")
            b.box((a0, y0 - depth + 0.2, z + 0.14), (a0 + 0.7, y0 - depth + 0.5, z + 0.75), "plaster", skip="z-")
        else:
            s = 1 if face == "x+" else -1
            xf = x1 if s > 0 else x0
            a, c = sorted((xf, xf + s * depth))
            y_a, y_b = y0 + 0.5, y1 - 0.5
            b.box((a, y_a, z), (c, y_b, z + 0.14), "concrete")
            rx = xf + s * depth
            ra, rc = sorted((rx, rx - s * 0.04))
            b.box((ra, y_a, z + 0.14), (rc, y_b, z + 1.15), "metal", skip="z-")
            ca, cc = sorted((xf + s * 0.25, xf + s * 0.55))
            b.box((ca, y_a + 0.3, z + 0.14), (cc, y_a + 1.0, z + 0.75), "plaster", skip="z-")


def _street_level(b, x0, x1, y0, y1, face, rng):
    """朝背巷的一层: 店面贴图 + 雨棚 + 竖招牌。"""
    s = 1 if face == "x+" else -1
    xf = (x1 if s > 0 else x0) + s * 0.012
    margin = 0.4
    ya, yb = y0 + margin, y1 - margin
    if y0 < 66 and rng.random() < 0.4:
        # 背巷里亮灯的小店: 实拍货品 + 上方灯带
        row = rng.randrange(8)
        b.poly([(xf, ya, 0.05), (xf, yb, 0.05), (xf, yb, 2.2), (xf, ya, 2.2)], "cedar", (s, 0, 0))
        b.poly([(xf + s * 0.01, ya + 0.1, 0.5), (xf + s * 0.01, yb - 0.1, 0.5), (xf + s * 0.01, yb - 0.1, 1.9), (xf + s * 0.01, ya + 0.1, 1.9)],
               "goods", (s, 0, 0), goods_uv(row, 0.0, (yb - ya) / 11.0))
        xa, xc = sorted((xf, xf + s * 0.12))
        b.box((xa, ya, 2.2), (xc, yb, 2.26), "glow")
    elif y0 < 66:
        # 可步行段会被走近看, 不用贴图假店面: 卷帘门 + 一扇小门
        door = min(yb, ya + 1.0)
        b.poly([(xf, ya, 0.05), (xf, door, 0.05), (xf, door, 2.15), (xf, ya, 2.15)], "cedar", (s, 0, 0))
        if yb - door > 1.2:
            b.poly([(xf, door + 0.2, 0.05), (xf, yb, 0.05), (xf, yb, 2.6), (xf, door + 0.2, 2.6)], "shutter", (s, 0, 0))
            xa, xb = sorted((xf, xf + s * 0.12))
            b.box((xa, door + 0.1, 2.6), (xb, yb + 0.1, 2.95), "metal")
    else:
        uv = rect_uv(K.lod_front(rng.randrange(4)), size=1024.0)
        b.poly([(xf, ya, 0.05), (xf, yb, 0.05), (xf, yb, 2.65), (xf, ya, 2.65)], "citysign", (s, 0, 0), uv)
    if rng.random() < 0.6:
        stripes = rect_uv(K.STRIPES[rng.randrange(2)], size=1024.0)
        out = xf + s * 0.75
        b.poly([(out, ya, 2.5), (out, yb, 2.5), (xf, yb, 3.0), (xf, ya, 3.0)], "props", (s, 0, 1), stripes)
    if rng.random() < 0.8:
        # 竖招牌伸出墙外
        i = rng.randrange(8)
        uv = rect_uv(K.city_sign(i), size=1024.0)
        y = rng.uniform(y0 + 0.4, y1 - 0.4)
        z0 = 3.2
        z1 = z0 + rng.uniform(2.2, 3.4)
        xa, xb = sorted((xf, xf + s * 0.9))
        b.poly([(xa, y, z0), (xb, y, z0), (xb, y, z1), (xa, y, z1)], "citysign", (0, -1, 0), uv)
        b.poly([(xb, y + 0.08, z0), (xa, y + 0.08, z0), (xa, y + 0.08, z1), (xb, y + 0.08, z1)], "citysign", (0, 1, 0), uv)
        b.box((xa, y, z0), (xb, y + 0.08, z0 + 0.02), "metal")
        b.box((xa, y, z1), (xb, y + 0.08, z1 + 0.02), "metal")


def _billboard(b, x0, x1, y0, h, rng):
    w = min(5.5, x1 - x0 - 0.6)
    cx = (x0 + x1) / 2
    y = y0 + 0.7
    uv = rect_uv(K.billboard(rng.randrange(2)), size=1024.0)
    z0, z1 = h + 1.0, h + 1.0 + w * 0.5
    b.poly([(cx - w / 2, y, z0), (cx + w / 2, y, z0), (cx + w / 2, y, z1), (cx - w / 2, y, z1)], "citysign", (0, -1, 0), uv)
    b.box((cx - w / 2, y + 0.01, z0), (cx + w / 2, y + 0.2, z1), "metal", skip="y-")
    for x in (cx - w / 3, cx + w / 3):
        b.pipe((x, y + 0.1, h), (x, y + 0.1, z0), 0.06, "metal", sides=4, smooth=False)


def building(b, x0, x1, y0, y1, floors, rng, street_face=None, roof=None, billboard=False):
    h = floors * FLOOR + 0.4
    roof = roof or rng.choices(("flat", "gable", "gable_red", "mansard"), (0.68, 0.17, 0.1, 0.05))[0]
    if fk(b) == "wall":
        b.poly([(x0, y0, h), (x1, y0, h), (x1, y1, h), (x0, y1, h)], "concrete", (0, 0, 1))
        for o, u, n, length, name in (((x0, y0), (1, 0), (0, -1), x1 - x0, "y-"), ((x1, y0), (0, 1), (1, 0), y1 - y0, "x+"),
                                      ((x1, y1), (-1, 0), (0, 1), x1 - x0, "y+"), ((x0, y1), (0, -1), (-1, 0), y1 - y0, "x-")):
            _window_face(b, o, u, n, length, h, floors, rng, skip_ground=name == street_face)
    else:
        b.box((x0, y0, 0), (x1, y1, h), fk(b), skip="z-")
    if roof == "flat":
        _parapet(b, x0, x1, y0, y1, h)
        _flat_roof_clutter(b, x0, x1, y0, y1, h, rng)
    elif roof == "gable":
        _gable_roof(b, x0, x1, y0, y1, h, "roof", (y1 - y0) > (x1 - x0))
    elif roof == "gable_red":
        _gable_roof(b, x0, x1, y0, y1, h, "roof_red", (y1 - y0) > (x1 - x0))
    else:
        _mansard(b, x0, x1, y0, y1, h, "roof_red", rng)
    # 水平腰线, 打破贴图平铺
    if rng.random() < 0.6:
        z = rng.randint(1, max(1, floors - 1)) * FLOOR
        for mn, mx, sk in (((x0 - 0.05, y0 - 0.05, z), (x1 + 0.05, y0, z + 0.2), "y+"),
                           ((x0 - 0.05, y0, z), (x0, y1, z + 0.2), "x+"), ((x1, y0, z), (x1 + 0.05, y1, z + 0.2), "x-")):
            b.box(mn, mx, "concrete", skip=sk)
    # 外墙的排水管
    b.pipe((x0 + 0.12, y0 - 0.06, 0), (x0 + 0.12, y0 - 0.06, h), 0.04, "metal", sides=4, smooth=False)
    if street_face and floors >= 2:
        if rng.random() < 0.7:
            _balconies(b, x0, x1, y0, y1, floors, street_face, rng)
        _street_level(b, x0, x1, y0, y1, street_face, rng)
    elif floors >= 2 and rng.random() < 0.55:
        _balconies(b, x0, x1, y0, y1, floors, "y-", rng)
    if billboard:
        _billboard(b, x0, x1, y0, h, rng)


def tower(b, cx, cy, hw, hd, h, rng):
    """远景高楼。"""
    b.box((cx - hw, cy - hd, 0), (cx + hw, cy + hd, h), fk(b), skip="z-")
    b.box((cx - hw * 0.6, cy - hd * 0.6, h), (cx + hw * 0.6, cy + hd * 0.6, h + 4.0), "concrete", skip="z-")
    b.pipe((cx, cy, h + 4), (cx, cy, h + 10), 0.15, "metal", sides=4, smooth=False)


def city_rows(seed):
    """生成 (x0, x1, y0, y1, 层数, 朝街面, 附加) 的列表。Y 轴从 -31 到 236。"""
    rng = random.Random(seed)
    lots = []

    def row(xa, xb, face, floors_range, weights, y_start=-31.0, y_end=236.0):
        y = y_start
        while y < y_end:
            d = rng.uniform(5.5, 12.5)
            depth = rng.uniform(0.75, 1.0) * abs(xb - xa)
            if xa < xb:
                x0, x1 = xa, xa + depth
            else:
                x0, x1 = xa - depth, xa
            floors = rng.choices(floors_range, weights)[0]
            lots.append((x0, x1, y, y + d, floors, face))
            y += d + rng.uniform(0.35, 0.9)

    row(-12.4, -21.0, "x+", (2, 3, 4, 5), (3, 5, 4, 2))
    row(-22.0, -36.0, None, (3, 4, 5, 6), (3, 4, 3, 2))
    row(12.4, 21.0, "x-", (2, 3, 4, 5), (3, 5, 4, 2))
    row(22.0, 36.0, None, (3, 4, 5, 6), (3, 4, 3, 2))
    row(-37.0, -55.0, None, (4, 5, 6, 7), (3, 4, 3, 2), y_start=-10.0, y_end=300.0)
    row(37.0, 55.0, None, (4, 5, 6, 7), (3, 4, 3, 2), y_start=-10.0, y_end=300.0)
    return lots


# ---- 门和塔 ----

def curved_hip(b, cx, cy, hw, hd, z0, z1, ridge, lift=0.9, nt=8, ns=4, key="roof"):
    """四坡曲面屋顶: 坡面内凹, 四角上翘, 屋脊沿 X。"""
    base_z = lambda t: z0 + lift * abs(2 * t - 1) ** 4

    def grid(eave, ridge_pts, facing):
        vs = []
        for s_i in range(ns + 1):
            s = s_i / ns
            row = []
            for t_i in range(nt + 1):
                t = t_i / nt
                ex, ey = eave(t)
                rx, ry = ridge_pts(t)
                ez = base_z(t)
                row.append((ex + (rx - ex) * s, ey + (ry - ey) * s, ez + (z1 - ez) * s ** 1.7))
            vs.append(row)
        for s_i in range(ns):
            for t_i in range(nt):
                b.poly([vs[s_i][t_i], vs[s_i][t_i + 1], vs[s_i + 1][t_i + 1], vs[s_i + 1][t_i]], key, facing)
        return vs[0]

    lines = []
    lines.append(grid(lambda t: (cx - hw + 2 * hw * t, cy - hd), lambda t: (cx - ridge + 2 * ridge * t, cy), (0, -1, 1)))
    lines.append(grid(lambda t: (cx + hw - 2 * hw * t, cy + hd), lambda t: (cx + ridge - 2 * ridge * t, cy), (0, 1, 1)))
    lines.append(grid(lambda t: (cx + hw, cy - hd + 2 * hd * t), lambda t: (cx + ridge, cy), (1, 0, 1)))
    lines.append(grid(lambda t: (cx - hw, cy + hd - 2 * hd * t), lambda t: (cx - ridge, cy), (-1, 0, 1)))
    # 檐口: 朱红封檐和受光的檐下
    for line, f in zip(lines, ((0, -1, 0), (0, 1, 0), (1, 0, 0), (-1, 0, 0))):
        for a, c in zip(line, line[1:]):
            b.poly([(a[0], a[1], a[2] - 0.5), (c[0], c[1], c[2] - 0.5), c, a], "lit", f)
    b.poly([(cx - hw, cy - hd, z0 - 0.45), (cx + hw, cy - hd, z0 - 0.45), (cx + hw, cy + hd, z0 - 0.45), (cx - hw, cy + hd, z0 - 0.45)],
           "lit", (0, 0, -1))
    # 屋脊和垂脊
    b.pipe((cx - ridge, cy, z1 + 0.1), (cx + ridge, cy, z1 + 0.1), 0.28, "metal", sides=5)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p0 = (cx + sx * hw, cy + sy * hd, z0 + lift + 0.05)
        p1 = (cx + sx * ridge, cy, z1 + 0.05)
        b.pipe(p0, p1, 0.16, "metal", sides=4, smooth=False)
    if ridge > 1:
        for sx in (-1, 1):
            b.lathe(cx + sx * ridge, cy, [(0.4, z1), (0.5, z1 + 0.5), (0.25, z1 + 1.1), (0.0, z1 + 1.4)], "gold", sides=6)


def brackets(b, cx, cy, hw, hd, z, n=14):
    """檐下斗拱的简化: 一排小方块, 受光。"""
    for i in range(n):
        x = cx - hw + 2 * hw * (i + 0.5) / n
        for y, sk in ((cy - hd - 0.35, "y+"), (cy + hd - 0.05, "y-")):
            b.box((x - 0.28, y, z - 0.75), (x + 0.28, y + 0.4, z - 0.35), "lit", skip=sk + " z+")
    for i in range(max(3, n // 3)):
        y = cy - hd + 2 * hd * (i + 0.5) / max(3, n // 3)
        b.box((cx + hw - 0.05, y - 0.28, z - 0.75), (cx + hw + 0.35, y + 0.28, z - 0.35), "lit", skip="x- z+")
        b.box((cx - hw - 0.35, y - 0.28, z - 0.75), (cx - hw + 0.05, y + 0.28, z - 0.35), "lit", skip="x+ z+")


def railing(b, cx, cy, hw, hd, z):
    b.box((cx - hw, cy - hd - 0.05, z + 0.85), (cx + hw, cy - hd + 0.05, z + 0.95), "lit", skip="y+ z-")
    n = int(hw * 2 / 0.9)
    for i in range(n + 1):
        x = cx - hw + i * 2 * hw / n
        b.box((x - 0.05, cy - hd - 0.05, z), (x + 0.05, cy - hd + 0.05, z + 0.85), "lit", skip="y+ z- z+")


def build_gate():
    """宝藏门替身。真实尺寸 22.7x21x8 米; 檐口出挑按 191 放宽。"""
    b = Builder()
    hw, hd = 10.5, 4.0
    # 一层: 柱列和进深
    b.box((-hw, -hd + 1.4, 0), (hw, hd, 7.1), "vermilion", skip="z-")
    b.poly([(-3.4, -hd + 1.38, 0), (3.4, -hd + 1.38, 0), (3.4, -hd + 1.38, 6.2), (-3.4, -hd + 1.38, 6.2)], "metal", (0, -1, 0))
    for x in (-10.0, -6.2, -2.2, 2.2, 6.2, 10.0):
        b.pipe((x, -hd + 0.2, 0), (x, -hd + 0.2, 7.2), 0.42, "lit", sides=8)
    b.box((-hw, -hd, 6.5), (hw, -hd + 1.5, 7.2), "lit", skip="y+")
    for x, kind in ((-4.2, "metal"), (0.0, "lantern"), (4.2, "metal")):
        r = 1.0 if kind == "lantern" else 0.85
        h0 = 1.9 if kind == "lantern" else 2.5
        b.lathe(x, -hd + 0.2, [(r * 0.5, h0), (r * 0.85, h0 + 0.45), (r, h0 + 1.2), (r * 0.85, h0 + 2.0), (r * 0.5, h0 + 2.4)],
                kind if kind == "lantern" else "gold", sides=12)
    # 一层檐
    curved_hip(b, 0, 0, 16.0, hd + 2.9, 8.0, 10.6, 9.0, lift=0.75)
    brackets(b, 0, 0, hw + 0.6, hd, 8.0, n=18)
    # 二层: 红柱白墙和栏杆
    b.box((-hw + 1.6, -hd + 1.2, 9.6), (hw - 1.6, hd - 1.2, 14.6), "lit", skip="z-")
    for i in range(9):
        x = -hw + 2.3 + i * (2 * hw - 4.6) / 8
        b.box((x - 0.25, -hd + 1.1, 11.0), (x + 0.25, -hd + 1.25, 14.4), "vermilion", skip="y+")
    for i in range(8):
        x0 = -hw + 2.3 + i * (2 * hw - 4.6) / 8 + 0.3
        x1 = -hw + 2.3 + (i + 1) * (2 * hw - 4.6) / 8 - 0.3
        b.poly([(x0, -hd + 1.18, 12.8), (x1, -hd + 1.18, 12.8), (x1, -hd + 1.18, 14.2), (x0, -hd + 1.18, 14.2)], "plaster", (0, -1, 0))
    railing(b, 0, 0, hw - 0.9, hd - 0.2, 10.6)
    b.box((-hw - 0.9 + 1.6, -hd - 0.3, 10.5), (hw + 0.9 - 1.6, -hd + 1.3, 10.65), "lit", skip="z-")
    b.box((-1.2, -hd + 1.05, 12.9), (1.2, -hd + 1.18, 14.3), "gold", skip="y+")
    # 上层檐
    curved_hip(b, 0, 0, hw + 3.5, hd + 2.7, 15.2, 22.7, hw - 3.0, lift=1.0)
    brackets(b, 0, 0, hw - 1.0, hd - 1.0, 15.2, n=16)
    return b


def build_pagoda():
    """五重塔替身, 约 53 米。"""
    b = Builder()
    tiers = [(9.0, 11.0), (15.2, 10.2), (21.0, 9.4), (26.4, 8.6), (31.4, 7.8)]
    for i, (z, w) in enumerate(tiers):
        core = w * 0.46
        z_prev = tiers[i - 1][0] + 1.8 if i else 0.0
        b.box((-core, -core, z_prev), (core, core, z), "lit", skip="z-")
        # 正面柱和白墙
        for k in range(4):
            x = -core + (k + 0.5) * 2 * core / 4
            b.box((x - 0.2, -core - 0.08, z_prev + 0.5), (x + 0.2, -core, z - 0.7), "vermilion", skip="y+")
        if z - z_prev > 3:
            b.poly([(-core + 0.2, -core - 0.03, z - 2.3), (core - 0.2, -core - 0.03, z - 2.3), (core - 0.2, -core - 0.03, z - 1.0), (-core + 0.2, -core - 0.03, z - 1.0)],
                   "plaster", (0, -1, 0))
        if i:
            railing(b, 0, 0, core + 0.4, core + 0.45, z_prev + 0.1)
        curved_hip(b, 0, 0, w, w, z, z + 2.8, 0.1, lift=0.75, nt=6, ns=3)
        brackets(b, 0, 0, core + 0.4, core + 0.4, z, n=9)
    # 相轮
    b.pipe((0, 0, 34.0), (0, 0, 52.2), 0.42, "gold", sides=8, r1=0.1)
    b.lathe(0, 0, [(1.5, 34.0), (1.7, 34.6), (0.7, 36.0), (0.4, 37.0)], "gold", sides=10)
    for i in range(9):
        z = 37.2 + i * 1.25
        r = 1.45 - 0.07 * i
        b.lathe(0, 0, [(0.2, z), (r, z + 0.08), (r, z + 0.25), (0.2, z + 0.34)], "gold", sides=10)
    b.lathe(0, 0, [(0.2, 49.0), (1.0, 49.8), (0.9, 50.8), (0.15, 51.4)], "gold", sides=8)
    b.lathe(0, 0, [(0.1, 52.0), (0.42, 52.4), (0.3, 52.8), (0.0, 53.0)], "gold", sides=8)
    return b


# ---- 人群 ----

SKIN = (0, 1)
PALETTE_SIZE = 8  # 贴图 8x8, 每格一种颜色


def _paint(b, start, cell):
    """把 start 之后新增的面都涂成调色板里的一格。"""
    u = (cell % PALETTE_SIZE + 0.5) / PALETTE_SIZE
    v = 1 - ((cell // PALETTE_SIZE) + 0.5) / PALETTE_SIZE
    for i in range(start, len(b.faces)):
        idx, m, uv, smooth = b.faces[i]
        b.faces[i] = (idx, b.mats["people"], [(u, v)] * len(idx), smooth)


def person(seed):
    """远中景行人: 身形压扁接近真人, 有手, 长发, 裙子, 包。朝 -Y 走。"""
    rng = random.Random(seed)
    b = Builder()
    woman = seed % 2 == 0
    h = rng.uniform(1.52, 1.68) if woman else rng.uniform(1.62, 1.82)
    k = h / 1.7
    coat = rng.choices((8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19), (4, 4, 4, 3, 3, 3, 3, 3, 2, 2, 3, 2))[0]
    pants = rng.choice((20, 21, 22, 23))
    skin = rng.choice(SKIN)
    hair = rng.choice((2, 3, 3, 3, 4))
    step = rng.uniform(0.1, 0.24)
    skirt = woman and rng.random() < 0.4
    long_hair = woman and rng.random() < 0.65
    long_coat = rng.random() < 0.3

    s = len(b.faces)
    for side, phase in ((-1, step), (1, -step)):
        hip = (side * 0.08 * k, 0, 0.86 * k)
        knee = (side * 0.085 * k, phase * 0.55 * k, 0.46 * k + abs(phase) * 0.1)
        foot = (side * 0.09 * k, phase * k, 0.07)
        b.pipe(hip, knee, 0.078 * k, "metal", sides=6, r1=0.058 * k)
        b.pipe(knee, foot, 0.056 * k, "metal", sides=6, r1=0.04 * k)
    _paint(b, s, skin if skirt else pants)
    s = len(b.faces)
    for side, phase in ((-1, step), (1, -step)):
        b.box((side * 0.09 * k - 0.042, phase * k - 0.1, 0), (side * 0.09 * k + 0.042, phase * k + 0.13, 0.075), "metal", skip="z-")
    _paint(b, s, 5)

    s = len(b.faces)
    if skirt:
        b.lathe(0, 0, [(0.26 * k, 0.5 * k), (0.2 * k, 0.8 * k), (0.135 * k, 0.98 * k)], "metal", sides=10)
    elif long_coat:
        b.lathe(0, 0, [(0.22 * k, 0.6 * k), (0.185 * k, 0.9 * k)], "metal", sides=10)
    prof = [(0.165 * k, 0.84 * k), (0.15 * k, 1.0 * k), (0.2 * k, 1.28 * k), (0.215 * k, 1.38 * k), (0.15 * k, 1.44 * k), (0.055 * k, 1.47 * k)]
    b.lathe(0, 0, prof, "metal", sides=10)
    for side, phase in ((-1, -step), (1, step)):
        sh = (side * 0.215 * k, 0, 1.37 * k)
        el = (side * 0.255 * k, phase * 0.45 * k, 1.08 * k)
        wr = (side * 0.26 * k, phase * 0.95 * k + 0.03, 0.84 * k)
        b.pipe(sh, el, 0.052 * k, "metal", sides=6, r1=0.044 * k)
        b.pipe(el, wr, 0.043 * k, "metal", sides=6, r1=0.034 * k)
    _paint(b, s, coat)

    s = len(b.faces)
    for side, phase in ((-1, -step), (1, step)):
        wr = (side * 0.26 * k, phase * 0.95 * k + 0.03, 0.84 * k)
        b.lathe(wr[0], wr[1], [(0.0, wr[2] - 0.09), (0.038, wr[2] - 0.05), (0.034, wr[2]), (0.0, wr[2] + 0.01)], "metal", sides=6)
    b.pipe((0, 0, 1.44 * k), (0, 0, 1.53 * k), 0.046 * k, "metal", sides=6)
    head = [(0.0, 1.5 * k), (0.06 * k, 1.515 * k), (0.09 * k, 1.57 * k), (0.095 * k, 1.63 * k), (0.07 * k, 1.68 * k), (0.0, 1.7 * k)]
    b.lathe(0, 0, head, "metal", sides=10)
    _paint(b, s, skin)

    s = len(b.faces)
    b.lathe(0, 0.02, [(0.094 * k, 1.57 * k), (0.104 * k, 1.63 * k), (0.082 * k, 1.69 * k), (0.0, 1.725 * k)], "metal", sides=10)
    if long_hair:
        b.lathe(0, 0.075 * k, [(0.05 * k, 1.2 * k), (0.095 * k, 1.36 * k), (0.1 * k, 1.56 * k), (0.06 * k, 1.68 * k)], "metal", sides=8)
    _paint(b, s, hair)

    if rng.random() < 0.5:
        s = len(b.faces)
        if rng.random() < 0.5:
            b.box((-0.13 * k, 0.16 * k, 1.0 * k), (0.13 * k, 0.3 * k, 1.38 * k), "metal")
        else:
            sx = rng.choice((-1, 1))
            b.box((sx * 0.27 * k - 0.05, -0.15, 0.5 * k), (sx * 0.27 * k + 0.05, 0.15, 0.8 * k), "metal")
        _paint(b, s, rng.choice((6, 7, 16, 19)))
    if rng.random() < 0.07:
        s = len(b.faces)
        b.lathe(0, 0.01, [(0.14 * k, 1.66 * k), (0.11 * k, 1.7 * k), (0.0, 1.75 * k)], "metal", sides=10)
        _paint(b, s, rng.choice((6, 7, 19)))
    # 人不是圆柱: 前后压扁
    b.verts = [(x, y * 0.72, z) for x, y, z in b.verts]
    return b
