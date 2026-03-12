import json
import sys
import shutil
from pathlib import Path

def select_best_angle(job_ids):
    print(f"Selecting best angle from: {job_ids}")
    
    candidates = []
    
    for jid in job_ids:
        metrics_path = Path(f"outputs/{jid}_debug_metrics.json")
        if not metrics_path.exists():
            print(f"Warning: No metrics for {jid}")
            continue
            
        with open(metrics_path, "r") as f:
            data = json.load(f)
            
        # Use safety pass metrics
        m = data.get("04_safety")
        if not m:
            continue
            
        dims = m.get("dimensions", [0,0,0])
        width, depth, height = dims
        
        # Calculate scores
        volume = width * depth * height
        aspect_ratio = width / depth if depth > 0 else 0
        
        # Plausibility Checks (for a Table)
        is_thin = width < 0.4 or depth < 0.4
        is_flat = height < 0.1
        
        score = volume
        if is_thin: score *= 0.1 # Penalty for thinness
        if is_flat: score *= 0.1 # Penalty for flatness
        
        candidates.append({
            "job_id": jid,
            "metrics": m,
            "score": score,
            "is_thin": is_thin
        })
        
    if not candidates:
        print("No valid candidates found.")
        return None
        
    # Sort by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    winner = candidates[0]
    print(f"\nWinner: {winner['job_id']}")
    print(f"  Score: {winner['score']:.4f}")
    print(f"  Dims: {winner['metrics']['dimensions']}")
    print(f"  Thin: {winner['is_thin']}")
    
    return winner["job_id"]

def package_winner(winner_id):
    print(f"\nPackaging winner: {winner_id}")
    
    # Source files
    src_usdz = Path(f"outputs/{winner_id}_safety.usdz")
    src_glb = Path(f"outputs/{winner_id}_safety.glb")
    
    # Dest dir
    dest_dir = Path("outputs/best_angle_package")
    dest_dir.mkdir(exist_ok=True)
    
    if src_usdz.exists():
        shutil.copy(src_usdz, dest_dir / "best_model.usdz")
        print(f"  Copied USDZ to {dest_dir}/best_model.usdz")
        
    if src_glb.exists():
        shutil.copy(src_glb, dest_dir / "best_model.glb")
        print(f"  Copied GLB to {dest_dir}/best_model.glb")

if __name__ == "__main__":
    # If args provided, use them. Else look for golden_angle_hr_*
    if len(sys.argv) > 1:
        ids = sys.argv[1:]
    else:
        # Auto-discover
        import glob
        files = glob.glob("outputs/golden_angle_hr_*_debug_metrics.json")
        ids = [Path(f).name.replace("_debug_metrics.json", "") for f in files]
        
    winner = select_best_angle(ids)
    if winner:
        package_winner(winner)
