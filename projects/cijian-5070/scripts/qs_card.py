# 远景卡片：把小样范围外的街道渲成透明底图，网页里摆在街道尽头。
# blender -b qs_bk.blend -P qs_card.py -- --dir t3 --spp 256
import bpy, os, sys, json, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
def arg(k, d):
    return argv[argv.index('--' + k) + 1] if '--' + k in argv else d
OUT = os.path.join(r'D:\Cijian\bake', arg('dir', 't3'))
sys.argv = [sys.argv[0], '--', '--groups', 'none', '--passes', 'none', '--out', arg('dir', 't3')]
src = open(r'D:\Cijian\scripts\qs_bk_bake.py', encoding='utf-8').read().split('# 植物：低模参与自身遮挡')[0].split('for g in GROUPS:')[0]
exec(compile(src, 'bk', 'exec'))
set_light('sunset')
for o in bpy.data.objects:
    if o.type == 'MESH' and (o.name.startswith('bk_') or o.name.startswith('bkp_')) and o.name not in ('bk_far', 'bk_ground'):
        o.hide_render = True
bpy.data.objects['bk_far'].hide_render = True
bpy.data.objects['bk_ground'].hide_render = True
c.samples = int(arg('spp', 256))
c.use_denoising = True
c.denoiser = 'OPTIX'
scene.render.film_transparent = True
scene.render.use_compositing = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '16'
scene.render.resolution_x, scene.render.resolution_y = 1536, 1024
meta = {}
for name, loc, tgt, dist, lens in (('west', (0, 6, 3.2), (0, -40, 3.6), 41.0, 45), ('east', (0, 12, 6.0), (0, 60, 7.0), 21.0, 28)):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = 36
    cam.clip_start = dist
    cam.clip_end = 5000
    ob = bpy.data.objects.new(name, cam)
    scene.collection.objects.link(ob)
    ob.location = loc
    d = (Vector(tgt) - Vector(loc)).normalized()
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.camera = ob
    scene.render.filepath = os.path.join(OUT, f'card_{name}.exr')
    bpy.ops.render.render(write_still=True)
    w = 2 * dist * 18 / lens
    ce = Vector(loc) + d * dist
    meta[name] = dict(center=list(ce), eye=list(loc), w=w, h=w * 1024 / 1536)
json.dump(meta, open(os.path.join(OUT, 'cards.json'), 'w'))
print('CARDSDONE', meta, flush=True)
os._exit(0)
