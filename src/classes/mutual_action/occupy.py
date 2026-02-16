from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.mutual_action.mutual_action import MutualAction
from src.classes.event import Event
from src.classes.action.registry import register_action
from src.classes.action.cooldown import cooldown_action
from src.classes.environment.region import CultivateRegion
from src.classes.action_runtime import ActionResult, ActionStatus
from src.systems.battle import decide_battle
from src.classes.story_teller import StoryTeller
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason
from src.classes.action.event_helper import EventHelper
from src.utils.resolution import resolve_query
from src.utils.config import CONFIG
from src.run.log import get_logger
from src.systems.cultivation import REALM_RANK

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


@cooldown_action
@register_action(actual=True)
class Occupy(MutualAction):
    """
    占据动作（互动版）：
    占据指定的洞府。如果是无主洞府直接占据；如果是有主洞府，则发起抢夺。
    对方拒绝则进入战斗，进攻方胜利则洞府易主。
    """

    # 多语言 ID
    ACTION_NAME_ID = "occupy_action_name"
    DESC_ID = "occupy_description"
    REQUIREMENTS_ID = "occupy_requirements"
    STORY_PROMPT_ID = "occupy_story_prompt"

    # 不需要翻译的常量
    EMOJI = "🚩"
    PARAMS = {"region_name": "str"}
    FEEDBACK_ACTIONS = ["Yield", "Reject"]

    # 自定义反馈标签
    FEEDBACK_LABEL_IDS = {"Yield": "feedback_yield", "Reject": "feedback_reject"}

    IS_MAJOR = True
    ACTION_CD_MONTHS = 6

    DEFAULT_SOFT_BLOCK_REALM_DELTA = 1
    DEFAULT_HARD_BLOCK_REALM_DELTA = 2
    DEFAULT_SOFT_DECAY_MULTIPLIER = 0.5
    DEFAULT_RECKLESS_OVERRIDE_PROB = 0.1
    DEFAULT_RECKLESS_TRAIT_KEYS = ("ADVENTUROUS", "AGGRESSIVE", "RASH")
    DEFAULT_RECKLESS_TRAIT_NAMES = ("冒险", "好斗", "鲁莽")

    def _get_region_and_host(self, region_name: str) -> tuple[CultivateRegion | None, "Avatar | None", str]:
        """解析区域并获取主人"""
        res = resolve_query(region_name, self.world, expected_types=[CultivateRegion])

        # resolve_query 可能返回普通 Region，这里需要严格检查是否为 CultivateRegion
        region = res.obj

        if not res.is_valid or region is None:
            return None, None, t("Cannot find region: {region}", region=region_name)

        if not isinstance(region, CultivateRegion):
            return None, None, t("{region} is not a cultivation area, cannot occupy",
                                region=region.name if region else t("wilderness"))

        return region, region.host_avatar, ""

    def _risk_cfg_value(self, key: str, default):
        risk_cfg = getattr(CONFIG, "cave_heaven_risk", None)
        if risk_cfg is None:
            return default
        return getattr(risk_cfg, key, default)

    def _is_reckless_avatar(self, avatar: "Avatar") -> bool:
        configured_keys = self._risk_cfg_value("reckless_trait_keys", self.DEFAULT_RECKLESS_TRAIT_KEYS)
        configured_names = self._risk_cfg_value("reckless_trait_names", self.DEFAULT_RECKLESS_TRAIT_NAMES)
        reckless_keys = {str(k).upper() for k in configured_keys}
        reckless_names = {str(n) for n in configured_names}

        for persona in avatar.personas:
            trait_key = str(getattr(persona, "key", "")).strip()
            if trait_key:
                if trait_key.upper() in reckless_keys:
                    return True
                continue

            trait_name = str(getattr(persona, "name", "")).strip()
            if trait_name and trait_name in reckless_names:
                return True

        return False

    def _log_risk_decision(
        self,
        reason: str,
        npc: "Avatar",
        owner: "Avatar",
        realm_delta: int,
    ) -> None:
        if not self._risk_cfg_value("debug_log", False):
            return

        logger = get_logger().logger
        logger.info(
            "occupy_risk reason=%s npc_id=%s npc_realm=%s owner_id=%s owner_realm=%s realm_delta=%s",
            reason,
            npc.id,
            npc.cultivation_progress.realm.name,
            owner.id,
            owner.cultivation_progress.realm.name,
            realm_delta,
        )

    def _risk_evaluator(self, npc: "Avatar", owner: "Avatar | None") -> tuple[bool, float, str]:
        if owner is None:
            return True, 1.0, "owner_none"

        npc_realm = npc.cultivation_progress.realm
        owner_realm = owner.cultivation_progress.realm
        realm_delta = REALM_RANK.get(owner_realm, 0) - REALM_RANK.get(npc_realm, 0)

        hard_block_delta = int(
            self._risk_cfg_value("hard_block_realm_delta", self.DEFAULT_HARD_BLOCK_REALM_DELTA)
        )
        soft_block_delta = int(
            self._risk_cfg_value("soft_block_realm_delta", self.DEFAULT_SOFT_BLOCK_REALM_DELTA)
        )
        soft_decay = float(
            self._risk_cfg_value("soft_decay_multiplier", self.DEFAULT_SOFT_DECAY_MULTIPLIER)
        )
        reckless_override_prob = float(
            self._risk_cfg_value("reckless_override_prob", self.DEFAULT_RECKLESS_OVERRIDE_PROB)
        )

        is_reckless = self._is_reckless_avatar(npc)

        if realm_delta >= hard_block_delta:
            if is_reckless and random.random() < reckless_override_prob:
                self._log_risk_decision("override_allowed", npc, owner, realm_delta)
                return True, 1.0, "override_allowed"

            self._log_risk_decision("hard_block", npc, owner, realm_delta)
            return False, 0.0, "hard_block"

        if realm_delta == soft_block_delta:
            self._log_risk_decision("soft_decay", npc, owner, realm_delta)
            return True, soft_decay, "soft_decay"

        return True, 1.0, "normal"

    def can_start(self, region_name: str) -> tuple[bool, str]:
        region, host, err = self._get_region_and_host(region_name)
        if err:
            return False, err
        if region.host_avatar == self.avatar:
            return False, t("Already the owner of this cave dwelling")

        allowed, weight_multiplier, _reason = self._risk_evaluator(self.avatar, host)
        if not allowed:
            return False, t("Risk too high to seize this cave dwelling")

        # Current action scheduler has no explicit weight field. For soft-block, apply
        # proportional acceptance probability to reduce frequency while keeping non-zero chance.
        if weight_multiplier < 1.0 and random.random() > weight_multiplier:
            return False, t("Risk too high to seize this cave dwelling")

        return super().can_start(target_avatar=host)

    def start(self, region_name: str) -> Event:
        region, host, _ = self._get_region_and_host(region_name)

        self._start_month_stamp = self.world.month_stamp
        self.target_region_name = region_name

        region_display_name = region.name if region else self.avatar.tile.location_name
        content = t("{initiator} attempts to seize {region} from {host}",
                   initiator=self.avatar.name, region=region_display_name, host=host.name)

        rel_ids = [self.avatar.id]
        if host:
            rel_ids.append(host.id)

        event = Event(
            self._start_month_stamp,
            content,
            related_avatars=rel_ids,
            is_major=self.IS_MAJOR
        )

        return event

    def step(self, region_name: str) -> ActionResult:
        region, host, _ = self._get_region_and_host(region_name)
        return super().step(target_avatar=host)

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        """处理反馈结果"""
        region_name = getattr(self, "target_region_name", self.avatar.tile.location_name)
        region, _, _ = self._get_region_and_host(region_name)

        if feedback_name == "Yield":
            # 对方让步：直接转移所有权
            if region:
                self.avatar.occupy_region(region)

            # 共用一个事件
            event_text = t("{initiator} forced {target} to yield {region}",
                          initiator=self.avatar.name, target=target_avatar.name, region=region_name)
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
            if attacker_won and region:
                self.avatar.occupy_region(region)

            self._last_result = (winner, loser, loser_dmg, winner_dmg, region_name, attacker_won)

    async def finish(self, region_name: str) -> list[Event]:
        """完成动作，生成战斗故事并处理死亡"""
        res = self._last_result if hasattr(self, '_last_result') else None
        if res is None:
            return []

        # res format from occupy: (winner, loser, l_dmg, w_dmg, r_name, attacker_won)
        winner, loser, l_dmg, w_dmg, r_name, attacker_won = res
        battle_res = (winner, loser, l_dmg, w_dmg)

        target = loser if winner == self.avatar else winner

        start_text = t("{initiator} attempted to seize {target}'s cave dwelling {region}, {target} rejected and engaged in battle",
                      initiator=self.avatar.name, target=target.name, region=r_name)

        postfix = t(", successfully seized {region}", region=r_name) if attacker_won else t(", defended {region}", region=r_name)

        from src.systems.battle import handle_battle_finish
        return await handle_battle_finish(
            self.world,
            self.avatar,
            target,
            battle_res,
            start_text,
            self.get_story_prompt(),  # 使用 classmethod
            action_desc=t("defeated"),
            postfix=postfix
        )
