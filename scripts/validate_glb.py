import sys
import os
import yaml
import trimesh
from rich import print
from pygltflib import GLTF2


def get_file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)


def get_tri_count(path):
    try:
        mesh = trimesh.load(path, force='mesh')
        return len(mesh.faces)
    except Exception as e:
        print(f"[red]Error loading mesh for tri count:[/red] {e}")
        return 0


def validate(glb_path, job_path):
    print(f"\n[bold]Validating:[/bold] {glb_path}")
    print(f"[dim]Against job:[/dim] {job_path}\n")


    with open(job_path, 'r') as f:
        job = yaml.safe_load(f)
    
    constraints = job.get("constraints", {})
    max_mb = float(constraints.get("glb_max_mb", 8))
    max_tris = int(constraints.get("max_tris", 150000))


    errors = []
    
    # 1. File Size
    size_mb = get_file_size_mb(glb_path)
    print(f"File size: {size_mb:.2f} MB (Limit: {max_mb} MB)")
    if size_mb > max_mb:
        errors.append(f"File size {size_mb:.2f}MB exceeds limit {max_mb}MB")


    # 2. Triangle Count
    tris = get_tri_count(glb_path)
    print(f"Tri count: {tris} (Limit: {max_tris})")
    if tris > max_tris:
        errors.append(f"Triangle count {tris} exceeds limit {max_tris}")


    # 3. Texture Checks (Basic)
    try:
        gltf = GLTF2().load(glb_path)
        print(f"Textures found: {len(gltf.textures)}")
        # Deep texture inspection would require extracting images
    except Exception as e:
        print(f"[yellow]Could not inspect internal GLTF structure:[/yellow] {e}")


    if errors:
        print("\n[red]FAIL[/red]")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n[green]PASS[/green]")
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate_glb.py <glb_path> <job_yaml_path>")
        sys.exit(1)
    
    validate(sys.argv[1], sys.argv[2])
