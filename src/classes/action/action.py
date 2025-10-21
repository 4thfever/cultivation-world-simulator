from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.classes.event import Event
from src.classes.action_runtime import ActionResult, ActionStatus

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
    不一定是多个step，也有可能就一个step。

    新接口：子类必须实现 can_start/start/step/finish。
    """

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
    def finish(self, **params) -> list[Event]:
        return []


class InstantAction(DefineAction, ActualActionMixin):
    """
    一次性动作：在一次 step 内完成。子类仅需实现 _execute。
    """

    def step(self, **params) -> ActionResult:
        self._execute(**params)
        return ActionResult(status=ActionStatus.COMPLETED, events=[])


class TimedAction(DefineAction, ActualActionMixin):
    """
    长态动作：通过类属性 duration_months 控制持续时间。
    子类实现 _execute 作为每月的执行逻辑。
    """

    duration_months: int = 1

    def step(self, **params) -> ActionResult:
        if getattr(self, 'start_monthstamp', None) is None:
            self.start_monthstamp = self.world.month_stamp
        self._execute(**params)
        done = (self.world.month_stamp - self.start_monthstamp) >= (self.duration_months - 1)
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])


