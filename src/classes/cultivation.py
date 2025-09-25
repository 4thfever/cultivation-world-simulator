from enum import Enum
from functools import total_ordering

@total_ordering
class Realm(Enum):
    Qi_Refinement = "练气"
    Foundation_Establishment = "筑基"
    Core_Formation = "金丹"
    Nascent_Soul = "元婴"

    @classmethod
    def from_id(cls, realm_id: int) -> "Realm":
        order: tuple[Realm, ...] = (
            cls.Qi_Refinement,
            cls.Foundation_Establishment,
            cls.Core_Formation,
            cls.Nascent_Soul,
        )
        index = realm_id - 1
        if index < 0 or index >= len(order):
            raise ValueError(f"Unknown realm_id: {realm_id}")
        return order[index]

    def __lt__(self, other):
        if not isinstance(other, Realm):
            return NotImplemented
        order: tuple[Realm, ...] = (
            Realm.Qi_Refinement,
            Realm.Foundation_Establishment,
            Realm.Core_Formation,
            Realm.Nascent_Soul,
        )
        return order.index(self) < order.index(other)

class Stage(Enum):
    Early_Stage = "前期"
    Middle_Stage = "中期"
    Late_Stage = "后期"

LEVELS_PER_REALM = 30
LEVELS_PER_STAGE = 10

REALM_TO_MOVE_STEP = {
    Realm.Qi_Refinement: 1,
    Realm.Foundation_Establishment: 2,
    Realm.Core_Formation: 2,
    Realm.Nascent_Soul: 2,
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
        order: tuple[Realm, ...] = (
            Realm.Qi_Refinement,
            Realm.Foundation_Establishment,
            Realm.Core_Formation,
            Realm.Nascent_Soul,
        )
        return order[min(realm_index, len(order) - 1)]

    def get_stage(self, level: int) -> Stage:
        """获取阶段（算术推导：1-10前期，11-20中期，21-30后期）"""
        if level <= 0:
            return Stage.Early_Stage
        stage_index = ((level - 1) % LEVELS_PER_REALM) // LEVELS_PER_STAGE
        order: tuple[Stage, ...] = (
            Stage.Early_Stage,
            Stage.Middle_Stage,
            Stage.Late_Stage,
        )
        return order[min(stage_index, len(order) - 1)]

    def get_move_step(self) -> int:
        """
        每月能够移动的距离，
        练气，筑基为1
        金丹，元婴为2
        """
        return REALM_TO_MOVE_STEP[self.realm]

    def __str__(self) -> str:
        return self.get_info()

    def get_info(self) -> str:
        can_break_through = self.can_break_through()
        can_break_through_str = "可以突破" if can_break_through else "不可以突破"
        return f"{self.realm.value}{self.stage.value}({self.level}级){can_break_through_str}"

    def get_simple_info(self) -> str:
        return f"{self.realm.value}{self.stage.value}"

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
        return f"{self.realm.value}{self.stage.value}({self.level}级)。在瓶颈期：{self.is_in_bottleneck()}"

    def get_breakthrough_success_rate(self) -> float:
        return breakthrough_success_rate_by_realm[self.realm]
    
    def get_breakthrough_fail_reduce_lifespan(self) -> int:
        return breakthrough_fail_reduce_lifespan_by_realm[self.realm]



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