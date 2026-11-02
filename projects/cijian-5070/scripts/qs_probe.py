# 反射探针：台阶中段的 Cycles 全景，太阳灯另算，这里关掉。blender -b qs_bk.blend -P qs_probe.py -- --dir t4
import bpy, os, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
D = argv[argv.index('--dir') + 1]
OUT = os.path.join(r'D:\Cijian\bake', D)
sys.argv = [sys.argv[0], '--', '--groups', 'none', '--passes', 'none', '--out', D]
src = open(r'D:\Cijian\scripts\qs_bk_bake.py', encoding='utf-8').read().split('for g in GROUPS:')[0]
exec(compile(src, 'bk', 'exec'))
set_light('sunset')
bpy.data.objects['sun'].data.energy = 7.5
c.samples = 512
c.use_denoising = True
c.denoiser = 'OPTIX'
c.max_bounces = 4
scene.render.use_compositing = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
s = scene.render.image_settings
s.file_format = 'OPEN_EXR'; s.color_mode = 'RGB'; s.color_depth = '16'; s.exr_codec = 'ZIP'
scene.render.resolution_x, scene.render.resolution_y = 1024, 512
cam = bpy.data.cameras.new('pano')
cam.type = 'PANO'
cam.panorama_type = 'EQUIRECTANGULAR'
ob = bpy.data.objects.new('pano', cam)
scene.collection.objects.link(ob)
# 朝 +x、上 +z，和网页端 eq() 的经纬约定一致
ob.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
scene.camera = ob
for name, loc in (('mid', (.1, -6, 2.2)),):
    ob.location = loc
    scene.render.filepath = os.path.join(OUT, f'probe_{name}.exr')
    bpy.ops.render.render(write_still=True)
print('PROBEDONE', flush=True)
os._exit(0)
