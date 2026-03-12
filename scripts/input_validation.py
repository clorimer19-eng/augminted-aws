import os
import sys
import numpy as np
from PIL import Image
from dataclasses import dataclass
from typing import Tuple, List

@dataclass
class ValidationResult:
    valid: bool
    reasons: List[str]

def validate_image(image_path: str) -> ValidationResult:
    if not os.path.exists(image_path):
        return ValidationResult(False, [f"Image file not found: {image_path}"])

    try:
        with Image.open(image_path) as img:
            # Convert to RGB to handle RGBA/P modes
            img = img.convert('RGB')
            width, height = img.size
            
            reasons = []
            
            # v1 Lock: Strict resolution gate
            # "Minimum usable resolution (≥ ~1024px shortest edge)"
            width, height = img.size
            min_edge = min(width, height)
            if min_edge < 1024:
                return ValidationResult(False, [f"Resolution too low: Shortest edge {min_edge}px < 1024px"])

            # Convert to numpy for pixel analysis
            arr = np.array(img)
            
            # 2. Object Coverage (Simple Thresholding)
            # Assume studio background is bright/white.
            # Calculate luminosity: 0.299*R + 0.587*G + 0.114*B
            lum = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
            
            # Threshold: Pixels darker than 240 (allow some noise in white bg) are "object"
            # This is a heuristic for studio shots.
            object_pixels = np.sum(lum < 240)
            total_pixels = width * height
            coverage = object_pixels / total_pixels
            
            if coverage < 0.15:
                reasons.append(f"Object coverage too low: {coverage:.1%} < 15%")

            # 3. Non-Photographic Detection
            # A. Flat Color Dominance
            # Check standard deviation of local regions? Or just global std dev?
            # Global std dev is cheap.
            std_dev = np.std(lum)
            if std_dev < 10: # Very flat image
                reasons.append(f"Low texture variance (StdDev={std_dev:.1f}): Possible vector/flat art")
                
            # B. Unique Colors (Palette check)
            # Real photos have thousands of unique colors due to noise/lighting.
            # Vector art has few.
            # Downsample for speed
            small = img.resize((100, 100))
            small_arr = np.array(small)
            unique_colors = len(np.unique(small_arr.reshape(-1, 3), axis=0))
            if unique_colors < 500: # Heuristic
                reasons.append(f"Low color complexity ({unique_colors} unique): Possible vector/flat art")

            if reasons:
                return ValidationResult(False, reasons)
            
            return ValidationResult(True, [])

    except Exception as e:
        return ValidationResult(False, [f"Validation error: {str(e)}"])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python input_validation.py <image_path>")
        sys.exit(1)
        
    res = validate_image(sys.argv[1])
    if res.valid:
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        for r in res.reasons:
            print(f"- {r}")
        sys.exit(1)
