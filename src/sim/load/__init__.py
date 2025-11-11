"""读档功能模块

延迟导入以避免循环依赖
"""

def __getattr__(name):
    """延迟导入，避免在模块级别触发循环依赖"""
    if name == "load_game":
        from .load_game import load_game
        return load_game
    elif name == "check_save_compatibility":
        from .load_game import check_save_compatibility
        return check_save_compatibility
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["load_game", "check_save_compatibility"]

