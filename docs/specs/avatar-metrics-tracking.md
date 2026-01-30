# Avatar 状态追踪功能

## 概述

新增可选的 Avatar 状态追踪功能，用于记录角色成长轨迹。该功能默认关闭，不影响现有游戏逻辑。

## 功能特点

- **可选性**：默认关闭，不影响现有功能
- **轻量**：仅记录关键指标（修为、资源、社交等）
- **不可变**：快照一旦创建不修改
- **持久化**：支持存档/读档
- **自动清理**：默认最多保留 1200 笔记录（100 年）

## 使用方式

### 启用追踪

```python
# 启用 Avatar 状态追踪
avatar.enable_metrics_tracking = True
```

### 自动记录

追踪启用后，模拟器会在每月自动调用 `record_metrics()`：

```python
# 在 simulator.py 的 _finalize_step() 中自动执行
# avatar.record_metrics()  # 每月自动调用
```

### 手动记录并标记事件

```python
from src.classes.avatar_metrics import MetricTag

# 手动记录状态（可选事件标记）
avatar.record_metrics(tags=["breakthrough"])
avatar.record_metrics(tags=[MetricTag.INJURED.value, MetricTag.BATTLE.value])
avatar.record_metrics(tags=["custom_event"])  # 支持自定义标签
```

### 查看摘要

```python
# 获取状态追踪摘要
summary = avatar.get_metrics_summary()
print(summary)
# 输出示例：
# {
#     "enabled": True,
#     "count": 120,
#     "first_record": 100,
#     "latest_record": 220,
#     "cultivation_growth": 5
# }
```

### 访问历史记录

```python
# 直接访问历史记录列表
for metrics in avatar.metrics_history:
    print(f"Month {metrics.timestamp}: Level {metrics.cultivation_level}, HP {metrics.hp}")
```

## 设计原则

### 1. 可选性

- 默认关闭（`enable_metrics_tracking = False`）
- 不影响现有 API 和逻辑
- 可随时启用或禁用

### 2. 轻量级

仅记录关键指标：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | `MonthStamp` | 记录时间 |
| `age` | `int` | 年龄 |
| `cultivation_level` | `int` | 修为等级 |
| `cultivation_progress` | `int` | 修为进度 |
| `hp` | `float` | 当前生命值 |
| `hp_max` | `float` | 最大生命值 |
| `spirit_stones` | `int` | 灵石数量 |
| `relations_count` | `int` | 关系数量 |
| `known_regions_count` | `int` | 已知区域数量 |
| `tags` | `List[str]` | 事件标签 |

### 3. 不可变性

- 快照一旦创建不修改
- 使用 dataclass 保证结构清晰
- 支持序列化/反序列化

### 4. 向后兼容

- 使用 `default_factory` 避免破坏旧代码
- 存档/读档完全兼容
- 旧存档会使用默认值（空列表、False）

## 性能影响

### 关闭时

- 零影响（不占用额外内存或 CPU）
- `record_metrics()` 直接返回 `None`

### 开启时

- 每月新增约 200 bytes 快照
- 100 年约 240 KB
- **有上限**：默认最多保留 1200 笔记录（可通过 `max_metrics_history` 调整）

```python
# 调整历史记录上限
avatar.max_metrics_history = 600  # 改为 50 年
```

## 默认标签

建议使用 `MetricTag` 枚举中的默认标签：

| 标签 | 值 | 说明 |
|------|-----|------|
| `BREAKTHROUGH` | `"breakthrough"` | 突破 |
| `INJURED` | `"injured"` | 受伤 |
| `RECOVERED` | `"recovered"` | 康复 |
| `SECT_JOIN` | `"sect_join"` | 加入宗门 |
| `SECT_LEAVE` | `"sect_leave"` | 离开宗门 |
| `TECHNIQUE_LEARN` | `"technique_learn"` | 学习功法 |
| `DEATH` | `"death"` | 死亡 |
| `BATTLE` | `"battle"` | 战斗 |
| `DUNGEON` | `"dungeon"` | 探索秘境 |

### 使用标签

```python
from src.classes.avatar_metrics import MetricTag

# 使用枚举（推荐）
avatar.record_metrics(tags=[MetricTag.BREAKTHROUGH.value])

# 多个标签
avatar.record_metrics(tags=[
    MetricTag.INJURED.value,
    MetricTag.BATTLE.value
])

# 自定义标签（也支持）
avatar.record_metrics(tags=["custom_event", "special_occurrence"])
```

## 数据结构

### AvatarMetrics

```python
@dataclass
class AvatarMetrics:
    timestamp: MonthStamp
    age: int
    cultivation_level: int
    cultivation_progress: int
    hp: float
    hp_max: float
    spirit_stones: int
    relations_count: int
    known_regions_count: int
    tags: List[str]

    def to_save_dict(self) -> dict:
        """转换为可序列化的字典"""
        pass

    @classmethod
    def from_save_dict(cls, data: dict) -> "AvatarMetrics":
        """从字典重建"""
        pass
```

## 序列化

### 存档

状态追踪数据会自动包含在存档中：

```python
save_dict = avatar.to_save_dict()
# 包含：
# - "metrics_history": [...]
# - "enable_metrics_tracking": True
```

### 读档

读档时自动恢复：

```python
avatar = Avatar.from_save_dict(data, world)
# metrics_history 和 enable_metrics_tracking 自动恢复
```

## 注意事项

### 1. 标签的可变性

`tags` 字段使用 `List[str]` 而非 `List[MetricTag]`，提供灵活性：
- 支持默认标签（使用 `MetricTag.value`）
- 支持自定义标签
- 允许混合使用

### 2. 自动清理

历史记录超过 `max_metrics_history` 时会自动清理旧记录：
```python
# 保留最新的 N 笔记录
if len(self.metrics_history) > self.max_metrics_history:
    self.metrics_history = self.metrics_history[-self.max_metrics_history:]
```

### 3. 不可变性

快照对象本身是可变的（Python dataclass 默认），但设计上应视为不可变：
- 创建后不修改 `AvatarMetrics` 对象
- 如需更新，创建新快照

## 使用场景

### 追踪修为成长

```python
# 启用追踪
avatar.enable_metrics_tracking = True

# 模拟运行...
# 自动记录每月状态

# 分析成长
first = avatar.metrics_history[0]
latest = avatar.metrics_history[-1]
print(f"修为增长: {latest.cultivation_level - first.cultivation_level}")
```

### 标记重大事件

```python
# 突破时标记
if avatar.cultivation_progress.realm != old_realm:
    avatar.record_metrics(tags=[MetricTag.BREAKTHROUGH.value])

# 受伤时标记
if avatar.hp.value < avatar.hp.max_value * 0.3:
    avatar.record_metrics(tags=[MetricTag.INJURED.value])
```

### 分析游戏数据

```python
# 导出数据到 CSV/Pandas
import pandas as pd

data = []
for metrics in avatar.metrics_history:
    data.append({
        "timestamp": metrics.timestamp,
        "age": metrics.age,
        "level": metrics.cultivation_level,
        "hp": metrics.hp,
        "spirit_stones": metrics.spirit_stones,
    })

df = pd.DataFrame(data)
df.plot(x="timestamp", y="level")
```
