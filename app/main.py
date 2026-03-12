import os
import json
import subprocess
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from google.cloud import storage
import yaml
import requests
from urllib.parse import urlparse

app = FastAPI()

# GCS Client
storage_client = storage.Client()

class JobRequest(BaseModel):
    job_id: str
    input_url: str # gs://bucket/path/to/image.jpg
    output_bucket: str # bucket_name
    callback_url: str = None
    category: str = "unknown"

def download_blob(bucket_name, source_blob_name, destination_file_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print(f"Downloaded {source_blob_name} to {destination_file_name}")

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"Uploaded {source_file_name} to {destination_blob_name}")

def is_http_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")

def normalize_bucket_name(output_bucket: str) -> str:
    return output_bucket.replace("gs://", "").strip("/")

def upload_bytes_to_gcs(bucket_name: str, dest_path: str, data: bytes, content_type: str):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(dest_path)
    blob.upload_from_string(data, content_type=content_type)
    print(f"Uploaded bytes to gs://{bucket_name}/{dest_path}")
    return f"gs://{bucket_name}/{dest_path}"

def ext_from_url_or_type(url: str, content_type: str) -> str:
    path = urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        return ext
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    return ".jpg"

def process_job(job: JobRequest):
    job_id = job.job_id
    print(f"Processing job {job_id}...")

    input_dir = Path("inputs")
    output_dir = Path("outputs")
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    input_url = job.input_url
    bucket_name = job.output_bucket.replace("gs://", "").strip("/")

    # If HTTP URL → download and upload to GCS first
    if input_url.startswith("http"):
        import requests

        print("Ingested external URL")

        r = requests.get(input_url, timeout=30)
        r.raise_for_status()

        ext = ".jpg"
        local_input = input_dir / f"{job_id}{ext}"

        with open(local_input, "wb") as f:
            f.write(r.content)

        upload_blob(bucket_name, str(local_input), f"inputs/{job_id}{ext}")

        input_url = f"gs://{bucket_name}/inputs/{job_id}{ext}"

    # Must now be gs://
    if not input_url.startswith("gs://"):
        print("Error: Invalid GCS URL")
        return

    parts = input_url.replace("gs://", "").split("/", 1)
    src_bucket = parts[0]
    blob_name = parts[1]

    ext = Path(blob_name).suffix
    local_input_path = input_dir / f"{job_id}{ext}"

    try:
        download_blob(src_bucket, blob_name, str(local_input_path))
    except Exception as e:
        print(f"Failed to download input: {e}")
        return

    # Create Job YAML
    job_yaml_path = Path(f"jobs/{job_id}.yaml")
    job_yaml_path.parent.mkdir(exist_ok=True)
    
    job_data = {
        "job_id": job_id,
        "category": job.category,
        "input_image": str(local_input_path),
        "pipeline": {
            "rembg": False,
            "slicer": False,
            "geometry_rules": False,
            "safety_pass": True
        }
    }
    
    with open(job_yaml_path, "w") as f:
        yaml.dump(job_data, f)
        
    # Run Pipeline
    try:
        cmd = ["python", "run_job.py", str(job_yaml_path)]
        subprocess.run(cmd, check=True)
        print("Pipeline completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed: {e}")
        return

# Upload Outputs (recursive search)
output_files = list(output_dir.rglob("*"))
output_files = [f for f in output_files if f.is_file()]

if not output_files:
    print("No output files found to upload.")
    return

for f in output_files:
    dest_blob = f"outputs/{job_id}/{f.name}"
    try:
        upload_blob(job.output_bucket, str(f), dest_blob)
    except Exception as e:
        print(f"Failed to upload {f.name}: {e}")
        try:
            upload_blob(job.output_bucket, str(f), dest_blob)
        except Exception as e:
            print(f"Failed to upload {f.name}: {e}")
            
    print(f"Job {job_id} complete.")

@app.post("/run_job")
async def run_job_endpoint(job: JobRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_job, job)
    return {"status": "accepted", "job_id": job.job_id}

@app.get("/health")
def health_check():
    return {"status": "ok"}
