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

# 显式定义的区域-地形映射表
# Key: 区域ID (int), Value: {"t": tile_name, "type": "tile" | "sect" | "city"}
REGION_TILE_MAP = {
    # --- 城市区域 (City Regions) - 使用 ID ---
    301: {"t": "city_301", "type": "city"},  # 青云城
    302: {"t": "city_302", "type": "city"},  # 沙月城
    303: {"t": "city_303", "type": "city"},  # 翠林城
    304: {"t": "city_304", "type": "city"},  # 沧澜城
    305: {"t": "city_305", "type": "city"},  # 揽月城
    
    # --- 洞府遗迹 (Cultivate Regions) - 使用 sub_type ---
    201: {"t": "cave", "type": "tile"},  # 太白金府
    202: {"t": "cave", "type": "tile"},  # 青木洞天
    203: {"t": "cave", "type": "tile"},  # 玄水秘境
    204: {"t": "cave", "type": "tile"},  # 离火洞府
    205: {"t": "cave", "type": "tile"},  # 厚土玄宫
    206: {"t": "ruin", "type": "tile"},  # 古越遗迹
    207: {"t": "ruin", "type": "tile"},  # 沧海遗迹
}

# 普通区域名称映射（用于后备查找）
NORMAL_REGION_NAME_MAP = {
    "平原地带": "plain",
    "西域流沙": "desert",
    "南疆蛮荒": "rainforest",
    "极北冰原": "glacier",
    "无边碧海": "sea",
    "天河奔流": "water",
    "青峰山脉": "mountain",
    "万丈雪峰": "snow_mountain",
    "碧野千里": "grassland",
    "青云林海": "forest",
    "炎狱火山": "volcano",
    "沃土良田": "farm",
    "幽冥毒泽": "swamp",
    "十万大山": "mountain",
    "紫竹幽境": "bamboo",
    "凛霜荒原": "tundra",
    "碎星戈壁": "gobi",
    "蓬莱遗岛": "island",
}

def get_default_tile(region_id, name, type_tag, sect_id=None, sub_type=None):
    """根据区域ID和类型查找默认 Tile
    
    Args:
        region_id: 区域ID
        name: 区域名称（用于后备查找）
        type_tag: 区域类型 (normal/sect/city/cultivate)
        sect_id: 宗门ID（仅 sect 类型）
        sub_type: 子类型（仅 cultivate 类型：cave/ruin）
    """
    
    # 1. 优先使用 ID 查表
    if region_id in REGION_TILE_MAP:
        return REGION_TILE_MAP[region_id]
    
    # 2. 宗门：使用 sect_id 生成 tile 名称
    if type_tag == 'sect' and sect_id is not None:
        return {"t": f"sect_{sect_id}", "type": "sect"}
    
    # 3. 城市：使用 region_id 生成 tile 名称
    if type_tag == 'city':
        return {"t": f"city_{region_id}", "type": "city"}
    
    # 4. 修炼区域：使用 sub_type
    if type_tag == 'cultivate':
        if sub_type in ['cave', 'ruin']:
            return {"t": sub_type, "type": "tile"}
        # 兜底：根据名称推断
        if '遗迹' in name:
            return {"t": "ruin", "type": "tile"}
        return {"t": "cave", "type": "tile"}
    
    # 5. 普通区域：尝试名称映射
    if type_tag == 'normal' and name in NORMAL_REGION_NAME_MAP:
        tile_name = NORMAL_REGION_NAME_MAP[name]
        return {"t": tile_name, "type": "tile"}
    
    # 默认
    return {"t": "plain", "type": "tile"}

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
                    bind_info = get_default_tile(r_id, name, type_tag, sect_id=sect_id, sub_type=sub_type)

                    regions.append({
                        "id": r_id,
                        "name": name,
                        "type": type_tag,
                        "color": color,
                        "bindTile": bind_info["t"],
                        "bindTileType": bind_info["type"]
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

    # 3. 尝试读取现有的地图数据
    saved_map = load_map_data()

    return jsonify({
        "width": MAP_WIDTH,
        "height": MAP_HEIGHT,
        "tiles": tiles,
        "sectTiles": sect_tiles,
        "cityTiles": city_tiles,
        "cityTilesMap": city_tiles_map,
        "regions": regions,
        "savedMap": saved_map
    })

@app.route('/api/save', methods=['POST'])
def save_map():
    data = request.json
    grid = data.get('grid', []) # list of {x, y, t, r}

    tile_csv_path = os.path.join(OUTPUT_DIR, "tile_map.csv")
    region_csv_path = os.path.join(OUTPUT_DIR, "region_map.csv")

    try:
        # 初始化二维数组 (Matrix)
        # MAP_HEIGHT 行, MAP_WIDTH 列
        tile_matrix = [["plain" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        region_matrix = [[-1 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

        # 填充数据
        for cell in grid:
            x, y = cell['x'], cell['y']
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                tile_matrix[y][x] = cell['t']
                if cell.get('r') is not None:
                    region_matrix[y][x] = cell['r']

        # 保存 Tile Map (矩阵形式)
        with open(tile_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(tile_matrix)

        # 保存 Region Map (矩阵形式)
        with open(region_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(region_matrix)
        
        return jsonify({"status": "success", "message": "Map saved successfully (Matrix Format)"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def load_map_data():
    """读取矩阵格式 CSV 并重建 Grid 状态"""
    tile_csv_path = os.path.join(OUTPUT_DIR, "tile_map.csv")
    region_csv_path = os.path.join(OUTPUT_DIR, "region_map.csv")
    
    loaded_data = {} # key: "x,y", value: {t: ..., r: ...}

    # 读取 Tile Matrix
    if os.path.exists(tile_csv_path):
        with open(tile_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for y, row in enumerate(reader):
                if y >= MAP_HEIGHT: break
                for x, val in enumerate(row):
                    if x >= MAP_WIDTH: break
                    key = f"{x},{y}"
                    loaded_data[key] = {"t": val}

    # 读取 Region Matrix
    if os.path.exists(region_csv_path):
        with open(region_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for y, row in enumerate(reader):
                if y >= MAP_HEIGHT: break
                for x, val in enumerate(row):
                    if x >= MAP_WIDTH: break
                    try:
                        rid = int(val)
                        if rid != -1:
                            key = f"{x},{y}"
                            if key not in loaded_data:
                                loaded_data[key] = {"t": "plain"} # 默认
                            loaded_data[key]["r"] = rid
                    except ValueError:
                        continue
    
    return loaded_data

if __name__ == '__main__':
    print(f"Starting Map Creator at http://127.0.0.1:5000")
    print(f"Assets Dir: {ASSETS_DIR}")
    app.run(debug=True, port=5000)