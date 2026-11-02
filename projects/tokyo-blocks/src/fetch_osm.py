import urllib.request, urllib.parse, json
q='[out:json][timeout:30];(way["highway"](35.7255,139.7640,35.7300,139.7700);way["building"](35.7262,139.7650,35.7292,139.7690););out tags geom;'
for ep in ["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter","https://overpass.private.coffee/api/interpreter"]:
    try:
        rq=urllib.request.Request(ep,data=urllib.parse.urlencode({"data":q}).encode(),headers={"User-Agent":"cijian-research/1.0"})
        d=urllib.request.urlopen(rq,timeout=60).read()
        open(r"D:\Cijian\data\osm_yanaka.json","wb").write(d); print("ok",ep,len(d)); break
    except Exception as e: print("fail",ep,e)
