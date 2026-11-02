# 打静态包：PNG 转 JPG，拷贴图、天空、植物贴图、页面。blender -b -P qs_pack.py -- --dir t4
import bpy, os, sys, json, shutil, glob
argv = sys.argv[sys.argv.index('--') + 1:]
D = argv[argv.index('--dir') + 1]
ROOT = r'D:\Cijian'
PK = os.path.join(ROOT, 'pack')
src = os.path.join(ROOT, 'bake', D)
dst = os.path.join(PK, 'bake', D)
shutil.rmtree(PK, ignore_errors=True)
os.makedirs(dst)
os.makedirs(os.path.join(PK, 'web', 'data'))
Q = dict(albedo=92, normal=94, orm=90, emit=92)
s = bpy.context.scene.render.image_settings
for f in sorted(os.listdir(src)):
    p = os.path.join(src, f)
    if f.endswith('.png'):
        k = f[:-4].rsplit('_', 1)[1]
        im = bpy.data.images.load(p)
        im.colorspace_settings.name = 'Non-Color'
        im.pixels[0]
        s.file_format = 'JPEG'
        s.color_mode = 'RGB'
        s.quality = Q.get(k, 90)
        q = os.path.join(dst, f[:-4] + '.jpg')
        im.filepath_raw = q
        im.file_format = 'JPEG'
        im.save(quality=s.quality)
        bpy.data.images.remove(im)
    elif f.endswith(('.exr', 'cards.json')):
        shutil.copy(p, dst)
print('TEX', len(os.listdir(dst)), flush=True)
W = os.path.join(ROOT, 'web')
for f in ('game.html', 'game.js'):
    shutil.copy(os.path.join(W, f), os.path.join(PK, 'web', f))
shutil.copytree(os.path.join(W, 'vendor'), os.path.join(PK, 'web', 'vendor'))
shutil.copytree(os.path.join(W, 'utils'), os.path.join(PK, 'web', 'utils'))
shutil.copytree(os.path.join(W, 'libs'), os.path.join(PK, 'web', 'libs'))
for f in ('bk.glb', 'lut_sunset.bin'):
    shutil.copy(os.path.join(W, 'data', f), os.path.join(PK, 'web', 'data', f))
m = json.load(open(os.path.join(W, 'data', 'bk.json')))
m['ext'] = 'jpg'
m['groups'] = {k: [x.replace('.png', '.jpg') for x in v] for k, v in m['groups'].items()}
json.dump(m, open(os.path.join(PK, 'web', 'data', 'bk.json'), 'w'))
os.makedirs(os.path.join(PK, 'assets', 'hdri'))
shutil.copy(os.path.join(ROOT, 'assets', 'hdri', 'qwantani_sunset_puresky_4k.hdr'), os.path.join(PK, 'assets', 'hdri'))
for k in m['plants']:
    t = os.path.join(PK, 'assets', 'models', k, 'textures')
    os.makedirs(t)
    for x in glob.glob(os.path.join(ROOT, 'assets', 'models', k, 'textures', '*')):
        shutil.copy(x, t)
open(os.path.join(PK, 'index.html'), 'w', encoding='utf-8').write('<!doctype html><meta charset=utf-8><meta http-equiv=refresh content="0;url=web/game.html"><a href=web/game.html>此间</a>')
n = 0
for r, _, fs in os.walk(PK):
    n += sum(os.path.getsize(os.path.join(r, f)) for f in fs)
print('PACKDONE', round(n / 1e6), 'MB', flush=True)
os._exit(0)
