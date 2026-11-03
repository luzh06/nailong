"""Create only derived access paving; do not open or overwrite source blocks.

Coordinates are measured on delivered D/S geometry, in Blender metres.
This is access work inside the fictional temple extension, not new geography.
"""
import argparse
import os
from pathlib import Path
import sys
import bpy

ap=argparse.ArgumentParser()
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('access_granite');mat.diffuse_color=(.46,.44,.40,1)
mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.46,.44,.40,1);bs.inputs['Roughness'].default_value=.92

def paving(name,x0,x1,z0,z1,width=3.4):
    # One continuous top face, surveyed ends overlap both existing surfaces.
    y0,y1=-9.5-width/2,-9.5+width/2
    verts=[(x0,y0,z0),(x1,y0,z1),(x1,y1,z1),(x0,y1,z0),
           (x0,y0,z0-.10),(x1,y0,z1-.10),(x1,y1,z1-.10),(x0,y1,z0-.10)]
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)])
    mesh.materials.append(mat)
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    uv=mesh.uv_layers.new()
    for face in mesh.polygons:
        for i in face.loop_indices:
            v=mesh.vertices[mesh.loops[i].vertex_index].co;uv.data[i].uv=(v.x/1.5,v.y/1.5)
    mod=obj.modifiers.new('Small worn stone edges','BEVEL');mod.width=.008;mod.segments=2
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj

# Accessible central approaches preserve the source gates, columns and plinths.
paving('L_ground_kaminarimon_approach',40.15,43.10,.974,1.338)
paving('L_ground_kaminarimon_exit',48.90,51.80,1.338,1.006)
paving('L_ground_hozomon_approach',67.10,70.10,1.006,1.438)
paving('L_ground_hozomon_exit',80.50,83.50,1.438,1.006)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'temple-access.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'temple-access.glb'),export_format='GLB',export_yup=True,export_extras=True)
print('DERIVED ACCESS',out,flush=True)
sys.stdout.flush();os._exit(0)
