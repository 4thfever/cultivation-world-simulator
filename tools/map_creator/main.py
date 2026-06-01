import os
import csv
import json
import glob
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__)

# --- 配置路径 ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CONFIG_DIR = os.path.join(BASE_DIR, "static", "game_configs")
OUTPUT_DIR = os.path.dirname(__file__)
DEFAULT_MAP_ID = "classic"
MAPS_DIR = os.path.join(CONFIG_DIR, "maps")
REGION_TILE_PATH = os.path.join(CONFIG_DIR, "region_tile.csv")

# 地图尺寸
MAP_WIDTH = 70
MAP_HEIGHT = 50

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tiles/<path:filename>')
def serve_tile_image(filename):
    return send_from_directory(os.path.join(ASSETS_DIR, "tiles"), filename)

@app.route('/sects/<path:filename>')
def serve_sect_image(filename):
    return send_from_directory(os.path.join(ASSETS_DIR, "sects"), filename)

@app.route('/cities/<path:filename>')
def serve_city_image(filename):
    return send_from_directory(os.path.join(ASSETS_DIR, "cities"), filename)

def load_region_tile_bindings():
    bindings = {}
    if not os.path.exists(REGION_TILE_PATH):
        return bindings
    with open(REGION_TILE_PATH, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    for row in rows[1:] if rows and str(rows[0].get('region_id', '')).startswith('区域') else rows:
        try:
            rid = int(row.get('region_id') or 0)
        except ValueError:
            continue
        if rid <= 0:
            continue
        bindings[rid] = {
            "tile": (row.get('tile') or 'plain').strip(),
            "landmarkAsset": (row.get('landmark_asset') or '').strip() or None,
        }
    return bindings


def get_default_tile(region_id, type_tag, sect_id=None, sub_type=None, bindings=None):
    bindings = bindings or {}
    if region_id in bindings:
        info = bindings[region_id]
        asset = info.get("landmarkAsset")
        if asset and asset.startswith("city_"):
            return {"t": info["tile"], "type": "city", "landmarkAsset": asset}
        if asset and asset.startswith("sect_"):
            return {"t": info["tile"], "type": "sect", "landmarkAsset": asset}
        return {"t": info["tile"], "type": "tile", "landmarkAsset": asset}
    if type_tag == 'sect' and sect_id is not None:
        return {"t": "mountain", "type": "sect", "landmarkAsset": f"sect_{sect_id}"}
    if type_tag == 'city':
        return {"t": "city", "type": "city", "landmarkAsset": f"city_{region_id}"}
    if type_tag == 'cultivate':
        asset = sub_type if sub_type in ['cave', 'ruin'] else 'cave'
        return {"t": "mountain", "type": "tile", "landmarkAsset": asset}
    raise ValueError(f"Missing tile binding for region {region_id}")

@app.route('/api/init')
def init_data():
    """初始化数据：读取Tiles列表和Region配置"""
    
    # 1. 获取所有 Tile 图片名称
    tile_files = glob.glob(os.path.join(ASSETS_DIR, "tiles", "*.png"))
    # 过滤切片 (name_0.png)
    tiles = [os.path.splitext(os.path.basename(f))[0] for f in tile_files if not os.path.splitext(os.path.basename(f))[0][-2:] in ['_0', '_1', '_2', '_3']]
    tiles.sort()

    # 2. 获取所有 Sect 图片名称 (sect_1, sect_2, ...)
    sect_files = glob.glob(os.path.join(ASSETS_DIR, "sects", "*.png"))
    sect_tiles_set = set()
    for f in sect_files:
        name = os.path.splitext(os.path.basename(f))[0]
        # Extract base name from slices: sect_1_0 -> sect_1
        if name.startswith('sect_') and '_' in name[5:]:
            # Split by underscore and take first two parts
            parts = name.split('_')
            if len(parts) >= 3:  # sect_1_0
                base_name = f"{parts[0]}_{parts[1]}"  # sect_1
                sect_tiles_set.add(base_name)
    sect_tiles = sorted(list(sect_tiles_set))

    # 3. 获取所有 City 图片名称 (city_301, city_302, ...)
    city_files = glob.glob(os.path.join(ASSETS_DIR, "cities", "*.*"))
    # 过滤非图片
    city_files = [f for f in city_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    city_tiles_map = {} # base_name -> extension (for first slice)
    city_tiles_set = set()
    for f in city_files:
        basename = os.path.basename(f)
        name = os.path.splitext(basename)[0]
        ext = os.path.splitext(basename)[1]
        
        # Extract base name from slices: city_301_0 -> city_301
        if name.startswith('city_') and '_' in name[5:]:
            parts = name.split('_')
            if len(parts) >= 3:  # city_301_0
                base_name = f"{parts[0]}_{parts[1]}"  # city_301
                city_tiles_set.add(base_name)
                # Store extension for the first slice
                if base_name not in city_tiles_map:
                    city_tiles_map[base_name] = f"{base_name}_0{ext}"
    
    city_tiles = sorted(list(city_tiles_set))

    # 4. 读取 sect.csv 建立 sect_id -> sect_name 映射
    sect_id_to_name = {}
    sect_csv_path = os.path.join(CONFIG_DIR, "sect.csv")
    if os.path.exists(sect_csv_path):
        with open(sect_csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
            data_rows = rows[2:] if len(rows) > 2 else []
            for row in data_rows:
                if len(row) >= 2:
                    try:
                        sid = int(row[0])
                        sname = row[1]
                        sect_id_to_name[sid] = sname
                    except ValueError:
                        continue

    region_tile_bindings = load_region_tile_bindings()

    # 5. 读取 Region 配置
    regions = []
    
    def parse_csv(filename, id_col, name_col, type_tag, sect_id_col=None, sub_type_col=None):
        path = os.path.join(CONFIG_DIR, filename)
        if not os.path.exists(path):
            print(f"Warning: {path} not found")
            return
        
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # 跳过前两行 (header 和 description)
            data_rows = rows[2:] if len(rows) > 2 else []
            
            for row in data_rows:
                if len(row) <= max(id_col, name_col): continue
                try:
                    r_id = int(row[id_col])
                    name = row[name_col]
                    # 简单的 hash 颜色生成
                    color_hash = hash(f"{type_tag}_{r_id}") & 0xFFFFFF
                    color = f"#{color_hash:06x}"
                    
                    # 获取 sect_id (用于宗门)
                    sect_id = None
                    if type_tag == 'sect' and sect_id_col is not None and len(row) > sect_id_col:
                        try:
                            sect_id = int(row[sect_id_col])
                        except ValueError:
                            pass
                    
                    # 获取 sub_type (用于修炼区域)
                    sub_type = None
                    if type_tag == 'cultivate' and sub_type_col is not None and len(row) > sub_type_col:
                        sub_type = row[sub_type_col].strip()
                    
                    # 计算默认绑定 Tile
                    bind_info = get_default_tile(r_id, type_tag, sect_id=sect_id, sub_type=sub_type, bindings=region_tile_bindings)

                    regions.append({
                        "id": r_id,
                        "name": name,
                        "type": type_tag,
                        "color": color,
                        "bindTile": bind_info["t"],
                        "bindTileType": bind_info["type"],
                        "landmarkAsset": bind_info.get("landmarkAsset"),
                    })
                except ValueError:
                    continue


    # 读取四种配置
    # normal_region.csv: id=0, name=1
    parse_csv("normal_region.csv", 0, 1, "normal")
    # sect_region.csv: id=0, name=1, sect_id=3
    parse_csv("sect_region.csv", 0, 1, "sect", sect_id_col=3)
    # cultivate_region.csv: id=0, name=1, sub_type=3 (在 desc 后面)
    parse_csv("cultivate_region.csv", 0, 1, "cultivate", sub_type_col=3)
    # city_region.csv: id=0, name=1
    parse_csv("city_region.csv", 0, 1, "city")
    
    # 排序优先级：normal > sect > cultivate > city > 其他
    def sort_priority(r):
        if r['type'] == 'normal': return 0
        if r['type'] == 'sect': return 1
        if r['type'] == 'cultivate': return 2
        if r['type'] == 'city': return 3
        return 4
        
    regions.sort(key=lambda x: (sort_priority(x), x['id']))

    saved_map = load_map_data()

    return jsonify({
        "width": saved_map["width"],
        "height": saved_map["height"],
        "wildernessTile": saved_map["wildernessTile"],
        "tiles": tiles,
        "sectTiles": sect_tiles,
        "cityTiles": city_tiles,
        "cityTilesMap": city_tiles_map,
        "regions": regions,
        "savedMap": saved_map["cells"],
        "landmarks": saved_map["landmarks"],
    })

@app.route('/api/save', methods=['POST'])
def save_map():
    data = request.json
    grid = data.get('grid', [])
    landmarks = data.get('landmarks', {})
    map_id = data.get('mapId') or DEFAULT_MAP_ID
    output_dir = os.path.join(MAPS_DIR, map_id)
    os.makedirs(output_dir, exist_ok=True)
    map_json_path = os.path.join(output_dir, "map.json")

    try:
        region_matrix = [[-1 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

        for cell in grid:
            x, y = cell['x'], cell['y']
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                if cell.get('r') is not None:
                    region_matrix[y][x] = cell['r']

        payload = {
            "schema_version": 2,
            "id": map_id,
            "version": 2,
            "width": MAP_WIDTH,
            "height": MAP_HEIGHT,
            "wilderness_tile": data.get("wildernessTile") or "plain",
            "region_rows": region_matrix,
            "landmarks": landmarks,
        }
        with open(map_json_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        
        return jsonify({"status": "success", "message": "Map saved successfully (region-first map.json)"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def load_map_data():
    """读取 region-first map.json 并重建 Grid 状态"""
    map_json_path = os.path.join(MAPS_DIR, DEFAULT_MAP_ID, "map.json")
    
    loaded_data = {} # key: "x,y", value: {t: ..., r: ...}
    landmarks = {}
    wilderness_tile = "plain"

    if os.path.exists(map_json_path):
        with open(map_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        wilderness_tile = data.get("wilderness_tile") or "plain"
        width = data.get("width", MAP_WIDTH)
        height = data.get("height", MAP_HEIGHT)
        region_rows = data.get("region_rows", [])
        bindings = load_region_tile_bindings()
        for y, row in enumerate(region_rows):
            for x, rid in enumerate(row):
                key = f"{x},{y}"
                tile = wilderness_tile
                if rid != -1 and rid in bindings:
                    tile = bindings[rid]["tile"]
                loaded_data[key] = {"t": tile, "r": rid if rid != -1 else None}
        landmarks = data.get("landmarks", {})

    return {
        "cells": loaded_data,
        "landmarks": landmarks,
        "wildernessTile": wilderness_tile,
        "width": width if os.path.exists(map_json_path) else MAP_WIDTH,
        "height": height if os.path.exists(map_json_path) else MAP_HEIGHT,
    }

if __name__ == '__main__':
    print(f"Starting Map Creator at http://127.0.0.1:5000")
    print(f"Assets Dir: {ASSETS_DIR}")
    app.run(debug=True, port=5000)
