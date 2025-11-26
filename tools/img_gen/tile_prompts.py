# Tile Generation Prompts
# Recommended Settings:
# - Model: Nano Banana / Any Pixel Art Model
# - Resolution: 1024x1024 (Recommended to resize to target size like 96x96 using "Nearest Neighbor" algorithm)
# - Sampler: Euler a / DPM++ 2M Karras

# Common Prefix: Emphasize pixel style, RPG view, grid layout, white background
BASE_PROMPT = (
    "pixel art style, 16-bit rpg game assets, top-down view, "
    "flat shading, high quality, sharp details, "
    "white background, 3x3 grid layout, sprite sheet, "
    "consistent lighting, same color palette"
)

TILE_PROMPTS = {
    # ==========================================
    # Category 1: High Frequency Backgrounds
    # Strategy: Emphasize seamlessness, subtle variations, unified tone, avoid obtrusive objects
    # ==========================================
    
    # Plain/Grassland
    "plain": (
        f"{BASE_PROMPT}, "
        "9 variations of green grass ground tiles, simple meadow texture, "
        "clearly different texture patterns between tiles, clean green lawn, "
        "some tiles with small stone clusters, some with sparse weeds, some with slightly drier patches, "
        "seamless pattern style, harmonious but not identical soothing green color"
    ),

    # Desert
    "desert": (
        f"{BASE_PROMPT}, "
        "9 variations of yellow sand ground tiles, desert floor texture, "
        "smooth sand with clearly different wind ripple directions and density, "
        "some tiles with small pebble clusters or tiny dried bushes, "
        "arid atmosphere, golden yellow color with slightly varied brightness, "
        "uniform texture"
    ),

    # Water/Sea
    "water": (
        f"{BASE_PROMPT}, "
        "9 variations of blue water surface tiles, lake texture, "
        "calm liquid surface with clearly different ripple shapes and wave crest directions, "
        "some tiles with gentle foam, some with brighter specular highlights, some almost flat, "
        "no islands, no rocks, clear blue color, "
        "consistent water pattern"
    ),

    # Glacier/Snow
    "glacier": (
        f"{BASE_PROMPT}, "
        "9 variations of white snow ground tiles, frozen ground texture, "
        "clean white snow with clearly different accumulation shapes, "
        "some tiles with clear shallow footprints, some with cracked ice patterns, subtle blueish tint, "
        "soft smooth surface, no rocks, seamless winter field"
    ),

    # Swamp
    "swamp": (
        f"{BASE_PROMPT}, "
        "9 variations of murky swamp ground tiles, dark purple and green mud, "
        "wet muddy ground with clearly different puddle shapes and distributions, "
        "some tiles with many bubbles, some with floating leaves, some almost only dark mud, "
        "toxic atmosphere, dark and gloomy color palette, flat texture"
    ),

    # ==========================================
    # Category 2: Obstacles & Terrain
    # Strategy: Emphasize independent objects, centered, clear outlines, slight shape variations without changing style
    # ==========================================

    # Forest - Temperate
    "forest": (
        f"{BASE_PROMPT}, "
        "9 variations of green oak trees, individual map trees, "
        "isolated trees centered in grid cells, "
        "strong differences in tree crown shape, height and density, same green foliage color, "
        "some tiles with one big tree, some with two thinner trees, some with a lower bushy tree, "
        "compact trees, game asset style, clear outline"
    ),

    # Rainforest - Tropical
    "rainforest": (
        f"{BASE_PROMPT}, "
        "9 variations of jungle palm trees and broadleaf trees, individual trees, "
        "isolated trees centered in grid cells, "
        "tropical dark green vibrant colors, strong variation in crown size, leaf shapes and trunk height, "
        "some tiles with hanging vines, some with extra side leaves, some with double trunks, "
        "rpg map obstacle, clear outline"
    ),

    # Mountain - Rocky
    "mountain": (
        f"{BASE_PROMPT}, "
        "9 variations of grey rocky mountains, small individual mountain peaks, "
        "isolated peaks centered in grid cells, "
        "clearly different peak shapes and slopes, some tall and thin, some low and wide, some double peaks, "
        "grey stone texture with moss hints, similar overall height, clear outline"
    ),

    # Snow Mountain
    "snow_mountain": (
        f"{BASE_PROMPT}, "
        "9 variations of snow-capped mountains, individual snowy peaks, "
        "isolated peaks centered in grid cells, "
        "different amounts of snow and rock exposed, some with wide snow caps, some with more rock showing, "
        "white snow on top, grey rock at bottom, "
        "compact shape, cold atmosphere, clear outline"
    ),

    # Volcano
    "volcano": (
        f"{BASE_PROMPT}, "
        "9 variations of active volcanoes, small individual volcano peaks, "
        "isolated peaks centered in grid cells, "
        "different crater openings and lava glow intensity, some narrow and tall, some wide and flat, "
        "some tiles with heavy smoke plumes, some with side lava cracks, "
        "dark rock with magma crater on top, dangerous red and black colors, clear outline"
    ),

    # City - Icon for world map
    "city": (
        f"{BASE_PROMPT}, "
        "9 variations of small ancient chinese houses, map icon style, "
        "isolated buildings centered in grid cells, "
        "clearly different roof shapes and small courtyard layouts, some with one house, some with two connected houses, "
        "grey tiled roofs, white walls, asian architecture, "
        "compact simple structure, similar size"
    ),

    # Sect - More magnificent than cities
    "sect": (
        f"{BASE_PROMPT}, "
        "9 variations of mystical chinese fantasy pavilions, map icon style, "
        "isolated floating palaces or pagodas centered in grid cells, "
        "strong variation in roof layers and tower heights, some with tall spires, some with wide halls, some with side towers, "
        "elegant blue and gold roofs, magical aura, "
        "ethereal atmosphere, clear outline"
    ),
    
    # Ruins
    "ruins": (
        f"{BASE_PROMPT}, "
        "9 variations of ancient stone ruins, broken pillars and walls, "
        "isolated debris centered in grid cells, "
        "clearly different collapse shapes and arrangements, some with standing half pillars, some mostly rubble, some with broken arches, "
        "weathered grey stone, mossy and cracked, "
        "mysterious atmosphere, clear outline"
    )
}

if __name__ == "__main__":
    print("=== Generated Prompts ===")
    print(f"Base Prompt: {BASE_PROMPT}\n")
    for key, prompt in TILE_PROMPTS.items():
        print(f"--- {key.upper()} ---")
        print(prompt)
        print()
