import json, os, shutil, subprocess, sys
R=r"D:\project\cijian\work\export\blocks"; O=r"D:\project\cijian\work\output\blocks"
def m(p): return [round(1.8-p[1],3), round(p[0]+32.5,3)]
ZD=7.95
GZ=[(-135,7.47),(-118,7.5),(-100,7.6),(-92,7.78),(-84,8.0),(-76,8.28),(-67,8.36),(-50,8.5)]
def gz(x):
    for i in range(len(GZ)-1):
        if x<=GZ[i+1][0]:
            t=max(0,(x-GZ[i][0])/(GZ[i+1][0]-GZ[i][0])); return round(GZ[i][1]+(GZ[i+1][1]-GZ[i][1])*t-ZD,3)
    return round(GZ[-1][1]-ZD,3)
def pt(n,E,N): return dict(name=n,enu=[E,N],qs_h1=[*m((E,N)),gz(E)])
FINAL={"A":("A_r5",["lane","alley","south","diag","roof","close"]),"B":("B_r4",["back","road","yard","roof","side","close"])}
IF={"A":[pt("小巷东端，接斜路",-60.7,-21.8),pt("小巷西端，出街块",-119.1,-18.5),pt("后巷东出口，接小巷",-73.4,-23.4),pt("后巷西端",-119.5,-29.15),pt("南路西端",-119.1,-42.2),pt("南路东端，接斜路",-71.9,-50.2),pt("斜路北端",-58.0,-26.8),pt("斜路南端",-69.4,-52.6)],
    "B":[pt("后巷西端",-111.5,14.15),pt("后巷东端，接东路",-57.6,14.15),pt("侧巷北端（尽头）",-99.15,25.2),pt("东路南端",-55.3,13.0),pt("东路北端",-58.0,48.0),pt("西路南端",-105.4,33.4)]}
for B,(tag,cams) in FINAL.items():
    d=os.path.join(R,"block_"+B); pv=os.path.join(d,"preview"); os.makedirs(pv,exist_ok=True)
    for c in cams: shutil.copy(os.path.join(O,f"{tag}_{c}.jpg"),os.path.join(pv,f"{B}_{c}.jpg"))
    shutil.copy(os.path.join(O,f"glb_check_{B}.jpg"),os.path.join(pv,f"{B}_glb_reimport_check.jpg"))
    subprocess.run([sys.executable,"-I",r"D:\project\cijian\work\src\glb_stats.py",os.path.join(d,f"block_{B}.glb"),os.path.join(d,"textures")],check=True)
    meta=json.load(open(os.path.join(d,f"block_{B}_meta.json"),encoding="utf8"))
    an=[]
    for a in meta["anchors"]:
        e=a["center_enu"]; o=a["outward_enu"]
        an.append(dict(a,center_qs_h1=[*m(e),round(e[2],3)],outward_qs_h1=[round(-o[1],4),round(o[0],4)]))
    json.dump(dict(block=B,note="预留位。店面和小道具由 5060 做；坐标已是 qs_h1 世界系，外法线 outward 指向路面",anchors=an),open(os.path.join(d,f"block_{B}_anchors.json"),"w",encoding="utf8"),indent=1,ensure_ascii=False)
    meta["interface_points"]=IF[B]
    json.dump(meta,open(os.path.join(d,f"block_{B}_meta.json"),"w",encoding="utf8"),indent=1,ensure_ascii=False)
    s=json.load(open(os.path.join(d,f"block_{B}_stats.json"),encoding="utf8"))
    print(B,s["glb_mb"],s["triangles"],s["materials"],s["textures"],s["texture_mb"],s["max_texture"],len(an),sum(1 for a in an if a["type"]=="storefront"),[(p["name"],p["qs_h1"]) for p in IF[B]])
print(sum(os.path.getsize(os.path.join(a,f)) for a,_,fs in os.walk(r"D:\project\cijian\work") for f in fs)/1e9)
