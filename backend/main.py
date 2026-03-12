import os
from dotenv import load_dotenv

load_dotenv()
import shutil
import subprocess
import uuid
import yaml
import json
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUTS_DIR = os.path.join(BASE_DIR, "inputs")
JOBS_DIR = os.path.join(BASE_DIR, "jobs")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
for d in [INPUTS_DIR, JOBS_DIR, OUTPUTS_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

class JobRequest(BaseModel):
    title: str
    category: str
    specs: Optional[str] = None

def run_job_process(job_id: str, job_file: str, input_file: Optional[str] = None):
    """
    Runs the run_job.py script as a subprocess.
    """
    cmd = ["python", "run_job.py", job_file]
    
    if input_file:
        cmd.extend(["--in", input_file])
    
    print(f"Starting job {job_id}...")
    try:
        # Run in the root directory
        subprocess.run(cmd, cwd=BASE_DIR, check=True)
        print(f"Job {job_id} completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Job {job_id} failed: {e}")

@app.post("/upload")
async def create_job(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    title: str = "Untitled Job",
    category: str = "General",
    specs: str = ""
):
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job_dir = os.path.join(INPUTS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save images
    saved_files = []
    for file in files:
        file_path = os.path.join(job_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
        
    # Create Job YAML
    # We'll use a default template for now, or infer from category
    # For this prototype, we'll default to the "chair_high_risk" template structure
    # but point to the new directory.
    
    # Parse specs if provided
    specs_dict = {}
    if specs:
        try:
            specs_dict = json.loads(specs)
        except json.JSONDecodeError:
            print("Failed to parse specs JSON")

    job_yaml = {
        "job_id": job_id,
        "category": category,
        "photos_dir": f"inputs/{job_id}", # Relative to root
        "material_specs": specs_dict, # Save user inputs
        "declared_parts": [
             # Mock parts for the slicer to find
             {"name": "seat", "material": "fabric", "geometry": "soft", "has_folds": True},
             {"name": "legs", "material": "wood", "geometry": "hard", "has_folds": False}
        ],
        "requested_outputs": ["glb"],
        "constraints": {
            "glb_max_mb": 8,
            "max_tris": 150000,
            "texture_max_px": 1024,
            "roughness_min": 0.08,
            "roughness_max": 0.92,
            "normal_strength_max": 0.6
        }
    }
    
    job_file = os.path.join(JOBS_DIR, f"{job_id}.yaml")
    with open(job_file, "w") as f:
        yaml.dump(job_yaml, f)
        
    # Detect if a GLB was uploaded
    input_glb = None
    for f in saved_files:
        if f.lower().endswith(".glb"):
            input_glb = os.path.join("inputs", job_id, f) # Relative path for runner
            break

    # Trigger Job Runner
    background_tasks.add_task(run_job_process, job_id, f"jobs/{job_id}.yaml", input_glb)
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Job started"
    }

@app.get("/jobs")
def list_jobs():
    # List all YAML files in jobs/
    jobs = []
    if not os.path.exists(JOBS_DIR):
        return []
        
    for f in os.listdir(JOBS_DIR):
        if f.endswith(".yaml"):
            job_id = f.replace(".yaml", "")
            # Check for logs to determine status
            status = "processing"
            
            # Find latest log for this job
            logs = [l for l in os.listdir(LOGS_DIR) if l.startswith(job_id)]
            if logs:
                # Simple check: if log exists, it's done (or failed)
                # We could parse the log for "status": "PROCESSED"
                status = "completed" 
                
            jobs.append({
                "id": job_id,
                "title": title_from_id(job_id), # Helper
                "status": status,
                "category": "Furniture" # Placeholder
            })
    return jobs

def title_from_id(job_id):
    return job_id.replace("job_", "Job ").replace("_", " ").title()

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    # Check if done
    logs = [l for l in os.listdir(LOGS_DIR) if l.startswith(job_id)]
    status = "processing"
    result = None
    
    if logs:
        # Parse the latest log to get actual status
        latest_log = sorted(logs)[-1]
        try:
            with open(os.path.join(LOGS_DIR, latest_log), "r") as f:
                log_data = json.load(f)
                status = "completed" if log_data.get("status") == "PROCESSED" else "failed"
        except Exception:
            status = "failed"

        # Check for output file
        output_path = os.path.join(OUTPUTS_DIR, f"{job_id}_safety.glb")
        if os.path.exists(output_path):
            result = f"/outputs/{job_id}_safety.glb"
            
    return {
        "id": job_id,
        "status": status,
        "result": result
    }

# Serve static outputs for the frontend to fetch
from fastapi.staticfiles import StaticFiles
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
