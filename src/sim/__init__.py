"""
Simulator module
"""
# 延迟导入 Simulator 以避免循环导入
# from .simulator import Simulator

def __getattr__(name):
    if name == "Simulator":
        from .simulator import Simulator
        return Simulator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# 导出常用的 save/load 函数，方便外部调用
from .save.save_game import save_game, list_saves, get_save_info
from .load.load_game import load_game, get_events_db_path, check_save_compatibility

__all__ = ["Simulator", "save_game", "list_saves", "get_save_info", "load_game", "get_events_db_path", "check_save_compatibility"]
