"""
图片切分工具：将2x2大图切分为4个64x64的tile切片。

用法：
    python tools/slice_images.py           # 仅切分未处理的图片
    python tools/slice_images.py --force   # 强制重新切分所有图片
"""
import os
from PIL import Image
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

TARGET_SIZE = (128, 128)  # 2x2 tile size (64*2)
TILE_SIZE = 64


def slice_image(image_path, force=False):
    """
    切分图片为4个64x64的tile。
    如果已存在切片文件且force=False，则跳过。
    """
    base_name, ext = os.path.splitext(image_path)
    
    # 检查是否已切分（通过检查_0文件是否存在）
    slice_0_path = f"{base_name}_0{ext}"
    if os.path.exists(slice_0_path) and not force:
        print(f"Skipped (already sliced): {os.path.basename(image_path)}")
        return
    
    try:
        img = Image.open(image_path)
        # Resize if necessary (to match 2x2 tiles exactly)
        if img.size != TARGET_SIZE:
            img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        
        # 0: TL, 1: TR, 2: BL, 3: BR
        pieces = [
            (0, 0, TILE_SIZE, TILE_SIZE),                          # TL
            (TILE_SIZE, 0, TILE_SIZE * 2, TILE_SIZE),              # TR
            (0, TILE_SIZE, TILE_SIZE, TILE_SIZE * 2),              # BL
            (TILE_SIZE, TILE_SIZE, TILE_SIZE * 2, TILE_SIZE * 2)   # BR
        ]
        
        for i, box in enumerate(pieces):
            piece = img.crop(box)
            save_path = f"{base_name}_{i}{ext}"
            piece.save(save_path)
            
        print(f"Sliced: {os.path.basename(image_path)}")
            
    except Exception as e:
        print(f"Error slicing {image_path}: {e}")


def process_folder(folder_name, extensions=['.png', '.jpg', '.jpeg'], force=False):
    folder_path = os.path.join(ASSETS_DIR, folder_name)
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder_path, f"*{ext}")))
    
    for f in files:
        # Skip already sliced files (ending with _0, _1, _2, _3)
        stem = os.path.splitext(os.path.basename(f))[0]
        if len(stem) >= 2 and stem[-2] == '_' and stem[-1] in ['0', '1', '2', '3']:
            continue
        
        slice_image(f, force)


def process_specific_files(folder_name, filenames, force=False):
    folder_path = os.path.join(ASSETS_DIR, folder_name)
    for name in filenames:
        # Try png/jpg
        found = False
        for ext in ['.png', '.jpg']:
            path = os.path.join(folder_path, name + ext)
            if os.path.exists(path):
                slice_image(path, force)
                found = True
                break
        if not found:
            print(f"File not found: {name} in {folder_name}")


if __name__ == "__main__":
    import sys
    force = '--force' in sys.argv
    
    print("Starting image slicing..." + (" (FORCE MODE)" if force else ""))
    
    # 1. Sects
    print("\nProcessing Sects...")
    process_folder("sects", force=force)
    
    # 2. Cities
    print("\nProcessing Cities...")
    process_folder("cities", force=force)
    
    # 3. Special Tiles (Cave, Ruin)
    print("\nProcessing Special Tiles...")
    process_specific_files("tiles", ["cave", "ruin"], force=force)
    
    print("\nDone.")
