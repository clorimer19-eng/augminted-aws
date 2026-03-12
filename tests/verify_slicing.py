import os
import time
import requests
import shutil
from pathlib import Path

# Config
API_URL = "http://localhost:8000"
TEST_IMAGE = "tests/fixtures/real_chair.jpg"
EXPECTED_JOB_DIR = "inputs"

def setup_fixture():
    """Ensures we have a test image to upload."""
    if not os.path.exists(TEST_IMAGE):
        print(f"[ERROR] Test image not found at {TEST_IMAGE}")
        exit(1)

def verify_slicing():
    print("\n=== Verifying Slicing Logic ===")
    
    # 1. Upload
    print(f"[1] Uploading {TEST_IMAGE}...")
    with open(TEST_IMAGE, "rb") as f:
        files = {"files": f}
        data = {"specs": '{"material": "wood"}'}
        response = requests.post(f"{API_URL}/upload", files=files, data=data)
    
    if response.status_code != 200:
        print(f"[ERROR] Upload failed: {response.text}")
        return

    job_id = response.json()["job_id"]
    print(f"    -> Job started: {job_id}")
    
    # 2. Monitor Slicing
    print(f"[2] Waiting for Slicing...")
    job_input_dir = Path(EXPECTED_JOB_DIR) / job_id
    max_retries = 15
    sliced = False
    
    for i in range(max_retries):
        time.sleep(1)
        seat = job_input_dir / "seat_sliced.png"
        legs = job_input_dir / "legs_sliced.png"
        
        if seat.exists() and legs.exists():
            print(f"    -> [SUCCESS] Slicing confirmed!")
            print(f"       Seat: {seat}")
            print(f"       Legs: {legs}")
            sliced = True
            break
        print(f"       Waiting... ({i+1}/{max_retries})")
            
    if not sliced:
        print("    -> [FAIL] Slicing timed out. Check logs.")
    else:
        print("\n[INFO] You can now inspect the sliced images in the paths above.")

if __name__ == "__main__":
    setup_fixture()
    verify_slicing()
