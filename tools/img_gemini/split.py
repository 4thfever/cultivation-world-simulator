import os
from PIL import Image, ImageChops

def trim_white_border(img, tolerance=50, shrink=2):
    """
    Trims white border from the image with tolerance.
    Args:
        img: PIL Image to trim
        tolerance: Threshold for difference from white (0-255). 
                   Higher value means more aggressive trimming.
        shrink: Number of pixels to shrink inwards after finding the bbox.
                Helps remove anti-aliasing artifacts/white halo.
    """
    if img.mode == 'RGBA':
        # Create a white background image
        bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
        # Composite the image on top
        comp = Image.alpha_composite(bg, img)
        rgb_img = comp.convert('RGB')
    else:
        rgb_img = img.convert('RGB')

    # Compare with pure white
    bg_white = Image.new('RGB', img.size, (255, 255, 255))
    diff = ImageChops.difference(rgb_img, bg_white)
    
    # Convert to grayscale to find "distance" from white
    diff = diff.convert('L')
    
    # Create a mask where Content=255, Background=0
    mask = diff.point(lambda x: 255 if x > tolerance else 0)
    
    bbox = mask.getbbox()
    if bbox:
        left, upper, right, lower = bbox
        
        # Apply shrink to remove the "halo"
        if shrink > 0:
            left += shrink
            upper += shrink
            right -= shrink
            lower -= shrink
            
            # Safety check: ensure we didn't shrink into nothingness
            if left >= right or upper >= lower:
                # Revert to original bbox if shrink was too aggressive
                left, upper, right, lower = bbox

        return img.crop((left, upper, right, lower))
    
    return img

def split_and_process():
    base_dir = os.path.dirname(__file__)
    origin_dir = os.path.join(base_dir, 'origin')
    split_dir = os.path.join(base_dir, 'split')
    
    if not os.path.exists(split_dir):
        os.makedirs(split_dir)
        
    if not os.path.exists(origin_dir):
        print(f"Origin directory not found: {origin_dir}")
        return

    files = [f for f in os.listdir(origin_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not files:
        print("No images found in origin directory.")
        return

    print(f"Found {len(files)} images to process.")

    for filename in files:
        filepath = os.path.join(origin_dir, filename)
        try:
            img = Image.open(filepath)
            w, h = img.size
            cell_w = w // 3
            cell_h = h // 3
            
            base_name = os.path.splitext(filename)[0]
            print(f"Processing {filename} ({w}x{h})...")

            count = 0
            for r in range(3):
                for c in range(3):
                    count += 1
                    left = c * cell_w
                    upper = r * cell_h
                    right = left + cell_w
                    lower = upper + cell_h
                    
                    # Crop the grid cell
                    crop = img.crop((left, upper, right, lower))
                    
                    # Remove white border with more aggressive tolerance and shrinking
                    # Tolerance 50 + Shrink 2px usually kills the halo
                    final_img = trim_white_border(crop, tolerance=50, shrink=2)
                    
                    save_name = f"{base_name}_{count}.png"
                    save_path = os.path.join(split_dir, save_name)
                    final_img.save(save_path)
            
            print(f"Finished {filename}")
            
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    split_and_process()
