# 地图质量优化 Spec

本文档记录官方地图质量优化的设计判断、潜在问题、分期方案与验收标准。它建立在现有 region-first 地图系统之上，不替代 `docs/specs/region-first-map-system.md`，而是补充“地图看起来是否合理、是否美观、是否容易维护”的质量层。

## 背景

当前官方地图已经收束为 schema v2：

1. 官方地图真源是 `static/game_configs/maps/<map_id>/map.json`。
2. `region_rows` 是唯一语义矩阵，只保存 region id。
3. tile 由 `static/game_configs/region_tile.csv` 与 `wilderness_tile` 推导。
4. 一个 region 当前只允许绑定一种 tile。
5. 城市、宗门、洞府、遗迹等大型图像位置由 `landmarks` 控制。
6. 地图局部名称与描述差异由 `region_overrides` 控制。

这个设计适合当前阶段，不应为了修地图观感而恢复 `tile_map.csv + region_map.csv` 双矩阵，也不应引入每格地形覆盖作为新的主路径。

当前问题主要不是 schema 选错，而是官方地图内容与工具链还没有形成稳定的质量门：地图可以被刷成大块 region，水系可以被切断，编辑工具也存在把官方地图尺寸写坏的风险。

## 当前已观察到的问题

### 地图设计问题

1. 水系拓扑不稳定。
   - `106` 在全局配置中是强水系语义 region。
   - `classic` 中 `106` 当前拆成多段水域，视觉上像河流被切断。
   - `mountain_frontier` 中 `106` 也拆成多段，与“峡河奔流”的地图覆盖文本不匹配。
   - `island_seas` 中 `106` 作为潮汐航道可以多段，但应表现为海峡、航道、内湾，而不是随机水块。

2. 大面积 region 过于块状。
   - 沙漠、雨林、冰原、山脉、草原、毒泽、海岸等 region 的主体过于实心。
   - 即使没有超长直线边界，整体仍像用矩形或大圆刷子铺出来。
   - 缺少山麓、湾口、岬角、河湾、绿洲、林缘、支脉、半岛等自然形态。

3. 边界参差不足但碎片又缺少语义。
   - 自然边界需要犬牙交错，但不是满天星碎片。
   - 少量 1 到 5 格小块如果没有绿洲、离岛、礁湖、山口、支流等地理解释，会显得像误刷。

4. 地图语义与视觉位置容易漂移。
   - 全局 region 名称中有方向、地貌和用途语义。
   - 地图覆盖文本可以修正局部语义，但如果形状和 landmark 不匹配，文本修正也会显得牵强。
   - 城市、宗门、洞府、遗迹应落在符合其描述的位置附近，而不仅是满足 landmark anchor 属于 region。

5. 三张官方地图的差异还可以更强。
   - `classic` 应该是均衡大陆，重点是主河、东海、西域、南疆、北境之间的完整地理关系。
   - `island_seas` 应该以群岛、海峡、港口、内湾、离岛为主，而不是把大陆地貌拆成小块散在海上。
   - `mountain_frontier` 应该以山脉、谷地、峡河、边城、荒原为主，而不是单纯扩大 mountain tile 的面积。

### 代码与工具链问题

1. `tools/map_creator/main.py` 的保存尺寸存在风险。
   - 当前常量仍是 `MAP_WIDTH = 70`、`MAP_HEIGHT = 50`。
   - 官方地图当前是 `84x60`。
   - 加载时会读 map source 的真实尺寸，但保存时仍按常量重建矩阵，可能裁坏地图。

2. `tools/map_creator/main.py` 当前默认只加载 `classic`。
   - `DEFAULT_MAP_ID = "classic"` 固定。
   - 缺少从 URL 或接口选择 `mapId` 的主路径。
   - 维护三张官方地图时容易误改或无法直接编辑目标预设。

3. 地图编辑器保存 payload 没有充分复用现有 parser / serializer。
   - `src/run/map_source.py` 已经有 `MapSource`、`map_source_to_dict`、读取与校验逻辑。
   - 编辑器目前自己组装 JSON，容易与主路径 drift。

4. 校验器偏重格式正确，缺少质量审计。
   - 现有 `tools/map_presets/validate_presets.py` 已检查 schema、region id、连通性、landmark anchor 等。
   - 视觉检查目前只有少量特例，例如群岛 island/plain 噪声、山脉左边缘过直。
   - 尚未系统检查水系连续性、小碎片、孤立水块、块状度、海岸/河岸质量、语义锚点。

5. 运行时 region 创建失败当前只 `print`。
   - `src/run/load_map.py` 中 `_load_and_assign_regions()` 创建 region 失败时打印错误后继续。
   - 对官方地图来说，这可能把数据错误变成“地图能加载但少 region”的隐性故障。
   - 校验器可以先兜住，但 loader 对官方预设也应尽量 fail fast。

6. 前端地图预览组件手写 preset import。
   - `web/src/components/game/panels/system/MapPresetPreview.vue` 直接 import 三张 SVG。
   - `tools/map_presets/export_frontend_previews.py` 能导出所有预设，但前端展示表仍需要手动同步。
   - 后续新增地图时容易出现已导出但前端不显示的状态。

7. 预览体系分散。
   - `render_preview.py` 输出 PNG 给人工审图。
   - `export_frontend_previews.py` 输出 SVG 给前端启动页。
   - 两者颜色表与标记规则重复维护，未来可能不一致。

8. 地图质量问题缺少可复现报告。
   - 现在需要人工看图发现“河断了”“太整齐”。
   - 应提供机器可读的 audit 输出，让 PR、测试和人工审图有共同语言。

## 设计原则

1. 保持 region-first。
   - 本轮不新增 tile layer、river layer、road layer、height layer。
   - 不恢复旧双矩阵。
   - 不为单个 region 增加每格 tile override。

2. 地图质量优先通过 `region_rows` 改善。
   - 水系用水域 region 的连续形状表达。
   - 海岸用海域、岛屿、荒野海面和陆地 region 的边界表达。
   - 山地、森林、沙漠、草原通过 region 犬牙交错表达过渡。

3. 自动化只做辅助，不做完全随机生成。
   - 官方地图是视觉资产，需要人工审图。
   - 可以用脚本发现问题、生成候选边界扰动、统计质量指标。
   - 最终 `map.json` 应是可审查的确定性结果。

4. 不用碎片冒充自然。
   - 自然边界要有主体与方向。
   - 小块必须有地理语义，否则合并或删除。
   - city / sect / cultivate region 应保持清晰连续。

5. 文本、landmark、形状三者一致。
   - 带方向词、河海词、山谷词、港口词的名称和描述必须匹配实际位置。
   - 优先移动 region / landmark，其次用 `region_overrides` 修正局部称呼。

6. 质量门分层。
   - 格式和运行时契约错误应 hard fail。
   - 审美指标先作为 audit warning 输出，稳定后再逐步转 hard fail。

## 分期方案

### Phase 0：修维护工具的安全问题

状态：已落地。

目标：确保后续编辑三张官方地图不会被工具链写坏。

任务：

1. 修复 `tools/map_creator/main.py` 保存尺寸。
   - 保存时使用请求中的 `width` / `height`。
   - 如果请求缺失，读取当前 `map.json` 的 `width` / `height` 兜底。
   - 禁止保存时无条件使用 `MAP_WIDTH` / `MAP_HEIGHT`。

2. 支持选择地图预设。
   - `load_map_data()` 支持传入 `map_id`。
   - `/api/init` 支持 `?mapId=<id>`。
   - `/api/save` 使用 payload 中的 `mapId`，并校验该目录存在或显式允许创建。
   - 页面初始化可从 URL query 读取 `mapId`。

3. 保存时保留 map source 元数据。
   - 保留已有 `schema_version`。
   - 保留或正确递增 `version` 的规则需要明确。
   - 保留 `wilderness_tile`、`landmarks`、`region_overrides`。
   - 输出仍使用 `ensure_ascii=False, indent=2` 并以换行结尾。

4. 加入工具级 smoke test。
   - 至少覆盖：读取 `84x60` 地图后保存仍是 `84x60`。
   - 覆盖：保存非 classic 地图不会写到 classic。
   - 可以优先抽出纯函数测试，避免启动 Flask 服务。

验收：

1. 使用地图编辑器读写 `classic` 后，`width=84`、`height=60`、`region_rows` 尺寸不变。
2. 使用地图编辑器读写 `island_seas` 与 `mountain_frontier` 不会覆盖 `classic`。
3. `python tools\map_presets\validate_presets.py` 通过。

已落地内容：

1. `tools/map_creator/main.py` 已改为按请求或现有 `map.json` 的真实尺寸保存。
2. 地图编辑器支持通过 `?mapId=<id>` 加载和保存指定预设。
3. 保存 payload 会携带 `mapId`、`width`、`height`、`regionOverrides`。
4. 未显式允许创建时，未知 map id 会被拒绝。
5. 已新增 `tests/test_map_creator.py` 覆盖尺寸保留、非 classic 读写、未知 map 拒绝和路径式 map id 拒绝。

### Phase 1：建立地图质量审计

状态：已落地第一版。

目标：把“河流断了”“太方”“太碎”变成可复现报告。

任务：

1. 在 `tools/map_presets` 下新增质量审计能力。
   - 可以集成进 `validate_presets.py`，也可以先新增 `audit_quality.py`。
   - 推荐先输出 warning report，避免初期 hard fail 过多。

2. 审计指标：
   - region 连通块数量与小碎片面积。
   - water / sea 连通块数量。
   - `106` 在 `classic` 与 `mountain_frontier` 中是否连续。
   - `106` 是否与 `105` 或海岸出口建立合理接触。
   - 小于阈值的孤立 water / sea / normal region 组件。
   - 大面积 region 的块状度，例如 `area / bbox_area`、perimeter、边界方向变化率。
   - region 边界长直线与长阶梯。
   - landmark 2x2 覆盖是否大部分落在所属 region 内。
   - landmark 到所属 region 边界距离是否过近。

3. 输出格式：
   - 控制台友好文本，用于人工阅读。
   - 可选 JSON，用于后续 CI 或 PR 评论。
   - 每条 warning 包含 map id、region id、问题类型、关键数值、建议动作。

4. 测试：
   - 为审计纯函数加单元测试。
   - 使用小矩阵覆盖断流、孤立水块、过高填充率、小碎片等场景。

验收：

1. 审计脚本能对三张官方地图输出稳定报告。
2. 现有地图即使有 warning，也不阻断 `validate_presets.py` 的基础校验，除非明确启用 strict。
3. 小矩阵测试覆盖核心指标。

已落地内容：

1. 新增 `tools/map_presets/quality_audit.py`。
2. 审计支持控制台报告、`--json` 机器可读输出、`--strict` 非零退出。
3. 当前第一版指标包括：
   - region 连通块与小碎片。
   - water / sea 小组件。
   - `classic` / `mountain_frontier` 的 `106` 连续性与入海口。
   - 大面积 normal region 的块状度。
   - normal region 长直边。
   - landmark 2x2 覆盖与贴边情况。
4. 新增 `tests/test_map_quality_audit.py` 覆盖核心审计函数。

### Phase 2：重绘三张官方地图

状态：已完成结构性硬问题修复，整体美化仍可继续迭代。

目标：修复不合理与不美观问题，并强化三张地图的差异。

通用规则：

1. 修改 `static/game_configs/maps/<id>/map.json` 的 `region_rows`。
2. 不改 `region_tile.csv`，除非发现 region 绑定本身错误。
3. 不新增 region id。
4. 不删除三张图共享的 region roster。
5. 移动 landmark 时必须保持 anchor 属于对应 region。
6. 修改地图后同步生成预览。

`classic` 调整方向：

1. 将 `106` 整理为连续主河。
2. 河流应从中北或西北水源穿过中部，最终接入东海或河口水域。
3. `110`、`115`、`112` 可沿河形成林带、竹境、农田过渡。
4. 西部 `102` / `117` 与南部 `103` 的交界应有戈壁、沙缘、林缘过渡。
5. 东海 `105` 海岸线增加湾口与岬角，避免一整块竖切海岸。
6. `118` 作为海外岛屿保留清晰孤岛语义。

`island_seas` 调整方向：

1. 保持大面积 `-1` sea wilderness 作为海面背景。
2. `106` 表达潮汐航道、海峡和内湾，允许多段，但应避免随机水块。
3. 删除或合并缺少语义的 1 到 2 格碎片。
4. 大岛边缘增加湾、岬、礁湖，但避免棋盘噪声。
5. 城市优先靠港口、内湾或河口。
6. `105` 表达强语义海域，不需要覆盖所有海面。

`mountain_frontier` 调整方向：

1. 将 `106` 整理为连续峡河。
2. 峡河应穿过山地和谷地，让城市、宗门、洞府位置更有解释。
3. `107` 从大灰块改为主山脉加支脉。
4. `109` / `101` / `301` / `406` 形成中央谷地或山口走廊。
5. `117` 戈壁边缘减少贴边整块感，增加山脚、荒原、绿洲式交错。
6. `105` 东海边界处理成海岸或入海湾，而不是被裁开的蓝块。

验收：

1. 人工查看 PNG 预览，三张图不再有明显断河。
2. 大面积 region 边缘有自然参差，但没有满天星碎片。
3. landmark 与文本语义匹配。
4. `python tools\map_presets\validate_presets.py` 通过。
5. `python tools\map_presets\render_preview.py --all` 生成预览。
6. `python tools\map_presets\export_frontend_previews.py` 更新前端预览 SVG。

已落地第一轮内容：

1. `classic` 的 `106` 已从多段水域调整为连续水系，并保持 `202`、`303` 等特殊 region 连续。
2. `mountain_frontier` 的 `106` 已调整为连续峡河，并补出入海口。
3. `mountain_frontier` 的 `406` 已从 1 格扩为可承载 2x2 landmark 的驻地区域。
4. `island_seas` 已清理部分缺少语义的 1 到 2 格小碎片。
5. 三张地图的 `map.json` 与 `meta.json` 版本已提升到 `2`。
6. 前端地图预览 SVG 已重新导出。
7. `tests/test_map_presets.py` 已增加核心质量回归，锁住大陆/山脉水系连续性和山脉 `406` landmark fit。

已落地第二轮内容：

1. `classic` 的东海 `105` 已进一步雕刻海岸线，北部林地、中部山麓与田垄形成连续岬角和湾口，块状度 warning 已消除。
2. `mountain_frontier` 的 `107` 山脚长直边已由相邻谷地区域轻微咬开，长直边 warning 已消除。
3. 当前质量审计中，断河、无入海口、块状大区、长直边、小碎片和 tiny water / sea component 等结构性 warning 已清零。
4. 三张 PNG 预览与前端 SVG 预览已重新生成，并完成人工预览检查。

当前剩余重点：

1. 当前自动审计剩余项均为 `landmark_near_boundary` 软提示。
2. `island_seas` 因为群岛和小岛语义天然容易贴边，不宜为了消除 warning 机械移动所有 landmark。
3. `classic` 的 `202`、`303` 与 `mountain_frontier` 的 `301`、`303`、`406` 可在后续实机审图时单独判断是否需要移动或扩区。
4. 后续美化可以继续做局部边界雕刻，但应优先保持地理语义、连通性和 landmark 可读性。

### Phase 3：收紧质量门与文档

状态：已落地第一版质量门与前端预览自动映射。

目标：避免以后官方地图再次退化。

任务：

1. 将稳定审计项接入 `validate_presets.py` strict 模式。
   - 基础格式错误继续 hard fail。
   - 已稳定且低误报的质量项可 hard fail。
   - 审美项保留 warning。

2. 更新测试。
   - `tests/test_map_presets.py` 增加关键质量断言。
   - 断言 `classic` / `mountain_frontier` 的 `106` 连续。
   - 断言群岛图没有过多孤立 1 格 sea/water 组件。
   - 断言 map creator 保存尺寸不会退回 `70x50`。

3. 更新文档。
   - `docs/map-design-notes.md` 增加地图质量维护流程。
   - 如 `.cursor/rules/map-system.mdc` 后续变更，需要同步 `AGENTS.md`。

4. 改善前端预览同步。
   - 优先让 `MapPresetPreview.vue` 使用动态映射或生成文件，避免每新增地图手动 import。
   - 如果受 bundler 限制必须静态 import，则由导出脚本同步生成一个 manifest。

已落地内容：

1. `tools/map_presets/validate_presets.py` 已接入 `quality_audit.audit_map_source()`。
2. 除 `landmark_near_boundary` 之外的质量审计项已成为官方地图 hard fail：
   - 断河 / 无入海口。
   - 小碎片 / tiny water / sea component。
   - 大面积 normal region 过度块状。
   - normal region 长直边。
   - landmark 2x2 poor fit。
3. `landmark_near_boundary` 仍保留为软提示，因为群岛、小岛、港口和洞府等语义经常需要贴边，机械 hard fail 容易误伤。
4. `web/src/components/game/panels/system/MapPresetPreview.vue` 已改为通过 `import.meta.glob()` 自动收集 `web/src/assets/map-previews/*.svg`，新增地图预览 SVG 后不再需要手写 import。
5. `tests/test_map_quality_audit.py` 已增加软/硬质量项分层的回归测试。

验收：

1. 地图质量审计已成为官方地图维护流程的一部分。
2. 新增或修改官方地图时，`python tools\map_presets\validate_presets.py` 会阻止客观结构问题进入官方预设。
3. 前端地图预览不会因为忘记手写 import 而漏图。

## 推荐命令

修改地图或地图工具后至少运行：

```powershell
python tools\map_presets\validate_presets.py
python tools\map_presets\render_preview.py --all
python tools\map_presets\export_frontend_previews.py
pytest tests/test_map_presets.py
```

如果修改了地图编辑器：

```powershell
pytest tests/test_map_presets.py
```

如果修改了前端预览组件或地图启动面板：

```powershell
cd web
npm run type-check
npm run test -- --run
```

## 暂不做

1. 不引入随机地图生成。
2. 不引入独立河流图层。
3. 不引入道路图层。
4. 不引入高度、气候、生态模拟。
5. 不引入每格 tile overlay。
6. 不改变三张官方地图共享同一 region roster 的阶段性约定。
7. 不为旧版地图格式增加新的兼容双轨。

## 后续留白

如果未来需要更强地图表达，可以重新设计以下能力：

1. base terrain layer：允许无 region 地貌不止一种。
2. river / road overlay：让河流、道路脱离 region 归属。
3. coast / border autotile：根据邻接关系自动渲染边缘。
4. runtime overlay：战争、灾害、建设改变局部地貌。
5. map editor brush：提供边缘扰动、连通河流、岛屿生成等确定性辅助工具。

这些能力都应在独立 spec 中设计，并重新评估存档、前端渲染、外接控制 API 与测试契约。
