from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.classes.mutual_action.mutual_action import MutualAction
from src.classes.event import Event
from src.classes.action.registry import register_action
from src.classes.action.cooldown import cooldown_action
from src.classes.region import resolve_region, CultivateRegion
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.battle import decide_battle
from src.classes.story_teller import StoryTeller
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason
from src.classes.action.event_helper import EventHelper

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@cooldown_action
@register_action(actual=True)
class Occupy(MutualAction):
    """
    占据动作（互动版）：
    占据指定的洞府。如果是无主洞府直接占据；如果是有主洞府，则发起抢夺。
    对方拒绝则进入战斗，进攻方胜利则洞府易主。
    """
    ACTION_NAME = "抢夺洞府"
    COMMENT = "占据或抢夺洞府"
    PARAMS = {"region_name": "str"}
    FEEDBACK_ACTIONS = ["Yield", "Reject"]
    FEEDBACK_LABELS = {"Yield": "让步", "Reject": "拒绝"}
    IS_MAJOR = True
    ACTION_CD_MONTHS = 6
    
    STORY_PROMPT = "这是一场争夺洞府的战斗。不要出现具体血量或伤害数值。"

    def _get_region_and_host(self, region_name: str) -> tuple[CultivateRegion | None, "Avatar | None", str]:
        """解析区域并获取主人"""
        region = resolve_region(self.world, region_name)
        if region is None:
            return None, None, f"无法找到区域：{region_name}"
        if not isinstance(region, CultivateRegion):
            return None, None, f"{region.name} 不是修炼区域，无法占据"
        return region, region.host_avatar, ""

    def can_start(self, region_name: str) -> tuple[bool, str]:
        region, host, err = self._get_region_and_host(region_name)
        if err:
            return False, err
        if region.host_avatar == self.avatar:
            return False, "已经是该洞府的主人了"
        return super().can_start(target_avatar=host)

    def start(self, region_name: str) -> Event:
        region, host, _ = self._get_region_and_host(region_name)

        # 必须初始化开始时间
        self._start_month_stamp = self.world.month_stamp

        target_name = host.name if host else "无主之地"
        event_text = f"{self.avatar.name} 对 {target_name} 的 {region.name} 发起抢夺"

        rel_ids = [self.avatar.id]
        if host:
            rel_ids.append(host.id)

        event = Event(
            self._start_month_stamp,
            event_text,
            related_avatars=rel_ids,
            is_major=self.IS_MAJOR
        )
        # 记录到历史，侧边栏推送由 ActionMixin.commit_next_plan 统一处理
        self.avatar.add_event(event, to_sidebar=False)
        if host:
            host.add_event(event, to_sidebar=False)

        return event

    def step(self, region_name: str) -> ActionResult:
        region, host, _ = self._get_region_and_host(region_name)
        return super().step(target_avatar=host)

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        """处理反馈结果"""
        region = self.avatar.tile.region
        
        if feedback_name == "Yield":
            # 对方让步：直接转移所有权
            region.host_avatar = self.avatar
            
            # 共用一个事件
            event_text = f"{self.avatar.name} 逼迫 {target_avatar.name} 让出了 {region.name}。"
            event = Event(
                self.world.month_stamp, 
                event_text, 
                related_avatars=[self.avatar.id, target_avatar.id],
                is_major=True
            )
            # 统一推送，避免重复
            EventHelper.push_pair(event, initiator=self.avatar, target=target_avatar, to_sidebar_once=True)
            
            self._last_result = None
            
        elif feedback_name == "Reject":
            # 对方拒绝：进入战斗
            winner, loser, loser_dmg, winner_dmg = decide_battle(self.avatar, target_avatar)
            loser.hp.reduce(loser_dmg)
            winner.hp.reduce(winner_dmg)
            
            # 进攻方胜利则洞府易主
            attacker_won = winner == self.avatar
            if attacker_won:
                region.host_avatar = self.avatar
            
            self._last_result = (winner, loser, loser_dmg, winner_dmg, region.name, attacker_won)

    async def finish(self, region_name: str) -> list[Event]:
        """完成动作，生成战斗故事并处理死亡"""
        res = self._last_result if hasattr(self, '_last_result') else None
        if res is None:
            return []
        
        # res format from occupy: (winner, loser, l_dmg, w_dmg, r_name, attacker_won)
        winner, loser, l_dmg, w_dmg, r_name, attacker_won = res
        battle_res = (winner, loser, l_dmg, w_dmg)
        
        target = loser if winner == self.avatar else winner
        
        start_text = f"{self.avatar.name} 试图抢夺 {target.name} 的洞府 {r_name}，{target.name} 拒绝并应战"
        
        postfix = f"，成功夺取了 {r_name}" if attacker_won else f"，守住了 {r_name}"

        from src.classes.battle import handle_battle_finish
        return await handle_battle_finish(
            self.world,
            self.avatar,
            target,
            battle_res,
            start_text,
            self.STORY_PROMPT,
            action_desc="击败了",
            postfix=postfix
        )
