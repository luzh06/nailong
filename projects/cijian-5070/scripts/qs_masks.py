# 《此间》质量样板：程序绘制 10×10 米路面遮罩（2K）。
# 单位：世界坐标米。x∈[-5,5]，y∈[-5,5]。输出 RGBA PNG，游戏端也能直接用这张图。
import numpy as np

N = 2048
S = 10.0


def smooth_noise(rng, shape, cell):
    """双线性放大的随机场，cell 为低分辨率格子数。"""
    h, w = shape
    g = rng.random((cell + 2, cell + 2))
    yy = np.linspace(0, cell, h, endpoint=False)
    xx = np.linspace(0, cell, w, endpoint=False)
    y0 = yy.astype(int)
    x0 = xx.astype(int)
    ty = (yy - y0)[:, None]
    tx = (xx - x0)[None, :]
    ty = ty * ty * (3 - 2 * ty)
    tx = tx * tx * (3 - 2 * tx)
    a = g[np.ix_(y0, x0)]
    b = g[np.ix_(y0, x0 + 1)]
    c = g[np.ix_(y0 + 1, x0)]
    d = g[np.ix_(y0 + 1, x0 + 1)]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fbm(rng, cells=(6, 13, 29, 61, 127, 257), gain=0.55):
    out = np.zeros((N, N))
    amp = 1.0
    tot = 0
    for c in cells:
        out += smooth_noise(rng, (N, N), c) * amp
        tot += amp
        amp *= gain
    out /= tot
    return (out - out.min()) / (out.max() - out.min())


def blur(a, r):
    """盒式模糊三次，近似高斯。"""
    if r < 1:
        return a
    for _ in range(3):
        a = (_box(a, r, 0) + 0)
        a = _box(a, r, 1)
    return a


def _box(a, r, axis):
    c = np.cumsum(np.pad(a, [(r + 1, r) if i == axis else (0, 0) for i in range(2)], mode='edge'), axis=axis)
    if axis == 0:
        return (c[2 * r + 1:, :] - c[:-(2 * r + 1), :]) / (2 * r + 1)
    return (c[:, 2 * r + 1:] - c[:, :-(2 * r + 1)]) / (2 * r + 1)


def w2p(v):
    return (np.asarray(v) + S / 2) / S * N


def draw_polyline(img, pts, width_m, value=1.0):
    """沿折线逐点盖圆章。pts 单位米。"""
    r = max(1, int(width_m / S * N / 2))
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    disk = (xx * xx + yy * yy) <= r * r + 0.5
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        px0, py0, px1, py1 = *w2p((x0, y0)), *w2p((x1, y1))
        n = int(max(abs(px1 - px0), abs(py1 - py0))) + 1
        for t in np.linspace(0, 1, n):
            px = int(px0 + (px1 - px0) * t)
            py = int(py0 + (py1 - py0) * t)
            a0, a1 = max(py - r, 0), min(py + r + 1, N)
            b0, b1 = max(px - r, 0), min(px + r + 1, N)
            if a0 >= a1 or b0 >= b1:
                continue
            d = disk[a0 - py + r:a1 - py + r, b0 - px + r:b1 - px + r]
            img[a0:a1, b0:b1][d] = np.maximum(img[a0:a1, b0:b1][d], value)


def crack_walk(rng, start, heading, length, step=0.06, wander=0.55):
    pts = [np.array(start, float)]
    h = heading
    for _ in range(int(length / step)):
        h += rng.normal(0, wander)
        h = heading + np.clip(h - heading, -1.1, 1.1)
        pts.append(pts[-1] + step * rng.uniform(.6, 1.4) * np.array([np.cos(h), np.sin(h)]))
    return pts


def rect_mask(xx, yy, warp, x0, x1, y0, y1, amt=0.05):
    wx = (warp - .5) * amt * 2
    wy = (np.roll(warp, 300, axis=0) - .5) * amt * 2
    return ((xx + wx) > x0) & ((xx + wx) < x1) & ((yy + wy) > y0) & ((yy + wy) < y1)


def make(seed=7, hero=True):
    rng = np.random.default_rng(seed)
    lin = (np.arange(N) + .5) / N * S - S / 2
    xx, yy = np.meshgrid(lin, lin)
    warp = fbm(rng, cells=(9, 23, 51, 111))
    fine = fbm(rng, cells=(31, 67, 141, 283, 571))

    # 道路范围：x∈[-2.6,2.2]，y<1.4（台阶起点）
    # 补丁：纵向管线开挖、井盖周围方块、横向小补丁
    if hero:
        trench = rect_mask(xx, yy, warp, -0.95, -0.25, -6, 0.75, .035)
        box_mh = rect_mask(xx, yy, warp, 0.55, 1.75, -2.75, -1.45, .03)
        small = rect_mask(xx, yy, warp, -2.35, -1.5, -3.7, -3.0, .04)
    else:
        # 延伸段：10 米一循环，补丁都留在中段，循环边界看不出来
        trench = rect_mask(xx, yy, warp, -1.6, -.5, -2.4, -.9, .04)
        box_mh = rect_mask(xx, yy, warp, .4, 1.5, 1.2, 2.3, .03)
        small = rect_mask(xx, yy, warp, -2.3, -1.4, 2.6, 3.5, .04)
    patch = trench | box_mh | small
    # 新旧有差：trench 老（0.55），box 新（1.0），small 中（0.75）
    patch_age = np.zeros((N, N))
    patch_age[trench] = .55
    patch_age[small] = .75
    patch_age[box_mh] = 1.0

    # 接缝沥青：边界带，宽度不均，偶有断续
    p = patch.astype(float)
    edge = np.clip(blur(p, 1) * (1 - blur(p, 1)) * 4, 0, 1)
    seam_w = .35 + .65 * smooth_noise(rng, (N, N), 41)
    seam = np.clip((edge - (1 - seam_w) * .82) * 3.2, 0, 1)
    seam *= np.clip((fbm(rng, cells=(15, 37, 83)) - .24) * 6, 0, 1)

    # 裂缝
    cr = np.zeros((N, N))
    starts = [((-2.4, 0.9), -.5, 3.4), ((2.1, -3.8), 2.7, 2.6), ((-.2, -4.9), 1.2, 3.0), ((1.9, .9), 3.5, 2.2),
              ((-2.5, -1.4), .15, 1.8), ((.3, .2), -2.1, 1.8)]
    for s, h, l in starts:
        pts = crack_walk(rng, s, h, l)
        draw_polyline(cr, pts, .0065)
        for k in rng.integers(4, len(pts) - 2, 4):
            draw_polyline(cr, crack_walk(rng, pts[k], h + rng.choice([-1, 1]) * rng.uniform(.6, 1.3), rng.uniform(.3, .9), wander=.7), .0042, .7)
    # 龟裂区：靠左路肩，网状细缝
    alli = rect_mask(xx, yy, warp, -2.6, -1.65, -1.2, .9, .12)
    cell = 0.16
    u = (xx + (warp - .5) * .22) / cell
    v = (yy + (np.roll(warp, 500, 1) - .5) * .22) / cell
    f = np.minimum(np.abs(((u + np.floor(v) * .5) % 1) - .5), np.abs((v % 1) - .5))
    net = np.clip((.05 - f) * 26, 0, 1) * alli * np.clip((blur(alli.astype(float), 30) - .25) * 4, 0, 1)
    cr = np.maximum(cr, net * .8)
    cr *= (1 - p * .85)
    cr = np.maximum(cr, blur(cr, 1) * .6)

    # 白线：右侧外侧线（y 方向），宽 15 厘米，距路缘 25 厘米；停止线在台阶前
    paint = np.zeros((N, N))
    wob = (smooth_noise(rng, (N, N), 8) - .5) * .018
    paint[(np.abs(xx + wob - 1.9) < .075) & (yy < .6)] = 1
    if hero:
        paint[(np.abs(yy + wob - .55) < .15) & (xx > -2.35) & (xx < 1.9)] = 1
    # 磨损：车轮带最重，骨料高点留漆，补丁处被切断
    wear = .58 + .42 * np.exp(-((xx - .3) / 1.1) ** 2) * (yy < 1)
    keep = np.clip((fine * .75 + fbm(rng, cells=(120, 300, 700), gain=.7) * .55 - wear * .72) * 5.5, 0, 1)
    paint = blur(paint, 1) * keep * (1 - p)

    # 水渍：沿路缘的低洼 + 补丁边的积水；wet=暗湿，puddle=镜面
    low = np.exp(-((xx - 2.05) / .55) ** 2) * .7 + np.exp(-((xx + 2.45) / .4) ** 2) * .55
    if hero:
        low += np.exp(-((yy - 1.15) / .4) ** 2) * .5
    tide = fbm(rng, cells=(5, 11, 23, 53, 113))
    wet = np.clip((low * .85 + tide * .85 - .82) * 3.2, 0, 1) * (np.abs(xx) < 3)
    # 水痕的盐边：湿区外缘一圈浅色
    tide_edge = np.clip(1 - np.abs(blur(wet, 2) - .35) * 7, 0, 1) * np.clip(tide * 1.6 - .25, 0, 1)
    puddle = np.clip((low * .9 + tide * .8 - 1.17) * 12, 0, 1)

    # 油污与轮迹：两条纵向暗带 + 随机斑点
    tyre = np.exp(-((xx - 1.05) / .32) ** 2) + np.exp(-((xx + .85) / .32) ** 2)
    oil = np.clip((fbm(rng, cells=(17, 41, 89)) - .58) * 7, 0, 1) * np.clip(tyre, 0, 1)
    grime = np.clip(tyre * .34 + oil * .5 + (tide - .5) * .7 + .24, 0, 1)
    grime = np.maximum(grime, blur(cr, 7) * 1.1)
    grime = np.maximum(grime, np.clip(low * .9 * (tide + .3), 0, 1) * .75)

    # 高度（厘米级微地形给 bump），补丁略高、裂缝低、沟边塌
    height = .5 + patch_age * .10 * blur(p, 4) - blur(cr, 1) * .3 - puddle * .03 + (warp - .5) * .2
    # 青苔：只在路缘最湿且车压不到的地方
    moss = np.clip((np.exp(-((xx - 2.14) / .10) ** 2) + np.exp(-((xx + 2.56) / .10) ** 2) ) * (tide * 1.8 - .62) + (np.exp(-((yy - 1.32) / .08) ** 2) * (tide * 1.8 - .62) if hero else 0), 0, 1)

    return dict(patch=p, age=patch_age, seam=seam, crack=np.clip(cr, 0, 1), paint=np.clip(paint, 0, 1), wet=wet,
                tide=tide_edge, puddle=puddle, grime=grime, height=np.clip(height, 0, 1), moss=moss, fine=fine)


def manhole_height(size=1024, seed=3):
    """日本常见的铸铁井盖：外框、防滑凸点、中央铭牌。返回 height, rim, lug。"""
    rng = np.random.default_rng(seed)
    lin = np.linspace(-1, 1, size)
    xx, yy = np.meshgrid(lin, lin)
    r = np.hypot(xx, yy)
    th = np.arctan2(yy, xx)
    h = np.zeros((size, size))
    frame = (r > .90) & (r < .985)
    gap = (r >= .875) & (r <= .90)
    cover = r < .875
    h[frame] = .85
    h[gap] = .0
    h[cover] = .55
    # 同心放射花纹：环带凸块
    ring = np.zeros((size, size))
    for rad, n, w in [(.34, 14, .028), (.5, 22, .028), (.66, 30, .028), (.8, 38, .026)]:
        band = np.abs(r - rad) < w
        a = ((th / (2 * np.pi) + .5) * n + (rad * 7) % 1) % 1
        ring[band & (a > .16) & (a < .84)] = 1
    # 六边形防滑点
    s = .058
    u = xx / s
    v = yy / (s * .866)
    v2 = np.floor(v)
    u2 = u + (v2 % 2) * .5
    cu = (u2 % 1) - .5
    cv = (v % 1) - .5
    lug = (np.hypot(cu, cv * .866) < .29) & (r < .86) & (r > .24)
    h[lug & cover] = .78
    h[(ring > 0) & cover] = .86
    # 中央圆铭牌
    plate = r < .22
    h[plate] = .84
    h[(r < .19) & (r > .17)] = .72
    # 两个提手孔
    for cx, cy in [(.68, .0), (-.68, .0)]:
        hole = np.hypot((xx - cx) / 1.0, (yy - cy) / .55) < .055
        h[hole] = .12
    h = blur(h, 2)
    rim = frame.astype(float)
    return h, rim, blur(((h > .7) & cover).astype(float), 1)
