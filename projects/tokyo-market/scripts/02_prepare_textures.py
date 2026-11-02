"""由 Poly Haven 原图调色出项目贴图, 生成虚构招牌图集, 裁出参考图。
用法: python 02_prepare_textures.py <F:\\东京 路径>
"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
REF = os.path.join(ROOT, "reference")
FONT = os.path.join(ROOT, "fonts", "ZenAntique-Regular.ttf")

# 所有招牌文字集中在这里, 同步抄到 japanese-text-list.csv 等人工核实
SHOP_NAME = "朝凪屋"
GOODS = "手焼きせんべい"
NOREN = "せんべい"
LANTERN = "朝凪"
PACK_A = "あられ"
PACK_B = "ざらめ"


def load(name):
    return np.asarray(Image.open(os.path.join(TEX, name)).convert("RGB"), dtype=np.float32) / 255.0


def save(arr, name, size=None, quality=92):
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    if size:
        im = im.resize((size, size), Image.LANCZOS)
    im.save(os.path.join(TEX, name), quality=quality)


def lum(a):
    return (a * [0.2126, 0.7152, 0.0722]).sum(axis=2, keepdims=True)


def grade():
    # 朱红涂装: 保留原图的掉漆, 涂层部分染朱红
    src = load("distressed_painted_planks_diff_2k.jpg")
    l = lum(src)
    detail = l / l.mean()
    paint = np.array([0.56, 0.17, 0.10], dtype=np.float32) * detail
    # 原图橙色掉漆处露出暗木色
    chip = np.clip((src[..., 0:1] - src[..., 2:3]) * 6 - 0.45, 0, 1)
    wood = np.array([0.25, 0.15, 0.10], dtype=np.float32) * detail
    save(paint * (1 - chip) + wood * chip, "yn_vermilion_basecolor_2k.jpg")

    # 瓦: 压暗成接近例图的黑灰
    src = load("grey_roof_tiles_02_diff_2k.jpg")
    save(lum(src) ** 1.25 * np.array([0.42, 0.43, 0.46], dtype=np.float32), "yn_roof_basecolor_2k.jpg")

    # 老木: 把偏橙的雪松压成深褐
    src = load("japanese_cedar_planks_diff_2k.jpg")
    save(lum(src) ** 1.3 * np.array([0.60, 0.42, 0.28], dtype=np.float32), "yn_cedar_basecolor_2k.jpg")

    # 卷帘门: 略偏暖的旧铁灰
    src = load("painted_metal_shutter_diff_2k.jpg")
    save(lum(src) * np.array([0.92, 0.88, 0.80], dtype=np.float32), "yn_shutter_basecolor_1k.jpg", 1024)

    # 灰浆和铁皮: 仅降到 1K
    save(load("plastered_wall_02_diff_2k.jpg"), "yn_plaster_basecolor_1k.jpg", 1024)
    save(load("corrugated_iron_02_diff_2k.jpg"), "yn_corrugated_basecolor_1k.jpg", 1024)

    # 路面: 去掉偏棕, 接近例图的浅灰石板
    src = load("rectangular_paving_diff_2k.jpg")
    save(lum(src) * np.array([1.18, 1.14, 1.08], dtype=np.float32) * 1.15, "yn_paving_basecolor_2k.jpg")

    # 法线和 ORM: 重点材质保留 2K, 其余降到 1K
    keep_2k = {"distressed_painted_planks": "vermilion", "grey_roof_tiles_02": "roof",
               "japanese_cedar_planks": "cedar", "rectangular_paving": "paving"}
    to_1k = {"painted_metal_shutter": "shutter", "plastered_wall_02": "plaster",
             "corrugated_iron_02": "corrugated"}
    for asset, role in keep_2k.items():
        for src_key, dst_key in (("nor_gl", "normal"), ("arm", "orm")):
            Image.open(os.path.join(TEX, f"{asset}_{src_key}_2k.jpg")).save(
                os.path.join(TEX, f"yn_{role}_{dst_key}_2k.jpg"), quality=92)
    for asset, role in to_1k.items():
        for src_key, dst_key in (("nor_gl", "normal"), ("arm", "orm")):
            Image.open(os.path.join(TEX, f"{asset}_{src_key}_2k.jpg")).resize((1024, 1024), Image.LANCZOS).save(
                os.path.join(TEX, f"yn_{role}_{dst_key}_1k.jpg"), quality=92)


def text_center(d, box, text, size, fill, vertical=False, spacing=1.08):
    x0, y0, x1, y1 = box
    f = ImageFont.truetype(FONT, size)
    if vertical:
        total = len(text) * size * spacing
        y = (y0 + y1 - total) / 2
        for ch in text:
            bb = d.textbbox((0, 0), ch, font=f)
            d.text(((x0 + x1 - (bb[2] - bb[0])) / 2 - bb[0], y + (size * spacing - (bb[3] - bb[1])) / 2 - bb[1]),
                   ch, font=f, fill=fill)
            y += size * spacing
    else:
        bb = d.textbbox((0, 0), text, font=f)
        d.text(((x0 + x1 - (bb[2] - bb[0])) / 2 - bb[0], (y0 + y1 - (bb[3] - bb[1])) / 2 - bb[1]),
               text, font=f, fill=fill)


def aged(im, strength=10, seed=3):
    """加一点纸纤维和污渍, 免得招牌像电脑字。"""
    rng = np.random.default_rng(seed)
    a = np.asarray(im, dtype=np.float32)
    h, w = a.shape[:2]
    fine = rng.normal(0, strength, (h, w, 1))
    coarse = np.asarray(Image.fromarray(rng.normal(128, 40, (h // 32, w // 32)).clip(0, 255).astype(np.uint8))
                        .resize((w, h), Image.BICUBIC), dtype=np.float32)[..., None] - 128
    return Image.fromarray(np.clip(a + fine + coarse * 0.12, 0, 255).astype(np.uint8))


def signs():
    """2K 招牌图集。像素区块要和 build_shop_a.py 里的 ATLAS 一致。"""
    S = 2048
    im = Image.new("RGB", (S, S), (60, 58, 54))
    d = ImageDraw.Draw(im)

    # 吊牌 (0,0)-(1024,320): 白底黑字, 顶部青绿色盖
    d.rectangle((0, 0, 1024, 320), fill=(226, 221, 206))
    d.rectangle((0, 0, 1024, 44), fill=(38, 92, 84))
    d.ellipse((860, 92, 992, 224), outline=(30, 28, 26), width=9)
    text_center(d, (860, 92, 992, 224), "凪", 86, (30, 28, 26))
    text_center(d, (30, 50, 850, 318), SHOP_NAME, 215, (24, 22, 21))

    # 店头横板 (0,340)-(2048,660): 旧木底黑字
    d.rectangle((0, 340, 2048, 660), fill=(150, 112, 72))
    for x in range(0, 2048, 512):
        d.line((x, 340, x, 660), fill=(92, 66, 42), width=5)
    text_center(d, (40, 340, 2010, 660), GOODS, 245, (22, 18, 16))

    # 暖帘三幅 (0,680)-(1536,1240): 藏青底白字
    for i in range(3):
        x0, x1 = i * 512, (i + 1) * 512
        d.rectangle((x0, 680, x1, 1240), fill=(27, 44, 74))
        d.line((x1 - 2, 680, x1 - 2, 1240), fill=(16, 26, 46), width=4)
    d.ellipse((90, 800, 422, 1132), outline=(232, 228, 214), width=14)
    text_center(d, (90, 800, 422, 1132), "凪", 220, (232, 228, 214))
    # 竖排从右往左读: 右幅「せん」, 中幅「べい」, 左幅店徽
    text_center(d, (512, 680, 1024, 1240), NOREN[2:], 225, (232, 228, 214), vertical=True)
    text_center(d, (1024, 680, 1536, 1240), NOREN[:2], 225, (232, 228, 214), vertical=True)

    # 商品包装 4 种 (1536,680)-(2048,1192), 每格 256
    packs = [((138, 58, 46), (226, 218, 198), PACK_A), ((176, 150, 92), (50, 36, 26), PACK_B),
             ((204, 196, 176), (120, 44, 36), PACK_A), ((62, 76, 66), (214, 208, 188), PACK_B)]
    for i, (bg, fg, label) in enumerate(packs):
        x0, y0 = 1536 + (i % 2) * 256, 680 + (i // 2) * 256
        d.rectangle((x0, y0, x0 + 256, y0 + 256), fill=bg)
        d.rectangle((x0 + 14, y0 + 14, x0 + 242, y0 + 242), outline=fg, width=5)
        text_center(d, (x0, y0, x0 + 256, y0 + 256), label, 66, fg, vertical=True, spacing=1.02)

    # 木盒里的仙贝 (0,1260)-(1024,1772): 程序画的圆饼
    d.rectangle((0, 1260, 1024, 1772), fill=(92, 62, 36))
    rng = np.random.default_rng(11)
    for _ in range(90):
        x, y = rng.integers(0, 1024), rng.integers(1260, 1772)
        r = rng.integers(42, 62)
        c = rng.integers(150, 205)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(int(c), int(c * 0.72), int(c * 0.42)),
                  outline=(int(c * 0.6), int(c * 0.42), int(c * 0.24)), width=4)

    aged(im).save(os.path.join(TEX, "yn_shop_a_signs_basecolor_2k.png"))

    # 灯笼 512: 红纸黑字, 同时作自发光贴图
    lan = Image.new("RGB", (512, 512), (178, 30, 22))
    ld = ImageDraw.Draw(lan)
    for y in range(0, 512, 26):
        ld.line((0, y, 512, y), fill=(140, 22, 16), width=3)
    # 文字画在单独一层再压窄, 否则绕灯笼一圈后会被拉宽; 前后各一组
    txt = Image.new("L", (512, 512), 0)
    text_center(ImageDraw.Draw(txt), (0, 0, 512, 512), LANTERN, 200, 255, vertical=True, spacing=1.0)
    txt = txt.resize((180, 512), Image.LANCZOS)
    for cx in (128, 384):
        lan.paste((24, 16, 14), (cx - 90, 0), txt)
    aged(lan, 6).save(os.path.join(TEX, "yn_lantern_basecolor_512.png"))


def refs(src_dir):
    # 去掉手机截图的状态栏和按钮, 只留原照片部分 (边界按截图目测)
    crops = {"191": ("ref_191_dusk.jpg", 543, 2330), "189": ("ref_189_day.jpg", 320, 2298)}
    for k, (name, y0, y1) in crops.items():
        path = [p for p in glob.glob(os.path.join(src_dir, "*.png"))
                if f"_{k}_" in p and not os.path.basename(p).startswith("._")][0]
        im = Image.open(path).convert("RGB")
        im.crop((0, y0, im.width, y1)).save(os.path.join(REF, name), quality=92)
        print(name, im.width, y1 - y0)


if __name__ == "__main__":
    grade()
    signs()
    refs(sys.argv[1])
    print("done")
