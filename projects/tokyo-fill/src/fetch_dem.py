# GSI dem5a (5 m laser DEM) PNG tiles around the stair top -> ENU height grid (metres, T.P.).
# Source: 国土地理院 地理院タイル (標高タイル dem5a). Attribution required: 「国土地理院」.
import math, io, json, os, urllib.request
import numpy as np
from PIL import Image
ROOT = r"D:\project\cijian\work"
LAT0, LON0 = 35.727641, 139.767341
Z = 15
a = 6378137.0; f = 1 / 298.257222101; e2 = f * (2 - f); s = math.sin(math.radians(LAT0))
Nr = a / math.sqrt(1 - e2 * s * s); Mr = a * (1 - e2) / (1 - e2 * s * s) ** 1.5
kx = math.radians(1) * Nr * math.cos(math.radians(LAT0)); ky = math.radians(1) * Mr
def tile(lat, lon):
    n = 2 ** Z; x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y
def latlon(px, py):   # global pixel (256/tile) -> lat lon
    n = 2 ** Z * 256
    lon = px / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * py / n))))
    return lat, lon
R = 220  # metres
lat_lo, lat_hi = LAT0 - R / ky, LAT0 + R / ky; lon_lo, lon_hi = LON0 - R / kx, LON0 + R / kx
x0, y0 = tile(lat_hi, lon_lo); x1, y1 = tile(lat_lo, lon_hi)
tx = range(int(x0), int(x1) + 1); ty = range(int(y0), int(y1) + 1)
big = np.full((len(ty) * 256, len(tx) * 256), np.nan, np.float32)
os.makedirs(ROOT + r"\data\dem", exist_ok=True)
for j, y in enumerate(ty):
    for i, x in enumerate(tx):
        p = ROOT + rf"\data\dem\{Z}_{x}_{y}.png"
        if not os.path.exists(p):
            u = f"https://cyberjapandata.gsi.go.jp/xyz/dem5a_png/{Z}/{x}/{y}.png"
            d = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "cijian-research/1.0"}), timeout=60).read()
            open(p, "wb").write(d)
        im = np.asarray(Image.open(p).convert("RGB")).astype(np.int64)
        v = im[..., 0] * 65536 + im[..., 1] * 256 + im[..., 2]
        h = np.where(v < 2 ** 23, v * .01, np.where(v == 2 ** 23, np.nan, (v - 2 ** 24) * .01))
        big[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = h
# resample to a 1 m ENU grid
E = np.arange(-200, 121, 1.0); N = np.arange(-150, 151, 1.0)
out = np.zeros((len(N), len(E)), np.float32)
for jj, n_ in enumerate(N):
    for ii, e_ in enumerate(E):
        lat = LAT0 + n_ / ky; lon = LON0 + e_ / kx
        px, py = tile(lat, lon); px = (px - tx[0]) * 256 - .5; py = (py - ty[0]) * 256 - .5
        ix, iy = int(math.floor(px)), int(math.floor(py)); fx, fy = px - ix, py - iy
        q = big[iy:iy + 2, ix:ix + 2]
        out[jj, ii] = q[0, 0] * (1 - fx) * (1 - fy) + q[0, 1] * fx * (1 - fy) + q[1, 0] * (1 - fx) * fy + q[1, 1] * fx * fy
json.dump(dict(src="GSI dem5a z15 (国土地理院)", E0=-200, N0=-150, step=1.0, nE=len(E), nN=len(N), h=[[round(float(v), 2) if v == v else None for v in r] for r in out]),
          open(ROOT + r"\data\dem_enu.json", "w"))
for e_, n_ in ((0, 0), (-31, 1.8), (-60, 1.8), (-95, 1.8), (-120, 1.8), (-80, -30), (-80, 30), (-45, 30), (-45, -25)):
    print(e_, n_, out[int(n_ + 150), int(e_ + 200)])
# preview
v = out.copy(); lo, hi = np.nanmin(v), np.nanmax(v)
Image.fromarray((np.nan_to_num((v - lo) / (hi - lo)) * 255).astype(np.uint8)[::-1]).resize((len(E) * 3, len(N) * 3)).save(ROOT + r"\output\dem.png")
print("range", lo, hi)
