# CC0 Poly Haven textures at 2K JPG: diffuse, GL normal, ARM (ao/rough/metal)
import requests, os, json, time
OUT=r"D:\project\cijian\work\assets\tex2k"; os.makedirs(OUT,exist_ok=True)
IDS="""worn_plaster_wall white_plaster_rough_01 grey_plaster beige_wall_001 plastered_wall_04 worn_mossy_plasterwall
exterior_wall_cladding exterior_wall_cladding_03 rectangular_facade_tiles concrete_tile_facade long_white_tiles
corrugated_iron_02 rusty_corrugated_iron box_profile_metal_sheet black_painted_planks japanese_cedar_planks weathered_plank_siding
concrete_block_wall concrete_wall_006 worn_asphalt asphalt_02 road_damaged_clean concrete_floor_worn_001 grey_roof_tiles_02 grey_roof_01
painted_metal_shutter rusty_metal_03 rusty_painted_metal gravel_concrete_03 concrete_moss""".split()
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
hd=requests.get("https://api.polyhaven.com/files/kloofendal_48d_partly_cloudy_puresky",headers=UA,timeout=40).json()
u=hd["hdri"]["2k"]["hdr"]["url"]; r=requests.get(u,headers=UA,timeout=200); open(r"D:\project\cijian\work\assets\sky_2k.hdr","wb").write(r.content); print("hdri",len(r.content))
print("ALLDONE")
