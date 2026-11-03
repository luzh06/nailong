"""Editable, staged repairs of exposed gables, paving and roof junctions.

All building positions/dimensions come from qs_h1 bounds, paving heights from
the delivered C/D/E triangles. No source building or geographic footprint moves.
"""
import argparse,json,math,os,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gltf_geometry import primitives,read,accessor,transform
ap=argparse.ArgumentParser();ap.add_argument('--stage',type=int,required=True);ap.add_argument('--web',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);args.out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mats={}
for name,color in {'plaster':(.78,.75,.68),'wood':(.5,.45,.36),'asphalt':(.83,.83,.81),'concrete':(.72,.7,.64),'metal':(.28,.3,.28),'soffit':(.62,.54,.43),'gravel':(.72,.68,.6),'roadmark':(.96,.96,.94),'paint':(.90,.90,.86)}.items():
 m=bpy.data.materials.new('repair_'+name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.93;mats[name]=m
def mesh(name,vertices,faces,mat,uv_axes=(0,2),uv_scale=2):
 data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.materials.append(mats[mat]);obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
 uv=data.uv_layers.new(name='UVMap')
 for p in data.polygons:
  for i in p.loop_indices:
   v=data.vertices[data.loops[i].vertex_index].co;uv.data[i].uv=(v[uv_axes[0]]/uv_scale,v[uv_axes[1]]/uv_scale)
 return obj
def box(name,lo,hi,mat,bevel=0):
 x,y,z=lo;a,b,c=hi
 obj=mesh(name,[(x,y,z),(a,y,z),(a,b,z),(x,b,z),(x,y,c),(a,y,c),(a,b,c),(x,b,c)],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],mat)
 if bevel:
  bpy.context.view_layer.objects.active=obj;mod=obj.modifiers.new('worn arris','BEVEL');mod.width=bevel;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
 return obj

# Body and roof bounds were measured from original named, retained houses.
ends=[('Gm13',-9.75,-3.25,-28.135,6.040,7.490,1),('Gm15',-9.75,-3.25,-21.558,5.169,6.619,-1),('Gp14',3.30,9.80,-28.882,5.199,6.649,1)]
for label,x0,x1,y,wall,ridge,outward in ends:
 y+=outward*.018;mid=(x0+x1)/2;eave=wall+.028
 outline=[(x0,y,.015),(x1,y,.015),(x1,y,eave),(mid,y,ridge-.018),(x0,y,eave)]
 # The skin includes a genuine gable closure and thickness, not a visual decal.
 verts=outline+[(x,y-outward*.06,z) for x,y,z in outline]
 faces=[tuple(range(5)),tuple(range(9,4,-1))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
 if outward>0:faces=[tuple(reversed(f)) for f in faces]
 mesh('J_endwall_'+label,verts,faces,'plaster')
 box('J_footing_'+label,(x0,y-.045,.005),(x1,y+.045,.28),'concrete',.015)
 if args.stage>=4:
  # Repair panels, a narrow expansion joint and service battens break up large
  # exposed blind walls without inventing new room openings.
  for x in np.arange(x0+.07,x1-.04,.82):box('J_batten_'+label,(x,y-.048,.3),(x+.025,y+.048,wall-.1),'wood',.004)
  box('J_floorline_'+label,(x0,y-.05,wall*.5),(x1,y+.05,wall*.5+.055),'wood',.006)
 if args.stage>=5:
  # Close the underside of the existing 0.65m overhang along both roof slopes.
  outer_y=y+outward*.62
  for xa,xb,za,zb in [(x0-.54,mid,wall-.19,ridge-.1),(mid,x1+.54,ridge-.1,wall-.19)]:
   mesh('J_soffit_'+label,[(xa,y,za),(xb,y,zb),(xb,outer_y,zb),(xa,outer_y,za)],[(0,3,2,1)],'soffit')
  for i in range(13):
   x=x0+(x1-x0)*i/12;z=eave+(ridge-eave)*(1-abs((x-mid)/((x1-x0)/2)))-.055
   box('J_soffit_joint_'+label,(x-.012,min(y,outer_y),z-.035),(x+.012,max(y,outer_y),z),'wood')
  # Vent slats sit outside the sealed wall; no unmodelled interior appears.
  for k in range(7):box('J_gable_vent_'+label,(mid-.34,y-.07,wall+.17+k*.065),(mid+.34,y+.07,wall+.20+k*.065),'metal',.004)

if args.stage>=3:
 floors=[]
 for layer in ['C','D','E']:
  for name,mat,v,idx in primitives(args.web/f'models/block_{layer}.gltf'):
   if '_ground' not in name.lower() or mat not in ('asphalt','concrete','pave','gravel'):continue
   t=v[idx];normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n=np.linalg.norm(normal,axis=1)
   mask=(normal[:,1]/np.maximum(n,1e-12)>.8)&(t[:,:,0].max(axis=1)>-12)&(t[:,:,0].min(axis=1)<12)&(t[:,:,2].max(axis=1)>18)&(t[:,:,2].min(axis=1)<32)
   t=t[mask];bl=t[:,:,[0,2,1]].copy();bl[:,:,1]*=-1;floors.extend(bl)
 vertices=[Vector(p) for t in floors for p in t];tree=BVHTree.FromPolygons(vertices,np.arange(len(vertices)).reshape(-1,3).tolist(),all_triangles=True)
 def height(x,y):
  hit=tree.ray_cast(Vector((x,y,2)),Vector((0,0,-1)),4)[0]
  if hit is not None:return hit.z+.014
  # The original central street is approximately z=0. No invented DEM slope.
  return .014
 xs=np.linspace(-11.25,11.25,91);ys=np.linspace(-30.1,-19.4,44);paving=[]
 for j in range(len(ys)-1):
  for i in range(len(xs)-1):
   x0,x1=xs[i:i+2];y0,y1=ys[j:j+2];x=(x0+x1)/2;y=(y0+y1)/2
   # Resurface the existing crossing, matching its old model footprint. This
   # buries the stale baked shadows left by houses now removed from the scene.
   z=[height(x0,y0),height(x1,y0),height(x1,y1),height(x0,y1)]
   points=[(x0,y0,z[0]),(x1,y0,z[1]),(x1,y1,z[2]),(x0,y1,z[3])]
   faces=[(0,1,2),(0,2,3)];paving.extend([[points[k] for k in f] for f in faces])
   mesh('J_ground_crossing',points,faces,'asphalt',(0,1),3.2 if args.stage>=4 else 2)
 if args.stage>=4:
  paving_verts=[Vector(p) for t in paving for p in t]
  paving_tree=BVHTree.FromPolygons(paving_verts,np.arange(len(paving_verts)).reshape(-1,3).tolist(),all_triangles=True)
  def paving_height(x,y):
   hit=paving_tree.ray_cast(Vector((x,y,2)),Vector((0,0,-1)),4)[0]
   return hit.z if hit is not None else height(x,y)
  paving_array=np.asarray(paving);paving_lo=paving_array.min(axis=1);paving_hi=paving_array.max(axis=1)
  def conform_paint(points,indices,uvdata):
   verts=[];uvs=[];faces=[]
   for tri in indices:
    xy=np.stack((points[tri,0],-points[tri,2]),axis=1);lo=xy.min(axis=0);hi=xy.max(axis=0)
    mask=(paving_hi[:,0]>=lo[0]-1e-7)&(paving_lo[:,0]<=hi[0]+1e-7)&(paving_hi[:,1]>=lo[1]-1e-7)&(paving_lo[:,1]<=hi[1]+1e-7)
    for floor in paving_array[mask]:
     poly=[np.array([p[0],p[1],uv[0],uv[1]],dtype='f8') for p,uv in zip(xy,uvdata[tri])]
     for a,b in zip(floor,floor[[1,2,0]]):
      if not poly:break
      edge=b[:2]-a[:2]
      def distance(p):return edge[0]*(p[1]-a[1])-edge[1]*(p[0]-a[0])
      clipped=[]
      for p,q in zip(poly,poly[1:]+poly[:1]):
       d=distance(p);e=distance(q)
       if d>=-1e-9:clipped.append(p)
       if (d>=0)!=(e>=0):clipped.append(p+(q-p)*d/(d-e))
      poly=clipped
     if len(poly)<3:continue
     normal=np.cross(floor[1]-floor[0],floor[2]-floor[0]);origin=floor[0]
     for k in range(1,len(poly)-1):
      t=[poly[0],poly[k],poly[k+1]]
      ab=t[1][:2]-t[0][:2];ac=t[2][:2]-t[0][:2]
      if abs(ab[0]*ac[1]-ab[1]*ac[0])<1e-9:continue
      start=len(verts)
      for x,y,u,v in t:
       z=origin[2]-(normal[0]*(x-origin[0])+normal[1]*(y-origin[1]))/normal[2]+.009
       verts.append((float(x),float(y),float(z)));uvs.append((float(u),float(v)))
      faces.append((start,start+1,start+2))
   return verts,faces,uvs
  # Reproject original source markings onto the repaired road. Shapes and UVs
  # come from E, including its authored stop text; no replacement signs invented.
  doc,buffers=read(args.web/'models/block_E.gltf')
  def source_markings(index,parent):
   node=doc['nodes'][index];matrix=parent@transform(node)
   if 'mesh' in node and '_ground' in node.get('name','').lower():
    for primitive in doc['meshes'][node['mesh']]['primitives']:
     material=doc['materials'][primitive.get('material',0)]['name']
     if material not in ('roadmark','paint'):continue
     points=accessor(doc,buffers,primitive['attributes']['POSITION']).astype('f4');points=points@matrix[:3,:3].T+matrix[:3,3]
     idx=accessor(doc,buffers,primitive['indices']).ravel().reshape(-1,3)
     center=points[idx].mean(axis=1);mask=(center[:,0]>=-11.25)&(center[:,0]<=11.25)&(-center[:,2]>=-30.1)&(-center[:,2]<=-19.4)&(center[:,1]<.5)
     idx=idx[mask]
     if not len(idx):continue
     uvdata=accessor(doc,buffers,primitive['attributes']['TEXCOORD_0']).astype('f4') if 'TEXCOORD_0' in primitive['attributes'] else np.zeros((len(points),2))
     if material=='paint':
      vertices,faces,uvdata=conform_paint(points,idx,uvdata);obj=mesh('J_source_markings',vertices,faces,material)
     else:
      obj=mesh('J_source_markings',[(float(x),float(-z),paving_height(float(x),float(-z))+.009) for x,y,z in points],idx.tolist(),material)
     for poly in obj.data.polygons:
      for loop in poly.loop_indices:
       u,v=uvdata[obj.data.loops[loop].vertex_index];obj.data.uv_layers[0].data[loop].uv=(float(u),float(1-v))
   for child in node.get('children',[]):source_markings(child,matrix)
  for index in doc['scenes'][doc.get('scene',0)]['nodes']:source_markings(index,np.eye(4))
  # Raised kerbs frame existing pavement corners, leaving both axes open.
  paths=[[(-10.2,-27.2),(-3.2,-27.2),(-2.65,-27.65),(-2.65,-29.8)],
         [(-10.2,-22.65),(-3.2,-22.65),(-2.65,-22.1),(-2.65,-19.6)],
         [(10.2,-27.4),(3.2,-27.4),(2.65,-27.9),(2.65,-29.8)],
         [(10.2,-22.2),(3.2,-22.2),(2.65,-21.65),(2.65,-19.6)]]
  for path in paths:
   for a,b in zip(path,path[1:]):
    d=Vector((b[0]-a[0],b[1]-a[1]));length=d.length;d.normalize();side=Vector((-d.y,d.x))*.08
    steps=max(1,math.ceil(length/.72))
    for k in range(steps):
     p=Vector(a)+d*(length*k/steps+.012);q=Vector(a)+d*(length*(k+1)/steps-.012)
     verts=[(p.x-side.x,p.y-side.y,height(p.x,p.y)),(q.x-side.x,q.y-side.y,height(q.x,q.y)),(q.x+side.x,q.y+side.y,height(q.x,q.y)),(p.x+side.x,p.y+side.y,height(p.x,p.y))]
     verts+= [(x,y,z+.075) for x,y,z in verts]
     mesh('J_kerb',verts,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'concrete',(0,1),1)
  if args.stage>=5:
   for x,y in [(-2.48,-27.7),(2.48,-22.0)]:
    for k in range(9):box('J_drain_grate',(x-.11,y-.3+k*.065,height(x,y)+.003),(x+.11,y-.282+k*.065,height(x,y)+.016),'metal')

# Join by material only. The editable blend keeps named repair families; the
# runtime GLB uses a handful of draw calls instead of one mesh per paving cell.
for mat in mats.values():
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.materials and o.data.materials[0]==mat]
 if not objects:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 if len(objects)>1:bpy.ops.object.join()
 objects[0].name='J_ground' if mat==mats['asphalt'] else 'J_'+mat.name
bpy.ops.wm.save_as_mainfile(filepath=str(args.out/f'junction-details-r{args.stage:02}.blend'))
bpy.ops.export_scene.gltf(filepath=str(args.out/'junction-details.glb'),export_format='GLB',export_yup=True,export_extras=True)
print('REFINEMENT STAGE',args.stage,flush=True);sys.stdout.flush();os._exit(0)
