import bpy
import os
import math

def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def setup_camera():
    bpy.ops.object.camera_add(location=(2, -2, 1.5), rotation=(math.radians(60), 0, math.radians(45)))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    
    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))

def import_models():
    base_path = "outputs"
    colors = [(1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1), (0,1,1,1)]
    
    for i in range(5):
        path = os.path.join(base_path, f"golden_angle_{i}_safety.glb")
        if not os.path.exists(path):
            continue
            
        bpy.ops.import_scene.gltf(filepath=path)
        
        # The import selects the objects. Let's color them to distinguish.
        # Create a material
        mat = bpy.data.materials.new(name=f"Mat_{i}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colors[i % len(colors)]
        
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                # Assign material (override existing)
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
                
                # Offset them slightly so we can see them if they overlap perfectly (unlikely)
                # obj.location.x += i * 0.2 

def render(out_path):
    bpy.context.scene.render.filepath = out_path
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 600
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    clean_scene()
    setup_camera()
    import_models()
    render("outputs/merge_feasibility_render.png")
