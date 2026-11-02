# Procedural ground textures: cast-iron manhole cover (fictional emblem) and painted road text with alpha.
import numpy as np, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = r"D:\project\cijian\work"; OUT = ROOT + r"\assets\gen"
S = 1024
X, Y = np.meshgrid(np.linspace(-1, 1, S), np.linspace(-1, 1, S)); R = np.hypot(X, Y); TH = np.arctan2(Y, X)
rng = np.random.default_rng(5)
# height field: rim, concentric bands, radial ribs, anti-slip studs, central emblem disc
h = np.zeros((S, S), np.float32)
h += (R > .9) * .6
h += ((R > .32) & (R < .88)) * (.35 + .25 * (np.sin(R * 70) > .6))
h += ((R > .32) & (R < .88)) * .25 * (np.abs(np.sin(TH * 12)) < .12)
gx = (np.mod((X + 1) * 40, 1) - .5) ** 2 + (np.mod((Y + 1) * 40, 1) - .5) ** 2
h += ((R > .35) & (R < .86)) * (gx < .04) * .2
h += (R < .3) * .5
em = Image.new("L", (S, S), 0); d = ImageDraw.Draw(em)
for k in range(6):            # fictional six-petal ward mark
    a = k * np.pi / 3; cx, cy = S / 2 + 90 * np.cos(a), S / 2 + 90 * np.sin(a)
    d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], outline=255, width=14)
h += np.asarray(em.filter(ImageFilter.GaussianBlur(2)), np.float32) / 255 * .4 * (R < .3)
h *= (R < .97)
n = rng.random((S // 8, S // 8)); n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255
# shade: worn raised parts are bright steel, recesses rusty-dark with grit
dx = np.gradient(h, axis=1); dy = np.gradient(h, axis=0); light = np.clip(.6 - (dx + dy) * 18, 0, 1)
worn = np.clip(h * 1.4, 0, 1)
base = np.stack([.16 + .05 * n, .15 + .04 * n, .14 + .03 * n], -1)
steel = np.array([.42, .41, .4])
rust = np.array([.26, .17, .11])
col = base * (1 - worn[..., None]) + steel * worn[..., None] * (.75 + .25 * n[..., None])
col = col * (1 - .4 * (n[..., None] > .7) * (1 - worn[..., None])) + rust * .4 * (n[..., None] > .7) * (1 - worn[..., None])
col *= (.7 + .5 * light)[..., None]
col[R >= .97] = [.2, .2, .2]
Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(OUT + r"\manhole.jpg", quality=90)
# road text: white thermoplastic, slightly broken, alpha for a decal material
F = ROOT + r"\assets\fonts\ZenKakuGothicNew-Bold.ttf"
im = Image.new("L", (1024, 2048), 0); d = ImageDraw.Draw(im)
f = ImageFont.truetype(F, 560)
for k, ch in enumerate("止まれ"):
    bb = d.textbbox((0, 0), ch, font=f); d.text(((1024 - (bb[2] - bb[0])) / 2 - bb[0], 60 + k * 650 - bb[1]), ch, font=f, fill=255)
a = np.asarray(im, np.float32) / 255
def blobs(h, w, cells, seed):
    g = np.random.default_rng(seed).random(cells)
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
xx = np.linspace(0, 1, 1024)[None, :]
tracks = np.exp(-((xx - .28) / .09) ** 2) + np.exp(-((xx - .72) / .09) ** 2)          # tyre tracks wear the paint most
wear = blobs(2048, 1024, (24, 12), 3) * .65 + blobs(2048, 1024, (160, 80), 4) * .35
a = a * np.clip((wear - .25 - .35 * tracks) * 4, 0, 1) * (.85 + .15 * blobs(2048, 1024, (400, 200), 6))
rgba = np.dstack([np.full_like(a, .92), np.full_like(a, .92), np.full_like(a, .88), a])
Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").transpose(Image.FLIP_TOP_BOTTOM).save(OUT + r"\roadmark.png")
print("ok")
