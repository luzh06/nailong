"""从 layout_report.txt 核查重复: 同侧相邻的店身/雨棚, 同名店铺的最近距离。"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for line in open(os.path.join(ROOT, "exports", "layout_report.txt"), encoding="utf-8"):
    m = re.match(r"s_([we])(\d+) y=\s*([\d.]+) w=([\d.]+) body=(\w) sign=(\S+) awning=(\w+)", line)
    rows.append((m[1], float(m[3]), float(m[4]), m[5], m[6], m[7]))
adj_body = adj_sign = adj_awning = 0
for side in "we":
    r = sorted((x for x in rows if x[0] == side), key=lambda x: x[1])
    for a, b in zip(r, r[1:]):
        if b[1] - a[1] > 8:
            continue
        adj_body += a[3] == b[3]
        adj_sign += a[4] == b[4]
        adj_awning += a[5] == b[5]
print("slots", len(rows), "adjacent same body", adj_body, "same sign", adj_sign, "same awning", adj_awning)
names = {}
for x in rows:
    names.setdefault(x[4], []).append(x)
print("names", len(names), "max uses", max(len(v) for v in names.values()))
closest = []
for n, v in names.items():
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            same_side = v[i][0] == v[j][0]
            closest.append((abs(v[i][1] - v[j][1]), same_side, n))
closest.sort()
print("closest same-name pairs (m, same side, name):", closest[:5])
print("bodies", {k: sum(1 for x in rows if x[3] == k) for k in "ABCDEFGH"})
print("awnings", {k: sum(1 for x in rows if x[5] == k) for k in ("nakamise", "corrugated", "cloth", "tile")})
