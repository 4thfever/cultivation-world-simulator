---
description: 宗门系统设计与重构约束
globs:
  - src/classes/core/sect.py
  - src/classes/core/world.py
  - src/classes/sect_decider.py
  - src/sim/managers/sect_manager.py
  - src/classes/ranking.py
  - src/server/assemblers/sect_detail.py
  - src/server/main.py
  - src/systems/sect_relations.py
  - src/systems/sect_decision_context.py
  - web/src/types/api.ts
  - web/src/api/mappers/detailMapper.ts
  - web/src/stores/ui.ts
---

# 宗门系统设计与重构规范 (Sect System)

本规则约束“宗门”相关代码的分层、契约与状态模型，避免再次出现领域对象职责过重、接口拼装分散、前后端契约弱化的问题。

## 1. 分层与依赖方向

- **领域层 (`Sect` 等) 只负责状态与规则，不负责 HTTP/API 组装**  
  - `src/classes/core/sect.py` 中的 `Sect`：
    - 只负责：静态配置加载、运行时成员 & 势力状态（含 `magic_stone/total_battle_strength/influence_radius` 等）、基础展示字段（名字、阵营、驻地、功法列表等）。
    - **禁止**：在 `Sect` 内直接 import `src.server.main` 或任何 FastAPI 路由模块。
  - API 详情组装统一走 `src/server/assemblers/sect_detail.py` 中的 `build_sect_detail`：
    - `/api/v1/query/detail?type=sect` 必须通过 assembler 构造完整 DTO，不允许在路由中再散落手写拼装。

- **依赖方向约束**  
  - 允许：`server/assemblers/*` 依赖 `classes/core/*`、`systems/*`。
  - 禁止：`classes/core/*` 反向依赖 `server/*`。

## 2. 宗门状态模型与字段语义

- `Sect` 中字段语义必须清晰区分“静态配置 vs 运行时状态”：
  - 静态/配置相关：
    - `effects / effect_desc`：来自宗门配表与道统合成，用于描述对角色/系统的长期被动加成。
    - `technique_names / techniques`：功法列表。
    - `alignment / member_act_style / headquarter / orthodoxy_id / color` 等基础设定。
  - 运行时状态：
    - `sect_effects / temporary_sect_effects`：宗门经济/加成类运行时效果（`build_sect_detail` 中会合并并生成 `runtime_effect_*` 字段）。
    - `magic_stone / total_battle_strength / influence_radius / is_active`：势力与经济结算相关字段。
    - `periodic_thinking`：宗门周期思考（仅展示用途），由 `SectThinker` 在每年 1 月按配置周期生成 30～100 字短文本，经 `build_sect_detail` 暴露给前端。
    - `members`：运行时成员映射，仅在内存中维护，不参与静态配置。
- 在扩展字段时：
  - **必须**在命名和 docstring 中注明“静态配置 / 运行时状态 / 仅序列化用”三者之一。
  - 若字段属于运行时状态且需要存档，优先放在 save/load 对应 mixin/模块中处理（参考 `save-load-serialization.mdc`）。

## 3. 宗门作用域：World.sect_context 统一入口

- 本局启用宗门的读写必须通过 `World.sect_context` 统一完成：
  - `World` (`src/classes/core/world.py`) 暴露属性：
    - `world.sect_context`：懒加载的 `SectContext` 实例。
    - `SectContext.active_sect_ids`：本局启用且仍标记为 `is_active=True` 的宗门 ID 集合。
    - `SectContext.get_active_sects()`：\*统一入口\*，优先基于 `world.existed_sects` 返回当前局实际挂载的 `Sect` 实例，再结合 `active_sect_ids` 过滤；如无，则回退到全局 `sects_by_id`。
  - 初始化与读档时：
    - 在 `init_game_async` 中确定 `existed_sects` 后，必须调用 `world.sect_context.from_existed_sects(existed_sects)`。
    - 在 `load_game` 中重建 `existed_sects` 后，同步调用 `world.sect_context.from_existed_sects(existed_sects)`。
- **使用约束**：
  - 新代码如需“本局启用宗门集合”，应优先使用 `world.sect_context.get_active_sects()`，避免直接遍历全局 `sects_by_id`。
  - 旧代码中的 `world.existed_sects` 视为兼容层，只读使用，逐步收敛到 `SectContext`。

## 4. 势力计算快照管线 (SectTerritorySnapshot)

- `SectManager` (`src/sim/managers/sect_manager.py`) 是宗门势力与年度结算的唯一入口：
  - 必须通过 `_compute_snapshot()` 产生 `SectTerritorySnapshot`，统一计算：
    - `active_sects`：当前仍存续且激活的宗门列表（来源于 `SectContext`）。
    - `sect_centers`：基于 `SectRegion` 的总部中心坐标。
    - `tile_owners`：每个地图格子被哪些宗门占据。
  - `get_tile_owners()` 与 `update_sects()` **必须复用**该 snapshot，不得各自重复实现“中心点 + 半径 + 曼哈顿菱形枚举”逻辑。
- 关系系统与地图展示：
  - `/api/v1/query/sect-relations` 只能通过 `SectManager.get_tile_owners()` 获取 `(active_sects, tile_owners)` 后，再调用 `compute_sect_relations`，禁止绕过 `SectManager` 自己重新枚举 tile 拥有者。
  - 地图势力图层（前端 `SectInfluenceLayer`）只依赖地图查询接口的宗门颜色与 `/api/v1/query/detail` 的 `influence_radius`，不直接参与势力快照计算。

## 5. 榜单与关系：只看本局 active 宗门

- 榜单 (`RankingManager`, `src/classes/ranking.py`)：
  - 更新接口首选 `update_rankings_with_world(world, living_avatars)`：
    - 角色榜单仍按全服活着的角色计算。
    - 宗门榜单必须通过 `world.sect_context.get_active_sects()` 获取候选宗门，仅对本局启用且存续的宗门进行统计。
  - `Simulator` 与 `/api/v1/query/rankings` 调用时必须使用 `update_rankings_with_world`，而不是裸用 `update_rankings` + 全局 `sects_by_id`。

- 宗门关系 (`compute_sect_relations`, `src/systems/sect_relations.py`)：
  - 输入 `sects` 参数应来源于 `SectManager.get_tile_owners()` 的 `active_sects`，不允许在调用处再从全局池筛选。
  - `tile_owners` 参数必须来自统一的势力快照，避免规则漂移。

## 6. `/api/v1/query/detail` 接口契约与前端 DTO

- 后端 `/api/v1/query/detail` (`src/server/main.py`)：
  - 目标解析逻辑固定：`type=avatar|region|sect` + `id`，解析出 `target` 对象。
  - `type="sect"` 分支必须调用 `build_sect_detail(sect, world, language_manager)`：
    - assembler 内负责：
      - 调用 `sect.get_structured_info()` 获取领域层基础信息。
      - 合并 `sect_effects` 与 `temporary_sect_effects`，生成 `runtime_effect_desc`、`runtime_extra_income_per_tile`、`runtime_effect_items` 等前端字段。
      - 将 `sect.periodic_thinking` 写入 `periodic_thinking` 字段供前端宗门 info panel 展示。
    - 路由层不再手写追加 runtime 字段。
- 前端 DTO (`web/src/types/api.ts`)：
  - `DetailResponseDTO` **不得再是** `Record<string, unknown>`。
  - 当前阶段（P0）直接以领域模型为 DTO：
    - `type AvatarDetailDTO = AvatarDetail`
    - `type RegionDetailDTO = RegionDetail`
    - `type SectDetailDTO = SectDetail`
    - `type DetailResponseDTO = AvatarDetailDTO | RegionDetailDTO | SectDetailDTO`
  - 如后端未来引入 `type` 字段或拆分 DTO 结构，需先更新 `types/api.ts`，再更新 mapper。

## 7. 前端 detail mapper 与 Store 使用方式

- Mapper (`web/src/api/mappers/detailMapper.ts`)：
  - 必须存在 `mapDetailDTOToDomain(dto, targetType)`，负责将 `/api/v1/query/detail` 的响应基于 `Selection.type` 收敛到：
    - `AvatarDetail` / `RegionDetail` / `SectDetail`。
  - 新增字段时，优先在 DTO 类型上补充，再在 mapper 中做兼容（默认值、类型守卫等），禁止直接在组件里读裸 JSON。

- UI Store (`web/src/stores/ui.ts`)：
  - `detailData` 类型固定为 `AvatarDetail | RegionDetail | SectDetail | null`，并存放于 `shallowRef` 中。
  - `refreshDetail()` 在写入 `detailData` 时：
    - 必须调用 mapper：`detailData.value = mapDetailDTOToDomain(raw, target.type)`。
    - **禁止**再使用 `as unknown as AvatarDetail | RegionDetail | SectDetail` 之类的双重断言。

## 8. 宗门周期决策与周期思考

- **宗门周期决策 (`SectDecider`)**：
  - **入口**：由年度维护流程 `src/sim/simulator_engine/phases/annual.py` 调度，仅在每年 1 月检查是否到达配置周期。
  - **输入**：由 `build_sect_decision_context(sect, world, event_storage)` 得到 `SectDecisionContext`。
  - **输出**：执行宗门行政动作，并生成“本轮宗门决策”摘要文本，写回 `sect.last_decision_summary`，同时写入事件流。
  - **实现**：`src/classes/sect_decider.py` 中 `SectDecider.decide(sect, decision_context, world)`；提示词模板位于 `static/locales/{lang}/templates/sect_decider.txt`，任务名 `sect_decider`。

- **宗门周期思考 (`SectThinker`)**：
  - **入口**：由年度维护流程 `src/sim/simulator_engine/phases/annual.py` 调度，仅在每年 1 月检查是否到达 `thinking_interval_years` 配置周期，且排在宗门年度结算与宗门周期决策之后。
  - **输入**：由 `build_sect_decision_context(sect, world, event_storage)` 得到 `SectDecisionContext`（宗门基础信息、战力/势力/经济、宗门关系、与本宗相关的近期历史事件），并参考 `sect.last_decision_summary`。
  - **输出**：30～100 字、以宗门口吻的“形势判断与方向思考”文本，写回 `sect.periodic_thinking`，并生成一条 `Event(related_sects=[sect.id])` 写入事件流。
  - **实现**：`src/classes/sect_thinker.py` 中 `SectThinker.think(sect, decision_context, world, decision_summary=...)`，LLM 不可用时使用固定兜底文案。提示词模板按语言放在 `static/locales/{lang}/templates/sect_thinker.txt`，任务名 `sect_thinker`。
  - **展示**：`build_sect_detail` 已把 `periodic_thinking` 写入详情 DTO，前端宗门 info panel 可直接使用该字段。

## 9. 重构与扩展时的检查清单

1. 新增宗门相关字段时，是否明确标注“静态/运行时/序列化用途”？  
2. 涉及“本局启用宗门集合”的新逻辑，是否通过 `World.sect_context.get_active_sects()` 访问？  
3. 涉及势力范围（tile 归属）的逻辑，是否通过 `SectManager` 的势力快照复用计算？  
4. 新增 `/api/v1/query/detail` 字段时，是否同时更新了：assembler → DTO 类型 → detailMapper → UI 组件？  
5. 修改宗门榜或关系算法时，是否仍然只作用于本局 active 宗门，而非全局 `sects_by_id`？  
6. 修改宗门周期思考逻辑时，是否仍使用 `SectDecisionContext` 作为唯一输入、并通过年度维护流程在每年 1 月按配置周期调度？  

