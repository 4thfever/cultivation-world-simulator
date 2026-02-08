# Effect 系统多语言使用指南

本文档说明 Effect 系统的多语言支持实现。

## 已完成的改动

### 1. `src/classes/effect/desc.py` 重构

将硬编码的中文映射字典改为使用翻译函数：

#### **Effect 名称翻译**

**修改前**：
```python
EFFECT_DESC_MAP = {
    "extra_max_hp": "最大生命值",
    "extra_battle_strength_points": "战力点数",
    # ... 30+ 项
}
```

**修改后**：
```python
def get_effect_desc(effect_key: str) -> str:
    """获取 effect 的描述名称（支持国际化）"""
    from src.i18n import t
    msgid_map = {
        "extra_max_hp": "effect_extra_max_hp",
        "extra_battle_strength_points": "effect_extra_battle_strength_points",
        # ...
    }
    msgid = msgid_map.get(effect_key, effect_key)
    return t(msgid)
```

#### **Action 名称翻译**

**修改前**：
```python
ACTION_DESC_MAP = {
    "DualCultivation": "双修",
    "DevourMortals": "吞噬凡人",
}
```

**修改后**：
```python
def get_action_short_name(action_name: str) -> str:
    """获取 action 的简短名称（复用 Action 系统翻译）"""
    from src.i18n import t
    msgid = f"action_{action_name.lower()}_short_name"
    return t(msgid)
```

#### **条件表达式翻译（简化方案）**

采用简化方案，保持代码形式，仅翻译前缀：

```python
def translate_condition(condition: str) -> str:
    """将代码形式的条件表达式转换为易读描述"""
    from src.i18n import t
    
    if not condition:
        return t("Conditional effect")
    
    # 特殊模式检测
    if "avatar.personas" in condition and "any" in condition:
        m = re.search(r'p\.name\s*==\s*["\'](.*?)["\']', condition)
        if m:
            return t("Has [{trait}] trait", trait=m.group(1))
    
    # 保持代码形式
    return t("When {condition}", condition=condition)
```

#### **Effect 文本格式化**

```python
def format_effects_to_text(effects: dict[str, Any] | list[dict[str, Any]]) -> str:
    """将 effects 字典转换为易读的文本描述"""
    from src.i18n import t
    
    # ... 处理逻辑 ...
    
    # 使用翻译的分隔符
    sep = t("effect_separator")  # "；" / "; "
    text = sep.join(desc_list)
    
    if effects.get("when"):
        cond = translate_condition(str(effects["when"]))
        return t("[{condition}] {effects}", condition=cond, effects=text)
    
    return text
```

### 2. `src/classes/effect/mixin.py` 重构

修改 `get_effect_breakdown()` 方法，使用翻译函数：

**修改前**：
```python
if self.sect:
    _collect(f"宗门【{self.sect.name}】", source_obj=self.sect)

if self.technique:
    _collect(f"功法【{self.technique.name}】", source_obj=self.technique)

_collect("灵根", source_obj=self.root)
# ...
```

**修改后**：
```python
from src.i18n import t

if self.sect:
    label = t("Sect [{name}]", name=self.sect.name)
    _collect(label, source_obj=self.sect)

if self.technique:
    label = t("Technique [{name}]", name=self.technique.name)
    _collect(label, source_obj=self.technique)

_collect(t("Spirit Root"), source_obj=self.root)
# ...
```

## PO 文件新增条目

共新增约 **60+ 条翻译**：

### Effect 名称（28 项）
- `effect_extra_max_hp` - 最大生命值 / Max HP
- `effect_extra_battle_strength_points` - 战力点数 / Battle Strength
- `effect_extra_cultivate_exp` - 修炼经验 / Cultivation Experience
- ... 等 25 项

### Action 简短名称（2 项）
- `action_dualcultivation_short_name` - 双修 / Dual Cultivation
- `action_devourmortals_short_name` - 吞噬凡人 / Devour Mortals

### 格式化相关（4 项）
- `action_list_separator` - 、 / , 
- `effect_separator` - ； / ; 
- `Special effect (dynamic)` - 特殊效果（动态）
- 条件翻译相关

### Effect 来源标签（9 项）
- `Sect [{name}]` - 宗门【{name}】
- `Technique [{name}]` - 功法【{name}】
- `Spirit Root` - 灵根
- `Trait [{name}]` - 特质【{name}】
- `Weapon [{name}]` - 兵器【{name}】
- `Auxiliary [{name}]` - 辅助【{name}】
- `Spirit Animal [{name}]` - 灵兽【{name}】
- `Heaven and Earth Phenomenon` - 天地灵机
- `Elixir [{name}]` - 丹药【{name}】

## 使用示例

### 获取 Effect 描述

```python
from src.classes.effect.desc import get_effect_desc

# 自动根据当前语言返回翻译
desc = get_effect_desc("extra_max_hp")
# 中文: "最大生命值"
# 英文: "Max HP"
```

### 格式化 Effect 文本

```python
from src.classes.effect.desc import format_effects_to_text

effects = {
    "extra_max_hp": 100,
    "extra_battle_strength_points": 3
}

text = format_effects_to_text(effects)
# 中文: "最大生命值 +100；战力点数 +3"
# 英文: "Max HP +100; Battle Strength +3"
```

### 带条件的 Effect

```python
effects = {
    "extra_battle_strength_points": 3,
    "when": "avatar.weapon.type == WeaponType.SWORD"
}

text = format_effects_to_text(effects)
# 中文: "[当avatar.weapon.type == WeaponType.SWORD] 战力点数 +3"
# 英文: "[When avatar.weapon.type == WeaponType.SWORD] Battle Strength +3"
```

### 自定义描述与条件 (高级用法)

对于复杂的动态效果（如包含公式）或特殊的代码条件判断，自动生成的文本可能难以阅读。此时可在 effects 配置中使用特殊字段进行覆盖。

#### 1. 覆盖整体描述 (`_desc`)

使用 `_desc` 字段指定一个翻译 Key，该 Key 对应的文本将直接替代整个 Effect 的自动生成描述。常用于隐藏复杂的计算公式。效果采用白描的叙述，不要参杂感情或者氛围叙述。

**CSV 配置示例**:
```json
{
    "extra_battle_strength_points": "3 + avatar.weapon_proficiency * 0.02",
    "_desc": "effect_god_slaying_spear_desc"
}
```

**PO 文件 (`static/locales/zh-CN/game_configs_modules/manual_effects.po`)**:
```po
msgid "effect_god_slaying_spear_desc"
msgstr "基于枪法资质提升战力"
```

**显示效果**: "基于枪法资质提升战力"

#### 2. 覆盖条件描述 (`when_desc`)

使用 `when_desc` 字段指定一个翻译 Key，用于替代 `when` 字段的代码表达式显示。

**CSV 配置示例**:
```json
{
    "when": "avatar.spirit_animal is not None",
    "when_desc": "condition_has_spirit_animal",
    "extra_battle_strength_points": 2
}
```

**PO 文件**:
```po
msgid "condition_has_spirit_animal"
msgstr "拥有本命灵兽时"
```

**显示效果**: "[拥有本命灵兽时] 战力点数 +2"

### 获取 Effect 来源明细

```python
# 在 Avatar 类中自动使用翻译
breakdown = avatar.get_effect_breakdown()
# 返回: [
#   ("宗门【天剑宗】", {"extra_battle_strength_points": 2}),
#   ("功法【太玄真经】", {"extra_cultivate_exp": 50}),
#   ("灵根", {"extra_max_hp": 30}),
#   ...
# ]
```

## 设计决策

### ✅ 采用的简化方案

1. **条件表达式保持代码形式**
   - 原因：条件表达式翻译复杂且容易出错
   - 方案：仅翻译前缀"当" / "When"，保持表达式本身为代码
   - 优势：简单可靠，对开发者友好

2. **百分比和数值符号不翻译**
   - 原因：`+`, `%`, `-` 等符号国际通用
   - 方案：保持原样，节省翻译工作量

3. **Action 名称复用现有翻译**
   - 原因：Action 系统已完成国际化
   - 方案：使用统一命名规则 `action_{name}_short_name`
   - 优势：避免重复维护

### 🎯 核心改动点

- ✅ 2 个文件修改（`desc.py`, `mixin.py`）
- ✅ 约 60+ 条新 msgid
- ✅ 难度较低，与 Action 系统模式一致

## 测试

```python
# 切换语言
from src.classes.language import language_manager

# 测试中文
language_manager.set_language("zh-CN")
from src.classes.effect.desc import get_effect_desc
print(get_effect_desc("extra_max_hp"))  # 输出：最大生命值

# 测试英文
language_manager.set_language("en-US")
print(get_effect_desc("extra_max_hp"))  # 输出：Max HP
```

## 最佳实践

1. **新增 Effect 时同步添加翻译**：
   - 在 `consts.py` 定义新 effect
   - 在 `desc.py` 的 `get_effect_desc()` 添加 msgid 映射
   - 在 `static/locales/{lang}/modules/effect.po` 添加中英文翻译

2. **保持命名规范**：
   - Effect msgid: `effect_{effect_key}`
   - Action msgid: `action_{action_name}_short_name`

3. **测试多语言切换**：
   - 添加新翻译后测试切换语言是否正常显示

## 已完成

- ✅ 28 个 Effect 名称国际化
- ✅ 9 个 Effect 来源标签国际化
- ✅ 条件表达式简化翻译方案
- ✅ Action 名称复用现有系统
- ✅ 格式化函数国际化
