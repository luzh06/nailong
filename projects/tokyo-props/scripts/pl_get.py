# pl_get.py: ask the official PLATEAU MCP for CityGML urls round Yanaka Ginza, fetch them, print real street dimensions
import json,subprocess,os,math,re,sys
import xml.etree.ElementTree as ET
D=r'D:\Cijian\assets\plateau'; os.makedirs(D,exist_ok=True)
def mcp(name,args):
    b=os.path.join(D,'_req.json')
    json.dump({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":name,"arguments":args}},open(b,'w'))
    for k in range(6):
        r=subprocess.run(['curl.exe','-sS','-m','50','https://api.plateauview.mlit.go.jp/mcp','-X','POST','-H','Content-Type: application/json','-H','Accept: application/json, text/event-stream','--data-binary','@'+b],capture_output=True,text=True,encoding='utf8')
        t=r.stdout
        if t.strip():
            if 'data: ' in t[:60]: t=t.split('data: ',1)[1]
            return json.loads(json.loads(t)['result']['content'][0]['text'])
    raise SystemExit('mcp failed '+r.stderr)
d=mcp('plateau_get_citygml_files',{'condition':'r:139.7640,35.7265,139.7680,35.7290','feature_types':['bldg','tran']})
json.dump(d,open(os.path.join(D,'files.json'),'w'),indent=0)
for c in d['cities']:
    print(c['cityCode'],c['cityName'],c['year'],c.get('spec'))
    for k,v in c['files'].items():
        for f in v:
            print(' ',k,f['code'],f.get('maxLod'))
            if c['cityCode'] in('13106','13118','13105') :
                p=os.path.join(D,c['cityCode']+'_'+os.path.basename(f['url']))
                if not os.path.exists(p):
                    q=subprocess.run(['curl.exe','-sS','-L','-f','--retry','6','--retry-all-errors','-m','280','-o',p,f['url']],capture_output=True,text=True)
                    print('   dl',q.returncode,q.stderr[:90],os.path.getsize(p)//1024 if os.path.exists(p) else 0,'KB',flush=True)
print('END')
