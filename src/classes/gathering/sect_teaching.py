import random
from typing import List, Optional, TYPE_CHECKING

from src.classes.gathering.gathering import Gathering, register_gathering
from src.classes.event import Event
if TYPE_CHECKING:
    from src.classes.core.world import World
from src.classes.core.sect import sects_by_id
from src.classes.effect.consts import EXTRA_EPIPHANY_PROBABILITY
from src.classes.story_event_service import StoryEventService
from src.classes.relation.relation_delta_service import RelationDeltaService
from src.utils.config import CONFIG
from src.i18n import t
from src.run.log import get_logger

@register_gathering
class SectTeachingConference(Gathering):
    """
    宗门传道大会
    """
    STORY_PROMPT_ID = "sect_teaching_story_prompt"

    def __init__(self):
        self.target_sect_id: Optional[int] = None

    def is_start(self, world: "World") -> bool:
        self.target_sect_id = None
        
        # 1. 筛选有效宗门 (成员数 >= 2)
        valid_sects = []
        for s in sects_by_id.values():
            # 过滤死者和不能参与的角色
            living_members = [m for m in s.members.values() if not m.is_dead and self._can_avatar_join(m)]
            if len(living_members) >= 2:
                valid_sects.append(s)
        
        if not valid_sects:
            return False
            
        # 2. 随机打乱以保证公平
        random.shuffle(valid_sects)
        
        # 从配置读取概率，默认 0.01
        trigger_prob = CONFIG.world.gathering.sect_teaching_prob
        
        # 3. 判定是否触发
        # 每个宗门独立判定，只要有一个中了就停下来。
        for sect in valid_sects:
            if random.random() < trigger_prob:
                self.target_sect_id = sect.id
                return True
                
        return False

    def get_related_avatars(self, world: "World") -> List[int]:
        if self.target_sect_id is None:
            return []
            
        sect = sects_by_id.get(self.target_sect_id)
        if not sect:
            return []
            
        return [m.id for m in sect.members.values() if not m.is_dead and self._can_avatar_join(m)]

    def get_info(self, world: "World") -> str:
        sect_name = ""
        if self.target_sect_id is not None:
             sect = sects_by_id.get(self.target_sect_id)
             if sect:
                 sect_name = sect.name
        
        return t("sect_teaching_gathering_info", sect_name=sect_name)

    async def execute(self, world: "World") -> List[Event]:
        if self.target_sect_id is None:
            return []
            
        sect = sects_by_id.get(self.target_sect_id)
        # 清空状态
        self.target_sect_id = None
        
        if not sect:
            return []
            
        events = []
        base_epiphany_prob = CONFIG.world.gathering.base_epiphany_prob
        
        # 1. 选定角色 (逻辑复用，但只针对 target_sect)
        members = list(sect.members.values())
        # 过滤掉死者（防御性编程）和不能参与的角色
        members = [m for m in members if not m.is_dead and self._can_avatar_join(m)]
        
        if len(members) < 2:
            return [] # 再次检查，防止状态变化
        
        # 按境界/等级排序，最高的为传道者
        # 优先按 Realm 排序，其次按 Level 排序
        members.sort(key=lambda x: (x.cultivation_progress.realm, x.cultivation_progress.level), reverse=True)
        
        teacher = members[0]
        students = members[1:]
        
        # 2. 结算奖励 & 稀有事件
        epiphany_students = []
        exp_gains = []
        
        for student in students:
            # 听道奖励
            student_exp = self._calc_student_exp(student, teacher)
            if student.cultivation_progress.can_cultivate():
                student.cultivation_progress.add_exp(student_exp)
                exp_gains.append((student, student_exp))
            
            # 判定顿悟（习得功法）
            # 逻辑：学生没有该功法 + 概率判定
            if student.technique != teacher.technique and teacher.technique is not None:
                # 计算概率
                extra_prob = student.effects.get(EXTRA_EPIPHANY_PROBABILITY, 0)
                prob = base_epiphany_prob + extra_prob
                
                if random.random() < prob:
                    # old_tech_name = student.technique.name if student.technique else t("None")
                    student.technique = teacher.technique
                    student.recalc_effects() # 重算属性（因为功法变了，可能有新的被动）
                    epiphany_students.append(student)

        # 3. 生成故事与事件
        
        # 生成摘要事件
        student_names = ", ".join([s.name for s in students])
        summary_content = t("sect_teaching_summary", 
                            sect_name=sect.name, 
                            teacher_name=teacher.name, 
                            student_names=student_names)
        
        summary_event = Event(
            month_stamp=world.month_stamp,
            content=summary_content,
            related_avatars=[m.id for m in members],
            is_story=False,
            is_major=False
        )
        events.append(summary_event)

        contribution_gain = 20 + len(students) * 10 + len(epiphany_students) * 15
        actual_gain = teacher.add_sect_contribution(contribution_gain)
        if actual_gain > 0:
            events.append(
                Event(
                    month_stamp=world.month_stamp,
                    content=t(
                        "{teacher_name} taught and guided others at the preaching conference, earning {amount} sect contribution for {sect_name}.",
                        teacher_name=teacher.name,
                        sect_name=sect.name,
                        amount=actual_gain,
                    ),
                    related_avatars=[teacher.id],
                    related_sects=[int(sect.id)],
                    is_story=False,
                    is_major=False,
                )
            )
        
        # 生成经验获得事件
        for student, exp in exp_gains:
            exp_content = t("sect_teaching_exp_gain", 
                            student_name=student.name, 
                            exp=exp)
            exp_event = Event(
                month_stamp=world.month_stamp,
                content=exp_content,
                related_avatars=[student.id],
                is_story=False,
                is_major=False
            )
            events.append(exp_event)

        story_event = await self._generate_story(sect, teacher, students, exp_gains, epiphany_students, world.month_stamp)
        if story_event is not None:
            events.append(story_event)

        for student in students:
            a_to_b, b_to_a = await RelationDeltaService.resolve_event_text_delta(
                action_key="gathering",
                avatar_a=teacher,
                avatar_b=student,
                event_text=summary_content,
            )
            RelationDeltaService.apply_bidirectional_delta(teacher, student, a_to_b, b_to_a)
            
        return events

    def _calc_student_exp(self, student, teacher) -> int:
        # 听道奖励
        # 基础值 30 -> 改为动态，约为当前等级所需经验的一部分
        req_exp = student.cultivation_progress.get_exp_required()
        # 随机浮动 0.1 ~ 0.3
        ratio = random.uniform(0.1, 0.3)
        return int(req_exp * ratio)

    async def _generate_story(self, sect, teacher, students, exp_gains, epiphany_list, month_stamp):
        # 1. 构造 Events Text (事件列表)
        events_list = []
        events_list.append(t("sect_teaching_event_desc", teacher_name=teacher.name))
        
        for student, exp in exp_gains:
            events_list.append(t("sect_teaching_exp_gain", student_name=student.name, exp=exp))
            
        if epiphany_list:
             names = ", ".join([s.name for s in epiphany_list])
             tech_name = teacher.technique.name if teacher.technique else ""
             events_list.append(t("epiphany_event_desc", names=names, tech_name=tech_name))

        events_text = "\n".join(events_list)

        # 2. 构造 Details Text (详细信息)
        details_list = []
        
        # 宗门信息：复用 decision context，但只提炼少量与传道大会氛围强相关的背景。
        details_list.append(self._build_sect_teaching_context_text(sect, teacher))
        
        # 讲师信息
        details_list.append(f"{teacher.name}: {str(teacher.get_info(detailed=True))}")
        
        # 学生信息
        for s in students:
            # 使用非 detailed 信息
            details_list.append(f"- {s.name}: {str(s.get_info(detailed=False))}")
            
        details_text = "\n".join(details_list)
        
        return await StoryEventService.maybe_create_gathering_story(
            month_stamp=month_stamp,
            gathering_info=t("sect_teaching_gathering_info", sect_name=sect.name),
            events_text=events_text,
            details_text=details_text,
            related_avatars=[teacher, *students],
            prompt=t(self.STORY_PROMPT_ID),
        )

    def _build_sect_teaching_context_text(self, sect, teacher) -> str:
        world = teacher.world
        event_storage = getattr(getattr(world, "event_manager", None), "_storage", None)
        if event_storage is None:
            return sect.get_detailed_info()

        try:
            from src.classes.core.sect import get_sect_decision_context

            ctx = get_sect_decision_context(
                sect=sect,
                world=world,
                event_storage=event_storage,
                history_limit=0,
            )
        except Exception as exc:
            get_logger().logger.warning(
                "Failed to build sect teaching context for %s(%s): %s",
                getattr(sect, "name", "unknown"),
                getattr(sect, "id", "unknown"),
                exc,
            )
            return sect.get_detailed_info()

        active_wars = list(getattr(ctx, "active_wars", []) or [])
        if active_wars:
            war_names = "、".join(
                str(item.get("other_sect_name", "") or "")
                for item in active_wars
                if item.get("other_sect_name")
            ) or "未知对手"
            diplomacy_line = f"当前局势：与 {war_names} 交战中。"
        else:
            diplomacy_line = "当前局势：宗门处于和平状态。"

        treasury_pressure = str(
            getattr(ctx, "economy", {}).get("treasury_pressure", "") or "stable"
        )
        treasury_map = {
            "ample": "财库充裕",
            "stable": "财库平稳",
            "tight": "财库偏紧",
            "critical": "财库吃紧",
        }
        resource_line = (
            f"宗门气象：{treasury_map.get(treasury_pressure, treasury_pressure)}，"
            f"备战状态 {str(getattr(ctx, 'self_assessment', {}).get('war_readiness', 'stable') or 'stable')}。"
        )

        border_ratio = float(getattr(ctx, "territory", {}).get("border_pressure_ratio", 0.0) or 0.0)
        border_line = (
            f"边境压力：{int(round(border_ratio * 100))}% 的势力边界与外界接壤，"
            f"当前势力范围 {int(getattr(ctx, 'territory', {}).get('tile_count', 0) or 0)} 格。"
        )

        members_line = (
            f"宗门现状：存活门人 {int(getattr(ctx, 'self_assessment', {}).get('alive_member_count', 0) or 0)} 人，"
            f"宗门总战力约 {int(float(getattr(ctx, 'power', {}).get('total_battle_strength', 0.0) or 0.0))}。"
        )

        return "\n".join(
            [
                sect.get_detailed_info(),
                diplomacy_line,
                resource_line,
                border_line,
                members_line,
            ]
        )
