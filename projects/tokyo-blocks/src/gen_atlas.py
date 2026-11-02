# Procedural decal atlas (RGBA PNG) and curtain texture
import numpy as np, os
from PIL import Image
OUT=r"D:\Cijian\assets\gen"; os.makedirs(OUT,exist_ok=True)
rng=np.random.default_rng(7)
def fbm(h,w,base=(4,4),oct=5,seed=None):
    r=rng if seed is None else np.random.default_rng(seed)
    out=np.zeros((h,w),np.float32); amp=1.0; tot=0
    bx,by=base
    for o in range(oct):
        n=r.random((max(2,by*2**o),max(2,bx*2**o))).astype(np.float32)
        im=Image.fromarray((n*65535).astype(np.uint16).astype(np.int32),mode='I').convert('F').resize((w,h),Image.BICUBIC)
        out+=np.asarray(im)/65535*amp; tot+=amp; amp*=.55
    return out/tot
S=512
X,Y=np.meshgrid(np.linspace(0,1,S),np.linspace(0,1,S))
def edge(p=.12):
    e=np.minimum.reduce([X/p,(1-X)/p,Y/p,(1-Y)/p]); return np.clip(e,0,1)**.7
def streak(seed,col,strength=.8):
    n=fbm(S,S,(26,2),5,seed)
    n2=fbm(S,S,(6,5),4,seed+1)
    cx=np.exp(-((X-.5)/.27)**2)
    fade=(1-Y)**1.3*np.clip(Y/.03,0,1)
    a=np.clip((n-.42)*5,0,1)*cx*fade*(.5+n2)*strength
    return col,a
def band(seed,col,up=True,strength=.8):
    n=fbm(S,S,(8,4),6,seed); t=Y if up else 1-Y
    a=np.clip((t**2.0*1.5+n-.82)*3.2,0,1)*strength
    a*=np.clip(np.minimum(X,1-X)/.06,0,1)
    return col,a
def splotch(seed,col,strength=.7):
    n=fbm(S,S,(5,5),6,seed); r=np.hypot(X-.5,Y-.5)
    a=np.clip((n+.55-r*1.25-.5)*5,0,1)*strength*edge(.05)
    return col,a
def crack(seed,col):
    r=np.random.default_rng(seed); a=np.zeros((S,S),np.float32)
    from PIL import ImageDraw
    im=Image.new('L',(S*2,S*2),0); d=ImageDraw.Draw(im)
    for b in range(4):
        x,y=S*(.6+r.random()*.8),S*.1+r.random()*S*.2; ang=np.pi/2+r.normal(0,.3)
        for i in range(int(50+r.random()*60)):
            ang+=r.normal(0,.35); nx=x+np.cos(ang)*18; ny=y+np.sin(ang)*18
            d.line((x,y,nx,ny),fill=255,width=int(r.integers(1,4))); x,y=nx,ny
    a=np.asarray(im.resize((S,S),Image.LANCZOS),np.float32)/255
    return col,a*.9*edge(.03)
def patch(seed,col,strength=.92):
    n=fbm(S,S,(10,10),5,seed)
    e=np.minimum.reduce([X,1-X,Y,1-Y])
    a=np.clip((e+(n-.5)*.09-.05)*40,0,1)*strength
    return col,a
def seam(seed,col):
    n=fbm(S,S,(3,20),5,seed); d=np.abs(Y-.5+(n-.5)*.35)
    a=np.clip((.035-d)*60,0,1)*.9*np.clip(np.minimum(X,1-X)/.04,0,1)
    return col,a
cells=[streak(11,(.07,.06,.05)),streak(21,(.10,.09,.07)),streak(31,(.05,.05,.05),.6),streak(41,(.32,.14,.05),.9),
       band(51,(.10,.09,.07)),band(61,(.14,.12,.09),True,.65),splotch(71,(.09,.08,.07)),splotch(81,(.16,.14,.11),.5),
       band(91,(.10,.14,.05),True,.8),crack(101,(.05,.045,.04)),crack(111,(.04,.04,.04)),splotch(121,(.62,.60,.55),.45),
       patch(131,(.055,.055,.06)),seam(141,(.025,.025,.028)),splotch(151,(.02,.02,.022),.55),patch(161,(.10,.10,.105),.85)]
A=np.zeros((S*4,S*4,4),np.float32)
for i,(c,a) in enumerate(cells):
    y,x=(i//4)*S,(i%4)*S
    pad=3; a2=a.copy(); a2[:pad]=0;a2[-pad:]=0;a2[:,:pad]=0;a2[:,-pad:]=0
    mottle=.85+.3*fbm(S,S,(30,30),3,i+500)
    A[y:y+S,x:x+S,:3]=np.stack([np.full((S,S),v)*mottle for v in c],-1)
    A[y:y+S,x:x+S,3]=a2
srgb=np.clip(A[...,:3],0,1)**(1/2.2)
im=Image.fromarray((np.dstack([srgb,A[...,3]])*255).astype(np.uint8),'RGBA'); im.save(OUT+r"\decals.png",optimize=True)
# Curtain: vertical folds, lace sheen; neutral so vertex colour tints it
W=1024
n=fbm(W,W,(14,2),4,5)
folds=.72+.28*np.sin(np.linspace(0,1,W)[None,:]*2*np.pi*11+6*n)
weave=(fbm(W,W,(240,240),1,6)-.5)*.05
c=np.clip(folds*.92+weave+(n-.5)*.15,0,1)**(1/2.2)
Image.fromarray((np.dstack([c,c,c])*255).astype(np.uint8)).save(OUT+r"\curtain.jpg",quality=88)
print("atlas ok",os.path.getsize(OUT+r"\decals.png")/1e6)
