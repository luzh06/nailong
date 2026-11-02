import json,urllib.request
def get(u):
    r=urllib.request.Request(u,headers={'User-Agent':'cijian-student-asset-pipeline'})
    return json.load(urllib.request.urlopen(r,timeout=40))
t=get('https://api.polyhaven.com/assets?t=textures')
print(len(t))
kw=['rust','corrugated','paint','plaster','wood','plank','fabric','canvas','concrete','metal','tile','brick','asphalt','plastic','stucco','tarp','rubber','cloth','linen','bamboo','terracotta','roof']
groups={k:[] for k in kw}
for i,a in t.items():
    for k in kw:
        if k in i: groups[k].append(i); break
for k,v in groups.items(): print(k,len(v),' '.join(sorted(v)[:40]))
h=get('https://api.polyhaven.com/assets?t=hdris')
print([i for i in h if any(x in i for x in ['street','road','alley','sunset','evening','city','urban'])][:50])
