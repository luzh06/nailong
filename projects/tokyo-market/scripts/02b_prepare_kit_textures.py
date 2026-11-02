"""第 4 步贴图: 招牌图集, 暖帘图集, 道具图集, 城市立面, 污渍。全部程序生成, 文字来自 kit_atlas。"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_atlas as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
FONT = os.path.join(ROOT, "fonts", "ZenAntique-Regular.ttf")
RNG = np.random.default_rng(23)


def font(size):
    return ImageFont.truetype(FONT, size)


def center_text(d, box, text, size, fill):
    f = font(size)
    bb = d.textbbox((0, 0), text, font=f)
    d.text(((box[0] + box[2] - (bb[2] - bb[0])) / 2 - bb[0], (box[1] + box[3] - (bb[3] - bb[1])) / 2 - bb[1]),
           text, font=f, fill=fill)


def fit_text(d, box, text, max_size, fill):
    """缩到能放进框里, 再居中。"""
    size = max_size
    while size > 12:
        bb = d.textbbox((0, 0), text, font=font(size))
        if bb[2] - bb[0] <= box[2] - box[0] and bb[3] - bb[1] <= box[3] - box[1]:
            break
        size -= 2
    center_text(d, box, text, size, fill)


def vertical(d, box, text, size, fill, spacing=1.04):
    f = font(size)
    total = len(text) * size * spacing
    y = (box[1] + box[3] - total) / 2
    for ch in text:
        bb = d.textbbox((0, 0), ch, font=f)
        d.text(((box[0] + box[2] - (bb[2] - bb[0])) / 2 - bb[0], y + (size * spacing - (bb[3] - bb[1])) / 2 - bb[1]),
               ch, font=f, fill=fill)
        y += size * spacing


def aged(im, strength=7, stain=0.14):
    a = np.asarray(im, dtype=np.float32)
    h, w = a.shape[:2]
    fine = RNG.normal(0, strength, (h, w, 1))
    small = RNG.normal(128, 45, (max(h // 40, 2), max(w // 40, 2))).clip(0, 255).astype(np.uint8)
    coarse = np.asarray(Image.fromarray(small).resize((w, h), Image.BICUBIC), dtype=np.float32)[..., None] - 128
    return Image.fromarray(np.clip(a + fine + coarse * stain, 0, 255).astype(np.uint8))


# 参考图里整条街的檐板是统一的浅灰白底黑字, 只留很小的差别
BOARD_STYLES = [((168, 163, 148), (22, 20, 18)), ((156, 152, 138), (24, 20, 18)), ((176, 170, 154), (20, 18, 16))]


def goods_tile(d, j):
    x0, y0, x1, y1 = K.goods(j)
    if j == K.GOODS_SENBEI:
        d.rectangle((x0, y0, x1, y1), fill=(92, 62, 36))
        for _ in range(26):
            x, y = RNG.integers(x0, x1), RNG.integers(y0, y1)
            r, c = RNG.integers(20, 30), RNG.integers(150, 205)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(int(c), int(c * 0.72), int(c * 0.42)),
                      outline=(int(c * 0.6), int(c * 0.42), int(c * 0.24)), width=2)
    elif j == K.GOODS_SWEETS:
        d.rectangle((x0, y0, x1, y1), fill=(120, 92, 62))
        for _ in range(34):
            x, y = RNG.integers(x0, x1), RNG.integers(y0, y1)
            r, c = RNG.integers(13, 20), RNG.integers(170, 225)
            d.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=(int(c), int(c * 0.78), int(c * 0.52)),
                      outline=(int(c * 0.65), int(c * 0.46), int(c * 0.28)), width=2)
    elif j in (K.GOODS_PACK_WARM, K.GOODS_PACK_COOL):
        palette = [(138, 58, 46), (176, 150, 92), (204, 196, 176)] if j == K.GOODS_PACK_WARM else \
            [(62, 76, 66), (70, 86, 110), (204, 196, 176)]
        n = 4
        for iy in range(n):
            for ix in range(n):
                c = palette[int(RNG.integers(0, 3))]
                d.rectangle((x0 + ix * 64 + 3, y0 + iy * 64 + 3, x0 + ix * 64 + 61, y0 + iy * 64 + 61), fill=c)
                d.rectangle((x0 + ix * 64 + 10, y0 + iy * 64 + 16, x0 + ix * 64 + 54, y0 + iy * 64 + 36),
                            fill=tuple(min(255, v + 46) for v in c))
    elif j == K.GOODS_FANS:
        d.rectangle((x0, y0, x1, y1), fill=(40, 34, 30))
        for iy in range(3):
            for ix in range(3):
                cx, cy = x0 + 42 + ix * 86, y0 + 62 + iy * 84
                c = [(170, 62, 48), (56, 78, 110), (206, 192, 150), (66, 96, 80)][int(RNG.integers(0, 4))]
                d.pieslice((cx - 38, cy - 38, cx + 38, cy + 38), 200, 340, fill=c, outline=(24, 20, 18))
    elif j == K.GOODS_CLOTH:
        for ix in range(8):
            c = [(36, 56, 90), (196, 188, 168), (120, 44, 38), (70, 96, 84), (160, 130, 76)][int(RNG.integers(0, 5))]
            d.rectangle((x0 + ix * 32, y0, x0 + ix * 32 + 30, y1), fill=c)
            for y in range(y0 + 8, y1, 26):
                d.line((x0 + ix * 32 + 4, y, x0 + ix * 32 + 26, y), fill=tuple(min(255, v + 60) for v in c), width=2)
    elif j == K.GOODS_TOYS:
        d.rectangle((x0, y0, x1, y1), fill=(70, 50, 36))
        for _ in range(16):
            x, y = RNG.integers(x0 + 20, x1 - 20), RNG.integers(y0 + 20, y1 - 20)
            r = RNG.integers(20, 34)
            c = [(176, 58, 44), (214, 174, 70), (66, 104, 130), (220, 210, 190), (76, 118, 84)][int(RNG.integers(0, 5))]
            d.ellipse((x - r, y - r, x + r, y + r), fill=c, outline=(30, 24, 20), width=2)
            d.line((x - r, y, x + r, y), fill=(236, 226, 200), width=2)
    else:
        d.rectangle((x0, y0, x1, y1), fill=(92, 42, 44))
        for _ in range(60):
            x, y = RNG.integers(x0, x1), RNG.integers(y0, y1)
            r = RNG.integers(5, 14)
            c = [(214, 176, 176), (200, 90, 80), (226, 214, 180), (110, 130, 110)][int(RNG.integers(0, 4))]
            d.ellipse((x - r, y - r, x + r, y + r), fill=c)


def signs_atlas():
    im = Image.new("RGB", (2048, 2048), (60, 56, 50))
    d = ImageDraw.Draw(im)
    for i, (name, mark, board_text, _, _) in enumerate(K.SHOPS):
        # 横板
        x0, y0, x1, y1 = K.board(i)
        bg, fg = BOARD_STYLES[i % len(BOARD_STYLES)]
        d.rectangle((x0, y0, x1, y1), fill=bg)
        for x in range(x0 + 256, x1, 256):
            d.line((x, y0, x, y1), fill=tuple(int(v * 0.72) for v in bg), width=2)
        fit_text(d, (x0 + 170, y0 + 8, x1 - 40, y1 - 8), board_text, 96, fg)
        # 左端的圆形店徽, 平视图里每家都有
        d.ellipse((x0 + 34, y0 + 12, x0 + 138, y0 + 116), fill=(26, 24, 22))
        center_text(d, (x0 + 34, y0 + 12, x0 + 138, y0 + 116), mark, 62, bg)
        # 吊牌: 白底黑字, 青绿盖
        x0, y0, x1, y1 = K.plaque(i)
        d.rectangle((x0, y0, x1, y1), fill=(222, 216, 200))
        d.rectangle((x0, y0, x1, y0 + 18), fill=(38, 92, 84))
        d.line((x0, y1 - 1, x1, y1 - 1), fill=(60, 56, 50), width=2)
        d.ellipse((x1 - 92, y0 + 34, x1 - 22, y0 + 104), outline=(30, 28, 26), width=4)
        center_text(d, (x1 - 92, y0 + 34, x1 - 22, y0 + 104), mark, 44, (30, 28, 26))
        fit_text(d, (x0 + 20, y0 + 24, x1 - 104, y1 - 6), name, 84, (24, 22, 21))
    for j in range(8):
        goods_tile(d, j)
    aged(im).save(os.path.join(TEX, "yn_signs_basecolor_2k.png"))


NOREN_COLORS = [((27, 44, 74), (232, 228, 214)), ((96, 30, 28), (236, 226, 204)), ((36, 58, 52), (230, 224, 204)),
                ((210, 202, 182), (30, 40, 66)), ((54, 40, 66), (232, 226, 210))]


def split_noren(text):
    """暖帘中幅和右幅各放一列字; 竖排从右往左读, 右幅放前半。"""
    n = len(text)
    k = (n + 1) // 2
    return text[:k], text[k:]


def noren_atlas():
    im = Image.new("RGB", (2048, 2048), (20, 20, 30))
    d = ImageDraw.Draw(im)
    for i, (_, mark, _, text, _) in enumerate(K.SHOPS):
        x0, y0, x1, y1 = K.noren(i)
        bg, fg = NOREN_COLORS[i % len(NOREN_COLORS)]
        d.rectangle((x0, y0, x1, y1), fill=bg)
        pw = (x1 - x0) / 3
        for k in (1, 2):
            d.line((x0 + k * pw, y0, x0 + k * pw, y1), fill=tuple(int(v * 0.6) for v in bg), width=3)
        # 左幅店徽
        cx, cy = x0 + pw / 2, (y0 + y1) / 2
        d.ellipse((cx - 88, cy - 88, cx + 88, cy + 88), outline=fg, width=7)
        center_text(d, (cx - 88, cy - 88, cx + 88, cy + 88), mark, 112, fg)
        right, mid = split_noren(text)
        size = 104 if max(len(right), len(mid)) <= 2 else 72
        vertical(d, (x0 + 2 * pw, y0, x1, y1), right, size, fg)
        if mid:
            vertical(d, (x0 + pw, y0, x0 + 2 * pw, y1), mid, size, fg)
    aged(im, 6, 0.1).save(os.path.join(TEX, "yn_noren_basecolor_2k.png"))


def props_atlas():
    im = Image.new("RGB", (1024, 1024), (70, 66, 60))
    d = ImageDraw.Draw(im)
    # 贩卖机正面: 无品牌, 上部陈列窗 + 取物口
    x0, y0, x1, y1 = K.VENDING_FRONT
    d.rectangle((x0, y0, x1, y1), fill=(214, 216, 214))
    d.rectangle((x0 + 28, y0 + 40, x1 - 28, y0 + 620), fill=(232, 236, 232))
    colors = [(170, 52, 44), (54, 88, 134), (220, 196, 96), (66, 120, 86), (232, 232, 226), (120, 74, 44)]
    for row in range(4):
        d.rectangle((x0 + 40, y0 + 52 + row * 142 + 112, x1 - 40, y0 + 52 + row * 142 + 124), fill=(150, 152, 150))
        for col in range(6):
            cx = x0 + 70 + col * 74
            cy = y0 + 56 + row * 142
            c = colors[int(RNG.integers(0, 6))]
            d.rounded_rectangle((cx - 22, cy + 12, cx + 22, cy + 110), 9, fill=c, outline=(40, 40, 40))
            d.rectangle((cx - 22, cy + 46, cx + 22, cy + 78), fill=tuple(min(255, v + 56) for v in c))
    label = (x0 + 30, y0 + 628, x1 - 30, y0 + 690)
    d.rectangle(label, fill=(34, 74, 136))
    center_text(d, label, K.PROP_TEXTS[0][0] + " · " + K.PROP_TEXTS[2][0], 40, (236, 236, 230))
    d.rectangle((x0 + 330, y0 + 710, x1 - 40, y0 + 820), fill=(52, 54, 56))
    d.rectangle((x0 + 40, y0 + 860, x1 - 40, y0 + 970), fill=(24, 24, 26))
    d.rectangle((x0 + 60, y0 + 880, x1 - 60, y0 + 950), fill=(44, 44, 46))
    for x in (x0 + 60, x0 + 110, x0 + 160, x0 + 210):
        d.ellipse((x, y0 + 730, x + 34, y0 + 764), fill=(180, 180, 176), outline=(40, 40, 40))
    center_text(d, (x0 + 40, y0 + 775, x0 + 310, y0 + 835), K.PROP_TEXTS[1][0], 34, (160, 46, 36))

    # 立式看板两种
    for (x0, y0, x1, y1), text, bg, fg in (
            (K.STAND_SIGN[0], K.PROP_TEXTS[3][0], (42, 44, 40), (230, 226, 208)),
            (K.STAND_SIGN[1], K.PROP_TEXTS[4][0], (206, 196, 172), (120, 34, 28))):
        d.rectangle((x0, y0, x1, y1), fill=bg)
        d.rectangle((x0 + 12, y0 + 12, x1 - 12, y1 - 12), outline=fg, width=4)
        size = 46 if len(text) <= 4 else 34
        vertical(d, (x0, y0, x1, y1), text, size, fg)

    # 布雨棚条纹两种
    for (x0, y0, x1, y1), a, b in ((K.STRIPES[0], (120, 40, 34), (214, 204, 182)),
                                   (K.STRIPES[1], (42, 62, 72), (206, 196, 172))):
        for i, x in enumerate(range(x0, x1, 32)):
            d.rectangle((x, y0, x + 32, y1), fill=a if i % 2 == 0 else b)
    # 红色旗幡
    x0, y0, x1, y1 = K.BANNER
    d.rectangle((x0, y0, x1, y1), fill=(148, 36, 30))
    aged(im, 5, 0.1).save(os.path.join(TEX, "yn_props_basecolor_1k.png"))


def city_facade():
    """远景楼立面: 9x9 米一格, 3 层 6 开间, 窗小一些、有疏有密, 再出一张亮窗贴图。"""
    S = 1024
    base = Image.new("RGB", (S, S), (160, 156, 148))
    emit = Image.new("RGB", (S, S), (0, 0, 0))
    db, de = ImageDraw.Draw(base), ImageDraw.Draw(emit)
    rows, cols = 3, 6
    ch, cw = S // rows, S // cols
    for iy in range(rows):
        db.rectangle((0, iy * ch, S, iy * ch + 14), fill=(134, 130, 122))
        for ix in range(cols):
            if RNG.random() < 0.22:
                continue  # 有的开间没有窗
            mw = int(RNG.integers(26, 46))
            x0, y0 = ix * cw + mw, iy * ch + 96
            x1, y1 = (ix + 1) * cw - mw, (iy + 1) * ch - 76
            db.rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), fill=(96, 92, 88))
            db.rectangle((x0, y0, x1, y1), fill=(46, 50, 56))
            if RNG.random() < 0.2:
                c = (int(RNG.integers(200, 255)), int(RNG.integers(140, 190)), int(RNG.integers(80, 130)))
                de.rectangle((x0, y0, x1, y1), fill=c)
    aged(base, 4, 0.1).save(os.path.join(TEX, "yn_city_facade_basecolor_1k.jpg"), quality=90)
    emit.save(os.path.join(TEX, "yn_city_facade_emissive_1k.jpg"), quality=90)


def grime():
    """透明污渍: 上方密, 向下淡, 带竖向流痕。用在檐下和墙角。"""
    S = 1024
    small = RNG.normal(0.5, 0.25, (S // 64, S // 8)).clip(0, 1)
    streak = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC),
                        dtype=np.float32) / 255
    fall = np.linspace(1.0, 0.0, S)[:, None] ** 1.6
    alpha = np.clip(streak * 1.3 - 0.15, 0, 1) * fall * 0.75
    rgba = np.zeros((S, S, 4), dtype=np.uint8)
    rgba[..., :3] = (26, 22, 18)
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(os.path.join(TEX, "yn_grime_1k.png"))

    # 地面水渍: 中心密, 边缘淡
    yy, xx = np.mgrid[-1:1:S * 1j, -1:1:S * 1j]
    r = np.sqrt(xx ** 2 + yy ** 2)
    blob = RNG.normal(0.5, 0.3, (S // 32, S // 32)).clip(0, 1)
    noise = np.asarray(Image.fromarray((blob * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC),
                       dtype=np.float32) / 255
    alpha = np.clip((noise * 1.1 - 0.2) * np.clip(1.0 - r, 0, 1) * 0.7, 0, 0.26)
    rgba[..., :3] = (20, 19, 18)
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(os.path.join(TEX, "yn_ground_stain_1k.png"))


if __name__ == "__main__":
    signs_atlas()
    noren_atlas()
    props_atlas()
    city_facade()
    grime()
    print("kit textures done")
