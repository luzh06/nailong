"""把导出的 GLB 编成 data_*.js, 这样 web/index.html 双击就能打开, 不需要起服务器。"""
import base64
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = (("master_tokyo_scene.glb", "data_scene.js", "GLB_SCENE"),
         ("master_tokyo_crowd.glb", "data_crowd.js", "GLB_CROWD"),
         ("master_tokyo_shutters_closed.glb", "data_shutters.js", "GLB_SHUTTERS"))
for glb, js, var in PAIRS:
    with open(os.path.join(ROOT, "exports", glb), "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    with open(os.path.join(ROOT, "web", js), "w", encoding="ascii") as f:
        f.write(f'window.{var}="{data}";\n')
    print(js, round(len(data) / 1048576, 1), "MB")
