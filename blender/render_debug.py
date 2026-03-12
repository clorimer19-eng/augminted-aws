import bpy
import sys
import os
import math

def parse_args():
    argv = sys.argv
    if "--" not in argv:
        return {}
    idx = argv.index("--") + 1
    args = argv[idx:]
    out = {}
    key = None
    for a in args:
        if a.startswith("--"):
            key = a[2:]
            out[key] = True
        else:
            if key:
                out[key] = a
                key = None
    return out

def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def setup_camera_and_light():
    # Camera
    bpy.ops.object.camera_add(location=(2, -2, 1.5))
    cam = bpy.context.object
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam
    
    # Light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    light = bpy.context.object
    light.data.energy = 5
    
    # Fill Light
    bpy.ops.object.light_add(type='POINT', location=(-2, -2, 2))
    light2 = bpy.context.object
    light2.data.energy = 50

def import_model(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".glb", ".gltf"]:
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext in [".obj"]:
        bpy.ops.import_scene.obj(filepath=path)
    
    # Center object
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            obj.location = (0, 0, 0)

def render_scene(out_path):
    bpy.context.scene.render.filepath = out_path
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 600
    bpy.ops.render.render(write_still=True)

def main():
    args = parse_args()
    in_path = args.get("in")
    out_path = args.get("out")

    if not in_path or not out_path:
        print("Usage: blender -P render_debug.py -- --in <input> --out <output_png>")
        sys.exit(1)

    clean_scene()
    setup_camera_and_light()
    import_model(in_path)
    render_scene(out_path)

if __name__ == "__main__":
    main()
