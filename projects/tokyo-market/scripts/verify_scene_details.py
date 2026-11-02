"""核验 GLB 里容易悄悄出错的内容: Draw Call, 透明模式, 颜色因子, 扩展, WebP 压缩损失。
用法: python verify_scene_details.py <scene.glb> <textures 目录>
"""
import io
import json
import math
import os
import struct
import sys

import numpy as np
from PIL import Image


def read(path):
    with open(path, "rb") as f:
        f.read(12)
        n, _ = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(n))
        n, _ = struct.unpack("<II", f.read(8))
        return doc, f.read(n)


def psnr(a, b):
    mse = np.mean((a.astype(np.float32) - b.astype(np.float32)) ** 2)
    return 99.0 if mse == 0 else 20 * math.log10(255.0 / math.sqrt(mse))


doc, blob = read(sys.argv[1])
tex_dir = sys.argv[2]

draws = 0
per_mat = {}
for node in doc["nodes"]:
    if "mesh" in node:
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            draws += 1
            k = prim.get("material", -1)
            per_mat[k] = per_mat.get(k, 0) + 1
print("nodes_with_mesh", sum(1 for n in doc["nodes"] if "mesh" in n))
print("unique_meshes", len(doc["meshes"]))
print("draw_calls_without_batching", draws)
print("materials", len(doc["materials"]))
print("extensionsUsed", doc.get("extensionsUsed"))
print("extensionsRequired", doc.get("extensionsRequired"))
for m in doc["materials"]:
    pbr = m.get("pbrMetallicRoughness", {})
    if "baseColorFactor" in pbr or "alphaMode" in m:
        print(" ", m["name"], "factor", pbr.get("baseColorFactor"), "alpha", m.get("alphaMode"))

print("--- WebP loss vs source ---")
SRC = {"yn_vermilion_basecolor_2k": ".jpg", "yn_vermilion_normal_2k": ".jpg", "yn_roof_basecolor_2k": ".jpg",
       "yn_roof_normal_2k": ".jpg", "yn_cedar_basecolor_2k": ".jpg", "yn_paving_basecolor_2k": ".jpg",
       "yn_signs_basecolor_2k": ".png", "yn_noren_basecolor_2k": ".png"}
for img in doc["images"]:
    if img.get("name") not in SRC:
        continue
    view = doc["bufferViews"][img["bufferView"]]
    start = view.get("byteOffset", 0)
    data = blob[start:start + view["byteLength"]]
    got = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
    src = np.asarray(Image.open(os.path.join(tex_dir, img["name"] + SRC[img["name"]])).convert("RGB"))
    print(f"  {img['name']:30s} {img.get('mimeType')} {len(data) // 1024:5d}KB  PSNR {psnr(got, src):.1f} dB")
