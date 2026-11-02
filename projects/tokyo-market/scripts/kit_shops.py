"""店面积木: 店身 (8 种), 招牌套件 (16 家), 雨棚 (3 种), 山墙端头, 远景 LOD。

三类部件原点相同 (沿街立面底边中点), 宽度相同就能互换:
  YN_shop_X_01          店身: 屋顶, 二层, 立柱横梁, 室内和货品
  YN_sign_NN_w36/w54    招牌: 横板, 吊牌, 暖帘, 灯笼
  YN_awning_T_w36/w54   雨棚: corrugated / cloth / tile
门脸结构没有平视例图, 是推断; 屋顶和前部低屋面按 191/189。
"""
import math

import kit_atlas as K
from kit_core import ATLAS, Builder, TILE, goods_uv, rect_uv, trim_uv

Z_LINTEL = 2.62
Z_TERRACE = 3.2
Z_EAVE = 4.6
Z_RIDGE = 7.3
Y_WALL = 2.0
Y_RIDGE = 4.5
Y_BACK = 7.0
Z_AWNING_OUT = 3.02
Y_AWNING_OUT = -0.7

# 店身: 键, 宽度, 店面类型, 二层样式, 朱红深浅
BODIES = [
    ("A", 3.6, "counter", "lattice", "a"),
    ("B", 5.4, "counter", "plain", "b"),
    ("C", 3.6, "hanging", "plain", "c"),
    ("D", 5.4, "hanging", "lattice", "a"),
    ("E", 3.6, "shelves", "lattice", "b"),
    ("F", 5.4, "shelves", "plain", "c"),
    ("G", 3.6, "table", "plain", "a"),
    ("H", 3.6, "bells", "lattice", "c"),
]


def _front_frame(b, w):
    hw = w / 2
    b.poly([(-hw, 0, 0.005), (hw, 0, 0.005), (hw, Y_WALL, 0.005), (-hw, Y_WALL, 0.005)], "plaster", (0, 0, 1))
    b.box((-hw, -0.08, 0), (hw, 0.06, 0.035), "metal", skip="z- y+")
    for x, facing in ((-hw + 0.18, 1), (hw - 0.18, -1)):
        # 隔墙用深色木板, 再挂两层小货架; 顺着街看时看到的主要就是这面墙
        b.poly([(x, 0.1, 0), (x, Y_WALL, 0), (x, Y_WALL, Z_LINTEL), (x, 0.1, Z_LINTEL)], "cedar", (facing, 0, 0))
        for level, z in enumerate((0.95, 1.55)):
            xa, xb = sorted((x, x + facing * 0.2))
            b.box((xa, 0.4, z - 0.03), (xb, 1.8, z), "cedar", skip="y+ y-")
            xf = x + facing * 0.08
            row = level + (0 if facing > 0 else 3) + int(w)
            b.poly([(xf, 0.4, z), (xf, 1.8, z), (xf, 1.8, z + 0.46), (xf, 0.4, z + 0.46)], "goods", (facing, 0, 0),
                   goods_uv(row, 0.1 * level + 0.3 * (facing > 0), 0.1 * level + 0.3 * (facing > 0) + 1.4 / 2.88))
    # 照片里是细圆红柱, 站在雨棚下靠街一侧, 不是每店两根粗方柱
    b.pipe((-hw + 0.08, -0.52, 0), (-hw + 0.08, -0.52, 2.5), 0.075, "vermilion", sides=10)
    b.lathe(-hw + 0.08, -0.52, [(0.1, 0.0), (0.1, 0.06), (0.078, 0.09)], "metal", sides=10, smooth=False)
    for sx in (-1, 1):
        b.box((sx * hw - 0.03, -0.05, 0), (sx * hw + 0.03, 0.14, 2.62), "metal", skip="z- z+")
    b.box((-hw, -0.13, Z_LINTEL), (hw, 0.16, 3.05), "vermilion", skip="y+")
    b.box((-hw + 0.2, 0.0, 2.4), (hw - 0.2, 0.09, Z_LINTEL), "shutter", skip="y+ z+ x- x+")
    # 横梁上的污渍和柱脚水痕
    b.poly([(-hw, -0.136, 2.62), (hw, -0.136, 2.62), (hw, -0.136, 3.05), (-hw, -0.136, 3.05)], "grime", (0, -1, 0),
           [(0, 0), (w / 3, 0), (w / 3, 1), (0, 1)])
    b.poly([(-hw, Y_WALL, 0), (hw, Y_WALL, 0), (hw, Y_WALL, Z_LINTEL), (-hw, Y_WALL, Z_LINTEL)], "cedar", (0, -1, 0))
    b.poly([(-hw, 0.1, Z_LINTEL), (hw, 0.1, Z_LINTEL), (hw, Y_WALL, Z_LINTEL), (-hw, Y_WALL, Z_LINTEL)],
           "plaster", (0, 0, -1))
    # 吊灯
    xs = (-0.85, 0.85) if w < 4 else (-1.7, 0.0, 1.7)
    for x in xs:
        b.pipe((x, 1.05, 2.38), (x, 1.05, Z_LINTEL), 0.008, "metal", sides=4)
        b.lathe(x, 1.05, [(0.01, 2.2), (0.075, 2.23), (0.09, 2.29), (0.06, 2.35), (0.012, 2.38)], "glow", sides=8)


def _shelves(b, w, levels=(0.62, 1.12, 1.62), seed=0):
    hw = w / 2
    span = hw - 0.3
    for level, z in enumerate(levels):
        b.box((-span, Y_WALL - 0.34, z - 0.035), (span, Y_WALL, z), "cedar", skip="y+")
        gap = min(0.46, levels[level + 1] - z - 0.04) if level + 1 < len(levels) else 0.42
        yp = Y_WALL - 0.17
        u0 = ((seed * 7 + level * 5 + int(w * 10)) % 10) / 10
        b.poly([(-span, yp, z), (span, yp, z), (span, yp, z + gap), (-span, yp, z + gap)], "goods", (0, -1, 0),
               goods_uv(seed + level * 3 + int(w * 10), u0, u0 + 2 * span / (2.88 * gap / 0.36)))
        x = -span + 0.06
        i = seed
        while x < span - 0.34:
            if (i + level) % 4:
                x += 0.28
                i += 1
                continue
            bw = (0.24, 0.34, 0.28, 0.2)[(i + level) % 4]
            h = 0.22 + 0.06 * ((i * 7 + level) % 4)
            tile = (K.GOODS_PACK_WARM, K.GOODS_PACK_COOL)[(i + level) % 2]
            y0 = Y_WALL - 0.28 + 0.03 * ((i * 3) % 3)
            b.box((x, y0, z), (x + bw, y0 + 0.18, z + h), "plaster", skip="y+ z-")
            # 只取货品格里的一小块, 每盒看起来不同
            rx0, ry0, _, _ = K.goods(tile)
            cx = (i * 3 + level) % 4
            cy = (i * 5 + level) % 4
            b.poly([(x + 0.004, y0 - 0.002, z + 0.004), (x + bw - 0.004, y0 - 0.002, z + 0.004),
                    (x + bw - 0.004, y0 - 0.002, z + h - 0.004), (x + 0.004, y0 - 0.002, z + h - 0.004)],
                   "signs", (0, -1, 0), rect_uv((rx0 + cx * 64, ry0 + cy * 64, rx0 + cx * 64 + 64, ry0 + cy * 64 + 64)))
            x += bw + 0.03 + 0.02 * ((i * 11) % 3)
            i += 1
    n = 2 if w < 4 else 3
    for k in range(n + 1):
        x = -span + 2 * span * k / n
        b.box((x - 0.025, Y_WALL - 0.34, 0), (x + 0.025, Y_WALL, levels[-1] + 0.44), "cedar", skip="y+ z-")


def _counter(b, w):
    hw = w / 2
    span = hw - 0.4
    y0, y1, top = 0.34, 0.98, 0.84
    b.box((-span, y0, 0), (span, y1, top), "cedar", skip="z- y+")
    b.box((-span - 0.04, y0 - 0.03, top), (span + 0.04, y1 + 0.03, top + 0.04), "cedar", skip="z-")
    n = int(2 * span / 0.22)
    for i in range(n + 1):
        x = -span + 0.08 + i * (2 * span - 0.16) / n
        b.box((x - 0.016, y0 - 0.03, 0.06), (x + 0.016, y0, top - 0.04), "vermilion", skip="y+ z- z+")
    trays = 3 if w < 4 else 5
    tw = (2 * span - 0.1) / trays
    for i in range(trays):
        x0 = -span + 0.05 + i * tw
        x1 = x0 + tw - 0.06
        z0, z1 = top + 0.05, top + 0.15
        yf, yb = y0 + 0.03, y1 - 0.03
        tile = K.GOODS_SENBEI if i % 2 == 0 else K.GOODS_SWEETS
        b.poly([(x0, yf, z0), (x1, yf, z0), (x1, yb, z1), (x0, yb, z1)], "signs", (0, -0.3, 1), rect_uv(K.goods(tile)))
        b.box((x0 - 0.02, yf - 0.02, top + 0.04), (x1 + 0.02, yf, z0 + 0.04), "cedar", skip="y+ z-")
        for x in (x0 - 0.02, x1):
            b.box((x, yf, top + 0.04), (x + 0.02, yb, z1 + 0.02), "cedar", skip="z-")
    # 收银处的一摞纸袋
    b.box((span - 0.32, 0.82, top + 0.04), (span - 0.1, 0.94, top + 0.17), "plaster", skip="z-")


def _hanging(b, w):
    """手巾、扇子挂在两排横杆上, 中间一张矮桌。"""
    hw = w / 2
    span = hw - 0.34
    tiles = (K.GOODS_CLOTH, K.GOODS_FANS)
    for row, (y, z_top, length) in enumerate(((Y_WALL - 0.06, 2.42, 0.86), (Y_WALL - 0.06, 1.38, 0.8), (1.0, 2.34, 0.7))):
        b.pipe((-span, y - 0.02, z_top + 0.02), (span, y - 0.02, z_top + 0.02), 0.012, "metal", sides=4)
        x = -span + 0.04
        i = row
        while x < span - 0.24:
            cw = 0.2 + 0.05 * ((i * 3) % 3)
            tile = tiles[(i + row) % 2]
            rx0, ry0, rx1, ry1 = K.goods(tile)
            col = (i * 5) % 8
            uv = rect_uv((rx0 + col * 32, ry0, rx0 + col * 32 + 32 * 2, ry1))
            h = length - 0.06 * ((i * 7) % 3)
            b.poly([(x, y, z_top - h), (x + cw, y, z_top - h), (x + cw, y, z_top), (x, y, z_top)], "signs", (0, -1, 0), uv)
            x += cw + 0.02
            i += 1
    tw = min(1.0, span - 0.2)
    for sx in (-1, 1):
        b.box((sx * tw - 0.03, 0.42, 0), (sx * tw + 0.03, 0.48, 0.66), "cedar", skip="z- z+")
        b.box((sx * tw - 0.03, 0.82, 0), (sx * tw + 0.03, 0.88, 0.66), "cedar", skip="z- z+")
    b.box((-tw - 0.05, 0.38, 0.66), (tw + 0.05, 0.92, 0.7), "cedar")
    # 叠好的手巾
    x = -tw + 0.06
    i = 0
    while x < tw - 0.26:
        rx0, ry0, rx1, ry1 = K.goods(K.GOODS_CLOTH)
        col = (i * 3) % 7
        h = 0.05 + 0.03 * (i % 3)
        b.box((x, 0.44, 0.7), (x + 0.26, 0.84, 0.7 + h), "plaster", skip="z-")
        b.poly([(x, 0.44, 0.7 + h + 0.002), (x + 0.26, 0.44, 0.7 + h + 0.002), (x + 0.26, 0.84, 0.7 + h + 0.002),
                (x, 0.84, 0.7 + h + 0.002)], "signs", (0, 0, 1),
               rect_uv((rx0 + col * 32, ry0, rx0 + col * 32 + 32, ry0 + 64)))
        x += 0.3
        i += 1


def _table(b, w):
    """三级阶梯矮台, 摆玩具和手工。"""
    hw = w / 2
    span = hw - 0.36
    for step, (y0, y1, z) in enumerate(((0.3, 0.8, 0.42), (0.8, 1.24, 0.72), (1.24, 1.66, 1.02))):
        b.box((-span, y0, 0), (span, y1, z), "cedar", skip="z- y+ ")
        tile = (K.GOODS_TOYS, K.GOODS_CRAFT, K.GOODS_TOYS)[step]
        b.poly([(-span + 0.03, y0 + 0.03, z + 0.003), (span - 0.03, y0 + 0.03, z + 0.003),
                (span - 0.03, y1 - 0.03, z + 0.003), (-span + 0.03, y1 - 0.03, z + 0.003)], "signs", (0, 0, 1),
               rect_uv(K.goods(tile)))
    # 几个真正有体积的手鞠球
    pts = [(-0.9, 0.55, 0.42), (-0.4, 0.5, 0.42), (0.6, 0.6, 0.42), (-0.2, 1.05, 0.72), (0.85, 1.0, 0.72)]
    for i, (x, y, z) in enumerate(pts):
        if abs(x) > span - 0.1:
            continue
        r = 0.05 + 0.012 * (i % 3)
        prof = [(0.0, z), (r * 0.7, z + r * 0.3), (r, z + r), (r * 0.7, z + r * 1.7), (0.0, z + 2 * r)]
        b.lathe(x, y, prof, "lantern" if i % 2 == 0 else "gold", sides=8)
    _shelves(b, w, levels=(1.5, 1.95), seed=3)


def _bells(b, w):
    """风铃架: 铃是有体积的, 短纸条垂下来。"""
    hw = w / 2
    span = hw - 0.36
    for row, (y, z) in enumerate(((0.5, 2.38), (1.0, 2.2), (1.5, 2.3))):
        b.pipe((-span, y, z + 0.04), (span, y, z + 0.04), 0.012, "metal", sides=4)
        x = -span + 0.1 + 0.05 * row
        i = row
        while x < span - 0.05:
            drop = 0.06 * ((i * 3) % 3)
            zt = z - drop
            b.pipe((x, y, zt), (x, y, z + 0.03), 0.003, "metal", sides=3, smooth=False)
            b.lathe(x, y, [(0.052, zt - 0.09), (0.058, zt - 0.05), (0.04, zt - 0.015), (0.008, zt)], "glass", sides=6)
            tile = K.goods(K.GOODS_CLOTH)
            col = (i * 3) % 7
            b.poly([(x - 0.018, y, zt - 0.3), (x + 0.018, y, zt - 0.3), (x + 0.018, y, zt - 0.09), (x - 0.018, y, zt - 0.09)],
                   "signs", (0, -1, 0), rect_uv((tile[0] + col * 32, tile[1], tile[0] + col * 32 + 16, tile[3])))
            x += 0.2 + 0.03 * (i % 2)
            i += 1
    span2 = span
    b.box((-span2, 0.45, 0), (span2, 1.0, 0.72), "cedar", skip="z- y+")
    b.box((-span2 - 0.03, 0.42, 0.72), (span2 + 0.03, 1.03, 0.76), "cedar", skip="z-")
    # 台上一排盒子
    x = -span2 + 0.06
    i = 0
    while x < span2 - 0.25:
        rx0, ry0, _, _ = K.goods(K.GOODS_PACK_COOL)
        cx, cy = (i * 3) % 4, (i * 5) % 4
        b.box((x, 0.52, 0.76), (x + 0.2, 0.74, 0.92), "plaster", skip="z-")
        b.poly([(x, 0.518, 0.76), (x + 0.2, 0.518, 0.76), (x + 0.2, 0.518, 0.92), (x, 0.518, 0.92)], "signs", (0, -1, 0),
               rect_uv((rx0 + cx * 64, ry0 + cy * 64, rx0 + cx * 64 + 64, ry0 + cy * 64 + 64)))
        x += 0.25
        i += 1
    _shelves(b, w, levels=(1.1, 1.6), seed=5)


def _terrace(b, w):
    hw = w / 2
    z_low, z_high = Z_TERRACE - 0.05, Z_TERRACE + 0.08
    b.poly([(-hw, 0.16, z_low), (hw, 0.16, z_low), (hw, Y_WALL, z_high), (-hw, Y_WALL, z_high)], "corrugated", (0, 0, 1))
    n = int(w / 0.26)
    slat_w = 0.15
    for i in range(n):
        x = -hw + (w / n) * (i + 0.5)
        b.box((x - slat_w / 2, 0.22, z_low + 0.02), (x + slat_w / 2, Y_WALL - 0.45, z_high + 0.02), "metal",
              skip="z- y+ y-")
    # 室外机, 位置避开中间的吊牌
    units = ((hw - 1.05,),) if w < 4 else ((-hw + 0.3,), (hw - 1.05,))
    for (ax0,) in units:
        ax1, ay0, ay1 = ax0 + 0.8, 1.4, 1.72
        b.box((ax0, ay0, 3.3), (ax1, ay1, 3.9), "plaster", skip="z-")
        b.poly([(ax0 + 0.05, ay0 - 0.004, 3.36), (ax1 - 0.05, ay0 - 0.004, 3.36),
                (ax1 - 0.05, ay0 - 0.004, 3.84), (ax0 + 0.05, ay0 - 0.004, 3.84)], "shutter", (0, -1, 0))
        for x in (ax0 + 0.08, ax1 - 0.14):
            b.box((x, ay0 + 0.05, 3.22), (x + 0.06, ay1 - 0.05, 3.3), "metal", skip="z- z+")


def _upper(b, w, style):
    hw = w / 2
    z0 = Z_TERRACE + 0.08
    b.poly([(-hw, Y_WALL, z0), (hw, Y_WALL, z0), (hw, Y_WALL, Z_EAVE), (-hw, Y_WALL, Z_EAVE)], "plaster", (0, -1, 0))
    b.poly([(-hw, Y_WALL - 0.004, 3.5), (hw, Y_WALL - 0.004, 3.5), (hw, Y_WALL - 0.004, Z_EAVE - 0.03),
            (-hw, Y_WALL - 0.004, Z_EAVE - 0.03)], "grime", (0, -1, 0), [(0.2, 0), (0.2 + w / 3, 0), (0.2 + w / 3, 1), (0.2, 1)])
    d = -0.008
    if style == "lattice":
        wx0, wx1, wz0, wz1 = -hw + 0.35, hw - 1.35 if w < 4 else 0.9, 3.52, 4.36
        b.poly([(wx0, Y_WALL + d, wz0), (wx1, Y_WALL + d, wz0), (wx1, Y_WALL + d, wz1), (wx0, Y_WALL + d, wz1)],
               "glass", (0, -1, 0))
        b.box((wx0 - 0.05, Y_WALL - 0.06, wz0 - 0.05), (wx1 + 0.05, Y_WALL, wz0), "cedar", skip="y+")
        b.box((wx0 - 0.05, Y_WALL - 0.06, wz1), (wx1 + 0.05, Y_WALL, wz1 + 0.05), "cedar", skip="y+")
        n = int((wx1 - wx0) / 0.19)
        for i in range(n + 1):
            x = wx0 + i * (wx1 - wx0) / n
            b.box((x - 0.016, Y_WALL - 0.045, wz0), (x + 0.016, Y_WALL, wz1), "cedar", skip="y+ z- z+")
        for z in (wz0 + 0.28, wz0 + 0.56):
            b.box((wx0, Y_WALL - 0.04, z - 0.012), (wx1, Y_WALL, z + 0.012), "cedar", skip="y+ x- x+")
    else:
        # 两扇小窗 + 通风口
        xs = (-hw + 0.5,) if w < 4 else (-hw + 0.5, 0.3)
        for wx0 in xs:
            wx1, wz0, wz1 = wx0 + 0.9, 3.72, 4.28
            b.poly([(wx0, Y_WALL + d, wz0), (wx1, Y_WALL + d, wz0), (wx1, Y_WALL + d, wz1), (wx0, Y_WALL + d, wz1)],
                   "glass", (0, -1, 0))
            for x in (wx0, (wx0 + wx1) / 2, wx1):
                b.box((x - 0.02, Y_WALL - 0.03, wz0), (x + 0.02, Y_WALL, wz1), "metal", skip="y+")
            for z in (wz0, wz1):
                b.box((wx0 - 0.02, Y_WALL - 0.03, z - 0.02), (wx1 + 0.02, Y_WALL, z + 0.02), "metal", skip="y+")
        b.poly([(hw - 0.72, Y_WALL + d, 3.9), (hw - 0.42, Y_WALL + d, 3.9), (hw - 0.42, Y_WALL + d, 4.2),
                (hw - 0.72, Y_WALL + d, 4.2)], "shutter", (0, -1, 0))
    b.pipe((hw - 0.18, Y_WALL - 0.05, z0), (hw - 0.18, Y_WALL - 0.05, Z_EAVE - 0.02), 0.035, "metal")


def _roof(b, w):
    hw = w / 2
    eave_f = Y_WALL - 0.35
    eave_b = Y_BACK + 0.35
    slope_f = math.hypot(Y_RIDGE - eave_f, Z_RIDGE - Z_EAVE)
    slope_b = math.hypot(eave_b - Y_RIDGE, Z_RIDGE - Z_EAVE)
    t = TILE["roof"]
    b.poly([(-hw, eave_f, Z_EAVE), (hw, eave_f, Z_EAVE), (hw, Y_RIDGE, Z_RIDGE), (-hw, Y_RIDGE, Z_RIDGE)], "roof",
           (0, -1, 1), [(-hw / t, 0), (hw / t, 0), (hw / t, slope_f / t), (-hw / t, slope_f / t)])
    b.poly([(hw, eave_b, Z_EAVE), (-hw, eave_b, Z_EAVE), (-hw, Y_RIDGE, Z_RIDGE), (hw, Y_RIDGE, Z_RIDGE)], "roof",
           (0, 1, 1), [(hw / t, 0), (-hw / t, 0), (-hw / t, slope_b / t), (hw / t, slope_b / t)])
    u = w / 3.2
    b.poly([(-hw, eave_f - 0.035, Z_EAVE - 0.03), (hw, eave_f - 0.035, Z_EAVE - 0.03), (hw, eave_f - 0.035, Z_EAVE + 0.1), (-hw, eave_f - 0.035, Z_EAVE + 0.1)],
           "trim", (0, -1, 0), trim_uv((1536, 1664), 0, u * 2))
    b.poly([(hw, eave_b + 0.035, Z_EAVE - 0.03), (-hw, eave_b + 0.035, Z_EAVE - 0.03), (-hw, eave_b + 0.035, Z_EAVE + 0.1), (hw, eave_b + 0.035, Z_EAVE + 0.1)],
           "trim", (0, 1, 0), trim_uv((1536, 1664), 0, u * 2))
    b.box((-hw, Y_RIDGE - 0.12, Z_RIDGE - 0.03), (hw, Y_RIDGE + 0.12, Z_RIDGE + 0.12), "metal", skip="x- x+ z-")
    b.box((-hw, eave_f - 0.03, Z_EAVE - 0.17), (hw, eave_f + 0.02, Z_EAVE + 0.03), "vermilion", skip="x- x+ y+")
    b.pipe((-hw, eave_f - 0.07, Z_EAVE - 0.07), (hw, eave_f - 0.07, Z_EAVE - 0.07), 0.05, "metal")
    b.poly([(-hw, eave_f, Z_EAVE - 0.15), (hw, eave_f, Z_EAVE - 0.15), (hw, Y_WALL, Z_EAVE - 0.03),
            (-hw, Y_WALL, Z_EAVE - 0.03)], "plaster", (0, 0, -1))
    n2 = int(w / 0.4)
    for i in range(n2):
        x = -hw + (w / n2) * (i + 0.5)
        b.box((x - 0.03, eave_f + 0.02, Z_EAVE - 0.17), (x + 0.03, Y_WALL, Z_EAVE - 0.06), "cedar", skip="y+ y- z+")


def _back(b, w, door_left):
    hw = w / 2
    y = Y_BACK
    b.poly([(hw, y, 0), (-hw, y, 0), (-hw, y, 2.9), (hw, y, 2.9)], "plaster", (0, 1, 0))
    b.poly([(hw, y, 2.9), (-hw, y, 2.9), (-hw, y, Z_EAVE), (hw, y, Z_EAVE)], "corrugated", (0, 1, 0))
    b.poly([(hw, y + 0.004, 1.7), (-hw, y + 0.004, 1.7), (-hw, y + 0.004, 2.9), (hw, y + 0.004, 2.9)], "grime", (0, 1, 0),
           [(w / 3, 0), (0, 0), (0, 1), (w / 3, 1)])
    b.box((-hw, y, 2.86), (hw, y + 0.05, 2.94), "metal", skip="x- x+ y-")
    s = -1 if door_left else 1
    dx0, dx1 = sorted((s * (hw - 0.35), s * (hw - 1.25)))
    b.box((dx0, y, 0), (dx1, y + 0.05, 2.1), "cedar", skip="y- z-")
    hx = dx1 - 0.13
    b.box((hx, y + 0.05, 0.95), (hx + 0.06, y + 0.08, 1.05), "metal", skip="y- z-")
    wx0, wx1 = sorted((-s * (hw - 0.4), -s * (hw - 1.3)))
    b.poly([(wx1, y + 0.005, 1.5), (wx0, y + 0.005, 1.5), (wx0, y + 0.005, 2.2), (wx1, y + 0.005, 2.2)], "glass", (0, 1, 0))
    for i in range(4):
        x = wx0 + i * (wx1 - wx0) / 3
        b.box((x - 0.012, y, 1.5), (x + 0.012, y + 0.03, 2.2), "metal", skip="y- z- z+")
    ax = -0.4 if w < 4 else 0.0
    b.box((ax, y, 0.1), (ax + 0.8, y + 0.3, 0.7), "plaster", skip="y-")
    b.poly([(ax + 0.75, y + 0.304, 0.15), (ax + 0.05, y + 0.304, 0.15), (ax + 0.05, y + 0.304, 0.65),
            (ax + 0.75, y + 0.304, 0.65)], "shutter", (0, 1, 0))
    b.pipe((hw - 0.25, y + 0.06, 0), (hw - 0.25, y + 0.06, Z_EAVE), 0.035, "metal")
    eave_b = Y_BACK + 0.35
    b.box((-hw, eave_b - 0.02, Z_EAVE - 0.17), (hw, eave_b + 0.03, Z_EAVE + 0.03), "vermilion", skip="x- x+ y-")
    b.pipe((-hw, eave_b + 0.07, Z_EAVE - 0.07), (hw, eave_b + 0.07, Z_EAVE - 0.07), 0.05, "metal")
    b.poly([(hw, y, Z_EAVE - 0.03), (-hw, y, Z_EAVE - 0.03), (-hw, eave_b, Z_EAVE - 0.15), (hw, eave_b, Z_EAVE - 0.15)],
           "plaster", (0, 0, -1))


def build_body(key, w, storefront, upper):
    b = Builder()
    _front_frame(b, w)
    {"counter": lambda: (_shelves(b, w), _counter(b, w)),
     "shelves": lambda: (_shelves(b, w, levels=(0.34, 0.8, 1.26, 1.72)),),
     "hanging": lambda: _hanging(b, w),
     "table": lambda: _table(b, w),
     "bells": lambda: _bells(b, w)}[storefront]()
    _terrace(b, w)
    _upper(b, w, upper)
    _roof(b, w)
    _back(b, w, door_left=key in "ACEG")
    return b


def _plaque(b, pw):
    """仲见世式吊牌: 垂直于街道, 上有小屋顶, 朝街一端挂白色球灯。参考 191 和平视图。"""
    pz0, pz1 = 3.42, 4.06
    py0, py1 = -0.5, 1.5
    w_u = (0, 1)
    # 牌面: 从 -x 看是 世見仲, 从 +x 看是 仲見世, 和参考图一样从街心向外读
    face_a = [(0.0, 0.5), (1.0, 0.5), (1.0, 1.0), (0.0, 1.0)]
    face_b = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.0, 0.5)]
    b.poly([(pw + 0.055, py0, pz0), (pw + 0.055, py1, pz0), (pw + 0.055, py1, pz1), (pw + 0.055, py0, pz1)], "plaque", (1, 0, 0), face_a)
    b.poly([(pw - 0.055, py1, pz0), (pw - 0.055, py0, pz0), (pw - 0.055, py0, pz1), (pw - 0.055, py1, pz1)], "plaque", (-1, 0, 0), face_b)
    # 深红底边和端板
    b.box((pw - 0.06, py0 - 0.03, pz0 - 0.1), (pw + 0.06, py1 + 0.03, pz0), "vermilion")
    for y in (py0 - 0.03, py1):
        b.box((pw - 0.06, y, pz0), (pw + 0.06, y + 0.03, pz1), "vermilion", skip="z- z+")
    # 小屋顶: 两坡黑顶 + 青绿封檐
    cap_h = 0.13
    for s in (-1, 1):
        b.poly([(pw + s * 0.2, py0 - 0.2, pz1 + 0.02), (pw + s * 0.2, py1 + 0.2, pz1 + 0.02), (pw, py1 + 0.2, pz1 + cap_h), (pw, py0 - 0.2, pz1 + cap_h)],
               "metal", (s, 0, 1))
        b.box(sorted((pw + s * 0.2, pw + s * 0.215)) and (min(pw + s * 0.2, pw + s * 0.215), py0 - 0.2, pz1 - 0.02),
              (max(pw + s * 0.2, pw + s * 0.215), py1 + 0.2, pz1 + 0.03), "bronze", skip="z- z+")
    # 支撑
    for y in (0.0, 1.1):
        b.pipe((pw, y, 3.1), (pw, y, pz0 - 0.08), 0.022, "metal", sides=4, smooth=False)
    # 朝街一端的白色球灯
    gy = py0 - 0.42
    b.pipe((pw, py0 - 0.03, (pz0 + pz1) / 2), (pw, gy + 0.14, (pz0 + pz1) / 2), 0.012, "metal", sides=4, smooth=False)
    zc = (pz0 + pz1) / 2
    r = 0.13
    prof = [(r * math.sin(math.pi * k / 8), zc - r * math.cos(math.pi * k / 8)) for k in range(9)]
    b.lathe(pw, gy, prof, "globe", sides=16)


def build_noren(shop_index, w):
    """暖帘单独一个部件, 关店时可以隐藏。"""
    b = Builder()
    rect = K.noren(shop_index)
    z1, z0 = 2.6, 1.92
    x_start = -1.5
    nx, nz = 10, 3
    m = b.mats["noren"]
    rw = (rect[2] - rect[0]) / 3
    for i in range(3):
        x0 = x_start + i + 0.01
        x1 = x0 + 0.98
        base = len(b.verts)
        for k in range(nz + 1):
            s = k / nz
            for j in range(nx + 1):
                t = j / nx
                fold = 0.012 + 0.03 * (1 - s)
                b.verts.append((x0 + (x1 - x0) * t, -0.055 + fold * math.sin(t * math.pi * 5 + i * 1.7 + shop_index),
                                z0 + (z1 - z0) * s - (0.012 * math.sin(t * 7 + i) if k == 0 else 0)))
        for k in range(nz):
            for j in range(nx):
                a = base + k * (nx + 1) + j
                c = a + nx + 2
                u0 = (rect[0] + rw * (i + j / nx)) / ATLAS
                u1 = (rect[0] + rw * (i + (j + 1) / nx)) / ATLAS
                v0 = 1 - (rect[3] - (rect[3] - rect[1]) * k / nz) / ATLAS
                v1 = 1 - (rect[3] - (rect[3] - rect[1]) * (k + 1) / nz) / ATLAS
                b.faces.append(([a, a + 1, c, c - 1], m, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], True))
    b.pipe((-1.56, -0.055, 2.615), (1.56, -0.055, 2.615), 0.012, "metal", sides=4)
    return b


def build_sign(shop_index, w):
    """招牌套件: 整条街统一的檐板店名带 + 吊牌 + 少量灯笼。"""
    b = Builder()
    hw = w / 2
    # 店名带贴在雨棚外沿, 就是平视图里那条长长的浅色带
    yf = Y_AWNING_OUT - 0.055
    z0, z1 = Z_AWNING_OUT - 0.62, Z_AWNING_OUT - 0.14
    # 店名带向街外鼓出, 分 6 条做出弧面
    uv = rect_uv(K.board(shop_index))
    v0, v1 = uv[0][1], uv[2][1]
    u0, u1 = uv[0][0], uv[1][0]
    rows = 6
    pts = [(yf - 0.1 * math.sin(math.pi * k / rows), z0 + (z1 - z0) * k / rows) for k in range(rows + 1)]
    base = len(b.verts)
    for y, z in pts:
        b.verts.append((-hw, y, z))
        b.verts.append((hw, y, z))
    for k in range(rows):
        a = base + k * 2
        vb, vt = v0 + (v1 - v0) * k / rows, v0 + (v1 - v0) * (k + 1) / rows
        b.faces.append(([a, a + 1, a + 3, a + 2], b.mats["signs"], [(u0, vb), (u1, vb), (u1, vt), (u0, vt)], True))
    _plaque(b, -0.2)

    # 灯笼只留给少数店: 一个或者没有
    lx = hw - 0.6
    for x in {0: (lx,), 1: (), 2: ()}[shop_index % 3]:
        y = -0.42
        b.pipe((x, y, 2.76), (x, y, Z_AWNING_OUT - 0.02), 0.006, "metal", sides=4)
        b.lathe(x, y, [(0.085, 2.34), (0.125, 2.36), (0.158, 2.41), (0.175, 2.48), (0.178, 2.55), (0.165, 2.62),
                       (0.135, 2.68), (0.095, 2.72)], "lantern", sides=14)
        b.lathe(x, y, [(0.0, 2.32), (0.09, 2.32), (0.09, 2.345)], "metal", sides=8, smooth=False)
        b.lathe(x, y, [(0.1, 2.72), (0.1, 2.76), (0.0, 2.76)], "metal", sides=8, smooth=False)
    return b


BULB_Y, BULB_Z = -0.42, 2.3


def bulb_xs(w):
    n = max(2, int(w / 1.2))
    return [-w / 2 + (i + 0.5) * w / n for i in range(n)]


def build_awning(kind, w):
    b = Builder()
    hw = w / 2
    y_out, z_out = Y_AWNING_OUT, Z_AWNING_OUT
    z_in = Z_TERRACE - 0.05
    if kind == "nakamise":
        # 仲见世统一的深雨棚: 黑色顶面, 朱红封边, 下沿一条灯带, 立柱顶上有小灯
        b.poly([(-hw, y_out, z_out), (hw, y_out, z_out), (hw, 0.16, z_in), (-hw, 0.16, z_in)], "metal", (0, 0, 1))
        b.poly([(-hw, y_out, z_out - 0.66), (hw, y_out, z_out - 0.66), (hw, 0.16, z_out - 0.28), (-hw, 0.16, z_out - 0.28)], "plaster", (0, 0, -1))
        b.box((-hw, y_out - 0.05, z_out - 0.72), (hw, y_out, z_out + 0.03), "vermilion", skip="x- x+ y+")
        b.box((-hw, y_out - 0.08, z_out - 0.14), (hw, y_out, z_out + 0.05), "metal", skip="x- x+ y+")
        # 檐下一排裸灯泡和导轨, 不是连续灯带
        b.box((-hw, BULB_Y - 0.02, BULB_Z + 0.16), (hw, BULB_Y + 0.02, BULB_Z + 0.19), "metal", skip="x- x+")
        for x in bulb_xs(w):
            b.pipe((x, BULB_Y, BULB_Z + 0.05), (x, BULB_Y, BULB_Z + 0.16), 0.012, "metal", sides=4, smooth=False)
            r = 0.05
            b.lathe(x, BULB_Y, [(r * math.sin(math.pi * k / 6), BULB_Z - r + r * (1 - math.cos(math.pi * k / 6))) for k in range(7)], "bulb", sides=10)
        # 照片里檐下还有射灯和电线
        for x in (-hw + 0.45, hw - 0.7):
            b.pipe((x, BULB_Y + 0.1, BULB_Z + 0.16), (x, BULB_Y + 0.16, BULB_Z + 0.04), 0.012, "metal", sides=4, smooth=False)
            b.pipe((x, BULB_Y + 0.2, BULB_Z + 0.06), (x, BULB_Y + 0.06, BULB_Z - 0.06), 0.042, "metal", sides=8)
        b.pipe((-hw, BULB_Y + 0.1, BULB_Z + 0.2), (hw, BULB_Y + 0.1, BULB_Z + 0.2), 0.007, "rubber", sides=3, smooth=False)
        # 店名带上方那条彩色小方块
        keys = ("plaster", "bronze", "vermilion", "plaster", "cedar")
        n = max(2, int(w / 0.6))
        for i in range(n):
            x0, x1 = -hw + i * w / n, -hw + (i + 1) * w / n
            b.box((x0, y_out - 0.09, z_out - 0.14), (x1, y_out - 0.08, z_out - 0.03), keys[(i * 3 + int(w)) % 5], skip="y+ x- x+ z- z+")
    elif kind == "corrugated":
        b.poly([(-hw, y_out, z_out), (hw, y_out, z_out), (hw, 0.16, z_in), (-hw, 0.16, z_in)], "corrugated", (0, 0, 1))
        b.poly([(-hw, y_out, z_out - 0.04), (hw, y_out, z_out - 0.04), (hw, 0.16, z_out - 0.01), (-hw, 0.16, z_out - 0.01)],
               "plaster", (0, 0, -1))
        b.box((-hw, y_out - 0.04, z_out - 0.2), (hw, y_out + 0.02, z_out + 0.03), "vermilion", skip="x- x+ y+")
        b.box((-hw, y_out + 0.04, z_out - 0.12), (hw, y_out + 0.1, z_out - 0.06), "glow", skip="x- x+ z+ y+")
    elif kind == "tile":
        # 小瓦檐: 瓦面 + 瓦当 + 木椽
        t = TILE["roof"]
        slope = math.hypot(0.16 - y_out, z_in - z_out)
        b.poly([(-hw, y_out, z_out), (hw, y_out, z_out), (hw, 0.16, z_in), (-hw, 0.16, z_in)], "roof", (0, 0, 1),
               [(-hw / t, 0), (hw / t, 0), (hw / t, slope / t), (-hw / t, slope / t)])
        b.poly([(-hw, y_out, z_out - 0.04), (hw, y_out, z_out - 0.04), (hw, 0.16, z_out - 0.01), (-hw, 0.16, z_out - 0.01)],
               "cedar", (0, 0, -1))
        n = int(w / 0.22)
        for i in range(n):
            x = -hw + (w / n) * (i + 0.5)
            b.box((x - 0.09, y_out - 0.05, z_out - 0.05), (x + 0.09, y_out + 0.02, z_out + 0.05), "metal", skip="z- y+")
        for i in range(int(w / 0.5)):
            x = -hw + 0.5 * (i + 0.5)
            b.box((x - 0.03, y_out + 0.03, z_out - 0.13), (x + 0.03, 0.14, z_out - 0.04), "cedar", skip="z+ y+")
        b.box((-hw, y_out + 0.12, z_out - 0.16), (hw, y_out + 0.18, z_out - 0.1), "glow", skip="x- x+ z+ y+")
    else:
        # 布雨棚: 上下各一条, 前缘垂边。条纹在道具图集里
        stripes = rect_uv(K.STRIPES[0 if w < 4 else 1], size=1024.0)
        nx = int(w / 0.4)
        for i in range(nx):
            x0 = -hw + i * w / nx
            x1 = x0 + w / nx
            y_m = (y_out + 0.16) / 2
            z_m = (z_out + z_in) / 2 - 0.02
            b.poly([(x0, y_out, z_out), (x1, y_out, z_out), (x1, y_m, z_m), (x0, y_m, z_m)], "props", (0, 0, 1), stripes)
            b.poly([(x0, y_m, z_m), (x1, y_m, z_m), (x1, 0.16, z_in), (x0, 0.16, z_in)], "props", (0, 0, 1), stripes)
            b.poly([(x0, y_out, z_out), (x1, y_out, z_out), (x1, y_out - 0.005, z_out - 0.2), (x0, y_out - 0.005, z_out - 0.2)],
                   "props", (0, -1, 0), stripes)
        b.pipe((-hw, y_out, z_out), (hw, y_out, z_out), 0.012, "metal", sides=4)
    for sx in (-1, 1):
        x = sx * (hw - 0.1)
        b.box((x - 0.03, y_out + 0.08, z_out - 0.04), (x + 0.03, 0.0, z_out), "metal", skip="y+ y-")
    return b


def build_end(s):
    """段尾山墙。s=-1 朝 -X, s=+1 朝 +X。宽 0.3 米, 原点在贴着店铺那一面。"""
    b = Builder()
    xf = 0.3 * s  # 山墙外立面
    # 下部墙面
    b.poly([(xf, 0.0, 0), (xf, Y_WALL, 0), (xf, Y_WALL, Z_TERRACE + 0.1), (xf, 0.0, Z_TERRACE + 0.1)], "plaster", (s, 0, 0))
    b.poly([(xf, Y_WALL, 0), (xf, Y_BACK, 0), (xf, Y_BACK, Z_EAVE), (xf, Y_WALL, Z_EAVE)], "plaster", (s, 0, 0))
    a, c = sorted((0.0, xf))
    # 沿街立柱和背面
    b.box((a, -0.15, 0), (c, 0.16, 3.25), "vermilion", skip="z-")
    b.box((a, 0.0, Z_TERRACE - 0.05), (c, Y_WALL, Z_TERRACE + 0.12), "metal", skip="z-")
    b.poly([(0, Y_BACK, 0), (xf, Y_BACK, 0), (xf, Y_BACK, Z_EAVE), (0, Y_BACK, Z_EAVE)], "plaster", (0, 1, 0))
    # 山花: 白墙三角
    x_g = s * 0.62
    eave_f, eave_b = Y_WALL - 0.35, Y_BACK + 0.35
    b.poly([(x_g, eave_f, Z_EAVE), (x_g, eave_b, Z_EAVE), (x_g, Y_RIDGE, Z_RIDGE)], "plaster", (s, 0, 0))
    # 屋顶延伸
    t = TILE["roof"]
    for ya in (eave_f, eave_b):
        slope = math.hypot(Y_RIDGE - ya, Z_RIDGE - Z_EAVE)
        b.poly([(0, ya, Z_EAVE), (s * 0.75, ya, Z_EAVE), (s * 0.75, Y_RIDGE, Z_RIDGE), (0, Y_RIDGE, Z_RIDGE)], "roof",
               (0, -1 if ya < Y_RIDGE else 1, 1), [(0, 0), (0.75 / t, 0), (0.75 / t, slope / t), (0, slope / t)])
        # 檐下封板
        b.poly([(0, ya, Z_EAVE - 0.03), (s * 0.75, ya, Z_EAVE - 0.03), (s * 0.75, Y_RIDGE, Z_RIDGE - 0.03),
                (0, Y_RIDGE, Z_RIDGE - 0.03)], "cedar", (0, 1 if ya < Y_RIDGE else -1, -1))
    a2, c2 = sorted((0.0, s * 0.8))
    b.box((a2, Y_RIDGE - 0.12, Z_RIDGE - 0.03), (c2, Y_RIDGE + 0.12, Z_RIDGE + 0.14), "metal", skip="z-")
    # 朱红破风: 带上翘的弧线, 正面看得到的那条红边
    segs = 7
    h = 0.34
    for ya in (eave_f - 0.25, eave_b + 0.25):
        prev = None
        for i in range(segs + 1):
            u = i / segs
            y = ya + (Y_RIDGE - ya) * u
            z = Z_EAVE + (Z_RIDGE - Z_EAVE) * u + 0.3 * (1 - u) ** 3 - 0.08
            if prev:
                y0, z0 = prev
                xo = s * 0.8
                b.poly([(xo, y0, z0 - h), (xo, y, z - h), (xo, y, z), (xo, y0, z0)], "vermilion", (s, 0, 0))
                b.poly([(xo, y0, z0), (xo, y, z), (s * 0.5, y, z), (s * 0.5, y0, z0)], "metal", (0, 0, 1))
                b.poly([(xo, y0, z0 - h), (xo, y, z - h), (s * 0.5, y, z - h), (s * 0.5, y0, z0 - h)], "vermilion", (0, 0, -1))
            prev = (y, z)
    # 悬鱼
    b.box((x_g + s * 0.1 if s > 0 else x_g - 0.1 + s * 0.08, Y_RIDGE - 0.2, Z_RIDGE - 0.75),
          (x_g + s * 0.18 if s > 0 else x_g - s * 0.02, Y_RIDGE + 0.2, Z_RIDGE - 0.22), "vermilion", skip="z-")
    return b


def _plaque_lod(b):
    x = -0.2
    b.poly([(x + 0.05, -0.5, 3.42), (x + 0.05, 1.5, 3.42), (x + 0.05, 1.5, 4.06), (x + 0.05, -0.5, 4.06)], "plaque", (1, 0, 0),
           [(0.0, 0.5), (1.0, 0.5), (1.0, 1.0), (0.0, 1.0)])
    b.poly([(x - 0.05, 1.5, 3.42), (x - 0.05, -0.5, 3.42), (x - 0.05, -0.5, 4.06), (x - 0.05, 1.5, 4.06)], "plaque", (-1, 0, 0),
           [(0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.0, 0.5)])
    b.poly([(x - 0.2, -0.7, 4.08), (x, -0.7, 4.2), (x, 1.7, 4.2), (x - 0.2, 1.7, 4.08)], "metal", (-1, 0, 1))
    b.poly([(x + 0.2, 1.7, 4.08), (x, 1.7, 4.2), (x, -0.7, 4.2), (x + 0.2, -0.7, 4.08)], "metal", (1, 0, 1))
    b.lathe(x, -0.92, [(0.0, 3.62), (0.1, 3.67), (0.13, 3.74), (0.09, 3.81), (0.0, 3.86)], "globe", sides=6)


def build_closed_shutter(w, art, y=0.04):
    """放下来的彩绘卷帘, 只有早晨才显示。5.4 米的店中间有立柱, 分两扇。"""
    b = Builder()
    hw = w / 2
    col, row = art % 2, (art // 2) % 4
    panels = ((-hw + 0.2, hw - 0.2),) if w < 4 else ((-hw + 0.2, -0.08), (0.08, hw - 0.2))
    for i, (x0, x1) in enumerate(panels):
        a = (art + i) % 8
        col, row = a % 2, a // 2
        b.poly([(x0, y, 0.02), (x1, y, 0.02), (x1, y, 2.62), (x0, y, 2.62)], "shutter_art", (0, -1, 0),
               rect_uv((col * 1024, row * 512, col * 1024 + 1024, row * 512 + 512)))
    return b


def build_plum(w, lite=False):
    """季节花枝: 对照 web_06/web_07, 从屋面长出, 向街心拱, 主枝分叉, 花成团。lite 给远景用。"""
    import random
    rng = random.Random(int(w * 10) + (7 if lite else 0))
    b = Builder()
    hw = w / 2
    branches = 2 if lite else 3
    per_twig = 18 if lite else 58
    for i in range(branches):
        x0 = -hw + (i + 0.5) * w / branches + rng.uniform(-0.2, 0.2)
        reach = rng.uniform(2.4, 3.3)
        rise = rng.uniform(0.5, 1.0)
        drift = rng.uniform(-0.3, 0.3)

        def main_at(t):
            return (x0 + drift * t, 1.5 - reach * t, 3.75 + rise * math.sin(math.pi * min(t * 1.1, 1.0)) - 0.25 * t)

        if not lite:
            for k in range(6):
                b.pipe(main_at(k / 6), main_at((k + 1) / 6), 0.018 * (1 - k / 7) + 0.005, "rubber", sides=3, smooth=False)
        for j in range(7):
            t0 = 0.28 + 0.72 * j / 6
            p0 = main_at(t0)
            side = -1 if j % 2 else 1
            length = rng.uniform(0.3, 0.6)
            tip = (p0[0] + side * length, p0[1] - rng.uniform(0.05, 0.3), p0[2] + rng.uniform(-0.3, 0.1))
            if not lite:
                b.pipe(p0, tip, 0.006, "rubber", sides=3, smooth=False)
            for _ in range(per_twig):
                s = rng.uniform(0, 1)
                spread = 0.075
                cx = p0[0] + (tip[0] - p0[0]) * s + rng.gauss(0, spread)
                cy = p0[1] + (tip[1] - p0[1]) * s + rng.gauss(0, spread)
                cz = p0[2] + (tip[2] - p0[2]) * s + rng.gauss(0, spread)
                r = rng.uniform(0.028, 0.044) * (2.6 if lite else 1.0)
                tilt = rng.uniform(-0.8, 0.8)
                ring = 4 if lite else 5
                b.poly([(cx + r * math.cos(k * 2 * math.pi / ring), cy + r * math.sin(k * 2 * math.pi / ring) * 0.85,
                         cz + r * math.sin(k * 2 * math.pi / ring) * tilt) for k in range(ring)], "blossom")
    return b


def build_lod(shop_index):
    """远景店面: 只保留 191 里从高处看得到的东西, 30 多个三角面。"""
    b = Builder()
    w = 3.6
    hw = w / 2
    b.poly([(-hw, -0.1, 0), (hw, -0.1, 0), (hw, -0.1, 3.0), (-hw, -0.1, 3.0)], "vermilion", (0, -1, 0))
    b.poly([(-hw + 0.2, -0.104, 0.05), (hw - 0.2, -0.104, 0.05), (hw - 0.2, -0.104, 2.7), (-hw + 0.2, -0.104, 2.7)], "citysign", (0, -1, 0),
           rect_uv(K.lod_front(shop_index % 4), size=1024.0))
    b.poly([(-hw, Y_AWNING_OUT, Z_AWNING_OUT), (hw, Y_AWNING_OUT, Z_AWNING_OUT), (hw, Y_WALL, Z_TERRACE + 0.08),
            (-hw, Y_WALL, Z_TERRACE + 0.08)], "corrugated", (0, 0, 1))
    b.box((-hw, Y_AWNING_OUT - 0.04, Z_AWNING_OUT - 0.2), (hw, Y_AWNING_OUT + 0.02, Z_AWNING_OUT), "vermilion", skip="x- x+ y+")
    b.box((-hw, Y_AWNING_OUT + 0.04, Z_AWNING_OUT - 0.12), (hw, Y_AWNING_OUT + 0.1, Z_AWNING_OUT - 0.06), "glow", skip="x- x+ z+ y+")
    b.poly([(-hw, Y_WALL, Z_TERRACE), (hw, Y_WALL, Z_TERRACE), (hw, Y_WALL, Z_EAVE), (-hw, Y_WALL, Z_EAVE)], "plaster", (0, -1, 0))
    eave_f, eave_b = Y_WALL - 0.35, Y_BACK + 0.35
    t = TILE["roof"]
    for ya in (eave_f, eave_b):
        slope = math.hypot(Y_RIDGE - ya, Z_RIDGE - Z_EAVE)
        b.poly([(-hw, ya, Z_EAVE), (hw, ya, Z_EAVE), (hw, Y_RIDGE, Z_RIDGE), (-hw, Y_RIDGE, Z_RIDGE)], "roof",
               (0, -1 if ya < Y_RIDGE else 1, 1), [(-hw / t, 0), (hw / t, 0), (hw / t, slope / t), (-hw / t, slope / t)])
    b.poly([(hw, Y_BACK, 0), (-hw, Y_BACK, 0), (-hw, Y_BACK, Z_EAVE), (hw, Y_BACK, Z_EAVE)], "plaster", (0, 1, 0))
    if shop_index < 4:
        _plaque_lod(b)
    return b
