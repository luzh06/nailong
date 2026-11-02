# Assemble the 80x80 m Yanaka area: qs_h1 (opened read-only, saved as a new file) + blocks A/B (5070 Ti) + C/D/E (this pass).
# --before 1 renders qs_h1 untouched with the same cameras and settings, for the before/after comparison.
import sys, os, json, time, argparse
sys.path.insert(0, r"D:\project\cijian\work\src")
import bpy
from mathutils import Vector as V
from blk_core import to_model, ALIGN_E, ALIGN_N
from blk_fill import G, h1_removed

ap = argparse.ArgumentParser()
ap.add_argument("--before", type=int, default=0); ap.add_argument("--cams", default="stairs_west,street_east,junction,temple,parking,clane,aerial")
ap.add_argument("--res", type=int, default=1600); ap.add_argument("--spp", type=int, default=128); ap.add_argument("--save", type=int, default=0); ap.add_argument("--tag", default="v1"); ap.add_argument("--light", default="sunset")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
ROOT = r"D:\project\cijian\work"; OUT = ROOT + r"\output\assembly"; os.makedirs(OUT, exist_ok=True)
t0 = time.time(); sc = bpy.context.scene
GLBS = {"A": ROOT + r"\ref\block_A.glb", "B": ROOT + r"\ref\block_B.glb", "C": ROOT + r"\export\blocks\block_C\block_C.glb",
        "D": ROOT + r"\export\blocks\block_D\block_D.glb", "E": ROOT + r"\export\blocks\block_E\block_E.glb"}
import math
import numpy as np
from mathutils import Vector
HDR = r"D:\Cijian\assets\hdri"
# Same presets as qs_build.py (LIGHT / set_light): qs_h1.blend is saved without world or sun, the build script adds them at render time.
LIGHT = dict(morning=dict(hdr="kloofendal_48d_partly_cloudy_puresky_4k.hdr", az=100, el=38, sun=4.0, col=(1, .92, .8), angle=1.0, strength=1.9, cap=8, exposure=.5, fog=.0010, look="AgX - Base Contrast", glow=0, fogc=(1, 1, 1)),
             sunset=dict(hdr="qwantani_sunset_puresky_4k.hdr", az=268, el=6.1, sun=7.5, col=(1, .58, .3), angle=1.6, strength=.85, cap=9, exposure=.3, fog=.0010, glow=.38, fogc=(1, .8, .58), look="AgX - Medium High Contrast"))


def hdri_sun(path):
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.empty(w * h * 4, "f"); img.pixels.foreach_get(px)
    lum = px.reshape(h, w, 4)[..., :3].sum(2); lum[:h // 2] = 0
    i = int(np.argmax(lum)); r, c = i // w, i % w
    return (.5 - (c + .5) / w) * 2 * math.pi, ((r + .5) / h - .5) * math.pi


def set_light(k):
    L = LIGHT[k]; path = os.path.join(HDR, L["hdr"]); phi, _ = hdri_sun(path); az = math.radians(L["az"])
    rot = phi - math.atan2(math.sin(az), -math.cos(az))
    w = bpy.data.worlds.new(k); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, rot)
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(path, check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = L["strength"]; out = nt.nodes.new("ShaderNodeOutputWorld")
    cap = nt.nodes.new("ShaderNodeVectorMath"); cap.operation = "MINIMUM"; cap.inputs[1].default_value = (L["cap"],) * 3
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs[0], env.inputs["Vector"]); nt.links.new(env.outputs[0], cap.inputs[0])
    nt.links.new(cap.outputs[0], bg.inputs["Color"]); nt.links.new(bg.outputs[0], out.inputs[0])
    sc.world = w; sc.view_settings.exposure = L["exposure"]; sc.view_settings.look = L["look"]
    sd = bpy.data.objects.get("sun") or bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    if sd.name not in sc.collection.objects: sc.collection.objects.link(sd)
    sd.data.energy = L["sun"]; sd.data.color = L["col"]; sd.data.angle = math.radians(L["angle"])
    e = math.radians(L["el"]); d = Vector((-math.cos(az) * math.cos(e), math.sin(az) * math.cos(e), math.sin(e)))
    sd.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    fm = bpy.data.materials.get("fog")
    if fm:
        fs = [n for n in fm.node_tree.nodes if n.bl_idname == "ShaderNodeVolumeScatter"][0]
        fs.inputs["Density"].default_value = L["fog"]; fs.inputs["Color"].default_value = (*L["fogc"], 1)
    for m in bpy.data.materials:          # warm window glow values, as qs_build's GLOW list
        if m.name.startswith("glass_warm") and m.node_tree:
            for n in m.node_tree.nodes:
                if n.bl_idname == "ShaderNodeValue": n.outputs[0].default_value = L["glow"]
    c = sc.cycles; c.use_adaptive_sampling = True; c.adaptive_threshold = .012; c.denoiser = "OPTIX"; c.max_bounces = 6; c.volume_bounces = 1
    c.volume_max_steps = 256; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.sample_clamp_indirect = 8


set_light(a.light)
removed = []
if not a.before:
    for o in list(bpy.data.objects):
        if o.type != "MESH": continue
        c = sum((o.matrix_world @ V(b) for b in o.bound_box), V()) / 8
        if h1_removed(o.name, (c.y - ALIGN_E, ALIGN_N - c.x)):
            removed.append(o.name); bpy.data.objects.remove(o, do_unlink=True)
    g = bpy.data.objects.get("ground_far")
    if g: g.location.z -= .4          # new terrain west of the street dips to -0.46; keep the far plane under it
    for k, p in GLBS.items():
        col = bpy.data.collections.new("block_" + k); sc.collection.children.link(col)
        before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
        for o in set(bpy.data.objects) - before:
            for c in o.users_collection: c.objects.unlink(o)
            col.objects.link(o)
    print("REMOVED", len(removed), sorted(set(n.split("_")[0] + "_" + n.split("_")[1] if "_" in n else n for n in removed)), flush=True)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=ROOT + r"\blend\tokyo80_assembly.blend", compress=True)
        print("SAVED", flush=True)
# cameras: ENU (z<3 means eye height above ground)
CAMS = {"stairs_west": None,                                                                                      # qs_h1's own hero camera
        "street_east": ((-121.0, 4.0, 1.65), (-62, 2.0, 3.2), 26), "junction": ((-58.2, -.3, 1.65), (-56.4, 20, 3.4), 24),
        "temple": ((-65.5, -20.4, 1.65), (-79, -15.6, 3.2), 26), "parking": ((-35.5, -31.5, 1.65), (-55, -16, 6.0), 24),
        "clane": ((-52.0, 27.2, 1.65), (-34, 26.8, 3.2), 26), "aerial": ((-12, -78, 52), (-74, -4, 0), 30)}
c = sc.render.engine = "CYCLES"
sc.cycles.samples = a.spp; sc.cycles.use_denoising = True
sc.render.resolution_x = a.res; sc.render.resolution_y = int(a.res * 9 / 16); sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 90
p = bpy.context.preferences.addons["cycles"].preferences; p.compute_device_type = "OPTIX"; p.get_devices()
for d in p.devices: d.use = d.type == "OPTIX"
sc.cycles.device = "GPU"
for n in a.cams.split(","):
    if n == "stairs_west":
        cam = bpy.data.objects["cam_west"]
    else:
        pos, look, lens = CAMS[n]
        if pos[2] < 3: pos = (pos[0], pos[1], pos[2] + G(pos[0], pos[1]))
        cd = bpy.data.cameras.new(n); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = .05; cd.clip_end = 3000
        cam = bpy.data.objects.new(n, cd); sc.collection.objects.link(cam)
        P = V(to_model(pos)); L = V(to_model(look)); cam.location = P; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (L - P).to_track_quat("-Z", "Y")
    sc.camera = cam
    sc.render.filepath = OUT + f"\\{'before' if a.before else 'after'}_{a.tag}_{a.light}_{n}.jpg"
    t1 = time.time(); bpy.ops.render.render(write_still=True); print("RENDER", n, round(time.time() - t1), flush=True)
print("ALLDONE", round(time.time() - t0), flush=True)
sys.stdout.flush(); os._exit(0)
