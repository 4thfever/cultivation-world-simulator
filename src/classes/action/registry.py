from __future__ import annotations

from typing import Callable, Dict, Type, Iterable


class ActionRegistry:
    """
    动作注册表：维护动作名到类的映射，并标注哪些是“可实际执行”的动作。

    - register(action_cls, actual): 注册一个动作类
    - get(name): 按名称获取动作类
    - all()/all_actual(): 获取全部/实际可执行的动作类集合
    """
    _name_to_cls: Dict[str, type] = {}
    _actual_name_to_cls: Dict[str, type] = {}

    @classmethod
    def register(cls, action_cls: type, *, actual: bool) -> None:
        name = action_cls.__name__
        cls._name_to_cls[name] = action_cls
        if actual:
            cls._actual_name_to_cls[name] = action_cls

    @classmethod
    def get(cls, name: str) -> type:
        return cls._name_to_cls[name]

    @classmethod
    def all(cls) -> Iterable[type]:
        # 去重保持稳定顺序
        seen = set()
        ordered: list[type] = []
        for t in cls._name_to_cls.values():
            if t not in seen:
                seen.add(t)
                ordered.append(t)
        return ordered

    @classmethod
    def all_actual(cls) -> Iterable[type]:
        # 去重保持稳定顺序
        seen = set()
        ordered: list[type] = []
        for t in cls._actual_name_to_cls.values():
            if t not in seen:
                seen.add(t)
                ordered.append(t)
        return ordered


def register_action(*, actual: bool = True) -> Callable[[type], type]:
    def deco(t: type) -> type:
        ActionRegistry.register(t, actual=actual)
        return t
    return deco


