from enum import Enum

class Realm(Enum):
    Qi_Refinement = "练气"
    Foundation_Establishment = "筑基"
    Core_Formation = "金丹"
    Nascent_Soul = "元婴"

class Stage(Enum):
    Early_Stage = "前期"
    Middle_Stage = "中期"
    Late_Stage = "后期"

LEVELS_PER_REALM = 30
LEVELS_PER_STAGE = 10

LEVEL_TO_REALM = {
    0: Realm.Qi_Refinement,
    30: Realm.Foundation_Establishment,
    60: Realm.Core_Formation,
    90: Realm.Nascent_Soul,
}
LEVEL_TO_STAGE = {
    0: Stage.Early_Stage,
    10: Stage.Middle_Stage,
    20: Stage.Late_Stage,
}

# realm_id到Realm的映射（用于物品等级系统）
REALM_ID_TO_REALM = {
    1: Realm.Qi_Refinement,
    2: Realm.Foundation_Establishment,
    3: Realm.Core_Formation,
    4: Realm.Nascent_Soul,
}

LEVEL_TO_BREAK_THROUGH = {
    30: Realm.Foundation_Establishment,
    60: Realm.Core_Formation,
    90: Realm.Nascent_Soul,
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

    def get_realm(self, level: int) -> str:
        """获取境界"""
        for level_threshold, realm in reversed(list(LEVEL_TO_REALM.items())):
            if level >= level_threshold:
                return realm
        return Realm.Qi_Refinement

    def get_stage(self, level: int) -> Stage:
        """获取阶段"""
        _level = level % LEVELS_PER_REALM
        for level_threshold, stage in reversed(list(LEVEL_TO_STAGE.items())):
            if _level >= level_threshold:
                return stage
        return Stage.Early_Stage

    def get_month_step(self) -> int:
        """
        每月能够移动的距离，
        练气，筑基为1
        金丹，元婴为2
        """
        return int(self.level // LEVELS_PER_REALM * 2) + 1

    def __str__(self) -> str:
        can_break_through = self.can_break_through()
        can_break_through_str = "可以突破" if can_break_through else "不可以突破"
        return f"{self.realm.value}{self.stage.value}({self.level}级){can_break_through_str}"

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
        
        # 境界加成：每跨越一个境界，额外增加1000点经验值
        realm_bonus = (next_level // 30) * 1000
        
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
        
        # 检查是否可以升级
        if self.is_level_up():
            required_exp = self.get_exp_required()
            self.exp -= required_exp
            self.level += 1
            # 更新境界和阶段
            self.realm = self.get_realm(self.level)
            self.stage = self.get_stage(self.level)
            return True
        
        return False

    def break_through(self):
        """
        突破境界
        """
        self.level += 1
        self.realm = self.get_realm(self.level)
        self.stage = self.get_stage(self.level)

    def can_break_through(self) -> bool:
        """
        检查是否可以突破
        """
        return self.level in LEVEL_TO_BREAK_THROUGH.keys()

    def can_cultivate(self) -> bool:
        """
        检查是否可以修炼
        可以突破，说明到顶了，说明不能修炼了，必须突破后才能正常修炼。
        """
        return not self.can_break_through()

    def is_level_up(self) -> bool:
        """
        检查是否可以进入下一级
        """
        exp_required = self.get_exp_required()
        return self.exp >= exp_required

    def __str__(self) -> str:
        return f"{self.realm.value}{self.stage.value}({self.level}级)。可以突破：{self.can_break_through()}"


# 为Realm类添加from_id类方法
def _realm_from_id(cls, realm_id: int) -> Realm:
    """
    根据realm_id获取对应的Realm
    
    Args:
        realm_id: 境界ID (1-4)
        
    Returns:
        对应的Realm枚举值
        
    Raises:
        ValueError: 如果realm_id不存在
    """
    if realm_id not in REALM_ID_TO_REALM:
        raise ValueError(f"Unknown realm_id: {realm_id}")
    return REALM_ID_TO_REALM[realm_id]

# 将from_id方法绑定到Realm类
Realm.from_id = classmethod(_realm_from_id)

# 境界顺序映射
_REALM_ORDER = {
    Realm.Qi_Refinement: 1,
    Realm.Foundation_Establishment: 2,
    Realm.Core_Formation: 3,
    Realm.Nascent_Soul: 4,
}

# 为Realm类添加比较操作符
def _realm_ge(self, other):
    """大于等于比较"""
    if not isinstance(other, Realm):
        return NotImplemented
    return _REALM_ORDER[self] >= _REALM_ORDER[other]

def _realm_le(self, other):
    """小于等于比较"""
    if not isinstance(other, Realm):
        return NotImplemented
    return _REALM_ORDER[self] <= _REALM_ORDER[other]

def _realm_gt(self, other):
    """大于比较"""
    if not isinstance(other, Realm):
        return NotImplemented
    return _REALM_ORDER[self] > _REALM_ORDER[other]

def _realm_lt(self, other):
    """小于比较"""
    if not isinstance(other, Realm):
        return NotImplemented
    return _REALM_ORDER[self] < _REALM_ORDER[other]

# 将比较方法绑定到Realm类
Realm.__ge__ = _realm_ge
Realm.__le__ = _realm_le
Realm.__gt__ = _realm_gt
Realm.__lt__ = _realm_lt