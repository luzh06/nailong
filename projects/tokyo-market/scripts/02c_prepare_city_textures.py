"""打磨阶段的贴图: 四种楼立面 (各带亮窗图), 背景招牌图集, 行人调色板。"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_atlas as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
FONT = os.path.join(ROOT, "fonts", "ZenAntique-Regular.ttf")
RNG = np.random.default_rng(77)


def font(size):
    return ImageFont.truetype(FONT, size)


def noise(im, strength, stain):
    a = np.asarray(im, dtype=np.float32)
    h, w = a.shape[:2]
    fine = RNG.normal(0, strength, (h, w, 1))
    small = RNG.normal(128, 45, (h // 24, w // 24)).clip(0, 255).astype(np.uint8)
    coarse = np.asarray(Image.fromarray(small).resize((w, h), Image.BICUBIC), dtype=np.float32)[..., None] - 128
    # 雨水从窗台和腰线往下流的竖向脏痕
    streak_src = RNG.normal(128, 50, (8, w // 8)).clip(0, 255).astype(np.uint8)
    streak = np.asarray(Image.fromarray(streak_src).resize((w, h), Image.BICUBIC), dtype=np.float32)[..., None] - 128
    return Image.fromarray(np.clip(a + fine + coarse * stain + streak * stain * 0.8, 0, 255).astype(np.uint8))


def facade(name, wall, band, cols, win_h, win_top, sash, lit_rate, extras=None):
    """9x9 米一格, 3 层。贴图上下必须能接上, 所以层线画在格子顶上。"""
    S = 1024
    base = Image.new("RGB", (S, S), wall)
    emit = Image.new("RGB", (S, S), (0, 0, 0))
    db, de = ImageDraw.Draw(base), ImageDraw.Draw(emit)
    ch = S // 3
    cw = S / cols
    if extras:
        extras(db, S)
    for iy in range(3):
        db.rectangle((0, iy * ch, S, iy * ch + 13), fill=band)
        for ix in range(cols):
            if RNG.random() < 0.16:
                continue
            mw = int(RNG.integers(int(cw * 0.15), int(cw * 0.26)))
            x0, x1 = int(ix * cw + mw), int((ix + 1) * cw - mw)
            y0 = iy * ch + win_top
            y1 = y0 + win_h
            db.rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 8), fill=tuple(int(v * 0.62) for v in wall))
            glass = int(RNG.integers(36, 62))
            db.rectangle((x0, y0, x1, y1), fill=(glass, glass + 4, glass + 10))
            # 窗帘, 让每扇窗不一样
            if RNG.random() < 0.45:
                c = int(RNG.integers(120, 190))
                db.rectangle((x0, y0, x0 + int((x1 - x0) * RNG.uniform(0.25, 0.6)), y1), fill=(c, c - 8, c - 20))
            for k in range(1, sash):
                x = x0 + (x1 - x0) * k // sash
                db.line((x, y0, x, y1), fill=tuple(int(v * 0.5) for v in wall), width=4)
                de.line((x, y0, x, y1), fill=(0, 0, 0), width=4)
            if RNG.random() < lit_rate:
                r = int(RNG.integers(205, 255))
                de.rectangle((x0, y0, x1, y1), fill=(r, int(r * RNG.uniform(0.62, 0.78)), int(r * RNG.uniform(0.34, 0.5))))
                for k in range(1, sash):
                    x = x0 + (x1 - x0) * k // sash
                    de.line((x, y0, x, y1), fill=(0, 0, 0), width=4)
    noise(base, 3, 0.09).save(os.path.join(TEX, f"yn_facade_{name}_basecolor_1k.jpg"), quality=90)
    emit.save(os.path.join(TEX, f"yn_facade_{name}_emissive_1k.jpg"), quality=90)


def tile_lines(d, S):
    for y in range(0, S, 15):
        d.line((0, y, S, y), fill=(150, 142, 128), width=1)
    for x in range(0, S, 30):
        d.line((x, 0, x, S), fill=(160, 152, 138), width=1)


def brick_lines(d, S):
    for i, y in enumerate(range(0, S, 12)):
        d.line((0, y, S, y), fill=(92, 62, 50), width=2)
        for x in range(i % 2 * 13, S, 26):
            d.line((x, y, x, y + 12), fill=(92, 62, 50), width=1)


def panel_lines(d, S):
    for x in range(0, S, 128):
        d.line((x, 0, x, S), fill=(120, 120, 118), width=2)


def center(d, box, text, size, fill):
    f = font(size)
    bb = d.textbbox((0, 0), text, font=f)
    d.text(((box[0] + box[2] - (bb[2] - bb[0])) / 2 - bb[0], (box[1] + box[3] - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=fill)


def vertical(d, box, text, size, fill):
    f = font(size)
    total = len(text) * size * 1.06
    y = (box[1] + box[3] - total) / 2
    for ch in text:
        bb = d.textbbox((0, 0), ch, font=f)
        d.text(((box[0] + box[2] - (bb[2] - bb[0])) / 2 - bb[0], y + (size * 1.06 - (bb[3] - bb[1])) / 2 - bb[1]), ch, font=f, fill=fill)
        y += size * 1.06


def citysigns():
    im = Image.new("RGB", (1024, 1024), (20, 20, 22))
    d = ImageDraw.Draw(im)
    styles = [((232, 226, 206), (30, 26, 22)), ((172, 40, 30), (244, 232, 204)), ((36, 58, 112), (240, 236, 220)),
              ((226, 182, 60), (40, 28, 18)), ((236, 236, 236), (34, 80, 150)), ((44, 90, 62), (238, 232, 210)),
              ((30, 28, 28), (236, 190, 90)), ((206, 64, 42), (250, 240, 210))]
    for i, word in enumerate(K.CITY_WORDS):
        x0, y0, x1, y1 = K.city_sign(i)
        bg, fg = styles[i]
        d.rectangle((x0 + 4, y0 + 4, x1 - 4, y1 - 4), fill=bg)
        d.rectangle((x0 + 12, y0 + 12, x1 - 12, y1 - 12), outline=fg, width=3)
        size = min(92, int(470 / max(len(word), 1) / 1.1))
        vertical(d, (x0, y0 + 10, x1, y1 - 10), word, size, fg)
    for i, word in enumerate(K.BILLBOARD_WORDS):
        x0, y0, x1, y1 = K.billboard(i)
        bg, fg = ((222, 110, 40), (40, 24, 18)) if i == 0 else ((230, 226, 210), (120, 34, 28))
        d.rectangle((x0 + 4, y0 + 4, x1 - 4, y1 - 4), fill=bg)
        d.rectangle((x0 + 14, y0 + 14, x1 - 14, y1 - 14), outline=fg, width=5)
        center(d, (x0, y0, x1, y1), word, 190, fg)
    # 远景店面: 暗的店内 + 亮的货架和暖帘色块
    for i in range(4):
        x0, y0, x1, y1 = K.lod_front(i)
        d.rectangle((x0, y0, x1, y1), fill=(46, 32, 22))
        for row in range(3):
            yy = y1 - 40 - row * 56
            d.rectangle((x0 + 10, yy, x1 - 10, yy + 6), fill=(92, 64, 40))
            x = x0 + 14
            while x < x1 - 24:
                w = int(RNG.integers(10, 26))
                h = int(RNG.integers(18, 40))
                c = [(186, 150, 90), (160, 60, 44), (210, 200, 176), (70, 96, 84), (72, 86, 120)][int(RNG.integers(0, 5))]
                d.rectangle((x, yy - h, x + w, yy), fill=c)
                x += w + int(RNG.integers(3, 8))
        c = [(27, 44, 74), (96, 30, 28), (36, 58, 52), (210, 202, 182)][i]
        d.rectangle((x0 + 4, y0 + 4, x1 - 4, y0 + 72), fill=c)
        for x in range(x0 + 4, x1, 80):
            d.line((x, y0 + 4, x, y0 + 72), fill=tuple(int(v * 0.6) for v in c), width=3)
        d.rectangle((x0 + 2, y0, x1 - 2, y0 + 4), fill=(240, 216, 170))
    noise(im, 3, 0.05).save(os.path.join(TEX, "yn_citysigns_1k.png"))


def people_palette():
    """8x8 调色板: 0-1 肤色, 2-4 发色, 5 鞋, 6-7 包, 8-19 衣服, 20-23 裤子。191 是冬天, 外套偏深, 夹几件亮色。"""
    cells = [(214, 170, 140), (196, 150, 120), (22, 18, 16), (38, 30, 26), (92, 72, 58), (28, 26, 26), (70, 48, 34), (150, 130, 106),
             (32, 34, 38), (46, 48, 56), (26, 28, 34), (70, 66, 62), (110, 100, 88), (150, 142, 128), (36, 52, 84), (58, 74, 92),
             (150, 40, 34), (196, 170, 120), (214, 208, 196), (96, 44, 52), (28, 30, 40), (48, 50, 58), (72, 66, 60), (112, 104, 94)]
    S = 8
    im = Image.new("RGB", (S * 16, S * 16), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, c in enumerate(cells):
        x, y = i % S, i // S
        d.rectangle((x * 16, y * 16, x * 16 + 15, y * 16 + 15), fill=c)
    im.save(os.path.join(TEX, "yn_people_palette.png"))


def red_roof():
    """191 左侧的红瓦: 由灰瓦原图染色, 不是新素材。"""
    src = np.asarray(Image.open(os.path.join(TEX, "grey_roof_tiles_02_diff_2k.jpg")).convert("RGB"), dtype=np.float32) / 255
    lum = (src * [0.2126, 0.7152, 0.0722]).sum(axis=2, keepdims=True)
    out = lum ** 1.1 * np.array([0.95, 0.36, 0.28], dtype=np.float32)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(os.path.join(TEX, "yn_roof_red_basecolor_2k.jpg"), quality=92)


if __name__ == "__main__":
    red_roof()
    facade("plaster", (176, 170, 158), (140, 134, 124), 4, 150, 92, 2, 0.2)
    facade("tile", (188, 178, 160), (150, 142, 128), 3, 170, 76, 3, 0.22, tile_lines)
    facade("concrete", (134, 134, 132), (104, 104, 102), 5, 190, 62, 2, 0.26, panel_lines)
    facade("brick", (136, 86, 68), (112, 104, 92), 4, 160, 84, 2, 0.2, brick_lines)
    citysigns()
    people_palette()
    print("city textures done")
