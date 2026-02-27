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
*   `SystemMenu.vue`: 按 ESC 呼出的模态菜单，用于挂载 `panels/system/` 下的子面板。
*   `SplashLayer.vue`: 游戏启动时的封面/开始界面。

### 2.3 逻辑复用层 (`src/composables/`)
封装复杂的业务逻辑，使组件保持轻量。
*   `useGameInit.ts`: 负责游戏启动流程检查、后端心跳检测。
*   `useGameControl.ts`: 负责暂停/继续、菜单开关、全局快捷键绑定。
*   `useSidebarResize.ts`: 负责侧边栏（事件面板）的拖拽调整宽度逻辑。
*   `useAudio.ts` / `useBgm.ts`: 音效与背景音乐管理。
*   `useTextures.ts`: Pixi 纹理的预加载与缓存管理。

### 2.4 状态管理层 (`src/stores/`)
基于 Pinia 的状态管理。
*   **`world.ts` (聚合层)**: **核心 Store**。
    *   职责：管理全局时间 (Year/Month)、天象、秘境。
    *   作用：作为 Facade 模式的入口，聚合了 Map、Avatar、Event 三个子 Store 的数据，对外提供统一的 `initialize` 和 `handleTick` 方法。
*   **`map.ts`**: 存储地图矩阵 (`mapData`) 和区域数据 (`regions`)。
*   **`avatar.ts`**: 存储所有角色数据 (`avatars`)，处理增量更新。
*   **`event.ts`**: 存储事件日志 (`events`)，处理分页加载、筛选、实时推送。
*   `ui.ts`: 管理当前选中对象 (`selectedAvatarId`, `selectedRegionId`) 和 UI 显隐状态。
*   `setting.ts`: 管理前端设置及与后端配置的同步。

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

### 3.3 渲染架构
*   **Vue3-Pixi**: 使用 Vue 组件声明式地编写 Pixi 对象。
*   **性能优化**:
    *   地图使用 `shallowRef` 存储，避免 Vue 深度监听 100x100 的地图数组。
    *   地块渲染使用 `onMounted` 一次性构建 Pixi Sprite，静态地块不参与响应式更新，仅在地图数据重载时重建。
    *   动态效果（如水面流动）使用 `PIXI.Ticker` 独立驱动，不依赖 Vue 渲染循环。

## 4. 关键文件索引 (Critical Files Index)

| 文件路径 | 职责描述 | 修改频率 |
| :--- | :--- | :--- |
| `web/src/App.vue` | 应用根组件，负责各层级组件的组装、全局快捷键、胶水逻辑。 | 高 |
| `web/src/stores/world.ts` | **世界状态总线**。处理 Tick 逻辑、初始化聚合。修改游戏核心数据流时必看。 | 高 |
| `web/src/components/game/panels/EventPanel.vue` | 事件日志面板。涉及 UI 展示、筛选、性能优化（虚拟滚动/分页）。 | 中 |
| `web/src/components/game/MapLayer.vue` | 地图渲染核心。涉及 Pixi 绘图、纹理管理、Shader/Mask 特效。 | 中 |
| `web/src/composables/useGameControl.ts` | 游戏流程控制。涉及暂停、菜单、输入锁定逻辑。 | 低 |
| `web/src/api/modules/*.ts` | 后端接口定义。新增 API 时需修改对应模块。 | 中 |
| `web/src/locales/*.json` | 多语言文本。修改 UI 文字时必改。 | 高 |

---

**Vibe Coding 提示**:
*   修改 UI 时，优先检查 `stores/ui.ts` 和对应的 Panel 组件。
*   修改数据逻辑时，先看 `stores/world.ts` 及其拆分出的子 Store。
*   涉及 Pixi 渲染问题时，直接关注 `web/src/components/game/` 下的 Layer 组件。

## 5. 桌面版与 Steam 适配 (Desktop & Steam)

为了支持 Steam 平台发布，我们从浏览器模式切换到了独立窗口模式。

1.  **独立窗口架构 (Standalone Window)**:
    *   使用 `pywebview` 将 Web 前端封装在一个原生的操作系统窗口中。
    *   不再调用 `webbrowser.open()` 打开系统默认浏览器。
    *   应用现在拥有独立的进程、任务栏图标和窗口标题，这对 Steam Overlay 集成至关重要。

2.  **启动流程变更为**:
    *   **Main Thread**: 运行 `pywebview` 的 GUI 循环 (`webview.start()`)。
    *   **Background Thread**: 运行 `uvicorn` 后端服务器 (`Daemon Thread`)。
    *   **Subprocess**: (仅开发模式) 运行 `npm run dev` 前端开发服务器。

3.  **开发体验**:
    *   运行 `python src/server/main.py --dev` 时，会自动开启 Debug 模式。
    *   在窗口内点击右键 -> `Inspect` 依然可以调出开发者工具 (DevTools)。
    *   HMR (热重载) 依然有效，修改 `web/src` 代码后窗口内容会自动刷新。

4.  **打包与发布**:
    *   在 `PyInstaller` 打包配置中，需确保 `webview` 及其后端依赖 (如 Edge WebView2 Loader) 被正确包含。
    *   打包后的 `.exe` 即为最终交付给玩家的可执行文件。

5.  **pywebview 下的画布尺寸原则**:
    *   **不要**使用 `useWindowSize()`（依赖 `window.resize` 事件）来驱动 PIXI 画布尺寸。pywebview 的 WebView2 在全屏切换时不触发该事件，导致画布无法跟随窗口扩大，右下角出现黑边。
    *   **应使用** `useElementSize(container)`（基于 `ResizeObserver`）。`ResizeObserver` 监听的是 DOM 元素的实际尺寸变化，在 WebView2 中可靠。
    *   当前实现（`GameCanvas.vue`）：`width/height` 和 `Viewport` 的 `screenWidth/screenHeight` 均直接来自 `useElementSize`，与 `resizeTo="container"` 指向同一数据源，无冲突。

## 6. 异常恢复与防卡死设计 (Error Recovery)

为了应对极少部分玩家设备可能出现的 WebView2 渲染卡顿、Vue 状态意外不同步等玄学问题，我们在前端全局实现了**内置重载 (F5 刷新)** 机制。

1.  **全局按键监听 (`App.vue`)**:
    *   劫持了键盘的 `F5` 事件，按下时执行 `window.location.reload()` 强行刷新前端页面。
    *   此时后端 (`uvicorn` 和 Python 模拟器) 不受影响，依然在后台保持原状态。

2.  **状态防闪烁设计 (`isAppReady`)**:
    *   因为 F5 刷新会导致 Vue 状态被清空，默认的 `showSplash` 状态很容易在刷新期间闪烁出启动封面图。
    *   通过引入 `isAppReady`（布尔值），**在页面刚加载、还未收到后端 `initStatus` 接口第一次响应时，前端界面保持纯黑 (`display: none` 等效)**。
    *   收到后端响应后，若后端返回 `idle`，则展示 `SplashLayer`；若后端正在运行中（如 `ready` 或 `loading`），则直接进入对应的 `LoadingOverlay` 或游戏界面。
    *   为了防止在 `ready` 状态下 F5 刷新时，前端初始化等待期间（`gameInitialized === false`）闪烁 Loading 界面，对 `LoadingOverlay` 的渲染条件增加了严格判断，使得 F5 后能更加平滑地直接呈现游戏画面。

## 7. 前端资源预加载策略 (Preloading Strategy)

在游戏开局初始化过程中，后端部分阶段（如调用 LLM 生成角色身世）需要消耗数秒乃至十几秒的时间。为了避免这段时间白白浪费，以及防止后端到达 100% 后前端还需要耗时加载图片而导致进度条“卡 100%”的临门一脚顿挫感，前端实现了一套异步预加载机制。

1. **阶段监听**: 前端通过 `useGameInit` 持续轮询 `/api/init-status` 接口，不仅获取总体进度，还监听当前所处的 `phase_name`。
2. **常量映射 (`GAME_PHASES`)**: 在 `constants/game.ts` 中，我们维护了不同资源可以开始加载的最小后端阶段要求：
   *   `MAP_READY`: 当后端排布完宗门或生成完角色时，地图数据已经就绪。
   *   `AVATAR_READY`: 当后端进入检查 LLM 或生成初始事件时，所有角色的基础信息（含头像 ID）已经完全确定。
   *   `TEXTURES_READY`: 与角色就绪同步，此时可以拉取到所有相关角色的头像、以及对应的地块纹理等，直接执行 PixiJS 的 Assets 预加载。
3. **“白嫖”等待时间**: 在轮询过程中，一旦后端状态进入 `TEXTURES_READY` 阶段（通常对应后端的长时间 LLM 阻塞操作），前端的 `useGameInit` 就会无阻塞地触发 `loadBaseTextures()`。
4. **无缝进入**: 利用 PixiJS `Assets` 的内置缓存机制，当后端最终发出 `ready` 并将控制权交还给前端 `initializeGame()` 时，再次调用的 `await loadBaseTextures()` 会瞬间命中缓存，耗时降至 0 毫秒，从而实现 Loading 结束后画面的无缝秒进。
