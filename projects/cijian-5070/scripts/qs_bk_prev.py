# 把烘焙图缩成 JPG 预览：blender -b -P qs_bk_prev.py -- <目录> <组,组> <宽>
import bpy, sys, os
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
d = os.path.join(r'D:\Cijian\bake', argv[0])
W = int(argv[2])
for g in argv[1].split(','):
    for suf in ('albedo.png', 'orm.png', 'normal.png', 'sunset.exr', 'sunset_vis.exr', 'morning.exr'):
        p = os.path.join(d, f'{g}_{suf}')
        if not os.path.exists(p):
            continue
        im = bpy.data.images.load(p)
        w, h = im.size
        px = np.empty(w * h * 4, 'f')
        im.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)
        st = max(1, w // W)
        px = px[::st, ::st].copy()
        px[..., 3] = 1
        if suf.endswith('.exr'):
            print('STAT', g, suf, 'mean', px[..., :3].mean((0, 1)), 'p99', np.percentile(px[..., :3], 99), 'max', px[..., :3].max(), flush=True)
            px[..., :3] = (px[..., :3] * .5 / (1 + px[..., :3] * .5)) ** (1 / 2.2)
        elif suf == 'albedo.png':
            px[..., :3] = px[..., :3] ** (1 / 2.2)
        o = bpy.data.images.new('o', px.shape[1], px.shape[0])
        o.colorspace_settings.name = 'Non-Color'
        o.pixels.foreach_set(px.ravel())
        o.filepath_raw = os.path.join(d, 'pv_' + g + '_' + suf.split('.')[0] + '.jpg')
        o.file_format = 'JPEG'
        o.save()
print('PV done', flush=True)
os._exit(0)
