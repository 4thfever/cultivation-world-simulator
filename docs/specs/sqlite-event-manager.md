# SQLite EventManager 重构规范

## 概述

将 EventManager 从内存存储迁移到 SQLite，实现事件持久化、分页加载和更好的查询性能。

## 决策摘要

| 项目 | 决定 |
|------|------|
| 写入策略 | 实时写入（每个事件立即写入 SQLite） |
| 前端加载 | 分页加载，向上滚动加载更旧事件 |
| 每页数量 | 100 条 |
| 数据库位置 | 每个存档一个，格式 `{save_name}_events.db` |
| 索引策略 | SQLite 原生索引 |
| 数据清理 | 用户控制（提供"清理历史"按钮） |
| 旧数据迁移 | 自动迁移（加载时从 JSON 迁移到 SQLite） |
| 实时推送 | 保持现有 WebSocket 方式 |
| 错误处理 | 静默失败，记录日志但不影响游戏运行 |
| API 分页 | Cursor 分页（复合 cursor: month_stamp + rowid） |
| Pair 查询 | 在事件筛选器中增加"筛选两人"选项 |
| 多存档 | 支持，使用时间戳命名（如 `save_20260105_1423`） |
| 优先级 | **高** |

---

## 数据库设计

### 表结构

```sql
-- 事件主表
CREATE TABLE events (
    id TEXT PRIMARY KEY,              -- UUID
    month_stamp INTEGER NOT NULL,     -- 月份时间戳
    content TEXT NOT NULL,            -- 事件内容
    is_major BOOLEAN DEFAULT FALSE,   -- 是否为大事（长期记忆）
    is_story BOOLEAN DEFAULT FALSE,   -- 是否为故事事件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 事件-角色关联表
CREATE TABLE event_avatars (
    event_id TEXT NOT NULL,
    avatar_id TEXT NOT NULL,
    PRIMARY KEY (event_id, avatar_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_events_month_stamp ON events(month_stamp DESC);
CREATE INDEX idx_events_is_major ON events(is_major);
CREATE INDEX idx_event_avatars_avatar_id ON event_avatars(avatar_id);
CREATE INDEX idx_event_avatars_event_id ON event_avatars(event_id);
```

### 复合 Cursor 格式

```
{month_stamp}_{rowid}
```

使用 SQLite rowid 而非 UUID，保证同一 month_stamp 内的确定性排序（UUID 排序不稳定）。

示例: `1764_12345`

---

## API 设计

### GET /api/events

获取事件列表（分页）。

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| avatar_id | string | 否 | 按单个角色筛选 |
| avatar_id_1 | string | 否 | Pair 查询：角色 1 |
| avatar_id_2 | string | 否 | Pair 查询：角色 2（需同时提供 avatar_id_1） |
| cursor | string | 否 | 分页 cursor，获取该位置之前的事件 |
| limit | int | 否 | 每页数量，默认 100 |

**Response:**

```json
{
  "events": [
    {
      "id": "uuid",
      "text": "147年5月: 张三开始修炼",
      "content": "张三开始修炼",
      "year": 147,
      "month": 5,
      "month_stamp": 1764,
      "related_avatar_ids": ["avatar_id_1"],
      "is_major": false,
      "is_story": false
    }
  ],
  "next_cursor": "1764_12345",  // null 表示没有更多
  "has_more": true
}
```

### DELETE /api/events/cleanup

清理历史事件（用户触发）。

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keep_major | bool | 否 | 是否保留大事，默认 true |
| before_month_stamp | int | 否 | 删除此时间之前的事件 |

---

## 后端实现

### 新增文件

```
src/classes/event_storage.py     # SQLite 存储层
```

### 修改文件

```
src/classes/event_manager.py     # 重构为使用 SQLite
src/server/main.py               # 新增分页 API
src/sim/save/save_game.py        # 关联数据库文件
src/sim/load/load_game.py        # 加载时连接数据库
```

### EventStorage 类

```python
class EventStorage:
    """SQLite 事件存储层。"""

    def __init__(self, db_path: Path):
        """初始化数据库连接，创建表（如不存在）。"""

    def add_event(self, event: Event) -> bool:
        """
        写入单个事件。
        失败时记录日志并返回 False，不抛异常。
        """

    def get_events(
        self,
        avatar_id: str | None = None,
        avatar_id_pair: tuple[str, str] | None = None,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[Event], str | None]:
        """
        分页查询事件。
        返回 (events, next_cursor)。
        """

    def get_events_by_avatar(self, avatar_id: str, limit: int = 50) -> list[Event]:
        """后端用：获取角色相关事件（供 LLM prompt 使用）。"""

    def get_events_between(self, id1: str, id2: str, limit: int = 50) -> list[Event]:
        """后端用：获取两角色之间的事件。"""

    def cleanup(self, keep_major: bool = True, before: int | None = None) -> int:
        """清理事件，返回删除数量。"""

    def close(self):
        """关闭数据库连接。"""
```

### EventManager 重构

```python
class EventManager:
    """重构后的 EventManager，使用 SQLite 存储。"""

    def __init__(self, storage: EventStorage):
        self._storage = storage
        # 移除所有内存索引（_events, _by_avatar, _by_pair 等）

    def add_event(self, event: Event) -> None:
        """实时写入 SQLite。"""
        self._storage.add_event(event)

    # 其他查询方法委托给 storage
```

---

## 前端实现

### 修改文件

```
web/src/stores/world.ts                    # 事件状态管理
web/src/components/panels/EventPanel.vue   # 分页 UI
web/src/api/game.ts                        # 新增 API
```

### 事件状态管理

```typescript
// world.ts
interface EventState {
  events: GameEvent[];
  cursor: string | null;
  hasMore: boolean;
  isLoading: boolean;
}

// 新增 actions
async function loadMoreEvents(): Promise<void>;
async function resetEvents(avatarId?: string, avatarId2?: string): Promise<void>;
```

### EventPanel 改动

1. **向上滚动加载**：监听滚动事件，当接近顶部时触发 `loadMoreEvents()`
2. **筛选器扩展**：增加"筛选两人"选项
3. **加载指示器**：显示加载状态
4. **切换筛选重置**：切换角色时调用 `resetEvents()` 重新加载

### 筛选器 UI

```
[所有人 ▼] [+ 添加第二人]

// 选择第二人后变为：
[张三 ▼] [李四 ▼] [×]
```

---

## 存档系统整合

### 文件结构

```
assets/saves/
├── save_20260105_1423.json          # 游戏状态
├── save_20260105_1423_events.db     # 事件数据库
├── save_20260105_1500.json
└── save_20260105_1500_events.db
```

### 保存流程

1. 保存 JSON 存档（现有逻辑）
2. 确保数据库文件存在（实时写入已处理）
3. 可选：执行 `VACUUM` 优化数据库大小

### 加载流程

1. 读取 JSON 存档
2. 连接对应的 `_events.db` 文件
3. 如果数据库不存在，创建空数据库

### 新建游戏

1. 生成时间戳名称：`save_YYYYMMDD_HHMM`
2. 创建空数据库文件
3. 初始化游戏状态

---

## 错误处理

### SQLite 写入失败

```python
def add_event(self, event: Event) -> bool:
    try:
        # 写入逻辑
        return True
    except Exception as e:
        logger.error(f"Failed to write event: {e}")
        return False  # 不抛异常，游戏继续运行
```

### 数据库文件丢失

加载存档时，如果 `_events.db` 不存在：
- 记录警告日志
- 创建新的空数据库
- 游戏正常运行（但没有历史事件）

---

## TODO（未来扩展）

```python
# TODO(xzhseh): 事件搜索功能
# - 支持按关键词搜索事件内容
# - 可能需要 SQLite FTS5 扩展

# TODO(xzhseh): 事件分类/标签系统
# - 添加 event_type 字段（combat/cultivation/social/death 等）
# - 支持按类型筛选
```

---

## 实现顺序

1. **Phase 1: 后端核心** ✅
   - [x] 创建 `EventStorage` 类
   - [x] 重构 `EventManager`
   - [x] 修复 `event_id` → `id` bug
   - [x] 实现分页 API

2. **Phase 2: 存档整合** ✅
   - [x] 修改保存/加载逻辑
   - [x] 支持多存档槽位
   - [x] 时间戳命名

3. **Phase 3: 前端** ✅
   - [x] 分页加载 UI
   - [x] 向上滚动加载
   - [x] 双人筛选器

4. **Phase 4: 清理**
   - [x] 用户清理历史 API（`/api/events/cleanup`）
   - [ ] 清理历史 UI 按钮
   - [x] 移除旧的内存索引代码（EventManager 已重构）
