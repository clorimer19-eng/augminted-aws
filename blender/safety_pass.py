import bpy
import sys
import os
import json
from mathutils import Vector


def parse_args():
    # Blender passes args after "--"
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


    # Remove orphan data blocks (optional)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


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


def count_tris_for_object(obj):
    if obj.type != "MESH":
        return 0
    mesh = obj.data
    # Ensure evaluated mesh
    return sum(len(p.vertices) - 2 for p in mesh.polygons)  # triangulated count estimate


def total_tris():
    tris = 0
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            tris += count_tris_for_object(obj)
    return tris


def apply_decimate(target_tris):
    current = total_tris()
    if current <= 0:
        return current, current


    if current <= target_tris:
        return current, current


    ratio = max(0.01, min(1.0, target_tris / float(current)))


    # Add decimate modifier to all meshes
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        mod = obj.modifiers.new(name="Augminted_Decimate", type='DECIMATE')
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.select_set(False)


    after = total_tris()
    return current, after


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def clamp_materials(rough_min=0.08, rough_max=0.92, normal_strength_max=0.6):
    """
    Clamp Principled BSDF roughness and reduce normal map node strength.
    This does not try to 'beautify'—it enforces stability guardrails.
    """
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        nt = mat.node_tree
        nodes = nt.nodes


        # Clamp Principled roughness
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                rough_input = node.inputs.get("Roughness")
                if rough_input is None:
                    continue
                # If it's a value (not linked), clamp it
                if not rough_input.is_linked:
                    try:
                        rough_input.default_value = clamp(rough_input.default_value, rough_min, rough_max)
                    except Exception:
                        pass


        # Reduce normal map strength
        for node in nodes:
            if node.type == "NORMAL_MAP":
                strength = node.inputs.get("Strength")
                if strength and not strength.is_linked:
                    try:
                        strength.default_value = min(strength.default_value, normal_strength_max)
                    except Exception:
                        pass


def resize_textures(max_px=2048):
    """
    Downscale all images in the blend file to fit within max_px.
    """
    print(f"Resizing textures to max {max_px}px...")
    for img in bpy.data.images:
        if not img.size[0] or not img.size[1]:
            continue
            
        width, height = img.size
        if width <= max_px and height <= max_px:
            continue
            
        # Calculate new size maintaining aspect ratio
        ratio = min(max_px / width, max_px / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        print(f"  - Scaling {img.name}: {width}x{height} -> {new_width}x{new_height}")
        
        img.scale(new_width, new_height)


def set_origin_and_scale():
    """
    Light cleanup: apply transforms for export consistency.
    """
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            obj.select_set(False)


def snap_to_floor():
    """
    Aligns the lowest point of the mesh to Z=0.
    """
    print("Snapping to floor...")
    
    # Calculate global min Z
    min_z = float('inf')
    mesh_objs = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    
    if not mesh_objs:
        return

    # Update matrices
    bpy.context.view_layer.update()

    for obj in mesh_objs:
        # Get world coordinates of vertices
        world_verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
        if not world_verts: continue
        local_min_z = min(v.z for v in world_verts)
        if local_min_z < min_z:
            min_z = local_min_z
            
    if min_z == float('inf'):
        return
        
    print(f"  - Found lowest point at Z={min_z:.4f}")
    
    # Move all objects up by -min_z
    if abs(min_z) > 0.001:
        print(f"  - Shifting up by {-min_z:.4f}")
        for obj in bpy.data.objects:
             # Move root objects (parents) or all if no hierarchy
             if not obj.parent:
                obj.location.z -= min_z
                
    # Apply transform again to bake it
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)


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


def export_usdz(out_path):
    try:
        # Blender 4.x USD export
        bpy.ops.wm.usd_export(
            filepath=out_path,
            selected_objects_only=False,
            export_textures=True,
            relative_paths=True
            # export_format="USDZ" # Removed invalid arg
        )
        print(f"Exported USDZ: {out_path}")
    except Exception as e:
        print(f"[WARN] USDZ Export failed: {e}")
        # Fallback for older Blender versions or different operator names
        try:
            bpy.ops.export_scene.usdz(filepath=out_path)
            print(f"Exported USDZ (Legacy): {out_path}")
        except Exception as e2:
            print(f"[ERROR] Could not export USDZ: {e2}")


def main():
    args = parse_args()
    print("[SAFETY_PASS] Parsed args:", args)
    
    in_path = args.get("in")
    out_path = args.get("out", "outputs/out.glb")
    metrics_path = args.get("metrics")

    # Constraints
    target_tris = int(args.get("max_tris", 100000))
    rough_min = float(args.get("rough_min", 0.08))
    rough_max = float(args.get("rough_max", 0.92))
    normal_max = float(args.get("normal_max", 0.3))


    if not in_path:
        raise RuntimeError("Missing required --in argument")


    clean_scene()
    import_model(in_path)


    before_tris = total_tris()
    b, a = apply_decimate(target_tris)


    clamp_materials(rough_min=rough_min, rough_max=rough_max, normal_strength_max=normal_max)
    
    # Texture Resizing
    tex_max = int(args.get("texture_max", 2048))
    resize_textures(max_px=tex_max)
    
    set_origin_and_scale()
    snap_to_floor()


    export_glb(out_path)
    
    # Export USDZ (for iOS)
    usdz_path = out_path.replace(".glb", ".usdz")
    export_usdz(usdz_path)

    # Write metrics (optional)
    if metrics_path:
        metrics = {
            "input": in_path,
            "output_glb": out_path,
            "output_usdz": usdz_path,
            "tris_before": int(before_tris),
            "tris_after": int(a),
            "max_tris": int(target_tris),
            "texture_max": int(tex_max),
            "rough_min": float(rough_min),
            "rough_max": float(rough_max),
            "normal_max": float(normal_max),
        }
        try:
            os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)
                f.write("\n")
            print(f"[SAFETY_PASS] Wrote metrics: {metrics_path}")
        except Exception as e:
            print(f"[SAFETY_PASS][WARN] Failed to write metrics to {metrics_path}: {e}")

    print("=== AUGMINTED SAFETY PASS ===")
    print(f"Input: {in_path}")
    print(f"Output: {out_path}")
    print(f"Tris before: {before_tris}")
    print(f"Tris after:  {a}")
    print(f"Roughness clamp: {rough_min}..{rough_max}")
    print(f"Normal strength max: {normal_max}")


if __name__ == "__main__":
    main()
