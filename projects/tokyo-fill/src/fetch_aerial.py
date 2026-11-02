# GSI seamless aerial photo mosaic (z18) around the area, with the ENU grid drawn on. Reference only, not used as texture.
# Source: 国土地理院 地理院タイル 全国最新写真（シームレス）. Attribution 「国土地理院」.
import math, io, os, urllib.request
from PIL import Image, ImageDraw
ROOT = r"D:\project\cijian\work"
LAT0, LON0 = 35.727641, 139.767341
Z = 18
def tile(lat, lon):
    n = 2 ** Z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
kx = 90350.0; ky = 110950.0
E0, E1, N0, N1 = -135, -20, -60, 60
xa, ya = tile(LAT0 + N1 / ky, LON0 + E0 / kx); xb, yb = tile(LAT0 + N0 / ky, LON0 + E1 / kx)
os.makedirs(ROOT + r"\data\aerial", exist_ok=True)
tx = range(int(xa), int(xb) + 1); ty = range(int(ya), int(yb) + 1)
im = Image.new("RGB", (len(tx) * 256, len(ty) * 256))
for j, y in enumerate(ty):
    for i, x in enumerate(tx):
        p = ROOT + rf"\data\aerial\{Z}_{x}_{y}.jpg"
        if not os.path.exists(p):
            u = f"https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{Z}/{x}/{y}.jpg"
            open(p, "wb").write(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "cijian-research/1.0"}), timeout=60).read())
        im.paste(Image.open(p), (i * 256, j * 256))
def px(E, N):
    x, y = tile(LAT0 + N / ky, LON0 + E / kx)
    return (x - tx[0]) * 256, (y - ty[0]) * 256
dr = ImageDraw.Draw(im)
for g in range(-140, 0, 10):
    dr.line([px(g, N0), px(g, N1)], fill=(255, 255, 0) if g % 50 == 0 else (120, 120, 0)); dr.text(px(g, N1 - 3), str(g), fill=(255, 255, 0))
for g in range(-60, 61, 10):
    dr.line([px(E0, g), px(E1, g)], fill=(255, 255, 0) if g % 50 == 0 else (120, 120, 0)); dr.text(px(E0 + 1, g), str(g), fill=(255, 255, 0))
a = px(-112.5, 41.8); b = px(-32.5, -38.2); dr.rectangle([a, b], outline=(255, 0, 0), width=3)
x0, y0 = px(E0, N1); x1, y1 = px(E1, N0)
c = im.crop((int(x0), int(y0), int(x1), int(y1))); c.resize((c.width * 4, c.height * 4), Image.LANCZOS).save(ROOT + r"\output\aerial.jpg", quality=88)
print(im.size)
