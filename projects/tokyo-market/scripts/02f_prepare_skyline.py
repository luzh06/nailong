"""远景绘景: 从 reference/web/web_01.jpg 抠出东京天际线 (去掉真实的五重塔和宝藏门, 3D 里已有),
拼成可水平重复的长条, 调出早晨, 日落, 蓝调三版。自用, 公开发布前要处理授权。
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
SRC = os.path.join(ROOT, "reference", "web", "web_01.jpg")
K = 3412 / 1165  # 下面的坐标在 1165 宽的缩略图上量
TOP, BOTTOM = 300, 437
PIECES = [(170, 660), (985, 1165)]
FADE = 40
RNG = np.random.default_rng(9)


def sky_alpha(a):
    """每一列从上往下走, 天空颜色缓慢变化; 突然变化的地方就是楼。"""
    h, w = a.shape[:2]
    line = np.zeros(w, dtype=int)
    for x in range(w):
        ref = a[:12, x].mean(axis=0)
        y = 12
        while y < h - 1:
            p = a[y, x]
            if np.abs(p - ref).sum() > 42:
                break
            ref = ref * 0.97 + p * 0.03
            y += 1
        line[x] = y
    # 去掉云边造成的尖刺: 比两侧高很多又很窄的柱子压回去
    k = 15
    smooth = np.array([np.median(line[max(0, i - k):i + k]) for i in range(w)])
    line = np.where(line < smooth - 90, smooth, line).astype(int)
    alpha = np.zeros((h, w), dtype=np.float32)
    for x in range(w):
        alpha[line[x]:, x] = 1.0
    im = Image.fromarray((alpha * 255).astype(np.uint8)).resize((w, h))
    return np.asarray(im, dtype=np.float32) / 255


def build():
    im = Image.open(SRC).convert("RGB")
    parts = []
    for x0, x1 in PIECES:
        box = (int(x0 * K), int(TOP * K), int(x1 * K), int(BOTTOM * K))
        c = np.asarray(im.crop(box), dtype=np.float32)
        parts.append(np.dstack((c, sky_alpha(c) * 255)))
    fade = int(FADE * K)
    a, b = parts
    w = a.shape[1] + b.shape[1] - fade
    out = np.zeros((a.shape[0], w, 4), dtype=np.float32)
    out[:, :a.shape[1]] = a
    t = np.linspace(0, 1, fade)[None, :, None]
    out[:, a.shape[1] - fade:a.shape[1]] = a[:, -fade:] * (1 - t) + b[:, :fade] * t
    out[:, a.shape[1]:] = b[:, fade:]
    # 接回开头, 水平重复时没有接缝
    head = out[:, :fade].copy()
    out[:, -fade:] = out[:, -fade:] * (1 - t) + head * t
    # 接缝处两边楼高不同, 透明度不能混, 否则出现虚影
    for x0, x1 in ((a.shape[1] - fade, a.shape[1]), (w - fade, w)):
        out[:, x0:x1, 3] = np.where(out[:, x0:x1, 3] > 127, 255, 0)
    return out


def grade(rgba, name, tone, lift, contrast, windows=0.0):
    rgb = rgba[..., :3] / 255
    lum = rgb.mean(axis=2, keepdims=True)
    rgb = lum + (rgb - lum) * 0.75  # 远处饱和度低一点
    rgb = np.clip((rgb - 0.5) * contrast + 0.5, 0, 1) * np.array(tone, dtype=np.float32) + np.array(lift, dtype=np.float32)
    if windows:
        h, w = rgb.shape[:2]
        solid = rgba[..., 3] > 200
        for _ in range(int(w * h * windows)):
            x, y = RNG.integers(0, w - 6), RNG.integers(0, h - 6)
            if not solid[y, x]:
                continue
            c = np.array(((1.0, 0.72, 0.42), (1.0, 0.82, 0.55), (0.85, 0.92, 1.0))[RNG.integers(0, 3)], dtype=np.float32) * RNG.uniform(0.5, 1.0)
            rgb[y:y + RNG.integers(2, 4), x:x + RNG.integers(2, 6)] = c
    out = np.dstack((np.clip(rgb, 0, 1) * 255, rgba[..., 3]))
    Image.fromarray(out.astype(np.uint8), "RGBA").save(os.path.join(TEX, f"yn_skyline_{name}_2k.png"))


if __name__ == "__main__":
    s = build()
    print("strip", s.shape, "metres note: natural scale about 49 px per degree")
    grade(s, "morning", (0.92, 0.97, 1.05), (0.05, 0.06, 0.08), 0.85)
    grade(s, "sunset", (1.0, 0.72, 0.55), (0.03, 0.015, 0.02), 0.9)
    grade(s, "dusk", (0.13, 0.17, 0.3), (0.0, 0.005, 0.02), 1.0, windows=0.0011)
