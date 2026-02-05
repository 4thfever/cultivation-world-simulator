# Action 多语言使用指南

本文档说明如何为 Action 类添加多语言支持。

## 已完成的改动

### 1. 基类增强 (`src/classes/action/action.py`)

在 `Action` 基类中添加了三个类方法和三个类变量：

**类变量**（子类覆盖）：
```python
ACTION_NAME_ID: str = ""    # 动作名称的 msgid
DESC_ID: str = ""           # 动作描述的 msgid
REQUIREMENTS_ID: str = ""   # 可执行条件的 msgid
```

**类方法**：
```python
@classmethod
def get_action_name(cls) -> str:
    """获取动作名称的翻译"""

@classmethod
def get_desc(cls) -> str:
    """获取动作描述的翻译"""

@classmethod
def get_requirements(cls) -> str:
    """获取可执行条件的翻译"""
```

### 2. 示例实现 (`src/classes/action/assassinate.py`)

以 `Assassinate` 为例，展示了完整的多语言支持：

```python
@cooldown_action
class Assassinate(InstantAction, TargetingMixin):
    # 多语言 ID
    ACTION_NAME_ID = "assassinate_action_name"
    DESC_ID = "assassinate_description"
    REQUIREMENTS_ID = "assassinate_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🗡️"
    PARAMS = {"avatar_name": "AvatarName"}
    ACTION_CD_MONTHS = 12
    
    # LLM 提示词 ID
    STORY_PROMPT_SUCCESS_ID = "assassinate_story_prompt_success"
    STORY_PROMPT_FAIL_ID = "assassinate_story_prompt_fail"
    
    # 自定义翻译方法（用于非标准字段）
    @classmethod
    def get_story_prompt_success(cls) -> str:
        from src.i18n import t
        return t(cls.STORY_PROMPT_SUCCESS_ID)
    
    @classmethod
    def get_story_prompt_fail(cls) -> str:
        from src.i18n import t
        return t(cls.STORY_PROMPT_FAIL_ID)
```

## 使用方法

### 方法一：使用基类提供的标准方法

适用于只有 `ACTION_NAME`、`DESC`、`REQUIREMENTS` 的 Action：

```python
class MyAction(InstantAction):
    # 1. 设置 msgid
    ACTION_NAME_ID = "my_action_name"
    DESC_ID = "my_action_description"
    REQUIREMENTS_ID = "my_action_requirements"
    
    # 2. 其他代码保持不变
    EMOJI = "⚔️"
    
    def _execute(self, **kwargs):
        # 实现逻辑
        pass

# 使用时：
action_name = MyAction.get_action_name()  # 自动翻译
desc = MyAction.get_desc()
```

### 方法二：自定义翻译方法

适用于有额外字段需要翻译的 Action（如 LLM 提示词）：

```python
class MyAction(InstantAction):
    # 标准字段
    ACTION_NAME_ID = "my_action_name"
    DESC_ID = "my_action_description"
    
    # 自定义字段
    CUSTOM_PROMPT_ID = "my_action_custom_prompt"
    
    @classmethod
    def get_custom_prompt(cls) -> str:
        from src.i18n import t
        return t(cls.CUSTOM_PROMPT_ID)
```

### 方法三：动态文本翻译

在运行时动态生成的文本（带占位符）：

```python
def start(self, target_name: str) -> Event:
    from src.i18n import t
    
    # 使用 t() 函数翻译并格式化
    content = t("{avatar} starts attacking {target}!",
               avatar=self.avatar.name,
               target=target_name)
    
    return Event(self.world.month_stamp, content, ...)
```

## 添加翻译

### 1. 在模块化 po 文件中添加条目

请在 `static/locales/{lang}/modules/action.po` 文件中添加翻译，而不是直接修改 `messages.po`。

**英文** (`static/locales/en-US/modules/action.po`)：
```po
# Action: MyAction
msgid "my_action_name"
msgstr "My Action"

msgid "my_action_description"
msgstr "This is my action description"

msgid "{avatar} starts attacking {target}!"
msgstr "{avatar} starts attacking {target}!"
```

**中文** (`static/locales/zh-CN/modules/action.po`)：
```po
# Action: MyAction
msgid "my_action_name"
msgstr "我的动作"

msgid "my_action_description"
msgstr "这是我的动作描述"

msgid "{avatar} starts attacking {target}!"
msgstr "{avatar} 开始攻击 {target}！"
```

### 2. 编译并合并

运行项目根目录下的构建脚本，它会将模块文件合并并编译：

```bash
python tools/i18n/build_mo.py
```


## 迁移现有 Action

对于现有的 Action（如 `Assassinate`），按以下步骤迁移：

### 步骤 1：替换类变量

**修改前**：
```python
class OldAction(InstantAction):
    ACTION_NAME = "旧动作"
    DESC = "这是旧动作的描述"
```

**修改后**：
```python
class OldAction(InstantAction):
    ACTION_NAME_ID = "old_action_name"
    DESC_ID = "old_action_description"
```

### 步骤 2：更新引用

**修改前**：
```python
# 在代码中直接使用
text = f"执行了{self.ACTION_NAME}"
```

**修改后**：
```python
# 使用类方法获取
text = f"执行了{self.get_action_name()}"
```

### 步骤 3：动态文本改用 t()

**修改前**：
```python
event_text = f"{self.avatar.name} 开始了动作"
```

**修改后**：
```python
from src.i18n import t
event_text = t("{avatar} started the action", avatar=self.avatar.name)
```

## 最佳实践

1. **msgid 使用英文**：便于回退和调试
2. **msgid 具有描述性**：如 `assassinate_action_name` 而非 `act1`
3. **占位符使用具名参数**：`{avatar}` 而非 `%s`
4. **完整句子作为 msgid**：不要拼接字符串
5. **添加注释**：在 po 文件中标注每个 msgid 的用途

## 测试

```python
# 切换语言
from src.classes.language import language_manager
language_manager.set_language("zh-CN")

# 测试翻译
from src.classes.action.assassinate import Assassinate
print(Assassinate.get_action_name())  # 输出：暗杀

# 切换到英文
language_manager.set_language("en-US")
print(Assassinate.get_action_name())  # 输出：Assassinate
```

## MutualAction 多语言支持

### 基类增强 (`src/classes/mutual_action/mutual_action.py`)

**类变量**（子类覆盖）：
```python
ACTION_NAME_ID: str = ""
DESC_ID: str = ""
REQUIREMENTS_ID: str = ""
STORY_PROMPT_ID: str = ""
FEEDBACK_LABEL_IDS: dict[str, str] = {...}  # 反馈标签 msgid 映射
```

**类方法**：
```python
@classmethod
def get_feedback_label(cls, feedback_name: str) -> str:
    """获取反馈标签的翻译"""

@classmethod
def get_story_prompt(cls) -> str:
    """获取故事提示词的翻译"""
```

### 示例实现 (`src/classes/mutual_action/dual_cultivation.py`)

```python
@cooldown_action
class DualCultivation(MutualAction):
    # 多语言 ID
    ACTION_NAME_ID = "dual_cultivation_action_name"
    DESC_ID = "dual_cultivation_description"
    REQUIREMENTS_ID = "dual_cultivation_requirements"
    STORY_PROMPT_ID = "dual_cultivation_story_prompt"
    
    # 不需要翻译的常量
    EMOJI = "💕"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["Accept", "Reject"]
    
    def start(self, target_avatar: "Avatar|str") -> Event:
        from src.i18n import t
        # 使用 t() 翻译动态文本
        content = t("{initiator} invites {target} for dual cultivation",
                   initiator=self.avatar.name, target=target_name)
        # ...
```

### 反馈标签翻译

在 PO 文件中定义通用反馈标签：
```po
# Feedback labels
msgid "feedback_accept"
msgstr "接受" / "Accept"

msgid "feedback_reject"
msgstr "拒绝" / "Reject"

msgid "feedback_yield"
msgstr "让步" / "Yield"
```

## 已支持的 Action

### InstantAction & TimedAction
- ✅ `Assassinate` - 暗杀
- ✅ `Attack` - 发起战斗
- ✅ `Breakthrough` - 突破
- ✅ `Buy` - 购买
- ✅ `Cast` - 铸造
- ✅ `Catch` - 御兽
- ✅ `Cultivate` - 修炼
- ✅ `DevourMortals` - 吞噬凡人
- ✅ `Escape` - 逃离
- ✅ `Harvest` - 采集
- ✅ `HelpMortals` - 帮助凡人
- ✅ `Hunt` - 狩猎
- ✅ `Mine` - 挖矿
- ✅ `Move` - 移动（基类）
- ✅ `MoveAwayFromAvatar` - 远离角色
- ✅ `MoveAwayFromRegion` - 离开区域
- ✅ `MoveToAvatar` - 移动到角色
- ✅ `MoveToDirection` - 移动探索
- ✅ `MoveToRegion` - 移动到区域
- ✅ `NurtureWeapon` - 温养兵器
- ✅ `Play` - 消遣
- ✅ `PlunderMortals` - 搜刮凡人
- ✅ `Refine` - 炼丹
- ✅ `SelfHeal` - 疗伤
- ✅ `Sell` - 出售

### MutualAction
- ✅ `MutualAttack` - 攻击（互动版）
- ✅ `Conversation` - 交谈
- ✅ `DriveAway` - 驱赶
- ✅ `DualCultivation` - 双修
- ✅ `Gift` - 赠送
- ✅ `Impart` - 传道
- ✅ `Occupy` - 抢夺洞府
- ✅ `Spar` - 切磋
- ✅ `Talk` - 攀谈

## TODO

- [x] 遍历所有 Action 并添加多语言支持
- [x] 为 MutualAction 添加类似的基类方法
- [x] 考虑为 LLM 提示词创建统一的辅助方法
