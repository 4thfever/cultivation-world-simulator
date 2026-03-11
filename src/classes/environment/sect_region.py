from dataclasses import dataclass

from src.classes.environment.region import Region
from src.classes.essence import Essence, EssenceType
from src.i18n import t


@dataclass(eq=False)
class SectRegion(Region):
    """
    宗门总部区域：
    - 作为兜底修炼区域使用；
    - 仅本门弟子在此吐纳时，享受等效「五行皆为 5」的灵气环境。
    """
    sect_name: str = ""
    sect_id: int = -1
    image_path: str | None = None

    @property
    def essence(self) -> Essence:
        """
        宗门总部的等效灵气设定：
        - 五行灵气（金木水火土）密度均为 5；
        - 仅在动作逻辑（如 Respire）中按此视为修炼环境。
        """
        density = {essence_type: 5 for essence_type in EssenceType}
        return Essence(density)

    def get_region_type(self) -> str:
        return "sect"

    def _get_desc(self) -> str:
        return t("sect_headquarters_desc_format", sect_name=self.sect_name)

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = t("Sect Headquarters")
        info["sect_name"] = self.sect_name
        info["sect_id"] = self.sect_id
        # 前端可复用修炼区域的展示方式，显示「兜底」灵气环境：
        # type 使用五种灵气翻译名用逗号拼接，例如「金,木,水,火,土」
        type_label = ",".join(str(essence_type) for essence_type in EssenceType)
        info["essence"] = {
            "type": type_label,
            "density": 5,
        }
        return info
