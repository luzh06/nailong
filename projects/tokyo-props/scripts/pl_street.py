# pl_street.py: frontages along Yanaka Ginza from PLATEAU LOD building footprints (coords in EPSG:6697 lat lon h)
import json,subprocess,os,math,re,statistics as st
import xml.etree.ElementTree as ET
D=r'D:\Cijian\assets\plateau'
BASE='https://assets.cms.plateau.reearth.io/assets/80/45b2b1-5a88-40ab-9877-70b540b8707e/13106_taito-ku_city_2025_citygml_1_op/udx/'
for k,n in (('bldg','53394671_bldg_6697_op.gml'),('tran','53394671_tran_6697_op.gml')):
    p=os.path.join(D,'13106_'+n)
    if not (os.path.exists(p) and os.path.getsize(p)>10000):
        for t in range(8):
            r=subprocess.run(['curl.exe','-sS','-L','-f','--compressed','--connect-timeout','15','-m','170','-o',p,BASE+k+'/'+n],capture_output=True,text=True)
            print(k,'try',t,r.returncode,r.stderr[:80],os.path.getsize(p)//1024 if os.path.exists(p) else 0,'KB',flush=True)
            if r.returncode==0: break
# street centre line, west to east (approximate, from 35.7278/139.7648 to the stairs top 35.7279/139.7664)
LINE=[(35.72778,139.76470),(35.72783,139.76510),(35.72788,139.76560),(35.72790,139.76610),(35.72792,139.76645)]
lat0=LINE[0][0]; mx=111320*math.cos(math.radians(lat0)); my=110940
def xy(la,lo): return ((lo-LINE[0][1])*mx,(la-lat0)*my)
L=[xy(*p) for p in LINE]
def nearest(px,py):
    best=(1e9,0,0); s0=0
    for (ax,ay),(bx,by) in zip(L,L[1:]):
        dx,dy=bx-ax,by-ay; ln=math.hypot(dx,dy); t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/ln/ln))
        cx,cy=ax+dx*t,ay+dy*t; d=math.hypot(px-cx,py-cy)
        sgn=1 if dx*(py-ay)-dy*(px-ax)>0 else -1
        if d<best[0]: best=(d,s0+t*ln,sgn)
        s0+=ln
    return best
NS={}
txt=open(os.path.join(D,'13106_53394671_bldg_6697_op.gml'),encoding='utf8').read()
print('size',len(txt)//1024,'KB')
out=[]
for m in re.finditer(r'<bldg:Building[ >].*?</bldg:Building>',txt,re.S):
    b=m.group(0)
    h=re.search(r'<bldg:measuredHeight[^>]*>([\d.]+)',b)
    st_=re.search(r'storeysAboveGround>(\d+)',b)
    fp=re.search(r'<bldg:lod0(?:RoofEdge|FootPrint).*?<gml:posList[^>]*>(.*?)</gml:posList>',b,re.S) or re.search(r'<gml:posList[^>]*>(.*?)</gml:posList>',b,re.S)
    if not fp: continue
    v=list(map(float,fp.group(1).split()))
    pts=[xy(v[i],v[i+1]) for i in range(0,len(v),3)]
    n=[nearest(*p) for p in pts]
    if min(x[0] for x in n)>7.5: continue
    ss=[x[1] for x in n if x[0]<9]
    if not ss: continue
    out.append(dict(side=max(n,key=lambda x:-x[0])[2],s0=round(min(ss),1),w=round(max(ss)-min(ss),1),h=float(h.group(1)) if h else None,fl=int(st_.group(1)) if st_ else None,d=round(min(x[0] for x in n),1)))
out.sort(key=lambda o:(o['side'],o['s0']))
json.dump(out,open(os.path.join(D,'yanaka_frontage.json'),'w'),indent=0)
print(len(out))
for o in out: print(o)
ws=[o['w'] for o in out if o['w']>1.5]; hs=[o['h'] for o in out if o['h']]
print('median frontage',st.median(ws),'median h',st.median(hs),'kerb distance median',st.median([o['d'] for o in out]))
print('END')
