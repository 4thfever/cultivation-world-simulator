import os
from typing import Dict, List
from pathlib import Path
from src.classes.tile import TileType


# 统一的贴图类型集合，供各加载函数复用
ALL_TILE_TYPES = [
    TileType.PLAIN, TileType.WATER, TileType.SEA, TileType.MOUNTAIN,
    TileType.FOREST, TileType.CITY, TileType.DESERT, TileType.RAINFOREST,
    TileType.GLACIER, TileType.SNOW_MOUNTAIN, TileType.VOLCANO,
    TileType.GRASSLAND, TileType.SWAMP, TileType.CAVE, TileType.RUINS, TileType.FARM
]


def load_tile_images(pygame_mod, tile_size: int) -> Dict[TileType, object]:
    images: Dict[TileType, object] = {}
    for tile_type in ALL_TILE_TYPES:
        image_path = f"assets/tiles/{tile_type.value}.png"
        if os.path.exists(image_path):
            image = pygame_mod.image.load(image_path)
            scaled = pygame_mod.transform.scale(image, (tile_size, tile_size))
            images[tile_type] = scaled
    return images


def load_tile_originals(pygame_mod) -> Dict[TileType, object]:
    originals: Dict[TileType, object] = {}
    for tile_type in ALL_TILE_TYPES:
        image_path = f"assets/tiles/{tile_type.value}.png"
        if os.path.exists(image_path):
            originals[tile_type] = pygame_mod.image.load(image_path)
    return originals


def load_avatar_images(pygame_mod, tile_size: int):
    def load_from_dir(base_dir: str) -> List[object]:
        results: List[object] = []
        if os.path.exists(base_dir):
            for filename in os.listdir(base_dir):
                if filename.endswith('.png') and filename != 'original.png' and filename.replace('.png', '').isdigit():
                    image_path = os.path.join(base_dir, filename)
                    image = pygame_mod.image.load(image_path)
                    avatar_size = max(26, int((tile_size * 4 // 3) * 1.8))
                    scaled = pygame_mod.transform.scale(image, (avatar_size, avatar_size))
                    results.append(scaled)
        return results
    return load_from_dir("assets/males"), load_from_dir("assets/females")


def load_sect_images(pygame_mod, tile_size: int):
    """
    加载宗门总部图片，缩放为 2x2 tile 大小，返回按文件名（不含后缀）为键的图像字典。
    文件名建议与宗门名称一致。
    """
    images: Dict[str, object] = {}
    base_dir = Path("assets/sects")
    if base_dir.exists():
        for filename in base_dir.iterdir():
            if filename.suffix.lower() == ".png" and filename.name != "original.png":
                try:
                    image = pygame_mod.image.load(str(filename))
                    scaled = pygame_mod.transform.scale(image, (tile_size * 2, tile_size * 2))
                    images[filename.stem] = scaled
                except pygame_mod.error:
                    continue
    return images


def load_region_images(pygame_mod, tile_size: int) -> Dict[str, Dict[int, object]]:
    """
    加载小区域整图：按名称加载 assets/regions/<name>.png。
    为兼容 2x2 和 3x3，分别生成两种缩放版本：
    - key 2 -> (tile_size*2, tile_size*2)
    - key 3 -> (tile_size*3, tile_size*3)
    返回结构: { name: {2: surf2x2, 3: surf3x3} }
    """
    results: Dict[str, Dict[int, object]] = {}
    base_dir = Path("assets/regions")
    if base_dir.exists():
        for filename in base_dir.iterdir():
            if filename.suffix.lower() != ".png" or filename.name == "original.png":
                continue
            try:
                image = pygame_mod.image.load(str(filename))
            except pygame_mod.error:
                continue
            name_key = filename.stem
            variants: Dict[int, object] = {}
            for n in (2, 3):
                w = tile_size * n
                h = tile_size * n
                variants[n] = pygame_mod.transform.scale(image, (w, h))
            results[name_key] = variants
    return results


__all__ = [
    "load_tile_images",
    "load_tile_originals",
    "load_avatar_images",
    "load_sect_images",
    "load_region_images",
    "ALL_TILE_TYPES",
]


