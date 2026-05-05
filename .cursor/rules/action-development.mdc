---
description: 动作(Action)与互动动作(Mutual Action)的开发规范与说明
globs: src/classes/action/**/*.py, src/classes/mutual_action/**/*.py
---
# 动作与互动动作开发规范 (Action & Mutual Action Development Guide)

在本项目中开发新的角色动作 (Action) 或互动动作 (MutualAction) 时，必须遵循以下规范，确保多语言支持、AI 决策正常工作，并顺利整合进游戏循环。

## 1. 核心概念分类

*   **单人动作 (Action)**: 继承自 `InstantAction`（瞬时动作，一次执行完毕）或 `TimedAction`（长态动作，持续数个月）。位于 `src/classes/action/`。
*   **互动动作 (MutualAction)**: 继承自 `MutualAction`。表示角色 A 对角色 B 发起的交互（如双修、切磋、送礼等），必定需要目标角色做出反馈。位于 `src/classes/mutual_action/`。

## 2. 通用属性与方法 (所有 Action 必填)

所有的动作（含单人和互动）类必须实现以下类变量，用于前端展示与多语言 (i18n)：

*   **`ACTION_NAME_ID: str`**: 动作名称的多语言 key（例如 `"meditate_action_name"`）。
*   **`DESC_ID: str`**: 动作具体描述的多语言 key（例如 `"meditate_description"`）。
*   **`REQUIREMENTS_ID: str`**: 动作执行条件的多语言 key（例如 `"meditate_requirements"`）。
*   **`EMOJI: str`**: 动作对应的 Emoji 图标（无需翻译，例如 `"🧘"`）。
*   **`PARAMS: dict`**: 执行此动作需要的参数格式定义（例如 `{"target_realm": "str"}`。若无参数填 `{}`）。
*   **`PARAM_OPTION_SOURCES: dict`** (按需必填): 如果 `PARAMS` 中包含需要从当前世界状态选择的参数（角色、地区、物品、境界、方向等），必须声明该参数的候选来源，供 `get_action_infos(avatar)` 生成 `param_options`。可用来源定义在 `src/classes/action/param_options.py::ParamOptionSource`。

### 生命周期方法

*   **`can_start(self, **kwargs) -> tuple[bool, str]`**:
    *   检查动作此时能否开始。返回 `(True, "")` 或 `(False, "失败原因的翻译字符串")`。
*   **`start(self, **kwargs) -> Event | None`**:
    *   启动动作，通常在此创建并返回一个开始执行动作的世界 `Event`。
*   **`_execute(self, **kwargs) -> None`** (单人动作):
    *   具体的底层执行逻辑（如增加修为、扣除灵石、增减繁荣度等）。
*   **`finish(self, **kwargs) -> list[Event]`** (异步):
    *   动作执行结束时调用，返回执行结果相关的 `Event` 列表。
*   **`can_possibly_start(self) -> bool`** (可选):
    *   **非常重要**：用于前置过滤掉对于特定角色**绝对不可能**执行的动作（如正道绝对不搜刮百姓）。
    *   这有助于大大缩短传给 LLM 的 `action_infos` prompt 长度。如果可能执行，返回 `True`；绝对不可能返回 `False`。默认返回 `True`。

### 时间管理 (TimedAction)

*   如果是 `TimedAction`，必须设置类变量 **`duration_months: int`** 来表示该动作默认耗时几个月。

## 3. 参数候选项规范

LLM 决策动作参数时会读取 `get_action_infos(avatar)` 中的 `param_options`。新增或修改动作时，必须保证动作 schema 与执行层参数解析一致。

### 需要声明 `PARAM_OPTION_SOURCES` 的参数

如果参数不是自由文本或纯数值，而是需要从当前世界状态中选择，必须声明来源。例如：

```python
from src.classes.action.param_options import ParamOptionSource

class Buy(InstantAction):
    PARAMS = {"target_name": "str"}
    PARAM_OPTION_SOURCES = {
        "target_name": ParamOptionSource.CURRENT_CITY_STORE_ITEM_NAME,
    }
```

常见来源：

*   `CURRENT_CITY_STORE_ITEM_NAME`: 当前城市商店物品名，用于购买。
*   `SELLABLE_ITEM_NAME`: 当前可出售材料/装备名，用于出售。
*   `GIFTABLE_ITEM_ID`: 当前可赠送物品 ID 或 `SPIRIT_STONE`，用于赠送。
*   `OBSERVABLE_AVATAR_NAME`: 当前可观察角色名，用于互动、攻击、移动到角色等。
*   `KNOWN_REGION_NAME`: 当前已知地区名，用于移动到/离开地区。
*   `KNOWN_CULTIVATE_REGION_NAME`: 当前已知修炼地区名，用于占据洞府。
*   `MATERIAL_REALM_VALUE`: 当前材料足够的境界值，用于铸造/炼丹。
*   `CARDINAL_DIRECTION`: `north/south/east/west`，用于方向移动。

### `param_options.value` 约定

每个候选项中的 `value` 是 LLM 应填入该参数的值；`id`、`name` 等字段只作为上下文。新增来源时必须保证 `value` 与对应动作执行层真实接受的参数格式一致。

### 测试要求

新增或修改世界状态参数时，必须补充测试：

*   该动作的 `PARAM_OPTION_SOURCES` 声明。
*   `get_action_infos(avatar)` 中对应参数存在合理的 `param_options`。
*   option 的 `value` 能被动作执行层解析。
*   候选范围符合角色视角（如可观察角色、已知地区），不能把不可见/不可操作对象暴露给 LLM。

## 4. MutualAction 特有规范

互动动作继承自 `MutualAction`，除上述通用规范外，还需遵循：

*   **`PARAMS`**: 必须包含 `"target_avatar": "Avatar"` 或类似定义。
    *   `MutualAction` 基类已声明 `"target_avatar": ParamOptionSource.OBSERVABLE_AVATAR_NAME`；子类如新增 `item_id`、`region_name` 等额外世界状态参数，仍需补充自身的 `PARAM_OPTION_SOURCES`。
*   **`FEEDBACK_ACTIONS: list[str]`**: 目标角色可选的反馈动作名称列表（如 `["Accept", "Reject"]`）。
*   **`STORY_PROMPT_ID: str`** (可选): 如果该互动动作在结束后要生成一段小故事（如双修），应提供对应的 Prompt 多语言 key。
*   **`_can_start(self, target: "Avatar") -> tuple[bool, str]`**:
    *   MutualAction 中应重写此方法来进行启动条件判断（基类已经处理了目标不存在、目标是自己、目标死亡等基础检查）。
*   **`_settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None`**:
    *   核心结算逻辑。根据目标给出的 `feedback_name`（如 `"Accept"`），在此处应用具体的数值/状态变化。

## 5. 注册与测试要求

*   **注册装饰器**: 必须在类定义上方添加 `@register_action(actual=True)` 装饰器。
*   **模块导出**: **必须**在当前目录的 `__init__.py` 中 `from .your_file import YourAction`，否则注册将无效！详细请参考 `.cursor/rules/python-registry.mdc`。
*   **测试覆盖**:
    *   新增动作必须在 `tests/` 中添加对应的测试（如 `test_action_my_action.py`）。
    *   如果重写了 `can_possibly_start`，必须在 `tests/test_action_can_possibly_start.py` 中补充相关分支的测试。
