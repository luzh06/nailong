"""店内和商品实拍, 自用贴图。取 1920 像素版, 控制请求频率, 被限流就停下, 再跑一次会跳过已有文件。"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "reference", "shops")
UA = {"User-Agent": "CijianReferenceResearch/0.1 (personal project)"}
API = "https://commons.wikimedia.org/w/api.php"
SEARCHES = ["Nakamise shop souvenirs Asakusa", "Japanese souvenir shop display", "Asakusa souvenir shop interior",
            "Japanese sweets shop display senbei", "tenugui shop display Japan", "Japanese fans shop display"]
WANT = ["05 Nakamise-dori, Asakusa (Tòquio), gats de la bona sort (Maneki Neko).jpg",
        "06 Nakamise-dori, Asakusa (Tòquio), aparador de nines.jpg",
        "Sake Set Asakusa (1).jpg", "Nakamise-Dori (3800868893).jpg",
        "Nakamise Dori 仲見世通り (191500421).jpeg", "Nakamise by Aranril in Asakusa, Tokyo.jpg"]
LIMIT = 16


def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError:
            raise
        except OSError as e:  # 这个网络环境偶尔断连, 等一会再试
            print("retry", attempt + 1, str(e)[:60])
            if attempt == 3:
                raise
            time.sleep(25)


def main():
    os.makedirs(OUT, exist_ok=True)
    names = list(WANT)
    for term in SEARCHES:
        q = urllib.parse.urlencode({"action": "query", "format": "json", "list": "search", "srnamespace": 6, "srlimit": 4, "srsearch": term})
        result = json.loads(fetch(f"{API}?{q}"))
        if "query" not in result:
            print("search skipped:", str(result.get("error", result))[:100])
            time.sleep(15)
            continue
        for hit in result["query"]["search"]:
            t = hit["title"][5:]
            if t.lower().endswith((".jpg", ".jpeg")) and t not in names:
                names.append(t)
        time.sleep(1)
    sources = []
    try:
        for i, name in enumerate(names[:LIMIT], 1):
            q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": "File:" + name, "prop": "imageinfo",
                                        "iiprop": "url|extmetadata", "iiurlwidth": 1920})
            info = next(iter(json.loads(fetch(f"{API}?{q}"))["query"]["pages"].values()))["imageinfo"][0]
            path = os.path.join(OUT, f"shop_{i:02d}.jpg")
            if not os.path.exists(path):
                data = fetch(info["thumburl"])  # 先下完再写文件, 断线不留空文件
                with open(path, "wb") as f:
                    f.write(data)
                time.sleep(10)
            meta = info["extmetadata"]
            sources.append({"local": f"shop_{i:02d}.jpg", "title": name, "page": info["descriptionurl"],
                            "author": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()[:80],
                            "license": meta.get("LicenseShortName", {}).get("value", "")})
            print(i, name[:60], sources[-1]["license"])
    except urllib.error.HTTPError as e:
        print("STOPPED", e)
    with open(os.path.join(OUT, "sources.json"), "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
