# 前端设计与架构修复计划

本文档记录 2026-04 对当前前端设计、架构和代码的评审结论，以及后续分阶段修复计划。目标不是重做前端，而是在现有方向上把已经出现的运行风险、性能隐患和架构债务逐步收口。

## 1. 背景

当前前端已经具备较清晰的基本分层：

1. `api/modules` 承接后端接口。
2. `api/mappers` 负责 DTO 到前端领域模型的转换。
3. Pinia stores 按 `world/avatar/map/event/sect/roleplay/settings` 等领域拆分。
4. 根层已经采用 `scene + overlay` 的渲染语义。
5. Pixi 地图、状态栏、系统菜单、小故事/事件面板和角色扮演 Dock 都已形成相对稳定的功能面。

但随着功能增长，以下问题开始显性化：

1. Pixi `Texture` 等对象存在进入 Vue 深层响应式代理路径的风险。
2. 部分静态资源路径仍硬编码为根路径，子路径部署或打包运行时可能失效。
3. 事件面板对长事件流存在重复计算和深层监听隐患。
4. 部分面板重复持有相同请求状态，缺少竞态保护。
5. `worldStore` 仍承担过多跨领域总线职责。
6. `StatusBar` 承载过多 modal 编排。
7. 大型单文件组件继续膨胀，维护成本上升。
8. 少量多语言文案仍引用旧配置路径。

## 2. 总体目标

本轮修复的目标是“稳住底盘、减小热区、让后续功能更容易接上”：

1. 消除已知部署风险和 Pixi 响应式风险。
2. 降低事件流、地图资源和详情面板的性能压力。
3. 把重复的请求/展示状态抽成可复用 store 或 composable。
4. 收敛 store 职责，让组件依赖更准确的领域 store。
5. 减少大型组件继续膨胀。
6. 保持现有视觉风格和交互习惯，不做无关的大改版。

## 3. 非目标

本计划不包含以下内容：

1. 不重做整套 UI 视觉主题。
2. 不引入路由系统，除非后续另有明确需求。
3. 不把所有组件请求一次性迁入 store。
4. 不重写 Pixi 地图渲染架构。
5. 不追求兼容已经废弃的前端内部 API 使用方式。
6. 不补全正式多语言 Phase 2；本计划只修正已发现的陈旧文案。

## 4. 修复原则

### 4.1 清晰优先

当前仍处于开发阶段。对于明显错误的旧路径、旧代理、旧职责，不新增双轨兼容；只有零成本兼容可以顺带保留。

### 4.2 前端状态边界

1. 共享领域状态进入 store。
2. 单次表单草稿可以留在组件内。
3. 重复请求流程优先抽 composable。
4. 会被多个入口打开的 modal 数据优先抽 store 或 composable。

### 4.3 Pixi 对象边界

Pixi 实例、纹理、ticker、viewport 等对象不得进入 Vue 深层响应式代理。优先使用：

1. 非响应式 `Map` / 模块级缓存。
2. `shallowRef`。
3. `markRaw`。
4. 轻量版本号触发渲染刷新。

### 4.4 静态资源路径

前端自带资源必须统一走 `BASE_URL` helper 或模块导入。游戏运行时资源若由后端 `/assets` 提供，也必须通过统一 helper 生成，不能在业务代码中散落根路径字符串。

## 5. 分阶段计划

### 阶段一：修复硬风险

#### 5.1 Pixi 纹理缓存硬化

状态：

- [x] 已完成

涉及文件：

- `web/src/components/game/composables/useTextures.ts`
- `web/src/components/game/MapLayer.vue`
- `web/src/components/game/AnimatedAvatar.vue`
- `web/src/__tests__/components/game/useTextures*.test.ts` 或相邻测试

计划：

1. 将 `textures` 从深层 `ref<Record<string, Texture>>` 改为安全结构。
2. 写入 Pixi `Texture` 时使用 `markRaw` 或非响应式缓存。
3. 若使用非响应式缓存，则暴露 `textureVersion` 或只读查询方法。
4. 保持 `getTileTexture()`、`loadBaseTextures()`、`preloadRegionTextures()` 的调用语义稳定。

验收：

1. Pixi `Texture` 不再被 Vue 深层代理。
2. 地图、头像、宗门、城市、云层资源正常加载。
3. 现有地图与纹理测试通过。

#### 5.2 资源路径统一

状态：

- [x] 已完成

涉及文件：

- `web/src/utils/assetUrls.ts`
- `web/src/components/game/composables/useTextures.ts`
- `web/src/composables/useAudio.ts`
- `web/src/composables/useBgm.ts`
- `web/src/components/SplashLayer.vue`
- `web/src/__tests__/utils/assetUrls.test.ts`

计划：

1. 明确两个 helper：
   - 前端 public 资源：走 `withBasePublicPath()`。
   - 后端游戏资源：走 `getGameAssetUrl()`。
2. `getGameAssetUrl()` 不再直接散落业务语义，至少集中处理 `/assets` 前缀。
3. `useTextures.ts` 内所有 `/assets/...` 字符串改为 helper。
4. 测试覆盖 `BASE_URL` 非根路径时的 public 资源。
5. 对后端 `/assets` 代理路径保留明确注释，避免与 Vite build `assetsDir: web_static` 混淆。

验收：

1. `rg "/assets/" web/src` 除 helper、测试和必要文档外不再出现业务硬编码。
2. `npm run build` 后前端自带资源路径正确。
3. dev server 代理 `/assets` 仍可加载后端游戏资源。

#### 5.3 陈旧配置文案修正

状态：

- [x] 已完成

涉及文件：

- `web/src/locales/en-US/llm.json`
- `web/src/locales/zh-TW/llm.json`
- 必要时同步 `ja-JP`、`vi-VN`

计划：

1. 将 `static/local_config.yml` 相关说明替换为用户数据目录下 `settings.json/secrets.json`。
2. 保持 `zh-CN` 当前语义为基准。
3. 不直接修改 `.po` 合并产物。

验收：

1. 前端文案不再出现 `static/local_config.yml`。
2. locale 测试通过。

### 阶段二：性能和重复逻辑

#### 5.4 事件面板性能收口

状态：

- [x] 已完成

涉及文件：

- `web/src/components/game/panels/EventPanel.vue`
- `web/src/components/game/EventStreamList.vue`
- `web/src/utils/eventHelper.ts`
- `web/src/__tests__/components/game/panels/EventPanel.test.ts`
- `web/src/__tests__/utils/eventHelper.test.ts`

计划：

1. 移除对事件列表的 deep watcher。
2. 自动滚动逻辑改为监听数组引用、长度或最后一个事件 id。
3. 为事件 tokenization 增加缓存，缓存 key 至少包含：
   - `event.id`
   - `event.content` 或 `event.text`
   - `event.renderKey`
   - `event.renderParams`
   - 当前 locale
4. `EventStreamList` 保持展示组件，不在模板中重复触发重计算。
5. 若事件规模继续增长，再独立评估虚拟滚动。

验收：

1. 切换筛选、实时 tick、新事件追加、向上加载更多行为不变。
2. 长列表刷新时不再 deep traverse 全事件对象。
3. 事件中的角色/宗门点击仍能打开对应详情。

#### 5.5 逝者记录逻辑抽取

状态：

- [x] 已完成

涉及文件：

- `web/src/components/game/panels/AvatarOverviewModal.vue`
- `web/src/components/game/panels/DeceasedModal.vue`
- 新增 `web/src/composables/useDeceasedRecords.ts` 或 `web/src/stores/deceased.ts`
- 对应测试

计划：

1. 抽出逝者列表、选中记录、记录事件、loading 状态。
2. `fetchDeceased()`、`selectRecord()`、`fetchEvents()`、`backToList()` 统一复用。
3. 使用 request id 或 `AbortController` 防止旧响应覆盖新状态。
4. 保留两个入口的 UI 差异，不强行合并 modal。

验收：

1. 两个入口行为保持一致。
2. 快速切换记录时只接受最新请求结果。
3. 关闭 modal 后旧请求不会污染下一次打开状态。

#### 5.6 组件直连 API 的边界整理

状态：

- [x] 已完成当前收口

优先处理范围：

- [x] deceased 相关
- [x] rankings / tournament / time overview / sect relations
- [x] avatar create / delete / adjust

计划：

1. 共享查询逻辑进 store 或 composable。
2. 一次性表单提交可以留在组件内。
3. 对重复出现的 loading/error/message 模式抽小型 helper，而不是抽大型框架。

验收：

1. 重复请求逻辑减少。
2. 组件中仍保留清晰的 UI 草稿状态。
3. 错误处理统一走 `appError` 或 UI message，不新增裸 `console.log`。

### 阶段三：架构职责收敛

#### 5.7 `worldStore` 去总线化

状态：

- [x] 已完成生产使用点迁移

涉及文件：

- `web/src/stores/world.ts`
- 仍依赖 `worldStore` deprecated proxies 的组件

计划：

1. 扫描 `worldStore.avatars`、`worldStore.avatarList`、`worldStore.mapData`、`worldStore.events`、`worldStore.loadEvents` 等代理使用点。
2. 分批改为直接依赖具体 store：
   - `useAvatarStore`
   - `useMapStore`
   - `useEventStore`
   - `useSectStore`
3. `worldStore` 最终只保留：
   - 年月与开局时间
   - 当前天象和秘境
   - 初始化快照编排
   - tick 分发
   - reset 编排

验收：

1. deprecated proxies 生产使用点已清空；兼容代理暂留在 `worldStore`，用于测试与过渡期。
2. 初始化、读档、重置、语言切换后的数据刷新行为保持正常。
3. store 间循环依赖不新增。

#### 5.8 StatusBar modal 编排收口

状态：

- [x] 已完成

涉及文件：

- `web/src/components/layout/StatusBar.vue`
- 新增 `web/src/components/layout/StatusBarPanels.vue` 或 `web/src/composables/useStatusBarPanels.ts`

计划：

1. 状态栏入口配置化，统一描述：
   - key
   - label
   - icon
   - color
   - visible 条件
   - open 行为
2. modal `showXxx` 状态迁出 `StatusBar.vue`。
3. `StatusBar` 保持顶部信息和入口渲染职责。

验收：

1. 新增状态栏入口无需继续修改大量模板。
2. 现有所有 modal 打开/关闭行为不变。
3. 状态栏在窄屏下不出现明显文本重叠。

#### 5.9 大型组件拆分

状态：

- [x] 已完成当前收口

优先级：

1. `web/src/components/game/panels/info/AvatarDetail.vue`（保留 UI 容器，调整面板逻辑已抽）
2. `web/src/components/game/panels/system/LLMConfigPanel.vue`（后续）
3. `web/src/components/game/panels/info/components/AvatarAdjustPanel.vue`（已抽 `useAvatarAdjustmentPanel`）
4. `web/src/components/game/panels/system/SaveLoadPanel.vue`（已抽 `useSaveLoadPanel`）
5. `web/src/components/game/panels/system/CreateAvatarPanel.vue`（已抽 `useCreateAvatarPanel`）
6. `web/src/components/game/panels/system/DeleteAvatarPanel.vue`（已抽 `useDeleteAvatarPanel`）
7. `web/src/components/layout/StatusBar.vue`（已抽 `StatusBarPanels`）

计划：

1. 按真实 UI 区域拆，不先抽过度通用组件。
2. 表单状态和提交流程可抽 composable。
3. 可复用视觉结构抽轻量组件或 CSS class。
4. 每次拆分保持行为不变，并补/保留对应组件测试。

验收：

1. 单文件行数和职责降低。
2. 测试覆盖不下降。
3. 不引入新的全局样式污染。

### 阶段四：体验一致性

#### 5.10 交互音效一致性

状态：

- [x] 已完成

涉及文件：

- `web/src/main.ts`
- `web/src/directives/vSound.ts`
- 各按钮和可点击元素

计划：

1. 明确约定：
   - 普通按钮走全局 click。
   - 特殊语义使用 `v-sound:open/select/cancel`。
   - 禁音元素使用 `data-no-sound`。
2. 扫描高频交互元素，避免重复播放或漏播。
3. `vSound` 解绑时应清理监听器，避免极端挂载/卸载场景遗留。

验收：

1. 系统菜单、状态栏、详情面板、角色扮演 Dock 的主要交互音效一致。
2. 不出现一次点击播放两次默认音效的问题。

#### 5.11 样式 token 和窄屏检查

状态：

- [x] 已完成当前收口

涉及范围：

- 状态栏
- 系统菜单
- 事件面板
- 存档面板
- 角色扮演 Dock
- 信息详情面板

计划：

1. 收敛常用 CSS 变量：
   - panel border
   - muted text
   - section title
   - danger/success/accent
   - icon mask
2. 检查按钮文字、状态栏入口、筛选器在窄屏下是否溢出或重叠。
3. 不做完整响应式重设计，只修明显破版点。

验收：

1. 主要面板视觉保持一致。
2. 常见桌面宽度和较窄窗口下不出现明显文本重叠。

## 6. 建议 PR 切分

建议按以下顺序落地：

- [x] PR 1：Pixi 纹理缓存硬化 + 资源路径统一。
- [x] PR 2：陈旧配置文案修正 + locale 测试。
- [x] PR 3：事件面板性能优化。
- [x] PR 4：逝者记录 composable/store 抽取。
- [x] PR 5：`worldStore` deprecated proxies 迁移。
- [x] PR 6：StatusBar modal 编排收口。
- [x] PR 7：大型面板拆分。
- [x] PR 8：音效一致性和窄屏 polish。

其中 PR 1 是最高优先级，因为它直接影响部署可靠性和 Pixi 渲染稳定性。

## 7. 验证命令

基础验证：

```bash
cd web
npm run type-check
npm run test
```

资源路径和构建验证：

```bash
cd web
npm run build
```

涉及 locale 文案时：

```bash
pytest tests/test_frontend_locales.py
```

涉及地图/Pixi 时，需要额外手动验证：

1. 地图瓦片加载正常。
2. 水面动画正常。
3. 角色头像正常。
4. 宗门和城市贴图正常。
5. 云层、BGM、SFX 正常。

## 8. 风险与注意事项

1. `useTextures` 改动容易影响 Pixi 渲染，必须小步改并保留现有 API 形状。
2. 资源路径不能简单全部改成 `BASE_URL`，因为后端游戏资源和前端 public 资源来源不同。
3. 事件面板缓存必须考虑 locale 变化，否则切换语言后可能显示旧文本。
4. `worldStore` 去总线化时要特别注意初始化、读档、重置、语言切换四条链路。
5. 大组件拆分不要顺手重做样式，否则 review 面积会失控。
6. 音效全局监听和 `v-sound` 的职责要保持清楚，避免重复播放。

## 9. 当前结论

前端当前不是需要推倒重写的状态。已有分层和测试基础可继续沿用。本计划的核心是把已经出现的几个高风险点及时修掉，同时把重复逻辑和过大的组件慢慢拆开，避免后续角色扮演、外接控制 API、更多系统面板继续叠上来后变得难以维护。
