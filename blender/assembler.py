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
    values = []
    
    # Simple parser that handles repeated flags like --part
    for a in args:
        if a.startswith("--"):
            if key:
                out[key] = values if len(values) > 1 else (values[0] if values else True)
            key = a[2:]
            values = []
        else:
            values.append(a)
    
    if key:
        out[key] = values if len(values) > 1 else (values[0] if values else True)
        
    return out


def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Purge orphans
    for block in bpy.data.meshes:
        if block.users == 0: bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0: bpy.data.materials.remove(block)


def import_part(path, part_name):
    if not os.path.exists(path):
        print(f"Warning: Part file not found: {path}")
        return
        
    ext = os.path.splitext(path)[1].lower()
    if ext in [".glb", ".gltf"]:
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext in [".obj"]:
        bpy.ops.import_scene.obj(filepath=path)
    elif ext in [".fbx"]:
        bpy.ops.import_scene.fbx(filepath=path)
        
    # Rename imported objects to include part_name for organization
    # (The imported objects are selected by default)
    for obj in bpy.context.selected_objects:
        obj.name = f"{part_name}_{obj.name}"


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


def main():
    args = parse_args()
    out_path = args.get("out", "outputs/assembled.glb")
    
    # Expecting args like: --part "name:path" --part "name2:path2"
    # Or just a list of paths if we don't care about names
    parts = args.get("part", [])
    if isinstance(parts, str): parts = [parts]
    
    clean_scene()
    
    print(f"Assembling {len(parts)} parts...")
    
    for p in parts:
        if ":" in p:
            name, path = p.split(":", 1)
        else:
            name = "part"
            path = p
            
        print(f"Importing {name} from {path}")
        import_part(path, name)
        
    export_glb(out_path)
    print(f"Exported assembled model to {out_path}")


if __name__ == "__main__":
    main()
