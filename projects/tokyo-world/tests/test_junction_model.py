import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from gltf_geometry import primitives,read,accessor,transform

class JunctionModelTests(unittest.TestCase):
 def test_paint_faces_stay_above_final_paving(self):
  path=Path(__file__).resolve().parents[1]/'derived/junction/junction-details.glb'
  if not path.exists():self.skipTest('details not built')
  floors=[];paint=[]
  for name,mat,v,idx in primitives(path):
   if mat=='repair_asphalt':floors.extend(v[idx])
   if mat=='repair_paint':paint.extend(v[idx])
  f=np.asarray(floors);a=f[:,0];u=f[:,1]-a;v=f[:,2]-a;det=u[:,0]*v[:,2]-v[:,0]*u[:,2]
  lo=f.min(axis=1);hi=f.max(axis=1);minimum=1
  for t in paint:
   for p in [t.mean(axis=0),(t[0]+t[1])/2,(t[1]+t[2])/2,(t[2]+t[0])/2]:
    mask=(lo[:,0]<=p[0]+1e-6)&(hi[:,0]>=p[0]-1e-6)&(lo[:,2]<=p[2]+1e-6)&(hi[:,2]>=p[2]-1e-6)
    px=p[0]-a[:,0];pz=p[2]-a[:,2];s=(px*v[:,2]-v[:,0]*pz)/det;r=(u[:,0]*pz-px*u[:,2])/det
    mask&=(s>=-1e-5)&(r>=-1e-5)&(s+r<=1.00001)
    if mask.any():minimum=min(minimum,float(p[1]-(a[:,1]+s*u[:,1]+r*v[:,1])[mask].max()))
  self.assertGreater(minimum,.002,'paint intersects final paving: '+str(minimum))
 def test_original_stop_marking_uv_orientation_is_preserved(self):
  root=Path(__file__).resolve().parents[1]
  source=root.parents[2]/'output/tokyo-three/web/models/block_E.gltf'
  derived=root/'derived/junction/junction-details.glb'
  if not derived.exists():self.skipTest('details not built')
  def collect(path,material):
   doc,buffers=read(path);result={}
   def walk(index,parent):
    node=doc['nodes'][index];matrix=parent@transform(node)
    if 'mesh' in node:
     for p in doc['meshes'][node['mesh']]['primitives']:
      if doc['materials'][p.get('material',0)]['name']!=material:continue
      points=accessor(doc,buffers,p['attributes']['POSITION']).astype('f4');points=points@matrix[:3,:3].T+matrix[:3,3]
      uv=accessor(doc,buffers,p['attributes']['TEXCOORD_0'])
      used=np.unique(accessor(doc,buffers,p['indices']))
      for i in used:result[(round(points[i,0],4),round(points[i,2],4))]=uv[i]
    for child in node.get('children',[]):walk(child,matrix)
   for index in doc['scenes'][doc.get('scene',0)]['nodes']:walk(index,np.eye(4))
   return result
  before=collect(source,'roadmark');after=collect(derived,'repair_roadmark');self.assertGreaterEqual(len(after),4)
  for key,uv in after.items():np.testing.assert_allclose(uv,before[key],atol=1e-5)
 def test_refinement_is_a_real_derived_mesh(self):
  path=Path(__file__).resolve().parents[1]/'derived/junction/bk-junction.glb'
  self.assertTrue(path.is_file(),'missing derived core; fragment discard is not a model repair')
 def test_removed_house_wall_has_no_fragment_outside_old_cut_box(self):
  path=Path(__file__).resolve().parents[1]/'derived/junction/bk-junction.glb'
  if not path.exists():self.skipTest('derived core not built')
  remnants=0
  for name,mat,v,idx in primitives(path):
   if name not in ('bk_plaster','bk_siding','bk_wood'):continue
   t=v[idx];c=t.mean(axis=1)
   # The G15 front continues beyond z=28.7, where the old shader left a sliver.
   remnants+=int(((abs(c[:,0]-3.30)<.025)&(c[:,2]>28.70)&(c[:,2]<28.81)&(c[:,1]>.3)&(c[:,1]<5.3)).sum())
  self.assertEqual(remnants,0,'G15 wall fragment still present')
if __name__=='__main__':unittest.main()
