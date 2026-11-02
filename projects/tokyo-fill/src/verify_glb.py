# Import delivered GLBs back in, report model-space bounds and materials, render one view of each from the same camera
import sys, os, json
sys.path.insert(0, r"D:\project\cijian\work\src")
import bpy
from blk_core import *
bpy.ops.wm.read_factory_settings(use_empty=True)
res = {}
for B in ("A", "B"):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=ROOT + rf"\export\blocks\block_{B}\block_{B}.glb")
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    xs = []; ys = []; zs = []
    for o in new:
        for c in o.bound_box:
            w = o.matrix_world @ V(c); xs.append(w.x); ys.append(w.y); zs.append(w.z)
    m = {s.material.name for o in new for s in o.material_slots if s.material}
    tex = sum(1 for n in m if any(k.type == "TEX_IMAGE" for k in bpy.data.materials[n].node_tree.nodes))
    va = sum(1 for o in new if len(o.data.color_attributes))
    res[B] = dict(objects=len(new), x=[round(min(xs), 2), round(max(xs), 2)], y=[round(min(ys), 2), round(max(ys), 2)], z=[round(min(zs), 2), round(max(zs), 2)], materials=len(m), textured=tex, with_vertex_color=va)
print("VERIFY", json.dumps(res), flush=True)
json.dump(res, open(ROOT + r"\export\blocks\glb_import_check.json", "w"), indent=1)
setup_render(1280, 64); lighting()
for n, pos, look, lens in (("A", (-101, -18.6, 1.75), (-74, -22, 3.2), 26), ("B", (-55.5, 46, 1.75), (-66, 31, 4.2), 26)):
    cam = add_cam("c" + n, pos, look, lens); bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = ROOT + rf"\output\blocks\glb_check_{n}.jpg"
    bpy.ops.render.render(write_still=True)
print("ALLDONE", flush=True); sys.stdout.flush(); os._exit(0)
