# 《此间》样板 r5 扩展：按实拍重做的部件。
# 参考：Wikimedia Commons 的夕焼けだんだん、东京电杆、井盖实拍，来源见 asset-register.csv。
# 店面归 4060，这里的楼房只作背景。
import bpy, math, os
import numpy as np
from mathutils import Vector


def rail_points(y0, y1, z0, z1, x, n=1):
    return [(x, y0 + (y1 - y0) * i / n, z0 + (z1 - z0) * i / n) for i in range(n + 1)]


def spline(pts, n=8):
    """Catmull-Rom 插值，让引线和盘线有自然弧度。"""
    P = [Vector(p) for p in pts]
    P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        a, b, c, d = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(.5 * ((2 * b) + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3))
    out.append(P[-2])
    return out


def build_all(E, ytop, ztop, tread, rise, Y0, Z0, n_steps):
    bbox, mesh, merge_mesh, tube, lathe, bx, box_uv, catenary, rng, scene, build_pole = (
        E['bbox'], E['mesh'], E['merge_mesh'], E['tube'], E['lathe'], E['bx'], E['box_uv'], E['catenary'],
        E['rng'], E['scene'], E['build_pole'])
    MATS = E['MATS']

    def sh(y):
        return Z0 + max(0, min((y - Y0) / tread, n_steps)) * rise

    # ---------- 台阶前的红砖铺地和横向排水格栅 ----------
    bbox('pavers', (-2.6, .36, -.12), (2.6, Y0 + .02, .012), 'pavers', .004, 1, off=(0, 0))
    E['build_grate']('drain_x', -2.5, 2.5, .08, .34, .006)
    bbox('drain_curb_a', (-2.6, .02, -.12), (2.6, .08, .012), 'cover', .006, 1)

    # ---------- 红砖花坛：沿台阶分段抬升 ----------
    SEGS = n_steps // 3

    def planter(side, x0, x1):
        segs = SEGS
        L = n_steps * tread / segs
        for j in range(segs):
            y0 = Y0 + j * L - (.25 if j == 0 else 0)
            y1 = Y0 + (j + 1) * L
            base = sh(y0) - .15 if j else -.15
            top = sh(y1) + .42
            bbox(f'pl_{side}_front{j}', (x0, y0, base), (x0 + .11, y1 + .005, top), 'brick', .005, 1)
            bbox(f'pl_{side}_soil{j}', (x0 + .11, y0, base), (x1, y1, top - .07), 'soil', 0)
            bbox(f'pl_{side}_end{j}', (x0, y1 - .11, base), (x1, y1, top + (.0 if j < segs - 1 else 0)), 'brick', .005, 1) if j < segs - 1 else None
        bbox(f'pl_{side}_head', (x0, Y0 - .36, -.15), (x1, Y0 - .25, sh(Y0 + L) + .42), 'brick', .005, 1)
        return segs, L

    planter('L', -3.0, -2.4)
    # 左右镜像：右侧靠路这边是 x 小的一面
    segs = SEGS
    L = n_steps * tread / segs
    for j in range(segs):
        y0 = Y0 + j * L - (.25 if j == 0 else 0)
        y1 = Y0 + (j + 1) * L
        base = sh(y0) - .15 if j else -.15
        top = sh(y1) + .42
        bbox(f'pl_R_front{j}', (2.6, y0, base), (2.71, y1 + .005, top), 'brick', .005, 1)
        bbox(f'pl_R_soil{j}', (2.71, y0, base), (3.5, y1, top - .07), 'soil', 0)
    bbox('pl_R_head', (2.6, Y0 - .36, -.15), (3.5, Y0 - .25, sh(Y0 + L) + .42), 'brick', .005, 1)
    # 花坛外的抬高地面，挡住楼基
    def ramp(name, x0, x1, y0, y1, n=14):
        ys = np.linspace(y0, y1, n + 1)
        v = []
        for y in ys:
            z = sh(float(y)) + .32
            v += [(x0, float(y), z), (x1, float(y), z)]
        f = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(n)]
        o = mesh(name, v, f, 'soil')
        box_uv(o.data)

    ramp('side_fill_L', -3.5, -2.9, 1.0, ytop + 1)
    ramp('side_fill_R', 3.4, 4.8, 1.0, ytop + 1)

    # ---------- 扶手：绿漆立柱、棕色上管，端部下弯 ----------
    def handrail(name, x, y0, y1):
        posts = []
        n = int((y1 - y0) / 1.25)
        for i in range(n + 1):
            y = y0 + (y1 - y0) * i / n
            z = sh(y)
            posts.append(tube('p', [(x, y, z - .02), (x, y, z + .88)], .021, 8, '', cap=True)[:2])
            posts.append(tube('p', [(x, y, z + .46), (x, min(y + (y1 - y0) / n, y1), sh(min(y + (y1 - y0) / n, y1)) + .46)], .013, 6, '')[:2] if i < n else ([], []))
        p = merge_mesh(name + '_posts', [q for q in posts if q[0]], 'rail_green', 60)
        box_uv(p.data, (float(x) * 3, 0))
        pts = [(x, y0 - .22, sh(y0) + .02), (x, y0 - .2, sh(y0) + .72), (x, y0 - .12, sh(y0) + .88)]
        ys = np.linspace(y0, y1, 8)
        pts += [(x, float(y), sh(float(y)) + .9) for y in ys]
        pts += [(x, y1 + .25, sh(y1) + .9), (x, y1 + .34, sh(y1) + .82), (x, y1 + .36, sh(y1) + .05)]
        tp = merge_mesh(name + '_top', [tube('t', spline(pts, 5), .027, 12, '')[:2]], 'rail_top', 50)
        box_uv(tp.data, (0, float(x)))

    y_end = Y0 + n_steps * tread
    handrail('rail_c', .1, Y0 + .1, y_end - .1)
    handrail('rail_l', -2.3, Y0 + .1, y_end - .1)
    handrail('rail_r', 2.5, Y0 + .1, y_end - .1)

    # ---------- 背景楼房 ----------
    def apartment(name, x, y0, y1, floors, zb):
        fh = 2.85
        xb = x + 1.15
        H = floors * fh
        bbox(name + '_body', (xb, y0, zb), (xb + 9, y1, zb + H + .9), 'apt', .01, 1)
        bbox(name + '_para', (xb - .02, y0 - .03, zb + H + .9), (xb + 9.03, y1 + .03, zb + H + 1.05), 'apt', .012, 1)
        bays = int((y1 - y0) / 3.6)
        bw = (y1 - y0) / bays
        for f in range(floors):
            z = zb + f * fh
            bbox(f'{name}_slab{f}', (x, y0, z + fh - .16), (xb, y1, z + fh), 'apt', .012, 1)
            if f:
                pass
            for b in range(bays):
                yy = y0 + b * bw
                # 磨砂栏板 + 钢扶手
                bbox(f'{name}_p{f}_{b}', (x + .02, yy + .1, z + .08), (x + .08, yy + bw - .1, z + 1.08), 'apt2', .008, 1)
                bbox(f'{name}_r{f}_{b}', (x, yy + .08, z + 1.08), (x + .1, yy + bw - .08, z + 1.13), 'steel', .004, 1)
                # 落地窗和窗框
                bbox(f'{name}_g{f}_{b}', (xb - .03, yy + .35, z + .08), (xb + .01, yy + bw - .35, z + 2.35), 'glass_warm' if rng.random() < .16 else 'glass', 0)
                bbox(f'{name}_fv{f}_{b}', (xb - .05, yy + bw / 2 - .025, z + .08), (xb, yy + bw / 2 + .025, z + 2.35), 'steel', 0)
                bbox(f'{name}_ft{f}_{b}', (xb - .05, yy + .35, z + 2.3), (xb, yy + bw - .35, z + 2.35), 'steel', 0)
                # 室外机
                bbox(f'{name}_ac{f}_{b}', (xb - .36, yy + bw - .75, z + .05), (xb - .08, yy + bw - .1, z + .6), 'ac', .012, 1)
            bbox(f'{name}_wall{f}', (x + .1, y0, z), (xb, y0 + .12, z + fh), 'apt', .006, 1)
        for b in range(bays + 1):
            yy = y0 + b * bw
            bbox(f'{name}_fin{b}', (x + .05, yy - .05, zb), (xb, yy + .05, zb + H), 'apt', .008, 1)
        # 雨水管
        pipes = [tube('p', [(xb - .08, y0 + .2, zb), (xb - .08, y0 + .2, zb + H)], .045, 10, '', cap=True)[:2]]
        pp = merge_mesh(name + '_pipe', pipes, 'pipe', 60)
        box_uv(pp.data)

    def jhouse(name, xf, y0, y1, h, depth, side, zb=0.0, wall='plaster'):
        """两层日式住宅：灰瓦双坡顶，挑檐，木百叶，side=+1 表示朝 -x。"""
        x0, x1 = (xf, xf + depth) if side > 0 else (xf - depth, xf)
        bbox(name + '_w', (x0, y0, zb), (x1, y1, zb + h), wall, .01, 1)
        ridge = zb + h + 1.45
        ov = .65
        ym = (y0 + y1) / 2
        v = [(x0 - ov, y0 - ov, zb + h - .25), (x1 + ov, y0 - ov, zb + h - .25), (x1 + ov, y1 + ov, zb + h - .25),
             (x0 - ov, y1 + ov, zb + h - .25), ((x0 + x1) / 2, y0 - ov, ridge), ((x0 + x1) / 2, y1 + ov, ridge)]
        f = [(0, 1, 4), (2, 3, 5), (0, 4, 5, 3), (1, 2, 5, 4)]
        rf = mesh(name + '_roof', v, f, 'roof')
        uvl = rf.data.uv_layers.new(name='UV0')
        for p in rf.data.polygons:
            for li in p.loop_indices:
                c = rf.data.vertices[rf.data.loops[li].vertex_index].co
                uvl.data[li].uv = (c.y, math.hypot(c.x - (x0 + x1) / 2, c.z - ridge))
        bbox(name + '_fascia1', (x0 - ov - .02, y0 - ov, zb + h - .32), (x0 - ov + .03, y1 + ov, zb + h - .2), 'wood', .004, 1)
        bbox(name + '_fascia2', (x1 + ov - .03, y0 - ov, zb + h - .32), (x1 + ov + .02, y1 + ov, zb + h - .2), 'wood', .004, 1)
        # 檐沟
        for xg in (x0 - ov + .02, x1 + ov - .02):
            g = merge_mesh(f'{name}_gut{xg:.1f}', [tube('g', [(xg, y0 - ov, zb + h - .31), (xg, y1 + ov, zb + h - .31)], .05, 8, '')[:2]], 'pipe', 40)
            box_uv(g.data)
        # 窗和百叶（朝街一面）
        xw = x0 if side > 0 else x1
        d = -.03 if side > 0 else .03
        wn = max(1, int((y1 - y0) / 2.6))
        for fl in (0, 1):
            z = zb + .95 + fl * (h / 2)
            for k in range(wn):
                c = y0 + (k + .5) * (y1 - y0) / wn
                a, b = sorted((xw + d * 1.2, xw + d * .2))
                bbox(f'{name}_gl{fl}{k}', (a, c - .72, z), (b, c + .72, z + 1.05), 'glass_warm' if rng.random() < .2 else 'glass', 0)
                a2, b2 = sorted((xw + d * 2, xw + d * .2))
                bbox(f'{name}_shut{fl}{k}', (a2, c - .78, z + 1.05), (b2, c + .78, z + 1.25), 'shutter', .004, 1)
                bbox(f'{name}_sill{fl}{k}', (a2, c - .78, z - .06), (b2, c + .78, z), 'wood', .003, 1)
                for t in (-.72, 0, .72):
                    bbox(f'{name}_mul{fl}{k}{t}', (a2, c + t - .02, z), (b2, c + t + .02, z + 1.05), 'wood', 0)
        # 室外机：机身、风扇盘、支脚
        ax0, ax1 = sorted((xw, xw + d * 11))
        ay = (y0 + y1) / 2 + float(rng.uniform(-1, 1))
        bbox(name + '_ac', (ax0, ay - .38, zb + .1), (ax1, ay + .38, zb + .62), 'ac', .012, 1)
        fx = ax0 if side > 0 else ax1
        sgn = -1 if side > 0 else 1
        ring = [(0, 0, 0)] + [(0, .19 * math.cos(t), .19 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
        disc = mesh(name + '_fan', [(fx + sgn * .003, ay - .12 + q[1], zb + .36 + q[2]) for q in ring], [(0, i + 1, (i + 1) % 24 + 1) for i in range(24)], 'cable')
        box_uv(disc.data)
        for fy in (-.28, .28):
            bbox(f'{name}_foot{fy}', (ax0, ay + fy - .02, zb), (ax1, ay + fy + .02, zb + .1), 'steel', 0)
        p = merge_mesh(name + '_dp', [tube('p', [(xw + d * 3, y0 + .3, zb), (xw + d * 3, y0 + .3, zb + h)], .04, 10, '', cap=True)[:2]], 'pipe', 60)
        box_uv(p.data)

    jhouse('h_R1', 3.9, -16, -5.2, 5.4, 6.0, 1)
    jhouse('h_R2', 3.9, -4.6, 1.0, 5.2, 6.0, 1, wall='siding')
    jhouse('h_L1', -4.1, -16, -4.5, 5.6, 6.0, -1, wall='siding')
    jhouse('h_L2', -4.1, -3.8, 1.0, 5.0, 5.5, -1)
    # 台阶两侧：住宅顺坡抬高，公寓贴右侧
    y = 1.8
    k = 0
    while y < ytop - 2:
        ln = float(rng.uniform(5.5, 7.5))
        jhouse(f'h_S{k}', -3.35, y, min(y + ln, ytop + .5), float(rng.uniform(5.0, 5.8)), 6.0, -1, zb=sh(y) + .2, wall='plaster' if k % 2 else 'siding')
        y += ln + .5
        k += 1
    apartment('apt_R', 4.6, 2.0, 15.2, 6, .9)
    # 台阶顶的街区
    for k in range(4):
        y0 = ytop + 1 + k * 8.5
        jhouse(f'h_TL{k}', -3.6, y0, y0 + 7.8, float(rng.uniform(5.0, 6.0)), 7.0, -1, zb=ztop, wall='siding' if k % 2 else 'plaster')
    apartment('apt_R2', 4.4, ytop + 1, ytop + 14, 4, ztop)
    jhouse('h_TR', 3.4, ytop + 15, ytop + 24, 5.6, 7.0, 1, zb=ztop)
    jhouse('h_far', -3.0, ytop + 36, ytop + 44, 5.4, 7.0, 1, zb=ztop, wall='plaster')
    yf = ytop + 36
    # 谷中银座方向的街道：两侧连续低层建筑
    for side, x in ((1, 3.3), (-1, -3.25)):
        y = -62.0
        k = 0
        lim = -5.6 if side > 0 else -16.5
        lim = -16.5
        while y < lim:
            ln = float(rng.uniform(5.5, 9.5))
            y1 = min(y + ln, lim)
            if side > 0 and k % 4 == 2:
                apartment(f'apt_G{k}', x, y, y1, 4, 0)
            else:
                jhouse(f'h_G{side}{k}', x, y, y1, float(rng.uniform(5.0, 6.5)), 6.5, side, wall=('plaster', 'siding')[int(rng.integers(2))])
                # 一层雨棚，颜色素一点；招牌和店面内容归 4060
                ax0, ax1 = sorted((x - side * .95, x))
                bbox(f'aw_{side}{k}', (ax0, y + .3, 2.42), (ax1, y1 - .3, 2.5), ('awn_a', 'awn_b', 'awn_c')[int(rng.integers(3))], .012, 1)
            y = y1 + .08
            k += 1
    # 远景天际线
    for k in range(90):
        fy = float(rng.uniform(-470, -150)) if k < 60 else float(rng.uniform(ytop + 90, 330))
        fx = float(rng.uniform(-300, 300))
        w, d = float(rng.uniform(14, 34)), float(rng.uniform(14, 30))
        h = float(rng.uniform(9, 24)) * (1.9 if rng.random() < .22 else 1)
        # 街道轴线上不能挡夕阳：太阳高 6 度
        if fy < 0 and abs(fx + w / 2) < 70:
            h = min(h, abs(fy) * .085)
        z0_ = ztop if fy > 0 else 0
        bbox(f'far_{k}', (fx, fy, z0_ - 1), (fx + w, fy + d, z0_ + h), 'far', 0)
    bbox('ground_top', (-60, ytop + .2, ztop - 3), (60, 80, ztop - .02), 'apron', 0)
    bbox('hf_base', (-60, 80, -1), (60, 86, ztop), 'soil', 0)

    # 台阶尽头的山墙不留白：窗、门、室外机、雨水管
    for gx, gz in ((.6, .9), (2.6, .9), (-1.6, 3.2), (.6, 3.2), (2.6, 3.2)):
        bbox(f'hf_win{gx}{gz}', (gx - .55, yf - .04, ztop + gz), (gx + .55, yf, ztop + gz + 1.1), 'glass', 0)
        bbox(f'hf_sh{gx}{gz}', (gx - .62, yf - .1, ztop + gz + 1.1), (gx + .62, yf, ztop + gz + 1.3), 'shutter', .004, 1)
        bbox(f'hf_sill{gx}{gz}', (gx - .62, yf - .08, ztop + gz - .06), (gx + .62, yf, ztop + gz), 'wood', .003, 1)
    bbox('hf_door', (-2.3, yf - .05, ztop), (-1.3, yf, ztop + 2.1), 'shutter', .004, 1)
    bbox('hf_awn', (-2.6, yf - .7, ztop + 2.15), (-1.0, yf, ztop + 2.25), 'roof', .01, 1)
    bbox('hf_ac', (-1.0, yf - .45, ztop + .05), (-.2, yf - .05, ztop + .65), 'ac', .012, 1)

    # 砌块墙：深灰，沿路左侧，顶上压一皮
    bbox('block_wall', (-3.14, -16, -.05), (-3.02, 1.0, 1.6), 'block_wall', .004, 1, off=(0, 0))
    bbox('block_cap', (-3.17, -16, 1.6), (-2.99, 1.0, 1.66), 'cover', .01)

    # ---------- 电杆群 ----------
    tA, lA, a = build_pole('pole_A', 2.95, .55, -.04, xfmr=False, seed=0)
    tB, lB, b = build_pole('pole_B', 3.02, ytop + 8.0, ztop, 12.0, seed=1)
    tZ, lZ, c = build_pole('pole_Z', 2.95, -26.0, -.04, 12.0, seed=2)
    tC, lC, cc = build_pole('pole_C', -3.25, 10.6, sh(10.6) + .3, 12.0, seed=3)
    H = 12.0

    def pv(v):
        return Vector(v) + Vector((a.x, a.y, a.z))

    # 双变压器，抱箍和横担：照实拍，机身有放射状散热片，底部深色
    z0 = H - 4.5
    xp = []
    dk = []
    for sx in (-1, 1):
        ox = sx * .44
        body = [(.0, 0), (.185, .0), (.2, .02), (.2, .86), (.17, .90), (.0, .92)]
        xp.append(lathe((ox, .0, z0), body, 20))
        dk.append(lathe((ox, .0, z0 - .03), [(.0, 0), (.178, .0), (.18, .04), (.0, .04)], 20))
        for k in range(30):
            th = k / 30 * 2 * math.pi
            if abs(math.sin(th)) < .25 and sx * math.cos(th) < 0:
                continue
            xp.append(bx((ox + .232 * math.cos(th), .232 * math.sin(th), z0 + .38), (.066, .005, .68), th))
        # 顶部瓷套管
        for dy in (-.1, 0, .1):
            xp.append(lathe((ox + dy * .4, dy, z0 + .92), [(.024, 0), (.04, .02), (.024, .045), (.036, .07), (.02, .095), (.03, .12), (.012, .16)], 8))
    T = merge_mesh('pole_A_xfmr', xp, 'xfmr', 30)
    box_uv(T.data)
    T.location = a
    D = merge_mesh('pole_A_xfmr_dark', dk, 'cable', 30)
    box_uv(D.data)
    D.location = a
    br = [bx((0, -.0, z0 + .72), (1.25, .05, .11)), bx((0, .0, z0 + .16), (1.25, .05, .11)),
          bx((0, 0, H - 3.05), (1.45, .06, .06)), bx((.2, .0, H - 3.6), (.09, .09, 1.2)), bx((-.2, .0, H - 3.6), (.09, .09, 1.2)),
          bx((0, 0, 5.15), (.5, .06, .05))]
    S = merge_mesh('pole_A_bracket', br, 'steel', 30)
    box_uv(S.data)
    S.location = a
    # 开关瓷件（cut-out）
    cu = []
    for dx in (-.6, -.3, .3, .6):
        cu.append(lathe((dx, 0, H - 3.0), [(.022, 0), (.036, .03), (.024, .06), (.036, .09), (.024, .12), (.036, .15), (.024, .18), (.036, .21), (.016, .27)], 8))
    C = merge_mesh('pole_A_cutout', cu, 'porcelain', 35)
    box_uv(C.data)
    C.location = a

    w = []
    def wire(pts, r=.0065, sides=5):
        w.append(tube('w', pts, r, sides, '')[:2])

    # 主线：高压 3 根、低压 4 根照旧，再加中性线和两根副线
    for i in range(3):
        wire(catenary(tA[i], tB[i], .34 + .02 * i, 24, .03 * (i - 1)), .0075)
        wire(catenary(tZ[i], tA[i], .32 + .02 * i, 18), .0075)
    for i in range(4):
        s = .55 + i * .06
        wire(catenary(lA[i], lB[i], s, 24, .05), .0105)
        wire(catenary(lZ[i], lA[i], s, 18), .0105)
    # 街道方向继续串杆：每跨约 26 米
    prevT, prevL, prev = tZ, lZ, c
    for n_, py in enumerate((-52.0,)):
        tY, lY, yy = build_pole(f'pole_Y{n_}', 2.95, py, -.04, 12.0, seed=4 + n_)
        for i in range(3):
            wire(catenary(tY[i], prevT[i], .33, 14), .0075)
        for i in range(4):
            wire(catenary(lY[i], prevL[i], .55 + i * .05, 14), .0105)
        for k in range(6):
            dz = 6.2 - k * .2
            wire(catenary(Vector((yy.x + .23, yy.y, yy.z + dz)), Vector((prev.x + .23, prev.y, prev.z + dz)), .75 + k * .1, 14), .012, 6)
        # 过街接户线
        for k in range(8):
            ty = py + float(rng.uniform(-10, 24))
            wire(catenary(prevL[k % 4] if k % 2 else lY[k % 4], Vector((-3.3, ty, float(rng.uniform(4.2, 4.9)))), .3, 10), .0065)
        prevT, prevL, prev = tY, lY, yy
    for k in range(8):
        ty = -26 + float(rng.uniform(-4, 24))
        wire(catenary(lZ[k % 4] if k % 2 else lA[k % 4], Vector((-3.3 if k < 4 else 3.4, ty, float(rng.uniform(4.2, 4.9)))), .25, 10), .0065)
    # 通信缆束：一组 8 根，粗细不一，松紧不一
    for k in range(8):
        dz = 6.25 - k * .17 + float(rng.uniform(-.03, .03))
        dx = .23 if k % 3 else -.24
        s = .75 + k * .09 + float(rng.uniform(-.06, .06))
        r = float(rng.choice([.0085, .011, .014, .018, .022]))
        p0 = Vector((a.x + dx, a.y, a.z + dz))
        p1 = Vector((b.x + dx, b.y, b.z + dz - 1.2))
        p2 = Vector((c.x + dx, c.y, c.z + dz))
        wire(catenary(p0, p1, s, 24, float(rng.uniform(-.08, .08))), r, 6)
        wire(catenary(p2, p0, s, 18, float(rng.uniform(-.08, .08))), r, 6)
    # 左侧电杆：线从街道上空斜穿，这是实拍天空线条的来源
    for i in range(3):
        wire(catenary(tC[i], tB[i], .3 + .03 * i, 18), .0075)
        wire(catenary(lA[i], lC[i], .42 + .05 * i, 18), .0095)
        wire(catenary(tC[i], Vector((-30, 18 + i * 1.2, ztop + 10.4)), .5, 12), .0075)
    for k in range(5):
        dz = 6.4 - k * .2
        p0 = Vector((cc.x + .2, cc.y, cc.z + dz))
        p1 = Vector((a.x - .2, a.y, a.z + 5.2 + k * .22))
        p2 = Vector((-30, 8 + k * 1.1, ztop + 6 + k * .2))
        p3 = Vector((b.x - .2, b.y, b.z + dz - 1.2))
        r = float(rng.choice([.008, .011, .014, .018]))
        wire(catenary(p0, p1, .5 + k * .12, 18, .05), r, 6)
        wire(catenary(p0, p2, .9 + k * .1, 14), r, 6)
        wire(catenary(p0, p3, .6 + k * .1, 16), r, 6)
    for t, src in (((-4.6, 6.8, 5.6), lC[0]), ((-5.6, 12.6, 5.8), lC[1]), ((5.75, 9.0, 11.0), lC[2]), ((5.75, 11.5, 9.6), lC[3])):
        wire(catenary(src, Vector(t), float(rng.uniform(.2, .5)), 14), .007)
    # 接户线：扇形散向两侧楼房
    targets = [((-4.1, -2.4, 4.7), lA[0]), ((-4.1, -1.2, 4.5), lA[1]), ((-4.1, -.2, 4.35), lA[0]), ((-4.6, 3.2, 4.9), lA[1]),
               ((-4.6, 5.6, 5.0), lA[0]), ((3.9, -1.9, 4.6), lA[3]), ((3.9, -.7, 4.45), lA[2]), ((5.75, 3.4, 5.6), lA[2]),
               ((5.75, 7.0, 8.4), lA[3]), ((5.75, 5.2, 6.6), lA[3])]
    for t, src in targets:
        wire(catenary(src, Vector(t), float(rng.uniform(.12, .36)), 14), float(rng.uniform(.0055, .0085)))
    # 变压器引线：黑色小环，互相缠绕
    for sx in (-1, 1):
        for k, dy in enumerate((-.1, 0, .1)):
            top = pv((sx * .44 + dy * .4, dy, z0 + 1.08))
            cut = pv((sx * .3 * (1 + k % 2), 0, H - 2.73))
            mid = (top + cut) / 2 + Vector((sx * float(rng.uniform(.1, .34)), float(rng.uniform(-.25, .25)), float(rng.uniform(-.16, .06))))
            wire(spline([top, mid, cut], 8), .0052, 4)
            hv = tA[(k + (sx > 0)) % 3]
            m2 = (cut + hv) / 2 + Vector((float(rng.uniform(-.2, .2)), float(rng.uniform(-.2, .2)), -.08))
            wire(spline([cut + Vector((0, 0, .02)), m2, hv], 8), .0052, 4)
            # 低压侧：从机身绕到横担
            low = pv((sx * .62, float(rng.uniform(-.15, .15)), H - 2.05))
            m3 = pv((sx * float(rng.uniform(.65, .95)), float(rng.uniform(-.4, .4)), z0 + float(rng.uniform(.3, 1.1))))
            wire(spline([pv((sx * .62, dy, z0 + .62)), m3, low], 8), .0062, 5)
    # 余线盘：实拍电杆上最显眼的黑圈
    for (ox, oy, oz, R, turns) in ((.34, 1.1, 5.25, .22, 2.3), (.3, -.9, 5.6, .17, 1.8), (.36, 2.3, 4.85, .25, 2.6), (-.3, .8, 5.4, .16, 1.6)):
        ph = np.linspace(0, 2 * math.pi * turns, int(turns * 18))
        wire([(a.x + ox + .025 * math.sin(t * 2.3), a.y + oy + R * math.cos(t), a.z + oz + R * math.sin(t)) for t in ph], .0072, 5)
    # 杆上竖走的线
    wire(spline([pv((.12, .15, 6.1)), pv((.14, .13, 4.2)), pv((.16, .15, 3.1)), pv((.5, .3, 2.75)), pv((.95, .3, 3.0))], 6), .009, 5)
    wire(spline([pv((-.13, .16, 6.0)), pv((-.14, .16, 3.5)), pv((-.14, .2, 2.5))], 6), .007, 5)
    W = merge_mesh('wires', w, 'wire', 60)
    box_uv(W.data)

    # 接头盒、通信箱
    cl = []
    for (ox, oy, oz, L2, r) in ((.25, 3.0, 5.1, .32, .062), (.23, -3.2, 5.7, .25, .05), (.22, 5.6, 4.8, .3, .058), (-.24, 2.0, 5.05, .22, .045)):
        cl.append(tube('c', [(ox, oy - L2 * 1.05, oz), (ox, oy - L2, oz + 0), (ox, oy - L2 * .9, oz), (ox, oy + L2 * .9, oz), (ox, oy + L2, oz), (ox, oy + L2 * 1.05, oz)], [.0, r * .7, r, r, r * .7, .0], 10, '')[:2])
    O = merge_mesh('closures', cl, 'cable', 50)
    box_uv(O.data)
    O.location = (a.x, a.y, a.z)
    bbox('pole_A_box', (a.x - .1, a.y + .19, a.z + 4.0), (a.x + .12, a.y + .32, a.z + 4.55), 'xfmr', .008, 1)

    # 街灯：杆上伸出一支弧形灯臂
    arm = spline([pv((-.15, 0, 5.9)), pv((-.55, 0, 6.15)), pv((-1.05, 0, 6.4)), pv((-1.4, 0, 6.45))], 5)
    L_ = merge_mesh('lamp_arm', [tube('a', arm, .024, 10, '', cap=True)[:2]], 'steel', 40)
    box_uv(L_.data)
    bbox('lamp_head', (a.x - 1.72, a.y - .1, a.z + 6.37), (a.x - 1.36, a.y + .1, a.z + 6.46), 'xfmr', .02, 1)
    bbox('lamp_lens', (a.x - 1.7, a.y - .08, a.z + 6.355), (a.x - 1.38, a.y + .08, a.z + 6.372), 'lens', 0)

    # 电杆广告板和编号牌：贴着杆身的弧面
    def plate(name, mat, z0_, z1_, width, ang0):
        rp = .163
        n = 10
        v = []
        f = []
        uv = []
        half = width / rp / 2
        for j, z in enumerate((z0_, z1_)):
            for i in range(n + 1):
                t = i / n
                th = ang0 - half + 2 * half * t
                v.append((a.x + rp * math.cos(th), a.y + rp * math.sin(th), a.z + z))
                uv.append((t, j))
        f = [(i, i + 1, n + 2 + i, n + 1 + i) for i in range(n)]
        ob = mesh(name, v, f, mat, smooth=60)
        l = ob.data.uv_layers.new(name='UV0')
        for lp in ob.data.loops:
            l.data[lp.index].uv = uv[lp.vertex_index]

    plate('pole_ad', 'ad', 2.45, 3.55, .34, -math.radians(138))
    plate('pole_tag', 'tag', 2.05, 2.2, .28, -math.radians(150))


def build_plants(E, Y0, Z0, tread, rise, n_steps, root):
    """导入 Poly Haven 扫描植物，用实例摆放。"""
    rng = E['rng']
    scene = E['scene']
    road_z = E['road_z']

    def sh(y):
        return Z0 + max(0, min((y - Y0) / tread, n_steps)) * rise

    lib = {}
    for key in ('nettle_plant', 'dandelion_01', 'grass_bermuda_01', 'moss_01', 'shrub_01', 'fern_02'):
        path = os.path.join(root, key, key + '_2k.gltf')
        if not os.path.exists(path):
            print('PLANT missing', key)
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == 'MESH']
        for o in new:
            o.hide_render = True
            o.hide_viewport = True
        lib[key] = meshes
        print('PLANT', key, [(m.name, len(m.data.polygons), tuple(round(d, 2) for d in m.dimensions)) for m in meshes][:6])

    count = 0

    def put(key, x, y, z, s, sel=None, rot=None):
        nonlocal count
        ms = lib.get(key)
        if not ms:
            return
        m = ms[int(rng.integers(len(ms)))] if sel is None else ms[sel % len(ms)]
        ob = bpy.data.objects.new(f'{key}_i{count}', m.data)
        scene.collection.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = (0, 0, float(rng.uniform(0, 6.28)) if rot is None else rot)
        ob.scale = (s, s, s)
        count += 1

    # 花坛：灌木打底，荨麻和蕨填缝，蒲公英点缀
    segs = n_steps // 3
    L = n_steps * tread / segs
    for side, x0, x1 in (('L', -2.95, -2.48), ('R', 2.78, 3.45)):
        for j in range(segs):
            y0, y1 = Y0 + j * L, Y0 + (j + 1) * L
            ztop = sh(y1) + .35
            # 灌木扫描是一条长带，顺着花坛放
            put('shrub_01', (x0 + x1) / 2, (y0 + y1) / 2, ztop, float(rng.uniform(.34, .42)), rot=1.5708)
            for k in range(7):
                put('nettle_plant', float(rng.uniform(x0, x1)), float(rng.uniform(y0, y1)), ztop, float(rng.uniform(2.6, 4.2)))
            for k in range(3):
                put('fern_02', float(rng.uniform(x0, x1)), float(rng.uniform(y0, y1)), ztop, float(rng.uniform(.55, .85)))
    # 路缘和缝隙：蒲公英、草
    spots = [(2.2, -4.2), (2.2, -3.05), (2.21, -.7), (-2.6, -2.4), (-2.6, -.3), (-2.58, -4.1), (2.58, -1.6), (2.62, -.1)]
    for i, (x, y) in enumerate(spots):
        z = road_z(min(max(x, -2.6), 2.2), y)
        put('dandelion_01', x, y, z, float(rng.uniform(.5, .85)))
        put('grass_bermuda_01', x + float(rng.uniform(-.05, .05)), y + float(rng.uniform(-.2, .2)), z, float(rng.uniform(.22, .35)))
    for x, y in ((-2.32, 1.5), (2.5, 1.48), (2.72, .35), (3.15, .75)):
        put('grass_bermuda_01', x, y, sh(y) if y > Y0 else -.04, .3)
        put('dandelion_01', x, y + .1, sh(y) if y > Y0 else -.04, .7)
    print('PLANTS placed', count)
