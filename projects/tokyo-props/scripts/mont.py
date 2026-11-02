import sys,os
from PIL import Image
paths=sys.argv[2:]; n=len(paths); c=4; th=380
W=Image.new('RGB',(c*th,(n+c-1)//c*th))
for i,p in enumerate(paths):
    im=Image.open(p).convert('RGB').resize((th,th)); W.paste(im,((i%c)*th,(i//c)*th))
W.save(sys.argv[1],quality=80)
