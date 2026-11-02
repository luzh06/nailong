# 把 Blender 的 AgX 显示变换导成 3D 查找表：输入按 2^(x*16-9) 编码，输出已是显示值。
import bpy, os, sys
import numpy as np
N = 48
ROOT = r'D:\Cijian\web\data'
scene = bpy.context.scene
s = scene.render.image_settings
s.file_format = 'PNG'; s.color_mode = 'RGB'; s.color_depth = '16'
scene.display_settings.display_device = 'sRGB'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = 0
g = np.linspace(0, 1, N)
b, gg, r = np.meshgrid(g, g, g, indexing='ij')
def dec(x):
    return np.where(x > 0, 2.0 ** (x * 16 - 9), 0)
im = bpy.data.images.new('lut', N * N, N, alpha=False, float_buffer=True)
im.colorspace_settings.name = 'Linear Rec.709'
px = np.ones((N, N * N, 4), 'f')
for bi in range(N):
    sl = np.ones((N, N, 3), 'f')
    px[:, bi * N:(bi + 1) * N, 0] = dec(np.tile(g, (N, 1)))
    px[:, bi * N:(bi + 1) * N, 1] = dec(np.tile(g[:, None], (1, N)))
    px[:, bi * N:(bi + 1) * N, 2] = dec(g[bi])
im.pixels.foreach_set(px.ravel())
for name, look in (('sunset', 'AgX - Medium High Contrast'), ('morning', 'AgX - Base Contrast')):
    scene.view_settings.look = look
    p = os.path.join(ROOT, f'lut_{name}.png')
    im.save_render(p, scene=scene)
    o = bpy.data.images.load(p)
    o.colorspace_settings.name = 'Non-Color'
    q = np.empty(N * N * N * 4, 'f')
    o.pixels.foreach_get(q)
    q = q.reshape(N, N * N, 4)[:, :, :3]
    # 排成 [b][g][r]
    out = np.empty((N, N, N, 3), 'f')
    for bi in range(N):
        out[bi] = q[:, bi * N:(bi + 1) * N]
    out.astype('<f4').tofile(os.path.join(ROOT, f'lut_{name}.bin'))
    print('LUT', name, out.min(), out.max(), out[N // 2, N // 2, N // 2], flush=True)
os._exit(0)
