---
description: 前端音效开发规范 (Sound Effect Guidelines)
globs: ["web/src/**/*.vue", "web/src/**/*.ts", "web/src/**/*.tsx"]
---
# 前端音效开发规范 (Sound Effect Guidelines)

在编写或修改前端组件（Vue/TS）时，必须严格遵守以下音效集成规范，确保用户体验的一致性，并降低开发成本。

## 1. 自动音效 (默认行为)
- 系统已实现全局事件委托。**绝不要**给标准的 `<button>`、`<a>`、`role="button"` 或带有 `.n-button`, `.btn`, `.clickable` 类的元素手动添加点击音效逻辑。它们会自动播放 `click` 音效。

## 2. 特殊音效控制 (v-sound)
- 如果需要非默认音效，使用 `v-sound` 指令，**不要**在 `@click` 中混入音效逻辑。全局监听器会自动检测该指令并避让，不会导致双重音效。
- 可选值：
  - `v-sound:cancel`：用于关闭、取消、删除、退出按钮。
  - `v-sound:select`：用于确认、保存、重要选择、开始游戏按钮。
  - `v-sound="'open'"`：用于打开新界面、跳转链接、查看详情的元素。
- 对于非标准交互元素（如普通的 `div` 或 `li`），如果需要交互音效，必须添加 `v-sound` 指令或 `.clickable` 类名。

## 3. 禁用音效 (data-no-sound)
- 如果一个按钮或交互元素**不应该**发声（例如仅作展示，或由父/子元素处理音效），必须添加 `data-no-sound` 属性。
  - 示例：`<button data-no-sound>Mute</button>`

## 4. 编程式播放 (仅限特殊场景)
- 只有在无法使用 DOM 事件的场景（如 Canvas 内部交互、键盘事件、自动触发的反馈）下，才允许引入并使用 `useAudio`。
  - 示例：
    ```typescript
    import { useAudio } from '@/composables/useAudio'
    const { play } = useAudio()
    play('select')
    ```
