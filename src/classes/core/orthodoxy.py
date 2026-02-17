from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.utils.df import game_configs, get_str
from src.classes.effect import load_effect_from_str, format_effects_to_text
from src.i18n import t

@dataclass
class Orthodoxy:
    """
    道统 (Orthodoxy)
    
    代表修炼的根本理念与方式：道、佛、儒等。
    """
    id: str
    name: str
    desc: str
    effects: Dict[str, Any]
    effect_desc: str

    def get_info(self, detailed: bool = False) -> Dict[str, Any]:
        """
        获取道统信息
        """
        from src.i18n import t
        info = {
            "id": self.id,
            "name": t(self.name),
            "type_name": t("Orthodoxy"),
        }
        if detailed:
            info["desc"] = t(self.desc)
            info["effect_desc"] = self.effect_desc
        return info

def _load_orthodoxy_data() -> Dict[str, Orthodoxy]:
    """从配表加载 orthodoxy 数据"""
    data = {}
    raw_data = game_configs.get("orthodoxy", [])
    
    for row in raw_data:
        oid = get_str(row, "id")
        if not oid:
            continue
            
        name = get_str(row, "name_id")
        desc = get_str(row, "desc_id")
        
        # 解析 effects
        effects_str = get_str(row, "effects")
        effects = load_effect_from_str(effects_str)
        effect_desc = format_effects_to_text(effects)
        
        orthodoxy = Orthodoxy(
            id=oid,
            name=name,
            desc=desc,
            effects=effects,
            effect_desc=effect_desc
        )
        data[oid] = orthodoxy
        
    return data

# 全局容器
orthodoxy_by_id: Dict[str, Orthodoxy] = {}

def reload():
    """重新加载数据"""
    new_data = _load_orthodoxy_data()
    orthodoxy_by_id.clear()
    orthodoxy_by_id.update(new_data)

# 初始化
reload()

def get_orthodoxy(oid: str) -> Optional[Orthodoxy]:
    return orthodoxy_by_id.get(oid)
