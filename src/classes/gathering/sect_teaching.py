import random
from typing import List, Optional, TYPE_CHECKING

from src.classes.gathering.gathering import Gathering, register_gathering
from src.classes.event import Event
if TYPE_CHECKING:
    from src.classes.core.world import World
from src.classes.core.sect import sects_by_id
from src.classes.effect.consts import EXTRA_EPIPHANY_PROBABILITY
from src.utils.config import CONFIG
from src.classes.story_teller import StoryTeller
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
            # 过滤死者
            living_members = [m for m in s.members.values() if not m.is_dead]
            if len(living_members) >= 2:
                valid_sects.append(s)
        
        if not valid_sects:
            return False
            
        # 2. 随机打乱以保证公平
        random.shuffle(valid_sects)
        
        # 从配置读取概率，默认 0.01
        trigger_prob = CONFIG.game.gathering.sect_teaching_prob
        
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
            
        return [m.id for m in sect.members.values() if not m.is_dead]

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
        base_epiphany_prob = CONFIG.game.gathering.base_epiphany_prob
        
        # 1. 选定角色 (逻辑复用，但只针对 target_sect)
        members = list(sect.members.values())
        # 过滤掉死者（防御性编程）
        members = [m for m in members if not m.is_dead]
        
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

        story = await self._generate_story(sect, teacher, students, exp_gains, epiphany_students)
        
        # 构造 Event 对象
        event = Event(
            month_stamp=world.month_stamp,
            content=story,
            related_avatars=[m.id for m in members],
            is_story=True,
            is_major=False # 虽是集体活动，但对个人而言算日常
        )
        events.append(event)
            
        return events

    def _calc_student_exp(self, student, teacher) -> int:
        # 听道奖励
        # 基础值 30 -> 改为动态，约为当前等级所需经验的一部分
        req_exp = student.cultivation_progress.get_exp_required()
        # 随机浮动 0.1 ~ 0.3
        ratio = random.uniform(0.1, 0.3)
        return int(req_exp * ratio)

    async def _generate_story(self, sect, teacher, students, exp_gains, epiphany_list):
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
        
        # 宗门信息
        # 使用 get_detailed_info 获取包含风格、阵营等完整信息
        details_list.append(sect.get_detailed_info())
        
        # 讲师信息
        details_list.append(f"{teacher.name}: {str(teacher.get_info(detailed=True))}")
        
        # 学生信息
        for s in students:
            # 使用非 detailed 信息
            details_list.append(f"- {s.name}: {str(s.get_info(detailed=False))}")
            
        details_text = "\n".join(details_list)
        
        return await StoryTeller.tell_gathering_story(
            gathering_info=t("sect_teaching_gathering_info", sect_name=sect.name),
            events_text=events_text,
            details_text=details_text,
            related_avatars=[teacher], # 传入Teacher用于获取世界观上下文
            prompt=t(self.STORY_PROMPT_ID)
        )
