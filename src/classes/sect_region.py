from dataclasses import dataclass
from pathlib import Path

from src.classes.region import Region


@dataclass
class SectRegion(Region):
    """
    宗门总部区域：仅用于显示宗门总部的名称与描述。
    无额外操作或属性。
    """
    sect_name: str
    image_path: str | None = None

    def get_region_type(self) -> str:
        return "sect"

    def get_hover_info(self) -> list[str]:
        # 覆盖基础 hover：明确显示“宗门驻地”
        return [
            f"宗门: {self.sect_name}",
            f"驻地: {self.name}",
            f"描述: {self.desc}",
        ]

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = "宗门驻地"
        info["sect_name"] = self.sect_name
        return info
