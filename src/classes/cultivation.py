from enum import Enum
from functools import total_ordering

from src.classes.color import Color

@total_ordering
class Realm(Enum):
    Qi_Refinement = "QI_REFINEMENT"           # 练气
    Foundation_Establishment = "FOUNDATION_ESTABLISHMENT"  # 筑基
    Core_Formation = "CORE_FORMATION"        # 金丹
    Nascent_Soul = "NASCENT_SOUL"            # 元婴

    def __str__(self) -> str:
        """返回境界的翻译名称"""
        from src.i18n import t
        return t(realm_msg_ids.get(self, self.value))

    @staticmethod
    def from_str(s: str) -> "Realm":
        s = str(s).strip().replace(" ", "_").upper()
        # 建立映射以兼容多种输入格式
        mapping = {
            "练气": "QI_REFINEMENT", "QI_REFINEMENT": "QI_REFINEMENT", "QI REFINEMENT": "QI_REFINEMENT",
            "筑基": "FOUNDATION_ESTABLISHMENT", "FOUNDATION_ESTABLISHMENT": "FOUNDATION_ESTABLISHMENT", "FOUNDATION ESTABLISHMENT": "FOUNDATION_ESTABLISHMENT",
            "金丹": "CORE_FORMATION", "CORE_FORMATION": "CORE_FORMATION", "CORE FORMATION": "CORE_FORMATION",
            "元婴": "NASCENT_SOUL", "NASCENT_SOUL": "NASCENT_SOUL", "NASCENT SOUL": "NASCENT_SOUL"
        }
        realm_id = mapping.get(s, "QI_REFINEMENT")
        return Realm(realm_id)

    @property
    def color_rgb(self) -> tuple[int, int, int]:
        """返回境界对应的RGB颜色值"""
        color_map = {
            Realm.Qi_Refinement: Color.COMMON_WHITE,
            Realm.Foundation_Establishment: Color.UNCOMMON_GREEN,
            Realm.Core_Formation: Color.EPIC_PURPLE,
            Realm.Nascent_Soul: Color.LEGENDARY_GOLD,
        }
        return color_map.get(self, Color.COMMON_WHITE)

    @classmethod
    def from_id(cls, realm_id: int) -> "Realm":
        index = realm_id - 1
        if index < 0 or index >= len(REALM_ORDER):
            raise ValueError(f"Unknown realm_id: {realm_id}")
        return REALM_ORDER[index]

    def __lt__(self, other):
        if not isinstance(other, Realm):
            return NotImplemented
        return REALM_RANK[self] < REALM_RANK[other]

    def __le__(self, other):
        if not isinstance(other, Realm):
            return NotImplemented
        return REALM_RANK[self] <= REALM_RANK[other]

    def __gt__(self, other):
        if not isinstance(other, Realm):
            return NotImplemented
        return REALM_RANK[self] > REALM_RANK[other]

    def __ge__(self, other):
        if not isinstance(other, Realm):
            return NotImplemented
        return REALM_RANK[self] >= REALM_RANK[other]
        

@total_ordering
class Stage(Enum):
    Early_Stage = "EARLY_STAGE"    # 前期
    Middle_Stage = "MIDDLE_STAGE"  # 中期
    Late_Stage = "LATE_STAGE"      # 后期

    def __str__(self) -> str:
        """返回阶段的翻译名称"""
        from src.i18n import t
        return t(stage_msg_ids.get(self, self.value))

    @staticmethod
    def from_str(s: str) -> "Stage":
        s = str(s).strip().replace(" ", "_").upper()
        mapping = {
            "前期": "EARLY_STAGE", "EARLY_STAGE": "EARLY_STAGE", "EARLY STAGE": "EARLY_STAGE",
            "中期": "MIDDLE_STAGE", "MIDDLE_STAGE": "MIDDLE_STAGE", "MIDDLE STAGE": "MIDDLE_STAGE",
            "后期": "LATE_STAGE", "LATE_STAGE": "LATE_STAGE", "LATE STAGE": "LATE_STAGE"
        }
        stage_id = mapping.get(s, "EARLY_STAGE")
        return Stage(stage_id)

    def __lt__(self, other):
        if not isinstance(other, Stage):
            return NotImplemented
        return STAGE_RANK[self] < STAGE_RANK[other]

    def __le__(self, other):
        if not isinstance(other, Stage):
            return NotImplemented
        return STAGE_RANK[self] <= STAGE_RANK[other]

    def __gt__(self, other):
        if not isinstance(other, Stage):
            return NotImplemented
        return STAGE_RANK[self] > STAGE_RANK[other]

    def __ge__(self, other):
        if not isinstance(other, Stage):
            return NotImplemented
        return STAGE_RANK[self] >= STAGE_RANK[other]

# msgid映射
realm_msg_ids = {
    Realm.Qi_Refinement: "qi_refinement",
    Realm.Foundation_Establishment: "foundation_establishment",
    Realm.Core_Formation: "core_formation",
    Realm.Nascent_Soul: "nascent_soul",
}

stage_msg_ids = {
    Stage.Early_Stage: "early_stage",
    Stage.Middle_Stage: "middle_stage",
    Stage.Late_Stage: "late_stage",
}

# 统一的境界顺序与排名，避免重复定义
REALM_ORDER: tuple[Realm, ...] = (
    Realm.Qi_Refinement,
    Realm.Foundation_Establishment,
    Realm.Core_Formation,
    Realm.Nascent_Soul,
)
REALM_RANK: dict[Realm, int] = {realm: idx for idx, realm in enumerate(REALM_ORDER)}

# 统一的阶段顺序与排名，避免重复定义
STAGE_ORDER: tuple[Stage, ...] = (
    Stage.Early_Stage,
    Stage.Middle_Stage,
    Stage.Late_Stage,
)
STAGE_RANK: dict[Stage, int] = {stage: idx for idx, stage in enumerate(STAGE_ORDER)}

LEVELS_PER_REALM = 30
LEVELS_PER_STAGE = 10

REALM_TO_MOVE_STEP = {
    Realm.Qi_Refinement: 2,
    Realm.Foundation_Establishment: 3,
    Realm.Core_Formation: 4,
    Realm.Nascent_Soul: 5,
}

class CultivationProgress:
    """
    修仙进度(包含等级、境界和经验值)
    目前一个四个大境界，每个境界分前期、中期、后期。每一期对应10级。
    所以每一个境界对应30级。境界的级别满了之后，需要突破才能进入下一个境界与升级。
    所以有：
    练气(Qi Refinement)：前期(1-10)、中期(11-20)、后期(21-30)、突破(31)
    筑基(Foundation Establishment)：前期(31-40)、中期(41-50)、后期(51-60)、突破(61)
    金丹(Core Formation)：前期(61-70)、中期(71-80)、后期(81-90)、突破(91)
    元婴(Nascent Soul)：前期(91-100)、中期(101-110)、后期(111-120)、突破(121)
    """

    def __init__(self, level: int, exp: int = 0):
        self.level = level
        self.exp = exp
        self.realm = self.get_realm(level)
        self.stage = self.get_stage(level)

    def get_realm(self, level: int) -> Realm:
        """获取境界（算术推导，不依赖映射表）"""
        if level <= 0:
            return Realm.Qi_Refinement
        realm_index = (level - 1) // LEVELS_PER_REALM  # 0-based index
        return REALM_ORDER[min(realm_index, len(REALM_ORDER) - 1)]

    def get_stage(self, level: int) -> Stage:
        """获取阶段（算术推导：1-10前期，11-20中期，21-30后期）"""
        if level <= 0:
            return Stage.Early_Stage
        stage_index = ((level - 1) % LEVELS_PER_REALM) // LEVELS_PER_STAGE
        return STAGE_ORDER[min(stage_index, len(STAGE_ORDER) - 1)]

    def get_move_step(self) -> int:
        """
        每月能够移动的距离，
        练气: 2
        筑基: 3
        金丹: 4
        元婴: 5
        """
        return REALM_TO_MOVE_STEP[self.realm]

    def get_detailed_info(self) -> str:
        from src.i18n import t
        can_break_through = self.can_break_through()
        can_break_through_str = t("Needs breakthrough") if can_break_through else t("Not at bottleneck, no breakthrough needed")
        return t("{realm} {stage} (Level {level}) {status}", 
                realm=str(self.realm), stage=str(self.stage), 
                level=self.level, status=can_break_through_str)

    def get_info(self) -> str:
        return f"{self.realm} {self.stage}"

    def get_exp_required(self) -> int:
        """
        计算升级到指定等级需要的经验值
        使用简单的代数加法：base_exp + (level - 1) * increment + realm_bonus
        
        参数:
            target_level: 目标等级
        
        返回:
            需要的经验值
        """
        next_level = self.level + 1
        
        base_exp = 100  # 基础经验值
        increment = 50   # 每级增加50点经验值
        
        # 基础经验值计算
        exp_required = base_exp + (next_level - 1) * increment
        
        # 境界加成：按 next_level 所处境界（延后入境界，算术推导）增加
        realm_index = (max(1, next_level) - 1) // LEVELS_PER_REALM
        realm_bonus = realm_index * 1000
        
        return exp_required + realm_bonus

    def get_exp_progress(self) -> tuple[int, int]:
        """
        获取当前经验值进度
        
        返回:
            (当前经验值, 升级所需经验值)
        """
        required_exp = self.get_exp_required()
        return self.exp, required_exp

    def add_exp(self, exp_amount: int) -> bool:
        """
        增加经验值
        
        参数:
            exp_amount: 要增加的经验值数量
        
        返回:
            如果升级了则返回True
        """
        self.exp += exp_amount

        leveled_up = False
        # 支持多级升级，但在瓶颈（30/60/90…）停下，等待突破
        while True:
            # 瓶颈位：level > 0 且 level % LEVELS_PER_REALM == 0
            if self.is_in_bottleneck():
                break
            if not self.is_level_up():
                break
            required_exp = self.get_exp_required()
            self.exp -= required_exp
            self.level += 1
            self.realm = self.get_realm(self.level)
            self.stage = self.get_stage(self.level)
            leveled_up = True
            if self.is_in_bottleneck():
                break

        return leveled_up

    def break_through(self):
        """
        突破境界
        """
        self.level += 1
        self.realm = self.get_realm(self.level)
        self.stage = self.get_stage(self.level)

    def is_in_bottleneck(self) -> bool:
        """
        是否处于瓶颈期。
        处于每个大境界的第 30、60、90…级时（level > 0 且 level % LEVELS_PER_REALM == 0）。
        """
        return self.level > 0 and (self.level % LEVELS_PER_REALM == 0)

    def can_break_through(self) -> bool:
        """
        检查是否可以突破
        """
        # 动态检测目前最高级别的修为：如果已经是最高境界的最高等级，则不能突破
        max_level = len(REALM_ORDER) * LEVELS_PER_REALM
        if self.level >= max_level:
            return False
        return self.is_in_bottleneck()

    def can_cultivate(self) -> bool:
        """
        检查是否可以修炼
        可以突破，说明到顶了，说明不能修炼了，必须突破后才能正常修炼。
        """
        return not self.is_in_bottleneck()

    def is_level_up(self) -> bool:
        """
        检查是否可以进入下一级
        """
        exp_required = self.get_exp_required()
        return self.exp >= exp_required

    def __str__(self) -> str:
        from src.i18n import t
        bottleneck_status = t("Yes") if self.is_in_bottleneck() else t("No")
        return t("{realm} {stage} (Level {level}). At bottleneck: {status}",
                realm=str(self.realm), stage=str(self.stage),
                level=self.level, status=bottleneck_status)

    def get_breakthrough_success_rate(self) -> float:
        return breakthrough_success_rate_by_realm[self.realm]
    
    def get_breakthrough_fail_reduce_lifespan(self) -> int:
        return breakthrough_fail_reduce_lifespan_by_realm[self.realm]
    
    def to_dict(self) -> dict:
        """转换为可序列化的字典"""
        return {
            "level": self.level,
            "exp": self.exp,
            "realm": self.realm.name,  # 保存枚举的name
            "stage": self.stage.name
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CultivationProgress":
        """从字典重建CultivationProgress"""
        return cls(level=data["level"], exp=data["exp"])



breakthrough_success_rate_by_realm = {
    Realm.Qi_Refinement: 0.8, # 练气，80%
    Realm.Foundation_Establishment: 0.6, # 筑基，60%
    Realm.Core_Formation: 0.4, # 金丹，40%
    Realm.Nascent_Soul: 0.2, # 元婴，20%
}

breakthrough_fail_reduce_lifespan_by_realm = {
    Realm.Qi_Refinement: 5,
    Realm.Foundation_Establishment: 10,
    Realm.Core_Formation: 15,
    Realm.Nascent_Soul: 20,
}