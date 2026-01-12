import os
import csv
import shutil
from pathlib import Path

# Configs
CONFIG_DIR = Path("static/game_configs")
ASSETS_DIR = Path("assets/sects")
TILE_MAP_PATH = CONFIG_DIR / "tile_map.csv"
SECT_PATH = CONFIG_DIR / "sect.csv"

def load_sect_mapping():
    """Load sect name -> id mapping"""
    mapping = {}
    if not SECT_PATH.exists():
        print(f"Error: {SECT_PATH} not found")
        return {}
        
    with open(SECT_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        next(reader) # skip comment
        
        try:
            id_idx = header.index('id')
            name_idx = header.index('name')
        except ValueError:
            print("Error parsing sect.csv header")
            return {}
            
        for row in reader:
            if len(row) > max(id_idx, name_idx):
                mapping[row[name_idx].strip()] = row[id_idx].strip()
    return mapping

def rename_assets(mapping):
    """Rename assets from {name}_{i}.png to sect_{id}_{i}.png"""
    print("\n--- Renaming Assets ---")
    if not ASSETS_DIR.exists():
        print(f"Assets dir {ASSETS_DIR} not found")
        return

    count = 0
    for filename in os.listdir(ASSETS_DIR):
        if not filename.endswith(".png"):
            continue
            
        # Parse filename: Name_Index.png
        # Handle names with underscores? Assuming names don't have _ for now, or match longest prefix
        # Actually standard format seems to be Name_0.png
        
        name_part = None
        index_part = None
        
        # Try to find a matching sect name
        matched_sect = None
        for sect_name in mapping.keys():
            if filename.startswith(sect_name + "_"):
                # Check if the rest is a number
                suffix = filename[len(sect_name)+1:] # remove name and _
                if suffix.replace(".png", "").isdigit():
                    matched_sect = sect_name
                    index_part = suffix.replace(".png", "")
                    break
        
        if matched_sect:
            sect_id = mapping[matched_sect]
            new_name = f"sect_{sect_id}_{index_part}.png"
            old_path = ASSETS_DIR / filename
            new_path = ASSETS_DIR / new_name
            
            if old_path != new_path:
                print(f"Renaming: {filename} -> {new_name}")
                shutil.move(old_path, new_path)
                count += 1
        else:
            # Maybe it is just Name.png (icon)?
            if filename.replace(".png", "") in mapping:
                sect_name = filename.replace(".png", "")
                sect_id = mapping[sect_name]
                new_name = f"sect_{sect_id}.png" # Icon
                old_path = ASSETS_DIR / filename
                new_path = ASSETS_DIR / new_name
                print(f"Renaming Icon: {filename} -> {new_name}")
                shutil.move(old_path, new_path)
                count += 1
            else:
                # check if already renamed
                if not filename.startswith("sect_"):
                    print(f"Skipping unknown file: {filename}")

    print(f"Renamed {count} files.")

def update_tile_map(mapping):
    """Update tile_map.csv replacing Name_Index with sect_{id}_{index}"""
    print("\n--- Updating Tile Map ---")
    if not TILE_MAP_PATH.exists():
        print(f"{TILE_MAP_PATH} not found")
        return

    with open(TILE_MAP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    count = 0
    
    # Sort mapping by key length desc to avoid partial replacements (though names should be distinct)
    sorted_sects = sorted(mapping.keys(), key=len, reverse=True)
    
    for sect_name in sorted_sects:
        sect_id = mapping[sect_name]
        # Iterate indices 0-3
        for i in range(4):
            old_str = f"{sect_name}_{i}"
            new_str = f"sect_{sect_id}_{i}"
            if old_str in new_content:
                new_content = new_content.replace(old_str, new_str)
                count += 1
    
    if content != new_content:
        with open(TILE_MAP_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated tile_map.csv (approx {count} replacements)")
    else:
        print("No changes in tile_map.csv")

def main():
    mapping = load_sect_mapping()
    if not mapping:
        print("No mapping loaded")
        return
        
    print(f"Loaded {len(mapping)} sects")
    rename_assets(mapping)
    update_tile_map(mapping)

if __name__ == "__main__":
    main()
