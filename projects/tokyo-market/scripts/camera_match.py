"""白模 + 主机位 (对应参考图 191), 渲染后和参考图叠加对比。
用法: blender -b --python camera_match.py -- <输出目录>
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_whitebox
from cijian_common import fresh_world, point_camera, setup_gpu

# 机位由 191 反推: 山墙等距算出地平线和高度约 24 米, 约 127mm 长焦, 在街道轴线东侧约 11 米
CAM_LOC = (10.7, -67.4, 24.0)
CAM_TARGET = (-18.0, 231.2, -8.8)
CAM_LENS = 127.0
REF_W, REF_H = 1320, 1787


def add_main_camera():
    cam_data = bpy.data.cameras.new("cam_main_ref191")
    cam_data.lens = CAM_LENS
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = 36.0
    cam = bpy.data.objects.new("cam_main_ref191", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    point_camera(cam, CAM_LOC, CAM_TARGET)
    bpy.context.scene.camera = cam
    return cam


def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def main():
    out = sys.argv[sys.argv.index("--") + 1]
    clear_scene()
    build_whitebox.build()
    add_main_camera()

    scene = bpy.context.scene
    setup_gpu(24)
    scene.render.resolution_x = REF_W // 2
    scene.render.resolution_y = REF_H // 2
    scene.world = fresh_world("wb_world", (0.62, 0.68, 0.78))
    sun = bpy.data.lights.new("wb_sun", "SUN")
    sun.energy = 2.5
    sun_ob = bpy.data.objects.new("wb_sun", sun)
    sun_ob.rotation_euler = (math.radians(50), 0, math.radians(35))
    scene.collection.objects.link(sun_ob)

    scene.render.filepath = os.path.join(out, "wb_ref191.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)


if __name__ == "__main__":
    main()
