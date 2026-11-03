# ph_fetch.py <core|all> : resumable parallel download through curl.exe (Python TLS gets reset on this network)
import json,os,sys,time,subprocess
from concurrent.futures import ThreadPoolExecutor
ROOT=r'D:\Cijian\assets\polyhaven'; F=r'D:\Cijian\assets\fonts'; UA='cijian-student-asset-pipeline'
CORE='''japanese_cedar_planks dark_wooden_planks weathered_planks hinoki_planks concrete_floor_worn_001 rectangular_facade_tiles
rough_linen fabric_pattern_07 metal_plate painted_metal_shutter rusty_metal_02 green_metal_rust worn_plaster_wall asphalt_02'''.split()
REST='''weathered_plank_siding wood_table_worn rusty_metal_sheet rusty_painted_metal rusted_shutter rusty_corrugated_iron worn_corrugated_iron blue_metal_plate box_profile_metal_sheet
denim_fabric white_plaster_rough_01 worn_cracked_plaster peeling_painted_wall painted_plaster_wall yellow_plaster concrete_wall_006 worn_asphalt dirty_tiles long_white_tiles grey_tiles brick_wall_001 clay_roof_tiles grey_roof_tiles'''.split()
HDR=['industrial_sunset_02_puresky','german_town_street','modern_evening_street']
FONTS='shipporimincho/ShipporiMincho-ExtraBold yujisyuku/YujiSyuku-Regular dotgothic16/DotGothic16-Regular zenkakugothicnew/ZenKakuGothicNew-Bold kaiseiopti/KaiseiOpti-Bold reggaeone/ReggaeOne-Regular'.split()
def curl(u,p,tries=8):
    for k in range(tries):
        r=subprocess.run(['curl.exe','-sS','-L','-f','--connect-timeout','15','-m','120','-A',UA,'-o',p,u],capture_output=True,text=True)
        if r.returncode==0 and os.path.getsize(p)>200: return True
        time.sleep(2+k)
    return False
def api(a):
    p=os.path.join(ROOT,'_%s.json'%a)
    if curl('https://api.polyhaven.com/files/'+a,p):
        d=json.load(open(p,encoding='utf8')); os.remove(p); return d
def fetch(a):
    f=api(a)
    if not f: print('FAILED api',a,flush=True); return False
    d=os.path.join(ROOT,a); os.makedirs(d,exist_ok=True); ok=True
    alt={'diff':('Diffuse','diffuse','Base Color','BaseColor','Color','diff','col_1','col_01'),'nor':('nor_gl','Normal','nor'),'rough':('Rough','rough','Roughness')}
    for short,keys in alt.items():
        key=next((k for k in keys if k in f and '2k' in f[k]),None)
        if key is None:
            ok=False; print('FAILED keys',a,short,sorted(f.keys()),flush=True); continue
        x=f[key]['2k']['jpg']['url']; p=os.path.join(d,short+'.jpg')
        if os.path.exists(p) and os.path.getsize(p)>1000: continue
        if curl(x,p+'.tmp'): os.replace(p+'.tmp',p)
        else: ok=False; print('FAILED',a,short,flush=True)
    print('ok' if ok else 'BAD',a,flush=True); return ok
def hdr(h):
    p=os.path.join(ROOT,'hdri',h+'.hdr'); os.makedirs(os.path.dirname(p),exist_ok=True)
    if os.path.exists(p): return True
    f=api(h)
    if f and curl(f['hdri']['2k']['hdr']['url'],p+'.tmp'):
        os.replace(p+'.tmp',p); print('ok',h,flush=True); return True
    print('FAILED',h,flush=True); return False
def font(n):
    os.makedirs(F,exist_ok=True); p=os.path.join(F,n.split('/')[1]+'.ttf')
    if os.path.exists(p): return True
    if curl('https://raw.githubusercontent.com/google/fonts/main/ofl/%s.ttf'%n,p+'.tmp'):
        os.replace(p+'.tmp',p); print('ok',n,flush=True); return True
    print('FAILED',n,flush=True); return False
mode=sys.argv[1]
tex=CORE if mode=='core' else CORE+REST
with ThreadPoolExecutor(4) as ex:
    r=list(ex.map(fetch,tex))+list(ex.map(hdr,HDR[:2] if mode=='core' else HDR))+list(ex.map(font,FONTS))
reg=[(a,'https://polyhaven.com/a/'+a,'CC0') for a in tex+HDR]+[(n.split('/')[1],'https://github.com/google/fonts/tree/main/ofl/'+n.split('/')[0],'SIL OFL 1.1') for n in FONTS]
json.dump(reg,open(r'D:\Cijian\assets\sources.json','w'),indent=1)
if all(r):
    open(r'D:\Cijian\logs\assets_%s.ok'%mode,'w').write('ok'); print('ALLDONE',flush=True)
else:
    print('INCOMPLETE',r.count(False),flush=True)
