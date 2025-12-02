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
MAP_WIDTH = 100
MAP_HEIGHT = 70

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tiles/<path:filename>')
def serve_tile_image(filename):
    return send_from_directory(os.path.join(ASSETS_DIR, "tiles"), filename)

@app.route('/sects/<path:filename>')
def serve_sect_image(filename):
    return send_from_directory(os.path.join(ASSETS_DIR, "sects"), filename)

# 显式定义的区域-地形映射表
# Key: 区域名称, Value: {"t": tile_name, "type": "tile" | "sect"}
REGION_TILE_MAP = {
    # --- 普通区域 (Normal Regions) ---
    "平原地带": {"t": "plain", "type": "tile"},
    "西域流沙": {"t": "desert", "type": "tile"},
    "南疆蛮荒": {"t": "rainforest", "type": "tile"},
    "极北冰原": {"t": "glacier", "type": "tile"},
    "无边碧海": {"t": "sea", "type": "tile"},
    "天河奔流": {"t": "water", "type": "tile"},
    "青峰山脉": {"t": "mountain", "type": "tile"},
    "万丈雪峰": {"t": "snow_mountain", "type": "tile"},
    "碧野千里": {"t": "grassland", "type": "tile"},
    "青云林海": {"t": "forest", "type": "tile"},
    "炎狱火山": {"t": "volcano", "type": "tile"},
    "沃土良田": {"t": "farm", "type": "tile"},
    "幽冥毒泽": {"t": "swamp", "type": "tile"},
    "十万大山": {"t": "mountain", "type": "tile"},
    "紫竹幽境": {"t": "bamboo", "type": "tile"},
    "凛霜荒原": {"t": "tundra", "type": "tile"},
    "碎星戈壁": {"t": "gobi", "type": "tile"},
    "蓬莱遗岛": {"t": "island", "type": "tile"},
    
    # --- 城市区域 (City Regions) ---
    "青云城": {"t": "city", "type": "tile"},
    "沙月城": {"t": "city", "type": "tile"},
    "翠林城": {"t": "city", "type": "tile"},
    
    # --- 洞府遗迹 (Cultivate Regions) ---
    "太白金府": {"t": "cave", "type": "tile"},
    "青木洞天": {"t": "cave", "type": "tile"},
    "玄水秘境": {"t": "cave", "type": "tile"},
    "离火洞府": {"t": "cave", "type": "tile"},
    "厚土玄宫": {"t": "cave", "type": "tile"},
    "古越遗迹": {"t": "ruins", "type": "tile"},
    "沧海遗迹": {"t": "ruins", "type": "tile"},
}

def get_default_tile(name, type_tag, all_tiles, all_sect_tiles):
    """根据区域名称和类型查找默认 Tile"""
    
    # 1. 查表 (精确匹配)
    if name in REGION_TILE_MAP:
        return REGION_TILE_MAP[name]
    
    # 2. 宗门：尝试匹配 Sect 图片
    if type_tag == 'sect':
        # 尝试直接匹配宗门名
        if name in all_sect_tiles:
            return {"t": name, "type": "sect"}
        # 尝试部分匹配
        for t in all_sect_tiles:
            if t in name or name in t:
                return {"t": t, "type": "sect"}
        return {"t": "mountain", "type": "tile"} # 默认建在山上

    # 3. 城市默认
    if type_tag == 'city':
        return {"t": "city", "type": "tile"}
        
    # 4. 包含特定关键词的兜底逻辑 (针对未在表中的新区域)
    name_lower = name.lower()
    if '洞' in name_lower or '府' in name_lower or '秘境' in name_lower: 
        return {"t": "cave", "type": "tile"}
    if '遗迹' in name_lower:
        return {"t": "ruins", "type": "tile"}

    # 默认
    return {"t": "plain", "type": "tile"}

@app.route('/api/init')
def init_data():
    """初始化数据：读取Tiles列表和Region配置"""
    
    # 1. 获取所有 Tile 图片名称
    tile_files = glob.glob(os.path.join(ASSETS_DIR, "tiles", "*.png"))
    tiles = [os.path.splitext(os.path.basename(f))[0] for f in tile_files]
    tiles.sort()

    # 2. 获取所有 Sect 图片名称
    sect_files = glob.glob(os.path.join(ASSETS_DIR, "sects", "*.png"))
    sect_tiles = [os.path.splitext(os.path.basename(f))[0] for f in sect_files]
    sect_tiles.sort()

    # 3. 读取 Region 配置
    regions = []
    
    def parse_csv(filename, id_col, name_col, type_tag):
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
                    
                    # 计算默认绑定 Tile
                    bind_info = get_default_tile(name, type_tag, tiles, sect_tiles)

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
    # sect_region.csv: sect_id=0, sect_name=1
    parse_csv("sect_region.csv", 0, 1, "sect")
    # cultivate_region.csv: id=0, name=1
    parse_csv("cultivate_region.csv", 0, 1, "cultivate")
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