# make_manifest.py: rebuild export/props/manifest.csv + LICENSES.md from each asset's JSON sidecar
import csv,glob,json,os
E=r'D:\Cijian\export\props'
reg={r[0]:r for r in json.load(open(r'D:\Cijian\assets\sources.json'))+json.load(open(r'D:\Cijian\assets\sources_models.json'))}
rows=[]; used={}
for p in sorted(glob.glob(E+r'\*\*.json')):
    m=json.load(open(p,encoding='utf8')); t=m['tris']
    rows.append([m['name']+'.glb',t.get('LOD0'),t.get('LOD1'),t.get('LOD2'),t.get('COL'),'x'.join(map(str,m['texture'])),'×'.join(map(str,m['size_m'])),m['glb_mb'],'; '.join(m['sources']),m['notes']])
    for s in m['sources']: used.setdefault(s,[]).append(m['name'])
with open(E+r'\manifest.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['文件名','LOD0三角面','LOD1','LOD2','碰撞体','贴图尺寸','尺寸米(XYZ)','GLB_MB','来源','备注']); w.writerows(rows)
with open(E+r'\LICENSES.md','w',encoding='utf8') as f:
    f.write('# 来源与许可\n\n招牌、标签、暖帘图案均为本项目原创绘制，店名和品牌均为虚构。\n\n')
    for s in sorted(used):
        if not s.startswith(('polyhaven:','font:','decals:')):
            f.write('- %s\n'%s); continue
        k=s.split(':',1)[1].split('(')[0]
        lic=next((v for n,v in reg.items() if n==k or n.lower().startswith(k.lower())),None)
        f.write('- %s：%s（%s）\n'%(s,lic[1] if lic else '本项目原创',lic[2] if lic else '原创'))
print('manifest',len(rows))
