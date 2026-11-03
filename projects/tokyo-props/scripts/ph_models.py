import json,subprocess
r=subprocess.run(['curl.exe','-sS','-m','60','-A','cijian-student-asset-pipeline','https://api.polyhaven.com/assets?t=models'],capture_output=True,text=True,encoding='utf8')
d=json.loads(r.stdout); print(len(d))
print(' '.join(sorted(d)))
