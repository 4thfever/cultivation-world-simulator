"""
Avatar 核心类

精简后的 Avatar 类，通过 Mixin 组合完整功能。
"""
import random
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.sect_ranks import SectRank

from src.classes.calendar import MonthStamp
from src.classes.world import World
from src.sim.save.avatar_save_mixin import AvatarSaveMixin
from src.sim.load.avatar_load_mixin import AvatarLoadMixin
from src.classes.tile import Tile
from src.classes.region import Region
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.technique import Technique, get_technique_by_sect
from src.classes.age import Age
from src.classes.event import Event
from src.classes.action_runtime import ActionPlan, ActionInstance
from src.classes.alignment import Alignment
from src.classes.persona import Persona, get_random_compatible_personas
from src.classes.material import Material
from src.classes.weapon import Weapon
from src.classes.auxiliary import Auxiliary
from src.classes.magic_stone import MagicStone
from src.classes.hp import HP, HP_MAX_BY_REALM
from src.classes.relation import Relation
from src.classes.sect import Sect
from src.classes.appearance import Appearance, get_random_appearance
from src.classes.spirit_animal import SpiritAnimal
from src.classes.long_term_objective import LongTermObjective
from src.classes.nickname_data import Nickname
from src.classes.emotions import EmotionType
from src.utils.config import CONFIG
from src.classes.elixir import ConsumedElixir, Elixir

# Mixin 导入
from src.classes.effect import EffectsMixin
from src.classes.avatar.inventory_mixin import InventoryMixin
from src.classes.avatar.action_mixin import ActionMixin

persona_num = CONFIG.avatar.persona_num


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

    def __str__(self) -> str:
        return gender_strs.get(self, self.value)


gender_strs = {
    Gender.MALE: "男",
    Gender.FEMALE: "女",
}


@dataclass
class Avatar(
    AvatarSaveMixin,
    AvatarLoadMixin,
    EffectsMixin,
    InventoryMixin,
    ActionMixin,
):
    """
    NPC的类。
    包含了这个角色的一切信息。
    """
    world: World
    name: str
    id: str
    birth_month_stamp: MonthStamp
    age: Age
    gender: Gender
    cultivation_progress: CultivationProgress = field(default_factory=lambda: CultivationProgress(0))
    pos_x: int = 0
    pos_y: int = 0
    tile: Optional[Tile] = None

    root: Root = field(default_factory=lambda: random.choice(list(Root)))
    personas: List[Persona] = field(default_factory=list)
    technique: Technique | None = None
    _pending_events: List[Event] = field(default_factory=list)
    current_action: Optional[ActionInstance] = None
    planned_actions: List[ActionPlan] = field(default_factory=list)
    thinking: str = ""
    short_term_objective: str = ""
    long_term_objective: Optional[LongTermObjective] = None
    magic_stone: MagicStone = field(default_factory=lambda: MagicStone(0))
    materials: dict[Material, int] = field(default_factory=dict)
    hp: HP = field(default_factory=lambda: HP(0, 0))
    relations: dict["Avatar", Relation] = field(default_factory=dict)
    alignment: Alignment | None = None
    sect: Sect | None = None
    sect_rank: "SectRank | None" = None
    appearance: Appearance = field(default_factory=get_random_appearance)
    weapon: Optional[Weapon] = None
    weapon_proficiency: float = 0.0
    auxiliary: Optional[Auxiliary] = None
    spirit_animal: Optional[SpiritAnimal] = None
    nickname: Optional[Nickname] = None
    emotion: EmotionType = EmotionType.CALM
    custom_pic_id: Optional[int] = None
    
    elixirs: List[ConsumedElixir] = field(default_factory=list)

    is_dead: bool = False
    death_info: Optional[dict] = None

    _new_action_set_this_step: bool = False
    _action_cd_last_months: dict[str, int] = field(default_factory=dict)
    
    known_regions: set[int] = field(default_factory=set)

    # 关系交互计数器: key=target_id, value={"count": 0, "checked_times": 0}
    relation_interaction_states: dict[str, dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"count": 0, "checked_times": 0}))

    # ========== 宗门相关 ==========

    def consume_elixir(self, elixir: Elixir) -> bool:
        """
        服用丹药
        :return: 是否成功服用
        """
        # 1. 境界校验：只能服用境界等于或者小于当前境界的丹药
        if elixir.realm > self.cultivation_progress.realm:
            return False
            
        # 2. 重复服用校验：若已服用过同种且未失效的丹药，则无效
        # 因为延寿丹药都是无限持久的，所以所有延寿丹药都只能服用一次。
        for consumed in self.elixirs:
            if consumed.elixir.id == elixir.id:
                if not consumed.is_completely_expired(int(self.world.month_stamp)):
                    return False

        # 3. 记录服用状态
        self.elixirs.append(ConsumedElixir(elixir, int(self.world.month_stamp)))
        
        # 4. 立即触发属性重算（因为可能有立即生效的数值变化，或者MaxHP/Lifespan改变）
        self.recalc_effects()
        
        return True
    
    def process_elixir_expiration(self, current_month: int) -> None:
        """
        处理丹药过期：
        1. 移除已完全过期的丹药
        2. 如果有移除，触发属性重算
        """
        if not self.elixirs:
            return

        original_count = len(self.elixirs)
        # 过滤掉完全过期的
        self.elixirs = [
            e for e in self.elixirs 
            if not e.is_completely_expired(current_month)
        ]
        
        # 如果数量减少，说明有过期，重算属性（主要是寿命、MaxHP）
        if len(self.elixirs) < original_count:
            self.recalc_effects()

    def join_sect(self, sect: Sect, rank: "SectRank") -> None:
        """加入宗门"""
        if self.is_dead:
            return
        if self.sect:
            self.leave_sect()
        self.sect = sect
        self.sect_rank = rank
        sect.add_member(self)
        
    def leave_sect(self) -> None:
        """退出宗门"""
        if self.sect:
            self.sect.remove_member(self)
            self.sect = None
            self.sect_rank = None

    def get_sect_str(self) -> str:
        """获取宗门显示名：有宗门则返回"宗门名+职位"，否则返回"散修"。"""
        if self.sect is None:
            return "散修"
        if self.sect_rank is None:
            return self.sect.name
        from src.classes.sect_ranks import get_rank_display_name
        rank_name = get_rank_display_name(self.sect_rank, self.sect)
        return f"{self.sect.name}{rank_name}"

    def get_sect_rank_name(self) -> str:
        """获取宗门职位的显示名称"""
        if self.sect is None or self.sect_rank is None:
            return "散修"
        from src.classes.sect_ranks import get_rank_display_name
        return get_rank_display_name(self.sect_rank, self.sect)

    # ========== 死亡相关 ==========

    def set_dead(self, reason: str, time: MonthStamp) -> None:
        """设置角色死亡状态。"""
        if self.is_dead:
            return
            
        self.is_dead = True
        self.death_info = {
            "time": int(time),
            "reason": reason,
            "location": (self.pos_x, self.pos_y)
        }
        
        self.planned_actions.clear()
        self.current_action = None
        self._pending_events.clear()
        self.thinking = ""
        self.short_term_objective = ""
        
        if self.sect:
            self.sect.remove_member(self)

    def death_by_old_age(self) -> bool:
        """检查是否老死"""
        return self.age.death_by_old_age(self.cultivation_progress.realm)

    # ========== 年龄与修为 ==========

    def update_age(self, current_month_stamp: MonthStamp):
        """更新年龄"""
        self.age.update_age(current_month_stamp, self.birth_month_stamp)

    def update_cultivation(self, new_level: int):
        """更新修仙进度，并在境界提升时更新寿命和宗门职位"""
        old_realm = self.cultivation_progress.realm
        self.cultivation_progress.level = new_level
        self.cultivation_progress.realm = self.cultivation_progress.get_realm(new_level)
        
        if self.cultivation_progress.realm != old_realm:
            self.age.update_realm(self.cultivation_progress.realm)
            self.recalc_effects()
            from src.classes.sect_ranks import check_and_promote_sect_rank
            check_and_promote_sect_rank(self, old_realm, self.cultivation_progress.realm)

    # ========== 区域与位置 ==========

    def _init_known_regions(self):
        """初始化已知区域：当前位置 + 宗门驻地"""
        if self.tile and self.tile.region:
            self.known_regions.add(self.tile.region.id)
        
        if self.sect:
            for r in self.world.map.sect_regions.values():
                if r.sect_id == self.sect.id:
                    self.known_regions.add(r.id)
                    break

    # ========== 关系相关 ==========

    def set_relation(self, other: "Avatar", relation: Relation) -> None:
        """设置与另一个角色的关系。"""
        from src.classes.relations import set_relation
        set_relation(self, other, relation)

    def get_relation(self, other: "Avatar") -> Optional[Relation]:
        """获取与另一个角色的关系。"""
        from src.classes.relations import get_relation
        return get_relation(self, other)

    def clear_relation(self, other: "Avatar") -> None:
        """清除与另一个角色的关系。"""
        from src.classes.relations import clear_relation
        clear_relation(self, other)

    # ========== 信息展示（委托） ==========

    def get_info(self, detailed: bool = False) -> dict:
        from src.classes.avatar.info_presenter import get_avatar_info
        return get_avatar_info(self, detailed)

    def get_structured_info(self) -> dict:
        from src.classes.avatar.info_presenter import get_avatar_structured_info
        return get_avatar_structured_info(self)

    def get_expanded_info(
        self, 
        co_region_avatars: Optional[List["Avatar"]] = None,
        other_avatar: Optional["Avatar"] = None,
        detailed: bool = False
    ) -> dict:
        from src.classes.avatar.info_presenter import get_avatar_expanded_info
        return get_avatar_expanded_info(self, co_region_avatars, other_avatar, detailed)

    def get_other_avatar_info(self, other_avatar: "Avatar") -> str:
        from src.classes.avatar.info_presenter import get_other_avatar_info
        return get_other_avatar_info(self, other_avatar)

    def get_desc(self, detailed: bool = False) -> str:
        """获取角色的文本描述（包含效果明细）"""
        from src.classes.avatar.info_presenter import get_avatar_desc
        return get_avatar_desc(self, detailed=detailed)

    # ========== 魔法方法 ==========

    @property
    def current_action_name(self) -> str:
        """获取当前动作名称，默认返回'思考'"""
        if self.current_action and self.current_action.action:
            action = self.current_action.action
            # 优先取 ACTION_NAME (中文名)，如果没有则使用类名
            return getattr(action, "ACTION_NAME", getattr(action, "name", "思考"))
        return "思考"

    def __post_init__(self):
        """在Avatar创建后自动初始化tile和HP"""
        self.tile = self.world.map.get_tile(self.pos_x, self.pos_y)
        
        max_hp = HP_MAX_BY_REALM.get(self.cultivation_progress.realm, 100)
        self.hp = HP(max_hp, max_hp)
        
        if not self.personas:
            self.personas = get_random_compatible_personas(persona_num, avatar=self)

        if self.technique is None:
            self.technique = get_technique_by_sect(self.sect)

        if self.sect:
            self.sect.add_member(self)

        if self.alignment is None:
            if self.sect is not None:
                self.alignment = self.sect.alignment
            else:
                self.alignment = random.choice(list(Alignment))
        
        self.recalc_effects()
        self._init_known_regions()

    def __hash__(self) -> int:
        if not hasattr(self, 'id'):
            # 防御性编程：如果id尚未初始化（例如deepcopy过程中），使用对象内存地址
            return super().__hash__()
        return hash(self.id)

    def __str__(self) -> str:
        return str(self.get_info(detailed=False))
