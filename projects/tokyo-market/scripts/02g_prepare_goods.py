"""店内货品图集: 8 行, 每行 2048x256, 取自 reference/shops 的货架实拍 (自用)。"""
import os

import numpy as np
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOPS = os.path.join(ROOT, "reference", "shops")
OUT = os.path.join(ROOT, "textures", "yn_goods_photo_2k.jpg")
W, H = 2048, 256
# (文件, 上沿比例, 下沿比例): 招财猫有三层货架, 木芥子娃娃一层
ROWS = [("shop_01.jpg", 0.04, 0.36), ("shop_01.jpg", 0.33, 0.66), ("shop_01.jpg", 0.62, 0.96),
        ("shop_02.jpg", 0.28, 0.95), ("shop_02.jpg", 0.0, 0.42)]


def row_image(name, t, b, flip):
    im = Image.open(os.path.join(SHOPS, name)).convert("RGB")
    w, h = im.size
    c = im.crop((0, int(h * t), w, int(h * b)))
    c = c.resize((max(1, int(c.width * H / c.height)), H), Image.LANCZOS)
    if flip:
        c = ImageOps.mirror(c)
    out = Image.new("RGB", (W, H))
    x = 0
    k = 0
    while x < W:
        out.paste(ImageOps.mirror(c) if k % 2 else c, (x, 0))
        x += c.width
        k += 1
    return out


def main():
    sheet = Image.new("RGB", (W, H * 8))
    for i in range(8):
        name, t, b = ROWS[i % len(ROWS)]
        r = row_image(name, t, b, i >= len(ROWS))
        a = np.asarray(r, dtype=np.float32)
        a = a * (118 / max(a.mean(), 1))  # 各行亮度拉齐, 灯光交给 3D
        sheet.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (0, i * H))
    sheet.save(OUT, quality=92)
    print("goods atlas", sheet.size)


if __name__ == "__main__":
    main()
