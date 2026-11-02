# Shop sign + noren atlases. All shop names are fictional. Fonts: Zen Old Mincho, Yuji Syuku, Zen Kaku Gothic New, Klee One (SIL OFL 1.1).
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = r"D:\project\cijian\work"; FD = ROOT + r"\assets\fonts"; OUT = ROOT + r"\assets\gen"; os.makedirs(OUT, exist_ok=True)
F = dict(min=FD + r"\ZenOldMincho-Bold.ttf", brush=FD + r"\YujiSyuku-Regular.ttf", goth=FD + r"\ZenKakuGothicNew-Bold.ttf", hand=FD + r"\KleeOne-SemiBold.ttf")
rng = np.random.default_rng(11)
S = 2048

def noise(h, w, sc, seed):
    r = np.random.default_rng(seed); n = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for o in range(5):
        g = r.random((max(2, h // max(1, sc >> o)), max(2, w // max(1, sc >> o)))).astype(np.float32)
        n += np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 * amp; tot += amp; amp *= .5
    return n / tot

def board(w, h, bg, fg, text, font, vertical=False, frame=None, seed=0, grain=False, sub=None):
    im = Image.new("RGB", (w, h), bg); d = ImageDraw.Draw(im)
    if grain:   # wood grain along the long axis
        a = np.asarray(im, np.float32)
        g = noise(h, w, 8, seed) if not vertical else noise(h, w, 8, seed)
        st = np.sin((np.arange(h if not vertical else w)[:, None] * .09 + g[:, :1] * 8)) if not vertical else None
        k = .82 + .25 * noise(h // 8 or 1, w, 2, seed + 1).repeat(8, 0)[:h] if not vertical else .82 + .25 * noise(h, w // 8 or 1, 2, seed + 1).repeat(8, 1)[:, :w]
        im = Image.fromarray(np.clip(a * k[..., None], 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    if frame:
        m = int(min(w, h) * .06); d.rectangle([m, m, w - m, h - m], outline=frame, width=max(3, m // 3))
    if vertical:
        n = len(text); size = int(min(w * .78, h * .86 / max(1, n)))
        fnt = ImageFont.truetype(F[font], size)
        y = (h - size * n * 1.02) / 2
        for ch in text:
            bb = d.textbbox((0, 0), ch, font=fnt); d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], y - bb[1] * .5), ch, font=fnt, fill=fg); y += size * 1.02
    else:
        size = int(h * (.56 if sub else .66)); fnt = ImageFont.truetype(F[font], size)
        while d.textlength(text, font=fnt) > w * .88: size -= 4; fnt = ImageFont.truetype(F[font], size)
        bb = d.textbbox((0, 0), text, font=fnt)
        yy = (h - (bb[3] - bb[1])) / 2 - bb[1] - (h * .08 if sub else 0)
        d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], yy), text, font=fnt, fill=fg)
        if sub:
            f2 = ImageFont.truetype(F["goth"], int(h * .14)); bb = d.textbbox((0, 0), sub, font=f2)
            d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], h * .8 - bb[1]), sub, font=f2, fill=fg)
    return im

def weather(im, seed, amt=1.0):
    a = np.asarray(im, np.float32) / 255; h, w = a.shape[:2]
    n = noise(h, w, 64, seed); n2 = noise(h, w, 8, seed + 3)
    fade = 1 - amt * .18 * n                                   # sun-bleached patches
    a = a * fade[..., None] + amt * .12 * n[..., None] * np.array([.9, .85, .75])
    y = np.linspace(0, 1, h)[:, None]
    streak = np.clip((n2 - .55) * 3, 0, 1) * (y ** 1.5) * amt * .35     # grime from the top edge running down
    a = a * (1 - streak[..., None] * .6)
    e = np.minimum.reduce([np.arange(w)[None, :].repeat(h, 0), np.arange(w)[::-1][None, :].repeat(h, 0), np.arange(h)[:, None].repeat(w, 1), np.arange(h)[::-1][:, None].repeat(w, 1)]).astype(np.float32)
    a *= (.78 + .22 * np.clip(e / (min(h, w) * .08), 0, 1))[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

H = [  # (text, sub, bg, fg, font, frame, grain)
    ("ことり菓子店", "KOTORI  SWEETS", (92, 58, 36), (238, 222, 190), "min", (200, 170, 120), True),
    ("惣菜 たまや", None, (28, 40, 70), (240, 236, 226), "brush", None, False),
    ("古書 月舟堂", None, (150, 118, 80), (30, 24, 20), "min", (60, 44, 30), True),
    ("珈琲 ひぐれ", "COFFEE & TOAST", (36, 58, 46), (236, 226, 200), "min", None, False),
    ("手ぬぐい 糸巻", None, (236, 232, 220), (34, 52, 98), "brush", (34, 52, 98), False),
    ("金物 山源商店", None, (160, 36, 30), (248, 244, 236), "goth", None, False),
    ("八百屋 松栄", None, (226, 186, 52), (26, 24, 22), "goth", None, False),
    ("茶舗 千草園", None, (22, 20, 20), (206, 170, 92), "min", (150, 120, 60), False),
    ("パン工房 こむぎ", None, (232, 220, 196), (110, 70, 40), "hand", None, False),
    ("雑貨 ねこまち", "zakka & gallery", (244, 242, 236), (36, 36, 36), "hand", None, False),
    ("せんべい 吉野屋", None, (110, 74, 44), (246, 236, 214), "brush", None, True),
    ("酒 まるい商店", None, (238, 234, 222), (120, 28, 24), "min", (120, 28, 24), False),
]
Vt = [("御菓子", (92, 58, 36), (238, 222, 190), "min"), ("惣菜", (28, 40, 70), (240, 236, 226), "brush"), ("古本", (40, 36, 30), (230, 220, 200), "min"),
      ("珈琲", (36, 58, 46), (236, 226, 200), "min"), ("手拭", (236, 232, 220), (34, 52, 98), "brush"), ("金物", (160, 36, 30), (248, 244, 236), "goth"),
      ("青果", (226, 186, 52), (26, 24, 22), "goth"), ("日本茶", (22, 20, 20), (206, 170, 92), "min"), ("焼きたて", (232, 220, 196), (110, 70, 40), "hand"),
      ("雑貨", (244, 242, 236), (36, 36, 36), "hand"), ("煎餅", (110, 74, 44), (246, 236, 214), "brush"), ("地酒", (238, 234, 222), (120, 28, 24), "min"),
      ("営業中", (250, 248, 240), (190, 30, 30), "goth"), ("谷中銀座", (40, 60, 120), (250, 248, 240), "goth"), ("貸間", (236, 232, 222), (30, 30, 30), "min"), ("氷", (250, 250, 250), (30, 70, 160), "brush")]
atlas = Image.new("RGB", (S, S), (40, 40, 40)); cells = {"h": [], "v": []}
for k, (t, sub, bg, fg, fn, fr, gr) in enumerate(H):
    x = (k % 2) * 1024; y = (k // 2) * 256
    im = weather(board(1024, 256, bg, fg, t, fn, frame=fr, seed=k, grain=gr, sub=sub), 100 + k, .9)
    atlas.paste(im, (x, y)); cells["h"].append([x / S, 1 - (y + 256) / S, (x + 1024) / S, 1 - y / S])
for k, (t, bg, fg, fn) in enumerate(Vt):
    x = k * 128; y = 1536
    im = weather(board(128, 512, bg, fg, t, fn, vertical=True, seed=50 + k), 200 + k, .8)
    atlas.paste(im, (x, y)); cells["v"].append([x / S, 1 - (y + 512) / S, (x + 128) / S, 1 - y / S])
atlas.save(OUT + r"\signs.jpg", quality=90)
# noren: 2x2, indigo / white / brown / red, with a fictional mark and soft fold shading
NR = [((30, 44, 86), (238, 236, 228), "菓"), ((238, 234, 224), (40, 52, 90), "茶"), ((96, 60, 38), (236, 226, 204), "そば"), ((150, 34, 30), (246, 240, 230), "甘味")]
nor = Image.new("RGB", (1024, 1024)); cells["noren"] = []
for k, (bg, fg, t) in enumerate(NR):
    im = Image.new("RGB", (512, 512), bg); d = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(F["brush"], 260 if len(t) == 1 else 190)
    bb = d.textbbox((0, 0), t, font=fnt); d.text(((512 - (bb[2] - bb[0])) / 2 - bb[0], 270 - (bb[3] - bb[1]) / 2 - bb[1]), t, font=fnt, fill=fg)
    d.rectangle([0, 0, 512, 40], fill=tuple(int(c * .7) for c in bg))
    a = np.asarray(im, np.float32)
    fold = .86 + .14 * np.sin(np.linspace(0, 1, 512)[None, :] * np.pi * 6)
    im = weather(Image.fromarray(np.clip(a * fold[..., None], 0, 255).astype(np.uint8)), 300 + k, .6)
    x = (k % 2) * 512; y = (k // 2) * 512; nor.paste(im, (x, y)); cells["noren"].append([x / 1024, 1 - (y + 512) / 1024, (x + 512) / 1024, 1 - y / 1024])
nor.save(OUT + r"\noren.jpg", quality=90)
json.dump(cells, open(OUT + r"\signs.json", "w"), indent=0)
atlas.resize((1024, 1024)).save(ROOT + r"\output\signs_preview.jpg", quality=85); print("ok")
