# One-off: qs_h1 building/road rects (model -> ENU) for ground exclusion. usage: python h1_rects.py h1.json
import json, sys, re
j = json.load(open(sys.argv[1]))
out = []
for r in j["rows"]:
    if r["hr"] or r["t"] != "MESH": continue
    k = re.split(r"[.]", r["n"])[0]
    if not re.match(r"^(h_|apt_)", k): continue
    (x0, y0), (x1, y1) = r["mn"][:2], r["mx"][:2]
    E0, E1 = y0 - 32.5, y1 - 32.5; N0, N1 = 1.8 - x1, 1.8 - x0
    out.append(dict(n=r["n"], E=[round(E0, 2), round(E1, 2)], N=[round(N0, 2), round(N1, 2)], z=r["mx"][2]))
# merge per building prefix (h_G-14_body, h_G-14_win... -> h_G-14)
g = {}
for o in out:
    m = re.match(r"^(h_[A-Za-z]+-?\d*|apt_[A-Za-z]+\d*)", o["n"]); k = m.group(1) if m else o["n"]
    d = g.setdefault(k, dict(E=[1e9, -1e9], N=[1e9, -1e9], z=0))
    d["E"] = [min(d["E"][0], o["E"][0]), max(d["E"][1], o["E"][1])]; d["N"] = [min(d["N"][0], o["N"][0]), max(d["N"][1], o["N"][1])]; d["z"] = max(d["z"], o["z"])
json.dump(g, open(r"D:\project\cijian\work\data\h1_rects.json", "w"), indent=1)
for k, d in sorted(g.items(), key=lambda kv: kv[1]["E"][0]): print(k, d)
