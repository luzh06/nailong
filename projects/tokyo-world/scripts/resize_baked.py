"""Reduce GPU memory of the delivered web copy, preserving original EXR radiance."""
import argparse
from pathlib import Path
import sys
import bpy
sys.path.insert(0, r'D:\project\cijian\work\.pydeps')
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--out', type=Path, required=True)
args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
count = 0
for path in (args.out / 'bake').rglob('*'):
    if path.suffix.lower() == '.exr':
        image = bpy.data.images.load(str(path))
        w,h = image.size
        if max(w,h) > 1024:
            ratio = 1024/max(w,h)
            image.scale(round(w*ratio), round(h*ratio))
            image.filepath_raw = str(path)
            image.file_format = 'OPEN_EXR'
            image.save()
            count += 1
        bpy.data.images.remove(image)
    elif path.suffix.lower() in ('.jpg','.png'):
        with Image.open(path) as im:
            if max(im.size) > 1024:
                im.thumbnail((1024,1024), Image.Resampling.LANCZOS)
                im.save(path, quality=90)
                count += 1
print('RESIZED',count,flush=True)
