# 前端质量与重构两阶段计划

本文档记录一次前端代码审查后的重构计划，目标不是重写前端，而是把已经形成的 API / store / composable / 展示组件分层继续收紧，优先处理真实风险，再清理长期维护负担。

## 1. 背景与目标

当前前端整体已经具备较好的基础结构：

- API 已按模块拆分，并逐步统一到 `/api/v1/query/*` 与 `/api/v1/command/*`。
- 部分复杂面板已经下沉到 composable，例如 `useAvatarDetailPanel`、`useLlmConfigPanel`、`useWorldOverviewData`。
- 大型 store 数据多数已经使用 `shallowRef`，避免深层响应式代理带来的性能开销。
- 状态栏、系统菜单、角色扮演、地图渲染等关键路径都有测试覆盖。
- 系统级图标基本统一到 `web/src/assets/icons/ui/lucide/`。

但也存在一些会持续累积维护成本的问题：

1. HTTP 请求层的 timeout 与外部 `AbortSignal` 组合语义不清晰。
2. Pixi 地图重渲染时只移除 display object，未显式销毁旧对象。
3. 全局音效监听的注释与实际事件捕获策略不一致。
4. `worldStore` 仍保留一批跨 store 的 deprecated proxy，边界容易重新糊住。
5. 状态栏弹窗入口由多个 boolean 与 `else if` 维护，新增入口时重复成本高。
6. 若干展示组件仍过大，尤其是 `AvatarDetail.vue`、`LLMConfigPanel.vue`。

本计划分为两个 phase：

- Phase 1：优先处理低风险、高确定性的质量问题。
- Phase 2：再做结构性瘦身与边界清理。

## 2. 设计原则

### 2.1 不做大爆炸重构

前端现有分层已经可用，本计划不要求重新设计框架、替换状态管理或改 UI 库。

每个改动应保持：

- 范围小；
- 行为可测试；
- 能单独提交；
- 不与新功能开发强耦合。

### 2.2 优先修真实风险，再整理审美问题

Phase 1 优先处理可能导致错误行为、资源泄漏或误导维护者的问题。

例如：

- 请求超时实际不生效；
- abort 错误被错误识别为 timeout；
- Pixi 对象未销毁；
- 注释与代码行为相反。

单纯“看起来不够漂亮”的结构拆分放到 Phase 2。

### 2.3 保持现有前端架构方向

继续遵守当前仓库规则：

- 后端驱动 UI，前端不硬编码后端可本地化的业务选项。
- DTO 先更新 `web/src/types/api.ts`，映射逻辑放到 `web/src/api/mappers/`。
- 大对象、Pixi 对象、长列表优先避免深层响应式代理。
- 懒加载弹窗若依赖 `show` 触发请求，watcher 必须 `{ immediate: true }`。
- 前端公共资源路径不写死站点根路径，使用模块导入或 `BASE_URL` helper。

## 3. Phase 1：质量修复与小范围收口

Phase 1 的目标是修掉“现在就可能误导或出错”的点，尽量不碰大规模组件拆分。

### 3.1 修正 HTTP timeout 与 AbortSignal 语义

涉及文件：

- `web/src/api/http.ts`
- `web/src/__tests__/api/http.test.ts`

当前问题：

`request()` 内部总是创建 `AbortController` 与 timeout：

```ts
const controller = new AbortController();
const timeout = globalThis.setTimeout(() => controller.abort(), timeoutMs);
```

但实际传给 `fetch` 的 signal 是：

```ts
signal: requestOptions.signal ?? options.signal ?? controller.signal
```

这会导致：

1. 如果调用方传入外部 `signal`，内部 timeout abort 的 controller 没有被 `fetch` 使用，超时不生效。
2. 如果外部 `signal` 触发 abort，当前 catch 会统一抛出 `Request timed out after ...`，错误信息不准确。

建议实现：

- 明确区分 timeout abort 与 caller abort。
- 可选方案 A：使用组合 signal，将外部 signal 与 timeout signal 合并。
- 可选方案 B：若传入外部 signal，则监听外部 abort，并由内部 controller 统一 abort，同时记录 abort reason。

验收标准：

1. 未传外部 signal 时，请求超过 timeout 后抛出 `ApiError(408, ...)`。
2. 传入外部 signal 时，timeout 仍然生效。
3. 外部 signal 主动 abort 时，不应误报为 timeout。
4. timeout 清理必须稳定执行，不留下悬挂 timer。

测试建议：

- 使用 fake timers 覆盖 timeout。
- 覆盖 caller abort。
- 覆盖 caller signal + timeout 的组合场景。

### 3.2 显式销毁 Pixi 地图旧对象

涉及文件：

- `web/src/components/game/composables/useMapLayerRenderer.ts`
- `web/src/__tests__/components/game/MapLayer.test.ts` 或相关 Pixi renderer 测试

当前问题：

`renderMap()` 中使用：

```ts
mapContainer.value.removeChildren()
```

这只会把 display object 从容器移除，不会销毁旧的 `Sprite`、`Graphics`、`TilingSprite`。

建议实现：

- 新增内部函数 `clearMapContainer()`。
- 在重渲染前：
  - 停止并销毁水面 ticker；
  - 移除旧 children；
  - 对移除的 display object 调用 `destroy({ children: true })`。
- 不销毁共享 texture，避免影响 `useTextures()` 的全局纹理缓存。
- 清理 `seaLayer`、`waterLayer` 引用，避免旧对象残留。

验收标准：

1. 地图重复渲染时旧 display object 会被销毁。
2. 共享 texture 不被销毁。
3. 重渲染后地图仍正常显示。
4. 离开地图组件时 ticker 被停止并销毁。

测试建议：

- mock Pixi display object 的 `destroy()`，验证重复 `renderMap()` 时会调用。
- 保留现有地图组件渲染测试。

### 3.3 收口全局音效点击监听

涉及文件：

- `web/src/main.ts`
- 可选新增 `web/src/utils/globalSound.ts`
- `web/src/directives/vSound.ts`
- `web/src/__tests__/directives/vSound.test.ts`
- 可选新增全局音效测试

当前问题：

`setupGlobalSound()` 实际使用 `{ capture: true }`，但注释中仍在说明“默认冒泡阶段监听是合理的”，代码和注释表达冲突。

建议实现：

- 将全局音效监听从 `main.ts` 抽到单独模块，例如 `setupGlobalSound(appRoot?)`。
- 删除过时注释，只保留当前策略的短说明。
- 明确策略二选一：
  - 若使用 capture：目标是即使组件阻止冒泡也能播放 UI 声音。
  - 若使用 bubble：目标是尽量只为最终有效点击播放声音。
- 继续遵守：
  - `data-no-sound` 禁用；
  - `data-has-sound` 避免与 `v-sound` 重复；
  - disabled button 不播放。

验收标准：

1. 默认按钮点击仍播放 click 音效。
2. `v-sound` 绑定的元素不重复播放。
3. `data-no-sound` 禁用播放。
4. 注释与实际事件阶段一致。

### 3.4 修整 `showClosedMessage()` 的直接 HTML 写入

涉及文件：

- `web/src/App.vue`

当前问题：

退出兜底路径中直接使用：

```ts
document.body.innerHTML = `...${t('game.controls.closed_msg')}...`
```

该路径风险较低，但在 Vue 应用中直接拼接 HTML 不够清晰。

建议实现：

- 可选方案 A：用 `document.createElement()` 与 `textContent` 构建兜底关闭页。
- 可选方案 B：增加一个极简 `closed` 状态，由 Vue template 渲染关闭页。

验收标准：

1. 退出兜底仍显示关闭提示。
2. 不再拼接包含翻译文本的 HTML 字符串。

### 3.5 调整少量高噪声模板表达式

涉及文件：

- `web/src/components/game/panels/info/AvatarDetail.vue`
- `web/src/composables/useAvatarDetailPanel.ts`

当前问题：

模板中存在较长三元表达式，例如头像调整面板的 `current-item`：

```vue
:current-item="adjustCategory === 'technique' ? data.technique ?? null : adjustCategory === 'weapon' ? data.weapon ?? null : adjustCategory === 'auxiliary' ? data.auxiliary ?? null : adjustCategory === 'goldfinger' ? data.goldfinger ?? null : null"
```

建议实现：

- 在 composable 或组件 script 中新增 computed：
  - `currentAdjustItem`
  - `currentAdjustPersonas`
- 模板只绑定 computed。

验收标准：

1. 行为不变。
2. 模板不再承载复杂选择表达式。

## 4. Phase 2：结构性重构与边界清理

Phase 2 的目标是减少长期维护负担，改动范围比 Phase 1 大，适合分多个小 PR 逐步落地。

### 4.1 移除 `worldStore` deprecated proxies

涉及文件：

- `web/src/stores/world.ts`
- 依赖 `worldStore` 代理字段的组件、store、测试

当前问题：

`worldStore` 中保留了跨 store 代理：

- `avatars`
- `avatarList`
- `mapData`
- `regions`
- `renderConfig`
- `events`
- `eventsCursor`
- `eventsHasMore`
- `eventsLoading`
- `eventsFilter`
- `loadEvents`
- `loadMoreEvents`
- `resetEvents`

这些代理会让新代码难以判断应该依赖 `worldStore` 还是具体 store。

建议迁移方向：

- 角色数据统一依赖 `useAvatarStore()`。
- 地图数据统一依赖 `useMapStore()`。
- 事件数据统一依赖 `useEventStore()`。
- `worldStore` 只保留世界时间、天地异象、秘境活动、本局初始化/reset 编排等真正 world-level 职责。

推荐步骤：

1. 使用 `rg "worldStore\\.(avatars|avatarList|mapData|regions|renderConfig|events|eventsCursor|eventsHasMore|eventsLoading|eventsFilter|loadEvents|loadMoreEvents|resetEvents)" web/src` 找调用点。
2. 每次迁移一类 proxy，补或更新对应测试。
3. 调用点清零后删除 proxy 与注释。

验收标准：

1. `worldStore` 不再导出 deprecated proxies。
2. 组件直接依赖职责对应的 store。
3. 现有 world / map / event / avatar store 测试通过。

### 4.2 将状态栏弹窗改为 registry 驱动

涉及文件：

- `web/src/components/layout/StatusBarPanels.vue`
- `web/src/components/layout/StatusBar.vue`
- 状态栏弹窗相关测试

当前问题：

状态栏弹窗目前使用多个 boolean：

- `showTimeOverviewModal`
- `showWorldInfoModal`
- `showRankingModal`
- `showTournamentModal`
- `showSectRelationsModal`
- `showMortalOverviewModal`
- `showDynastyOverviewModal`
- `showHiddenDomainModal`
- `showPhenomenonSelector`
- `showAvatarOverviewModal`
- `showWorldSecretModal`

并通过一串 `else if` 打开弹窗。新增入口时需要改多处。

建议实现：

- 使用 `activePanel: Ref<StatusBarPanelKey | null>` 表示当前弹窗。
- 建立 panel registry，记录：
  - key；
  - component；
  - 是否 async；
  - 打开前置逻辑，例如 avatar overview 首次打开前刷新 overview；
  - 可选 props。
- template 通过 registry 渲染当前 panel。

注意事项：

- 仍要保留懒加载收益。
- 依赖 `show` 触发请求的弹窗，watcher 必须继续 `{ immediate: true }`。
- 若未来允许多个弹窗同时打开，再单独设计 stack，不在本次顺手实现。

验收标准：

1. 状态栏入口行为不变。
2. 每个弹窗仍可正常打开、关闭、再次打开。
3. 首次挂载 `show=true` 的弹窗仍会请求数据。
4. 新增弹窗入口只需扩展 registry，而不是新增一组 boolean + 分支。

### 4.3 拆分 `AvatarDetail.vue` 展示层

涉及文件：

- `web/src/components/game/panels/info/AvatarDetail.vue`
- 可新增 `web/src/components/game/panels/info/avatar-detail/*`
- `web/src/composables/useAvatarDetailPanel.ts`
- `web/src/__tests__/components/game/panels/info/AvatarDetail.test.ts`

当前问题：

`AvatarDetail.vue` 约 900 行，虽然业务逻辑已下沉到 composable，但模板和 scoped CSS 仍然过大。

建议拆分为展示子组件：

- `AvatarDetailHeader.vue`
- `AvatarObjectivesBlock.vue`
- `AvatarStatsGrid.vue`
- `AvatarEquipmentSection.vue`
- `AvatarRelationsSection.vue`
- `AvatarEffectsSection.vue`
- `AvatarObjectiveModal.vue`

拆分原则：

- 子组件尽量接收明确 props 与 emit，不直接重新读 store。
- 复杂派生仍放在 `useAvatarDetailPanel` 或专用 composable。
- 不在拆分时改变 DTO 结构。
- 不在拆分时重写样式体系，只搬迁 scoped CSS。

验收标准：

1. `AvatarDetail.vue` 成为编排层，显著减少模板体积。
2. 现有 avatar detail 测试继续通过。
3. 点击详情、跳转角色/宗门、调整装备、设置目标、头像面板、扮演入口行为不变。

### 4.4 拆分 `LLMConfigPanel.vue` 展示层

涉及文件：

- `web/src/components/game/panels/system/LLMConfigPanel.vue`
- 可新增 `web/src/components/game/panels/system/llm-config/*`
- `web/src/composables/useLlmConfigPanel.ts`
- `web/src/__tests__/components/game/panels/system/LLMConfigPanel.test.ts`

当前问题：

`LLMConfigPanel.vue` 约 800 行，模板与 help modal 内容较重。

建议拆分为展示子组件：

- `LlmPresetSection.vue`
- `LlmApiConfigSection.vue`
- `LlmModelSection.vue`
- `LlmModeSection.vue`
- `LlmHelpModal.vue`
- `LlmConfigActions.vue`

拆分原则：

- `useLlmConfigPanel` 继续作为业务状态真源。
- 子组件只处理展示与局部输入事件。
- API key 不回传、不泄漏的既有契约保持不变。
- 外部链接、模型名称等用户可见文本仍走 i18n 或既有配置。

验收标准：

1. `LLMConfigPanel.vue` 成为编排层。
2. 保存、测试、清空已保存 key、预设填充行为不变。
3. LLM 配置测试继续通过。

### 4.5 拆分 world overview loading 状态

涉及文件：

- `web/src/composables/useWorldOverviewData.ts`
- 使用 rankings / relations 的弹窗和测试

当前问题：

`useWorldOverviewData()` 使用一个 `loading` 同时表示 rankings 与 sect relations 请求状态。如果同一调用者并发触发多个请求，先完成的请求可能提前把 loading 置为 false。

建议实现：

- 拆为：
  - `rankingsLoading`
  - `relationsLoading`
  - `loading = computed(() => rankingsLoading.value || relationsLoading.value)`
- 或者让每个弹窗使用更专用的 composable：
  - `useRankingsData`
  - `useSectRelationsData`

验收标准：

1. 并发请求时 loading 不会提前消失。
2. 单请求调用方行为不变。

## 5. 非目标

本计划不包含：

1. 不替换 Vue / Pinia / Naive UI / Pixi。
2. 不重做 UI 视觉风格。
3. 不改 API 命名空间或后端接口契约。
4. 不顺手做正式多语言补全。
5. 不重构角色扮演业务语义。
6. 不为旧前端内部调用保留额外兼容层；清晰迁移优先。

## 6. 测试与验证

Phase 1 建议至少运行：

```powershell
cd web
npm run test -- http
npm run test -- MapLayer
npm run test -- vSound
npm run type-check
```

Phase 2 每个子任务应按影响范围运行对应测试：

```powershell
cd web
npm run test -- AvatarDetail
npm run test -- LLMConfigPanel
npm run test -- StatusBar
npm run test -- world
npm run test -- event
npm run test -- avatar
npm run type-check
```

完整前端回归：

```powershell
cd web
npm run test
npm run type-check
```

若改动触及后端 DTO 或 `/api/v1` 契约，再补充运行相关后端 API 测试。

## 7. 推荐落地顺序

1. Phase 1.1：HTTP timeout / AbortSignal。
2. Phase 1.2：Pixi 地图旧对象销毁。
3. Phase 1.3：全局音效监听收口。
4. Phase 1.4：关闭页兜底渲染调整。
5. Phase 1.5：少量高噪声模板表达式下沉。
6. Phase 2.1：迁移并删除 `worldStore` deprecated proxies。
7. Phase 2.2：状态栏弹窗 registry。
8. Phase 2.5：world overview loading 状态拆分。
9. Phase 2.3：拆分 `AvatarDetail.vue`。
10. Phase 2.4：拆分 `LLMConfigPanel.vue`。

Phase 2 中大组件拆分建议分开提交，避免一次 PR 同时移动大量 template 与 style，降低 review 和回归成本。
