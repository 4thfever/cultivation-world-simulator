# AGENTS.md

本文件是仓库级的 agent 工作说明，目标是把 `.cursor/` 下的规则、技能、命令做统一沉淀，供 Codex/Cursor 等代理在进入仓库后直接读取。

## 1. Codex 自动读取 AGENTS.md 的格式与规则（官方核对）

截至 2026-03-11，Codex 对 AGENTS 指令链的核心行为如下：

1. 文件格式：`AGENTS.md` 是标准 Markdown，没有强制字段。
2. 全局层：先看 `~/.codex/AGENTS.override.md`，不存在再看 `~/.codex/AGENTS.md`。该层只取第一个非空文件。
3. 项目层：从项目根目录走到当前工作目录，逐级查找：
   - `AGENTS.override.md`
   - `AGENTS.md`
   - `project_doc_fallback_filenames` 中配置的备用文件名
   每一层目录最多纳入一个文件。
4. 合并顺序：从根到当前目录拼接，越靠近当前目录优先级越高（后拼接，覆盖前面的语义）。
5. 空文件会被忽略。
6. 有大小上限（默认 `project_doc_max_bytes = 32 KiB`），超过上限后不会继续追加指令。
7. 冲突优先级：系统/开发者/用户消息 > AGENTS.md；更深层目录中的 AGENTS > 上层 AGENTS。

## 2. 本仓库说明范围

1. 本文件作用域：仓库根目录及其全部子目录。
2. 当前仓库暂无更深层级的 `AGENTS.md` 或 `AGENTS.override.md`，因此本文件是项目级主说明。
3. 指令来源：`.cursor/rules/*.mdc`、`.cursor/skills/*/SKILL.md`、`.cursor/commands/*.md`。
4. 补充设计文档：`docs/specs/*.md` 中记录已经落地的重要系统设计；其中“小故事系统”请优先参考 `docs/specs/story-event-system.md`。

## 3. `.cursor/rules` 沉淀

### 3.1 规则索引

| 规则文件 | 作用范围（globs） | 关键约束摘要 |
|---|---|---|
| `.cursor/rules/action-development.mdc` | `src/classes/action/**/*.py`, `src/classes/mutual_action/**/*.py` | 新动作必须补齐 `ACTION_NAME_ID/DESC_ID/REQUIREMENTS_ID/EMOJI/PARAMS`、生命周期方法、注册装饰器、`__init__.py` 导出和测试。 |
| `.cursor/rules/config-architecture.mdc` | `src/config/**/*.py`, `src/server/**/*.py`, `src/utils/config.py`, `src/utils/llm/**/*.py`, `src/sim/save/**/*.py`, `src/sim/load/**/*.py`, `web/src/stores/setting.ts`, `web/src/api/modules/system.ts`, `web/src/api/modules/llm.ts`, `web/src/components/game/panels/system/**/*.vue`, `web/src/App.vue` | 配置分为只读版本配置、`settings.json/secrets.json` 应用设置、`RunConfig` 本局快照；用户数据统一走 data root；前端设置真源是 `/api/settings`；LLM key 不回传前端；存档需保存 `run_config`。 |
| `.cursor/rules/development-phase.mdc` | `*.py`, `*.vue`, `*.ts`, `*.tsx`, `*.json` | 开发阶段：**原则上不要求**向前/向下兼容，以新代码清晰合理为先；若兼容可**零代价**顺带（如一行 `.get` 且不拖结构）可做，**不得**为兼容付出双轨/分支/牺牲主路径可读性。 |
| `.cursor/rules/event-system.mdc` | `src/classes/event.py`, `src/classes/event_storage.py`, `src/systems/**/*.py` | 明确 `is_major/is_story` 语义，准确填写 `related_avatars`，统一由模拟器集中入库，查询走分页。 |
| `.cursor/rules/frontend-sound.mdc` | `web/src/**/*.vue|ts|tsx` | 标准按钮默认自动音效，特殊音效用 `v-sound`，禁音用 `data-no-sound`，仅特殊场景允许 `useAudio` 编程式播放。 |
| `.cursor/rules/frontend-typing-error.mdc` | `web/src/**/*.vue|ts|tsx` | DTO 先更新 `types/api.ts`，映射逻辑放 `api/mappers`，避免 `any` 扩散，错误统一 `appError`，Socket 分发在 `socketMessageRouter`。 |
| `.cursor/rules/frontend.mdc` | `web/src/**/*.{vue,ts,js}` | 后端驱动架构、Store 职责边界、启动状态机集中、Socket 分层、`shallowRef`/长列表性能策略、容器尺寸统一用 `useElementSize()` 等。 |
| `.cursor/rules/i18n-phase1.mdc` | `*.py`, `*.vue`, `*.json`, `*.po` | 当前处于 Phase 1：只改 `zh-CN`，禁止改 `en-US/zh-TW`；因此 locale 对齐测试失败可忽略。 |
| `.cursor/rules/llm-integration.mdc` | `src/utils/llm/**/*.py`, `src/**/*.py` | 统一走 `src.utils.llm.client`，按场景选 `LLMMode`，重试交给底层，异常捕获 `LLMError/ParseError` 并降级。 |
| `.cursor/rules/python-registry.mdc` | `src/classes/**/*.py` | 使用注册装饰器的新类，必须在对应 `__init__.py` 导入，否则注册不生效；同时要补注册测试。 |
| `.cursor/rules/save-load-serialization.mdc` | `src/sim/save/**/*.py`, `src/sim/load/**/*.py`, `src/classes/**/*.py` | 存档只保存 JSON 基础类型，跨对象引用只存 ID；复杂类序列化拆到 Mixin；加载侧以当前模型清晰为准，旧存档迁就服从 `development-phase.mdc`（零代价可 `.get`，不买单不双轨）。 |
| `.cursor/rules/simulator-logic.mdc` | `src/sim/simulator.py`, `src/sim/**/*.py` | 相位优先拆为 `simulator_engine/phases` 中的独立函数，`step()` 只做编排；共享状态走 `SimulationStepContext`；新相位需重排索引；LLM/重计算相位异步化；死亡结算后维护 `living_avatars`；收尾统一走 `finalizer.finalize_step()`。 |
| `.cursor/rules/story-event-system.mdc` | `src/classes/story_event_service.py`, `src/classes/action/**/*.py`, `src/classes/mutual_action/**/*.py`, `src/classes/gathering/**/*.py`, `src/systems/battle.py`, `src/systems/fortune.py`, `static/config.yml`, `tests/**/*.py` | 小故事统一走 `StoryEventService`；先生成基础结果事件，再尝试追加故事；非 gathering 按 `StoryEventKind + game.story.probabilities` 控制，`gathering` 固定 100%；LLM 展开的故事正文统一标记 `is_story=True`。 |
| `.cursor/rules/sect-system.mdc` | `src/classes/core/sect.py`, `src/classes/core/world.py`, `src/classes/sect_decider.py`, `src/sim/managers/sect_manager.py`, `src/systems/sect_decision_context.py`, `src/classes/ranking.py`, `src/server/**/*.py`, `src/systems/sect_relations.py`, `web/src/**/*.{ts,vue}` | 统一宗门领域模型与 API 分层；通过 `SectContext` 管理本局启用宗门；势力快照由 `SectManager` 统一计算；宗门年度思考由 `SectDecider` 每年 1 月生成并写回 `yearly_thinking`，经 detail 暴露给前端；前端 detail 链路必须经过强类型 DTO + mapper。 |
| `.cursor/rules/testing.mdc` | `tests/**/*.py` | 优先复用 `conftest.py` fixtures（`dummy_avatar`/`mock_llm_managers` 等），异步测试加 `@pytest.mark.asyncio`，避免过度设计。 |
| `.cursor/rules/vue-performance.mdc` | `web/src/**/*.vue|ts|tsx` | 大对象必须 `shallowRef`，长列表分页或虚拟滚动，昂贵派生用 `computed`，重构前后保留性能基线对比。 |

### 3.2 执行时应优先遵守的硬约束

1. 新增可注册模块后，必须改对应 `__init__.py`。
2. 动作系统改动必须配套测试，特别是 `can_possibly_start` 分支。
3. 前端大对象和 Pixi 实例禁止深层响应式代理。
4. i18n 开发遵守 Phase 1（只改 `zh-CN`）直到显式进入 Phase 2。
5. 存档与持久化：`save-load-serialization.mdc` 的技术形状仍须遵守；是否迁就旧存档以 `.cursor/rules/development-phase.mdc` 为准——**清晰优先**，兼容仅可在**零代价**时顺带，禁止为兼容增加实质负担。
6. 语言列表的单一真相源是 `static/locales/registry.json`；Python 侧 i18n 工具、校验和新增语言流程应优先读取该文件，不要在脚本中重新写死 `zh-CN/zh-TW/en-US`。
7. 用户设置不得再写入 `static/local_config.yml`；正式真源是用户数据目录中的 `settings.json/secrets.json`，本局参数必须走 `RunConfig` 并随存档保存。
8. 小故事统一通过 `src/classes/story_event_service.py` 生成；业务代码应先产出事实事件，再决定是否追加故事事件。
9. `gathering` 的故事固定为 `100%`，且所有 LLM 展开的故事正文统一使用 `is_story=True`，不要再混用 `is_major=True` 作为故事正文标记。

## 4. `.cursor/skills` 沉淀

| 技能 | 用途 | 关键流程 |
|---|---|---|
| `fill-i18n-phase2` | 进入多语言补全 Phase 2 | 生成缺失报告 -> 补全 `en-US/zh-TW` -> 必要时编译 `.mo` -> 跑 locale 测试 -> 清理报告。 |
| `git-pr` | 创建规范 PR | 从 `main` 拉新分支，标准 commit type，push 后 `gh pr create`，遵守 PR 模板。 |
| `i18n-development` | 日常 i18n 开发 | 在拆分 `.po` 维护条目，避免直接改 `LC_MESSAGES/messages.po`，改完必须 `build_mo.py`。 |
| `spec-interview` | 需求访谈后产出 spec | 多轮提问澄清隐含约束与风险，最后落地到 `docs/specs/<feature>.md`。 |
| `test-validate` | 测试执行参考 | 后端 `pytest`、前端 `npm run test/type-check`、变更类型对应测试策略。 |

## 5. `.cursor/commands` 沉淀

| 命令文件 | 建议命令名 | 功能 |
|---|---|---|
| `.cursor/commands/pack_to_github.md` | `/pack_to_github` | 依次执行 GitHub 打包流程：`pack_github.ps1` -> `compress.ps1` -> `release.ps1`。 |
| `.cursor/commands/pack_to_steam.md` | `/pack_to_steam` | 依次执行 Steam 打包流程：`pack_steam.ps1` -> `upload_steam.ps1`（需人工输密码）。 |
| `.cursor/commands/sync_contributors.md` | `/sync_contributors` | 从 GitHub contributors API 同步仓库贡献者，并自动更新根目录 `CONTRIBUTORS.md`。 |
| `.cursor/commands/sync_readme.md` | `/sync_readme` | 以 `README.md` 为源，按 `static/locales/registry.json` 中需同步语言，更新 `docs/readme/` 下各 `*_README.md`。 |
| `.cursor/commands/update_version.md` | `/update_version` | 打 tag、更新 `static/config.yml` 版本并提交。 |
| `.cursor/commands/sync_agents.md` | `/sync_agents` | 重新扫描 `.cursor` 并更新根目录 `AGENTS.md`（本次新增）。 |

## 6. 测试与验证命令（从技能中提炼）

1. 后端全量测试：`pytest`
2. 前端测试：`cd web && npm run test`
3. 前端类型检查：`cd web && npm run type-check`
4. locale 对齐检查：
   - `pytest tests/test_frontend_locales.py`
   - `pytest tests/test_backend_locales.py`
5. 语言注册表检查：`python tools/i18n/generate_missing_report.py`

## 7. 维护约定

1. 修改 `.cursor/rules`、`.cursor/skills`、`.cursor/commands` 后，建议执行一次 `/sync_agents` 同步本文件。
2. 本文件是“聚合索引 + 执行约束”文档，不替代原文件；细节以原始文件为准。
3. 若后续引入子目录 `AGENTS.md`，请遵循“越近优先”的覆盖策略，并在对应子目录内写局部规则。
4. 若后续新增语言，先更新 `static/locales/registry.json`，再处理目录、脚本与资源骨架；不要先从前端菜单或单个测试文件开始零散修改。
5. 若后续继续调整小故事逻辑，请同步维护 `.cursor/rules/story-event-system.mdc`、`docs/specs/story-event-system.md` 与本文件中的摘要说明。

## 8. 原始来源路径

1. `.cursor/rules/*.mdc`
2. `.cursor/skills/*/SKILL.md`
3. `.cursor/commands/*.md`
4. `docs/specs/story-event-system.md`
