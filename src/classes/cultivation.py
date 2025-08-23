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

levels_per_realm = 30
levels_per_stage = 10

level_to_realm = {
    0: Realm.Qi_Refinement,
    30: Realm.Foundation_Establishment,
    60: Realm.Core_Formation,
    90: Realm.Nascent_Soul,
}
level_to_stage = {
    0: Stage.Early_Stage,
    10: Stage.Middle_Stage,
    20: Stage.Late_Stage,
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
        for level_threshold, realm in reversed(list(level_to_realm.items())):
            if level >= level_threshold:
                return realm
        return Realm.Qi_Refinement

    def get_stage(self, level: int) -> str:
        """获取阶段"""
        _level = self.level % levels_per_realm
        for level_threshold, stage in reversed(list(level_to_stage.items())):
            if _level >= level_threshold:
                return stage
        return Stage.Early_Stage

    def __str__(self) -> str:
        return f"{self.realm.value}{self.stage.value}({self.level}级)"

    def get_exp_required(self, target_level: int) -> int:
        """
        计算升级到指定等级需要的经验值
        使用指数增长公式：base_exp * (growth_rate ^ level) * realm_multiplier
        
        参数:
            target_level: 目标等级
        
        返回:
            需要的经验值
        """
        if target_level <= 0 or target_level > 120:
            return 0
        
        base_exp = 100  # 基础经验值
        growth_rate = 1.15  # 每级增长15%
        
        # 境界加成倍数：每跨越一个境界，经验需求增加50%
        realm_multiplier = 1 + (target_level // 30) * 0.5
        
        exp_required = int(base_exp * (growth_rate ** target_level) * realm_multiplier)
        return exp_required

    def can_level_up(self) -> bool:
        """
        检查是否可以升级
        
        返回:
            如果经验值足够升级则返回True
        """
        required_exp = self.get_exp_required(self.level + 1)
        return self.exp >= required_exp

    def get_exp_progress(self) -> tuple[int, int]:
        """
        获取当前经验值进度
        
        返回:
            (当前经验值, 升级所需经验值)
        """
        required_exp = self.get_exp_required(self.level + 1)
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
        while self.can_level_up():
            required_exp = self.get_exp_required()
            self.exp -= required_exp
            self.level += 1
            # 更新境界和阶段
            self.realm = self.get_realm(self.level)
            self.stage = self.get_stage(self.level)
            return True
        
        return False
