# Gathering 系统多语言使用指南

本文档说明 Gathering 系统的多语言支持实现。

## 已完成的改动

### 1. `src/classes/gathering/auction.py` 重构

将硬编码的中文文本改为使用翻译函数，使拍卖会系统支持多语言。

#### **1.1 添加类变量和 classmethod（LLM Prompt）**

遵循 Action/MutualAction 系统的模式，为 LLM Prompt 添加统一的翻译支持：

**修改后**：
```python
@register_gathering
class Auction(Gathering):
    """拍卖会事件"""
    
    # 类变量 - LLM Prompt
    STORY_PROMPT_ID = "auction_story_prompt"
    
    @classmethod
    def get_story_prompt(cls) -> str:
        """获取故事生成提示词"""
        from src.i18n import t
        return t(cls.STORY_PROMPT_ID)
```

#### **1.2 get_info() 方法**

**修改前**：
```python
def get_info(self, world: "World") -> str:
    # TODO: Implement get_info
    return "拍卖会正在举行..."
```

**修改后**：
```python
def get_info(self, world: "World") -> str:
    from src.i18n import t
    return t("Auction is in progress...")
```

#### **1.3 _generate_auction_events() 方法 - 事件内容**

这是拍卖会生成事件记录的核心方法，有两种情况：有竞争和无竞争。

**修改前**：
```python
if len(bids) >= 2:
    runner_up = sorted_bids[1][0]
    content = f"在{item.name}的竞拍中，{winner.name}以 {deal_price} 灵石力压{runner_up.name}一头，将其收入囊中。"
    related_avatars = [winner.id, runner_up.id]
else:
    content = f"在拍卖会上，{winner.name}以 {deal_price} 灵石拍下了{item.name}。"
    related_avatars = [winner.id]
```

**修改后**：
```python
from src.i18n import t

if len(bids) >= 2:
    runner_up = sorted_bids[1][0]
    content = t(
        "In the auction for {item_name}, {winner_name} outbid {runner_up_name} with {price} spirit stones and won the item.",
        item_name=item.name,
        winner_name=winner.name,
        runner_up_name=runner_up.name,
        price=deal_price
    )
    related_avatars = [winner.id, runner_up.id]
else:
    content = t(
        "At the auction, {winner_name} acquired {item_name} for {price} spirit stones.",
        winner_name=winner.name,
        item_name=item.name,
        price=deal_price
    )
    related_avatars = [winner.id]
```

#### **1.4 _generate_story() 方法 - 故事生成文本**

这个方法为 StoryTeller 收集信息并生成故事，包含多处需要翻译的文本。

##### **成交信息和竞争信息**

**修改前**：
```python
# 收集成交信息
for item, (winner, deal_price) in deal_results.items():
    interaction_lines.append(f"成交：{winner.name}以{deal_price}灵石拍下{item.name}。")

# 收集竞争信息
for item, bids in willing_prices.items():
    if len(bids) < 2:
        continue
    sorted_bids = sorted(bids.items(), key=lambda x: x[1], reverse=True)
    winner = sorted_bids[0][0]
    runner_up = sorted_bids[1][0]
    interaction_lines.append(f"竞争：在{item.name}的竞拍中，{winner.name}力压{runner_up.name}（出价{sorted_bids[1][1]}）。")
```

**修改后**：
```python
from src.i18n import t

# 收集成交信息
for item, (winner, deal_price) in deal_results.items():
    interaction_lines.append(
        t("Deal: {winner_name} acquired {item_name} for {price} spirit stones.",
          winner_name=winner.name, item_name=item.name, price=deal_price)
    )

# 收集竞争信息
for item, bids in willing_prices.items():
    if len(bids) < 2:
        continue
    sorted_bids = sorted(bids.items(), key=lambda x: x[1], reverse=True)
    winner = sorted_bids[0][0]
    runner_up = sorted_bids[1][0]
    interaction_lines.append(
        t("Competition: In the auction for {item_name}, {winner_name} outbid {runner_up_name} (bid: {bid}).",
          item_name=item.name, winner_name=winner.name, 
          runner_up_name=runner_up.name, bid=sorted_bids[1][1])
    )
```

##### **物品信息格式**

**修改前**：
```python
items_info_list.append(f"物品：{item.name}，介绍：{info}")
```

**修改后**：
```python
items_info_list.append(
    t("Item: {item_name}, Description: {description}",
      item_name=item.name, description=info)
)
```

##### **场景设定**

**修改前**：
```python
gathering_info = (
    "事件类型：神秘拍卖会\n"
    "场景设定：拍卖会发生在一处神秘空间，由一位面目模糊、气息深不可测的神秘人主持。"
)
```

**修改后**：
```python
gathering_info = t(
    "Event Type: Mysterious Auction\nScene Setting: The auction takes place in a mysterious space, hosted by a mysterious figure with an unfathomable aura."
)
```

##### **标签文本**

**修改前**：
```python
if items_info_str:
    details_list.append("【涉及拍品信息】")
    details_list.append(items_info_str)
    
details_list.append("\n【相关角色信息】")
```

**修改后**：
```python
if items_info_str:
    details_list.append(t("【Auction Items Information】"))
    details_list.append(items_info_str)
    
details_list.append(t("\n【Related Avatars Information】"))
```

##### **LLM Prompt**

**修改前**：
```python
story = await StoryTeller.tell_gathering_story(
    gathering_info=gathering_info,
    events_text=interaction_result,
    details_text=details_text,
    related_avatars=list(related_avatars),
    prompt="选取其中最有趣的一个侧面或一次竞价进行描写，无需面面俱到。"
)
```

**修改后**：
```python
story = await StoryTeller.tell_gathering_story(
    gathering_info=gathering_info,
    events_text=interaction_result,
    details_text=details_text,
    related_avatars=list(related_avatars),
    prompt=self.get_story_prompt()
)
```

---

## PO 文件新增条目

共新增约 **10 条翻译**：

### 状态文本（1 项）
- `Auction is in progress...` - 拍卖会正在举行... / Auction is in progress...

### 事件内容（2 项）
- `In the auction for {item_name}, {winner_name} outbid {runner_up_name} with {price} spirit stones and won the item.` - 有竞争的拍卖
- `At the auction, {winner_name} acquired {item_name} for {price} spirit stones.` - 无竞争的拍卖

### 故事生成文本（3 项）
- `Deal: {winner_name} acquired {item_name} for {price} spirit stones.` - 成交信息
- `Competition: In the auction for {item_name}, {winner_name} outbid {runner_up_name} (bid: {bid}).` - 竞争信息
- `Item: {item_name}, Description: {description}` - 物品信息格式

### 场景设定（1 项）
- `Event Type: Mysterious Auction\nScene Setting: ...` - 神秘拍卖会场景设定

### 标签（2 项）
- `【Auction Items Information】` - 拍品信息标签
- `\n【Related Avatars Information】` - 角色信息标签

### LLM Prompt（1 项）
- `auction_story_prompt` - 故事生成提示词

---

## 使用示例

### 获取拍卖会状态

```python
from src.classes.gathering.auction import Auction

auction = Auction()

# 获取拍卖会信息（自动翻译）
info = auction.get_info(world)
# 中文: "拍卖会正在举行..."
# 英文: "Auction is in progress..."
```

### 生成拍卖事件

```python
# 拍卖会执行后会自动生成事件
events = await auction.execute(world)

# 有竞争的拍卖事件
# 中文: "在玄铁剑的竞拍中，李云以 1500 灵石力压王峰一头，将其收入囊中。"
# 英文: "In the auction for Mystic Iron Sword, Li Yun outbid Wang Feng with 1500 spirit stones and won the item."

# 无竞争的拍卖事件
# 中文: "在拍卖会上，李云以 800 灵石拍下了破虚丹。"
# 英文: "At the auction, Li Yun acquired Void-Breaking Pill for 800 spirit stones."
```

### 获取故事生成提示词

```python
# 使用 classmethod 获取翻译后的 prompt
prompt = Auction.get_story_prompt()
# 中文: "选取其中最有趣的一个侧面或一次竞价进行描写，无需面面俱到。"
# 英文: "Select the most interesting aspect or bidding moment to describe, no need to cover everything."
```

---

## 设计决策

### ✅ 采用的方案

1. **与 Action/MutualAction 系统保持一致**
   - 使用 `t()` 翻译函数
   - LLM Prompt 使用类变量 + classmethod 模式
   - 占位符格式化字符串
   - 优势：统一的代码风格，易于维护

2. **事件内容完全国际化**
   - 所有事件文本使用 `t()` 和占位符
   - 支持不同语言的语序和表达习惯
   - 优势：翻译灵活，自然流畅

3. **故事生成相关文本统一处理**
   - 交互结果文本使用固定模板
   - 标签文本使用翻译函数
   - LLM Prompt 可切换语言
   - 优势：StoryTeller 可以使用相应语言生成故事

4. **保持代码简洁**
   - 避免过多的字符串拼接
   - 使用完整的句子模板而非片段
   - 优势：符合用户的代码风格要求

---

## 测试

```python
# 切换语言
from src.classes.language import language_manager

# 测试中文
language_manager.set_language("zh-CN")
auction = Auction()
print(auction.get_info(world))  # 输出：拍卖会正在举行...
print(Auction.get_story_prompt())  # 输出中文提示词

# 测试英文
language_manager.set_language("en-US")
print(auction.get_info(world))  # 输出：Auction is in progress...
print(Auction.get_story_prompt())  # 输出英文提示词
```

---

## 最佳实践

1. **新增 Gathering 类型时同步添加翻译**：
   - 如果添加新的 Gathering 实现（如"宗门大比"、"秘境开启"）
   - 遵循相同的模式：类变量 + classmethod
   - 在 `static/locales/{lang}/modules/gathering.po` 添加对应翻译

2. **保持命名规范**：
   - LLM Prompt msgid 格式：`{gathering_type}_story_prompt`
   - 事件内容使用完整句子作为 msgid
   - 标签使用描述性文本作为 msgid

3. **格式化字符串命名**：
   - 使用描述性占位符名称（如 `{winner_name}`, `{item_name}`, `{price}`）
   - 保持占位符在中英文翻译中一致

4. **测试多语言切换**：
   - 添加新翻译后测试切换语言是否正常显示
   - 检查事件内容和故事生成是否符合语言习惯

---

## 已完成

- ✅ 1 个文件修改（`auction.py`）
- ✅ 约 10 条新翻译（状态、事件、故事文本、标签、Prompt）
- ✅ 完全国际化的拍卖会系统
- ✅ LLM Prompt 支持多语言
- ✅ 统一的代码模式

---

## 影响范围

Gathering 系统的本地化影响以下功能：

1. **拍卖会信息展示** - `get_info()`
2. **拍卖事件生成** - `_generate_auction_events()`
3. **故事生成** - `_generate_story()`
4. **LLM Prompt** - `get_story_prompt()`

所有这些功能现在都完全支持多语言切换！

---

## 扩展性

### 未来添加新 Gathering 类型的模板

如果需要添加新的 Gathering 类型（如"宗门大比"），可以参考以下模板：

```python
from src.classes.gathering.gathering import Gathering, register_gathering
from src.i18n import t

@register_gathering
class SectCompetition(Gathering):
    """宗门大比事件"""
    
    # 类变量
    STORY_PROMPT_ID = "sect_competition_story_prompt"
    
    @classmethod
    def get_story_prompt(cls) -> str:
        """获取故事生成提示词"""
        return t(cls.STORY_PROMPT_ID)
    
    def get_info(self, world: "World") -> str:
        return t("Sect competition is underway...")
    
    # ... 其他方法使用 t() 翻译所有文本
```

然后在 `static/locales/{lang}/modules/gathering.po` 添加对应翻译即可。

---

## 总结

Gathering 系统的本地化采用了与 Action/MutualAction 一致的模式，工作量小、易于维护、扩展性好。这是项目中最简单的本地化任务之一，只涉及 1 个文件和约 10 条翻译！🎉
