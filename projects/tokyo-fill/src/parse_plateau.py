# Extract buildings and road polygons near the stair top to local metres (x=east, y=north, origin stair top)
import sys, json, math, glob, os
from lxml import etree
LAT0,LON0=35.727641,139.767341
R=250.0
mx=111319.49*math.cos(math.radians(LAT0))*1.0013 if False else None
a=6378137.0; f=1/298.257222101; e2=f*(2-f); s=math.sin(math.radians(LAT0))
N=a/math.sqrt(1-e2*s*s); M=a*(1-e2)/(1-e2*s*s)**1.5
kx=math.radians(1)*N*math.cos(math.radians(LAT0)); ky=math.radians(1)*M
def xy(lat,lon): return (lon-LON0)*kx,(lat-LAT0)*ky
NS={'gml':'http://www.opengis.net/gml'}
G='{http://www.opengis.net/gml}'
def ring(el):
    t=el.text.split(); p=[]
    for i in range(0,len(t),3):
        x,y=xy(float(t[i]),float(t[i+1])); p.append((round(x,3),round(y,3),round(float(t[i+2]),3)))
    return p
def local(tag): return tag.split('}')[-1]
out={"origin":[LAT0,LON0],"buildings":[],"roads":[]}
for fn in sorted(glob.glob(r"D:\project\cijian\work\data\plateau\*_bldg_*.gml")):
    src=os.path.basename(fn); n=0
    for ev,el in etree.iterparse(fn,events=('end',),tag='{*}Building',huge_tree=True):
        pos=el.find('.//'+G+'posList')
        keep=False
        if pos is not None:
            t=pos.text.split()
            x,y=xy(float(t[0]),float(t[1])); keep=abs(x)<R and abs(y)<R
        if keep:
            b={"src":src,"id":el.get(G+'id'),"attrs":{}}
            for c in el:
                ln=local(c.tag)
                if ln in('measuredHeight','storeysAboveGround','storeysBelowGround','usage','class','roofType','yearOfConstruction') and c.text: b["attrs"][ln]=c.text
                if ln in ('buildingDetailAttribute',):
                    for d in c.iter():
                        if local(d.tag) in('buildingStructureType','totalFloorArea','buildingRoofEdgeArea','buildingStructureOrgType','detailedUsage','fireproofStructureType','surveyYear') and d.text: b["attrs"][local(d.tag)]=d.text
            lod={}
            for c in el.iter():
                ln=local(c.tag)
                if ln in('lod0FootPrint','lod0RoofEdge','lod0Polygon'):
                    lod.setdefault('lod0',[]).extend(ring(p) for p in c.iter(G+'posList'))
                elif ln in('RoofSurface','WallSurface','GroundSurface'):
                    lod.setdefault(ln,[]).extend(ring(p) for p in c.iter(G+'posList'))
                elif ln=='lod1Solid':
                    lod.setdefault('lod1',[]).extend(ring(p) for p in c.iter(G+'posList'))
            b["lod"]=lod; out["buildings"].append(b); n+=1
        el.clear()
        while el.getprevious() is not None: del el.getparent()[0]
    print(src,n,flush=True)
for fn in sorted(glob.glob(r"D:\project\cijian\work\data\plateau\*_tran_*.gml")):
    src=os.path.basename(fn); n=0
    for ev,el in etree.iterparse(fn,events=('end',),tag='{*}Road',huge_tree=True):
        polys=[ring(p) for p in el.iter(G+'posList')]
        if polys and any(abs(p[0][0])<R and abs(p[0][1])<R for p in polys):
            lds=set(local(c.tag) for c in el.iter() if isinstance(c.tag,str))
            rec={"src":src,"polys":polys,"func":[c.text for c in el.iter() if isinstance(c.tag,str) and local(c.tag)=='function'],
                 "elems":sorted(x for x in lds if x in('TrafficArea','AuxiliaryTrafficArea','lod1MultiSurface','lod2MultiSurface','lod3MultiSurface'))}
            out["roads"].append(rec); n+=1
        el.clear()
        while el.getprevious() is not None: del el.getparent()[0]
    print(src,n,flush=True)
json.dump(out,open(r"D:\project\cijian\work\data\plateau_near.json","w"))
print("done",len(out["buildings"]),len(out["roads"]))
ids=[b for b in out["buildings"]]
import collections
print(collections.Counter(tuple(sorted(b["lod"].keys())) for b in ids).most_common(6))
print(json.dumps(ids[0]["attrs"],ensure_ascii=True))
