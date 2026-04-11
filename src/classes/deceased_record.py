from dataclasses import dataclass
from typing import Optional


@dataclass
class DeceasedRecord:
    """已故角色轻量档案，独立于 Avatar 对象，不受 cleanup_long_dead_avatars 影响。"""

    id: str
    name: str
    gender: str
    age_at_death: int
    realm_at_death: str       # cultivation_progress.realm.value
    stage_at_death: str       # cultivation_progress.stage.value
    death_reason: str
    death_time: int            # MonthStamp int, 与 death_info["time"] 同语义
    sect_name_at_death: str    # avatar.sect.name if avatar.sect else ""
    alignment_at_death: str    # avatar.alignment.value if avatar.alignment else ""
    backstory: Optional[str] = None
    custom_pic_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "age_at_death": self.age_at_death,
            "realm_at_death": self.realm_at_death,
            "stage_at_death": self.stage_at_death,
            "death_reason": self.death_reason,
            "death_time": self.death_time,
            "sect_name_at_death": self.sect_name_at_death,
            "alignment_at_death": self.alignment_at_death,
            "backstory": self.backstory,
            "custom_pic_id": self.custom_pic_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeceasedRecord":
        fields = cls.__dataclass_fields__
        filtered = {k: data[k] for k in fields if k in data}
        return cls(**filtered)
