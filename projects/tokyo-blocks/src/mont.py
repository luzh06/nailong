import sys
from PIL import Image
tag=sys.argv[1]; names=sys.argv[2].split(",")
W=800;H=450;C=2;rows=(len(names)+1)//2
im=Image.new("RGB",(C*W,rows*H))
for i,n in enumerate(names):
    t=Image.open(rf"D:\Cijian\output\blocks\{tag}_{n}.jpg").resize((W,H),Image.LANCZOS)
    im.paste(t,((i%C)*W,(i//C)*H))
im.save(rf"D:\Cijian\work\m_{tag}.jpg",quality=82)
