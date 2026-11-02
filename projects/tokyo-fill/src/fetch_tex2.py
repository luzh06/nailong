# CC0 Poly Haven textures at 2K JPG: diffuse, GL normal, ARM (ao/rough/metal)
import requests, os, json, time
OUT=r"D:\project\cijian\work\assets\tex2k"; os.makedirs(OUT,exist_ok=True)
IDS="""granite_tile_02 precast_stone_paving monastery_stone_floor white_plaster_02 white_stucco plastered_wall_02 plastered_wall_05 rough_plaster_03 damaged_plaster worn_cracked_plaster concrete_pavement_02 asphalt_05 asphalt_07 cobblestone_embedded_asphalt metal_plate_02 green_metal_rust rusty_metal_02 wood_planks_grey painted_concrete red_plaster_weathered roof_tiles_14 grey_roof_tiles granite_wall""".split()
UA={"User-Agent":"cijian-research/1.0"}
reg=[]
for i in IDS:
    d=os.path.join(OUT,i); os.makedirs(d,exist_ok=True)
    try:
        f=requests.get(f"https://api.polyhaven.com/files/{i}",headers=UA,timeout=40).json()
        for key,tag in (("Diffuse","diff"),("nor_gl","nor"),("arm","arm"),("AO","ao"),("Rough","rough"),("Metal","metal"),("Displacement","disp")):
            if key not in f: continue
            if tag in("ao","rough","metal") and "arm" in f: continue
            k=f[key].get("2k",{}); u=(k.get("jpg") or k.get("png") or {}).get("url")
            if not u: print("no",i,key); continue
            p=os.path.join(d,tag+os.path.splitext(u)[1])
            if os.path.exists(p): continue
            for a in range(4):
                try:
                    r=requests.get(u,headers=UA,timeout=120); r.raise_for_status(); open(p,"wb").write(r.content); break
                except Exception as e: print("retry",u,e); time.sleep(4)
            reg.append((i,tag,u))
        print("ok",i,flush=True)
    except Exception as e: print("FAIL",i,e,flush=True)
json.dump(reg,open(r"D:\project\cijian\work\assets\tex2k\sources.json","a"))
pass
print("ALLDONE")
