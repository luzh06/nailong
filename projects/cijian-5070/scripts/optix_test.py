import bpy, os
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
print('DEVICES', [(d.name, d.type) for d in prefs.devices])
for d in prefs.devices:
    d.use = d.type == 'OPTIX'
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.device = 'GPU'
s.cycles.samples = 64
s.render.resolution_x, s.render.resolution_y = 640, 360
s.render.filepath = r'D:\Cijian\output\test_optix.png'
bpy.ops.render.render(write_still=True)
print('DONE', os.path.getsize(s.render.filepath))
