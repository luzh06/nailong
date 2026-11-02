# Neutralise saturated CC0 maps so vertex tints control final colour
import os, shutil
import numpy as np
from PIL import Image
R=r"D:\Cijian\assets\tex2k"
JOB=[("box_profile_metal_sheet","box_grey",.0,1.75),("japanese_cedar_planks","cedar_muted",.28,.62),("rusty_painted_metal","steel_muted",.3,.75),("rectangular_facade_tiles","facade_tiles_n",.5,1.25),
     ("concrete_block_wall","block_n",.35,1.7),("concrete_floor_worn_001","lot_n",.6,1.7),("grey_plaster","mortar_n",.25,1.3)]
for src,dst,sat,gain in JOB:
    d=os.path.join(R,dst); os.makedirs(d,exist_ok=True)
    a=np.asarray(Image.open(os.path.join(R,src,"diff.jpg")).convert("RGB"),np.float32)/255
    g=a.mean(-1,keepdims=True); b=g+(a-g)*sat
    if dst=="mortar_n":
        m=b.mean((0,1),keepdims=True); b=m+(b-m)*.5
    b=np.clip(b*gain,0,1)
    Image.fromarray((b*255).astype(np.uint8)).save(os.path.join(d,"diff.jpg"),quality=90)
    for f in ("nor.jpg","arm.jpg"):
        p=os.path.join(R,src,f)
        if os.path.exists(p): shutil.copy(p,os.path.join(d,f))
    print(dst,os.path.getsize(os.path.join(d,"diff.jpg")))
