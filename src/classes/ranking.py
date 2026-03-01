from dataclasses import dataclass, field
from typing import List, Dict, Any, TYPE_CHECKING, Optional
from src.systems.cultivation import Realm
from src.systems.battle import get_base_strength

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

@dataclass
class RankingManager:
    heaven_ranking: List[Dict[str, Any]] = field(default_factory=list)
    earth_ranking: List[Dict[str, Any]] = field(default_factory=list)
    human_ranking: List[Dict[str, Any]] = field(default_factory=list)
    sect_ranking: List[Dict[str, Any]] = field(default_factory=list)
    tournament_info: Dict[str, Any] = field(default_factory=lambda: {
        "next_year": 2,
        "heaven_first": None,
        "earth_first": None,
        "human_first": None
    })

    def update_rankings(self, living_avatars: List["Avatar"]) -> None:
        heaven = []
        earth = []
        human = []
        
        for avatar in living_avatars:
            realm = avatar.cultivation_progress.realm
            if realm == Realm.Nascent_Soul:
                heaven.append(avatar)
            elif realm == Realm.Core_Formation:
                earth.append(avatar)
            elif realm == Realm.Foundation_Establishment:
                human.append(avatar)
                
        def get_avatar_info(avatar: "Avatar") -> dict:
            from src.i18n import t
            # Translate sect name if necessary, or just use string
            sect_name = avatar.sect.name if avatar.sect else t("Rogue Cultivator")
            return {
                "id": str(avatar.id),
                "name": avatar.name,
                "sect_id": avatar.sect.id if avatar.sect else None,
                "sect": sect_name,
                "realm": str(avatar.cultivation_progress.realm),
                "stage": str(avatar.cultivation_progress.stage),
                "power": int(get_base_strength(avatar))
            }
            
        heaven.sort(key=lambda a: get_base_strength(a), reverse=True)
        earth.sort(key=lambda a: get_base_strength(a), reverse=True)
        human.sort(key=lambda a: get_base_strength(a), reverse=True)
        
        self.heaven_ranking = [get_avatar_info(a) for a in heaven[:5]]
        self.earth_ranking = [get_avatar_info(a) for a in earth[:5]]
        self.human_ranking = [get_avatar_info(a) for a in human[:5]]
        
        from src.classes.core.sect import sects_by_id
        sect_list = []
        for sect in sects_by_id.values():
            # Filter living members of the sect
            living_members = [m for m in sect.members.values() if not m.is_dead]
            total_power = sum(get_base_strength(m) for m in living_members)
            
            from src.i18n import t
            sect_list.append({
                "id": sect.id,
                "name": sect.name,
                "alignment": str(sect.alignment),
                "hq_name": sect.headquarter.name,
                "member_count": len(living_members),
                "total_power": int(total_power)
            })
            
        sect_list.sort(key=lambda s: s["total_power"], reverse=True)
        self.sect_ranking = sect_list[:5]

    def get_rankings_data(self) -> Dict[str, Any]:
        return {
            "heaven": self.heaven_ranking,
            "earth": self.earth_ranking,
            "human": self.human_ranking,
            "sect": self.sect_ranking,
            "tournament": self.tournament_info
        }

    def get_avatar_rank(self, avatar_id: str) -> Optional[tuple[str, int]]:
        for i, info in enumerate(self.heaven_ranking):
            if info["id"] == str(avatar_id):
                return "heaven", i + 1
        for i, info in enumerate(self.earth_ranking):
            if info["id"] == str(avatar_id):
                return "earth", i + 1
        for i, info in enumerate(self.human_ranking):
            if info["id"] == str(avatar_id):
                return "human", i + 1
        return None

    def init_tournament_info(self, start_year: int, current_year: int, current_month_value: int) -> None:
        """
        Initialize or recalculate the next tournament year based on current game time.
        Tournament happens every 10 years starting from start_year + 1 in January.
        """
        target_first_year = start_year + 1
        
        if current_year < target_first_year or (current_year == target_first_year and current_month_value <= 1):
            next_year = target_first_year
        else:
            diff = current_year - target_first_year
            if diff % 10 == 0:
                if current_month_value <= 1:
                    next_year = current_year
                else:
                    next_year = current_year + 10
            else:
                next_year = target_first_year + ((diff // 10) + 1) * 10
                
        self.tournament_info["next_year"] = next_year
