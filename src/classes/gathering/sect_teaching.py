import random
from typing import List, Optional

from src.classes.gathering.gathering import Gathering, register_gathering
from src.classes.event import Event
from src.classes.core.world import World
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
        for s in world.sect_manager.sects.values():
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

    async def execute(self, world: "World") -> List[Event]:
        if self.target_sect_id is None:
            return []
            
        sect = world.sect_manager.sects.get(self.target_sect_id)
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
        
        for student in students:
            # 听道奖励
            student_exp = self._calc_student_exp(student, teacher)
            if student.cultivation_progress.can_cultivate():
                student.cultivation_progress.add_exp(student_exp)
            
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
                    get_logger().logger.info(f"[SectTeaching] {student.name} learned {teacher.technique.name} from {teacher.name} via Epiphany.")

        # 3. 生成故事与事件
        story = await self._generate_story(sect, teacher, epiphany_students)
        
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
        # 基础值 30
        return 30

    async def _generate_story(self, sect, teacher, epiphany_list):
        # 构造 Prompt
        
        # 收集顿悟者名单
        epiphany_text = ""
        if epiphany_list:
             names = ", ".join([s.name for s in epiphany_list])
             epiphany_text = t("epiphany_event_desc", names=names, tech_name=teacher.technique.name if teacher.technique else "")
        
        # 构造详细上下文
        prompt = t("sect_teaching_context_prompt", 
                   sect_name=sect.name, 
                   style=t(sect.member_act_style),
                   teacher_name=teacher.name,
                   teacher_realm=teacher.cultivation_progress.get_info(),
                   epiphany_text=epiphany_text)

        # 基础事件描述
        event_desc = t("sect_teaching_event_desc", teacher_name=teacher.name)
        
        return await StoryTeller.tell_gathering_story(
            gathering_info=t("sect_teaching_gathering_info", sect_name=sect.name),
            events_text=event_desc,
            details_text=prompt,
            related_avatars=[teacher] # 传入Teacher用于获取世界观上下文
        )
