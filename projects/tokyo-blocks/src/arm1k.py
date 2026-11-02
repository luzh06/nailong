import os
from PIL import Image
R=r"D:\Cijian\assets\tex2k"
for d in os.listdir(R):
    p=os.path.join(R,d,"arm.jpg")
    if os.path.exists(p):
        Image.open(p).convert("RGB").resize((1024,1024),Image.LANCZOS).save(os.path.join(R,d,"arm1k.jpg"),quality=82)
print("ok")
