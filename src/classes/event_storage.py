"""
SQLite 事件存储层。

提供事件的持久化存储、分页查询和清理功能。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from contextlib import contextmanager
from datetime import datetime, timezone

from src.run.log import get_logger

if TYPE_CHECKING:
    from src.classes.event import Event

def _format_time(ts: float) -> str:
    """将 timestamp float 转换为 SQLite 兼容的 UTC 字符串"""
    return datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')

def _parse_time(ts_str: str) -> float:
    """将 SQLite 时间字符串解析为 timestamp float"""
    if not ts_str:
        return 0.0
    try:
        # 尝试带微秒的格式
        dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        try:
            # 尝试不带微秒的格式
            dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return 0.0
    # 假设数据库存的是 UTC (naive time string from sqlite usually treated as such)
    return dt.replace(tzinfo=timezone.utc).timestamp()

class EventStorage:
    """
    SQLite 事件存储层。

    提供：
    - 实时写入事件
    - 分页查询（cursor-based）
    - 按角色/角色对查询
    - 历史清理
    """

    def __init__(self, db_path: Path):
        """
        初始化数据库连接，创建表（如不存在）。

        Args:
            db_path: 数据库文件路径。
        """
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._logger = get_logger().logger
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库连接和表结构。"""
        try:
            # 确保目录存在。
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

            # 启用外键约束。
            self._conn.execute("PRAGMA foreign_keys = ON")

            # 创建表。
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    month_stamp INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_major BOOLEAN DEFAULT FALSE,
                    is_story BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS event_avatars (
                    event_id TEXT NOT NULL,
                    avatar_id TEXT NOT NULL,
                    PRIMARY KEY (event_id, avatar_id),
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_events_month_stamp
                    ON events(month_stamp DESC);
                CREATE INDEX IF NOT EXISTS idx_events_is_major
                    ON events(is_major);
                CREATE INDEX IF NOT EXISTS idx_event_avatars_avatar_id
                    ON event_avatars(avatar_id);
                CREATE INDEX IF NOT EXISTS idx_event_avatars_event_id
                    ON event_avatars(event_id);
            """)
            self._conn.commit()
            self._logger.info(f"EventStorage initialized: {self._db_path}")
        except Exception as e:
            self._logger.error(f"Failed to initialize EventStorage: {e}")
            raise

    @contextmanager
    def _transaction(self):
        """事务上下文管理器。"""
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def add_event(self, event: "Event") -> bool:
        """
        写入单个事件。

        失败时记录日志并返回 False，不抛异常。

        Args:
            event: 要写入的事件对象。

        Returns:
            写入是否成功。
        """
        if self._conn is None:
            self._logger.error("EventStorage not initialized")
            return False

        try:
            with self._transaction():
                # 插入事件主表。
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO events (id, month_stamp, content, is_major, is_story, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.id,
                        int(event.month_stamp),
                        event.content,
                        event.is_major,
                        event.is_story,
                        _format_time(event.created_at),
                    )
                )

                # 插入关联表。
                if event.related_avatars:
                    for avatar_id in event.related_avatars:
                        self._conn.execute(
                            """
                            INSERT OR IGNORE INTO event_avatars (event_id, avatar_id)
                            VALUES (?, ?)
                            """,
                            (event.id, str(avatar_id))
                        )
            return True
        except Exception as e:
            self._logger.error(f"Failed to write event {event.id}: {e}")
            return False

    def _parse_cursor(self, cursor: str) -> tuple[int, int]:
        """
        解析复合 cursor。

        格式: {month_stamp}_{rowid}

        Returns:
            (month_stamp, rowid)
        """
        parts = cursor.split("_", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid cursor format: {cursor}")
        return int(parts[0]), int(parts[1])

    def _make_cursor(self, month_stamp: int, rowid: int) -> str:
        """生成复合 cursor。"""
        return f"{month_stamp}_{rowid}"

    def get_events(
        self,
        avatar_id: Optional[str] = None,
        avatar_id_pair: Optional[tuple[str, str]] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
    ) -> tuple[list["Event"], Optional[str]]:
        """
        分页查询事件。

        Args:
            avatar_id: 按单个角色筛选。
            avatar_id_pair: Pair 查询（两个角色之间的事件）。
            cursor: 分页 cursor，获取该位置之前的事件。
            limit: 每页数量。

        Returns:
            (events, next_cursor)，next_cursor 为 None 表示没有更多。
        """
        from src.classes.event import Event
        from src.systems.time import MonthStamp

        if self._conn is None:
            return [], None

        try:
            # 构建查询。
            params: list = []

            if avatar_id_pair:
                # Pair 查询：两个角色都相关的事件。
                id1, id2 = avatar_id_pair
                base_query = """
                    SELECT DISTINCT e.rowid, e.id, e.month_stamp, e.content, e.is_major, e.is_story, e.created_at
                    FROM events e
                    JOIN event_avatars ea1 ON e.id = ea1.event_id AND ea1.avatar_id = ?
                    JOIN event_avatars ea2 ON e.id = ea2.event_id AND ea2.avatar_id = ?
                """
                params.extend([id1, id2])
            elif avatar_id:
                # 单角色查询。
                base_query = """
                    SELECT DISTINCT e.rowid, e.id, e.month_stamp, e.content, e.is_major, e.is_story, e.created_at
                    FROM events e
                    JOIN event_avatars ea ON e.id = ea.event_id AND ea.avatar_id = ?
                """
                params.append(avatar_id)
            else:
                # 全部事件。
                base_query = """
                    SELECT rowid, id, month_stamp, content, is_major, is_story, e.created_at
                    FROM events e
                """

            # Cursor 条件（获取更旧的事件）。
            # 使用 rowid 保证同一 month_stamp 内的确定性顺序。
            where_clauses = []
            if cursor:
                cursor_month, cursor_rowid = self._parse_cursor(cursor)
                where_clauses.append(
                    "(e.month_stamp < ? OR (e.month_stamp = ? AND e.rowid < ?))"
                )
                params.extend([cursor_month, cursor_month, cursor_rowid])

            # 组装 WHERE。
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)

            # 排序和分页（最新的在前，向上加载更旧的）。
            # 使用 rowid 保证同一 month_stamp 内的插入顺序。
            base_query += " ORDER BY e.month_stamp DESC, e.rowid DESC LIMIT ?"
            params.append(limit + 1)  # 多取一条判断是否有更多。

            rows = self._conn.execute(base_query, params).fetchall()

            # 判断是否有更多。
            has_more = len(rows) > limit
            if has_more:
                rows = rows[:limit]

            # 构建事件对象。
            events = []
            last_rowid = None
            last_month_stamp = None
            for row in rows:
                # 获取关联的 avatar IDs。
                avatar_rows = self._conn.execute(
                    "SELECT avatar_id FROM event_avatars WHERE event_id = ?",
                    (row["id"],)
                ).fetchall()
                related_avatars = [r["avatar_id"] for r in avatar_rows]

                event = Event(
                    month_stamp=MonthStamp(row["month_stamp"]),
                    content=row["content"],
                    related_avatars=related_avatars if related_avatars else None,
                    is_major=bool(row["is_major"]),
                    is_story=bool(row["is_story"]),
                    id=row["id"],
                    created_at=_parse_time(row["created_at"]),
                )
                events.append(event)
                last_rowid = row["rowid"]
                last_month_stamp = row["month_stamp"]

            # 生成 next_cursor。
            next_cursor = None
            if has_more and last_rowid is not None:
                next_cursor = self._make_cursor(last_month_stamp, last_rowid)

            return events, next_cursor

        except Exception as e:
            self._logger.error(f"Failed to query events: {e}")
            return [], None

    def get_events_by_avatar(self, avatar_id: str, limit: int = 50) -> list["Event"]:
        """
        后端用：获取角色相关事件（供 LLM prompt 使用）。

        返回最新的 N 条，按时间正序排列。
        """
        events, _ = self.get_events(avatar_id=avatar_id, limit=limit)
        return list(reversed(events))  # 转为时间正序。

    def get_events_between(self, id1: str, id2: str, limit: int = 50) -> list["Event"]:
        """
        后端用：获取两角色之间的事件。

        返回最新的 N 条，按时间正序排列。
        """
        events, _ = self.get_events(avatar_id_pair=(id1, id2), limit=limit)
        return list(reversed(events))  # 转为时间正序。

    def get_major_events_by_avatar(self, avatar_id: str, limit: int = 10) -> list["Event"]:
        """获取角色的大事（长期记忆）。"""
        from src.classes.event import Event
        from src.systems.time import MonthStamp

        if self._conn is None:
            return []

        try:
            rows = self._conn.execute(
                """
                SELECT DISTINCT e.id, e.month_stamp, e.content, e.is_major, e.is_story, e.created_at
                FROM events e
                JOIN event_avatars ea ON e.id = ea.event_id AND ea.avatar_id = ?
                WHERE e.is_major = TRUE AND e.is_story = FALSE
                ORDER BY e.month_stamp DESC
                LIMIT ?
                """,
                (avatar_id, limit)
            ).fetchall()

            events = []
            for row in rows:
                avatar_rows = self._conn.execute(
                    "SELECT avatar_id FROM event_avatars WHERE event_id = ?",
                    (row["id"],)
                ).fetchall()
                related_avatars = [r["avatar_id"] for r in avatar_rows]

                event = Event(
                    month_stamp=MonthStamp(row["month_stamp"]),
                    content=row["content"],
                    related_avatars=related_avatars if related_avatars else None,
                    is_major=bool(row["is_major"]),
                    is_story=bool(row["is_story"]),
                    id=row["id"],
                    created_at=_parse_time(row["created_at"]),
                )
                events.append(event)

            return list(reversed(events))  # 时间正序。
        except Exception as e:
            self._logger.error(f"Failed to query major events: {e}")
            return []

    def get_minor_events_by_avatar(self, avatar_id: str, limit: int = 10) -> list["Event"]:
        """获取角色的小事（短期记忆，包括故事）。"""
        from src.classes.event import Event
        from src.systems.time import MonthStamp

        if self._conn is None:
            return []

        try:
            rows = self._conn.execute(
                """
                SELECT DISTINCT e.id, e.month_stamp, e.content, e.is_major, e.is_story, e.created_at
                FROM events e
                JOIN event_avatars ea ON e.id = ea.event_id AND ea.avatar_id = ?
                WHERE e.is_major = FALSE OR e.is_story = TRUE
                ORDER BY e.month_stamp DESC
                LIMIT ?
                """,
                (avatar_id, limit)
            ).fetchall()

            events = []
            for row in rows:
                avatar_rows = self._conn.execute(
                    "SELECT avatar_id FROM event_avatars WHERE event_id = ?",
                    (row["id"],)
                ).fetchall()
                related_avatars = [r["avatar_id"] for r in avatar_rows]

                event = Event(
                    month_stamp=MonthStamp(row["month_stamp"]),
                    content=row["content"],
                    related_avatars=related_avatars if related_avatars else None,
                    is_major=bool(row["is_major"]),
                    is_story=bool(row["is_story"]),
                    id=row["id"],
                    created_at=_parse_time(row["created_at"]),
                )
                events.append(event)

            return list(reversed(events))  # 时间正序。
        except Exception as e:
            self._logger.error(f"Failed to query minor events: {e}")
            return []

    def get_major_events_between(self, id1: str, id2: str, limit: int = 10) -> list["Event"]:
        """获取两个角色之间的大事（长期记忆）。"""
        from src.classes.event import Event
        from src.systems.time import MonthStamp

        if self._conn is None:
            return []

        try:
            rows = self._conn.execute(
                """
                SELECT DISTINCT e.id, e.month_stamp, e.content, e.is_major, e.is_story, e.created_at
                FROM events e
                JOIN event_avatars ea1 ON e.id = ea1.event_id AND ea1.avatar_id = ?
                JOIN event_avatars ea2 ON e.id = ea2.event_id AND ea2.avatar_id = ?
                WHERE e.is_major = TRUE AND e.is_story = FALSE
                ORDER BY e.month_stamp DESC
                LIMIT ?
                """,
                (id1, id2, limit)
            ).fetchall()

            events = []
            for row in rows:
                avatar_rows = self._conn.execute(
                    "SELECT avatar_id FROM event_avatars WHERE event_id = ?",
                    (row["id"],)
                ).fetchall()
                related_avatars = [r["avatar_id"] for r in avatar_rows]

                event = Event(
                    month_stamp=MonthStamp(row["month_stamp"]),
                    content=row["content"],
                    related_avatars=related_avatars if related_avatars else None,
                    is_major=bool(row["is_major"]),
                    is_story=bool(row["is_story"]),
                    id=row["id"],
                    created_at=_parse_time(row["created_at"]),
                )
                events.append(event)

            return list(reversed(events))  # 时间正序。
        except Exception as e:
            self._logger.error(f"Failed to query major events between: {e}")
            return []

    def get_minor_events_between(self, id1: str, id2: str, limit: int = 10) -> list["Event"]:
        """获取两个角色之间的小事（短期记忆）。"""
        from src.classes.event import Event
        from src.systems.time import MonthStamp

        if self._conn is None:
            return []

        try:
            rows = self._conn.execute(
                """
                SELECT DISTINCT e.id, e.month_stamp, e.content, e.is_major, e.is_story, e.created_at
                FROM events e
                JOIN event_avatars ea1 ON e.id = ea1.event_id AND ea1.avatar_id = ?
                JOIN event_avatars ea2 ON e.id = ea2.event_id AND ea2.avatar_id = ?
                WHERE e.is_major = FALSE OR e.is_story = TRUE
                ORDER BY e.month_stamp DESC
                LIMIT ?
                """,
                (id1, id2, limit)
            ).fetchall()

            events = []
            for row in rows:
                avatar_rows = self._conn.execute(
                    "SELECT avatar_id FROM event_avatars WHERE event_id = ?",
                    (row["id"],)
                ).fetchall()
                related_avatars = [r["avatar_id"] for r in avatar_rows]

                event = Event(
                    month_stamp=MonthStamp(row["month_stamp"]),
                    content=row["content"],
                    related_avatars=related_avatars if related_avatars else None,
                    is_major=bool(row["is_major"]),
                    is_story=bool(row["is_story"]),
                    id=row["id"],
                    created_at=_parse_time(row["created_at"]),
                )
                events.append(event)

            return list(reversed(events))  # 时间正序。
        except Exception as e:
            self._logger.error(f"Failed to query minor events between: {e}")
            return []

    def get_recent_events(self, limit: int = 100) -> list["Event"]:
        """获取最近的事件（供初始状态 API 使用）。"""
        events, _ = self.get_events(limit=limit)
        return list(reversed(events))  # 时间正序。

    def cleanup(self, keep_major: bool = True, before_month_stamp: Optional[int] = None) -> int:
        """
        清理事件。

        Args:
            keep_major: 是否保留大事。
            before_month_stamp: 删除此时间之前的事件。

        Returns:
            删除的事件数量。
        """
        if self._conn is None:
            return 0

        try:
            conditions = []
            params: list = []

            if keep_major:
                conditions.append("is_major = FALSE")

            if before_month_stamp is not None:
                conditions.append("month_stamp < ?")
                params.append(before_month_stamp)

            # 如果没有条件且要保留大事，则无需删除任何内容
            if not conditions and keep_major:
                return 0

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            with self._transaction():
                cursor = self._conn.execute(
                    f"DELETE FROM events WHERE {where_clause}",
                    params
                )
                deleted = cursor.rowcount

            self._logger.info(f"Cleaned up {deleted} events")
            return deleted

        except Exception as e:
            self._logger.error(f"Failed to cleanup events: {e}")
            return 0

    def count(self) -> int:
        """获取事件总数。"""
        if self._conn is None:
            return 0
        try:
            row = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
            return row[0] if row else 0
        except Exception:
            return 0

    def close(self) -> None:
        """关闭数据库连接。"""
        if self._conn:
            try:
                self._conn.close()
                self._logger.info("EventStorage closed")
            except Exception as e:
                self._logger.error(f"Failed to close EventStorage: {e}")
            finally:
                self._conn = None
