"""宝藏门和五重塔: 对照 F:\\东京 的 201/193 (门) 和 188/194/190 (塔) 重做。

结构和比例按例图目测, 总尺寸按公开数据 (门 22.7x21x8 米, 塔约 53 米)。
这是用于构图和气氛的还原, 不是文物测绘; 匾额不写字。
"""
import math

from kit_atlas import TRIM_ROWS
from kit_core import Builder, trim_uv

TRIM_METERS = 3.2  # Trim Sheet 水平一格对应的米数


def _dist(a, b):
    return math.dist(a, b)


def eave_line(b, line, facing, inner, z_inner, band=0.62):
    """沿檐口线铺: 瓦当 + 两层椽头 + 椽底。inner(i) 给出同一位置贴墙的点。"""
    u = 0.0
    for i, (a, c) in enumerate(zip(line, line[1:])):
        du = _dist(a, c) / TRIM_METERS
        u0, u1 = u, u + du
        u = u1
        # 瓦当
        b.poly([(a[0], a[1], a[2] - 0.15), (c[0], c[1], c[2] - 0.15), (c[0], c[1], c[2] + 0.02), (a[0], a[1], a[2] + 0.02)], "trim", facing,
               trim_uv(TRIM_ROWS["tile_nose"], u0 * 2, u1 * 2))
        # 椽头
        b.poly([(a[0], a[1], a[2] - 0.15 - band), (c[0], c[1], c[2] - 0.15 - band), (c[0], c[1], c[2] - 0.15), (a[0], a[1], a[2] - 0.15)], "trim", facing,
               trim_uv(TRIM_ROWS["rafter_ends"], u0, u1))
        # 椽底: 由檐口斜向墙里
        ia, ic = inner(i), inner(i + 1)
        b.poly([(a[0], a[1], a[2] - 0.15 - band), (c[0], c[1], c[2] - 0.15 - band), (ic[0], ic[1], z_inner), (ia[0], ia[1], z_inner)], "trim", (0, 0, -1),
               trim_uv(TRIM_ROWS["rafter_under"], u0, u1))


def curved_hip(b, cx, cy, hw, hd, z0, z1, ridge, wall_hw, wall_hd, lift=0.9, nt=10, ns=5, power=1.9, key="roof", z_inner=None):
    """四坡曲面屋顶: 坡面内凹, 四角上翘, 屋脊沿 X。檐口带瓦当和椽子。"""
    z_inner = z0 + 0.5 if z_inner is None else z_inner

    def edge_z(t):
        return z0 + lift * abs(2 * t - 1) ** 3.2

    def slope(eave, ridge_pts, facing, inner):
        rows = []
        for s_i in range(ns + 1):
            s = s_i / ns
            row = []
            for t_i in range(nt + 1):
                t = t_i / nt
                ex, ey = eave(t)
                rx, ry = ridge_pts(t)
                ez = edge_z(t)
                row.append((ex + (rx - ex) * s, ey + (ry - ey) * s, ez + (z1 - ez) * s ** power))
            rows.append(row)
        for s_i in range(ns):
            for t_i in range(nt):
                b.poly([rows[s_i][t_i], rows[s_i][t_i + 1], rows[s_i + 1][t_i + 1], rows[s_i + 1][t_i]], key, (facing[0], facing[1], 1))
        eave_line(b, rows[0], (facing[0], facing[1], 0), lambda i: inner(i / nt), z_inner)
        return rows

    # 前后两坡和两个山面
    def lerp(a, c, t):
        return a + (c - a) * t

    front = slope(lambda t: (cx - hw + 2 * hw * t, cy - hd), lambda t: (cx - ridge + 2 * ridge * t, cy), (0, -1),
                  lambda t: (cx + lerp(-wall_hw, wall_hw, t), cy - wall_hd))
    back = slope(lambda t: (cx + hw - 2 * hw * t, cy + hd), lambda t: (cx + ridge - 2 * ridge * t, cy), (0, 1),
                 lambda t: (cx + lerp(wall_hw, -wall_hw, t), cy + wall_hd))
    right = slope(lambda t: (cx + hw, cy - hd + 2 * hd * t), lambda t: (cx + ridge, cy), (1, 0),
                  lambda t: (cx + wall_hw, cy + lerp(-wall_hd, wall_hd, t)))
    left = slope(lambda t: (cx - hw, cy + hd - 2 * hd * t), lambda t: (cx - ridge, cy), (-1, 0),
                 lambda t: (cx - wall_hw, cy + lerp(wall_hd, -wall_hd, t)))

    # 屋脊
    if ridge > 0.5:
        b.pipe((cx - ridge, cy, z1 + 0.12), (cx + ridge, cy, z1 + 0.12), 0.3, "metal", sides=6)
    # 垂脊: 跟着曲面走, 角上加一个翘起的鬼瓦
    for rows, idx in ((front, 0), (front, -1), (back, 0), (back, -1)):
        prev = None
        for row in rows:
            p = row[idx]
            cur = (p[0], p[1], p[2] + 0.1)
            if prev:
                b.pipe(prev, cur, 0.17, "metal", sides=5, smooth=False)
            prev = cur
        tip = rows[0][idx]
        b.lathe(tip[0], tip[1], [(0.34, tip[2]), (0.3, tip[2] + 0.28), (0.14, tip[2] + 0.5), (0.0, tip[2] + 0.62)], "metal", sides=6)
    return [front[0], back[0], right[0], left[0]]


def trim_wall(b, cx, cy, hw, hd, z0, z1, row, sub=(0.0, 1.0)):
    """四面贴 Trim 的墙带。"""
    w_u = 2 * hw / TRIM_METERS
    d_u = 2 * hd / TRIM_METERS
    r = TRIM_ROWS[row]
    b.poly([(cx - hw, cy - hd, z0), (cx + hw, cy - hd, z0), (cx + hw, cy - hd, z1), (cx - hw, cy - hd, z1)], "trim", (0, -1, 0), trim_uv(r, 0, w_u, *sub))
    b.poly([(cx + hw, cy + hd, z0), (cx - hw, cy + hd, z0), (cx - hw, cy + hd, z1), (cx + hw, cy + hd, z1)], "trim", (0, 1, 0), trim_uv(r, 0, w_u, *sub))
    b.poly([(cx + hw, cy - hd, z0), (cx + hw, cy + hd, z0), (cx + hw, cy + hd, z1), (cx + hw, cy - hd, z1)], "trim", (1, 0, 0), trim_uv(r, 0, d_u, *sub))
    b.poly([(cx - hw, cy + hd, z0), (cx - hw, cy - hd, z0), (cx - hw, cy - hd, z1), (cx - hw, cy + hd, z1)], "trim", (-1, 0, 0), trim_uv(r, 0, d_u, *sub))


def beam_brackets(b, cx, cy, hw, hd, z, per_side=5, depth=1.3):
    """伸向檐外的挑枋: 真实几何, 白色端头, 201 和 188 里最显眼。"""
    for i in range(per_side):
        x = cx - hw + 2 * hw * (i + 0.5) / per_side
        for s in (-1, 1):
            y0, y1 = sorted((cy + s * hd, cy + s * (hd + depth)))
            b.box((x - 0.2, y0, z - 0.72), (x + 0.2, y1, z - 0.4), "vermilion", skip="z+")
            yf = cy + s * (hd + depth)
            a, c = sorted((yf, yf + s * 0.03))
            b.box((x - 0.2, a, z - 0.72), (x + 0.2, c, z - 0.4), "plaster", skip="z- z+")
    n = max(2, int(per_side * hd / hw))
    for i in range(n):
        y = cy - hd + 2 * hd * (i + 0.5) / n
        for s in (-1, 1):
            x0, x1 = sorted((cx + s * hw, cx + s * (hw + depth)))
            b.box((x0, y - 0.2, z - 0.72), (x1, y + 0.2, z - 0.4), "vermilion", skip="z+")


def column(b, x, y, z0, z1, r=0.42):
    b.pipe((x, y, z0), (x, y, z1), r, "vermilion", sides=12)
    b.lathe(x, y, [(r * 1.4, z0), (r * 1.4, z0 + 0.25), (r * 1.08, z0 + 0.32)], "concrete", sides=12, smooth=False)
    # 201 里柱头的白色铁箍
    b.lathe(x, y, [(r * 1.04, z1 - 0.95), (r * 1.04, z1 - 0.6)], "plaster", sides=12, smooth=False)


def giant_lantern(b, x, y, z_top, r, h, kind):
    """kind='black' 是两侧黑金灯笼, 'red' 是中间大红灯笼。匾和灯笼都不写字。"""
    mid = "metal" if kind == "black" else "lantern"
    prof = [(r * 0.62, z_top - h), (r * 0.86, z_top - h * 0.86), (r, z_top - h * 0.64), (r * 1.03, z_top - h * 0.5),
            (r, z_top - h * 0.36), (r * 0.86, z_top - h * 0.14), (r * 0.62, z_top)]
    b.lathe(x, y, prof, mid, sides=16)
    for z, rr in ((z_top, 0.68), (z_top - h, 0.68)):
        b.lathe(x, y, [(r * rr, z - 0.16), (r * (rr + 0.05), z - 0.08), (r * (rr + 0.05), z + 0.08), (r * rr, z + 0.16)], "gold", sides=16, smooth=False)
    if kind == "black":
        # 金色肋线
        for i in range(8):
            a = 2 * math.pi * i / 8
            pts = [(x + (pr + 0.012) * math.cos(a), y + (pr + 0.012) * math.sin(a), pz) for pr, pz in prof]
            for p0, p1 in zip(pts, pts[1:]):
                b.pipe(p0, p1, 0.022, "gold", sides=3, smooth=False)
    b.pipe((x, y, z_top + 0.16), (x, y, z_top + 0.9), 0.05, "metal", sides=4, smooth=False)


def build_gate():
    b = Builder()
    hw, hd = 10.5, 4.0
    fy = -hd  # 正面柱线
    # 一层: 三开间。柱 + 中间门洞 + 两侧金刚力士间
    xs = (-9.7, -3.4, 3.4, 9.7)
    for x in xs:
        column(b, x, fy, 0, 7.6)
        column(b, x, hd, 0, 7.6)
    # 门洞里的暗墙和天花, 退后 3 米
    b.poly([(-3.2, fy + 3.0, 0), (3.2, fy + 3.0, 0), (3.2, fy + 3.0, 6.6), (-3.2, fy + 3.0, 6.6)], "metal", (0, -1, 0))
    b.poly([(-3.2, fy, 6.6), (3.2, fy, 6.6), (3.2, fy + 3.0, 6.6), (-3.2, fy + 3.0, 6.6)], "vermilion", (0, 0, -1))
    for s in (-1, 1):
        b.poly([(s * 3.2, fy, 0), (s * 3.2, fy + 3.0, 0), (s * 3.2, fy + 3.0, 6.6), (s * 3.2, fy, 6.6)], "vermilion", (-s, 0, 0))
        # 两侧间: 退进去的暗色金属网, 上面一条青绿连子窗, 下面矮栅
        xa, xc = sorted((s * 3.8, s * 9.3))
        yb = fy + 0.5
        b.poly([(xa, yb, 0.5), (xc, yb, 0.5), (xc, yb, 4.9), (xa, yb, 4.9)], "metal", (0, -1, 0))
        width = (xc - xa) / TRIM_METERS
        b.poly([(xa, yb - 0.02, 5.1), (xc, yb - 0.02, 5.1), (xc, yb - 0.02, 5.85), (xa, yb - 0.02, 5.85)], "trim", (0, -1, 0),
               trim_uv(TRIM_ROWS["lattice"], 0, width))
        b.box((xa, yb - 0.1, 4.9), (xc, yb, 5.1), "vermilion", skip="y+")
        b.box((xa, yb - 0.1, 5.85), (xc, yb, 6.15), "vermilion", skip="y+")
        b.box((xa, yb - 0.12, 0), (xc, yb, 0.5), "vermilion", skip="y+ z-")
    # 后侧和两端的墙, 只是把体量封起来
    b.poly([(hw, hd, 0), (-hw, hd, 0), (-hw, hd, 6.2), (hw, hd, 6.2)], "vermilion", (0, 1, 0))
    for s in (-1, 1):
        b.poly([(s * hw, fy, 0), (s * hw, hd, 0), (s * hw, hd, 6.2), (s * hw, fy, 6.2)], "vermilion", (s, 0, 0))
    # 额枋和斗拱墙
    trim_wall(b, 0, 0, hw, hd + 0.12, 6.15, 6.9, "beam")
    trim_wall(b, 0, 0, hw, hd + 0.08, 6.9, 8.0, "bracket_wall")
    beam_brackets(b, 0, 0, hw - 0.2, hd + 0.1, 8.05, per_side=7, depth=1.5)
    # 灯笼: 两侧黑金 + 中间红
    giant_lantern(b, -2.15, fy + 0.2, 6.15, 1.0, 3.5, "black")
    giant_lantern(b, 2.15, fy + 0.2, 6.15, 1.0, 3.5, "black")
    giant_lantern(b, 0.0, fy + 1.9, 6.35, 1.28, 3.9, "red")

    # 一层檐: 出挑很深, 坡度平缓, 两端长出墙外
    curved_hip(b, 0, 0, 15.2, hd + 3.9, 8.45, 10.75, 9.2, hw, hd, lift=0.72, z_inner=8.15)

    # 二层
    uw, ud = hw - 1.5, hd - 0.9
    b.box((-uw - 1.3, -ud - 1.2, 10.55), (uw + 1.3, ud + 1.2, 10.75), "vermilion", skip="z-")
    trim_wall(b, 0, 0, uw + 1.1, ud + 1.0, 10.75, 11.75, "railing")
    trim_wall(b, 0, 0, uw, ud, 10.75, 13.0, "bracket_wall", sub=(0.0, 0.42))
    trim_wall(b, 0, 0, uw, ud, 13.0, 15.15, "bracket_wall", sub=(0.0, 1.0))
    # 匾: 金框青底, 不写字
    b.box((-1.05, -ud - 0.2, 12.85), (1.05, -ud, 15.0), "gold", skip="y+")
    b.poly([(-0.86, -ud - 0.205, 13.02), (0.86, -ud - 0.205, 13.02), (0.86, -ud - 0.205, 14.83), (-0.86, -ud - 0.205, 14.83)], "leaf", (0, -1, 0))
    beam_brackets(b, 0, 0, uw - 0.2, ud + 0.05, 15.2, per_side=7, depth=1.8)
    # 上层檐
    curved_hip(b, 0, 0, 14.8, ud + 3.9, 15.65, 22.5, 8.6, uw, ud, lift=1.05, z_inner=15.45)
    # 歇山: 屋脊两端的三角山面和封檐板 (对照 web_04/web_05)
    gx, gz, gy = 11.2, 18.3, ud + 1.9
    for s in (-1, 1):
        x = s * gx
        b.poly([(x, -gy, gz), (x, gy, gz), (x, 0, 22.5)], "vermilion", (s, 0, 0))
        b.pipe((s * 8.6, 0, 22.62), (x, 0, 22.62), 0.3, "metal", sides=6)
        for sy in (-1, 1):
            b.pipe((x + s * 0.1, sy * gy, gz - 0.1), (x + s * 0.1, 0, 22.62), 0.17, "metal", sides=4, smooth=False)
            b.poly([(s * 8.6, sy * (gy + 0.3), gz + 0.6), (x, sy * (gy + 0.3), gz - 0.1), (x, 0, 22.56), (s * 8.6, 0, 22.56)], "roof", (0, sy, 1))
    # 鸱尾
    for s in (-1, 1):
        x = s * 8.6
        b.lathe(x, 0, [(0.5, 22.5), (0.62, 23.0), (0.42, 23.6), (0.0, 24.0)], "gold", sides=8)
    return b


def build_pagoda():
    b = Builder()
    # (檐口高, 檐半宽, 塔身半宽): 下大上小, 188 里收分不大
    tiers = [(10.5, 11.2, 5.0), (16.4, 10.4, 4.6), (21.9, 9.7, 4.25), (27.1, 9.0, 3.9), (32.0, 8.3, 3.55)]
    # 底层裳阶 (188 里一层下面那圈小屋檐)
    b.box((-6.2, -6.2, 0), (6.2, 6.2, 3.8), "vermilion", skip="z-")
    trim_wall(b, 0, 0, 6.25, 6.25, 0.6, 3.1, "lattice")
    curved_hip(b, 0, 0, 8.6, 8.6, 4.6, 6.6, 0.1, 6.2, 6.2, lift=0.5, nt=6, ns=3, z_inner=4.4)
    prev_top = 3.8
    for i, (z, w, core) in enumerate(tiers):
        # 塔身: 下半是红柱和白壁
        base = prev_top
        trim_wall(b, 0, 0, core, core, base, z - 2.2, "beam" if z - 2.2 - base < 1.2 else "bracket_wall", sub=(0.0, 0.42))
        trim_wall(b, 0, 0, core, core, z - 2.2, z - 0.05, "bracket_wall")
        beam_brackets(b, 0, 0, core - 0.1, core, z, per_side=3, depth=1.6)
        lines = curved_hip(b, 0, 0, w, w, z + 0.2, z + 3.0, 0.1, core, core, lift=1.0, nt=8, ns=4, power=2.2, z_inner=z)
        # 栏杆: 188 里下面两层有明显的朱红栏杆
        if i < 4:
            rail = tiers[i + 1][2] + 0.75
            rz = z + 2.3
            b.box((-rail, -rail, rz - 0.15), (rail, rail, rz), "vermilion", skip="z-")
            trim_wall(b, 0, 0, rail, rail, rz, rz + 0.95, "railing")
        # 角上的风铎
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = sx * (w - 0.1), sy * (w - 0.1)
                bz = z + 0.2 + 1.0 - 0.8
                b.pipe((x, y, bz), (x, y, bz - 0.5), 0.012, "metal", sides=3, smooth=False)
                b.lathe(x, y, [(0.2, bz - 1.05), (0.18, bz - 0.8), (0.1, bz - 0.55), (0.0, bz - 0.48)], "bronze", sides=6)
        prev_top = z + 2.7
    # 相轮: 188 的金色粗环和水烟
    z = tiers[-1][0] + 3.0
    b.lathe(0, 0, [(2.1, z - 0.2), (2.0, z + 0.2), (1.0, z + 0.45), (0.9, z + 1.2)], "metal", sides=12, smooth=False)
    b.lathe(0, 0, [(1.0, z + 1.2), (1.5, z + 1.45), (1.65, z + 1.9), (1.35, z + 2.5), (0.5, z + 2.9)], "gold", sides=14)
    b.pipe((0, 0, z + 2.8), (0, 0, 52.6), 0.3, "gold", sides=10, r1=0.09)
    rings_start = z + 3.3
    n = 9
    rings_top = 47.5
    for i in range(n):
        zr = rings_start + i * (rings_top - rings_start) / (n - 1)
        r = 1.5 - 0.07 * i
        b.lathe(0, 0, [(r * 0.86, zr - 0.24), (r, zr - 0.13), (r, zr + 0.13), (r * 0.86, zr + 0.24)], "gold", sides=14)
        # 环上的小风铃
        for a in range(4):
            ang = a * math.pi / 2 + i * 0.3
            bx, by = r * math.cos(ang), r * math.sin(ang)
            b.lathe(bx, by, [(0.09, zr - 0.5), (0.06, zr - 0.3), (0.0, zr - 0.2)], "gold", sides=4, smooth=False)
    # 水烟: 8 片火焰形
    fz = 48.0
    for i in range(8):
        a = i * math.pi / 4
        dx, dy = math.cos(a), math.sin(a)
        p = [(0.15 * dx, 0.15 * dy, fz), (1.25 * dx, 1.25 * dy, fz + 0.5), (1.4 * dx, 1.4 * dy, fz + 1.9), (0.95 * dx, 0.95 * dy, fz + 3.0), (0.15 * dx, 0.15 * dy, fz + 3.4)]
        b.poly(p, "gold", (-dy, dx, 0))
    b.lathe(0, 0, [(0.15, 51.2), (0.55, 51.6), (0.5, 52.1), (0.14, 52.4)], "gold", sides=10)
    b.lathe(0, 0, [(0.12, 52.3), (0.34, 52.6), (0.3, 52.9), (0.0, 53.0)], "gold", sides=10)
    return b
