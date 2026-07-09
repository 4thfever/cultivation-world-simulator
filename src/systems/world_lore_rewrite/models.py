from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


RewriteSource = Literal["llm", "fallback"]
JobKind = Literal["regions", "sect_group", "techniques", "weapons", "auxiliaries"]


@dataclass(frozen=True)
class EntityRewrite:
    id: int
    name: str
    desc: str
    source: RewriteSource = "llm"

    def to_snapshot(self) -> dict[str, str]:
        return {
            "name": self.name,
            "desc": self.desc,
        }


@dataclass
class WorldLoreRewriteDraft:
    regions: dict[int, EntityRewrite] = field(default_factory=dict)
    sects: dict[int, EntityRewrite] = field(default_factory=dict)
    techniques: dict[int, EntityRewrite] = field(default_factory=dict)
    weapons: dict[int, EntityRewrite] = field(default_factory=dict)
    auxiliaries: dict[int, EntityRewrite] = field(default_factory=dict)
    llm_count: int = 0
    fallback_count: int = 0
    elapsed_seconds: float = 0.0

    def merge(self, other: "WorldLoreRewriteDraft") -> None:
        self.regions.update(other.regions)
        self.sects.update(other.sects)
        self.techniques.update(other.techniques)
        self.weapons.update(other.weapons)
        self.auxiliaries.update(other.auxiliaries)
        self.llm_count += other.llm_count
        self.fallback_count += other.fallback_count


@dataclass(frozen=True)
class WorldLoreRewriteConfig:
    rewrite_items: bool = True
    total_timeout_seconds: float = 240.0
    task_timeout_seconds: float = 60.0
    min_retry_budget_seconds: float = 20.0
    max_parse_retries: int = 1
    max_transport_retries: int = 0
    chunk_size_regions: int = 10
    chunk_size_sect_groups: int = 6
    chunk_size_techniques: int = 10
    chunk_size_weapons: int = 10
    chunk_size_auxiliaries: int = 10


@dataclass(frozen=True)
class WorldLoreRewriteContext:
    world: Any
    lore_text: str
    map_summary: dict[str, Any]
    style_guide: dict[str, Any]
    config: WorldLoreRewriteConfig


@dataclass(frozen=True)
class RewriteJob:
    id: str
    kind: JobKind
    task_name: str
    entities: list[dict[str, Any]]
    entity_label: str
    instructions: str
    result_field: str
    map_summary: dict[str, Any]
    style_guide: dict[str, Any]
    lore_text: str
    paired_entities: list[dict[str, Any]] = field(default_factory=list)
    paired_result_field: str = ""
    paired_entity_label: str = ""

    @property
    def expected_ids(self) -> set[int]:
        return {int(entity["id"]) for entity in self.entities}

    @property
    def paired_expected_ids(self) -> set[int]:
        return {int(entity["id"]) for entity in self.paired_entities}
