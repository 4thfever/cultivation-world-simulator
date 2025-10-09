from __future__ import annotations

from inspect import signature, Parameter
from typing import Callable, Mapping, Any


def filter_kwargs_for_callable(func: Callable[..., Any], kwargs: Mapping[str, Any]) -> dict[str, Any]:
    """
    依据可调用对象的签名过滤 kwargs，只保留目标函数可接收的关键字参数。

    - 若目标函数含有 **kwargs（VAR_KEYWORD），直接原样返回（无需过滤）。
    - 仅保留 POSITIONAL_OR_KEYWORD 与 KEYWORD_ONLY 两类参数名。
    - 自动忽略 "self"。
    - 在签名不可获取时（如内建或 C 扩展），原样返回。
    """
    try:
        sig = signature(func)
    except (ValueError, TypeError):
        return dict(kwargs)

    params = sig.parameters
    if any(p.kind == Parameter.VAR_KEYWORD for p in params.values()):
        return dict(kwargs)

    allowed_names = {
        name
        for name, p in params.items()
        if name != "self" and p.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    return {k: v for k, v in kwargs.items() if k in allowed_names}


