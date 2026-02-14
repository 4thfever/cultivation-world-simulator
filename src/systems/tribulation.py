"""
天劫系统
负责管理突破时的各种劫难类型、描述和选择逻辑
"""
from __future__ import annotations
import random
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

from src.classes.relation.relation import Relation


@dataclass
class TribulationType:
    """天劫类型定义"""
    name: str  # 劫难名称
    description: str  # 劫难描述（用于生成故事的提示）
    requires_other_avatar: bool = False  # 是否需要关联其他角色
    relation_type: Optional[Relation] = None  # 需要的关系类型


# 天劫类型定义
TRIBULATION_TYPES = {
    "心魔": TribulationType(
        name="心魔",
        description="心念起伏，自我否定与执念缠斗，外寂而内喧。道心深处，旧日疑惑与未来迷茫交织，一念之差即可坠入心魔深渊。",
        requires_other_avatar=False
    ),
    "雷劫": TribulationType(
        name="雷劫",
        description="天威如潮，电光凝成纹理，压迫骨血与神识。紫霄雷霆自九天垂落，每一道雷光都是天地对修士的考校，稍有不慎便是形神俱灭。",
        requires_other_avatar=False
    ),
    "肉身": TribulationType(
        name="肉身",
        description="筋骨皮膜重塑，真气磨砺经脉，疼痛与新生并至。肉身如熔炉，每一寸血肉都在烈火中淬炼，破而后立，痛极方能重生。",
        requires_other_avatar=False
    ),
    "寻仇": TribulationType(
        name="寻仇",
        description="仇人旧怨不散，刀光在心底回响，一念之差改写因果。因果纠缠，宿怨难消，突破之际正是因果清算之时。",
        requires_other_avatar=True,
        relation_type=Relation.IS_ENEMY_OF
    ),
    "情劫": TribulationType(
        name="情劫",
        description="柔情即刃，难舍难分，念头被拉回人间烟火。情丝缠绕，斩不断理还乱，一念执着便是万劫不复。",
        requires_other_avatar=True,
        relation_type=Relation.IS_LOVER_OF
    ),
    "阳罡": TribulationType(
        name="阳罡",
        description="日轮灼烈，天地赤白两色，阳罡刀风如白金烈焰。正气涤秽，刚猛直击，阳盛则裂。午时最烈，光杀心识，经脉燥爆之险时刻相随。",
        requires_other_avatar=False
    ),
    "雷火": TribulationType(
        name="雷火",
        description="云海层叠，紫电潜伏，雷中生火、火中孕雷。外冲与内炼同调，神魂与经络双线考校。雷海覆顶，业劫天火焚因果，一瞬之间便是生死两重天。",
        requires_other_avatar=False
    ),
    "风灾": TribulationType(
        name="风灾",
        description="无风之地先起丝音，罡风断骨，真空撕扯，噬灵风蚀。风洞共鸣如锯切，位移与姿态稍有不慎便是肉身裂口、护体法相被剥。",
        requires_other_avatar=False
    ),
    "阴狱": TribulationType(
        name="阴狱",
        description="温度突降，黑霜上爬，冤魂压境，寒狱锁身。六道幻刑，阴火烛骨，以业、怖、悔、执为四柱。善恶因果入场，心神判定重于肉身。",
        requires_other_avatar=False
    ),
    "魔劫": TribulationType(
        name="魔劫",
        description="心跳与灵识节奏错位，旧欲旧恨自启，识海生魔胎影。心魔境中，欲、嗔、痴、慢、疑轮番试探，道心完整度与自洽度为核，一念之差即可走火入魔。",
        requires_other_avatar=False
    ),
}


# 故事生成的基础提示词
STORY_PROMPT_BASE = "以古风、凝练、不炫技的笔触，描绘修士历经{calamity}劫时的心境与取舍，篇幅100~150字。"


class TribulationSelector:
    """天劫选择器，负责根据修士状态选择合适的劫难"""
    
    @staticmethod
    def choose_tribulation(avatar: Avatar) -> str:
        """
        根据修士的境界、关系等选择劫难类型
        
        Args:
            avatar: 渡劫的修士
            
        Returns:
            劫难名称
        """
        # 基础劫难池（不需要其他角色）
        base_tribulations = ["心魔", "雷劫", "肉身", "阳罡", "雷火", "风灾", "阴狱", "魔劫"]
        
        # 检查是否有特殊关系，可以触发关系型劫难
        available_tribulations = base_tribulations.copy()
        
        rels = getattr(avatar, "relations", {})
        has_enemy = any(rel is Relation.IS_ENEMY_OF for rel in rels.values())
        has_lover = any(rel is Relation.IS_LOVER_OF for rel in rels.values())
        
        if has_enemy:
            available_tribulations.append("寻仇")
        if has_lover:
            available_tribulations.append("情劫")
        
        return random.choice(available_tribulations)
    
    @staticmethod
    def choose_related_avatar(avatar: Avatar, tribulation_name: str) -> Optional[Avatar]:
        """
        根据劫难类型选择相关的角色（如果需要）
        
        Args:
            avatar: 渡劫的修士
            tribulation_name: 劫难名称
            
        Returns:
            相关角色，如果不需要则返回 None
        """
        tribulation = TRIBULATION_TYPES.get(tribulation_name)
        if not tribulation or not tribulation.requires_other_avatar:
            return None
        
        target_rel = tribulation.relation_type
        candidates = [
            other for other, rel in avatar.relations.items() 
            if rel is target_rel
        ]
        
        if not candidates:
            return None
        
        return random.choice(candidates)
    
    @staticmethod
    def get_description(tribulation_name: str) -> str:
        """
        获取劫难的描述文本
        
        Args:
            tribulation_name: 劫难名称
            
        Returns:
            劫难描述
        """
        tribulation = TRIBULATION_TYPES.get(tribulation_name)
        return tribulation.description if tribulation else ""
    
    @staticmethod
    def get_story_prompt(tribulation_name: str) -> str:
        """
        获取生成故事的提示词
        
        Args:
            tribulation_name: 劫难名称
            
        Returns:
            完整的故事生成提示词
        """
        desc = TribulationSelector.get_description(tribulation_name)
        prompt = STORY_PROMPT_BASE.format(calamity=tribulation_name)
        return (prompt + (" " + desc if desc else "")).strip()

