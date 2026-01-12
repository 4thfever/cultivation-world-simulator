# Map Creator ID Migration

## 修改说明

已将地图编辑器从基于名称的配置迁移到基于 ID 的配置，以匹配主项目的修改。

### 主要修改

#### 1. 后端 (main.py)

**区域-地形映射表 (REGION_TILE_MAP)**
- 从名称映射改为 ID 映射
- 示例：
  ```python
  # 旧：
  "青云城": {"t": "青云城", "type": "city"}
  
  # 新：
  301: {"t": "city_301", "type": "city"}
  ```

**get_default_tile 函数**
- 新增参数：`sect_id`, `sub_type`
- 支持根据 ID 生成 tile 名称：
  - 宗门：`sect_{sect_id}` (如 `sect_1`)
  - 城市：`city_{region_id}` (如 `city_301`)
  - 修炼区域：根据 `sub_type` 返回 `cave` 或 `ruin`

**资源文件扫描**
- 宗门：从 `sect_1_0.png` 等切片提取基础名称 `sect_1`
- 城市：从 `city_301_0.png` 等切片提取基础名称 `city_301`

**CSV 解析**
- 新增 `sub_type_col` 参数，用于读取 `cultivate_region.csv` 的 `sub_type` 列

#### 2. 前端 (templates/index.html)

**预览图片显示**
- 添加 `getRegionPreviewSrc` 函数，根据区域类型动态生成预览图片路径
- 支持：
  - 宗门：`/sects/sect_1_0.png`
  - 城市：`/cities/city_301_0.png` (支持 jpg/png)
  - 修炼区域：`/tiles/cave_0.png` 或 `/tiles/ruin_0.png`

### 兼容性

**资源文件命名要求**：
- 宗门图片：`assets/sects/sect_{id}_{0-3}.png`
- 城市图片：`assets/cities/city_{id}_{0-3}.{png|jpg}`
- 修炼区域：`assets/tiles/{cave|ruin}_{0-3}.png`

**CSV 文件要求**：
- `sect_region.csv`: 必须包含 `sect_id` 列（第3列，索引为3）
- `cultivate_region.csv`: 必须包含 `sub_type` 列（第3列，索引为3）

### 使用方法

1. 确保资源文件已按新的命名规则重命名
2. 确保 CSV 文件包含必要的列
3. 运行地图编辑器：
   ```bash
   python tools/map_creator/main.py
   ```
4. 访问 http://127.0.0.1:5000

### 示例数据

**宗门区域**：
- ID: 401, sect_id: 1 → 绑定 tile: `sect_1`

**城市区域**：
- ID: 301, name: "青云城" → 绑定 tile: `city_301`

**修炼区域**：
- ID: 201, name: "太白金府", sub_type: "cave" → 绑定 tile: `cave`
- ID: 206, name: "古越遗迹", sub_type: "ruin" → 绑定 tile: `ruin`
