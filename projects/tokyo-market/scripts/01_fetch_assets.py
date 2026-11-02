"""下载 Poly Haven CC0 贴图和 OFL 字体, 并把来源写到 textures/sources.json。
用法: python 01_fetch_assets.py
"""
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
FONT = os.path.join(ROOT, "fonts")
UA = {"User-Agent": "Cijian-project/0.1"}

# 用途 -> Poly Haven 资产 id
TEXTURES = {
    "roof": "grey_roof_tiles_02",
    "paint_wood": "distressed_painted_planks",
    "cedar": "japanese_cedar_planks",
    "shutter": "painted_metal_shutter",
    "plaster": "plastered_wall_02",
    "paving": "rectangular_paving",
    "corrugated": "corrugated_iron_02",
}
MAPS = {"Diffuse": "diff", "nor_gl": "nor_gl", "arm": "arm"}
FONT_FILES = {
    "ZenAntique-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/zenantique/ZenAntique-Regular.ttf",
    "ZenAntique-OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/zenantique/OFL.txt",
}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
        f.write(r.read())


def main():
    sources = {}
    for role, asset in TEXTURES.items():
        files = get_json(f"https://api.polyhaven.com/files/{asset}")
        info = get_json(f"https://api.polyhaven.com/info/{asset}")
        for key, short in MAPS.items():
            url = files[key]["2k"]["jpg"]["url"]
            download(url, os.path.join(TEX, f"{asset}_{short}_2k.jpg"))
        sources[role] = {
            "asset": asset,
            "url": f"https://polyhaven.com/a/{asset}",
            "authors": list(info.get("authors", {}).keys()),
            "license": "CC0",
            "dimensions_mm": info.get("dimensions"),
        }
        print(role, asset, sources[role]["dimensions_mm"], sources[role]["authors"])
    for name, url in FONT_FILES.items():
        download(url, os.path.join(FONT, name))
        print(name, os.path.getsize(os.path.join(FONT, name)))
    with open(os.path.join(TEX, "sources.json"), "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
