# Save a light copy of qs_h1 (frontage, street, poles, wires, stairs) for block previews. Source file is opened read-only.
import bpy, os, re
DROP = re.compile(r"^(shrub|nettle|fern|dandelion|grass|moss|far|fog|hf|h_far|ground|cam_|plan)")
for o in list(bpy.data.objects):
    if DROP.match(o.name) or o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=r"D:\project\cijian\work\ref\h1_frontage.blend", copy=True, compress=True)
print("SAVED", len(bpy.data.objects), flush=True)
os._exit(0)
