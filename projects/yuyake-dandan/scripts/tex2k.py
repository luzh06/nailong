# 把用到的 4K 贴图缩成 2K，放到 assets\tex2k，优化版用
import bpy, os
src=r'D:\Cijian\assets\textures4k'; dst=r'D:\Cijian\assets\tex2k'
n=0
for d in os.listdir(src):
    os.makedirs(os.path.join(dst,d),exist_ok=True)
    for f in os.listdir(os.path.join(src,d)):
        if f.endswith('.jpg'):
            im=bpy.data.images.load(os.path.join(src,d,f)); im.colorspace_settings.name='Non-Color'
            im.scale(2048,2048); im.filepath_raw=os.path.join(dst,d,f); im.file_format='JPEG'
            s=bpy.context.scene.render.image_settings; s.file_format='JPEG'; s.quality=88
            im.save_render(os.path.join(dst,d,f)); bpy.data.images.remove(im); n+=1
print('TEX2K',n)
