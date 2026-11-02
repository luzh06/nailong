# Coverage map: PLATEAU footprints + what already exists (qs_h1 street, blocks A/B) + the 80x80 target square.
import json, sys
from PIL import Image, ImageDraw
ROOT = r"D:\project\cijian\work"
d = json.load(open(ROOT + r"\data\plateau_near.json"))
h1 = json.load(open(sys.argv[1]))
S = 9.0; W = H = 1500; CX, CY = -70, 2
def P(x, y): return (W / 2 + (x - CX) * S, H / 2 - (y - CY) * S)
def m2e(x, y): return (y - 32.5, 1.8 - x)          # qs_h1 model -> ENU
im = Image.new("RGB", (W, H), (245, 243, 238)); dr = ImageDraw.Draw(im, "RGBA")
for r in d["roads"]:
    for p in r["polys"]:
        if len(p) > 2: dr.polygon([P(a, b) for a, b, c in p], fill=(215, 215, 220), outline=(170, 170, 180))
seen = set()
for b in d["buildings"]:
    fp = b["lod"].get("lod0", [[]])[0]
    if len(fp) < 3: continue
    key = (round(fp[0][0], 1), round(fp[0][1], 1))
    if key in seen: continue
    seen.add(key)
    st = int(b["attrs"].get("storeysAboveGround", 0) or 0)
    col = (150, 190, 150) if st <= 2 else (220, 190, 120) if st <= 4 else (220, 130, 110)
    dr.polygon([P(a, z) for a, z, _ in fp], fill=col, outline=(60, 60, 60))
    cx = sum(q[0] for q in fp) / len(fp); cy = sum(q[1] for q in fp) / len(fp)
    dr.text((P(cx, cy)[0] - 8, P(cx, cy)[1] - 5), f"{st}|{cx:.0f},{cy:.0f}", fill=(0, 0, 0))
# existing qs_h1 objects (buildings/street) in blue
for r in h1["rows"]:
    if r["hr"] or r["n"].startswith(("far", "fog", "ground", "hf", "wires")): continue
    (x0, y0), (x1, y1) = r["mn"][:2], r["mx"][:2]
    a = m2e(x0, y0); b = m2e(x1, y1)
    dr.rectangle([P(min(a[0], b[0]), max(a[1], b[1])), P(max(a[0], b[0]), min(a[1], b[1]))], fill=(40, 90, 220, 40), outline=(40, 90, 220, 120))
# blocks A / B
for nm, (x0, x1, y0, y1) in {"A": (17.16, 56.8, -91.51, -21.6), "B": (-47.27, -11.1, -83.5, -17.5)}.items():
    a = m2e(x0, y0); b = m2e(x1, y1)
    dr.rectangle([P(min(a[0], b[0]), max(a[1], b[1])), P(max(a[0], b[0]), min(a[1], b[1]))], outline=(200, 0, 160), width=4)
    dr.text(P((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), "BLOCK " + nm, fill=(200, 0, 160))
# target square, model x[-40,40] y[-80,0]
a = m2e(-40, -80); b = m2e(40, 0)
dr.rectangle([P(min(a[0], b[0]), max(a[1], b[1])), P(max(a[0], b[0]), min(a[1], b[1]))], outline=(230, 0, 0), width=5)
for g in range(-200, 101, 10):
    c = (120, 120, 255, 160) if g % 50 == 0 else (205, 205, 240, 90)
    dr.line([P(g, -200), P(g, 200)], fill=c); dr.line([P(-300, g), P(100, g)], fill=c)
    dr.text((P(g, 0)[0] + 2, 3), str(g), fill=(0, 0, 200)); dr.text((3, P(0, g)[1] + 2), str(g), fill=(0, 0, 200))
im.save(ROOT + r"\output\cover_plan.png"); print("ok")
