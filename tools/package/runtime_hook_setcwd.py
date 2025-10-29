import os
import sys

def _set_cwd_to_exe_dir() -> None:
    # 在 PyInstaller 运行时，将工作目录切换到可执行文件所在目录
    try:
        if hasattr(sys, "_MEIPASS"):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        os.chdir(base_dir)
    except Exception:
        # 保持默认工作目录
        pass

_set_cwd_to_exe_dir()


