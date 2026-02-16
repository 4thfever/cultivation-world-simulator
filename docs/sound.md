# 前端音效开发指南 (Sound Effect Guide)

本文档旨在规范前端开发中的音效集成，确保用户体验的一致性，并降低开发成本。

## 1. 自动音效机制 (Global Auto-Sound)

我们实施了全局事件委托机制，这意味着**绝大多数标准交互组件无需编写任何额外代码即可自动拥有音效**。

### 原理
在 `main.ts` 中，我们监听了 window 级的 `click` 事件。系统会自动识别以下元素并播放默认点击音效 (`click`)：
- `<button>` 标签
- `<a>` 标签
- 带有 `role="button"` 的元素
- 带有 `.n-button` (Naive UI), `.btn`, `.clickable` 类名的元素

### 开发者注意事项
- **默认行为**：只要你使用了上述标准标签或类名，音效就会自动生效。
- **避免重复**：不要给普通按钮重复添加手动点击监听来播放音效。

## 2. 特殊控制 (Manual Control)

当自动机制不满足需求时，可以使用以下方式进行控制。

### 2.1 禁用音效 (`data-no-sound`)
如果某个按钮不应该有音效（例如虽然是按钮但仅作展示用，或者由子元素处理音效），请添加 `data-no-sound` 属性。

```html
<!-- 这个按钮点击时不会有声音 -->
<button data-no-sound>Mute Button</button>
```

### 2.2 指定特殊音效 (`v-sound` 指令)
如果需要播放非默认的音效（如取消、确认、打开界面），使用 `v-sound` 指令。全局监听器会自动检测该指令并避让，**不会**导致双重音效。

支持的音效类型：
- `'click'` (默认，普通点击)
- `'cancel'` (关闭、取消、删除、退出)
- `'select'` (确认、保存、重要选择、开始游戏)
- `'open'` (打开新界面、跳转链接、查看详情)

使用示例：

```html
<!-- 播放取消音效 -->
<button v-sound:cancel @click="close">Close</button>

<!-- 播放确认音效 -->
<button v-sound:select @click="confirm">Confirm</button>

<!-- 播放打开音效 -->
<div class="card" v-sound="'open'" @click="openDetail">...</div>
```

**注意**：对于非标准交互元素（如 `div`, `span` 列表项），如果需要音效，**必须**添加 `v-sound` 指令，因为全局监听器默认不会处理它们（除非它们有 `.clickable` 类）。

### 2.3 编程式播放 (`useAudio`)
对于无法使用 DOM 事件的场景（例如 Canvas 内部交互、键盘事件、自动触发的反馈），请直接调用 `useAudio`。

```typescript
import { useAudio } from '@/composables/useAudio'

// 在 setup 中获取
const { play } = useAudio()

function handleCanvasClick() {
  // 手动播放
  play('select')
}
```

## 3. 最佳实践总结

1.  **新建界面时**：优先使用 `<button>` 或 `.btn`，这样你什么都不用做就有音效。
2.  **列表项**：如果是可点击的列表项（如 `EntityRow`），记得添加 `v-sound` 或类名 `.clickable`。
3.  **关闭/取消按钮**：请显式添加 `v-sound:cancel` 以提供正确的听觉反馈。
4.  **重要操作**：请显式添加 `v-sound:select` 以增强确认感。
5.  **Canvas 交互**：必须手动调用 `play()`。

## 4. 音频资源

所有音效资源位于 `web/public/sfx/`。目前支持 `.ogg` 格式。

- `click.ogg`: 通用点击（短促）
- `select.ogg`: 确认/选中（清脆）
- `cancel.ogg`: 取消/关闭（低沉）
- `open.ogg`: 展开/跳转（上扬）
