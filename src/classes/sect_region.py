from dataclasses import dataclass
from pathlib import Path

from src.classes.region import Region


@dataclass
class SectRegion(Region):
    """
    宗门总部区域：仅用于显示宗门总部的名称与描述。
    无额外操作或属性。
    """
    image_path: str | None = None

    def get_region_type(self) -> str:
        return "sect"

    # hover 信息沿用基类，仅显示名称与描述


