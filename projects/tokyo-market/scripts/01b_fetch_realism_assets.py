"""画面真实感用的 Poly Haven CC0 素材: 三张天空 HDRI 和几种真实墙面。来源写进 textures/sources_realism.json。"""
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "textures")
HDR = os.path.join(ROOT, "hdri")
UA = {"User-Agent": "Cijian-project/0.1"}

HDRIS = {"morning": "kloppenheim_06_puresky", "sunset": "belfast_sunset_puresky", "dusk": "qwantani_dusk_2_puresky"}
WALLS = {"plaster": "white_plaster_rough_01", "concrete": "concrete_wall_006", "tile": "rectangular_facade_tiles",
         "brick": "red_brick_03", "paint": "painted_concrete"}
MAPS = {"Diffuse": "diff", "nor_gl": "nor_gl", "arm": "arm"}


def get_json(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except OSError as e:
            print("retry", e)
            if attempt == 3:
                raise
            time.sleep(15)


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(path, "wb") as f:
        f.write(r.read())


def main():
    os.makedirs(HDR, exist_ok=True)
    sources = {}
    for look, asset in HDRIS.items():
        url = get_json(f"https://api.polyhaven.com/files/{asset}")["hdri"]["8k"]["hdr"]["url"]
        path = os.path.join(HDR, f"{look}.hdr")
        download(url, path)
        info = get_json(f"https://api.polyhaven.com/info/{asset}")
        sources[f"hdri_{look}"] = {"asset": asset, "url": f"https://polyhaven.com/a/{asset}", "authors": list(info["authors"]), "license": "CC0"}
        print(look, asset, round(os.path.getsize(path) / 1048576, 1), "MB")
    for role, asset in WALLS.items():
        files = get_json(f"https://api.polyhaven.com/files/{asset}")
        info = get_json(f"https://api.polyhaven.com/info/{asset}")
        for key, short in MAPS.items():
            download(files[key]["2k"]["jpg"]["url"], os.path.join(TEX, f"wall_{role}_{short}_2k.jpg"))
        sources[f"wall_{role}"] = {"asset": asset, "url": f"https://polyhaven.com/a/{asset}", "authors": list(info["authors"]), "license": "CC0",
                                   "dimensions_mm": info.get("dimensions")}
        print(role, asset, info.get("dimensions"))
    with open(os.path.join(TEX, "sources_realism.json"), "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
