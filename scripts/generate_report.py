import json
import sys
import os
from pathlib import Path

def generate_report(job_id):
    metrics_path = f"outputs/{job_id}_debug_metrics.json"
    if not os.path.exists(metrics_path):
        print(f"[red]Metrics file not found:[/red] {metrics_path}")
        return

    with open(metrics_path, "r") as f:
        metrics = json.load(f)

    report_lines = []
    report_lines.append(f"# Debug Report: {job_id}")
    report_lines.append("")
    report_lines.append("## Pipeline Metrics")
    report_lines.append("")
    report_lines.append("| Stage | Tris | Dimensions (m) | File Size (MB) | Textures |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")

    # Sort stages by key (00, 01, 02...)
    for stage in sorted(metrics.keys()):
        data = metrics[stage]
        tris = f"{data.get('tris', 0):,}"
        dims = data.get('dimensions', [0,0,0])
        dim_str = f"{dims[0]:.2f} x {dims[1]:.2f} x {dims[2]:.2f}"
        size = f"{data.get('file_size_mb', 0):.2f}"
        tex = f"{data.get('texture_count', 0)} (Max {data.get('max_texture_resolution', 0)}px)"
        
        report_lines.append(f"| **{stage}** | {tris} | {dim_str} | {size} | {tex} |")

    report_lines.append("")
    report_lines.append("## Visuals")
    report_lines.append("(Screenshots to be added manually or via render script)")
    
    out_path = f"outputs/{job_id}_report.md"
    with open(out_path, "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"Generated report: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <job_id>")
        sys.exit(1)
    generate_report(sys.argv[1])
