# Print PLATEAU lots inside a box: centroid, obb size/angle, height, storeys, usage. usage: lots.py E0 E1 N0 N1
import json, sys, math
d = json.load(open(r"D:\project\cijian\work\data\plateau_near.json"))
E0, E1, N0, N1 = map(float, sys.argv[1:5])
seen = set()
for b in d["buildings"]:
    fp = b["lod"].get("lod0", [[]])[0]
    if len(fp) < 3: continue
    xs = [p[0] for p in fp]; ys = [p[1] for p in fp]
    cx = sum(xs) / len(xs); cy = sum(ys) / len(ys)
    if not (E0 <= cx <= E1 and N0 <= cy <= N1): continue
    k = (round(cx, 1), round(cy, 1))
    if k in seen: continue
    seen.add(k)
    best = None
    n = len(fp)
    for i in range(n - 1):
        ex = fp[i + 1][0] - fp[i][0]; ey = fp[i + 1][1] - fp[i][1]; L = math.hypot(ex, ey)
        if L < .5: continue
        ux, uy = ex / L, ey / L
        a_ = [p[0] * ux + p[1] * uy for p in fp]; b_ = [-p[0] * uy + p[1] * ux for p in fp]
        ar = (max(a_) - min(a_)) * (max(b_) - min(b_))
        if best is None or ar < best[0]: best = (ar, math.degrees(math.atan2(uy, ux)), max(a_) - min(a_), max(b_) - min(b_))
    at = b["attrs"]
    print(f"c=({cx:7.1f},{cy:6.1f}) E[{min(xs):7.1f},{max(xs):7.1f}] N[{min(ys):6.1f},{max(ys):6.1f}] obb {best[2]:5.1f}x{best[3]:5.1f} @{best[1]:6.1f}  H={at.get('measuredHeight')} st={at.get('storeysAboveGround')} use={at.get('usage')} struct={at.get('buildingStructureType')} roof={at.get('roofType')} z0={min(p[2] for p in fp):.2f} lod2={'RoofSurface' in b['lod']}")
