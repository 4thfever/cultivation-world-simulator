import os
from PIL import Image
import glob

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def split_image(image_path):
    try:
        img = Image.open(image_path)
        w, h = img.size
        
        # 假设我们要切成 2x2
        # 无论原图多大，都切成 4 份
        # 或者强制 resize 到 128x128 (64*2) 再切？
        # 用户之前的代码里 TILE_SIZE = 64。
        # 最好保持原图比例，或者检查是否是正方形
        
        # 为了保证清晰度，我们按照原图尺寸切分，前端显示时会自动缩放到 TILE_SIZE
        # 只要是 2x2 的逻辑关系即可
        
        half_w = w // 2
        half_h = h // 2
        
        # 0: TL, 1: TR, 2: BL, 3: BR
        pieces = [
            (0, 0, half_w, half_h),
            (half_w, 0, w, half_h),
            (0, half_h, half_w, h),
            (half_w, half_h, w, h)
        ]
        
        base_name, ext = os.path.splitext(image_path)
        
        generated_files = []
        for i, box in enumerate(pieces):
            # Crop
            piece = img.crop(box)
            
            # Save as _0, _1, _2, _3
            # 统一保存为 png 以支持透明度（虽然 jpg 源文件可能不支持，但统一输出比较好管理）
            # 如果源文件是 jpg，切分后也存为 jpg 可能会丢失透明度信息（虽然 jpg 本身就没有），
            # 但如果为了统一 web 加载逻辑，最好统一格式？
            # 不，还是保持原扩展名或者统一 png。为了兼容性，统一存为 .png 比较稳妥（特别是 sects 都是 png）。
            # 只有 cities 有 jpg。
            
            # 决定：统一输出 .png，方便前端逻辑统一
            save_path = f"{base_name}_{i}.png"
            piece.save(save_path, "PNG")
            generated_files.append(save_path)
            
        print(f"Split {os.path.basename(image_path)} -> 4 parts")
        return generated_files
        
    except Exception as e:
        print(f"Error splitting {image_path}: {e}")
        return []

def main():
    # 1. Sects
    sect_files = glob.glob(os.path.join(ASSETS_DIR, "sects", "*.png"))
    # Filter out already split files (ending with _0.png, etc)
    sect_files = [f for f in sect_files if not (f.endswith("_0.png") or f.endswith("_1.png") or f.endswith("_2.png") or f.endswith("_3.png"))]
    
    for f in sect_files:
        split_image(f)
        
    # 2. Cities
    city_files = glob.glob(os.path.join(ASSETS_DIR, "cities", "*.*"))
    city_files = [f for f in city_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    city_files = [f for f in city_files if not (f.split('.')[0].endswith("_0") or f.split('.')[0].endswith("_1"))] # Simple check
    
    for f in city_files:
        split_image(f)

    # 3. Special Tiles (Cave, Ruin)
    # cave.png, ruin.png (注意之前代码里有时候叫 ruins.png, 有时候叫 ruin.png, 现在统一处理)
    # 检查 assets/tiles 下的文件
    special_names = ['cave', 'ruin', 'ruins']
    for name in special_names:
        path = os.path.join(ASSETS_DIR, "tiles", f"{name}.png")
        if os.path.exists(path):
            split_image(path)
        else:
            # Try jpg just in case?
            pass

if __name__ == "__main__":
    main()

