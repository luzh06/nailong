# fetch Poly Haven CC0 models (glTF 2k) through curl.exe; resumable
import json,os,subprocess,time
from concurrent.futures import ThreadPoolExecutor
ROOT=r'D:\Cijian\assets\polyhaven_models'; UA='cijian-student-asset-pipeline'
M='exterior_aircon_unit cardboard_box_01 potted_plant_01 potted_plant_02 potted_plant_04 planter_pot_clay plastic_crate_01 plastic_crate_02 metal_trash_can modular_pipes_plastic_01 modular_metal_gutter power_box_01 trashbag painted_wooden_table plastic_broom plastic_bottle_gallon standing_chalkboard_01 modular_electric_cables modular_electricity_poles'.split()
def curl(u,p):
    os.makedirs(os.path.dirname(p),exist_ok=True)
    for k in range(8):
        r=subprocess.run(['curl.exe','-sS','-L','-f','--connect-timeout','15','-m','150','-A',UA,'-o',p+'.tmp',u],capture_output=True,text=True)
        if r.returncode==0 and os.path.getsize(p+'.tmp')>100:
            os.replace(p+'.tmp',p); return True
        time.sleep(2+k)
    return False
def one(a):
    d=os.path.join(ROOT,a); j=os.path.join(d,'_files.json')
    if not curl('https://api.polyhaven.com/files/'+a,j): print('FAILED api',a,flush=True); return False
    f=json.load(open(j,encoding='utf8'))
    g=f['gltf']['2k']['gltf']; ok=curl(g['url'],os.path.join(d,a+'.gltf'))
    for rel,x in g.get('include',{}).items():
        p=os.path.join(d,rel.replace('/',os.sep))
        if not os.path.exists(p): ok=curl(x['url'],p) and ok
    print('ok' if ok else 'BAD',a,flush=True); return ok
with ThreadPoolExecutor(4) as e: r=list(e.map(one,M))
json.dump([(a,'https://polyhaven.com/a/'+a,'CC0') for a in M],open(r'D:\Cijian\assets\sources_models.json','w'))
print('ALLDONE' if all(r) else 'INCOMPLETE',flush=True)
