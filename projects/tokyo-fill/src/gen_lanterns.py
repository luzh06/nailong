# Chochin (paper lantern) textures as cylindrical unwraps: u=0..1 around, front faces u=0.5. Texts are the real landmark inscriptions;
# donor names (a corporate brand on the real 雷門 lantern) are left out. Font: Yuji Syuku (SIL OFL 1.1).
import numpy as np, os
from PIL import Image, ImageDraw, ImageFont
ROOT = r"D:\project\cijian\work"; OUT = ROOT + r"\assets\gen"; FONT = ROOT + r"\assets\fonts\YujiSyuku-Regular.ttf"
W, H = 2048, 768

def noise(h, w, sc, seed):
    r = np.random.default_rng(seed); n = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for o in range(5):
        g = r.random((max(2, h // max(1, sc >> o)), max(2, w // max(1, sc >> o)))).astype(np.float32)
        n += np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 * amp; tot += amp; amp *= .5
    return n / tot

def column(d, text, cx, size, top, font, fill):
    f = ImageFont.truetype(font, size); y = top
    for ch in text:
        bb = d.textbbox((0, 0), ch, font=f); d.text((cx - (bb[2] + bb[0]) / 2, y - bb[1]), ch, font=f, fill=fill); y += size * .98

def lantern(name, front, back, red=(178, 34, 26), seed=0):
    im = Image.new("RGB", (W, H), red); d = ImageDraw.Draw(im)
    column(d, front, W * .5, int(H * .40), H * .1, FONT, (18, 14, 12))
    if back:
        n = len(back); sz = int(H * .8 / n * .98)
        if n > 2:   # two columns either side of the seam (u=0 is the back centre), drawn twice so they wrap
            for off in (0, W, -W):
                column(d, back[:2], W * .075 + off, int(H * .34), H * .14, FONT, (18, 14, 12))
                column(d, back[2:], W * .925 + off, int(H * .34), H * .14, FONT, (18, 14, 12))
        else:
            column(d, back, 0, sz, H * .1, FONT, (18, 14, 12)); column(d, back, W, sz, H * .1, FONT, (18, 14, 12))
    a = np.asarray(im, np.float32) / 255
    y = np.arange(H)[:, None] / H
    ribs = .86 + .14 * np.abs(np.sin(y * np.pi * 46))          # bamboo ribs under the paper
    seams = 1 - .05 * (np.abs(np.sin(np.arange(W)[None, :] / W * np.pi * 24)) > .985)
    n = noise(H, W, 96, seed); n2 = noise(H, W, 12, seed + 1)
    shade = .88 + .2 * n + .05 * n2                             # uneven lacquer and paper
    a = a * (ribs * seams * shade)[..., None]
    dark = (y < .045) | (y > .955)                              # black lacquered rims
    a[dark[:, 0]] = np.array([.05, .045, .04]) * (.8 + .3 * n[dark[:, 0]])[..., None]
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(OUT + rf"\{name}.jpg", quality=90)

lantern("chochin_kaminarimon", "雷門", "風雷神門", seed=3)
lantern("chochin_kobunacho", "小舟町", None, seed=7)
# bronze relief for the lantern bottom and gold leaf noise for the finial
r = noise(512, 512, 24, 11); g = noise(512, 512, 4, 12)
X, Y = np.meshgrid(np.linspace(-1, 1, 512), np.linspace(-1, 1, 512)); rr = np.hypot(X, Y); th = np.arctan2(Y, X)
coil = .5 + .5 * np.sin(th * 3 + rr * 14 + g * 6)                # coiled-dragon suggestion: spiralling scales
rel = np.clip(coil * .7 + r * .5, 0, 1) * (rr < .98)
img = np.stack([.42 + .3 * rel, .3 + .22 * rel, .14 + .1 * rel], -1)
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(OUT + r"\bronze_relief.jpg", quality=90)
print("ok")
