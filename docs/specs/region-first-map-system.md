# Region-First 地图系统重构 Spec

本文档记录下一轮地图与地图工具重构方案。

当前已经落地的地图第一版是“官方地图预设 + 地图快照”，详见 `docs/specs/official-map-presets.md`。第一版仍使用 `tile_map.csv` 与 `region_map.csv` 两张平行矩阵维护地图。下一轮重构的目标，是把地图语义收束为 **region-first**：地图首先由区域归属决定，地块图像由 region 的视觉绑定推导，而不是让 tile 矩阵与 region 矩阵各自成为真源。

## 背景问题

当前地图维护方式存在几个结构性问题：

1. `tile_map.csv` 与 `region_map.csv` 必须保持同尺寸、同坐标语义，维护时需要额外对齐。
2. 实际编辑地图时，经常会出现 region 归属已经变化，但 tile 图像没有同步变化，或反过来。
3. “一个 region 对应一种地图图像”的设计意图没有被数据结构表达出来。
4. 地图设计工具内部其实已经在用 `{ x, y, t, r }` 这样的单元格模型，但保存时又拆回两张 CSV。
5. 存档快照沿用了双矩阵结构，继续放大了源格式的不优雅。

本次重构要解决的是地图源格式和维护方式的问题，不是重做地理模拟。

## 核心结论

地图以 region 为主语义：

1. 一个 region 在地图上可以占据多个格子。
2. 一个 region 当前只允许绑定一种 tile 图像。
3. 不同 region 可以犬牙交错，形成真实地图边界感。
4. 无 region 的格子就是荒野。
5. 地图上只有 region 可以点击，tile 不作为独立可点击对象。
6. 城市、宗门、洞府、遗迹等大型图像的位置由 landmark 控制；未配置时回退到 region center。

## 目标

本次重构目标：

1. 取消官方地图源文件中的 `tile_map.csv + region_map.csv` 平行真源。
2. 新增单一地图源格式，主矩阵只保存 region 归属。
3. 建立 region 到 tile 图像的统一解析机制。
4. 将地图设计工具改为读写新格式。
5. 将地图快照升级为 region-first 的 schema v2。
6. 保持运行时 `Map` / `Tile` / `Region` 主模型尽量稳定。
7. 保持前端主地图展示第一阶段尽量稳定，后续再按需升级 DTO。
8. 补充校验、迁移、预览与测试，降低地图维护风险。

非目标：

1. 不做随机地图生成。
2. 不做玩家地图编辑器。
3. 不引入道路、河网、高度、气候、文化、经济网络等复杂地理系统。
4. 不允许 tile 成为可点击交互对象。
5. 不实现运行时灾害、战争等造成的局部地形覆盖。
6. 不追求旧地图 CSV 长期兼容。开发阶段允许一次性迁移后删除旧双 CSV 主路径。

## 设计原则

### 1. Region 是地图语义真源

地图源文件中的主矩阵保存 `region_id`。

同一个格子属于哪个 region，是地图设计层最重要的信息。该格子的 tile 图像由 region 绑定推导，不再由独立 tile 矩阵维护。

示意：

```json
{
  "region_rows": [
    [102, 102, 108, -1],
    [102, 108, 108, -1]
  ]
}
```

其中 `-1` 表示荒野。

### 2. 一个 Region 只有一个 Tile 图像

一个 region 当前只能绑定一个地图 tile 图像。

例如：

1. `沃土良田` 对应 `farm`。
2. `西域流沙` 对应 `desert`。
3. `青云林海` 对应 `forest`。
4. 城市 region 对应城市大型 landmark 图像，但其底层 tile 仍由统一规则推导。

这条规则应由校验器保证。地图设计工具不应允许同一个 region 的不同格子手动涂成不同 tile。

### 3. 荒野是无 Region 格子

无 region 的格子统一视为荒野。

第一版荒野使用统一 tile：

```json
"wilderness_tile": "plain"
```

不为荒野维护复杂地貌层。也就是说，本轮不引入 `base_tile_rows`。如果未来需要海域、无人雪山、不可进入地貌等“非 region 地貌”，应先重新评估荒野是否仍然只是缺省区域，而不是在本轮提前加入双层地图。

### 4. Landmark 与 Region 范围分离

region 的范围表示“这个区域占据哪些格子”。

城市、宗门、洞府、遗迹的大型图像表示“这个区域的视觉标记放在哪里”。这两个概念分离。

地图源文件允许显式配置 landmark：

```json
{
  "landmarks": {
    "301": {
      "x": 20,
      "y": 15,
      "asset": "city_301"
    },
    "204": {
      "x": 62,
      "y": 4,
      "asset": "cave"
    }
  }
}
```

规则：

1. landmark 坐标必须在地图范围内。
2. landmark 锚点格子应属于对应 region。
3. 2x2 landmark 必须完整落在地图范围内。
4. 2x2 landmark 覆盖范围原则上应尽量落在对应 region 内；若允许少量跨边界，必须由校验器给 warning，而不是静默通过。
5. 未配置 landmark 时，使用 region center 作为 fallback。

### 5. 犬牙交错可以，碎片化要限制

region 之间允许犬牙交错，边界不必规整。

但 region 不应碎成难以阅读的满天星。

建议校验规则：

1. `normal` region 允许少量多块，用于表现山脉支脉、林海边缘、农田嵌入等自然形态。
2. `city` region 必须连续。
3. `sect` region 必须连续。
4. `cultivate` region 必须连续，除非后续明确设计某类秘境可以多入口。
5. `normal` region 的连通块数量设置上限，例如 8；超出报错或至少强 warning。
6. 所有 region 必须至少有一个格子。

### 6. 前端只交互 Region

前端地图交互对象是 region，不是 tile。

本轮约束：

1. tile 不可点击。
2. 地图标签点击仍然选择 region。
3. 后续如果支持点击地图格子，也应解析为“点击该格子的 region”；若格子是荒野，则不触发 region detail。
4. 前端不展示 tile 详情面板。

## 数据格式

### 地图预设源文件

每个官方地图预设目录改为：

```text
static/game_configs/maps/
  classic/
    meta.json
    map.json
  mountain_frontier/
    meta.json
    map.json
  island_seas/
    meta.json
    map.json
```

`map.json` 建议格式：

```json
{
  "schema_version": 2,
  "id": "classic",
  "version": 2,
  "width": 84,
  "height": 60,
  "wilderness_tile": "plain",
  "region_rows": [
    [102, 102, 108, -1],
    [102, 108, 108, -1]
  ],
  "landmarks": {
    "301": {
      "x": 20,
      "y": 15,
      "asset": "city_301"
    }
  }
}
```

字段说明：

1. `schema_version`：地图源格式版本，本轮为 `2`。
2. `id`：地图 ID，必须与目录名和 `meta.json.id` 一致。
3. `version`：官方地图预设版本，可随地图内容调整递增。
4. `width` / `height`：地图尺寸。
5. `wilderness_tile`：荒野格子使用的 tile，第一版默认为 `plain`。
6. `region_rows`：主矩阵，保存 region id；`-1` 表示荒野。
7. `landmarks`：可选，保存大型视觉标记位置。

不保存：

1. 不保存 `tile_rows`。
2. 不保存每格 tile。
3. 不保存 region 静态元数据。
4. 不保存未来 runtime overlay。

### Region Tile 绑定

region 到 tile 的绑定需要一个统一解析器，不由地图矩阵表达。

建议新增独立配置文件：

```text
static/game_configs/region_tile.csv
```

建议字段：

```csv
region_id,tile,landmark_asset
101,plain,
102,desert,
112,farm,
201,mountain,cave
206,mountain,ruin
301,city,city_301
401,mountain,sect_1
```

设计理由：

1. 不污染 `normal_region.csv` / `city_region.csv` / `cultivate_region.csv` / `sect_region.csv` 的玩法字段。
2. 视觉绑定集中维护，适合地图设计工具读取。
3. 允许特殊 region 显式覆盖默认规则。
4. 后续如果更换地图图像，不需要改 region 玩法配置。

解析优先级：

1. `region_tile.csv` 中有显式配置时，使用显式配置。
2. `city` region 未显式配置时，tile 使用 `city`，landmark 使用 `city_<region_id>`。
3. `sect` region 未显式配置时，tile 使用 `mountain`，landmark 使用 `sect_<sect_id>`。
4. `cultivate` region 未显式配置时，tile 使用 `mountain`，landmark 使用 `sub_type`，例如 `cave` / `ruin`。
5. `normal` region 必须显式配置 tile；缺失时报错。
6. 荒野使用 `wilderness_tile`。

注意：`tile` 是底层地貌图像；`landmark_asset` 是 2x2 或特殊覆盖图像。两者不混为同一个字段。

## 后端设计

### 新增地图源模块

建议新增：

```text
src/run/map_source.py
```

职责：

1. 读取 `map.json`。
2. 校验 schema、尺寸和 region 矩阵。
3. 读取 `region_tile.csv`。
4. 根据 region id 解析每个格子的 tile。
5. 根据 `landmarks` 或 fallback center 生成 region summary 所需视觉标记。
6. 为现有 `build_map_from_rows(...)` 提供兼容输入，或新增 `build_map_from_region_rows(...)`。

核心类型示意：

```python
@dataclass(frozen=True)
class MapSource:
    map_id: str
    version: int
    width: int
    height: int
    wilderness_tile: str
    region_rows: list[list[int]]
    landmarks: dict[int, MapLandmark]

@dataclass(frozen=True)
class RegionTileBinding:
    region_id: int
    tile: str
    landmark_asset: str | None = None

@dataclass(frozen=True)
class MapLandmark:
    x: int
    y: int
    asset: str
```

### 加载流程

`load_cultivation_world_map(map_id)` 改为：

1. 通过 `map_presets` 找到 preset 目录。
2. 读取 `map.json`。
3. 聚合 `region_rows` 得到 `region_coords`。
4. 读取 region 元数据 CSV 创建 `Region` 对象。
5. 根据 region tile binding 创建每个 `Tile`。
6. 将 `Tile.region` 绑定到对应 `Region`。
7. 写入 `Map.region_cors`。
8. 写入 landmark 信息到 `Map` 或额外结构。
9. 刷新 `update_sect_regions()`。

运行时仍保持：

1. `Tile.type` 是最终可用于底图渲染的 tile。
2. `Tile.region` 是该格所属 region 或 `None`。
3. `Map.regions` 是 region id 到 region 对象的索引。
4. `Map.region_cors` 是 region id 到坐标列表的索引。

### Map 对象扩展

建议在 `Map` 上新增：

```python
self.landmarks: dict[int, MapLandmark] = {}
```

或者使用普通 dict 保存 JSON 友好的结构：

```python
self.landmarks: dict[int, dict[str, object]] = {}
```

第一版建议用普通 dict，减少序列化和测试成本。

### 地图查询接口

第一阶段 `/api/v1/query/world/map` 可以保持现有 DTO：

```json
{
  "data": [["PLAIN", "FARM"]],
  "regions": [
    {
      "id": 112,
      "name": "沃土良田",
      "type": "normal",
      "x": 10,
      "y": 20
    }
  ]
}
```

但 region summary 中的大型图像坐标应优先使用 landmark，而不是无条件使用 center。

后续如需点击任意格子选择 region，可新增：

```json
{
  "region_ids": [[112, 112, null]]
}
```

不过本轮不是必须，因为当前交互仍以 region 标签为主。

## 存档快照

地图快照升级到 schema v2。

建议结构：

```json
{
  "schema_version": 2,
  "preset_id": "classic",
  "preset_version": 2,
  "width": 84,
  "height": 60,
  "wilderness_tile": "plain",
  "region_rows": [
    [102, 102, 108, -1],
    [102, 108, 108, -1]
  ],
  "landmarks": {
    "301": {
      "x": 20,
      "y": 15,
      "asset": "city_301"
    }
  },
  "region_tile_overrides": {}
}
```

说明：

1. 存档保存本局真实 region 归属矩阵。
2. 存档保存本局真实 landmark 位置。
3. 存档不保存完整 region 静态元数据。
4. `region_tile_overrides` 预留给未来“整个 region 换图像”的 runtime 变化；本轮始终为空。
5. 不预留每格 tile overlay，直到未来玩法明确需要。

开发阶段不要求长期兼容旧 v1 snapshot。若实现时保留 v1 读取只需很小成本，可以将 v1 的 `region_rows` 直接转为 v2，再按 region tile binding 推导 tile。

## 地图设计工具

`tools/map_creator` 改为 region-first 编辑器。

### 编辑体验

主模式：

1. 选择 region。
2. 在地图上绘制 region 归属。
3. tile 图像自动由 region tile binding 决定。
4. 选择荒野橡皮擦时，将格子 region 设置为 `-1`，显示 `wilderness_tile`。

辅助能力：

1. region 列表展示绑定 tile 预览。
2. city / sect / cultivate region 展示 landmark asset 预览。
3. 支持拖动 landmark。
4. 未设置 landmark 时显示自动 center fallback。
5. 保存时写 `map.json`。
6. 可提供一次性导出旧 CSV 的调试功能，但不作为主路径。

### 工具 API

`/api/init` 返回：

```json
{
  "width": 84,
  "height": 60,
  "wilderness_tile": "plain",
  "regionRows": [[102, 102, -1]],
  "regions": [
    {
      "id": 112,
      "name": "沃土良田",
      "type": "normal",
      "tile": "farm",
      "landmarkAsset": null
    }
  ],
  "landmarks": {
    "301": {
      "x": 20,
      "y": 15,
      "asset": "city_301"
    }
  }
}
```

`/api/save` 接收并保存：

```json
{
  "regionRows": [[102, 102, -1]],
  "landmarks": {
    "301": {
      "x": 20,
      "y": 15,
      "asset": "city_301"
    }
  }
}
```

## 校验规则

`tools/map_presets/validate_presets.py` 改为校验 `map.json`。

必须校验：

1. `meta.json.id`、目录名、`map.json.id` 一致。
2. `schema_version == 2`。
3. `width` / `height` 与 `region_rows` 尺寸一致。
4. `wilderness_tile` 是合法 `TileType`。
5. 所有 region id 存在于 region 元数据配置。
6. 所有官方地图使用同一批 region id。
7. 所有 region 至少有一个格子。
8. `normal` region 有 tile binding。
9. tile binding 中的 tile 是合法 `TileType`。
10. landmark asset 对应的资源存在，或符合现有资源命名规则。
11. landmark 坐标在地图范围内。
12. landmark 锚点属于对应 region。
13. 2x2 landmark 不越界。
14. city / sect / cultivate region 连续。
15. normal region 连通块数量不超过阈值。

建议 warning：

1. landmark 2x2 覆盖范围没有全部落在对应 region 内。
2. region 面积极小，可能导致标签和 landmark 不稳定。
3. region center fallback 与视觉主体偏离过大。

## 前端影响

第一阶段尽量不重做前端地图渲染。

保持：

1. `MapMatrix = string[][]`。
2. `RegionSummary` 仍包含 `x` / `y`。
3. `MapLayer` 仍渲染底图和 region 标签。
4. tile 不可点击。

调整：

1. 后端 region summary 的 `x` / `y` 对大型 region 应来自 landmark 或 fallback center。
2. 如果后续前端需要更精准边界、hover、点击格子选 region，再扩展 DTO，新增 `region_ids` 或 `cells`。

不做：

1. 不新增 tile detail。
2. 不让 tile 成为交互对象。
3. 不在前端硬编码 region 到 tile 的中文映射。

## 迁移计划

建议实施顺序：

1. 新增 `region_tile.csv`，补齐所有现有 region 的 tile / landmark 绑定。
2. 新增迁移脚本，将每个 preset 的旧 `region_map.csv` 转为 `map.json`。
3. 使用旧 `tile_map.csv` 校验 region tile binding 是否与当前视觉结果一致，生成差异报告。
4. 人工确认差异后，删除或弃用旧 `tile_map.csv` / `region_map.csv` 主路径。
5. 改 `load_cultivation_world_map()` 读取 `map.json`。
6. 改 `serialize_map_snapshot()` 与 `load_map_from_snapshot()` 使用 schema v2。
7. 改地图设计工具读写 `map.json`。
8. 改预览和校验工具。
9. 跑地图、存档、API、前端类型检查。

## 测试计划

后端测试：

1. `region_tile.csv` 覆盖所有 region。
2. 三张官方地图 `map.json` 都能加载。
3. 三张官方地图尺寸一致。
4. 三张官方地图 region 覆盖集合一致。
5. 荒野格子加载为 `wilderness_tile` 且 `Tile.region is None`。
6. region 格子加载为绑定 tile 且 `Tile.region.id` 正确。
7. city / sect / cultivate landmark 优先于 center。
8. 未配置 landmark 时 fallback center。
9. snapshot v2 round trip 保持 region 归属、荒野、landmark。
10. `/api/v1/query/world/map` 返回可渲染 tile 类型，不暴露不可渲染内部类型。
11. 校验器能发现非法 region、非法 tile、缺失 binding、landmark 越界、碎片化超限。

工具测试或脚本验证：

1. 旧 CSV 到 `map.json` 迁移后 region 覆盖不丢失。
2. 使用 binding 推导出的 tile 与旧 `tile_map.csv` 差异可报告。
3. 预览图能生成并显示 region 边界、荒野和 landmark。

前端验证：

1. `cd web && npm run type-check`。
2. 三张地图能正常加载和渲染。
3. region 标签可点击。
4. tile 不触发独立点击行为。
5. city / sect / cultivate 大型图像显示在 landmark 位置。

## 后续留白

未来如果要加入地图演化，应重新设计以下内容：

1. 整个 region 更换 tile 图像，例如城市废墟化、森林焚毁。
2. 局部格子的 runtime overlay。
3. 无 region 地貌是否从单一荒野升级为 base terrain layer。
4. 道路、河流、边界、海岸线等独立地理图层。
5. 外接控制 API 修改 region 归属或 landmark。

这些都不属于本轮实现范围。当前 spec 的核心是先把地图源格式从双矩阵收束为 region-first 单真源。
