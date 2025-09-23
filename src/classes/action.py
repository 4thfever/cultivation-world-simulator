from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import random
import json
import inspect

from src.classes.essence import Essence, EssenceType
from src.classes.root import Root, get_essence_types_for_root, extra_breakthrough_success_rate
from src.classes.region import Region, CultivateRegion, NormalRegion, CityRegion
from src.classes.event import Event, NULL_EVENT
from src.classes.item import Item, items_by_name
from src.classes.prices import prices
from src.classes.hp_and_mp import HP_MAX_BY_REALM, MP_MAX_BY_REALM
from src.classes.battle import decide_battle

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.world import World


def long_action(step_month: int):
    """
    长态动作装饰器，用于为动作类自动添加时间管理功能
    
    Args:
        step_month: 动作需要的月份数
    """
    def decorator(cls):
        # 设置类属性，供基类使用
        cls._step_month = step_month
        
        def is_finished(self, *args, **kwargs) -> bool:
            """
            根据时间差判断动作是否完成
            接受但忽略额外的参数以保持与其他动作类型的兼容性
            """
            if self.start_monthstamp is None:
                return False
            # 修正逻辑：使用 >= step_month - 1 而不是 >= step_month
            # 这样1个月的动作在第1个月完成（时间差0 >= 0），10个月的动作在第10个月完成（时间差9 >= 9）
            # 避免了原来多执行一个月的bug
            return (self.world.month_stamp - self.start_monthstamp) >= self.step_month - 1
        
        # 只添加 is_finished 方法
        cls.is_finished = is_finished
        
        return cls
    
    return decorator

class Action(ABC):
    """
    角色可以执行的动作。
    比如，移动、攻击、采集、建造、etc。
    """
    def __init__(self, avatar: Avatar, world: World):
        """
        传一个avatar的ref
        这样子实际执行的时候，可以知道avatar的能力和状态
        可选传入world；若不传，则尝试从avatar.world获取。
        """
        self.avatar = avatar
        self.world = world

    @abstractmethod
    def execute(self) -> None:
        pass


    @property
    def name(self) -> str:
        """
        获取动作名称
        """
        return str(self.__class__.__name__)


class DefineAction(Action):
    def __init__(self, avatar: Avatar, world: World):
        """
        初始化动作，处理长态动作的属性设置
        """
        super().__init__(avatar, world)
        
        # 如果是长态动作，初始化相关属性
        if hasattr(self.__class__, '_step_month'):
            self.step_month = self.__class__._step_month
            self.start_monthstamp = None
    
    def execute(self, *args, **kwargs) -> None:
        """
        执行动作，处理时间管理逻辑，然后调用具体的_execute实现
        """
        # 如果是长态动作且第一次执行，记录开始时间
        if hasattr(self, 'step_month') and self.start_monthstamp is None:
            self.start_monthstamp = self.world.month_stamp
        
        self._execute(*args, **kwargs)
    
    @abstractmethod
    def _execute(self, *args, **kwargs) -> None:
        """
        具体的动作执行逻辑，由子类实现
        """
        pass 

class LLMAction(Action):
    """
    基于LLM的action，这种action一般是不需要实际的规则定义。
    而是一种抽象的，仅有社会层面的后果的定义。
    比如“折辱”“恶狠狠地盯着”“退婚”等
    这种action会通过LLM生成并被执行，让NPC记忆并产生后果。
    但是不需要规则侧做出反应来。
    """
    pass

class ChunkActionMixin():
    """
    动作片，可以理解成只是一种切分出来的动作。
    不能被avatar直接执行，而是成为avatar执行某个动作的步骤。
    """
    pass

class ActualActionMixin():
    """
    实际的可以被规则/LLM调用，让avatar去执行的动作。
    不一定是多个step，也有可能就一个step
    """
    @abstractmethod
    def is_finished(self) -> bool:
        """
        判断动作是否完成
        """
        pass
    
    @abstractmethod
    def get_event(self, *args, **kwargs) -> Event:
        """
        获取动作开始时的事件
        """
        pass

    @property
    @abstractmethod
    def is_doable(self) -> bool:
        """
        判断动作是否可以执行
        """
        pass


class Move(DefineAction, ChunkActionMixin):
    """
    最基础的移动动作，在tile之间进行切换。
    """
    COMMENT = "移动到某个相对位置"
    PARAMS = {"delta_x": "int", "delta_y": "int"}
    def _execute(self, delta_x: int, delta_y: int) -> None:
        """
        移动到某个tile
        """
        world = self.world
        # 基于境界的移动步长：每轴最多移动 move_step_length 格
        step = getattr(self.avatar, "move_step_length", 1)
        clamped_dx = max(-step, min(step, delta_x))
        clamped_dy = max(-step, min(step, delta_y))

        new_x = self.avatar.pos_x + clamped_dx
        new_y = self.avatar.pos_y + clamped_dy

        # 边界检查：越界则不移动
        if world.map.is_in_bounds(new_x, new_y):
            self.avatar.pos_x = new_x
            self.avatar.pos_y = new_y
            target_tile = world.map.get_tile(new_x, new_y)
            self.avatar.tile = target_tile
        else:
            # 超出边界：不改变位置与tile
            pass

class MoveToRegion(DefineAction, ActualActionMixin):
    """
    移动到某个region
    """
    COMMENT = "移动到某个区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "region_name"}
    def _execute(self, region: Region|str) -> None:
        """
        移动到某个region
        """
        if isinstance(region, str):
            from src.classes.region import regions_by_name
            region = regions_by_name[region]
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        region_center_loc = region.center_loc
        delta_x = region_center_loc[0] - cur_loc[0]
        delta_y = region_center_loc[1] - cur_loc[1]
        # 横纵向一次最多移动 move_step_length 格（可以同时横纵移动）
        step = getattr(self.avatar, "move_step_length", 1)
        delta_x = max(-step, min(step, delta_x))
        delta_y = max(-step, min(step, delta_y))
        Move(self.avatar, self.world).execute(delta_x, delta_y)

    def is_finished(self, region: Region|str) -> bool:
        """
        判断动作是否完成
        """
        if isinstance(region, str):
            from src.classes.region import regions_by_name
            region = regions_by_name[region]
        return self.avatar.is_in_region(region)
    
    def get_event(self, region: Region|str) -> Event:
        """
        获取移动动作开始时的事件
        """
        if isinstance(region, str):
            region_name = region
            from src.classes.region import regions_by_name
            if region in regions_by_name:
                region_name = regions_by_name[region].name
        elif hasattr(region, 'name'):
            region_name = region.name
        else:
            region_name = str(region)
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {region_name}")

    @property
    def is_doable(self) -> bool:
        """
        判断移动到区域动作是否可以执行
        """
        return True


class MoveToAvatar(DefineAction, ActualActionMixin):
    """
    朝另一个角色当前位置移动。
    """
    COMMENT = "移动到某个角色所在位置"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "str"}

    def _get_target(self, avatar_name: str):
        """
        根据名字查找目标角色；找不到返回 None。
        """
        for v in self.world.avatar_manager.avatars.values():
            if v.name == avatar_name:
                return v
        raise ValueError(f"未找到名为 {avatar_name} 的角色")

    def _execute(self, avatar_name: str) -> None:
        target = self._get_target(avatar_name)
        if target is None:
            return
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        target_loc = (target.pos_x, target.pos_y)
        delta_x = target_loc[0] - cur_loc[0]
        delta_y = target_loc[1] - cur_loc[1]
        step = getattr(self.avatar, "move_step_length", 1)
        delta_x = max(-step, min(step, delta_x))
        delta_y = max(-step, min(step, delta_y))
        Move(self.avatar, self.world).execute(delta_x, delta_y)

    def is_finished(self, avatar_name: str) -> bool:
        target = self._get_target(avatar_name)
        if target is None:
            return True
        return self.avatar.pos_x == target.pos_x and self.avatar.pos_y == target.pos_y

    def get_event(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {target_name}")

    @property
    def is_doable(self) -> bool:
        return True

@long_action(step_month=10)
class Cultivate(DefineAction, ActualActionMixin):
    """
    修炼动作，可以增加修仙进度。
    """
    COMMENT = "修炼，增进修为"
    DOABLES_REQUIREMENTS = "在修炼区域中，修炼区域的灵气为角色的灵根之一，且角色未到瓶颈。"
    PARAMS = {}
    def _execute(self) -> None:
        """
        修炼
        获得的exp增加取决于essence的对应灵根的大小。
        """
        root = self.avatar.root
        essence = self.avatar.tile.region.essence
        # 多元素：取与角色灵根任一匹配元素的最大密度
        essence_types = get_essence_types_for_root(root)
        essence_density = max((essence.get_density(et) for et in essence_types), default=0)
        exp = self.get_exp(essence_density)
        self.avatar.cultivation_progress.add_exp(exp)

    def get_exp(self, essence_density: int) -> int:
        """
        根据essence的密度，计算获得的exp。
        公式为：base * essence_density
        """
        base = 100
        return base * essence_density
    
    def get_event(self) -> Event:
        """
        获取修炼动作开始时的事件
        """
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.region.name} 开始修炼")

    @property
    def is_doable(self) -> bool:
        """
        判断修炼动作是否可以执行
        """
        root = self.avatar.root
        region = self.avatar.tile.region
        essence_types = get_essence_types_for_root(root)
        if not self.avatar.cultivation_progress.can_cultivate():
            return False
        if not isinstance(region, CultivateRegion):
            return False
        if all(region.essence.get_density(et) == 0 for et in essence_types):
            return False
        return True

# 突破境界class
@long_action(step_month=1)
class Breakthrough(DefineAction, ActualActionMixin):
    """
    突破境界。
    成功率由 `CultivationProgress.get_breakthrough_success_rate()` 决定；
    失败时按 `CultivationProgress.get_breakthrough_fail_reduce_lifespan()` 减少寿元（年）。
    """
    COMMENT = "尝试突破境界（成功增加寿元上限，失败折损寿元上限；境界越高，成功率越低。）"
    DOABLES_REQUIREMENTS = "角色处于瓶颈时"
    PARAMS = {}
    def calc_success_rate(self) -> float:
        """
        计算突破境界的成功率（由修为进度给出）
        """
        base = self.avatar.cultivation_progress.get_breakthrough_success_rate()
        bonus = extra_breakthrough_success_rate[self.avatar.root]
        # 夹紧到 [0, 1]
        return max(0.0, min(1.0, base + bonus))

    def _execute(self) -> None:
        """
        突破境界
        """
        assert self.avatar.cultivation_progress.can_break_through()   
        success_rate = self.calc_success_rate()
        if random.random() < success_rate:
            old_realm = self.avatar.cultivation_progress.realm
            self.avatar.cultivation_progress.break_through()
            new_realm = self.avatar.cultivation_progress.realm
            
            # 突破成功时更新HP和MP的最大值
            if new_realm != old_realm:
                self._update_hp_mp_on_breakthrough(new_realm)
                # 成功：确保最大寿元至少达到新境界的基线
                self.avatar.age.ensure_max_lifespan_at_least_realm_base(new_realm)
        else:
            # 突破失败：减少最大寿元上限
            reduce_years = self.avatar.cultivation_progress.get_breakthrough_fail_reduce_lifespan()
            self.avatar.age.decrease_max_lifespan(reduce_years)
    
    def _update_hp_mp_on_breakthrough(self, new_realm):
        """
        突破境界时更新HP和MP的最大值并完全恢复
        
        Args:
            new_realm: 新的境界
        """
        new_max_hp = HP_MAX_BY_REALM.get(new_realm, 100)
        new_max_mp = MP_MAX_BY_REALM.get(new_realm, 100)
        
        # 计算增加的最大值
        hp_increase = new_max_hp - self.avatar.hp.max
        mp_increase = new_max_mp - self.avatar.mp.max
        
        # 更新最大值并恢复相应的当前值
        self.avatar.hp.add_max(hp_increase)
        self.avatar.hp.recover(hp_increase)  # 突破时完全恢复HP
        self.avatar.mp.add_max(mp_increase)
        self.avatar.mp.recover(mp_increase)  # 突破时完全恢复MP
    
    def get_event(self) -> Event:
        """
        获取突破动作开始时的事件
        """
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始尝试突破境界")

    @property
    def is_doable(self) -> bool:
        """
        判断突破动作是否可以执行
        """
        return self.avatar.cultivation_progress.can_break_through()

@long_action(step_month=6)
class Play(DefineAction, ActualActionMixin):
    """
    游戏娱乐动作，持续半年时间
    """
    COMMENT = "游戏娱乐，放松身心"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {}
    
    def _execute(self) -> None:
        """
        进行游戏娱乐活动
        """
        # 游戏娱乐的具体逻辑可以在这里实现
        # 比如增加心情值、减少压力等
        pass
    
    def get_event(self) -> Event:
        """
        获取游戏娱乐动作开始时的事件
        """
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始玩耍")

    @property
    def is_doable(self) -> bool:
        return True


@long_action(step_month=6)
class Hunt(DefineAction, ActualActionMixin):
    """
    狩猎动作，在有动物的区域进行狩猎，持续6个月
    可以获得动物对应的物品
    """
    COMMENT = "在当前区域狩猎动物，获取动物材料"
    DOABLES_REQUIREMENTS = "在有动物的普通区域，且avatar的境界必须大于等于动物的境界"
    PARAMS = {}

    def get_available_animals(self) -> list[Animal]:
        """
        获取avatar境界足够的动物
        """
        region = self.avatar.tile.region
        avatar_realm = self.avatar.cultivation_progress.realm
        return [animal for animal in region.animals if avatar_realm >= animal.realm]
    
    def _execute(self) -> None:
        """
        执行狩猎动作
        """
        success_rate = self.get_success_rate()
        available_animals = self.get_available_animals()
        if len(available_animals) == 0:
            # TODO: 我的doable检查有问题，之后看看问题在哪里
            return
        
        if random.random() < success_rate:
            # 成功狩猎，从avatar境界足够的动物中随机选择一种
            target_animal = random.choice(available_animals)
            # 随机选择该动物的一种物品
            item = random.choice(target_animal.items)
            self.avatar.add_item(item, 1)
    
    def get_success_rate(self) -> float:
        """
        获取狩猎成功率，预留接口，目前固定为100%
        """
        return 1.0  # 100%成功率
    
    def get_event(self) -> Event:
        """
        获取狩猎动作开始时的事件
        """
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 开始狩猎")
    
    @property
    def is_doable(self) -> bool:
        """
        判断是否可以狩猎：必须在有动物的普通区域，且avatar的境界必须大于等于动物的境界
        """
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False
        available_animals = self.get_available_animals()
        if len(available_animals) == 0:
            return False
        return True


@long_action(step_month=6)
class Harvest(DefineAction, ActualActionMixin):
    """
    采集动作，在有植物的区域进行采集，持续6个月
    可以获得植物对应的物品
    """
    COMMENT = "在当前区域采集植物，获取植物材料"
    DOABLES_REQUIREMENTS = "在有植物的普通区域，且avatar的境界必须大于等于植物的境界"
    PARAMS = {}

    def get_available_plants(self) -> list[Plant]:
        """
        获取avatar境界足够的植物
        """
        region = self.avatar.tile.region
        avatar_realm = self.avatar.cultivation_progress.realm
        return [plant for plant in region.plants if avatar_realm >= plant.realm]
    
    def _execute(self) -> None:
        """
        执行采集动作
        """
        success_rate = self.get_success_rate()
        available_plants = self.get_available_plants()
        if len(available_plants) == 0:
            # TODO: 我的doable检查有问题，之后看看问题在哪里
            return

        if random.random() < success_rate:
            # 成功采集，从avatar境界足够的植物中随机选择一种
            target_plant = random.choice(available_plants)
            # 随机选择该植物的一种物品
            item = random.choice(target_plant.items)
            self.avatar.add_item(item, 1)
    
    def get_success_rate(self) -> float:
        """
        获取采集成功率，预留接口，目前固定为100%
        """
        return 1.0  # 100%成功率
    
    def get_event(self) -> Event:
        """
        获取采集动作开始时的事件
        """
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 开始采集")
    
    @property
    def is_doable(self) -> bool:
        """
        判断是否可以采集：必须在有植物的普通区域，且avatar的境界必须大于等于植物的境界
        """
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False
        avaliable_plants = self.get_available_plants()
        if len(avaliable_plants) == 0:
            return False
        return True


@long_action(step_month=1)
class Sold(DefineAction, ActualActionMixin):
    """
    在城镇出售指定名称的物品，一次性卖出持有的全部数量。
    收益为 item_price * item_num，动作耗时1个月。
    """
    COMMENT = "在城镇出售持有的某类物品的全部"
    DOABLES_REQUIREMENTS = "在城镇且背包非空"
    PARAMS = {"item_name": "str"}

    def _execute(self, item_name: str) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return

        # 找到物品
        item = items_by_name.get(item_name)
        if item is None:
            return

        # 检查持有数量
        quantity = self.avatar.get_item_quantity(item)
        if quantity <= 0:
            return

        # 计算价格并结算
        price_per = prices.get_price(item)
        total_gain = price_per * quantity

        # 扣除物品并增加灵石
        removed = self.avatar.remove_item(item, quantity)
        if not removed:
            return

        self.avatar.magic_stone = self.avatar.magic_stone + total_gain

    def get_event(self, item_name: str) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇出售 {item_name}")

    @property
    def is_doable(self) -> bool:
        # 只允许在城镇且背包非空时出现在动作空间
        region = self.avatar.tile.region
        return isinstance(region, CityRegion) and bool(self.avatar.items)


class Battle(DefineAction, ChunkActionMixin):
    COMMENT = "与目标进行对战，判定胜负"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}
    def _execute(self, avatar_name: str) -> None:
        target = None
        for v in self.world.avatar_manager.avatars.values():
            if v.name == avatar_name:
                target = v
                break
        if target is None:
            return
        winner, loser, _ = decide_battle(self.avatar, target)
        # 简化：失败者HP小额扣减
        if hasattr(loser, "hp"):
            loser.hp.reduce(10)
    def is_finished(self, avatar_name: str) -> bool:
        return True
    def get_event(self, avatar_name: str) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 与 {avatar_name} 进行对战")
    @property
    def is_doable(self) -> bool:
        return True
