"""真实感贴图: 实拍卷帘图集 (自用, 直接取自 reference/web 的照片并做透视校正), 窗户图集。"""
import os

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
WEB = os.path.join(ROOT, "reference", "web")
RNG = np.random.default_rng(5)
THUMB_W = 1200.0  # 下面的四边形坐标是在 1200 宽的缩略图上量的


def rectify(name, quad, size):
    """quad: 左上, 右上, 右下, 左下。"""
    im = Image.open(os.path.join(WEB, name)).convert("RGB")
    k = im.width / THUMB_W
    src = [(x * k, y * k) for x, y in quad]
    w, h = size
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([u, v, 1, 0, 0, 0, -x * u, -x * v])
        A.append([0, 0, 0, u, v, 1, -y * u, -y * v])
        B += [x, y]
    coef = np.linalg.solve(np.array(A, dtype=np.float64), np.array(B, dtype=np.float64))
    return im.transform(size, Image.PERSPECTIVE, tuple(coef), Image.BICUBIC)


def normalize(im, target=118):
    """夜景照片压暗了, 拉回白天贴图该有的亮度, 同时把偏黄的灯光色去掉一些。"""
    a = np.asarray(im, dtype=np.float32)
    mean = a.reshape(-1, 3).mean(axis=0)
    a = a * (mean.mean() / mean)[None, None] * 0.5 + a * 0.5
    a = a * (target / a.mean())
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def shutter_atlas():
    S = 2048
    W, H = 1024, 512
    quads = [
        ("web_12.jpg", [(100, 90), (720, 90), (720, 770), (100, 770)]),
        ("web_12.jpg", [(720, 95), (1195, 95), (1195, 790), (720, 790)]),
        ("web_07.jpg", [(14, 306), (118, 320), (116, 585), (10, 628)]),
        ("web_07.jpg", [(135, 322), (212, 332), (210, 548), (133, 580)]),
        ("web_07.jpg", [(1090, 316), (1198, 298), (1198, 640), (1090, 592)]),
        ("web_06.jpg", [(4, 352), (122, 355), (122, 598), (4, 600)]),
        ("web_06.jpg", [(926, 352), (986, 346), (986, 560), (926, 532)]),
        ("web_06.jpg", [(1098, 374), (1198, 372), (1198, 610), (1098, 590)]),
    ]
    sheet = Image.new("RGB", (S, S))
    for i, (name, q) in enumerate(quads):
        cell = normalize(rectify(name, q, (W, H)))
        sheet.paste(cell, ((i % 2) * W, (i // 2) * H))
    sheet.save(os.path.join(TEX, "yn_shutter_art_2k.jpg"), quality=93)


def window_atlas():
    """8x8 格。底图是暗玻璃加窗帘/百叶, 亮窗图是里面开灯的样子。"""
    S, N = 1024, 8
    c = S // N
    base = Image.new("RGB", (S, S), (20, 22, 26))
    emit = Image.new("RGB", (S, S), (0, 0, 0))
    db, de = ImageDraw.Draw(base), ImageDraw.Draw(emit)
    for iy in range(N):
        for ix in range(N):
            x0, y0, x1, y1 = ix * c, iy * c, (ix + 1) * c - 1, (iy + 1) * c - 1
            kind = RNG.integers(0, 4)
            lit = RNG.random() < 0.34
            warm = (int(RNG.integers(225, 255)), int(RNG.integers(165, 205)), int(RNG.integers(95, 140)))
            if lit and RNG.random() < 0.2:
                warm = (232, 236, 228)  # 日光灯
            if lit:
                de.rectangle((x0, y0, x1, y1), fill=warm)
            if kind == 1:  # 半拉窗帘
                w = int(c * RNG.uniform(0.25, 0.6))
                col = int(RNG.integers(120, 190))
                db.rectangle((x0, y0, x0 + w, y1), fill=(col, col - 6, col - 18))
                if lit:
                    de.rectangle((x0, y0, x0 + w, y1), fill=tuple(int(v * 0.6) for v in warm))
                for x in range(x0, x0 + w, 9):
                    db.line((x, y0, x, y1), fill=(col - 28, col - 34, col - 44), width=2)
            elif kind == 2:  # 百叶
                col = int(RNG.integers(110, 170))
                bottom = y0 + int(c * RNG.uniform(0.4, 0.8))
                for y in range(y0, bottom, 7):
                    db.line((x0, y, x1, y), fill=(col, col, col - 6), width=4)
                    if lit:
                        de.line((x0, y + 4, x1, y + 4), fill=(0, 0, 0), width=4)
            # 窗扇中梃和外框
            xm = (x0 + x1) // 2
            for d in (db, de):
                d.line((xm, y0, xm, y1), fill=(10, 10, 10) if d is de else (88, 90, 92), width=5)
                d.rectangle((x0, y0, x1, y1), outline=(10, 10, 10) if d is de else (96, 98, 100), width=5)
    base.save(os.path.join(TEX, "yn_window_basecolor_1k.jpg"), quality=92)
    emit.save(os.path.join(TEX, "yn_window_emissive_1k.jpg"), quality=92)


if __name__ == "__main__":
    shutter_atlas()
    window_atlas()
    print("realism textures done")
