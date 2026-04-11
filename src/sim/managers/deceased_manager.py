from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

from src.classes.deceased_record import DeceasedRecord


@dataclass
class DeceasedManager:
    """已故角色档案管理器，独立于 AvatarManager，不受 cleanup_long_dead_avatars 影响。"""

    _records: Dict[str, DeceasedRecord] = field(default_factory=dict)

    def record_death(self, avatar: "Avatar") -> None:
        """从 Avatar 快照生成 DeceasedRecord，按 id 覆盖写入（幂等）。"""
        death_info = avatar.death_info or {}
        record = DeceasedRecord(
            id=avatar.id,
            name=avatar.name,
            gender=avatar.gender.value if hasattr(avatar.gender, "value") else str(avatar.gender),
            age_at_death=avatar.age.age,
            realm_at_death=avatar.cultivation_progress.realm.value,
            stage_at_death=avatar.cultivation_progress.stage.value,
            death_reason=death_info.get("reason", ""),
            death_time=death_info.get("time", 0),
            sect_name_at_death=str(death_info.get("sect_name_at_death", "")),
            alignment_at_death=str(death_info.get("alignment_at_death", "")),
            backstory=avatar.backstory,
            custom_pic_id=avatar.custom_pic_id,
        )
        self._records[avatar.id] = record

    def get_all_records(self) -> List[DeceasedRecord]:
        """按死亡时间倒序返回所有记录。"""
        return sorted(self._records.values(), key=lambda r: r.death_time, reverse=True)

    def get_record(self, avatar_id: str) -> Optional[DeceasedRecord]:
        return self._records.get(avatar_id)

    def to_save_list(self) -> List[dict]:
        return [r.to_dict() for r in self._records.values()]

    def load_from_list(self, data: List[dict]) -> None:
        self._records.clear()
        for item in data:
            record = DeceasedRecord.from_dict(item)
            self._records[record.id] = record
