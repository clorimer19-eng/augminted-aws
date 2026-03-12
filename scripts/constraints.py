import json
import os
from typing import Any, Dict, List, Tuple

# Load Presets
PRESETS_PATH = os.path.join(os.path.dirname(__file__), "../config/presets.json")
try:
    with open(PRESETS_PATH, "r") as f:
        CONFIG = json.load(f)
except Exception as e:
    print(f"[WARN] Could not load presets.json: {e}")
    CONFIG = {"global": {}, "presets": {}}

GLOBAL_RULES = CONFIG.get("global", {})
PRESETS = CONFIG.get("presets", {})

def get_preset_for_job(job: Dict[str, Any]) -> str:
    """
    Routes a job to a material preset based on category or explicit hint.
    """
    # 1. Explicit Hint
    hint = job.get("material_hint", "").lower()
    if hint in PRESETS:
        return hint
        
    # 2. Category Routing
    cat = job.get("category", "").lower()
    
    if cat in ["rug", "mat", "carpet"]:
        return "fabric_high_risk"
    elif cat in ["chair_wood", "table_wood", "cabinet"]:
        return "wood"
    elif cat in ["chair_plastic", "lamp_plastic"]:
        return "matte_paint_plastic"
    elif cat in ["lamp_metal", "chair_metal"]:
        return "metal"
        
    # Default fallback
    return "semi_gloss"

def enforce_constraints(job: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Validates job against GLOBAL safety rules.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Global Safety Limits
    rmin = GLOBAL_RULES.get("roughness_min", 0.08)
    rmax = GLOBAL_RULES.get("roughness_max", 0.92)
    nmax = GLOBAL_RULES.get("normal_max", 0.6)
    max_tris = GLOBAL_RULES.get("max_tris", 150000)
    max_mb = GLOBAL_RULES.get("max_file_mb", 8)
    
    # We don't strictly enforce these on the *input* job definition, 
    # but we check if the job *requests* something dangerous.
    
    # Check for unsupported materials (Transparency)
    mat_hint = job.get("material_hint", "").lower()
    if "glass" in mat_hint or "water" in mat_hint or "transparent" in mat_hint:
        errors.append("Unsupported material: Transparency/Refraction is currently rejected.")

    # Scale Check (Mock implementation - would need bounding box analysis)
    # if job.get("dimensions", {}).get("height", 0) > 3.0:
    #     errors.append("Implausible scale: Object > 3m tall.")

    return errors, warnings

