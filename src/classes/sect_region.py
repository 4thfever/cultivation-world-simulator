from dataclasses import dataclass
from pathlib import Path

from src.classes.region import Region


@dataclass(eq=False)
class SectRegion(Region):
    """
    宗门总部区域：仅用于显示宗门总部的名称与描述。
    无额外操作或属性。
    """
    sect_name: str = ""
    sect_id: int = -1
    image_path: str | None = None

    def get_region_type(self) -> str:
        return "sect"

    def _get_desc(self) -> str:
        return f"（{self.sect_name}）"

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = "宗门驻地"
        info["sect_name"] = self.sect_name
        info["sect_id"] = self.sect_id
        return info
