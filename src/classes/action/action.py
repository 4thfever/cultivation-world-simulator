from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.event import Event
from src.classes.action_runtime import ActionResult, ActionStatus
from src.utils.params import filter_kwargs_for_callable

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World


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
    
    # 多语言支持的类变量（子类覆盖）
    ACTION_NAME_ID: str = ""
    DESC_ID: str = ""
    REQUIREMENTS_ID: str = ""

    # 是否允许参与聚会（如拍卖会、大比）
    ALLOW_GATHERING: bool = True
    
    # 是否允许触发世界随机事件（如奇遇、霉运）
    ALLOW_WORLD_EVENTS: bool = True

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

    EMOJI: str = ""
    
    @classmethod
    def get_action_name(cls) -> str:
        """获取动作名称的翻译"""
        if cls.ACTION_NAME_ID:
            return t(cls.ACTION_NAME_ID)
        return cls.__name__
    
    @classmethod
    def get_desc(cls) -> str:
        """获取动作描述的翻译"""
        if cls.DESC_ID:
            return t(cls.DESC_ID)
        return ""
    
    @classmethod
    def get_requirements(cls) -> str:
        """获取可执行条件的翻译"""
        if cls.REQUIREMENTS_ID:
            return t(cls.REQUIREMENTS_ID)
        return ""

    def get_save_data(self) -> dict:
        """获取需要存档的运行时数据"""
        return {}

    def load_save_data(self, data: dict) -> None:
        """加载运行时数据"""
        pass


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

    def get_save_data(self) -> dict:
        data = super().get_save_data()
        # 很多长态动作（包括MoveToDirection）都会设置此属性
        if hasattr(self, 'start_monthstamp'):
            val = self.start_monthstamp
            data['start_monthstamp'] = int(val) if val is not None else None
        return data

    def load_save_data(self, data: dict) -> None:
        super().load_save_data(data)
        if 'start_monthstamp' in data:
            val = data['start_monthstamp']
            if val is not None:
                from src.systems.time import MonthStamp
                self.start_monthstamp = MonthStamp(val)
            else:
                self.start_monthstamp = None


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
    不一定是多个step，也有可能就一个step。

    新接口：子类必须实现 can_start/start/step/finish。
    
    类变量：
    - IS_MAJOR: 是否为大事（长期记忆），默认False（小事/短期记忆）
    """
    
    # 默认为小事（短期记忆）
    IS_MAJOR: bool = False

    def create_event(self, content: str, related_avatars=None) -> Event:
        """
        创建事件的辅助方法，自动带上is_major属性
        
        Args:
            content: 事件内容
            related_avatars: 相关角色ID列表
            
        Returns:
            Event对象，is_major根据当前Action的IS_MAJOR类变量设置
        """
        from src.classes.action.action import Action
        # 获取当前类的IS_MAJOR属性
        is_major = self.__class__.IS_MAJOR if hasattr(self.__class__, 'IS_MAJOR') else False
        return Event(
            month_stamp=self.world.month_stamp,
            content=content,
            related_avatars=related_avatars,
            is_major=is_major
        )

    @abstractmethod
    def can_start(self, **params) -> tuple[bool, str]:
        return True, ""

    @abstractmethod
    def start(self, **params) -> Event | None:
        return None

    @abstractmethod
    def step(self, **params) -> ActionResult:
        ...

    @abstractmethod
    async def finish(self, **params) -> list[Event]:
        return []


class InstantAction(DefineAction, ActualActionMixin):
    """
    一次性动作：在一次 step 内完成。子类仅需实现 _execute。
    """

    def step(self, **params) -> ActionResult:
        params_for_execute = filter_kwargs_for_callable(self._execute, params)
        self._execute(**params_for_execute)
        return ActionResult(status=ActionStatus.COMPLETED, events=[])


class TimedAction(DefineAction, ActualActionMixin):
    """
    长态动作：通过类属性 duration_months 控制持续时间。
    子类实现 _execute 作为每月的执行逻辑。
    """

    duration_months: int = 1

    def step(self, **params) -> ActionResult:
        if not hasattr(self, 'start_monthstamp') or self.start_monthstamp is None:
            self.start_monthstamp = self.world.month_stamp
        params_for_execute = filter_kwargs_for_callable(self._execute, params)
        self._execute(**params_for_execute)
        done = (self.world.month_stamp - self.start_monthstamp) >= (self.duration_months - 1)
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])
