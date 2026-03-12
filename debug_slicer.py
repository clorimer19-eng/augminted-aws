import os
import shutil
from scripts.slicer import slice_image

# Setup
job_id = "debug_slice"
photos_dir = "inputs/debug_slice"
if os.path.exists(photos_dir):
    shutil.rmtree(photos_dir)
os.makedirs(photos_dir)

# Copy test image
shutil.copy("tests/fixtures/real_chair.jpg", f"{photos_dir}/main.jpg")

# Define parts
parts = [
    {"name": "seat"},
    {"name": "legs"}
]

# Run
print("Running slicer...")
results = slice_image(job_id, photos_dir, parts)
print("Results:", results)
