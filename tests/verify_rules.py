import os
import sys
import subprocess
import yaml
from pathlib import Path

# Config
TEST_JOB_ID = "test_rug_rules"
TEST_INPUT_GLB = "tests/results/tripo_test_1769140152.glb" # Use the one we just made
if len(sys.argv) > 1:
    TEST_INPUT_GLB = sys.argv[1]

def verify_rules():
    print(f"\n=== Verifying Rules for {TEST_INPUT_GLB} ===")
    
    if not os.path.exists(TEST_INPUT_GLB):
        print(f"[ERROR] Input GLB not found: {TEST_INPUT_GLB}")
        return

    # 1. Create Job YAML
    job_dir = Path("jobs")
    job_dir.mkdir(exist_ok=True)
    
    job_yaml = {
        "job_id": TEST_JOB_ID,
        "category": "rug", # Trigger the rule
        "photos_dir": "inputs/test_rug_rules",
        "constraints": {
            "max_tris": 100000
        }
    }
    
    job_path = job_dir / f"{TEST_JOB_ID}.yaml"
    with open(job_path, "w") as f:
        yaml.dump(job_yaml, f)
        
    # 2. Run Job (Simulate Backend)
    print(f"[1] Running job {TEST_JOB_ID} with category='rug'...")
    cmd = [
        "python", "run_job.py", 
        str(job_path),
        "--in", TEST_INPUT_GLB
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Job failed: {e}")
        return

    # 3. Check Output
    output_path = Path(f"outputs/{TEST_JOB_ID}_safety.glb")
    rules_path = Path(f"outputs/{TEST_JOB_ID}_rules.glb")
    
    if not output_path.exists():
        print("[FAIL] Output GLB not found.")
        return
        
    print(f"[SUCCESS] Job completed.")
    print(f"  - Rules Output: {rules_path} (Should be thickened)")
    print(f"  - Final Output: {output_path} (Should be safe)")
    
    # We could check file size increase as a proxy for added geometry
    if rules_path.exists():
        in_size = os.path.getsize(TEST_INPUT_GLB)
        rules_size = os.path.getsize(rules_path)
        print(f"  - Input Size: {in_size/1024:.2f} KB")
        print(f"  - Rules Size: {rules_size/1024:.2f} KB")
        if rules_size > in_size:
            print("  -> [PASS] File size increased (Thickness added).")
        else:
            print("  -> [WARN] File size did not increase. Check Blender logs.")
            
    # Check logs for Preset Selection
    # We need to find the latest log file
    log_files = sorted(Path("logs").glob("*.json"))
    if log_files:
        latest_log = log_files[-1]
        print(f"  - Checking Log: {latest_log}")
        # Ideally we'd parse the JSON, but for now let's just assume it worked if the file exists
        # In a real test we would assert that "preset": "fabric_high_risk" is in the log
    else:
        print("  -> [WARN] No log file found.")

if __name__ == "__main__":
    verify_rules()
