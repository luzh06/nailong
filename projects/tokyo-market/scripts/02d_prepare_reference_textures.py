"""按参考图重做的程序贴图 (不使用任何照片像素):
  yn_kawara_*        本瓦屋面: 由高度场算出法线和 AO, 可四方连续
  yn_trim_*          屋檐 Trim Sheet: 椽头, 椽底, 斗拱墙, 连子窗, 栏杆, 瓦当; 水平可连续
  yn_shutter_art_2k  8 幅彩绘卷帘, 自己构图, 不是复制真实壁画
  yn_plaque_1k       仲见世式吊牌
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit_atlas import TRIM_ROWS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
FONT = os.path.join(ROOT, "fonts", "ZenAntique-Regular.ttf")
RNG = np.random.default_rng(101)


def periodic_noise(size, cells):
    """四方连续的低频噪声。"""
    grid = RNG.normal(0, 1, (cells, cells))
    small = np.tile(grid, (3, 3))
    im = Image.fromarray(((small - small.min()) / np.ptp(small) * 255).astype(np.uint8))
    big = np.asarray(im.resize((size * 3, size * 3), Image.BICUBIC), dtype=np.float32) / 255
    return big[size:2 * size, size:2 * size]


def height_to_normal(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    n = np.dstack((-dx, dy, np.ones_like(h)))  # OpenGL: 贴图 y 向下, 所以 dy 取正
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return (n * 0.5 + 0.5)


def save_rgb(a, name, quality=92):
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(os.path.join(TEX, name), quality=quality)


def kawara():
    """本瓦: 6 垄 x 6 行 = 1.5 米一格。平瓦上盖半圆筒瓦, 每行下压一点。"""
    S = 2048
    cols, rows = 6, 6
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    u = (x / S * cols) % 1.0
    v = (y / S * rows)
    row = np.floor(v).astype(int)
    fv = v - row
    # 筒瓦截面: 半圆
    round_w = 0.42
    d = np.abs(u - 0.5) / round_w
    barrel = np.sqrt(np.clip(1 - d ** 2, 0, 1))
    # 平瓦微凹, 排水槽
    pan = 0.1 * (np.cos((u - 0.5) * 2 * np.pi) * 0.5 + 0.5) * 0.4
    # 每行瓦的下缘翘起一点, 上一行压住下一行
    lap = fv ** 2.2 * 0.16
    h = np.maximum(barrel * 0.75, pan) + lap
    # 瓦与瓦之间的接缝
    seam = np.clip((fv - 0.965) / 0.035, 0, 1)
    h = h - seam * 0.3
    # 每块瓦随机抬高和换色
    col = np.floor(x / S * cols).astype(int)
    tid = (col % cols) + (row % rows) * cols
    jitter = RNG.normal(0, 1, cols * rows)
    tone = RNG.normal(0, 1, cols * rows)
    h = h + jitter[tid] * 0.012 + periodic_noise(S, 96) * 0.03
    normal = height_to_normal(h, 42.0)
    save_rgb(normal, "yn_kawara_normal_2k.jpg")

    # 底色: 黑灰烧瓦, 每块略有不同, 垄沟积灰, 少量发白的水渍和地衣
    base = 0.2 + tone[tid] * 0.014
    grooves = 1 - np.clip(barrel * 1.6, 0, 1)
    base = base - grooves * 0.09
    macro = periodic_noise(S, 8)
    base = base + (macro - 0.5) * 0.07
    fine = periodic_noise(S, 256)
    base = base + (fine - 0.5) * 0.05
    rgb = np.dstack((base * 0.97, base * 0.99, base * 1.04))
    lichen = np.clip(periodic_noise(S, 40) * 2.2 - 1.45, 0, 1) * (1 - barrel * 0.5)
    rgb = rgb * (1 - lichen[..., None] * 0.6) + np.array([0.3, 0.3, 0.25]) * lichen[..., None] * 0.6
    # 筒瓦顶部被雨水洗得亮一点
    rgb = rgb + (barrel ** 6)[..., None] * 0.035
    save_rgb(rgb, "yn_kawara_basecolor_2k.jpg")
    # 红瓦: 同一块瓦染色, 共用法线和 ORM
    lum = rgb.mean(axis=2, keepdims=True)
    save_rgb(lum * np.array([2.5, 1.0, 0.78]), "yn_roof_red_basecolor_2k.jpg")

    # ORM: 沟里 AO 重, 瓦面半光
    ao = np.clip(0.42 + 0.58 * (h - h.min()) / np.ptp(h), 0, 1)
    rough = np.clip(0.58 + (fine - 0.5) * 0.25 + lichen * 0.3 + grooves * 0.14, 0, 1)
    metal = np.zeros_like(h)
    save_rgb(np.dstack((ao, rough, metal)), "yn_kawara_orm_2k.jpg")


# Trim Sheet 水平 2048 像素对应约 3.2 米; 每条的范围在 kit_atlas.TRIM_ROWS
RED = (154, 44, 26)
DARK = (58, 18, 10)
WHITE = (226, 218, 198)


def trim():
    S = 2048
    im = Image.new("RGB", (S, S), RED)
    h = Image.new("L", (S, S), 128)
    d, dh = ImageDraw.Draw(im), ImageDraw.Draw(h)

    # 椽头: 上排密, 下排疏; 白色端面 + 红色椽身
    y0, y1 = TRIM_ROWS["rafter_ends"]
    d.rectangle((0, y0, S, y1), fill=DARK)
    d.rectangle((0, y0, S, y0 + 34), fill=WHITE)  # 上面那条白色茅负
    d.rectangle((0, y0 + 112, S, y0 + 136), fill=RED)
    dh.rectangle((0, y0, S, y0 + 34), fill=220)
    dh.rectangle((0, y0 + 112, S, y0 + 136), fill=210)
    for x in range(0, S, 64):
        d.rectangle((x + 14, y0 + 48, x + 50, y0 + 100), fill=WHITE)
        d.rectangle((x + 14, y0 + 92, x + 50, y0 + 100), fill=(190, 182, 164))
        dh.rectangle((x + 14, y0 + 48, x + 50, y0 + 100), fill=240)
    for x in range(0, S, 128):
        d.rectangle((x + 30, y0 + 150, x + 98, y0 + 226), fill=WHITE)
        d.rectangle((x + 30, y0 + 214, x + 98, y0 + 226), fill=(186, 178, 160))
        dh.rectangle((x + 30, y0 + 150, x + 98, y0 + 226), fill=240)
    d.rectangle((0, y1 - 24, S, y1), fill=RED)

    # 椽底: 沿檐深方向的平行椽子, u 沿檐口
    y0, y1 = TRIM_ROWS["rafter_under"]
    d.rectangle((0, y0, S, y1), fill=(86, 28, 16))
    dh.rectangle((0, y0, S, y1), fill=70)
    for x in range(0, S, 64):
        d.rectangle((x + 16, y0, x + 48, y1), fill=(150, 46, 26))
        d.rectangle((x + 16, y0, x + 22, y1), fill=(176, 62, 34))
        d.rectangle((x + 42, y0, x + 48, y1), fill=(96, 28, 16))
        dh.rectangle((x + 16, y0, x + 48, y1), fill=210)
    d.rectangle((0, y0 + 118, S, y0 + 138), fill=(120, 36, 20))
    dh.rectangle((0, y0 + 118, S, y0 + 138), fill=230)

    # 斗拱墙: 下白墙, 上一组组三跳斗拱
    y0, y1 = TRIM_ROWS["bracket_wall"]
    d.rectangle((0, y0, S, y1), fill=RED)
    for i in range(2):
        x = i * 1024
        # 白壁
        d.rectangle((x + 40, y0 + 330, x + 460, y0 + 440), fill=WHITE)
        d.rectangle((x + 564, y0 + 330, x + 984, y0 + 440), fill=WHITE)
        dh.rectangle((x + 40, y0 + 330, x + 460, y0 + 440), fill=90)
        dh.rectangle((x + 564, y0 + 330, x + 984, y0 + 440), fill=90)
        d.rectangle((x + 40, y0 + 120, x + 460, y0 + 200), fill=WHITE)
        d.rectangle((x + 564, y0 + 120, x + 984, y0 + 200), fill=WHITE)
        # 斗拱组 (柱头和补间各一组)
        for cx in (x + 0, x + 512):
            for level, (w, yb, hh) in enumerate(((150, y0 + 300, 34), (230, y0 + 230, 34), (310, y0 + 160, 34), (400, y0 + 90, 30))):
                for xx in (cx,):
                    d.rectangle((xx - w // 2, yb, xx + w // 2, yb + hh), fill=(132, 36, 20))
                    dh.rectangle((xx - w // 2, yb, xx + w // 2, yb + hh), fill=225)
                    # 下方的小斗: 白色端头是参考图里最醒目的细节
                    for off in (-w // 2, 0, w // 2):
                        if xx + off < 0:
                            continue
                        d.rectangle((xx + off - 18, yb + hh, xx + off + 18, yb + hh + 34), fill=(112, 32, 18))
                        d.rectangle((xx + off - 18, yb - 12, xx + off + 18, yb), fill=WHITE)
                        dh.rectangle((xx + off - 18, yb + hh, xx + off + 18, yb + hh + 34), fill=240)
            # 向外伸出的挑枋端头
            d.rectangle((cx - 26, y0 + 20, cx + 26, y0 + 86), fill=WHITE)
            d.rectangle((cx - 44, y0 + 8, cx + 44, y0 + 26), fill=(120, 34, 18))
            dh.rectangle((cx - 26, y0 + 20, cx + 26, y0 + 86), fill=250)
        # 墙和梁交界的暗缝
    d.rectangle((0, y1 - 54, S, y1), fill=(130, 38, 22))
    d.rectangle((0, y1 - 60, S, y1 - 54), fill=DARK)

    # 连子窗: 青绿竖棂
    y0, y1 = TRIM_ROWS["lattice"]
    d.rectangle((0, y0, S, y1), fill=(30, 40, 34))
    dh.rectangle((0, y0, S, y1), fill=60)
    for x in range(0, S, 32):
        d.rectangle((x + 6, y0 + 20, x + 24, y1 - 20), fill=(52, 118, 96))
        d.rectangle((x + 6, y0 + 20, x + 11, y1 - 20), fill=(78, 150, 126))
        dh.rectangle((x + 6, y0 + 20, x + 24, y1 - 20), fill=210)
    d.rectangle((0, y0, S, y0 + 20), fill=RED)
    d.rectangle((0, y1 - 20, S, y1), fill=RED)

    # 栏杆: 背后暗, 望柱和横杆朱红
    y0, y1 = TRIM_ROWS["railing"]
    d.rectangle((0, y0, S, y1), fill=(60, 26, 18))
    dh.rectangle((0, y0, S, y1), fill=50)
    for yy, hh in ((y0 + 26, 28), (y0 + 150, 24), (y1 - 34, 34)):
        d.rectangle((0, yy, S, yy + hh), fill=(176, 50, 28))
        dh.rectangle((0, yy, S, yy + hh), fill=230)
    for x in range(0, S, 256):
        d.rectangle((x + 112, y0, x + 144, y1), fill=(176, 50, 28))
        d.ellipse((x + 106, y0 - 2, x + 150, y0 + 24), fill=(196, 160, 70))
        dh.rectangle((x + 112, y0, x + 144, y1), fill=245)
    for x in range(0, S, 64):
        d.rectangle((x + 24, y0 + 54, x + 38, y0 + 150), fill=(146, 42, 24))
        dh.rectangle((x + 24, y0 + 54, x + 38, y0 + 150), fill=190)

    # 瓦当一排: 黑灰圆头
    y0, y1 = TRIM_ROWS["tile_nose"]
    d.rectangle((0, y0, S, y1), fill=(26, 26, 28))
    dh.rectangle((0, y0, S, y1), fill=60)
    for x in range(0, S, 128):
        d.ellipse((x + 16, y0 + 18, x + 112, y0 + 114), fill=(62, 62, 66), outline=(92, 92, 96), width=5)
        d.ellipse((x + 44, y0 + 46, x + 84, y0 + 86), outline=(92, 92, 96), width=4)
        dh.ellipse((x + 16, y0 + 18, x + 112, y0 + 114), fill=240)

    # 彩绘额枋: 朱红底金边绿饰
    y0, y1 = TRIM_ROWS["beam"]
    d.rectangle((0, y0, S, y1), fill=RED)
    dh.rectangle((0, y0, S, y1), fill=200)
    d.rectangle((0, y0 + 24, S, y0 + 34), fill=(196, 160, 70))
    d.rectangle((0, y1 - 34, S, y1 - 24), fill=(196, 160, 70))
    for x in range(0, S, 512):
        cx, cy = x + 256, (y0 + y1) // 2
        d.ellipse((cx - 96, cy - 70, cx + 96, cy + 70), fill=(52, 118, 96), outline=(196, 160, 70), width=8)
        d.ellipse((cx - 48, cy - 36, cx + 48, cy + 36), fill=(176, 66, 44), outline=(226, 218, 198), width=5)
        for s in (-1, 1):
            d.arc((cx + s * 120 - 90, cy - 50, cx + s * 120 + 90, cy + 50), 0, 360, fill=(226, 218, 198), width=8)

    # 老化: 全局污渍和轻微色差, 水平要能接上
    a = np.asarray(im, dtype=np.float32)
    grime = periodic_noise(S, 32)[..., None]
    a = a * (0.82 + grime * 0.32) + RNG.normal(0, 3.5, (S, S, 1))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(TEX, "yn_trim_basecolor_2k.jpg"), quality=93)

    hh = np.asarray(h.filter(ImageFilter.GaussianBlur(1.6)), dtype=np.float32) / 255
    save_rgb(height_to_normal(hh, 3.0), "yn_trim_normal_2k.jpg")
    ao = np.clip(0.45 + hh * 0.7, 0, 1)
    rough = np.full_like(hh, 0.58)
    save_rgb(np.dstack((ao, rough, np.zeros_like(hh))), "yn_trim_orm_2k.jpg")
    # 夜里被投光照亮的样子: 深的地方压暗, 不是一片平光
    glow = np.clip(np.asarray(im, dtype=np.float32) / 255 * np.array([1.25, 0.72, 0.42]) * (0.25 + hh[..., None] * 1.1), 0, 1)
    save_rgb(glow, "yn_trim_emissive_1k.jpg")
    Image.open(os.path.join(TEX, "yn_trim_emissive_1k.jpg")).resize((1024, 1024), Image.LANCZOS).save(
        os.path.join(TEX, "yn_trim_emissive_1k.jpg"), quality=90)


def wave_band(d, x0, x1, y, amp, col, step=70):
    pts = []
    x = x0
    while x <= x1:
        pts.append((x, y + math.sin(x / step * 2.2) * amp))
        x += 8
    d.line(pts, fill=col, width=9)


def shutter_panel(d, box, kind):
    """一幅卷帘画。朴素的平涂风, 主题是祭礼和四季, 全是自己的构图。"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    backgrounds = [(226, 214, 190), (196, 214, 222), (232, 206, 176), (44, 58, 92), (222, 200, 196), (206, 216, 196), (60, 42, 58), (230, 222, 200)]
    bg = backgrounds[kind % 8]
    d.rectangle(box, fill=bg)
    rng = np.random.default_rng(kind * 7 + 3)
    # 下方是深色波浪或地面
    ground = y0 + h * 0.72
    if kind % 4 == 0:
        for k in range(7):
            wave_band(d, x0, x1, ground + k * 26, 11, (34, 72, 118) if k % 2 else (64, 110, 150))
    else:
        d.rectangle((x0, ground, x1, y1), fill=(92, 72, 56) if kind % 3 else (70, 90, 70))
    if kind in (0, 4):
        # 富士和太阳
        d.polygon([(x0 + w * 0.15, ground), (x0 + w * 0.5, y0 + h * 0.2), (x0 + w * 0.85, ground)], fill=(58, 76, 112))
        d.polygon([(x0 + w * 0.41, y0 + h * 0.31), (x0 + w * 0.5, y0 + h * 0.2), (x0 + w * 0.59, y0 + h * 0.31), (x0 + w * 0.5, y0 + h * 0.36)], fill=(236, 232, 224))
        d.ellipse((x0 + w * 0.72, y0 + h * 0.08, x0 + w * 0.88, y0 + h * 0.08 + w * 0.16), fill=(192, 56, 42))
    elif kind in (1, 5):
        # 祭礼的灯笼串
        for row in range(3):
            yy = y0 + h * (0.14 + row * 0.17)
            d.line((x0, yy, x1, yy), fill=(70, 50, 40), width=4)
            for i in range(9):
                cx = x0 + (i + 0.5) * w / 9
                d.ellipse((cx - 24, yy + 4, cx + 24, yy + 62), fill=(190, 58, 44), outline=(60, 30, 24), width=3)
        for i in range(10):
            cx = x0 + (i + 0.5) * w / 10
            cy = ground + 8
            c = [(40, 44, 66), (150, 50, 44), (210, 190, 140)][i % 3]
            d.ellipse((cx - 12, cy - 36, cx + 12, cy - 12), fill=(210, 176, 150))
            d.polygon([(cx - 26, cy + 60), (cx + 26, cy + 60), (cx + 12, cy - 12), (cx - 12, cy - 12)], fill=c)
    elif kind in (2, 6):
        # 樱花枝
        for b in range(5):
            sx, sy = x0 + rng.uniform(0, w), y0
            ex, ey = sx + rng.uniform(-140, 140), y0 + rng.uniform(h * 0.3, h * 0.65)
            d.line((sx, sy, ex, ey), fill=(66, 44, 36), width=9)
            for _ in range(46):
                t = rng.uniform(0, 1)
                cx = sx + (ex - sx) * t + rng.normal(0, 36)
                cy = sy + (ey - sy) * t + rng.normal(0, 26)
                r = rng.uniform(7, 15)
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(232, 176, 186) if rng.random() < 0.7 else (246, 224, 228))
    else:
        # 屋顶排和塔的剪影
        for i in range(7):
            cx = x0 + (i + 0.5) * w / 7
            rw = w / 8
            base = ground - rng.uniform(0, 40)
            d.polygon([(cx - rw, base), (cx, base - rng.uniform(70, 120)), (cx + rw, base)], fill=(60, 56, 60))
            d.rectangle((cx - rw * 0.75, base, cx + rw * 0.75, ground), fill=(184, 72, 50) if i % 2 else (206, 192, 164))
        cx = x0 + w * 0.68
        for t in range(5):
            yy = y0 + h * 0.2 + t * 42
            rw = 26 + t * 12
            d.polygon([(cx - rw, yy + 24), (cx + rw, yy + 24), (cx, yy)], fill=(40, 36, 40))
    # 卷帘的水平条影, 让它看起来是画在铁皮上
    for yy in range(y0, y1, 22):
        d.line((x0, yy, x1, yy), fill=tuple(int(v * 0.66) for v in bg), width=2)


def shutter_art():
    S = 2048
    im = Image.new("RGB", (S, S), (60, 60, 60))
    d = ImageDraw.Draw(im)
    for i in range(8):
        col, row = i % 2, i // 2
        shutter_panel(d, (col * 1024, row * 512, col * 1024 + 1024, row * 512 + 512), i)
    # 风吹日晒: 褪色, 底部更脏, 铁皮竖向锈痕
    a = np.asarray(im, dtype=np.float32)
    streak_src = RNG.normal(128, 50, (10, S // 6)).clip(0, 255).astype(np.uint8)
    streak = np.asarray(Image.fromarray(streak_src).resize((S, S), Image.BICUBIC), dtype=np.float32)[..., None] - 128
    a = a * 0.62 + 8 + streak * 0.22 + periodic_noise(S, 48)[..., None] * 34 - 17 + RNG.normal(0, 4, (S, S, 1))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(TEX, "yn_shutter_art_2k.jpg"), quality=92)


def text(d, box, s, size, fill):
    f = ImageFont.truetype(FONT, size)
    bb = d.textbbox((0, 0), s, font=f)
    d.text(((box[0] + box[2] - (bb[2] - bb[0])) / 2 - bb[0], (box[1] + box[3] - (bb[3] - bb[1])) / 2 - bb[1]), s, font=f, fill=fill)


def plaque():
    """吊牌: 深红边 + 白底黑字。街名, 一面从右往左读, 和参考图一样。"""
    W, H = 1024, 256
    im = Image.new("RGB", (W, H * 2), (120, 34, 24))
    d = ImageDraw.Draw(im)
    for row, s in enumerate(("仲見世", "世見仲")):
        y = row * H
        d.rectangle((0, y, W, y + H), fill=(116, 30, 22))
        d.rounded_rectangle((26, y + 26, W - 26, y + H - 26), 60, fill=(226, 220, 204))
        text(d, (60, y + 22, W - 60, y + H - 22), s, 176, (24, 22, 20))
    a = np.asarray(im, dtype=np.float32) + RNG.normal(0, 3, (H * 2, W, 1))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(TEX, "yn_plaque_1k.png"))


if __name__ == "__main__":
    kawara()
    trim()
    shutter_art()
    plaque()
    print("reference textures done")
