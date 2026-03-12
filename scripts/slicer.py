import os
import numpy as np
from typing import List, Dict, Any
from rich import print
from PIL import Image
from rembg import remove

def slice_image(job_id: str, photos_dir: str, parts: List[Dict[str, Any]], skip_bg: bool = False) -> Dict[str, str]:
    """
    Slices an image into parts using AI background removal and smart cropping.
    If skip_bg is True, uses the original image as-is (no removal, no cropping).
    """
    print(f"\n[bold]Slicing Image for Job:[/bold] {job_id} (Skip BG: {skip_bg})")
    
    results = {}
    
    # Ensure photos_dir exists
    if not os.path.exists(photos_dir):
        print(f"[red]Photos directory not found:[/red] {photos_dir}")
        return {}

    # List available files
    files = os.listdir(photos_dir)
    
    # Find main image
    main_image = None
    for f in files:
        if f.lower().startswith("main."):
            main_image = os.path.join(photos_dir, f)
            break
            
    # Fallback: If no "main" image, just take the first image found
    if not main_image:
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                main_image = os.path.join(photos_dir, f)
                break
    
    if not main_image:
        print("[red]No valid input image found to slice.[/red]")
        return {}

    print(f"[dim]Using source image:[/dim] {os.path.basename(main_image)}")
    
    if skip_bg:
        print("  [yellow]Skipping background removal and slicing as requested.[/yellow]")
        # Just map every part to the original image
        for part in parts:
            results[part["name"]] = main_image
        return results
    
    try:
        # 1. Load and Remove Background
        print("  - Removing background (AI)...")
        with open(main_image, "rb") as i:
            input_data = i.read()
            output_data = remove(input_data)
            
        # Save the transparent version
        clean_path = os.path.join(photos_dir, "clean_cutout.png")
        with open(clean_path, "wb") as o:
            o.write(output_data)
            
        with Image.open(clean_path) as img:
            # 2. Tight Crop (Bounding Box)
            bbox = img.getbbox()
            if bbox:
                print(f"  - Tight cropping to content: {bbox}")
                img = img.crop(bbox)
            
            width, height = img.size
            
            # 3. Smart Split Logic
            # We want to find the "neck" - the thinnest part of the object in the vertical center.
            # This is often where the chair seat meets the legs.
            
            # Convert to numpy to analyze alpha channel
            # Alpha is the 4th channel (index 3)
            img_np = np.array(img)
            alpha = img_np[:, :, 3]
            
            # Calculate width of object at each row (sum of non-zero alpha pixels)
            row_widths = np.sum(alpha > 0, axis=1)
            
            # Look for the "neck" in the middle 20-80% of the image
            search_start = int(height * 0.4)
            search_end = int(height * 0.8)
            
            # Find the row with the minimum width in this range
            # We add search_start because argmin returns index relative to the slice
            if search_end > search_start:
                neck_y = np.argmin(row_widths[search_start:search_end]) + search_start
                print(f"  - Detected split point (neck) at Y={neck_y} (width={row_widths[neck_y]}px)")
            else:
                neck_y = int(height * 0.65) # Fallback
                print(f"  - Using fallback split point at Y={neck_y}")

            for part in parts:
                p_name = part["name"].lower()
                output_path = os.path.join(photos_dir, f"{p_name}_sliced.png")
                
                if "legs" in p_name or "base" in p_name:
                    # Bottom Part
                    # We create a new blank image and paste the bottom part
                    # This preserves the transparency of the top part
                    part_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                    
                    # Crop the bottom part from the source
                    bottom_crop = img.crop((0, neck_y, width, height))
                    
                    # Paste it into the new image at the correct position
                    part_img.paste(bottom_crop, (0, neck_y))
                    
                    # Actually, for Tripo, it might be better to just send the cropped content
                    # rather than a full canvas with empty space.
                    # Let's just save the crop itself for better resolution usage.
                    part_img = bottom_crop
                    
                    print(f"  - Part '{p_name}': Saved bottom section")
                    part_img.save(output_path)
                    results[part["name"]] = output_path
                    
                elif "seat" in p_name or "body" in p_name or "top" in p_name:
                    # Top Part
                    top_crop = img.crop((0, 0, width, neck_y))
                    
                    print(f"  - Part '{p_name}': Saved top section")
                    top_crop.save(output_path)
                    results[part["name"]] = output_path
                    
                else:
                    # Fallback
                    print(f"  - Part '{p_name}': Using full image")
                    img.save(output_path)
                    results[part["name"]] = output_path
                    
    except Exception as e:
        print(f"[red]Error during slicing:[/red] {e}")
        import traceback
        traceback.print_exc()
        return {}
            
    return results
