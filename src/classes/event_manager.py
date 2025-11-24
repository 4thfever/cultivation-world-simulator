from typing import Dict, List
from collections import deque, defaultdict

from src.classes.event import Event


class EventManager:
    """
    全局事件管理器：统一保存事件，并提供按角色、按角色对、按时间的查询。
    - 限长清理，避免内存无限增长。
    - 幂等写入（基于 event_id）。
    - 仅对恰为两人参与的事件建立“按人对”索引。
    """

    def __init__(self, *, max_global_events: int = 5000, max_index_events: int = 200) -> None:
        self.max_global_events = max_global_events
        self.max_index_events = max_index_events

        self._events: deque[Event] = deque()
        self._by_id: Dict[str, Event] = {}
        self._by_avatar: Dict[str, deque[Event]] = defaultdict(deque)
        self._by_pair: Dict[frozenset[str], deque[Event]] = defaultdict(deque)
        # 按角色分类的大事/小事索引
        self._by_avatar_major: Dict[str, deque[Event]] = defaultdict(deque)
        self._by_avatar_minor: Dict[str, deque[Event]] = defaultdict(deque)
        # 按角色对分类的大事/小事索引
        self._by_pair_major: Dict[frozenset[str], deque[Event]] = defaultdict(deque)
        self._by_pair_minor: Dict[frozenset[str], deque[Event]] = defaultdict(deque)

    def _append_with_limit(self, dq: deque, item: Event) -> None:
        dq.append(item)
        if len(dq) > self.max_index_events:
            dq.popleft()

    def add_event(self, event: Event) -> None:
        # 过滤掉空事件
        from src.classes.event import is_null_event
        if is_null_event(event):
            return

        # 幂等：若已存在同 id，跳过
        if getattr(event, "id", None) and event.id in self._by_id:
            return
        if getattr(event, "id", None):
            self._by_id[event.id] = event

        # 全局
        self._events.append(event)
        if len(self._events) > self.max_global_events:
            self._events.popleft()

        # 分索引：按人/人对
        rel = event.related_avatars or []
        rel_unique = list(dict.fromkeys(rel))  # 去重但保持顺序
        for aid in rel_unique:
            self._append_with_limit(self._by_avatar[aid], event)
            # 故事事件进入小事索引，不进入大事索引
            if event.is_story:
                self._append_with_limit(self._by_avatar_minor[aid], event)
            elif event.is_major:
                self._append_with_limit(self._by_avatar_major[aid], event)
            else:
                self._append_with_limit(self._by_avatar_minor[aid], event)
        # 仅当且仅当"恰有两位参与者"时建立按人对索引
        if len(rel_unique) == 2:
            a, b = rel_unique[0], rel_unique[1]
            pair_key = frozenset([a, b])
            self._append_with_limit(self._by_pair[pair_key], event)
            # 角色对也建立分类索引
            if event.is_story:
                self._append_with_limit(self._by_pair_minor[pair_key], event)
            elif event.is_major:
                self._append_with_limit(self._by_pair_major[pair_key], event)
            else:
                self._append_with_limit(self._by_pair_minor[pair_key], event)

    # —— 查询接口 ——
    def get_recent_events(self, limit: int = 100) -> List[Event]:
        if limit <= 0:
            return []
        return list(self._events)[-limit:]

    def get_events_by_avatar(self, avatar_id: str, *, limit: int = 50) -> List[Event]:
        dq = self._by_avatar.get(avatar_id)
        if not dq:
            return []
        return list(dq)[-limit:]

    def get_events_between(self, avatar_id1: str, avatar_id2: str, *, limit: int = 50) -> List[Event]:
        key = frozenset([avatar_id1, avatar_id2])
        dq = self._by_pair.get(key)
        if not dq:
            return []
        return list(dq)[-limit:]

    def get_major_events_by_avatar(self, avatar_id: str, *, limit: int = 10) -> List[Event]:
        """获取角色的大事（长期记忆）"""
        dq = self._by_avatar_major.get(avatar_id)
        if not dq:
            return []
        return list(dq)[-limit:]

    def get_minor_events_by_avatar(self, avatar_id: str, *, limit: int = 10) -> List[Event]:
        """获取角色的小事（短期记忆）"""
        dq = self._by_avatar_minor.get(avatar_id)
        if not dq:
            return []
        return list(dq)[-limit:]

    def get_major_events_between(self, avatar_id1: str, avatar_id2: str, *, limit: int = 10) -> List[Event]:
        """获取两个角色之间的大事（长期记忆）"""
        key = frozenset([avatar_id1, avatar_id2])
        dq = self._by_pair_major.get(key)
        if not dq:
            return []
        return list(dq)[-limit:]

    def get_minor_events_between(self, avatar_id1: str, avatar_id2: str, *, limit: int = 10) -> List[Event]:
        """获取两个角色之间的小事（短期记忆）"""
        key = frozenset([avatar_id1, avatar_id2])
        dq = self._by_pair_minor.get(key)
        if not dq:
            return []
        return list(dq)[-limit:]


