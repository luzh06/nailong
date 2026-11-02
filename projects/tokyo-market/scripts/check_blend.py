"""打开 master_tokyo.blend 后核对内容。用法: blender -b master_tokyo.blend --python check_blend.py"""
import os

import bpy

scene = bpy.context.scene
print("CHECK camera", scene.camera.name, "lens", scene.camera.data.lens, "res", scene.render.resolution_x,
      scene.render.resolution_y, "world", scene.world.name)
missing = [i.name for i in bpy.data.images if i.source == "FILE" and not os.path.exists(bpy.path.abspath(i.filepath))]
print("CHECK images", len(bpy.data.images), "missing", missing)
print("CHECK collections", [c.name for c in bpy.data.collections])
print("CHECK objects", len(bpy.data.objects), "meshes", len(bpy.data.meshes))
ascii_bad = [m.name for m in bpy.data.meshes if not m.name.replace("_", "").replace(".", "").isalnum() or not m.name.isascii()]
print("CHECK non_ascii_mesh_names", ascii_bad)
print("CHECK duplicated_mesh_suffix", [m.name for m in bpy.data.meshes if "." in m.name])
