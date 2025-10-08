import os
from typing import Dict, List
from pathlib import Path
from src.classes.tile import TileType


def load_tile_images(pygame_mod, tile_size: int) -> Dict[TileType, object]:
    images: Dict[TileType, object] = {}
    tile_types = [
        TileType.PLAIN, TileType.WATER, TileType.SEA, TileType.MOUNTAIN,
        TileType.FOREST, TileType.CITY, TileType.DESERT, TileType.RAINFOREST,
        TileType.GLACIER, TileType.SNOW_MOUNTAIN, TileType.VOLCANO,
        TileType.GRASSLAND, TileType.SWAMP, TileType.CAVE, TileType.RUINS, TileType.FARM
    ]
    for tile_type in tile_types:
        image_path = f"assets/tiles/{tile_type.value}.png"
        if os.path.exists(image_path):
            image = pygame_mod.image.load(image_path)
            scaled = pygame_mod.transform.scale(image, (tile_size, tile_size))
            images[tile_type] = scaled
    return images


def load_avatar_images(pygame_mod, tile_size: int):
    male_avatars: List[object] = []
    female_avatars: List[object] = []

    male_dir = "assets/males"
    if os.path.exists(male_dir):
        for filename in os.listdir(male_dir):
            if filename.endswith('.png') and filename != 'original.png' and filename.replace('.png', '').isdigit():
                image_path = os.path.join(male_dir, filename)
                image = pygame_mod.image.load(image_path)
                avatar_size = max(26, int((tile_size * 4 // 3) * 1.2))
                scaled = pygame_mod.transform.scale(image, (avatar_size, avatar_size))
                male_avatars.append(scaled)

    female_dir = "assets/females"
    if os.path.exists(female_dir):
        for filename in os.listdir(female_dir):
            if filename.endswith('.png') and filename != 'original.png' and filename.replace('.png', '').isdigit():
                image_path = os.path.join(female_dir, filename)
                try:
                    image = pygame_mod.image.load(image_path)
                    avatar_size = max(26, int(tile_size * 4 // 3 * 0.8 * 1.2 * 1.2 * 1.2))
                    scaled = pygame_mod.transform.scale(image, (avatar_size, avatar_size))
                    female_avatars.append(scaled)
                except pygame_mod.error:
                    continue

    return male_avatars, female_avatars


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


__all__ = ["load_tile_images", "load_avatar_images", "load_sect_images"]


