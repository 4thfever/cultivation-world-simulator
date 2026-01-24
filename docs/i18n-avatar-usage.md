# Avatar 系统多语言使用指南

本文档说明 Avatar 系统的多语言支持实现。

## 已完成的改动

### 1. `src/classes/avatar/core.py` 重构

修改了两个方法，将硬编码的 "散修" 改为使用翻译函数：

#### **get_sect_str() 方法**

**修改前**：
```python
def get_sect_str(self) -> str:
    if self.sect is None:
        return "散修"
    # ...
```

**修改后**：
```python
def get_sect_str(self) -> str:
    from src.i18n import t
    if self.sect is None:
        return t("Rogue Cultivator")
    # ...
```

#### **get_sect_rank_name() 方法**

**修改前**：
```python
def get_sect_rank_name(self) -> str:
    if self.sect is None or self.sect_rank is None:
        return "散修"
    # ...
```

**修改后**：
```python
def get_sect_rank_name(self) -> str:
    from src.i18n import t
    if self.sect is None or self.sect_rank is None:
        return t("Rogue Cultivator")
    # ...
```

---

### 2. `src/classes/avatar/action_mixin.py` 重构

修改了 `get_planned_actions_str()` 方法：

**修改前**：
```python
def get_planned_actions_str(self: "Avatar") -> str:
    if not self.planned_actions:
        return "无"
    # ...
```

**修改后**：
```python
def get_planned_actions_str(self: "Avatar") -> str:
    from src.i18n import t
    if not self.planned_actions:
        return t("None")
    # ...
```

---

### 3. `src/classes/avatar/info_presenter.py` 重构（核心文件）

这是本次重构的核心文件，包含大量用户可见文本的国际化。

#### **3.1 默认值统一翻译**

将所有硬编码的默认值改为翻译函数调用：

```python
# "无" -> t("None")
weapon_info = avatar.weapon.get_info() if avatar.weapon else t("None")

# "未知" -> t("Unknown")
alignment_info = avatar.alignment.get_info() if avatar.alignment else t("Unknown")

# "散修" -> t("Rogue Cultivator")
sect = to_avatar.sect.name if to_avatar.sect else t("Rogue Cultivator")

# "弟子" -> t("Disciple")
sect_info["rank"] = t("Disciple")
```

#### **3.2 分隔符国际化**

```python
# 关系分隔符：中文 "；" / 英文 "; "
relations_info = t("relation_separator").join(relation_lines) if relation_lines else t("None")

# 元素分隔符：中文 "、" / 英文 ", "
elements = t("element_separator").join(str(e) for e in avatar.root.elements)

# 材料分隔符：中文 "，" / 英文 ", "
materials_info = t("material_separator").join([...]) if avatar.materials else t("None")
```

#### **3.3 info_dict 键名翻译**

`get_avatar_info()` 函数返回的字典，所有键名都改为翻译：

**修改前**：
```python
info_dict = {
    "名字": avatar.name,
    "性别": str(avatar.gender),
    "年龄": str(avatar.age),
    "hp": str(avatar.hp),
    # ... 20+ 项
}
```

**修改后**：
```python
info_dict = {
    t("Name"): avatar.name,
    t("Gender"): str(avatar.gender),
    t("Age"): str(avatar.age),
    t("HP"): str(avatar.hp),
    t("Spirit Stones"): magic_stone_info,
    t("Relations"): relations_info,
    t("Sect"): sect_info,
    t("Alignment"): alignment_info,
    t("Region"): region_info,
    t("Spirit Root"): root_info,
    t("Technique"): technique_info,
    t("Realm"): cultivation_info,
    t("Traits"): personas_info,
    t("Materials"): materials_info,
    t("Appearance"): appearance_info,
    t("Weapon"): weapon_info,
    t("Auxiliary"): auxiliary_info,
    t("Emotion"): avatar.emotion.value,
    t("Long-term Goal"): avatar.long_term_objective.content if avatar.long_term_objective else t("None"),
    t("Short-term Goal"): avatar.short_term_objective if avatar.short_term_objective else t("None"),
}

if detailed:
    info_dict[t("Current Effects")] = _get_effects_text(avatar)

if avatar.nickname is not None:
    info_dict[t("Nickname")] = avatar.nickname.value

if avatar.spirit_animal is not None:
    info_dict[t("Spirit Animal")] = spirit_animal_info
```

#### **3.4 格式化字符串翻译**

所有复杂的格式化字符串都使用占位符模式：

```python
# 武器信息（带熟练度）
weapon_info = t("{weapon_name}, Proficiency: {proficiency}%", 
               weapon_name=avatar.weapon.get_detailed_info(), 
               proficiency=f"{avatar.weapon_proficiency:.1f}") if avatar.weapon else t("None")

# 观察到的角色
observed.append(t("{name}, Realm: {realm}", 
                 name=other.name, 
                 realm=other.cultivation_progress.get_info()))

# 动作状态
"action_state": t("Performing {action}", action=avatar.current_action_name)

# 灵根元素描述
"desc": t("Contains elements: {elements}", 
         elements=t("element_separator").join(str(e) for e in avatar.root.elements))

# 角色基础描述
lines = [t("【{name}】 {gender} {age} years old", 
          name=avatar.name, gender=avatar.gender, age=avatar.age)]
lines.append(t("Realm: {realm}", realm=avatar.cultivation_progress.get_info()))
lines.append(t("Identity: {identity}", identity=avatar.get_sect_str()))
```

#### **3.5 其他字段键名翻译**

在 `get_avatar_expanded_info()` 中：

```python
info[t("Nearby Avatars")] = observed
info[t("Major Events")] = major_list
info[t("Recent Events")] = minor_list
```

#### **3.6 复杂信息串翻译**

`get_other_avatar_info()` 函数的整个返回字符串改为使用翻译：

**修改前**：
```python
return (
    f"{to_avatar.name}，绰号：{nickname}，境界：{to_avatar.cultivation_progress.get_info()}，"
    f"关系：{relation}，宗门：{sect}，阵营：{alignment}，"
    f"外貌：{to_avatar.appearance.get_info()}，功法：{tech}，兵器：{weapon}，辅助：{aux}，HP：{to_avatar.hp}"
)
```

**修改后**：
```python
return t(
    "{name}, Nickname: {nickname}, Realm: {realm}, Relation: {relation}, Sect: {sect}, Alignment: {alignment}, Appearance: {appearance}, Technique: {technique}, Weapon: {weapon}, Auxiliary: {aux}, HP: {hp}",
    name=to_avatar.name,
    nickname=nickname,
    realm=to_avatar.cultivation_progress.get_info(),
    relation=relation,
    sect=sect,
    alignment=alignment,
    appearance=to_avatar.appearance.get_info(),
    technique=tech,
    weapon=weapon,
    aux=aux,
    hp=to_avatar.hp
)
```

---

## PO 文件新增条目

共新增约 **40+ 条翻译**：

### 字段标签（23 项）
- `Name` - 名字 / Name
- `Gender` - 性别 / Gender
- `Age` - 年龄 / Age
- `HP` - hp / HP
- `Spirit Stones` - 灵石 / Spirit Stones
- `Relations` - 关系 / Relations
- `Sect` - 宗门 / Sect
- `Alignment` - 阵营 / Alignment
- `Region` - 地区 / Region
- `Spirit Root` - 灵根 / Spirit Root
- `Technique` - 功法 / Technique
- `Realm` - 境界 / Realm
- `Traits` - 特质 / Traits
- `Materials` - 材料 / Materials
- `Appearance` - 外貌 / Appearance
- `Weapon` - 兵器 / Weapon
- `Auxiliary` - 辅助装备 / Auxiliary
- `Emotion` - 情绪 / Emotion
- `Long-term Goal` - 长期目标 / Long-term Goal
- `Short-term Goal` - 短期目标 / Short-term Goal
- `Current Effects` - 当前效果 / Current Effects
- `Nickname` - 绰号 / Nickname
- `Spirit Animal` - 灵兽 / Spirit Animal

### 扩展信息标签（3 项）
- `Nearby Avatars` - 周围角色 / Nearby Avatars
- `Major Events` - 重大事件 / Major Events
- `Recent Events` - 短期事件 / Recent Events

### 默认值（4 项）
- `None` - 无 / None
- `Unknown` - 未知 / Unknown
- `Rogue Cultivator` - 散修 / Rogue Cultivator
- `Disciple` - 弟子 / Disciple

### 分隔符（3 项）
- `relation_separator` - ；/ ; 
- `element_separator` - 、/ , 
- `material_separator` - ，/ , 

### 格式化字符串（8 项）
- `{weapon_name}, Proficiency: {proficiency}%` - 武器和熟练度
- `{name}, Realm: {realm}` - 名字和境界
- `Performing {action}` - 正在执行动作
- `Contains elements: {elements}` - 包含元素
- `【{name}】 {gender} {age} years old` - 角色基础描述
- `Realm: {realm}` - 境界标签
- `Identity: {identity}` - 身份标签
- `\n--- Current Effects Detail ---` - 效果明细标题
- `No additional effects` - 无额外效果
- 复杂的 `get_other_avatar_info` 格式化字符串

---

## 使用示例

### 获取角色信息

```python
from src.classes.avatar import Avatar

# 获取基础信息（字典键名自动翻译）
info = avatar.get_avatar_info(detailed=False)
# 中文环境：{"名字": "李云", "性别": "男", ...}
# 英文环境：{"Name": "Li Yun", "Gender": "Male", ...}

# 获取详细信息
detailed_info = avatar.get_avatar_info(detailed=True)
```

### 获取角色描述文本

```python
# 获取简要描述
desc = avatar.get_avatar_desc(detailed=False)
# 中文：【李云】 男 23岁\n境界: 筑基初期\n身份: 天剑宗内门弟子
# 英文：【Li Yun】 Male 23 years old\nRealm: Foundation Early\nIdentity: ...

# 获取详细描述（包含效果分析）
detailed_desc = avatar.get_avatar_desc(detailed=True)
```

### 获取宗门信息

```python
# 获取宗门显示名（含职位）
sect_str = avatar.get_sect_str()
# 中文：天剑宗内门弟子 / 散修
# 英文：Heaven Sword Sect Inner Disciple / Rogue Cultivator

# 仅获取职位
rank_str = avatar.get_sect_rank_name()
# 中文：内门弟子 / 散修
# 英文：Inner Disciple / Rogue Cultivator
```

### 获取计划动作

```python
# 获取计划动作列表字符串
plans_str = avatar.get_planned_actions_str()
# 中文：无 / 1. 修炼 (参数: ...) \n 2. 突破 (参数: ...)
# 英文：None / 1. Cultivate (params: ...) \n 2. Breakthrough (params: ...)
```

---

## 设计决策

### ✅ 采用的方案

1. **info_dict 键名直接翻译**
   - 原因：返回的字典直接用于显示，翻译键名最直接
   - 方案：使用 `t("Key")` 作为字典键
   - 优势：一次性解决，无需后续处理

2. **统一默认值文本**
   - "无" → `t("None")`
   - "未知" → `t("Unknown")`
   - "散修" → `t("Rogue Cultivator")`
   - "弟子" → `t("Disciple")`
   - 优势：保持一致性，易于维护

3. **格式化字符串使用占位符**
   - 复杂字符串拆分为带占位符的模板
   - 使用 `t("{key}: {value}", key=k, value=v)` 格式
   - 优势：翻译灵活，支持不同语言的语序

4. **分隔符可配置**
   - 中文：顿号（、）、分号（；）、逗号（，）
   - 英文：逗号（, ）、分号（; ）
   - 优势：符合各语言的标点使用习惯

---

## 测试

```python
# 切换语言
from src.classes.language import language_manager

# 测试中文
language_manager.set_language("zh-CN")
info = avatar.get_avatar_info()
print(info[t("Name")])  # 输出键名为中文的字典

# 测试英文
language_manager.set_language("en-US")
info = avatar.get_avatar_info()
print(info[t("Name")])  # 输出键名为英文的字典
```

---

## 最佳实践

1. **新增字段时同步添加翻译**：
   - 在 `info_presenter.py` 添加新字段时
   - 使用 `t("New Field Label")` 作为键名
   - 在 PO 文件添加对应翻译

2. **保持命名规范**：
   - 字段名使用英文，首字母大写（如 `"Spirit Root"`）
   - 默认值使用简短英文（如 `"None"`, `"Unknown"`）
   - 分隔符使用下划线命名（如 `"relation_separator"`）

3. **格式化字符串命名**：
   - 使用描述性占位符名称（如 `{weapon_name}`, `{proficiency}`）
   - 保持占位符在中英文翻译中一致

4. **测试多语言切换**：
   - 添加新翻译后测试切换语言是否正常显示
   - 检查分隔符和格式是否符合语言习惯

---

## 已完成

- ✅ 3 个文件修改（`core.py`, `action_mixin.py`, `info_presenter.py`）
- ✅ 约 40+ 条新翻译（字段标签、默认值、分隔符、格式化字符串）
- ✅ info_dict 完全国际化
- ✅ 所有用户可见文本国际化
- ✅ 统一默认值和分隔符处理

---

## 影响范围

Avatar 系统的本地化影响以下功能：

1. **角色信息展示** - `get_avatar_info()`, `get_avatar_structured_info()`
2. **角色描述生成** - `get_avatar_desc()`, `get_other_avatar_info()`
3. **扩展信息查询** - `get_avatar_expanded_info()`
4. **宗门信息显示** - `get_sect_str()`, `get_sect_rank_name()`
5. **计划动作显示** - `get_planned_actions_str()`

所有这些功能现在都完全支持多语言切换！🎉
