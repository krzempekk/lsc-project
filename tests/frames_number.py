import bpy

scene = bpy.context.scene
# frame_end is included
print(f"Scene {scene.name} frames: {scene.frame_start}..{scene.frame_end} = {scene.frame_end - scene.frame_start + 1}")
