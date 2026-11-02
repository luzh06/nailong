# Fetch only the needed members of PLATEAU zips: direct URL first, HTTP-range into the zip otherwise.
import sys, json, os, io, zipfile, urllib.request
OUT=r"D:\Cijian\data\plateau"; os.makedirs(OUT,exist_ok=True)
Z={"taito":"https://assets.cms.plateau.reearth.io/assets/80/45b2b1-5a88-40ab-9877-70b540b8707e/13106_taito-ku_city_2025_citygml_1_op",
   "arakawa":"https://assets.cms.plateau.reearth.io/assets/a1/351cc4-8dfa-4825-b22f-a55a7fe09125/13118_arakawa-ku_pref_2025_citygml_1_op"}
WANT=["udx/bldg/53394671_bldg_6697_op.gml","udx/tran/53394671_tran_6697_op.gml"]
UA={"User-Agent":"cijian-research/1.0"}
class R(io.RawIOBase):
    def __init__(s,u):
        s.u=u; s.p=0
        rq=urllib.request.Request(u,headers=dict(UA,Range="bytes=0-0"))
        with urllib.request.urlopen(rq,timeout=60) as f: s.n=int(f.headers["Content-Range"].split("/")[1])
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.p
    def seek(s,o,w=0):
        s.p={0:o,1:s.p+o,2:s.n+o}[w]; return s.p
    def read(s,k=-1):
        if k<0: k=s.n-s.p
        if k==0 or s.p>=s.n: return b""
        rq=urllib.request.Request(s.u,headers=dict(UA,Range=f"bytes={s.p}-{min(s.p+k,s.n)-1}"))
        with urllib.request.urlopen(rq,timeout=120) as f: b=f.read()
        s.p+=len(b); return b
    def readinto(s,b):
        d=s.read(len(b)); b[:len(d)]=d; return len(d)
for city,base in Z.items():
    for w in WANT:
        dst=os.path.join(OUT,city+"_"+os.path.basename(w))
        if os.path.exists(dst): print("have",dst); continue
        try:
            rq=urllib.request.Request(base+"/"+w,headers=UA)
            with urllib.request.urlopen(rq,timeout=120) as f: d=f.read()
            print("direct",w,len(d))
        except Exception as e:
            print("direct failed",e,"-> range zip",flush=True)
            r=R(base+".zip"); print(" zip GB",r.n/1e9,flush=True)
            z=zipfile.ZipFile(io.BufferedReader(r,1<<20))
            m=[n for n in z.namelist() if n.endswith(w)][0]
            print(" member",m,z.getinfo(m).compress_size,z.getinfo(m).file_size,flush=True)
            d=z.read(m)
        open(dst,"wb").write(d); print("wrote",dst,len(d),flush=True)
