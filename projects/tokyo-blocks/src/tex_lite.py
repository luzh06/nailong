# Export-size copies: 2K base and normal at q74, ARM 1K q78. Originals stay untouched.
import os
from PIL import Image
S=r"D:\Cijian\assets\tex2k"; D=r"D:\Cijian\assets\tex2k_lite"; tot=0
for d in os.listdir(S):
    if not os.path.isdir(os.path.join(S,d)): continue
    os.makedirs(os.path.join(D,d),exist_ok=True)
    for f,q in (("diff.jpg",74),("nor.jpg",74),("arm1k.jpg",78)):
        p=os.path.join(S,d,f)
        if os.path.exists(p):
            o=os.path.join(D,d,f); Image.open(p).convert("RGB").save(o,quality=q,optimize=True); tot+=os.path.getsize(o)
print("lite MB",tot/1e6)
