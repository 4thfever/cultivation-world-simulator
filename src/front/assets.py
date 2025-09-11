import os
from typing import Dict, List
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
                try:
                    image = pygame_mod.image.load(image_path)
                    avatar_size = max(26, int(tile_size * 4 // 3))
                    scaled = pygame_mod.transform.scale(image, (avatar_size, avatar_size))
                    male_avatars.append(scaled)
                except pygame_mod.error:
                    continue

    female_dir = "assets/females"
    if os.path.exists(female_dir):
        for filename in os.listdir(female_dir):
            if filename.endswith('.png') and filename != 'original.png' and filename.replace('.png', '').isdigit():
                image_path = os.path.join(female_dir, filename)
                try:
                    image = pygame_mod.image.load(image_path)
                    avatar_size = max(26, int(tile_size * 4 // 3 * 0.8 * 1.2))
                    scaled = pygame_mod.transform.scale(image, (avatar_size, avatar_size))
                    female_avatars.append(scaled)
                except pygame_mod.error:
                    continue

    return male_avatars, female_avatars


__all__ = ["load_tile_images", "load_avatar_images"]


