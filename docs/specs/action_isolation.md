# Action Isolation Strategy (动作隔离策略)

## 背景

在修仙世界模拟中，角色会执行各种持续性动作（如闭关、战斗、移动等）。同时，系统存在各种全局机制（如拍卖会、大比、奇遇、霉运等）会尝试与角色互动。

此前存在的问题是：全局机制无视角色当前状态，导致“正在闭关的角色跑去参加拍卖会”或“闭关时路边捡到神兵”等逻辑违和现象。

## 解决方案：Trait-based Declarative Control

我们采用“基于特性的声明式控制”方案，将“是否允许被打扰”的定义权下放给 `Action` 类本身。

### 1. Action 基类定义

在 `src/classes/action/action.py` 中，所有动作默认开放交互：

```python
class Action(ABC):
    # ...
    # 是否允许参与聚会（如拍卖会、大比）
    ALLOW_GATHERING: bool = True
    
    # 是否允许触发世界随机事件（如奇遇、霉运）
    ALLOW_WORLD_EVENTS: bool = True
```

### 2. 特定动作重写策略

例如 `Retreat` (闭关) 动作 (`src/classes/action/retreat.py`) 需要与世隔绝：

```python
class Retreat(TimedAction):
    # ...
    # 闭关期间，不问世事，不染因果
    ALLOW_GATHERING = False
    ALLOW_WORLD_EVENTS = False
```

### 3. Avatar 状态检查接口

在 `Avatar` (`src/classes/avatar/action_mixin.py`) 中封装了状态检查属性：

- `avatar.can_join_gathering`: 检查当前动作是否允许参加聚会。
- `avatar.can_trigger_world_event`: 检查当前动作是否允许触发奇遇/霉运。

### 4. 外部调用规范

- **Gathering (如 Auction)**: 在获取参与者列表时，必须过滤 `can_join_gathering` 为 True 的角色。
- **Passive Effects (Fortune/Misfortune)**: 在触发前，必须检查 `can_trigger_world_event` 为 True。

## 扩展指南

当你创建一个新的 Action 时：
- 如果该动作需要角色全神贯注（如“突破”、“炼丹”），应考虑将 `ALLOW_GATHERING` 设为 `False`。
- 如果该动作处于特殊空间或心流状态（如“心魔劫”、“顿悟”），应考虑将 `ALLOW_WORLD_EVENTS` 设为 `False`。
- 默认情况下不需要做任何修改。
