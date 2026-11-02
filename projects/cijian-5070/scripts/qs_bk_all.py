# 读 groups.json，烘全部组（井盖并进路面），再转给 qs_bk_bake
import json, sys
d = json.load(open(r'D:\Cijian\bake\groups.json'))
g = ','.join(k for k in d if not k.startswith('p_') and k != 'manhole')
sys.argv += ['--groups', g]
exec(compile(open(r'D:\Cijian\scripts\qs_bk_bake.py', encoding='utf-8').read(), 'qs_bk_bake.py', 'exec'))
