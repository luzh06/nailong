import json, math
from PIL import Image, ImageDraw, ImageFont
d=json.load(open(r"D:\Cijian\data\plateau_near.json"))
S=7.0; W=H=1400; CX,CY=-40,0   # centre of view in metres
def P(x,y): return (W/2+(x-CX)*S, H/2-(y-CY)*S)
im=Image.new("RGB",(W,H),(245,243,238)); dr=ImageDraw.Draw(im)
for r in d["roads"]:
    for p in r["polys"]:
        if len(p)>2: dr.polygon([P(a,b) for a,b,c in p],fill=(215,215,220),outline=(170,170,180))
for b in d["buildings"]:
    fp=b["lod"].get("lod0",[[]])[0]
    if len(fp)<3: continue
    h=float(b["attrs"].get("measuredHeight",0) or 0); st=int(b["attrs"].get("storeysAboveGround",0) or 0)
    has2="RoofSurface" in b["lod"]
    col=(150,190,150) if st<=2 else (220,190,120) if st<=4 else (220,130,110)
    if h>=30:col=(190,90,90)
    dr.polygon([P(a,z) for a,z,_ in fp],fill=col,outline=(60,60,60) if has2 else (200,50,200))
    cx=sum(q[0] for q in fp)/len(fp); cy=sum(q[1] for q in fp)/len(fp)
    px=P(cx,cy)
    if 0<=px[0]<W and 0<=px[1]<H: dr.text((px[0]-6,px[1]-5),f"{st}",fill=(0,0,0))
# stairs from OSM
A=(0,0); B=((139.766997-139.767341)*90400,(35.727652-35.727641)*110900)
dr.line([P(*A),P(*B)],fill=(255,0,0),width=6)
for g in range(-200,201,20):
    c=(120,120,255) if g%100==0 else (205,205,240)
    dr.line([P(g,-300),P(g,300)],fill=c); dr.line([P(-300,g),P(300,g)],fill=c)
    dr.text((P(g,0)[0]+2,3),str(g),fill=(0,0,200)); dr.text((3,P(0,g)[1]+2),str(g),fill=(0,0,200))
im.save(r"D:\Cijian\work\plan.jpg",quality=78); print(B)
