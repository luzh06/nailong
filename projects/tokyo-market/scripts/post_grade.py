"""渲染后期: 高光辉光, 暗角, 胶片颗粒, 轻微色差感的色调。用法: python post_grade.py <输入.png> <输出.jpg> [辉光强度]"""
import sys

import numpy as np
from PIL import Image, ImageFilter


def grade(src, dst, bloom=0.5):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im, dtype=np.float32) / 255
    lum = a.mean(axis=2, keepdims=True)
    bright = np.clip((lum - 0.72) / 0.28, 0, 1) * a
    glow = np.zeros_like(a)
    for r, w in ((im.width / 240, 0.5), (im.width / 70, 0.3), (im.width / 22, 0.2)):
        b = Image.fromarray((bright * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
        glow += np.asarray(b, dtype=np.float32) / 255 * w
    a = 1 - (1 - a) * (1 - np.clip(glow * bloom * 2.2, 0, 1))
    # S 曲线, 暗部略提蓝, 高光略偏暖
    a = np.clip(a, 0, 1)
    a = a * a * (3 - 2 * a) * 0.35 + a * 0.65
    lum = a.mean(axis=2, keepdims=True)
    a = a + (1 - lum) ** 3 * np.array([-0.006, 0.0, 0.016]) + lum ** 3 * np.array([0.012, 0.004, -0.012])
    h, w = a.shape[:2]
    y, x = np.mgrid[-1:1:h * 1j, -1:1:w * 1j]
    vig = 1 - 0.2 * np.clip(x ** 2 + y ** 2 - 0.25, 0, 1.6)
    a = a * vig[..., None]
    rng = np.random.default_rng(1)
    grain = rng.normal(0, 0.011, (h, w, 1))
    a = a + grain * (1.2 - a.mean(axis=2, keepdims=True))
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(dst, quality=94)


if __name__ == "__main__":
    grade(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.5)
