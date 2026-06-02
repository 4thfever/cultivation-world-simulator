---
description: Region-first map system rules
globs:
  - "src/run/map_*.py"
  - "src/run/load_map.py"
  - "src/classes/environment/map.py"
  - "src/classes/environment/region.py"
  - "src/classes/environment/tile.py"
  - "src/server/services/game_queries.py"
  - "src/sim/save/**/*.py"
  - "src/sim/load/**/*.py"
  - "static/game_configs/maps/**/*.json"
  - "static/game_configs/region_tile.csv"
  - "tools/map_presets/**/*.py"
  - "tools/map_creator/**/*.py"
  - "tests/test_map_presets.py"
  - "tests/test_save_load_map_snapshot.py"
  - "web/src/components/game/**/*.vue"
  - "web/src/components/game/utils/mapLabels.ts"
  - "web/src/types/**/*.ts"
alwaysApply: false
---

# Region-first 地图系统规则

地图系统的完整设计优先参考 `docs/specs/region-first-map-system.md`。后续修改地图源、加载、存档、查询、预览、地图设计工具或前端地图交互时，必须遵守本规则。

## 官方地图真源

1. 官方地图预设真源是 `static/game_configs/maps/<map_id>/map.json`。
2. `map.json` 当前为 schema v2，主矩阵是 `region_rows`。
3. 不要重新引入 `tile_map.csv` / `region_map.csv` 作为平行主路径。
4. `region_rows` 是地图语义唯一矩阵；每格 tile 必须由 `region_tile.csv` 和 `wilderness_tile` 推导。
5. `-1` 表示无 region / 荒野。荒野可以按地图使用不同 `wilderness_tile`，例如群岛地图用 `sea`。

## Region 与 Tile

1. 一个 region 当前只能绑定一个 tile 图像。
2. 不允许为同一个 region 的不同格子写不同 tile。
3. 想做犬牙交错的真实地图边界时，应调整不同 region 的边界，而不是引入每格 tile override。
4. `static/game_configs/region_tile.csv` 是 region 到底层 tile / landmark asset 的统一绑定表。
5. `tile` 是底层地貌图像；`landmark_asset` 是城市、宗门、洞府、遗迹等大型覆盖图像，不要混用。

## 交互语义

1. 只有 region 可以点击。
2. tile 不可点击，也不应有独立 detail 面板。
3. 后续如果支持点击地图格子，也必须解析为点击该格子的 region。
4. 点击 `-1` 荒野不应打开 region detail。

## Landmark

1. `landmarks` 负责大型视觉标记位置，region 范围负责区域占格，两者不要混成一个概念。
2. landmark 坐标必须在地图范围内。
3. landmark 锚点格子应属于对应 region。
4. city / sect / cultivate region 应保持连续。
5. normal region 可以少量分块以表现自然边界，但碎片数量应受校验器限制。

## Region Overrides

1. `region_overrides` 是 map-local 的 region 展示文本覆盖，目前支持 `name` 和 `desc`。
2. 只有某张地图需要不同地理称呼或描述时，使用 `region_overrides`；所有地图都共享的语义才改全局 region CSV。
3. `region_overrides` 必须随 map source、map snapshot、map creator 保存和恢复，不能在工具保存或读档时丢失。
4. 覆盖文本必须匹配该地图中的实际位置、周边地貌和 landmark 位置。
5. 带方向词的名称必须与地图坐标一致；若方向不稳定，优先改成不含方向的名称。
6. i18n Phase 1 下日常可只维护中文覆盖文本；正式多语言补全时不得把中文 `region_overrides` 复制到非中文 locale 伪装翻译，应升级翻译 key 或结构化本地化策略。

## 语义一致性

1. 地图文本、地理位置、tile 绑定、landmark 和周边 region 必须互相解释得通。
2. 群岛地图应避免直接继承大陆、山城、内陆农田等不匹配描述。
3. 山脉边疆地图应让城市、宗门、洞府和特殊地点贴合山岭、峡谷、寒林、边城等拓扑。
4. 如果发现名称或描述与地图不匹配，优先移动 region / landmark，或添加 `region_overrides`；不要让明显不匹配的全局文本继续暴露到 region detail。

## 验证

修改官方地图后至少运行：

```powershell
python tools\map_presets\validate_presets.py
```

涉及预览资源时运行：

```powershell
python tools\map_presets\render_preview.py --all
python tools\map_presets\export_frontend_previews.py
```

涉及加载、存档、查询或编辑器时，按改动范围运行：

```powershell
pytest tests/test_map_presets.py tests/test_save_load_map_snapshot.py
pytest tests/test_init_status_api.py tests/test_websocket_handlers.py
pytest tests/test_csv_loading.py
cd web; npm run type-check
cd web; npm run test -- --run
```
