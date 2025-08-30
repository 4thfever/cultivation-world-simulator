from pathlib import Path

def read_txt(path: Path) -> str:
    """
    读入中文txt文件
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()