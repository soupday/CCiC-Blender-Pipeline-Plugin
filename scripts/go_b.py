import bpy

BLEND_PATH = r"$1"
FPS = $2

try:
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.render.fps_base = 1.0
except: ...
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.file.make_paths_relative()
bpy.ops.ccic.datalink(param="GOB_START")