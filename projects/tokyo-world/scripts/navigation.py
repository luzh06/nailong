"""Generate collision solids and ground from the exact delivered web geometry."""
import argparse
import json
import math
from pathlib import Path
import sys
import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gltf_geometry import primitives, outside_box

ap=argparse.ArgumentParser()
ap.add_argument('--package',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
web=args.package/'web';world=json.loads((web/'world.json').read_text(encoding='utf-8'))
floors=[];solids=[];stats={}

def consume(path,base=None,props=False):
    count=0
    for name,material,vertices,indices in primitives(path,base):
        if name.startswith(('prop_','bkp_','bk_far')):continue
        if props and '_COL' not in name.upper():continue
        t=vertices[indices];lo=t.min(axis=1);hi=t.max(axis=1)
        keep=(hi[:,0]>=-58)&(lo[:,0]<=86)&(hi[:,2]>=-38)&(lo[:,2]<=98)&(hi[:,1]>=-.8)&(lo[:,1]<=6.8)
        t=t[keep]
        if not len(t):continue
        if not len(t):continue
        cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(cross,axis=1);normals=cross/np.maximum(area[:,None],1e-12)
        isfloor=('_ground' in name.lower() or name in ('S_site','bk_stone','bk_ground','bk_apron','bk_road_a','bk_road_b','bk_pavers','bk_soil'))
        if isfloor:floors.append(t[(normals[:,1]>.65)&(area>.0001)])
        t=t[(normals[:,1]<.65)&(area>.004)]
        if not len(t):continue
        mesh=bpy.data.meshes.new('collision-temp');mesh.from_pydata(t.reshape(-1,3).tolist(),[],np.arange(len(t)*3).reshape(-1,3).tolist())
        bm=bmesh.new();bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0002)
        bmesh.ops.dissolve_limit(bm,angle_limit=.015,verts=list(bm.verts),edges=list(bm.edges),use_dissolve_boundaries=False)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        result=np.array([[tuple(v.co) for v in f.verts] for f in bm.faces if len(f.verts)==3],dtype='f4')
        if len(result):solids.append(result);count+=len(result)
        bm.free();bpy.data.meshes.remove(mesh)
    stats[path.name]=stats.get(path.name,0)+count;print('COLLISION',path.name,count,flush=True)

consume(web/'data/bk.glb')
for layer in world['layers']:
    if not layer.get('background'):consume(web/layer['url'])
for p in world['placements']:
    east,north,z=p['center_enu'];oe,on=p['outward_enu']
    cx,cy,cz=p.get('center_qs_h1',[1.8-north,east+32.5,z]);nx,ny=p.get('outward_qs_h1',[-on,oe])
    angle=math.atan2(ny,nx)+math.pi/2;s=p.get('scale',1);d=p.get('offset',0)
    c=math.cos(angle);sn=math.sin(angle);m=np.array([[c*s,0,sn*s,cx+nx*d],[0,s,0,cz],[-sn*s,0,c*s,-cy-ny*d],[0,0,0,1]])
    consume(web/world['props'][p['asset']]['url'],m,props=True)
def quad(x0,x1,y0,y1,z0,z1):
    a=[x0,z0,-y0];b=[x1,z1,-y0];c=[x1,z1,-y1];d=[x0,z0,-y1]
    return np.array([[a,b,c],[a,c,d]],dtype='f4')
floors.append(quad(-2.3,2.3,-62.05,-33.95,-.008,-.008))
f=np.concatenate(floors);verts=f.reshape(-1,3)
v=[Vector((float(x),float(-z),float(y))) for x,y,z in verts]
tree=BVHTree.FromPolygons(v,np.arange(len(v)).reshape(-1,3).tolist(),all_triangles=True)
x0,y0,step,nx,ny=-58,-98,.25,577,545
heights=[]
for j in range(ny):
    y=y0+j*step
    for i in range(nx):
        x=x0+i*step
        inside=(-40<=x<=51 and -91<=y<=1.5) or (-2.05<=x<=2.05 and 1.5<y<=18.5) or (41.8<=x<=84 and -21<=y<=15.6)
        hit=tree.ray_cast(Vector((x,y,7)),Vector((0,0,-1)),9)[0] if inside else None
        heights.append(round(hit.z,3) if hit else None)
args.out.mkdir(parents=True,exist_ok=True)
data={'x0':x0,'y0':y0,'step':step,'nx':nx,'ny':ny,'heights':heights}
(args.out/'navigation.json').write_text(json.dumps(data,separators=(',',':')))
t=np.concatenate(solids).astype('<f4');t.tofile(args.out/'collision.bin')
(args.out/'collision-info.json').write_text(json.dumps({'triangles':len(t),'sources':stats},indent=2))
print('DONE',len(t),'triangles',sum(h is not None for h in heights),'floor cells',flush=True)
