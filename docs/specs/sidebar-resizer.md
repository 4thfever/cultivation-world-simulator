# Sidebar Resizer 规格

## 概述

在地图区域和事件记录面板（sidebar）之间添加一条可拖曳的分隔线，允许用户调整 sidebar 的宽度。

## 需求

### 功能

- 在 `.map-container` 和 `.sidebar` 之间添加一个垂直的 resizer 手柄。
- 用户可以通过拖曳该手柄来调整 sidebar 的宽度。

### 宽度限制

- **最小宽度**: 300px
- **最大宽度**: 50% 屏幕宽度
- **默认宽度**: 400px

### 持久化

- 不需要持久化，每次打开页面都恢复为默认 400px。

## 实现细节

### 修改文件

- `web/src/App.vue` - resizer 逻辑
- `web/src/components/game/GameCanvas.vue` - canvas 尺寸调整

### 技术方案

1. 在 `.main-content` 中，在 `.map-container` 和 `.sidebar` 之间插入一个 `.resizer` 元素。
2. 使用 `mousedown` / `mousemove` / `mouseup` 事件实现拖曳逻辑。
3. 拖曳时动态计算并设置 sidebar 宽度。
4. Canvas 使用窗口大小而非容器大小，确保拖曳 sidebar 时地图不会被缩放，只改变可视区域。

### UI 细节

- Resizer 宽度: 4px
- 默认颜色: 透明或与背景融合
- Hover/拖曳时颜色: 高亮（如 `#555` 或主题色）
- 鼠标样式: `col-resize`

### 边界处理

- 拖曳超出最小/最大范围时，宽度固定在边界值。
- 窗口 resize 时，如果当前宽度超过 50% 屏幕宽，自动调整为 50%。
