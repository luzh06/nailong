# Neutral, mean-normalised copies of textures that are tinted by vertex colour (so a vermilion tint stays vermilion).
import os, shutil
import numpy as np
from PIL import Image
R = r"D:\project\cijian\work\assets\tex2k"; L = r"D:\project\cijian\work\assets\tex2k_lite"
JOB = [("painted_concrete", "shu_n", .82, .55), ("plastered_wall_05", "plaster5_n", .8, .8), ("rough_plaster_03", "rough3_n", .78, .8),
       ("worn_cracked_plaster", "cracked_n", .76, .8), ("damaged_plaster", "damaged_n", .74, .9)]
for src, dst, mean, contrast in JOB:
    a = np.asarray(Image.open(os.path.join(R, src, "diff.jpg")).convert("RGB"), np.float32) / 255
    g = a.mean(-1, keepdims=True); g = g.mean() + (g - g.mean()) * contrast
    b = np.clip(g * (mean / g.mean()), 0, 1).repeat(3, -1)
    for root in (R, L):
        d = os.path.join(root, dst); os.makedirs(d, exist_ok=True)
        Image.fromarray((b * 255).astype(np.uint8)).save(os.path.join(d, "diff.jpg"), quality=86)
        for f in ("nor.jpg", "arm.jpg", "arm1k.jpg"):
            p = os.path.join(root if root == L else R, src, f)
            if os.path.exists(p): shutil.copy(p, os.path.join(d, f))
    print(dst, round(float(b.mean()), 3))
