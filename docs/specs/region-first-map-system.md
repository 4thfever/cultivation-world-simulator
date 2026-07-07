# Region-First 地图系统 Spec

本文档记录当前已经落地的 region-first 地图系统。地图系统已经从早期 `tile_map.csv + region_map.csv` 双矩阵维护方式，收束为以 `static/game_configs/maps/<map_id>/map.json` 为官方地图真源的 schema v2。

## 当前结论

地图以 region 为主语义：

1. 一个 region 在地图上可以占据多个格子。
2. 一个 region 当前只允许绑定一种 tile 图像。
3. 不同 region 可以犬牙交错，形成更自然的地图边界。
4. `-1` 表示无 region，也就是荒野。
5. 荒野使用地图自己的 `wilderness_tile`，可以是 `plain`，也可以是 `sea` 等合法 tile。
6. 地图上只有 region 可以点击，tile 不作为独立交互对象。
7. 城市、宗门、洞府、遗迹等大型图像的位置由 `landmarks` 控制；未配置时回退到 region center。
8. 地图特有的 region 名称和描述差异通过 `region_overrides` 表达。

本系统只解决地图源格式、地图加载、快照和维护工具的一致性问题，不引入随机地图生成、玩家编辑器、道路河网、高度气候、战争灾害地貌覆盖等复杂地理系统。

## 代码地图

当前地图系统的主要入口：

1. `static/game_configs/maps/<map_id>/map.json`：官方地图预设真源。
2. `static/game_configs/maps/<map_id>/meta.json`：地图预设元数据。
3. `static/game_configs/region_tile.csv`：region 到底层 tile / landmark asset 的绑定。
4. `src/run/map_source.py`：读取、校验、序列化 map source，并从 region 矩阵推导 tile 矩阵。
5. `src/run/load_map.py`：把 `MapSource` 加载为运行时 `Map` / `Tile` / `Region` 对象。
6. `src/run/map_snapshot.py`：保存和读取存档中的地图快照 schema v2。
7. `src/classes/environment/map.py`：运行时地图对象，保存 `landmarks`、`wilderness_tile`、`region_overrides` 等地图级信息。
8. `src/server/services/game_queries.py`：对外查询地图和 region detail，读取运行时 region 信息。
9. `tools/map_creator/main.py`：region-first 地图设计工具，读写 `map.json`。
10. `tools/map_presets/validate_presets.py`：官方地图预设校验。
11. `tools/map_presets/render_preview.py`：生成本地预览图。
12. `tools/map_presets/export_frontend_previews.py`：导出前端使用的预览 SVG。

历史上的双 CSV 路径不再是官方地图主路径。后续维护不应重新扩散 `tile_map.csv` / `region_map.csv` 平行真源。

## 数据格式

每个官方地图预设目录：

```text
static/game_configs/maps/
  classic/
    meta.json
    map.json
  island_seas/
    meta.json
    map.json
  mountain_frontier/
    meta.json
    map.json
```

`map.json` 当前格式：

```json
{
  "schema_version": 2,
  "id": "island_seas",
  "version": 2,
  "width": 84,
  "height": 60,
  "wilderness_tile": "sea",
  "region_overrides": {
    "102": {
      "name": "北海沙岛",
      "desc": "北部海域中被白沙与浅礁环绕的岛屿。"
    },
    "305": {
      "name": "揽月港",
      "desc": "潮汐平稳的海港城，夜里月影落在长堤与船帆之间。"
    }
  },
  "region_rows": [
    [-1, -1, 102],
    [-1, 102, 102]
  ],
  "landmarks": {
    "305": {
      "x": 50,
      "y": 18,
      "asset": "city_305"
    }
  }
}
```

字段说明：

1. `schema_version`：地图源格式版本，当前为 `2`。
2. `id`：地图 ID，必须与目录名和 `meta.json.id` 一致。
3. `version`：官方地图预设版本，地图内容调整时递增。
4. `width` / `height`：地图尺寸。
5. `wilderness_tile`：`-1` 荒野格子使用的 tile，必须是合法 `TileType`。
6. `region_rows`：主矩阵，只保存 region id；`-1` 表示荒野。
7. `landmarks`：大型视觉标记的位置与资源。
8. `region_overrides`：地图局部的 region 展示文本覆盖，目前支持 `name` 和 `desc`。

不保存：

1. 不保存 `tile_rows`。
2. 不保存每格 tile。
3. 不保存每格地形覆盖。
4. 不保存未来 runtime overlay。

`region_overrides` 是例外：它不是玩法静态元数据的完整复制，而是地图预设自己的展示语义。它用于解决“同一个 region id 在不同地图里需要不同地理称呼或描述”的问题。

## Region Tile 绑定

region 到 tile 的绑定由 `static/game_configs/region_tile.csv` 统一维护，地图矩阵本身不表达 tile。

示意：

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

解析规则：

1. `region_tile.csv` 中有显式配置时，使用显式配置。
2. `city` region 未显式配置时，tile 使用 `city`，landmark 使用 `city_<region_id>`。
3. `sect` region 未显式配置时，tile 使用 `mountain`，landmark 使用 `sect_<sect_id>`。
4. `cultivate` region 未显式配置时，tile 使用 `mountain`，landmark 使用 `sub_type`，例如 `cave` / `ruin`。
5. `normal` region 必须显式配置 tile；缺失时报错。
6. 荒野使用当前地图的 `wilderness_tile`。

关键约束：

1. 一个 region 只能有一个 tile 图像。
2. 不允许为同一 region 的不同格子手工指定不同 tile。
3. 如果想做更丰富的边界，应通过不同 region 犬牙交错实现，而不是给同一 region 做每格 tile 覆盖。
4. `tile` 是底层地貌图像；`landmark_asset` 是 2x2 或特殊覆盖图像，两者不能混为一个字段。

## 荒野语义

`-1` 表示无 region，也就是荒野。

荒野不是可点击 region，不会进入 region detail。前端如果未来支持点击格子，也应先解析格子的 region；当值为 `-1` 时不触发 region 面板。

荒野 tile 由地图决定：

1. 经典地图和山脉边疆可以使用 `plain`。
2. 群岛地图可以使用 `sea`，从而让大面积海域成为不可点击的无 region 海面。

不要为了表达海域、无人雪山等无 region 地貌而恢复双矩阵主路径。若未来确实需要多种无 region 地貌，应重新设计 base terrain layer，而不是把本轮的 region-first 真源稀释回两套矩阵。

## Landmark

region 的范围表示“这个区域占据哪些格子”。城市、宗门、洞府、遗迹的大型图像表示“这个区域的视觉标记放在哪里”。两者分离。

规则：

1. landmark 坐标必须在地图范围内。
2. landmark 锚点格子应属于对应 region。
3. 2x2 landmark 必须完整落在地图范围内。
4. 2x2 landmark 覆盖范围原则上应尽量落在对应 region 内；允许少量跨边界时，应由校验器给 warning，而不是静默通过。
5. 未配置 landmark 时，使用 region center 作为 fallback。

维护时要保证语义一致：如果城市名或描述暗示它在群山、海港、沙岛、林海之中，landmark 周围地貌和所在地图的描述也应匹配。不匹配时优先移动 region / landmark，或增加 `region_overrides`。

## Region Overrides

`region_overrides` 是 map-local 的 region 展示文本覆盖，按 region id 存在 `map.json` 中。

当前支持字段：

1. `name`：覆盖 region 名称。
2. `desc`：覆盖 region 描述。

加载流程：

1. `src/run/map_source.py` 读取并校验 `region_overrides`。
2. `src/run/load_map.py` 创建 `Region` 时应用覆盖。
3. 运行时 `Map.region_overrides` 保留覆盖信息。
4. `src/run/map_snapshot.py` 将覆盖写入存档快照，并在读取存档时恢复。
5. region detail 查询自然返回覆盖后的名称和描述。
6. `tools/map_creator/main.py` 读写 `regionOverrides`，避免编辑器保存时丢失。

使用原则：

1. 当所有地图都共享某个 region 的含义时，改全局 region CSV。
2. 当只有某张地图需要不同地理称呼、方向、港口/山城/沙岛语义时，使用 `region_overrides`。
3. 不要为了某一张地图的文本差异污染全局 region 配置。
4. 描述必须匹配该地图中的实际位置、周围地貌和 landmark 位置。
5. 方向词要谨慎使用。比如“南海沙岛”如果实际在地图北侧，应改成“北海沙岛”或改为不含方向的名称。

i18n 说明：当前仓库日常开发仍按 Phase 1 维护中文内容。若后续进入正式多语言补全，`region_overrides` 需要升级为翻译 key 或结构化本地化数据，不能把中文覆盖文案复制到非中文 locale 中冒充翻译。

## 连通与边界

region 之间允许犬牙交错，边界不必规整。这样可以让农田、林海、山地、沙地之间形成真实地图感。

但 region 不应碎成难以阅读的满天星：

1. `city` region 必须连续。
2. `sect` region 必须连续。
3. `cultivate` region 必须连续，除非后续明确设计某类秘境可以多入口。
4. `normal` region 允许少量多块，用于表现山脉支脉、林海边缘、农田嵌入等自然形态。
5. `normal` region 的连通块数量由校验器限制，超过上限应报错或 warning。
6. 所有 region 必须至少有一个格子。

边界维护建议：

1. 避免大段纯直线边缘，尤其是山脉、林海、沙漠和海岸。
2. 大块同质区域可以保留主体形状，但边缘应有小范围咬合、半岛、谷地、绿洲或山麓过渡。
3. 小块突兀出现时必须有地理理由，例如绿洲、孤岛、山口、河湾；否则应合并或删除。
4. 不同地图应优先通过整体拓扑差异体现差异，而不是只换局部形状。

## 语义一致性

地图文本、地理位置、tile 绑定、landmark 和周边 region 必须互相解释得通。

已经修过的典型问题：

1. 群岛地图里 “南海沙岛” 位于北侧，改为 “北海沙岛”。
2. 群岛地图里 “揽月城” 不在群山中，改为更贴合海岛语义的 “揽月港”。
3. 山脉边疆地图里的城市和特殊地点使用更符合山岭、峡河、边城的覆盖文本。

后续检查地图时，重点看：

1. 带方向词的 region 名称是否真的位于对应方向。
2. 城市/宗门/洞府描述是否匹配周边地貌。
3. 群岛地图是否避免大片陆地文本直接继承大陆语义。
4. 山脉地图是否避免城市、农田、秘境文本与高山边疆拓扑冲突。
5. 沙漠、雪山、海域等强语义地貌是否在 region 名称和描述中被正确表达。

修复方式按优先级：

1. 移动 region 或 landmark，让视觉和文本一致。
2. 使用 `region_overrides` 覆盖该地图的名称和描述。
3. 如果所有地图都应该改，再调整全局 region CSV。

## 存档快照

地图快照当前为 schema v2。

结构：

```json
{
  "schema_version": 2,
  "preset_id": "island_seas",
  "preset_version": 2,
  "width": 84,
  "height": 60,
  "wilderness_tile": "sea",
  "region_rows": [
    [-1, -1, 102],
    [-1, 102, 102]
  ],
  "landmarks": {
    "305": {
      "x": 50,
      "y": 18,
      "asset": "city_305"
    }
  },
  "region_overrides": {
    "305": {
      "name": "揽月港",
      "desc": "潮汐平稳的海港城。"
    }
  },
  "region_tile_overrides": {}
}
```

说明：

1. 存档保存本局真实 `region_rows`。
2. 存档保存本局真实 `wilderness_tile`。
3. 存档保存本局真实 `landmarks`。
4. 存档保存本局真实 `region_overrides`，确保读档后的 region 展示语义不被后续预设文件变化破坏。
5. `region_tile_overrides` 预留给未来“整个 region 换图像”的 runtime 变化，当前始终为空。
6. 不预留每格 tile overlay，直到未来玩法明确需要。

开发阶段不要求长期兼容旧 v1 snapshot。当前代码保留了低成本 v1 读取路径，但新设计不应为旧格式继续引入双轨复杂度。

## 地图设计工具

`tools/map_creator` 已按 region-first 思路读写 `map.json`。

编辑主路径：

1. 选择 region。
2. 在地图上绘制 region 归属。
3. tile 图像自动由 `region_tile.csv` 和 `wilderness_tile` 推导。
4. 选择荒野时，将格子 region 设置为 `-1`。
5. 保存时写回 `map.json`。
6. 编辑器必须保留并写回 `regionOverrides` / `region_overrides`，不能保存后丢失地图特有文本。

工具接口中的前端字段使用驼峰形式，例如：

1. `regionRows`
2. `wildernessTile`
3. `regionOverrides`
4. `landmarks`

落盘时转换为 `map.json` 的蛇形字段。

## 前端交互

当前前端地图交互对象是 region，不是 tile。

约束：

1. tile 不可点击。
2. 地图标签点击选择 region。
3. 后续如果支持点击地图格子，也应解析为“点击该格子的 region”。
4. 如果格子是 `-1` 荒野，不触发 region detail。
5. 前端不展示 tile 详情面板。
6. 前端不硬编码 region 到 tile 的中文映射。

地图查询接口可以继续返回可渲染 tile 矩阵和 region summary；大型 region 的 summary 坐标应优先使用 landmark，再 fallback 到 center。

## 当前官方地图策略

当前官方预设包括：

1. `classic`：均衡大陆。
2. `island_seas`：群岛海域，`wilderness_tile` 为 `sea`，大量海面为 `-1` 非点击区域。
3. `mountain_frontier`：山脉、林地、寒冷边疆。

当前测试仍要求三张官方地图使用同一批 region id，这是现阶段为了玩法配置、角色分布和验证成本保持稳定的预设约定，不是 schema 的根本限制。

如果未来要让不同地图拥有真正不同的 region roster，应同步调整：

1. 地图校验器，不再强制所有官方地图 region 集合一致。
2. 角色出生、行动参数、region 选项来源等依赖全局 region 集合的逻辑。
3. 前端 region 列表和 detail 的空态。
4. 存档和外接控制 API 对地图差异的描述。
5. 对应测试和文档。

在此之前，地图差异主要通过以下方式实现：

1. `region_rows` 拓扑差异。
2. `wilderness_tile` 差异。
3. `landmarks` 位置差异。
4. `region_overrides` 文本差异。

## 校验与验证

修改官方地图后至少运行：

```powershell
python tools\map_presets\validate_presets.py
```

涉及预览时运行：

```powershell
python tools\map_presets\render_preview.py --all
python tools\map_presets\export_frontend_previews.py
```

需要查看所有软提示时运行：

```powershell
python tools\map_presets\quality_audit.py
```

涉及加载、存档、查询或编辑器时，按改动范围运行：

```powershell
pytest tests/test_map_presets.py tests/test_save_load_map_snapshot.py
pytest tests/test_init_status_api.py tests/test_websocket_handlers.py
pytest tests/test_csv_loading.py
cd web; npm run type-check
cd web; npm run test -- --run
```

校验器应覆盖：

1. `meta.json.id`、目录名、`map.json.id` 一致。
2. `schema_version == 2`。
3. `width` / `height` 与 `region_rows` 尺寸一致。
4. `wilderness_tile` 是合法 `TileType`。
5. 所有 region id 存在于 region 元数据配置。
6. 当前阶段官方地图使用同一批 region id。
7. 所有 region 至少有一个格子。
8. `normal` region 有 tile binding。
9. tile binding 中的 tile 是合法 `TileType`。
10. landmark asset 对应资源存在，或符合现有资源命名规则。
11. landmark 坐标在地图范围内。
12. landmark 锚点属于对应 region。
13. 2x2 landmark 不越界。
14. city / sect / cultivate region 连续。
15. normal region 连通块数量不超过阈值。
16. `region_overrides` 的 region id 必须存在。
17. `quality_audit.py` 中低误报的结构质量项：
    - `classic` / `mountain_frontier` 的 `106` 水系连续且接入 `105`。
    - 不能出现 tiny water / sea component。
    - normal region 不能出现过小脱离碎片。
    - 大面积 normal region 不能过度块状。
    - normal region 不能出现过长内部直边。
    - landmark 2x2 覆盖不能 poor fit。

`landmark_near_boundary` 仍是软提示，只在 `quality_audit.py` 报告中展示，不作为 `validate_presets.py` hard fail。群岛、小岛、港口、洞府等语义经常天然贴边，是否移动应结合预览图人工判断。

审美和叙事语义仍需要人工审图辅助。每次大幅调整地图后，应抽查名称、描述、方向词、城市位置、宗门/洞府周边地貌和预览图。地图质量优化的完整背景见 `docs/specs/map-quality-optimization.md`。

## 后续留白

未来如果要加入地图演化，应重新设计以下内容：

1. 整个 region 更换 tile 图像，例如城市废墟化、森林焚毁。
2. 局部格子的 runtime overlay。
3. 无 region 地貌是否从单一 `wilderness_tile` 升级为 base terrain layer。
4. 道路、河流、边界、海岸线等独立地理图层。
5. 外接控制 API 修改 region 归属或 landmark。
6. 不同地图拥有不同 region roster 的完整契约。

这些都不属于当前已落地系统的范围。当前核心仍是：官方地图源格式以 `region_rows` 为唯一语义矩阵，tile 从 region 绑定和荒野 tile 推导。
