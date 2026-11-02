"""下载用户确认的 12 张维基共享资源照片, 只作建模参考, 不当贴图。
原图请求被站点限流 (HTTP 429), 按站点建议改取 1920 像素的标准缩略图; 已下好的原图保留。
作者和许可写到 reference/web/sources.json。
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "reference", "web")
THUMBS = os.path.join(OUT, "thumbs")
UA = {"User-Agent": "CijianReferenceResearch/0.1 (personal project)"}
API = "https://commons.wikimedia.org/w/api.php"
WIDTH = 1920
PAUSE = 12

FILES = [
    "Sensō-ji Tempel mit Nakamise-dor.jpg",
    "Five-storied pagoda and Sensō-ji Hōzōmon at night, Asakusa, Tokyo, 2016.jpg",
    "Hozomon (main gate), Sensoji Temple, Asakusa, Tokyo.jpg",
    "Hozomon and pagoda, Sensoji Temple, Asakusa, Tokyo.jpg",
    "Sensō-ji. Asakusa Tokyo. (41781495365).jpg",
    "Nakamise-Dōri, Asakusa (9409495501).jpg",
    "Nakamise-Dōri by night (9412263950).jpg",
    "Nakamise-Dōri, Asakusa on a rainy evening (9409049063).jpg",
    "Side Street of Nakamise-Dōri (15204175141).jpg",
    "Hōzōmon, Sensōji 20241030.jpg",
    "Five-storied Pagoda, Sensoji, Tokyo, 20240824 1103 5616.jpg",
    "07 Nakamise-dori, Asakusa (Tòquio), decoració pictòrica a la persiana d'una botiga.jpg",
]


class Limited(Exception):
    pass


def fetch(url):
    """被限流就停下, 不反复重试; 只对连接重置等一次。"""
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise Limited(str(e)) from e
            raise
        except OSError as e:
            print("retry", e)
            if attempt == 1:
                raise
            time.sleep(30)


def main():
    os.makedirs(THUMBS, exist_ok=True)
    sources_path = os.path.join(OUT, "sources.json")
    sources = []
    try:
        for i, name in enumerate(FILES, 1):
            q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": "File:" + name, "prop": "imageinfo",
                                        "iiprop": "url|size|extmetadata", "iiurlwidth": WIDTH})
            page = next(iter(json.loads(fetch(f"{API}?{q}"))["query"]["pages"].values()))
            info = page["imageinfo"][0]
            meta = info["extmetadata"]
            local = f"web_{i:02d}.jpg"
            path = os.path.join(OUT, local)
            if not (os.path.exists(path) and os.path.getsize(path) > 0):
                data = fetch(info["thumburl"])
                with open(path, "wb") as f:
                    f.write(data)
                time.sleep(PAUSE)
            artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()
            im = Image.open(path).convert("RGB")
            w, h = im.size
            im.thumbnail((1200, 1200))
            im.save(os.path.join(THUMBS, local), quality=85)
            sources.append({"local": local, "title": name, "page": info["descriptionurl"], "author": artist,
                            "license": meta.get("LicenseShortName", {}).get("value", ""),
                            "saved_size": f"{w}x{h}", "original_size": f"{info['width']}x{info['height']}"})
            print(local, f"{w}x{h}", round(os.path.getsize(path) / 1048576, 2), "MB |", sources[-1]["license"], "|", artist[:50])
            time.sleep(2)
    except Limited as e:
        print("STOPPED, rate limited at", len(sources) + 1, e)
    with open(sources_path, "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)
    print("done", len(sources), "of", len(FILES))


if __name__ == "__main__":
    main()
