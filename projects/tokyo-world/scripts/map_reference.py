"""Render the map from actual web triangles, without generating geography or footprints.

The earlier image-model illustration is retained only as a decorative paper source.
This map uses orthographic projection of the delivered geometry, including bk.glb.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,r'D:\project\cijian\work\.pydeps')
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from gltf_geometry import primitives

ap=argparse.ArgumentParser()
ap.add_argument('--web',type=Path,default=Path(r'D:\project\chatgpt\ci\output\tokyo-three\web'))
ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'web/map')
ap.add_argument('--size',type=int,default=1536)
args=ap.parse_args()
root=args.web;out=args.out;out.mkdir(parents=True,exist_ok=True)
S=args.size
bounds={'eastMin':-137,'eastMax':22,'northMin':-88,'northMax':71,'width':S,'height':S}

def xy(e,n):
    return ((e-bounds['eastMin'])/159*S,(bounds['northMax']-n)/159*S)

def projected(v):
    return np.stack(((-v[...,2]-32.5+137)/159*S,(71-1.8+v[...,0])/159*S),axis=-1)

def split_outside(poly,axis,value,sign):
    """Partition a convex polygon by one boundary of the shader's removal box."""
    inside=[];outside=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        d=(p[axis]-value)*sign;f=(q[axis]-value)*sign
        (inside if d>=0 else outside).append(p)
        if (d>=0)!=(f>=0):
            r=tuple(p[k]+(q[k]-p[k])*d/(d-f) for k in range(2))
            inside.append(r);outside.append(r)
    return inside,outside

cross0=xy(-61.2,12.3);cross1=xy(-52.6,-8.7)
clipbox=(cross0[0],cross1[0],cross0[1],cross1[1])

def outside_crossing(poly):
    x0,x1,y0,y1=clipbox
    if max(p[0] for p in poly)<x0 or min(p[0] for p in poly)>x1 or max(p[1] for p in poly)<y0 or min(p[1] for p in poly)>y1:
        return [poly]
    remaining=poly;parts=[]
    for axis,value,sign in [(0,x0,1),(0,x1,-1),(1,y0,1),(1,y1,-1)]:
        if not remaining:break
        remaining,outer=split_outside(remaining,axis,value,sign)
        if len(outer)>=3:parts.append(outer)
    return parts

world=json.loads((root/'world.json').read_text(encoding='utf-8'))
sources=[('core',root/'data/bk.glb')]+[(x['id'],root/x['url']) for x in world['layers'] if not x.get('background')]
floor_faces=[];building_faces=[];audit=[]
floor_names={'bk_stone','bk_ground','bk_apron','bk_road_a','bk_road_b','bk_pavers','bk_soil','S_site'}
for layer,path in sources:
    count=0
    for name,mat,v,idx in primitives(path):
        if name.startswith(('prop_','bkp_','bk_far')):continue
        if name in ('bk_cable','bk_pipe','bk_pole','bk_steel','bk_xfmr','bk_lens','bk_rail_green','bk_rail_top'):continue
        t=v[idx];normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(normal,axis=1)
        up=normal[:,1]/np.maximum(area,1e-12)
        lo=t.min(axis=1);hi=t.max(axis=1)
        keep=(up>.12)&(area>.003)&(hi[:,0]>-69.2)&(lo[:,0]<89.8)&(hi[:,2]>-54.5)&(lo[:,2]<104.5)
        if layer=='core':keep &= area<400  # Generic background plane is not geographic ground detail.
        t=t[keep];unit=normal[keep]/np.maximum(area[keep,None],1e-12)
        if not len(t):continue
        points=projected(t);heights=t[:,:,1].mean(axis=1)
        floor='_ground' in name.lower() or name in floor_names
        if floor:
            base=(229,222,205) if any(s in mat.lower() for s in ('asphalt','road','pave','granite','stone')) else (220,221,201)
        elif any(s in mat.lower() for s in ('roof','kawara','slate','galva','tile')):base=(134,144,130)
        elif layer=='S' and any(s in mat.lower() for s in ('shu','paint','lacq','plank')):base=(170,110,83)
        else:base=(190,185,160)
        for triangle,height,normal3 in zip(points,heights,unit):
            if not floor and height<.45:continue
            shade=(normal3[0]*18-normal3[2]*12+min(height,35)*.24) if not floor else min(height,5)*.65
            color=tuple(max(0,min(255,round(c+shade))) for c in base)+(255,)
            poly=[tuple(float(c) for c in p) for p in triangle]
            clipped=[poly]  # Core is now repaired geometry; no fragment-discard box.
            target=floor_faces if floor else building_faces
            target.extend((float(height),p,color) for p in clipped)
            count+=1
    audit.append({'layer':layer,'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'projectedTriangles':count})
    print('MAP',layer,count,flush=True)

ground=Image.new('RGBA',(S,S),(0,0,0,0));draw=ImageDraw.Draw(ground)
for h,p,c in sorted(floor_faces,key=lambda q:q[0]):draw.polygon(p,fill=c)
# Match the visible bridge already declared in the viewer, rather than invent a road.
a=projected(np.array([[-2.3,-.008,62.05],[2.3,-.008,62.05],[2.3,-.008,33.95],[-2.3,-.008,33.95]]))
draw.polygon([tuple(p) for p in a],fill=(225,219,203,255))
buildings=Image.new('RGBA',(S,S),(0,0,0,0));draw=ImageDraw.Draw(buildings)
for h,p,c in sorted(building_faces,key=lambda q:q[0]):draw.polygon(p,fill=c)
alpha=buildings.getchannel('A');edges=alpha.filter(ImageFilter.FIND_EDGES)
ink=Image.new('RGBA',(S,S),(74,82,66,190));ink.putalpha(edges.point(lambda p:round(p*.56)))
buildings.alpha_composite(ink)
ground.alpha_composite(buildings)
ground.save(out/'actual-map.png',optimize=True)
# Preview uses a plain paper colour. Runtime paper decoration never changes geometry.
preview=Image.new('RGBA',(S,S),(238,232,217,255));preview.alpha_composite(ground)
preview.convert('RGB').save(out/'actual-map-preview.jpg',quality=93)
(out/'registration.json').write_text(json.dumps(bounds,indent=2))
(out/'map-provenance.json').write_text(json.dumps({'projection':'orthographic ENU, north up','bounds':bounds,'inputs':audit,'note':'Actual delivered model geometry. Senso-ji is the authored fictional splice, not its real geographic location. Generated illustration is decorative only.'},ensure_ascii=False,indent=2))
print('READY',out/'actual-map.png',flush=True)
