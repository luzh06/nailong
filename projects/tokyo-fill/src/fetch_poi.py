# All tagged OSM objects around the 80x80 m area, printed in ENU metres (origin = stair top).
import urllib.request, urllib.parse, json, time
LAT0, LON0 = 35.727641, 139.767341
q = '[out:json][timeout:60];nwr(35.7266,139.7655,35.7286,139.7678);out tags center;'
EPS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
d = None
for ep in EPS * 2:
    try:
        rq = urllib.request.Request(ep, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "cijian-research/1.0"})
        d = json.loads(urllib.request.urlopen(rq, timeout=90).read()); print("ok", ep); break
    except Exception as e:
        print("fail", ep, e); time.sleep(3)
open(r"D:\project\cijian\work\data\osm_poi.json", "w", encoding="utf8").write(json.dumps(d, ensure_ascii=False))
KEEP = ("name", "amenity", "shop", "landuse", "leisure", "highway", "building", "parking", "barrier", "tourism", "historic", "surface", "width", "religion", "craft", "office", "building:levels")
for e in d["elements"]:
    c = e.get("center") or e; lat, lon = c.get("lat"), c.get("lon")
    if lat is None or not e.get("tags"): continue
    E = (lon - LON0) * 90350; N = (lat - LAT0) * 110950
    t = {k: v for k, v in e["tags"].items() if k in KEEP}
    if t and -130 < E < -25 and -45 < N < 55 and set(t) != {"building"}:
        print(f"{e['type'][0]} E{E:7.1f} N{N:6.1f}", t)
