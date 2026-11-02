# Read a GLB without loading it into Blender: triangles, materials, embedded textures, vertex colour check; extract textures
import json, struct, sys, os
p=sys.argv[1]; out=sys.argv[2] if len(sys.argv)>2 else None
f=open(p,"rb"); magic,ver,ln=struct.unpack("<4sII",f.read(12)); assert magic==b"glTF"
jl,jt=struct.unpack("<I4s",f.read(8)); g=json.loads(f.read(jl)); bl,bt=struct.unpack("<I4s",f.read(8)); bin_=f.read(bl)
acc=g["accessors"]; tris=0; bymat={}; col=0; prims=0
for m in g["meshes"]:
    for pr in m["primitives"]:
        prims+=1
        n=acc[pr["indices"]]["count"]//3 if "indices" in pr else acc[pr["attributes"]["POSITION"]]["count"]//3
        tris+=n; k=g["materials"][pr.get("material",0)]["name"]; bymat[k]=bymat.get(k,0)+n
        col+=("COLOR_0" in pr["attributes"])
imgs=[]
if out: os.makedirs(out,exist_ok=True)
# name each image after the first material and role that uses it; embedded names repeat (diff/nor/arm1k)
role={}
def use(tex,mat,r):
    i=g["textures"][tex["index"]]["source"]
    if i not in role: role[i]=f"{mat}_{r}"
for mt in g["materials"]:
    p_=mt.get("pbrMetallicRoughness",{})
    if "baseColorTexture" in p_: use(p_["baseColorTexture"],mt["name"],"base")
    if "metallicRoughnessTexture" in p_: use(p_["metallicRoughnessTexture"],mt["name"],"orm")
    if "normalTexture" in mt: use(mt["normalTexture"],mt["name"],"normal")
for idx,im in enumerate(g.get("images",[])):
    im["name"]=role.get(idx,f"unused_{idx}")
    bv=g["bufferViews"][im["bufferView"]]; b=bin_[bv.get("byteOffset",0):bv.get("byteOffset",0)+bv["byteLength"]]
    w=h=0
    if b[:2]==b"\xff\xd8":
        i=2
        while i<len(b):
            if b[i]!=0xFF: i+=1; continue
            mk=b[i+1]
            if mk in (0xC0,0xC1,0xC2): h,w=struct.unpack(">HH",b[i+5:i+9]); break
            i+=2+struct.unpack(">H",b[i+2:i+4])[0]
    elif b[:4]==b"\x89PNG": w,h=struct.unpack(">II",b[16:24])
    ext=".jpg" if im.get("mimeType")=="image/jpeg" else ".png"
    imgs.append((im.get("name"),w,h,len(b),im.get("mimeType")))
    if out: open(os.path.join(out,im.get("name","img")+ext),"wb").write(b)
missing=[m["name"] for m in g["materials"] if "baseColorTexture" not in m.get("pbrMetallicRoughness",{}) ]
r=dict(file=os.path.basename(p),glb_mb=round(os.path.getsize(p)/1e6,1),triangles=tris,primitives=prims,prims_with_vertex_color=col,meshes=len(g["meshes"]),
       materials=len(g["materials"]),textures=len(imgs),texture_mb=round(sum(i[3] for i in imgs)/1e6,1),max_texture=max((max(i[1],i[2]) for i in imgs),default=0),
       tris_by_material=dict(sorted(bymat.items(),key=lambda kv:-kv[1])),mats_without_base_texture=missing,images=imgs)
print(json.dumps({k:v for k,v in r.items() if k not in("images","tris_by_material")},ensure_ascii=False))
json.dump(r,open(p[:-4]+"_stats.json","w"),indent=1,ensure_ascii=False)
