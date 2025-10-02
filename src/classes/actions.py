from __future__ import annotations

import json

from src.classes.action import (
    Move,
    Cultivate,
    Breakthrough,
    MoveToRegion,
    MoveToAvatar,
    Play,
    Hunt,
    Harvest,
    Sold,
    Battle,
)
from src.classes.mutual_action import (
    DriveAway,
    Attack,
    MoveAwayFromAvatar,
    MoveAwayFromRegion,
)


ALL_ACTION_CLASSES = [
    Move,
    Battle,
    Cultivate,
    Breakthrough,
    MoveToRegion,
    MoveToAvatar,
    Play,
    Hunt,
    Harvest,
    Sold,
    # 互动相关动作（实际执行的反馈动作也纳入）
    DriveAway,
    Attack,
    MoveAwayFromAvatar,
    MoveAwayFromRegion,
]

ALL_ACTUAL_ACTION_CLASSES = [
    Cultivate,
    Breakthrough,
    MoveToRegion,
    MoveToAvatar,
    Play,
    Hunt,
    Harvest,
    Sold,
    DriveAway,
    Attack,
]

ALL_ACTION_NAMES = [action.__name__ for action in ALL_ACTION_CLASSES]
ALL_ACTUAL_ACTION_NAMES = [action.__name__ for action in ALL_ACTUAL_ACTION_CLASSES]

ACTION_INFOS = {
    action.__name__: {
        "comment": getattr(action, "COMMENT", ""),
        "doable_requirements": getattr(action, "DOABLES_REQUIREMENTS", ""),
        "params": getattr(action, "PARAMS", {}),
    }
    for action in ALL_ACTUAL_ACTION_CLASSES
}
ACTION_INFOS_STR = json.dumps(ACTION_INFOS, ensure_ascii=False)


