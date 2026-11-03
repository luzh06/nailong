import bpy, sys, os
print("VER", bpy.app.version_string)
p = bpy.context.preferences.addons['cycles'].preferences
for t in ('OPTIX','CUDA'):
    try:
        p.compute_device_type = t
        p.get_devices()
        print("DEV", t, [(d.name, d.type) for d in p.devices])
    except Exception as e:
        print("ERR", t, e)
sys.stdout.flush()
os._exit(0)
