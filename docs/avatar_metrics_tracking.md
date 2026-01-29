# Avatar 狀態追蹤功能

## 概述

新增可選的 Avatar 狀態追蹤功能，用於記錄角色成長軌跡。該功能預設關閉，不影響現有遊戲邏輯。

## 功能特點

- **可選性**：預設關閉，不影響現有功能
- **輕量**：僅記錄關鍵指標（修為、資源、社交等）
- **不可變**：快照一旦創建不修改
- **持久化**：支援存檔/讀檔
- **自動清理**：預設最多保留 1200 筆記錄（100 年）

## 使用方式

### 啟用追蹤

```python
# 啟用 Avatar 狀態追蹤
avatar.enable_metrics_tracking = True
```

### 自動記錄

追蹤啟用後，模擬器會在每月自動調用 `record_metrics()`：

```python
# 在 simulator.py 的 _finalize_step() 中自動執行
# avatar.record_metrics()  # 每月自動調用
```

### 手動記錄並標記事件

```python
from src.classes.avatar_metrics import MetricTag

# 手動記錄狀態（可選事件標記）
avatar.record_metrics(tags=["breakthrough"])
avatar.record_metrics(tags=[MetricTag.INJURED.value, MetricTag.BATTLE.value])
avatar.record_metrics(tags=["custom_event"])  # 支援自定義標籤
```

### 查看摘要

```python
# 獲取狀態追蹤摘要
summary = avatar.get_metrics_summary()
print(summary)
# 輸出示例：
# {
#     "enabled": True,
#     "count": 120,
#     "first_record": 100,
#     "latest_record": 220,
#     "cultivation_growth": 5
# }
```

### 訪問歷史記錄

```python
# 直接訪問歷史記錄列表
for metrics in avatar.metrics_history:
    print(f"Month {metrics.timestamp}: Level {metrics.cultivation_level}, HP {metrics.hp}")
```

## 設計原則

### 1. 可選性

- 預設關閉（`enable_metrics_tracking = False`）
- 不影響現有 API 和邏輯
- 可隨時啟用或禁用

### 2. 輕量級

僅記錄關鍵指標：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `timestamp` | `MonthStamp` | 記錄時間 |
| `age` | `int` | 年齡 |
| `cultivation_level` | `int` | 修為等級 |
| `cultivation_progress` | `int` | 修為進度 |
| `hp` | `float` | 當前生命值 |
| `hp_max` | `float` | 最大生命值 |
| `spirit_stones` | `int` | 靈石數量 |
| `relations_count` | `int` | 關係數量 |
| `known_regions_count` | `int` | 已知區域數量 |
| `tags` | `List[str]` | 事件標籤 |

### 3. 不可變性

- 快照一旦創建不修改
- 使用 dataclass 保證結構清晰
- 支援序列化/反序列化

### 4. 向後兼容

- 使用 `default_factory` 避免破壞舊代碼
- 存檔/讀檔完全兼容
- 舊存檔會使用默認值（空列表、False）

## 性能影響

### 關閉時

- 零影響（不佔用額外記憶體或 CPU）
- `record_metrics()` 直接返回 `None`

### 開啟時

- 每月新增約 200 bytes 快照
- 100 年約 240 KB
- **有上限**：預設最多保留 1200 筆記錄（可通過 `max_metrics_history` 調整）

```python
# 調整歷史記錄上限
avatar.max_metrics_history = 600  # 改為 50 年
```

## 預設標籤

建議使用 `MetricTag` 枚舉中的預設標籤：

| 標籤 | 值 | 說明 |
|------|-----|------|
| `BREAKTHROUGH` | `"breakthrough"` | 突破 |
| `INJURED` | `"injured"` | 受傷 |
| `RECOVERED` | `"recovered"` | 康復 |
| `SECT_JOIN` | `"sect_join"` | 加入宗門 |
| `SECT_LEAVE` | `"sect_leave"` | 離開宗門 |
| `TECHNIQUE_LEARN` | `"technique_learn"` | 學習功法 |
| `DEATH` | `"death"` | 死亡 |
| `BATTLE` | `"battle"` | 戰鬥 |
| `DUNGEON` | `"dungeon"` | 探索秘境 |

### 使用標籤

```python
from src.classes.avatar_metrics import MetricTag

# 使用枚舉（推薦）
avatar.record_metrics(tags=[MetricTag.BREAKTHROUGH.value])

# 多個標籤
avatar.record_metrics(tags=[
    MetricTag.INJURED.value,
    MetricTag.BATTLE.value
])

# 自定義標籤（也支援）
avatar.record_metrics(tags=["custom_event", "special_occurrence"])
```

## 數據結構

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
        """轉換為可序列化的字典"""
        pass

    @classmethod
    def from_save_dict(cls, data: dict) -> "AvatarMetrics":
        """從字典重建"""
        pass
```

## 序列化

### 存檔

狀態追蹤數據會自動包含在存檔中：

```python
save_dict = avatar.to_save_dict()
# 包含：
# - "metrics_history": [...]
# - "enable_metrics_tracking": True
```

### 讀檔

讀檔時自動恢復：

```python
avatar = Avatar.from_save_dict(data, world)
# metrics_history 和 enable_metrics_tracking 自動恢復
```

## 注意事項

### 1. 標籤的可變性

`tags` 欄位使用 `List[str]` 而非 `List[MetricTag]`，提供靈活性：
- 支援預設標籤（使用 `MetricTag.value`）
- 支援自定義標籤
- 允許混合使用

### 2. 自動清理

歷史記錄超過 `max_metrics_history` 時會自動清理舊記錄：
```python
# 保留最新的 N 筆記錄
if len(self.metrics_history) > self.max_metrics_history:
    self.metrics_history = self.metrics_history[-self.max_metrics_history:]
```

### 3. 不可變性

快照對象本身是可變的（Python dataclass 預設），但設計上應視為不可變：
- 創建後不修改 `AvatarMetrics` 對象
- 如需更新，創建新快照

## 使用場景

### 追蹤修為成長

```python
# 啟用追蹤
avatar.enable_metrics_tracking = True

# 模擬運行...
# 自動記錄每月狀態

# 分析成長
first = avatar.metrics_history[0]
latest = avatar.metrics_history[-1]
print(f"修為增長: {latest.cultivation_level - first.cultivation_level}")
```

### 標記重大事件

```python
# 突破時標記
if avatar.cultivation_progress.realm != old_realm:
    avatar.record_metrics(tags=[MetricTag.BREAKTHROUGH.value])

# 受傷時標記
if avatar.hp.value < avatar.hp.max_value * 0.3:
    avatar.record_metrics(tags=[MetricTag.INJURED.value])
```

### 分析遊戲數據

```python
# 導出數據到 CSV/Pandas
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

## 相關文件

- [Avatar 類實現](../src/classes/avatar/core.py)
- [測試用例](../tests/test_avatar_metrics.py)
- [PR 規劃文檔](../Library/開發/cultivation-world-simulator/pr_plan_001_avatar_metrics.md)

## 更新日誌

- **2026-01-29**：初始版本（PR #1）
  - 新增 `AvatarMetrics` 類
  - 新增 `record_metrics()` 和 `get_metrics_summary()` 方法
  - 支援存檔/讀檔
  - 完整測試覆蓋
