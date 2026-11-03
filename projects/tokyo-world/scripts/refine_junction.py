"""Repair the baked core by source-object identity, preserving all LM/UV data.

The source blend and original delivered bk.glb are read-only. Only an independent
GLB copy, its provenance, and a derived inspection blend are written.
"""
import argparse, hashlib, json, os, struct, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gltf_geometry import read,accessor,transform

ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);args.out.mkdir(parents=True,exist_ok=True)
deps=bpy.context.evaluated_depsgraph_get();groups={};removed=[]
for obj in bpy.data.objects:
 if obj.type!='MESH':continue
 corners=[obj.matrix_world@Vector(v) for v in obj.bound_box];center=sum(corners,Vector())/8
 selected=obj.name.startswith(('h_G-14','h_G15')) or (obj.name.startswith(('aw','block','side','closures')) and -10.5<=center.x<=10.5 and -28.7<=center.y<=-20.1)
 if not selected:continue
 evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles();removed.append(obj.name)
 for tri in mesh.loop_triangles:
  mat=mesh.materials[tri.material_index].name if mesh.materials else ''
  groups.setdefault(mat,[]).append([tuple(obj.matrix_world@mesh.vertices[i].co) for i in tri.vertices])
 evaluated.to_mesh_clear()
trees={}
for mat,faces in groups.items():
 verts=[Vector(p) for f in faces for p in f];trees[mat]=BVHTree.FromPolygons(verts,np.arange(len(verts)).reshape(-1,3).tolist(),all_triangles=True)
doc,buffers=read(args.input);binary=bytearray(buffers[0]);audit=[]

def walk(index,parent):
 node=doc['nodes'][index];matrix=parent@transform(node)
 if 'mesh' in node:
  for primitive in doc['meshes'][node['mesh']]['primitives']:
   if primitive.get('mode',4)!=4:continue
   mat=doc['materials'][primitive.get('material',0)].get('name','');tree=trees.get(mat)
   if tree is None:continue
   points=accessor(doc,buffers,primitive['attributes']['POSITION']).astype('f4');points=points@matrix[:3,:3].T+matrix[:3,3]
   idx=accessor(doc,buffers,primitive['indices']).ravel().reshape(-1,3)
   triangles=points[idx];bl=triangles[:,:,[0,2,1]].copy();bl[:,:,1]*=-1
   center=bl.mean(axis=1);candidate=(center[:,0]>-11)&(center[:,0]<11)&(center[:,1]>-30)&(center[:,1]<-19)&(center[:,2]>-.1)&(center[:,2]<9)
   keep=np.ones(len(idx),dtype=bool)
   for i in np.flatnonzero(candidate):
    hit=tree.find_nearest(Vector(center[i]),.045)
    if hit[0] is None:continue
    # Require vertices too; a neighbouring face merely touching an old house
    # must remain intact, including roof overhangs and adjoining whole facades.
    if all(tree.find_nearest(Vector(p),.085)[0] is not None for p in bl[i]):keep[i]=False
   cut=int((~keep).sum())
   if not cut:continue
   kept=idx[keep].astype('<u4').ravel();binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(kept.tobytes())
   doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':kept.nbytes,'target':34963})
   doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,'componentType':5125,'count':len(kept),'type':'SCALAR'})
   primitive['indices']=len(doc['accessors'])-1
   audit.append({'mesh':node.get('name',''),'material':mat,'before':len(idx),'removed':cut,'after':int(keep.sum())})
 for child in node.get('children',[]):walk(child,matrix)
for index in doc['scenes'][doc.get('scene',0)]['nodes']:walk(index,np.eye(4))
doc['buffers'][0]['byteLength']=len(binary);payload=json.dumps(doc,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4);binary.extend(b'\0'*((-len(binary))%4))
target=args.out/'bk-junction.glb';target.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(payload)+8+len(binary))+struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(binary),0x004e4942)+binary)
report={'sourceBlend':bpy.data.filepath,'input':str(args.input),'inputSHA256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'removedSourceObjects':removed,'groups':audit,'removedTriangles':sum(r['removed'] for r in audit),'preserved':'all vertex attributes, positions, UV/LM, material assignments of remaining triangles'}
(args.out/'junction-provenance.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(target));bpy.ops.wm.save_as_mainfile(filepath=str(args.out/'junction-core.blend'))
print('MODEL REPAIR',report['removedTriangles'],'triangles',len(removed),'source objects',flush=True);sys.stdout.flush();os._exit(0)
