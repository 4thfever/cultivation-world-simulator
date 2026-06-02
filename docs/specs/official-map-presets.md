# 官方地图预设与地图快照系统

本文档记录“多个官方地图 + 开局地图选择 + 存档地图快照”的设计方案。

当前状态说明：本文档保留官方地图预设、开局选择和存档快照的第一版设计背景。地图源格式和快照格式已经升级为 region-first schema v2，官方地图真源不再是 `tile_map.csv + region_map.csv`，而是 `static/game_configs/maps/<id>/map.json`。涉及地图源、region/tile 绑定、`wilderness_tile`、`region_overrides`、地图设计工具和快照 schema v2 的当前事实，请优先参考 `docs/specs/region-first-map-system.md`。

当前目标不是动态地图生成，也不是完整地理模拟，而是把现有唯一静态地图升级为三张官方地图预设，并为后续“地图可被角色行动改变”预留清晰的数据接口。

## 目标

本次实现目标：

1. 官方内置三张地图：
   - `classic`：九州中土
   - `mountain_frontier`：万山边境
   - `island_seas`：沧海诸洲
2. 三张地图统一尺寸，第一版统一为 `60 x 84`。
3. 现有默认地图 `classic` 也扩展到新尺寸。
4. 不新增 region，不新增具体地块语义，只改变 region 的形状、面积和位置。
5. 开局时可选择地图。
6. `RunConfig` 保存本局选择的 `map_id`，并随存档保存。
7. 存档保存全量地图快照，而不是只保存 `map_id`。
8. 读档优先恢复存档中的地图快照，避免未来官方地图更新或地图演化破坏旧存档。
9. 新增地图预设校验和预览工具，支持 Codex/开发者可视化维护地图。

非目标：

1. 不做动态地图生成器。
2. 不做玩家地图编辑器。
3. 不引入区域文化、资源权重、交通网络等新系统字段。
4. 不让事件、角色、宗门逻辑在本次改动中强依赖地图主题。
5. 不保存完整 region 静态元数据到存档。
6. 不在本次实现中重做前端地图渲染架构。

## 设计原则

### 1. 地图预设是开局来源，地图快照是本局事实

`map_id` 只表示这局游戏从哪张官方地图开始。

存档中的 `map_snapshot` 才表示本局当前真实地图。

因此：

1. 新开局时，根据 `RunConfig.map_id` 读取官方地图预设。
2. 保存时，将当前 `world.map` 序列化为 `map_snapshot`。
3. 读档时，优先从 `map_snapshot` 重建地图。
4. 只有旧存档或快照缺失时，才回退到 `RunConfig.map_id` 对应的官方地图。

### 2. region 身份保持一致，空间形状可以变化

三张官方地图必须使用同一批 region id。

允许：

1. 同一个 region 在不同地图中位于不同位置。
2. 同一个 region 在不同地图中形状、面积显著不同。
3. 普通 region 在某张地图上面积很小。
4. 同一个宗门总部在不同地图中出现在不同地理位置。

不允许：

1. 某张地图缺失已有 region id。
2. 新增只存在于某张地图的 region id。
3. 某张地图使用不存在于 `normal_region.csv` / `city_region.csv` / `cultivate_region.csv` / `sect_region.csv` 的 region id。
4. `tile_map.csv` 与 `region_map.csv` 尺寸不一致。

### 3. 第一版保存全量矩阵，不做过早压缩

地图尺寸约为 `60 x 84`，全量保存 `tile_rows` 与 `region_rows` 的 JSON 成本可接受。

第一版不做 RLE、delta、二进制压缩或只保存 overrides。

未来地图明显扩大后，再考虑压缩格式或增量快照。

### 4. region 静态定义仍来自配置表

地图快照只保存地块类型和 region 空间归属。

region 名称、描述、城市初始人口、洞府属性、宗门绑定等仍由现有 CSV 配置提供：

1. `static/game_configs/normal_region.csv`
2. `static/game_configs/city_region.csv`
3. `static/game_configs/cultivate_region.csv`
4. `static/game_configs/sect_region.csv`

运行时状态继续走现有存档字段，例如：

1. `cultivate_regions_hosts`
2. `regions_status`
3. 后续新增的 region runtime state

未来如果 region 静态定义也会被本局改变，再在 `map_snapshot.region_overrides` 中保存差异。

## 官方地图

### classic / 九州中土

定位：默认均衡大陆。

特点：

1. 作为默认新手体验。
2. 保留当前地图的大体气质。
3. 扩展到统一尺寸。
4. 中央与周边地貌分布相对均衡。
5. 城市、宗门、洞府分布不过度极端。

### mountain_frontier / 万山边境

定位：山地、森林、险地更多的边境世界。

特点：

1. 山脉、森林、雪峰、峡谷占比更高。
2. 城市集中在谷地、山口或少数平原。
3. 洞府和宗门更靠近山地、险地和灵脉感较强的位置。
4. region 可以更狭长，但不应碎到不可读。
5. 视觉气质应明显不同于 `classic`。

### island_seas / 沧海诸洲

定位：海域、岛屿、海岸更多的诸洲世界。

特点：

1. 水域显著增加。
2. region 分布在几个岛屿、半岛或大陆碎片上。
3. 城市多位于海岸、内湾或河口。
4. 宗门可位于大岛高地、孤岛或海岸山脉。
5. 水域多但不能让地图显得空，region 不应被切得过碎。

## 文件结构

新增地图预设目录：

```text
static/game_configs/maps/
  classic/
    meta.json
    tile_map.csv
    region_map.csv
  mountain_frontier/
    meta.json
    tile_map.csv
    region_map.csv
  island_seas/
    meta.json
    tile_map.csv
    region_map.csv
```

`meta.json` 第一版字段：

```json
{
  "id": "classic",
  "name": "九州中土",
  "desc": "地貌均衡，适合默认体验。",
  "size_label": "中型",
  "version": 1,
  "is_default": true
}
```

约定：

1. `id` 必须与目录名一致。
2. `version` 是官方地图预设版本，不等同于存档快照 schema 版本。
3. 第一版名称和描述可以只维护中文，符合当前 i18n Phase 1。
4. 后续需要正式多语言时，再将 `name` / `desc` 改为 i18n key 或按 locale 提供本地化结构。

兼容旧路径：

1. 旧的 `static/game_configs/tile_map.csv` 与 `static/game_configs/region_map.csv` 可以暂时保留。
2. `classic` 目录存在时，加载器优先读取 `maps/classic/`。
3. 若旧工具或旧流程仍调用默认加载入口，默认仍解析为 `classic`。

## 后端设计

### 地图预设模块

新增：

```text
src/run/map_presets.py
```

建议提供：

```python
DEFAULT_MAP_ID = "classic"

def list_map_presets() -> list[MapPreset]:
    ...

def get_map_preset(map_id: str | None) -> MapPreset:
    ...

def resolve_map_files(map_id: str | None) -> tuple[MapPreset, Path, Path]:
    ...
```

`MapPreset` 可使用 dataclass 或 Pydantic model。

职责：

1. 读取 `static/game_configs/maps/*/meta.json`。
2. 校验 `id` 与目录名一致。
3. 提供默认地图 fallback。
4. 屏蔽 `load_map.py` 对文件路径结构的直接了解。

### 地图加载

修改：

```text
src/run/load_map.py
```

当前：

```python
def load_cultivation_world_map() -> Map:
    ...
```

改为：

```python
def load_cultivation_world_map(map_id: str | None = None) -> Map:
    ...
```

加载流程：

1. 通过 `resolve_map_files(map_id)` 获取 `tile_map.csv` 与 `region_map.csv`。
2. 使用现有 CSV 解析逻辑创建 `Map`。
3. 将 `map_id`、`map_name`、`preset_version` 写入 `Map`。
4. 按现有 `_load_and_assign_regions(...)` 绑定 region。
5. 刷新 `update_sect_regions()`。

### Map 对象

修改：

```text
src/classes/environment/map.py
```

建议字段：

```python
class Map:
    def __init__(
        self,
        width: int,
        height: int,
        map_id: str = "classic",
        map_name: str = "",
        preset_version: int = 1,
    ):
        self.map_id = map_id
        self.map_name = map_name
        self.preset_version = preset_version
        ...
```

如果为了减少构造调用影响，也可先保持构造参数不变，在加载器创建后赋值。

### RunConfig

修改：

```text
src/config/settings_schema.py
```

在 `NewGameDefaults` 中新增：

```python
map_id: str = "classic"
```

由于 `RunConfig(NewGameDefaults)` 继承该字段，新开局请求、当前运行配置和存档 `run_config` 会自然包含 `map_id`。

约定：

1. 开局选择地图后，`map_id` 会保存到 `new_game_defaults`。
2. 下次打开新游戏面板时，默认记住上次选择。
3. 若 `map_id` 无效，后端应返回清晰错误，或 fallback 到 `classic` 并记录 warning。第一版推荐启动新游戏时显式报错，读旧存档 fallback。

### 初始化流程

修改：

```text
src/server/init_flow.py
```

当前地图加载发生在读取 `run_config` 之前，需要调整顺序：

```python
run_config = get_runtime_run_config(runtime)
game_map = await asyncio.to_thread(load_cultivation_world_map, run_config.map_id)
```

之后创建 `World`、`Simulator`、`world.run_config_snapshot` 的逻辑保持不变。

### 公共查询接口

新增 query：

```text
GET /api/v1/query/world/map-presets
```

返回：

```json
{
  "maps": [
    {
      "id": "classic",
      "name": "九州中土",
      "desc": "地貌均衡，适合默认体验。",
      "size_label": "中型",
      "version": 1,
      "is_default": true
    }
  ]
}
```

职责：

1. 前端开局界面从后端获取官方地图列表。
2. 避免前端硬编码地图 id、名称和描述。
3. 后续地图新增、改名或隐藏时，优先在后端/配置层处理。

现有地图查询：

```text
GET /api/v1/query/world/map
```

建议补充字段：

```json
{
  "map_id": "classic",
  "map_name": "九州中土",
  "preset_version": 1,
  "width": 84,
  "height": 60,
  "data": [],
  "regions": [],
  "render_config": {}
}
```

## 地图快照存档

### 存档结构

在 `world` 下新增：

```json
{
  "world": {
    "map_snapshot": {
      "schema_version": 1,
      "preset_id": "classic",
      "preset_version": 1,
      "width": 84,
      "height": 60,
      "tile_rows": [
        ["plain", "plain", "water"]
      ],
      "region_rows": [
        [-1, 101, 101]
      ],
      "region_overrides": {}
    }
  }
}
```

字段说明：

1. `schema_version`：地图快照结构版本，第一版为 `1`。
2. `preset_id`：本局地图来源。
3. `preset_version`：官方地图预设版本。
4. `width` / `height`：快照尺寸。
5. `tile_rows`：当前地图所有 tile type，使用小写字符串保存，例如 `plain`、`water`。
6. `region_rows`：当前地图所有 region id，未归属为 `-1`。
7. `region_overrides`：预留字段，第一版保存空对象。

### 序列化职责

建议新增：

```text
src/run/map_snapshot.py
```

提供：

```python
def serialize_map_snapshot(game_map: Map) -> dict:
    ...

def load_map_from_snapshot(snapshot: dict) -> Map:
    ...
```

`serialize_map_snapshot(...)`：

1. 遍历 `game_map.tiles`。
2. 生成 `tile_rows`。
3. 根据 `tile.region.id` 或 `game_map.region_cors` 生成 `region_rows`。
4. 写入 `schema_version`、`preset_id`、`preset_version`、`width`、`height`。

`load_map_from_snapshot(...)`：

1. 校验 `schema_version`。
2. 校验 `width` / `height` 与矩阵尺寸一致。
3. 根据 `tile_rows` 创建 `Map`。
4. 根据 `region_rows` 聚合 region 坐标。
5. 复用现有 region 元数据加载逻辑绑定 region。
6. 刷新宗门 region 缓存。

注意：

1. `load_map_from_snapshot` 不应依赖官方 preset CSV。
2. 但它仍依赖 region 元数据 CSV 来构造 region 对象。
3. 第一版不处理 `region_overrides`，但保留字段。

### 保存流程

修改：

```text
src/sim/save/save_game.py
```

在 `world_data` 中新增：

```python
"map_snapshot": serialize_map_snapshot(world.map)
```

`meta` 中建议新增：

```python
"map_id": run_config_snapshot.get("map_id", getattr(world.map, "map_id", "classic")),
"map_name": getattr(world.map, "map_name", ""),
```

前端存档列表第一版可以不展示地图名，但后端 meta 先写入。

### 读档流程

修改：

```text
src/sim/load/load_game.py
```

读档顺序：

```python
world_data = save_data.get("world", {})
run_config_snapshot = save_data.get("run_config", default_run_config)
map_snapshot = world_data.get("map_snapshot")

if map_snapshot:
    game_map = load_map_from_snapshot(map_snapshot)
else:
    map_id = run_config_snapshot.get("map_id", "classic")
    game_map = load_cultivation_world_map(map_id)
```

旧存档兼容：

1. 没有 `map_snapshot` 的旧存档使用 `run_config.map_id`。
2. 没有 `run_config.map_id` 的旧存档使用 `classic`。
3. 这属于低成本兼容，不引入双轨业务逻辑。

## 前端设计

### DTO

修改：

```text
web/src/types/api.ts
```

`RunConfigDTO` 新增：

```ts
map_id: string;
```

新增：

```ts
export interface MapPresetDTO {
  id: string;
  name: string;
  desc: string;
  size_label?: string;
  version?: number;
  is_default?: boolean;
}

export interface MapPresetsResponseDTO {
  maps: MapPresetDTO[];
}
```

`MapResponseDTO` 建议新增：

```ts
map_id?: string;
map_name?: string;
preset_version?: number;
width?: number;
height?: number;
```

`SaveFileDTO` 可新增：

```ts
map_id?: string;
map_name?: string;
```

第一版不强制在存档列表展示。

### API

修改：

```text
web/src/api/modules/world.ts
```

或按现有职责放在 `system.ts` / `world.ts` 中，建议放 `world.ts`：

```ts
fetchMapPresets(): Promise<MapPresetDTO[]>
```

### 设置 Store

修改：

```text
web/src/stores/setting.ts
```

默认 draft：

```ts
const newGameDraft = ref<RunConfigDTO>({
  content_locale: defaultLocale,
  init_npc_num: 9,
  sect_num: 3,
  npc_awakening_rate_per_month: 0.01,
  world_lore: '',
  map_id: 'classic',
});
```

`applySettings(...)` 需要兼容后端返回的新字段。

若后端旧设置缺少 `map_id`，前端可在合并时补 `classic`。

### 开局界面

修改：

```text
web/src/components/game/panels/system/GameStartPanel.vue
```

新增地图选择。

UI 方案：

1. 第一版可以使用简洁的三项选择控件。
2. 若实现成本低，优先使用三张紧凑卡片，比普通下拉更符合“选择世界”的语义。
3. 不做地图预览大图，不做复杂 landing，不做额外说明页。

约束：

1. `readonly=true` 时不可修改地图。
2. 地图选项来自后端 `map-presets` 接口。
3. 接口失败时可 fallback 为 `classic` 单项，避免开局面板完全不可用。

## 地图维护工具

新增目录：

```text
tools/map_presets/
  render_preview.py
  validate_presets.py
```

### validate_presets.py

职责：

1. 校验三张地图目录和 `meta.json`。
2. 校验 `tile_map.csv` 与 `region_map.csv` 尺寸一致。
3. 校验所有行列宽一致。
4. 校验 tile type 可被 `TileType` 解析，或符合现有宗门驻地 fallback 规则。
5. 校验 region id 存在于 region 元数据配置。
6. 校验三张地图 region id 覆盖集合一致。
7. 校验所有 city / cultivate / sect region 至少有一个坐标。
8. 校验 region 中心点在地图范围内。
9. 校验 region 不出现过度碎片化。

### render_preview.py

职责：

1. 将指定地图预设渲染为 PNG。
2. 输出到：

```text
tmp/map_previews/<map_id>.png
```

预览图应显示：

1. 地貌底色。
2. region 边界。
3. region id 或名称。
4. 城市 / 洞府 / 宗门标记。
5. 地图尺寸和 map id。

Codex/开发者维护流程：

```text
编辑或生成 CSV
-> python tools/map_presets/validate_presets.py
-> python tools/map_presets/render_preview.py --map-id classic
-> 查看 tmp/map_previews/*.png
-> 前端实机验证
```

## 测试计划

### 后端测试

新增：

```text
tests/test_map_presets.py
tests/test_save_load_map_snapshot.py
```

覆盖：

1. `list_map_presets()` 返回三张官方地图。
2. 三张地图都能通过 `load_cultivation_world_map(map_id)` 加载。
3. 三张地图尺寸统一为 `60 x 84`。
4. `tile_map.csv` 与 `region_map.csv` 尺寸一致。
5. 三张地图 region id 覆盖一致。
6. 所有 region center 坐标合法。
7. `RunConfig` 支持 `map_id`。
8. 新开局初始化时使用 `run_config.map_id`。
9. `serialize_map_snapshot` 输出完整矩阵。
10. `load_map_from_snapshot` 不依赖官方 preset CSV 即可恢复空间形状。
11. 保存后 JSON 中包含 `world.map_snapshot`。
12. 读档优先使用 `map_snapshot`，并恢复 `world.map.map_id`、尺寸、tile 和 region 归属。
13. 旧存档没有 `map_snapshot` 时 fallback 到 `run_config.map_id` 或 `classic`。

### 前端测试

至少执行：

```text
cd web && npm run type-check
```

如修改开局组件较多，补充组件测试：

1. 初始挂载会请求地图 preset。
2. 选择地图会更新 `settingStore.newGameDraft.map_id`。
3. `readonly=true` 时地图选择不可用。

### 集成验证

手动或自动验证：

1. 启动前后端。
2. 开局分别选择三张地图。
3. `/api/v1/query/world/map` 返回对应 `map_id`、尺寸和 region。
4. 前端地图非空，尺寸正确。
5. region 标签没有明显大面积重叠。
6. 宗门势力层、云层、感知层跟随新地图尺寸。
7. 保存后 JSON 含 `map_snapshot`。
8. 读档后恢复同一张地图，而不是重新读取默认地图。

## 实施顺序

建议按以下顺序落地：

1. 新增地图预设目录，将现有地图复制为 `classic`。
2. 生成并调整三张 `60 x 84` 官方地图。
3. 新增 `map_presets.py`，改造 `load_cultivation_world_map(map_id)`。
4. 新增 `map_snapshot.py`，实现序列化和反序列化。
5. 修改 `RunConfig`、初始化流程、保存和读档。
6. 新增 `map-presets` query 接口，地图 query 返回 map 元信息。
7. 修改前端 DTO、API、setting store 和开局面板。
8. 新增地图校验和预览工具。
9. 补测试。
10. 运行后端相关测试、前端 type-check，并做三张地图实机验证。

## 后续扩展

未来如果要让地图影响风土人情，可以在本系统之上继续扩展：

1. `map_id` 影响默认世界气质。
2. region 根据地貌和位置生成文化标签。
3. 角色出生地、宗门所在地、事件发生地接入地区上下文。
4. 地图变化写入 `map_snapshot.tile_rows` / `region_rows`。
5. region 静态字段变化写入 `region_overrides`。
6. 外接控制 API 提供地图查询与地图变更 command。

这些扩展都不属于本次实现范围。
