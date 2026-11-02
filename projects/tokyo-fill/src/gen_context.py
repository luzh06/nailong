# Repeating facade tiles for the context ring: one tile = 3.0 m wide x 2.9 m (one storey). Four wall types.
import numpy as np, os
from PIL import Image, ImageDraw
OUT = r"D:\project\cijian\work\assets\gen"; S = 512
rng = np.random.default_rng(21)

def noise(sc, seed):
    g = np.random.default_rng(seed).random((S // sc, S // sc)).astype(np.float32)
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255

def tile(name, wall, frame, seed, kind):
    n = noise(16, seed) * .6 + noise(4, seed + 1) * .4
    a = np.ones((S, S, 3), np.float32) * np.array(wall) * (.85 + .25 * n)[..., None]
    if kind == "tile":
        a[(np.arange(S) % 22 < 2)[:, None].repeat(S, 1)] *= .82
        a[:, (np.arange(S) % 44 < 2)] *= .85
    if kind == "siding":
        a[(np.arange(S) % 18 < 3)[:, None].repeat(S, 1)] *= .7
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    x0, x1, y0, y1 = int(S * .22), int(S * .78), int(S * .25), int(S * .66)          # one window per bay
    d.rectangle([x0 - 6, y0 - 6, x1 + 6, y1 + 6], fill=frame)
    gl = tuple(int(c) for c in rng.integers(40, 90, 3))
    d.rectangle([x0, y0, x1, y1], fill=gl); d.rectangle([x0, y0, (x0 + x1) // 2 + 20, y1], fill=(150, 140, 120))       # half-drawn curtain
    d.line([(x0 + x1) // 2, y0, (x0 + x1) // 2, y1], fill=frame, width=6)
    d.rectangle([x0 - 10, y1 + 6, x1 + 10, y1 + 14], fill=tuple(int(c * .8) for c in frame))
    b = np.asarray(im, np.float32) / 255
    streak = np.clip((noise(64, seed + 5) - .55) * 3, 0, 1) * np.linspace(.3, 1, S)[:, None]
    b *= (1 - .25 * streak)[..., None]
    Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, f"ctx_{name}.jpg"), quality=86)

tile("plaster", (.82, .78, .7), (170, 168, 160), 1, "plain")
tile("tile", (.76, .72, .66), (120, 120, 118), 2, "tile")
tile("siding", (.55, .5, .44), (60, 55, 50), 3, "siding")
tile("concrete", (.68, .68, .66), (190, 190, 186), 4, "plain")
print("ok")
