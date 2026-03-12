import bpy
import sys
import os

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

def import_model(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".glb", ".gltf"]:
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext in [".obj"]:
        bpy.ops.import_scene.obj(filepath=path)
    elif ext in [".fbx"]:
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        raise RuntimeError(f"Unsupported input format: {ext}")

def export_glb(out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        export_yup=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
        export_animations=False
    )

def apply_rug_rules():
    print("Applying Rug Rules: Adding Thickness...")
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # Cleanup first
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.001)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Add Solidify Modifier
            mod = obj.modifiers.new(name="Augminted_Thickness", type='SOLIDIFY')
            mod.thickness = 0.015  # 1.5cm
            mod.offset = 1.0 # Extrude outwards
            mod.use_even_offset = True
            mod.use_quality_normals = True
            
            bpy.ops.object.modifier_apply(modifier=mod.name)
            print(f"  - Applied Solidify to {obj.name} (1.5cm, Offset=1)")
            obj.select_set(False)

def main():
    args = parse_args()
    in_path = args.get("in")
    out_path = args.get("out")
    category = args.get("category", "").lower()

    if not in_path or not out_path:
        print("Usage: blender -P apply_rules.py -- --in <input> --out <output> --category <cat>")
        sys.exit(1)

    clean_scene()
    import_model(in_path)

    # Apply Rules based on Category
    if category in ["rug", "mat", "carpet"]:
        apply_rug_rules()
    else:
        print(f"No specific rules for category: {category}")

    export_glb(out_path)

if __name__ == "__main__":
    main()
