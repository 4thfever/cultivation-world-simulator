---
description: 存档与序列化规范 (Save/Load & Serialization)
globs: src/sim/save/**/*.py, src/sim/load/**/*.py, src/classes/**/*.py
---

# 存档与序列化规范 (Save/Load & Serialization)

本规范定义游戏状态（如 Avatar、World 等）的持久化存储原则（形状与组织方式）。**开发阶段**下是否加载旧存档、在加载侧迁就旧键，以 `.cursor/rules/development-phase.mdc` 为准：新模型清晰优先，不为兼容付费。

## 1. 序列化边界与引用管理

*   **仅序列化基础类型**：`to_dict` 或 `to_save_dict` 方法返回的字典中，所有值必须是 JSON 可序列化的基础数据类型（`str`, `int`, `float`, `bool`, `list`, `dict`）。
*   **禁止深拷贝引用**：涉及跨实体引用时（例如 `Avatar` 认识另一个 `Avatar`，或属于某个 `Sect`），**仅保存其 ID 字符串**。
    *   *错误示例*：`"sect": self.sect.to_dict()`
    *   *正确示例*：`"sect_id": self.sect.id if self.sect else None`
*   **反序列化重建**：加载存档时，通过全局注册表或世界管理器，利用保存的 ID 重新建立对象引用。

## 2. 代码组织与 Mixin 模式

*   **分离读写逻辑**：对于复杂的实体类（如 `Avatar`），其序列化和反序列化逻辑必须剥离到独立的 Mixin 类中。
    *   参考 `src/sim/save/avatar_save_mixin.py` (`AvatarSaveMixin`)
    *   参考 `src/sim/load/avatar_load_mixin.py` (`AvatarLoadMixin`)
*   **保持核心类纯粹**：不要在 `src/classes/core/avatar/core.py` 中堆砌几百行的 `to_dict` 逻辑。

## 3. 加载侧与旧数据（与开发阶段策略一致）

*   **以当前模型清晰为准**：读入字典时的主路径应直接、好懂，不必为尚未承诺支持的旧存档形态预留一整套兼容分支。
*   **零代价可顺手容忍缺键**：若用 `.get(key, default)`（或等价写法）即可表达当前模型、且不引入并行格式或拖累结构，可以采用；若为了旧存档必须加双轨、改名映射或妥协字段语义，则**不**为兼容承担该代价（见 `development-phase.mdc`）。
