---
description: 事件系统规范 (Event System)
globs: src/classes/event.py, src/classes/event_storage.py, src/systems/**/*.py
---

# 事件系统规范 (Event System)

本规范定义了游戏中事件 (Event) 的生成、分类、关联与存储机制。事件是游戏历史记录和 LLM 上下文记忆的核心。

## 1. 事件粒度与分类 (`Event` 类)

*   **`is_major=True` (大事/长期记忆)**：
    *   **定义**：对角色生命周期有重大影响的事件（如：出生、死亡、大境界突破、结仇、道侣）。
    *   **处理**：永久保留，不会被清理。作为 LLM 推演时的核心上下文（长期记忆）。
*   **`is_major=False` (小事/短期记忆)**：
    *   **定义**：日常行为和琐碎交互（如：日常修炼、普通切磋、移动）。
    *   **处理**：定期被 `EventStorage` 清理。仅作为近期行为的上下文（短期记忆）。
*   **`is_story=True` (纯文本故事)**：
    *   **定义**：为了丰富前端表现而生成的纯文本故事（如：双修过程描写、战斗细节）。
    *   **处理**：不进入 AI 记忆引擎（不作为 prompt 传入 LLM），以节省 Token 消耗和避免干扰逻辑推理。

## 2. 角色关联 (`related_avatars`)

*   **准确记录**：在实例化 `Event` 时，必须准确填写 `related_avatars` 列表，包含所有参与该事件的角色 ID。
*   **双向查询**：底层 SQLite 依赖此字段建立 `event_avatars` 关联表。只有准确记录，才能支持 `get_events_between(id1, id2)` 这种双向关系查询。

## 3. 存储与读取 (`EventStorage`)

*   **统一入库**：业务代码（如 `Action` 或 `System`）只需生成并返回 `Event` 对象，由模拟器主循环 (`Simulator`) 统一收集并写入 `EventStorage`。严禁在业务逻辑中直接调用数据库写入。
*   **分页查询**：前端或外围接口查询事件时，必须使用基于 `cursor` 的分页机制 (`get_events`)，严禁拉取全量数据，防止内存溢出和传输阻塞。
*   **后端查询**：LLM 提示词组装时，应使用 `get_major_events_by_avatar` 和 `get_minor_events_by_avatar` 获取结构化的记忆切片。
