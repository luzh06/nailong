// Scene switches release the old renderer and shared resources exactly once.
export function disposeGraphs(...roots){
 const geometries=new Set(),materials=new Set(),textures=new Set();
 for(const root of roots)root?.traverse(o=>{
  if(o.geometry)geometries.add(o.geometry);
  for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m)materials.add(m);
 });
 for(const m of materials){for(const v of Object.values(m))if(v?.isTexture)textures.add(v);m.dispose();}
 for(const g of geometries)g.dispose();
 for(const t of textures)t.dispose();
}
