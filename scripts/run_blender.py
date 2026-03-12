import subprocess
from typing import Dict, Any


BLENDER_BIN = "/Applications/Blender.app/Contents/MacOS/Blender"


def run_safety_pass(
    in_path: str,
    out_path: str,
    constraints: Dict[str, Any],
) -> None:
    max_tris = int(constraints.get("max_tris", 150000))
    rough_min = float(constraints.get("roughness_min", 0.08))
    rough_max = float(constraints.get("roughness_max", 0.92))
    normal_max = float(constraints.get("normal_strength_max", 0.6))
    texture_max = int(constraints.get("texture_max_px", 2048))


    cmd = [
        BLENDER_BIN, "-b",
        "-P", "blender/safety_pass.py",
        "--",
        "--in", in_path,
        "--out", out_path,
        "--max_tris", str(max_tris),
        "--rough_min", str(rough_min),
        "--rough_max", str(rough_max),
        "--normal_max", str(normal_max),
        "--texture_max", str(texture_max),
    ]


    subprocess.run(cmd, check=True)
