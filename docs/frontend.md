# 前端架构与开发指南 (Frontend Architecture Guide)

本文档旨在帮助开发者（及 AI 助手）快速理解 `web/` 目录下的前端架构、文件职责及核心数据流。在进行 Vibe Coding 或重构时，请参考此文档。

## 1. 技术栈概览 (Tech Stack)

*   **核心框架**: Vue 3 (Composition API + `<script setup>`) + TypeScript
*   **构建工具**: Vite
*   **状态管理**: Pinia (模块化 Store)
*   **UI 组件库**: Naive UI (用于系统菜单、面板等常规 UI)
*   **游戏渲染**: Vue3-Pixi (基于 Pixi.js 的 2D 渲染引擎，处理地图、角色动画)
*   **网络请求**: Axios (RESTful API)
*   **国际化**: Vue I18n

## 2. 目录结构详解 (Directory Structure)

根目录: `web/src/`

### 2.1 API 层 (`src/api/`)
封装所有与后端的 HTTP 交互。
*   `index.ts`: 统一导出点。
*   `modules/`:
    *   `system.ts`: 系统级控制（启动、暂停、重置、存档）。
    *   `world.ts`: 获取地图数据、初始状态、天象信息。
    *   `event.ts`: 事件日志的分页拉取。
*   `mappers/`:
    *   `event.ts`: `EventDTO -> GameEvent` 的转换与时间线顺序规范化。
    *   `world.ts`: `rankings/config` 的响应归一化，减少组件和 store 内散乱兼容逻辑。

### 2.2 组件层 (`src/components/`)
*   **`game/` (核心游戏画面)**
    *   `GameCanvas.vue`: Pixi.js 应用入口，管理视口 (`Viewport`) 和图层顺序。
    *   `MapLayer.vue`: 负责地图瓦片渲染、动态水面效果 (Shader/Ticker)、区域标注。
    *   `EntityLayer.vue`: 负责角色 (Avatar) 的渲染、移动动画插值。
    *   `CloudLayer.vue`: 战争迷雾或装饰性云层。
    *   `panels/`: 游戏内悬浮面板。
        *   `EventPanel.vue`: 左侧事件日志，包含无限滚动、单人/双人筛选逻辑。
        *   `info/`: 选中对象（角色/地块）的详细信息面板容器。
        *   `system/`: 系统菜单内的子面板（存档、设置、LLM配置、创建角色）。
*   **`layout/`**: 全局布局组件。
    *   `StatusBar.vue`: 顶部状态栏（显示年份、资源等）。
*   **`common/`**: 通用 UI 组件（如自定义按钮、加载条）。
*   **`settings/`**:
    *   `SettingsPanel.vue`: 可复用设置面板。负责语言、音量、自动保存等设置项，不承担菜单壳层职责。
*   **`system-menu/`**:
    *   `SystemMenuShell.vue`: 系统菜单壳层。负责 modal 外框、header、tab bar 与内容槽位。
    *   `tabs/`: 各个菜单 tab 的薄包装组件。
        *   `SystemMenuSettingsTab.vue`: 挂载 `SettingsPanel`。
        *   `SystemMenuAboutTab.vue` / `SystemMenuOtherTab.vue`: 静态 tab 内容。
        *   其余 tab 组件主要负责挂载现有 `panels/system/` 子面板。
*   `SystemMenu.vue`: 系统菜单装配入口。组合 `SystemMenuShell` 与各 tab 内容，不直接承载大段业务 UI。
*   `SplashLayer.vue`: 游戏启动时的封面/开始界面。

### 2.3 逻辑复用层 (`src/composables/`)
封装复杂的业务逻辑，使组件保持轻量。
*   `useAppShell.ts`: 应用壳层状态机。统一管理 `boot / splash / initializing / game` 场景，以及系统菜单、LoadingOverlay 等 overlay 的挂载时机。
*   `useGameInit.ts`: 负责游戏启动流程检查、后端心跳检测。
*   `useSystemMenuFlow.ts`: 系统菜单流程层。负责菜单 tab、上下文（`splash/game`）、可关闭状态、LLM 启动检查与菜单打开关闭。
*   `useGameControl.ts`: 负责纯游戏控制逻辑，如暂停/继续、ESC 输入处理、与菜单可见性的联动暂停恢复。
*   `useSidebarResize.ts`: 负责侧边栏（事件面板）的拖拽调整宽度逻辑。
*   `useAudio.ts` / `useBgm.ts`: 音效与背景音乐管理。
*   `useTextures.ts`: Pixi 纹理的预加载与缓存管理。

### 2.4 状态管理层 (`src/stores/`)
基于 Pinia 的状态管理。
*   **`world.ts` (聚合层)**: **核心 Store**。
    *   职责：管理全局时间 (Year/Month)、天象、秘境。
    *   作用：作为 Facade 模式入口，负责 world 级编排（`initialize/handleTick`）。  
        说明：为平滑迁移，仍保留部分兼容代理字段；新代码应优先直接依赖子 Store（`map/avatar/event`）。
*   **`map.ts`**: 存储地图矩阵 (`mapData`) 和区域数据 (`regions`)。
*   **`avatar.ts`**: 存储所有角色数据 (`avatars`)，处理增量更新。
*   **`event.ts`**: 存储事件日志 (`events`)，处理分页加载、筛选、实时推送。
*   `ui.ts`: 管理当前选中对象与 UI 显隐状态；系统菜单的 tab、是否可关闭、菜单上下文（`splash/game`）也集中在此处。
*   `setting.ts`: 管理前端设置及与后端配置的同步。
*   `socket.ts`: 连接状态与订阅管理（轻业务）。
*   `socketMessageRouter.ts`: Socket 消息分发与业务响应路由（`tick/toast/llm_config_required/...`）。

### 2.5 类型定义 (`src/types/`)
*   `core.ts`: 前端核心领域模型（如 `AvatarSummary`, `RegionSummary`, `GameEvent`）。
*   `api.ts`: 后端接口返回的数据结构 (DTO)。

## 3. 核心机制与数据流 (Core Architecture)

### 3.1 游戏初始化流程
1.  **Entry**: `App.vue` 挂载。
2.  **Check**: 调用 `useGameInit` 检查后端服务状态（Idle/Ready/Running）。
3.  **Load**: 用户点击 "Start" -> 触发 `worldStore.initialize()`。
    *   并行加载地图数据 (`mapStore.preloadMap`) 和初始状态 (`worldApi.fetchInitialState`)。
    *   重置事件列表 (`eventStore.resetEvents`)。
4.  **Render**: 数据就绪 (`isLoaded = true`) -> `GameCanvas` 和 `MapLayer` 开始渲染。

### 3.2 游戏循环 (Tick Loop)
游戏采用后端驱动模式（Server-Authoritative）。
1.  **Source**: 后端通过 WebSocket 或轮询接口推送 `TickPayloadDTO`。
2.  **Store Update**: `worldStore.handleTick(payload)` 接收数据。
    *   更新时间 (`year`, `month`)。
    *   调用 `avatarStore.updateAvatars` 进行角色状态增量合并。
    *   调用 `eventStore.addEvents` 将新事件插入日志流。
    *   更新天象 (`currentPhenomenon`)。
3.  **Reactivity**: Vue 响应式系统检测到 Store 变化。
    *   `EntityLayer` 检测到坐标变化 -> 触发平滑移动动画。
    *   `EventPanel` 检测到新事件 -> 自动滚动到底部。
    *   `InfoPanel` 检测到选中角色属性变化 -> 实时刷新数值。

### 3.3 应用壳层状态机 (App Shell)
当前根层页面编排由 `useAppShell` 统一管理，`App.vue` 只负责根据场景装配视图。
1. `useGameInit` 轮询 `initStatus`，并在 `ready` 且未初始化时触发一次前端初始化。
2. `useAppShell` 将根层场景收敛为四种：
    * `boot`: 设置或第一次 `initStatus` 尚未准备好，只显示纯黑壳层。
    * `splash`: 应用已准备好，但尚未进入一局游戏，底层显示 `SplashLayer`。
    * `initializing`: 玩家已触发开始/读档，但前后端初始化尚未完成，底层保持黑壳层，`LoadingOverlay` 作为 overlay 展示。
    * `game`: 前后端均完成初始化，才允许渲染 `StatusBar / GameCanvas / EventPanel` 等游戏 UI。
3. 系统菜单与 Loading 不再决定底层场景，而是作为 overlay 挂载在当前场景之上。
4. `useSystemMenuFlow` 负责菜单流程：打开/关闭菜单、LLM 校验、菜单上下文与 tab 跳转。
5. `useGameControl` 只处理游戏控制，不再承担 splash <-> game 的根层场景切换职责，也不直接持有菜单业务流程。

### 3.4 Scene + Overlay 约束
为了避免出现“菜单打开但底下渲染了错误页面”的非法组合，根层视图必须遵守以下约束：
1. `App.vue` 不应再通过 `showSplash/showMenu/showLoading` 多个布尔值拼装页面。
2. 游戏主界面只能由 `scene === 'game'` 驱动，不能通过 “`!showSplash`” 之类的反向条件推断。
3. 从 `SplashLayer` 打开 `settings/load/about` 时，底层场景仍然是 `splash`，只是额外叠加 `SystemMenu` overlay。
4. `SystemMenu` 必须显式记录上下文（`splash` 或 `game`），用于关闭行为、返回主界面与后续扩展。

### 3.5 菜单与设置分层 (Menu / Settings Layering)
系统菜单与设置相关 UI 采用“壳层 + 内容层 + 流程层”拆分：
1. `SystemMenuShell` 只负责 modal 容器、tab bar 与内容槽位。
2. `SystemMenu.vue` 只负责把 tab key 路由到对应内容组件。
3. `SettingsPanel` 只负责设置项本身，不感知自己处于系统菜单、Splash 还是未来的独立设置页。
4. `useSystemMenuFlow` 作为菜单流程层，负责：
    * 菜单打开/关闭
    * tab 默认值与切换
    * `splash/game` 菜单上下文
    * LLM 启动检查与强制跳转 `llm` tab
5. `useGameControl` 不应再承担“菜单打开后跳到哪个 tab”这类菜单业务决策。

### 3.6 Socket 消息流 (Transport -> Router -> Store/UI)
1. `api/socket.ts` 只负责 WebSocket 连接/重连/订阅。
2. `stores/socket.ts` 维护连接状态并把消息交给 `socketMessageRouter`。
3. `stores/socketMessageRouter.ts` 按消息类型分发到 world/ui/message 相关动作。
4. 新增消息类型时，优先修改 router 和 DTO，不在组件层做消息分支。

### 3.7 渲染架构
*   **Vue3-Pixi**: 使用 Vue 组件声明式地编写 Pixi 对象。
*   **性能优化与避坑 (Gotchas)**:
    *   **严禁将 PIXI 原生对象 (如 `Sprite`, `Container`) 放入 Vue 的深层响应式对象 (`ref`, `reactive`) 中**。这会导致 PIXI 内部严格相等 (`===`) 比较失败（如 `removeChild` 失效），引发内存泄漏和逻辑堆积 Bug。若需在组件中保存实例引用，请使用普通变量或 `shallowRef`。
    *   地图使用 `shallowRef` 存储，避免 Vue 深度监听 100x100 的地图数组。
    *   地块渲染使用 `onMounted` 一次性构建 Pixi Sprite，静态地块不参与响应式更新，仅在地图数据重载时重建。
    *   动态效果（如水面流动）使用 `PIXI.Ticker` 独立驱动，不依赖 Vue 渲染循环。
    *   地图区域名（`MapLayer` / `utils/mapLabels.ts`）默认应采用“碰撞避让”而非“重叠即隐藏”。避让策略必须兼容 `zh-CN / zh-TW / en-US / vi-VN / ja-JP` 五种语言：紧凑脚本（中文、日文）与拉丁脚本（英文、越南文）分别使用各自的文字尺寸估算与换行策略。
    *   地图区域名避让逻辑必须保持轻量。优先使用固定数量候选位置 + 邻域碰撞检测（如空间桶 / 网格索引），避免引入全局两两比较、力导向模拟、逐帧布局或其他会随区域数量快速退化的算法。

## 4. 关键文件索引 (Critical Files Index)

| 文件路径 | 职责描述 | 修改频率 |
| :--- | :--- | :--- |
| `web/src/composables/useAppShell.ts` | 应用壳层状态机核心。统一管理 `scene + overlay`、菜单上下文与 Splash/Game 场景切换。 | 高 |
| `web/src/composables/useSystemMenuFlow.ts` | 系统菜单流程层。负责 tab、closable、菜单上下文与 LLM 启动检查。 | 高 |
| `web/src/App.vue` | 根组件装配层。只按 `scene` 渲染底层页面，并挂载菜单/Loading overlay。 | 高 |
| `web/src/components/SystemMenuShell.vue` | 菜单壳层组件。负责 modal/header/tab bar，不承载具体 tab 内容。 | 中 |
| `web/src/components/settings/SettingsPanel.vue` | 可复用设置内容面板。负责语言、音量、自动保存等设置项。 | 中 |
| `web/src/stores/world.ts` | world 级编排与时间/天象状态。 | 高 |
| `web/src/stores/socketMessageRouter.ts` | Socket 业务消息路由中心。新增消息类型时优先修改此处。 | 高 |
| `web/src/components/game/panels/EventPanel.vue` | 事件日志面板。涉及 UI 展示、筛选、性能优化（虚拟滚动/分页）。 | 中 |
| `web/src/components/game/MapLayer.vue` | 地图渲染核心。涉及 Pixi 绘图、纹理管理、Shader/Mask 特效。 | 中 |
| `web/src/composables/useGameControl.ts` | 游戏控制层。负责暂停恢复、ESC 输入、菜单显隐联动暂停恢复。 | 低 |
| `web/src/api/modules/*.ts` + `web/src/api/mappers/*.ts` | API 请求与 DTO 归一化。新增接口建议同步补 mapper。 | 中 |
| `web/src/locales/*.json` | 多语言文本。修改 UI 文字时必改。 | 高 |

---

**Vibe Coding 提示**:
*   修改 UI 时，优先检查 `stores/ui.ts`、`useAppShell.ts`、`useSystemMenuFlow.ts` 和对应的 Panel 组件。
*   修改数据逻辑时，先看 `stores/world.ts` 及其拆分出的子 Store。
*   涉及 Pixi 渲染问题时，直接关注 `web/src/components/game/` 下的 Layer 组件。
*   Socket 消息逻辑优先改 `stores/socketMessageRouter.ts`，不要把消息分支散到组件中。
*   新增后端响应字段时，优先在 `types/api.ts` 和 `api/mappers/` 收敛转换。
*   修改地图文字显示时，优先检查 `web/src/components/game/utils/mapLabels.ts` 和 `web/src/utils/mapStyles.ts`，不要在 `MapLayer.vue` 内临时堆叠随机偏移或硬编码语言分支。
*   修改设置项时，优先改 `SettingsPanel.vue`；除非是菜单容器行为，不要把设置 UI 直接塞回 `SystemMenu.vue`。

## 5. 桌面版与 Steam 适配 (Desktop & Steam)

当前桌面打包版本统一使用本地 HTTP 服务 + 系统浏览器的模式运行。

1.  **统一启动流程**:
    *   `start()` 会先计算目标 URL，再调用 `webbrowser.open()` 打开系统默认浏览器。
    *   `uvicorn` 后端服务继续在当前 Python 进程中运行。
    *   在开发模式下，前端仍会以子进程方式启动 `npm run dev`。

2.  **开发体验**:
    *   运行 `python src/server/main.py --dev` 时，会自动开启 Debug 模式。
    *   HMR (热重载) 依然有效，修改 `web/src` 代码后浏览器页面会自动刷新。

3.  **打包与发布**:
    *   打包后的 `.exe` 会负责拉起本地服务并打开浏览器页面。
    *   不再需要额外包含桌面嵌入式 WebView 宿主运行时。

4.  **画布尺寸原则**:
    *   **不要**使用 `useWindowSize()`（依赖 `window.resize` 事件）来驱动 PIXI 画布尺寸。
    *   **应使用** `useElementSize(container)`（基于 `ResizeObserver`），让画布尺寸直接跟随容器变化。
    *   当前实现（`GameCanvas.vue`）：`width/height` 和 `Viewport` 的 `screenWidth/screenHeight` 均直接来自 `useElementSize`，与 `resizeTo="container"` 指向同一数据源，无冲突。

## 6. 启动渲染保护与场景边界 (Startup Rendering Guard)

为了避免前端刚接管页面时出现闪烁，同时避免未开局时误渲染游戏壳层，应用保留了一层启动阶段的渲染保护与场景边界。

1.  **`boot` 防闪烁设计**:
    *   在页面刚加载、还未完成 settings hydrate 或还未收到后端 `initStatus` 第一次响应前，根层场景保持 `boot`，页面显示纯黑壳层。
2.  **`splash` 与 `game` 的硬边界**:
    *   收到后端 `idle` 且前端未初始化时，场景进入 `splash`。
    *   只有当前后端准备完毕并且前端 `gameInitialized === true` 后，场景才允许进入 `game`。
    *   打开菜单、设置、关于页等 overlay 不得隐式切换到底层 `game` 场景。
3.  **`initializing` 过渡场景**:
    *   玩家开始开局/读档后，到真正完成前端装载前，根层应进入 `initializing`，底层维持黑壳层，`LoadingOverlay` 负责向用户表达进度。

## 7. 前端资源预加载策略 (Preloading Strategy)

在游戏开局初始化过程中，后端部分阶段（如调用 LLM 生成角色身世）需要消耗数秒乃至十几秒的时间。为了避免这段时间白白浪费，以及防止后端到达 100% 后前端还需要耗时加载图片而导致进度条“卡 100%”的临门一脚顿挫感，前端实现了一套异步预加载机制。

1. **阶段监听**: 前端通过 `useGameInit` 持续轮询 `/api/v1/query/runtime/status` 接口，不仅获取总体进度，还监听当前所处的 `phase_name`。
2. **常量映射 (`GAME_PHASES`)**: 在 `constants/game.ts` 中，我们维护了不同资源可以开始加载的最小后端阶段要求：
   *   `MAP_READY`: 当后端排布完宗门或生成完角色时，地图数据已经就绪。
   *   `AVATAR_READY`: 当后端进入检查 LLM 或生成初始事件时，所有角色的基础信息（含头像 ID）已经完全确定。
   *   `TEXTURES_READY`: 与角色就绪同步，此时可以拉取到所有相关角色的头像、以及对应的地块纹理等，直接执行 PixiJS 的 Assets 预加载。
3. **“白嫖”等待时间**: 在轮询过程中，一旦后端状态进入 `TEXTURES_READY` 阶段（通常对应后端的长时间 LLM 阻塞操作），前端的 `useGameInit` 就会无阻塞地触发 `loadBaseTextures()`。
4. **无缝进入**: 利用 PixiJS `Assets` 的内置缓存机制，当后端最终发出 `ready` 并将控制权交还给前端 `initializeGame()` 时，再次调用的 `await loadBaseTextures()` 会瞬间命中缓存，耗时降至 0 毫秒，从而实现 Loading 结束后画面的无缝秒进。

## 8. 错误处理与性能基线 (Error Policy & Baseline)

### 8.1 错误处理规范
*   统一使用 `utils/appError.ts` 中的 `logError/logWarn` 记录上下文，不直接散落 `console.error/warn`。
*   用户可见提示通过 `message` 统一出口，避免重复提示和风格不一致。

### 8.2 性能基线指标（轻量）
*   `useGameInit.ts`:  
    *   `initializeDurationMs`：一次初始化耗时。  
    *   `lastPollDurationMs`：最近一次状态轮询耗时。
*   `stores/event.ts`:  
    *   `lastMergeDurationMs`：tick 事件合并耗时。  
    *   `lastLoadDurationMs`：历史事件加载耗时。

这些指标用于回归比较，不用于线上用户可见展示。

## 9. UI Icon 约定 (UI Icon Guidelines)

当前前端已收敛出一套统一的 UI icon 方案，后续新增系统级 icon 时应优先复用，而不是重新从不同站点混搭。

1. **单一来源**:
   * 当前统一使用 `Lucide` outline SVG。
   * 本地图标目录：`web/src/assets/icons/ui/lucide/`
   * 来源与当前映射说明：`web/src/assets/icons/ui/lucide/README.md`
2. **使用范围**:
   * 顶部悬浮控制按钮
   * 系统菜单 tab
   * 顶部状态栏入口
   * 设置页、存档页、关于/其他等系统级面板
3. **风格约束**:
   * 不要在同一 UI 区域混用多个 icon 家族。
   * 默认使用 outline 风格，不与 filled / emoji / 彩色拟物图标混搭。
   * icon 只作为辅助识别，不替代多语言文案；关键入口旁必须保留文字。
4. **技术形态**:
   * 优先通过 `import xxxIcon from '@/assets/icons/ui/lucide/*.svg'` 模块导入。
   * 优先使用 `currentColor + mask-image` 渲染，让 hover / active / disabled 状态与文字颜色保持一致。
   * 不要为同类按钮分别内嵌手写 SVG，除非现有 icon 库确实没有合适素材。
5. **增量维护**:
   * 新增 icon 前先检查 `web/src/assets/icons/ui/lucide/` 是否已有可复用图标。
   * 若需下载新图标，优先补到同一目录，并同步更新该目录下 README 的来源与建议映射。
