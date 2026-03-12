import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path to import scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.tripo_client import generate_glb_from_image

def verify_tripo(image_path):
    load_dotenv()
    api_key = os.environ.get("TRIPO_API_KEY")
    
    if not api_key:
        print("[ERROR] TRIPO_API_KEY not found in environment.")
        return

    if not os.path.exists(image_path):
        print(f"[ERROR] Image not found: {image_path}")
        return

    print(f"\n=== Verifying Tripo API ===")
    print(f"Input Image: {image_path}")
    
    output_dir = Path("tests/results")
    output_dir.mkdir(exist_ok=True)
    
    output_filename = f"tripo_test_{int(time.time())}.glb"
    output_path = output_dir / output_filename
    
    print(f"Target Output: {output_path}")
    print("Starting generation (this may take 1-3 minutes)...")
    
    try:
        generate_glb_from_image(image_path, str(output_path), api_key)
        print(f"\n[SUCCESS] Model generated successfully!")
        print(f"File saved to: {output_path}")
        print(f"Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"\n[FAIL] Generation failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/verify_tripo.py <path_to_image>")
        print("Example: python tests/verify_tripo.py tests/fixtures/chair_test.jpg")
    else:
        verify_tripo(sys.argv[1])
