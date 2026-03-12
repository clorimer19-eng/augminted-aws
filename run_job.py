\
import json
import os
from dotenv import load_dotenv

load_dotenv()
import sys
from datetime import datetime
from pathlib import Path


import yaml
from rich import print

BLENDER_BIN = os.environ.get(
    "BLENDER_PATH",
    os.environ.get("BLENDER_BIN", "/usr/local/blender/blender"),
)

# from scripts.routing import classify_and_route # TODO: Integrate this for v2 risk assessment
from scripts.constraints import enforce_constraints
from scripts.run_blender import run_safety_pass

ALLOWED_CATEGORIES = {
    "table",
    "chair",
    "armchair",
    "sofa",
    "sofa_bed",
    "bed",
    "desk",
    "computer_desk",
    "bench",
    "cabinet",
    "storage_unit",
    "wardrobe",
    "bookcase",
    "shelving_unit",
}

DEFAULT_CATEGORY = "table"


def write_log(job_id: str, data: dict) -> str:
    Path("logs").mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    path = f"logs/{job_id}-{ts}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


import subprocess
from scripts.slicer import slice_image

import os
BLENDER_PATH = os.environ.get("BLENDER_PATH", os.environ.get("BLENDER_BIN", "/Applications/Blender.app/Contents/MacOS/Blender"))

def run_assembler(part_glbs, out_path):
    cmd = [
        BLENDER_BIN, "-b",
        "-P", "blender/assembler.py",
        "--",
        "--out", out_path
    ]
    for p in part_glbs:
        cmd.extend(["--part", p])
        
    subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) < 2:
        print("[red]Usage:[/red] python run_job.py jobs/<job>.yaml [--in inputs/model.glb]")
        sys.exit(1)


    job_path = sys.argv[1]
    in_model = None
    if "--in" in sys.argv:
        idx = sys.argv.index("--in")
        if idx + 1 < len(sys.argv):
            in_model = sys.argv[idx + 1]


    with open(job_path, "r") as f:
        job = yaml.safe_load(f) or {}

    raw_category = job.get("category", DEFAULT_CATEGORY)
    category = str(raw_category).strip().lower()

    if category in ("", "unknown", "none", "null"):
        category = DEFAULT_CATEGORY

    if category not in ALLOWED_CATEGORIES:
        print(f"[yellow]Unknown category '{category}', defaulting to '{DEFAULT_CATEGORY}'[/yellow]")
        category = DEFAULT_CATEGORY
    job_id = job.get("job_id", "unknown_job")
    constraints = job.get("constraints", {})
    photos_dir = job.get("photos_dir", "inputs")

    print(f"\n[bold]Running job:[/bold] {job_id}")
    print(f"[dim]Job file:[/dim] {job_path}")

    if in_model:
        print(f"[dim]Input model:[/dim] {in_model}")
    print("")


    # 1) Validation (Pre-Flight)
    print("\n[bold]Validating Job...[/bold]")
    from scripts import constraints
    from scripts.input_validation import validate_image
    
    # A. Constraints Check
    errors, warnings = constraints.enforce_constraints(job)
    for w in warnings:
        print(f"[yellow]Warning:[/yellow] {w}")
    if errors:
        print(f"[red]Job Rejected (Constraints):[/red] {errors}")
        sys.exit(2)
        
    # B. Input Image Sanity Check
    # Find the main image
    photos_dir = job.get("photos_dir", "")
    main_img = job.get("input_image") # Allow explicit override
    if not main_img and photos_dir:
        for ext in [".jpg", ".jpeg", ".png"]:
            p = Path(photos_dir) / f"main{ext}"
            if p.exists():
                main_img = str(p)
                break
    
    if main_img:
        if job.get("skip_validation"):
            print("[yellow]Skipping input validation as requested.[/yellow]")
        else:
            print(f"[dim]Validating input image: {main_img}[/dim]")
            res = validate_image(main_img)
            if not res.valid:
                print(f"[red]Job Rejected (Input Sanity):[/red]")
                for r in res.reasons:
                    print(f"  - {r}")
                sys.exit(2)
            print("[green]Input Image Valid.[/green]")
    else:
        print("[yellow]Warning: No 'main.{jpg,png}' found in photos_dir. Skipping image validation.[/yellow]")

    # 2) Routing & Presets
    # A. Material Preset
    preset_name = constraints.get_preset_for_job(job)
    preset_data = constraints.PRESETS.get(preset_name, {})
    
    # B. Pipeline Routing
    from scripts.routing import get_pipeline_config
    try:
        pipe_conf = get_pipeline_config(category)
    except ValueError as e:
        print(f"[red]Job Rejected (Routing):[/red] {e}")
        sys.exit(2)

    
    # Allow YAML overrides (for debugging)
    if "skip_bg_removal" in job:
        pipe_conf.rembg = not job["skip_bg_removal"]
    if "run_slicer" in job:
        pipe_conf.slicer = job["run_slicer"]
    if "run_geometry_rules" in job:
        pipe_conf.geometry_rules = job["run_geometry_rules"]
    if "run_safety_pass" in job:
        pipe_conf.safety_pass = job["run_safety_pass"]
    
    print(f"[bold]Routing:[/bold] Category='[cyan]{category}[/cyan]'")
    print(f"  -> Preset: '[cyan]{preset_name}[/cyan]'")
    print(f"  -> Pipeline: rembg={pipe_conf.rembg}, slicer={pipe_conf.slicer}, rules={pipe_conf.geometry_rules}, safety={pipe_conf.safety_pass}")
    
    # Extract preset limits
    p_rough_min = preset_data.get("roughness", [0.08, 0.92])[0]
    p_rough_max = preset_data.get("roughness", [0.08, 0.92])[1]
    p_normal_max = preset_data.get("normal_strength", [0.0, 0.6])[1]


    print("\n[green]PASS:[/green] Constraints OK. Job allowed to proceed.")


    # Helper to collect metrics
    metrics = {}
    def collect_metrics(stage_name, glb_path):
        if not glb_path or not Path(glb_path).exists():
            return
        try:
            cmd = [
                BLENDER_BIN, "-b",
                "-P", "blender/get_stats.py",
                "--",
                "--in", glb_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Parse JSON from stdout (last line)
            lines = result.stdout.strip().split('\n')
            # Find the JSON block
            json_str = ""
            in_json = False
            for line in lines:
                if line.strip() == "{": in_json = True
                if in_json: json_str += line + "\n"
                if line.strip() == "}": in_json = False
            
            if json_str:
                metrics[stage_name] = json.loads(json_str)
                print(f"[dim]Collected metrics for {stage_name}[/dim]")
        except Exception as e:
            print(f"[yellow]Failed to collect metrics for {stage_name}: {e}[/yellow]")

    # If an input model was provided, collect its initial metrics
    if in_model:
        collect_metrics("00_initial_input", in_model)

    # 3) Slicing & Assembly (New Flow)
    if not in_model:
        print("\n[bold]Starting Multi-Part Flow...[/bold]")
        
        # A. Slice Images
        parts = job.get("parts", job.get("declared_parts", []))
        
        sliced_images = {}
        
        # If no parts declared but we have a main image, treat as single-part job
        if not parts and main_img:
            print(f"[dim]Single image job detected. Using {main_img}[/dim]")
            sliced_images["main"] = main_img
        else:
            # Use the routing flag for skip_bg
            # Note: slice_image expects 'skip_bg' (True means SKIP). 
            # Our flag is 'rembg' (True means RUN). So we invert it.
            skip_bg_flag = not pipe_conf.rembg
            
            sliced_images = slice_image(job_id, photos_dir, parts, skip_bg=skip_bg_flag)
            
            if not sliced_images:
                print("[red]No images found for slicing. Cannot proceed.[/red]")
                write_log(job_id, {
                    "job_id": job_id,
                    "status": "FAILED",
                    "error": "No images found for slicing"
                })
                sys.exit(1)
            
        # B. Generate Parts
        print("\n[bold]Generating parts...[/bold]")
        part_glbs = []
        api_key = os.environ.get("TRIPO_API_KEY")

        if api_key:
            print("[green]Tripo API Key found. Using AI generation.[/green]")
            from scripts.tripo_client import generate_glb_from_image
            
            for p_name, img_path in sliced_images.items():
                print(f"  - Generating '{p_name}' from {img_path}...")
                out_part_path = f"inputs/{job_id}_{p_name}.glb"
                
                if Path(out_part_path).exists():
                     print(f"    -> Found existing {out_part_path}, skipping generation.")
                     part_glbs.append(f"{p_name}:{out_part_path}")
                     continue

                try:
                    generate_glb_from_image(str(img_path), out_part_path, api_key)
                    part_glbs.append(f"{p_name}:{out_part_path}")
                except Exception as e:
                    print(f"[red]Failed to generate {p_name}: {e}[/red]")
                    write_log(job_id, {
                        "job_id": job_id,
                        "status": "FAILED",
                        "error": f"Tripo API failed for {p_name}: {str(e)}"
                    })
                    sys.exit(1)
        else:
            print("[yellow]No TRIPO_API_KEY found. Using Mock Mode.[/yellow]")
            print("[dim]Generating parts (Mocking with 'inputs/ArmChair AR.glb' if available)...[/dim]")
            mock_glb = "inputs/ArmChair AR.glb"
            if not Path(mock_glb).exists():
                 glbs = list(Path("inputs").glob("*.glb"))
                 if glbs: mock_glb = str(glbs[0])
            
            if Path(mock_glb).exists():
                for p_name, img_path in sliced_images.items():
                    print(f"  - Generated GLB for '{p_name}' from {img_path}")
                    part_glbs.append(f"{p_name}:{mock_glb}")
            else:
                 print("[red]No GLB found in inputs/ to use as mock part.[/red]")
                 write_log(job_id, {
                    "job_id": job_id,
                    "status": "FAILED",
                    "error": "No mock GLB found in inputs/ directory"
                })
                 sys.exit(1)

        # Stop here if requested (Debug Mode)
        if job.get("stop_after_generation", False):
            # Collect metrics for the first part (assuming single part for debug)
            if part_glbs:
                p_path = part_glbs[0].split(":")[1]
                collect_metrics("02_tripo", p_path)
                # Also save metrics before exiting
                with open(f"outputs/{job_id}_debug_metrics.json", "w") as f:
                    json.dump(metrics, f, indent=2)
            
            print("\n[yellow]STOPPING after generation as requested (stop_after_generation=True).[/yellow]")
            sys.exit(0)

        # C. Assemble Parts
        if len(part_glbs) == 1:
            in_model = part_glbs[0].split(":")[1]
            print(f"[dim]Single part detected. Using {in_model} directly.[/dim]")
            collect_metrics("02_tripo", in_model)
        else:
            # Check slicer flag? 
            # If slicer=False, we shouldn't even be here? 
            # Actually, slicer=False usually means we treat it as 1 part.
            # If we have multiple parts, we MUST assemble.
            assembled_glb = f"outputs/{job_id}_assembled.glb"
            print(f"\n[bold]Assembling {len(part_glbs)} parts...[/bold]")
            run_assembler(part_glbs, assembled_glb)
            in_model = assembled_glb
            collect_metrics("02_assembled", in_model)


    # 3.5) Apply Product Rules (Geometry Fixes)
    if pipe_conf.geometry_rules:
        print("\n[bold]Applying Product Rules...[/bold]")
        rules_out_path = f"outputs/{job_id}_rules.glb"
        
        # We pass the category to apply_rules.py, which handles specific logic
        cmd = [
            BLENDER_BIN, "-b",
            "-P", "blender/apply_rules.py",
            "--",
            "--in", in_model,
            "--out", rules_out_path,
            "--category", category
        ]
        subprocess.run(cmd, check=True)
        in_model = rules_out_path 
        print(f"[green]Rules Applied:[/green] {rules_out_path}")
        collect_metrics("03_rules", rules_out_path)
    else:
        print(f"[dim]Geometry Rules skipped (Routing: rules=False).[/dim]")

    # 4) Global Safety Pass + Preset Application
    if pipe_conf.safety_pass:
        out_path = f"outputs/{job_id}_safety.glb"
        print("\n[bold]Running Blender Safety Pass & Presets...[/bold]")
        
        cmd = [
            BLENDER_BIN, "-b",
            "-P", "blender/safety_pass.py",
            "--",
            "--in", in_model,
            "--out", out_path,
            "--metrics", f"outputs/{job_id}_debug_metrics.json",
            "--max_tris", str(constraints.GLOBAL_RULES.get("max_tris", 300000)),
            "--texture_max", str(constraints.GLOBAL_RULES.get("max_texture_px", 2048)),
            "--rough_min", "0.60",
            "--rough_max", "0.85",
            "--normal_max", "0.20"
        ]
        
        subprocess.run(cmd, check=True)
        print(f"[green]Success![/green] Final output: {out_path}")
        collect_metrics("04_safety", out_path)
    else:
        print(f"[dim]Safety Pass skipped (Routing: safety=False).[/dim]")
        # If safety pass is skipped, the final output is the input model
        out_path = in_model
        collect_metrics("04_safety_skipped", out_path)


    # Save all collected metrics
    metrics_path = f"outputs/{job_id}_debug_metrics.json"

    # Only write if we actually have metrics.
    # Otherwise preserve whatever Blender wrote.
    if metrics:
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
            f.write("\n")
        print(f"[dim]Saved debug metrics:[/dim] {metrics_path}")
    else:
        print(f"[dim]Metrics dict empty; leaving existing file untouched:[/dim] {metrics_path}")

    log_path = write_log(job_id, {
        "job_id": job_id,
        "status": "PROCESSED",
        "preset": preset_name,
        "pipeline": {
            "rembg": pipe_conf.rembg,
            "slicer": pipe_conf.slicer,
            "rules": pipe_conf.geometry_rules,
            "safety": pipe_conf.safety_pass
        },
        "warnings": warnings,
        "errors": errors,
        "input_model": in_model,
        "output_glb": out_path,
    })
    print(f"\n[dim]Wrote log:[/dim] {log_path}\n")


if __name__ == "__main__":
    main()
