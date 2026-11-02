"""直接解析 GLB 文件核验: 三角面数, UV 套数, 朝向和原点, 贴图, 文件大小。
用法: python verify_glb.py <a.glb> [b.glb ...]
"""
import io
import json
import os
import struct
import sys

from PIL import Image


def read_glb(path):
    with open(path, "rb") as f:
        magic, version, _ = struct.unpack("<III", f.read(12))
        assert magic == 0x46546C67, "not a GLB"
        length, kind = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(length))
        length, kind = struct.unpack("<II", f.read(8))
        return doc, f.read(length), version


def report(path):
    doc, blob, version = read_glb(path)
    tris = 0
    uv_sets = set()
    mins = [1e9] * 3
    maxs = [-1e9] * 3
    for node in doc.get("nodes", []):
        if "mesh" not in node:
            continue
        t = node.get("translation", [0, 0, 0])
        rotated = "rotation" in node and node["rotation"] != [0, 0, 0, 1]
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            count = doc["accessors"][prim["indices"]]["count"]
            tris += count // 3
            uv_sets.add(sum(1 for k in prim["attributes"] if k.startswith("TEXCOORD_")))
            pos = doc["accessors"][prim["attributes"]["POSITION"]]
            if not rotated:
                for i in range(3):
                    mins[i] = min(mins[i], pos["min"][i] + t[i])
                    maxs[i] = max(maxs[i], pos["max"][i] + t[i])
    images = []
    for img in doc.get("images", []):
        view = doc["bufferViews"][img["bufferView"]]
        data = blob[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]]
        im = Image.open(io.BytesIO(data))
        images.append({"name": img.get("name"), "size": f"{im.width}x{im.height}", "KB": round(len(data) / 1024)})
    mats = []
    for m in doc.get("materials", []):
        pbr = m.get("pbrMetallicRoughness", {})
        mats.append({
            "name": m["name"],
            "base": "baseColorTexture" in pbr,
            "orm": "metallicRoughnessTexture" in pbr,
            "ao": "occlusionTexture" in m,
            "normal": "normalTexture" in m,
            "emissive": "emissiveTexture" in m or "emissiveFactor" in m,
            "double_sided": m.get("doubleSided", False),
        })
    tex_bytes = sum(i["KB"] for i in images)
    return {
        "file": os.path.basename(path),
        "glb_version": version,
        "size_MB": round(os.path.getsize(path) / 1024 / 1024, 2),
        "tris": tris,
        "meshes": len(doc.get("meshes", [])),
        "uv_sets_per_primitive": sorted(uv_sets),
        "bounds_min_xyz": [round(v, 3) for v in mins],
        "bounds_max_xyz": [round(v, 3) for v in maxs],
        "textures_KB": tex_bytes,
        "images": images,
        "materials": mats,
    }


if __name__ == "__main__":
    out = [report(p) for p in sys.argv[1:]]
    print(json.dumps(out, ensure_ascii=False, indent=1))
