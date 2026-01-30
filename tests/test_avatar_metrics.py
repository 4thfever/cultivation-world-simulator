"""
测试 Avatar 状态追踪功能
"""
import pytest
from src.classes.avatar_metrics import AvatarMetrics, MetricTag
from src.classes.calendar import MonthStamp


def test_avatar_metrics_creation():
    """测试状态快照创建"""
    metrics = AvatarMetrics(
        timestamp=MonthStamp(100),
        age=20,
        cultivation_level=5,
        cultivation_progress=100,
        hp=100.0,
        hp_max=100.0,
        spirit_stones=50,
        relations_count=3,
        known_regions_count=2,
        tags=["breakthrough"],
    )

    assert metrics.age == 20
    assert metrics.cultivation_level == 5
    assert metrics.cultivation_progress == 100
    assert metrics.hp == 100.0
    assert metrics.hp_max == 100.0
    assert metrics.spirit_stones == 50
    assert metrics.relations_count == 3
    assert metrics.known_regions_count == 2
    assert "breakthrough" in metrics.tags
    assert metrics.timestamp == MonthStamp(100)


def test_avatar_metrics_serialization():
    """测试序列化与反序列化"""
    original = AvatarMetrics(
        timestamp=MonthStamp(200),
        age=30,
        cultivation_level=10,
        cultivation_progress=500,
        hp=150.0,
        hp_max=200.0,
        spirit_stones=1000,
        relations_count=5,
        known_regions_count=10,
        tags=["injured", "battle"],
    )

    # 序列化
    data = original.to_save_dict()
    assert isinstance(data, dict)
    assert data["age"] == 30
    assert data["cultivation_level"] == 10
    assert "injured" in data["tags"]
    assert "battle" in data["tags"]

    # 反序列化
    restored = AvatarMetrics.from_save_dict(data)
    assert restored.age == original.age
    assert restored.cultivation_level == original.cultivation_level
    assert restored.hp == original.hp
    assert restored.tags == original.tags
    assert restored.timestamp == original.timestamp


def test_metric_tag_enum():
    """测试 MetricTag 枚举"""
    assert MetricTag.BREAKTHROUGH.value == "breakthrough"
    assert MetricTag.INJURED.value == "injured"
    assert MetricTag.RECOVERED.value == "recovered"
    assert MetricTag.SECT_JOIN.value == "sect_join"
    assert MetricTag.SECT_LEAVE.value == "sect_leave"
    assert MetricTag.TECHNIQUE_LEARN.value == "technique_learn"
    assert MetricTag.DEATH.value == "death"
    assert MetricTag.BATTLE.value == "battle"
    assert MetricTag.DUNGEON.value == "dungeon"


def test_avatar_metrics_with_standard_tags():
    """测试使用标准标签"""
    metrics = AvatarMetrics(
        timestamp=MonthStamp(50),
        age=25,
        cultivation_level=7,
        cultivation_progress=300,
        hp=80.0,
        hp_max=100.0,
        spirit_stones=200,
        relations_count=4,
        known_regions_count=5,
        tags=[MetricTag.BREAKTHROUGH.value, MetricTag.BATTLE.value],
    )

    assert "breakthrough" in metrics.tags
    assert "battle" in metrics.tags
    assert len(metrics.tags) == 2


def test_avatar_metrics_empty_tags():
    """测试空标签列表"""
    metrics = AvatarMetrics(
        timestamp=MonthStamp(0),
        age=0,
        cultivation_level=0,
        cultivation_progress=0,
        hp=100.0,
        hp_max=100.0,
        spirit_stones=0,
        relations_count=0,
        known_regions_count=0,
        tags=[],
    )

    assert metrics.tags == []
    assert len(metrics.tags) == 0


def test_avatar_metrics_multiple_tags():
    """测试多个标签"""
    tags = [
        MetricTag.BREAKTHROUGH.value,
        MetricTag.INJURED.value,
        MetricTag.BATTLE.value,
        "custom_event",  # 允许自定义标签
    ]

    metrics = AvatarMetrics(
        timestamp=MonthStamp(1000),
        age=100,
        cultivation_level=15,
        cultivation_progress=1000,
        hp=50.0,
        hp_max=500.0,
        spirit_stones=10000,
        relations_count=20,
        known_regions_count=50,
        tags=tags,
    )

    assert len(metrics.tags) == 4
    assert "breakthrough" in metrics.tags
    assert "injured" in metrics.tags
    assert "battle" in metrics.tags
    assert "custom_event" in metrics.tags
