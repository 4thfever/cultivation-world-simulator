from typing import List, Dict, Optional, Any, TYPE_CHECKING
import random
import asyncio
from dataclasses import dataclass

from src.classes.gathering.gathering import Gathering, register_gathering
from src.classes.event import Event
if TYPE_CHECKING:
    from src.classes.core.world import World
    from src.classes.core.avatar import Avatar

from src.classes.items.item import Item
from src.utils.df import game_configs, get_str, get_float, get_int
from src.systems.cultivation import Realm, REALM_ORDER, REALM_RANK
from src.classes.death_reason import DeathReason, DeathType
from src.classes.death import handle_death
from src.classes.items.weapon import get_random_weapon_by_realm
from src.classes.items.auxiliary import get_random_auxiliary_by_realm
from src.classes.technique import get_random_technique_for_avatar
from src.i18n import t
from src.run.log import get_logger

logger = get_logger().logger

@dataclass
class DomainConfig:
    id: str
    name: str
    desc: str
    required_realm: Realm
    danger_prob: float
    hp_loss_percent: float
    drop_prob: float
    cd_years: int
    open_prob: float

@register_gathering
class HiddenDomain(Gathering):
    """
    秘境系统 (Hidden Domain)
    定期开启，只有对应境界的修士可进入探索，面临凶险或获得机缘。
    """
    
    # 记录每个秘境上次开启的年份 {domain_id: last_open_year}
    _domain_states: Dict[str, int] = {}
    
    # 临时存储本轮开启的秘境
    _active_domains: List[DomainConfig] = []
    
    # LLM Prompt ID
    STORY_PROMPT_ID = "hidden_domain_story_prompt"

    @classmethod
    def get_story_prompt(cls) -> str:
        return t(cls.STORY_PROMPT_ID)

    def _load_configs(self) -> List[DomainConfig]:
        """从配置表加载秘境配置"""
        configs = []
        df = game_configs.get("hidden_domain")
        if df is None:
            return []
        
        for row in df:
            try:
                # 必须字段
                conf = DomainConfig(
                    id=get_str(row, "id"),
                    name=get_str(row, "name"),
                    desc=get_str(row, "desc"),
                    required_realm=Realm.from_str(get_str(row, "required_realm")),
                    danger_prob=get_float(row, "danger_prob"),
                    hp_loss_percent=get_float(row, "hp_loss_percent"),
                    drop_prob=get_float(row, "drop_prob"),
                    cd_years=get_int(row, "cd_years"),
                    open_prob=get_float(row, "open_prob"),
                )
                configs.append(conf)
            except Exception as e:
                logger.error(f"Failed to load hidden domain config: {e}")
                continue
        return configs

    def is_start(self, world: "World") -> bool:
        """
        判断是否有秘境开启
        """
        self._active_domains = []
        current_year = world.month_stamp.get_year()
        configs = self._load_configs()
        
        for conf in configs:
            last_open = self._domain_states.get(conf.id, -999)
            
            # 只有 CD 转好才进行概率判定
            if current_year - last_open >= conf.cd_years:
                if random.random() < conf.open_prob:
                    self._active_domains.append(conf)
                    # 立即更新状态，防止同一step多次调用导致状态不一致（虽然后续execute才算正式执行）
                    # 但GatheringManager是 is_start -> execute 顺序执行，所以这里更新没问题
                    # 如果需要execute失败回滚，可以把更新移到execute里。这里简单起见放在这里。
                    self._domain_states[conf.id] = current_year
                    
        return len(self._active_domains) > 0

    def get_related_avatars(self, world: "World") -> List[int]:
        """
        获取所有可能参与的角色（即所有存活角色，具体筛选在 execute 中按秘境条件进行）
        """
        return [av.id for av in world.avatar_manager.get_living_avatars()]

    def get_info(self, world: "World") -> str:
        details = []
        for conf in self._active_domains:
            detail = t("Hidden Domain {name} opened! Entry restricted to {realm} only.", 
                       name=conf.name, 
                       realm=str(conf.required_realm))
            details.append(detail)
        return t("Hidden Domains opened: {names}", names="\n".join(details))

    def _get_next_realm(self, realm: Realm) -> Optional[Realm]:
        """获取下一个大境界"""
        current_idx = REALM_RANK.get(realm)
        if current_idx is not None and current_idx + 1 < len(REALM_ORDER):
            return REALM_ORDER[current_idx + 1]
        return None

    def _generate_loot(self, avatar: "Avatar", next_realm: Realm) -> Optional[Item]:
        """生成掉落物：优先给予高一阶的物品"""
        # 掉落类型权重：兵器(40%), 防具(40%), 功法(20%)
        roll = random.random()
        
        loot = None
        if roll < 0.4:
            # 兵器
            loot = get_random_weapon_by_realm(next_realm)
        elif roll < 0.8:
            # 防具
            loot = get_random_auxiliary_by_realm(next_realm)
        else:
            # 功法：尝试获取更高级的功法
            # get_random_technique_for_avatar 根据灵根匹配，但这里我们希望给一点“机缘”
            # 复用该函数，但可能获取到同阶的。为了体现“机缘”，我们允许多试几次取最好的，或者直接给
            # 这里简单调用现有接口
            loot = get_random_technique_for_avatar(avatar)
            
        return loot

    async def execute(self, world: "World") -> List[Event]:
        events = []
        
        for domain in self._active_domains:
            domain_events = await self._process_single_domain(world, domain)
            events.extend(domain_events)
            
        return events

    async def _process_single_domain(self, world: "World", domain: DomainConfig) -> List[Event]:
        """处理单个秘境的逻辑"""
        events = []
        month_stamp = world.month_stamp
        
        # 1. 筛选进入秘境的角色
        entrants: List["Avatar"] = []
        for av in world.avatar_manager.get_living_avatars():
            # 境界判定：只能是对应境界进入
            if av.cultivation_progress.realm == domain.required_realm:
                entrants.append(av)

        # 添加开启事件
        entrants_names = [av.name for av in entrants]
        if entrants_names:
            entrants_str = ", ".join(entrants_names)
            open_event_content = t("Hidden Domain {name} opened! Entry restricted to {realm} only. Entrants: {entrants}", 
                                   name=domain.name, 
                                   realm=str(domain.required_realm),
                                   entrants=entrants_str)
        else:
            open_event_content = t("Hidden Domain {name} opened! Entry restricted to {realm} only. No one entered.", 
                                   name=domain.name, 
                                   realm=str(domain.required_realm))
        events.append(Event(month_stamp, open_event_content))
                
        if not entrants:
            return events

        # 记录本次秘境的事件文本和相关角色
        event_texts: List[str] = [open_event_content]
        related_avatars_set: set["Avatar"] = set()
        empty_handed_avatars: List["Avatar"] = []
        
        # 2. 遍历角色执行逻辑
        for av in entrants:
            # --- 效果结算 ---
            extra_drop = float(av.effects.get("extra_hidden_domain_drop_prob", 0.0))
            extra_danger = float(av.effects.get("extra_hidden_domain_danger_prob", 0.0))

            drop_prob = domain.drop_prob + extra_drop
            danger_prob = domain.danger_prob + extra_danger
            
            # 确保概率合理
            danger_prob = max(0.0, danger_prob)
                
            # --- 凶险判定 ---
            triggered_event = False
            
            if random.random() < danger_prob:
                triggered_event = True
                loss_percent = domain.hp_loss_percent
                damage = int(av.hp.max * loss_percent)
                av.hp.cur -= damage
                
                if av.hp.cur <= 0:
                    # 死亡结算
                    reason = DeathReason(DeathType.HIDDEN_DOMAIN)
                    handle_death(world, av, reason)
                    
                    event_content = t("{name} perished in the hidden domain {domain}.", name=av.name, domain=domain.name)
                    event = Event(
                        month_stamp,
                        event_content,
                        related_avatars=[av.id]
                    )
                    events.append(event)
                    
                    event_texts.append(event_content)
                    related_avatars_set.add(av)
                    continue # 死了就不能拿奖励了
            
            # --- 机缘判定 ---
            if random.random() < drop_prob:
                triggered_event = True
                # 获取奖励阶位（高一阶）
                target_realm = self._get_next_realm(av.cultivation_progress.realm)
                # 如果已经是最高阶，则维持当前阶位
                if not target_realm:
                    target_realm = av.cultivation_progress.realm
                    
                loot = self._generate_loot(av, target_realm)
                
                if loot:
                    # 发放奖励
                    from src.classes.items.weapon import Weapon
                    from src.classes.items.auxiliary import Auxiliary
                    from src.classes.technique import Technique
                    from src.classes.prices import prices
                    
                    loot_name = loot.name
                    
                    if isinstance(loot, Weapon):
                        old = av.weapon
                        av.change_weapon(loot)
                        if old: # 回收旧物
                            av.magic_stone += prices.get_selling_price(old, av)
                            
                    elif isinstance(loot, Auxiliary):
                        old = av.auxiliary
                        av.change_auxiliary(loot)
                        if old:
                            av.magic_stone += prices.get_selling_price(old, av)
                            
                    elif isinstance(loot, Technique):
                        # 只有当比当前功法好，或者还没功法时才更换？
                        # 或者直接放入背包（如果有）？目前 Avatar 没有通用背包，通常直接修习
                        # 简化逻辑：直接修习
                        av.technique = loot
                    
                    # 记录事件
                    event_content = t("{name} found a treasure {loot} in {domain}!", name=av.name, loot=loot_name, domain=domain.name)
                    event = Event(
                        month_stamp,
                        event_content,
                        related_avatars=[av.id]
                    )
                    events.append(event)
                    
                    event_texts.append(event_content)
                    related_avatars_set.add(av)

            if not triggered_event:
                # 既没死也没拿东西，一无所获
                empty_handed_avatars.append(av)
        
        # 处理一无所获的人
        if empty_handed_avatars:
            empty_names = ", ".join([av.name for av in empty_handed_avatars])
            empty_event_content = t("{names} returned from {domain} empty-handed.", names=empty_names, domain=domain.name)
            
            # 作为一个聚合事件添加（避免刷屏）
            # 或者仅添加到 event_texts 用于生成故事，不作为独立 Event 显示？
            # 按照需求 "显示所有人的名字 + 均一无所获的文字"，应该也是一条 Log
            events.append(Event(
                month_stamp,
                empty_event_content,
                related_avatars=[av.id for av in empty_handed_avatars]
            ))
            event_texts.append(empty_event_content)
            # 也要加入 related_avatars_set 以便 story teller 知道他们参与了
            related_avatars_set.update(empty_handed_avatars)


        # 3. 生成故事 (StoryTeller)
        # 只有当发生了一些值得记录的事情（死人、或者有人获得重宝）才生成故事，避免刷屏
        if event_texts:
            story_event = await self._generate_story(world, domain, event_texts, list(related_avatars_set))
            if story_event:
                events.append(story_event)
                
        return events

    async def _generate_story(
        self, 
        world: "World", 
        domain: DomainConfig, 
        event_texts: List[str], 
        related_avatars: List["Avatar"]
    ) -> Optional[Event]:
        """调用 LLM 生成秘境探索故事"""
        
        if not related_avatars:
            return None
            
        # 1. 场景描述
        gathering_info = t(
            "Event: Hidden Domain Opening\nName: {name}\nDescription: {desc}",
            name=domain.name, desc=domain.desc
        )
        
        # 2. 事件列表
        events_str = "\n".join(event_texts)
        
        # 3. 角色信息 (可选，增加故事细节)
        details_list = []
        details_list.append(t("\n【Related Avatars Information】"))
        for av in related_avatars:
            info = av.get_info(detailed=True)
            details_list.append(f"- {av.name}: {info}")
        details_text = "\n".join(details_list)

        # 4. 调用 StoryTeller
        from src.classes.story_teller import StoryTeller
        story = await StoryTeller.tell_gathering_story(
            gathering_info=gathering_info,
            events_text=events_str,
            details_text=details_text,
            related_avatars=related_avatars,
            prompt=self.get_story_prompt() 
        )
        
        return Event(
            month_stamp=world.month_stamp,
            content=story,
            related_avatars=[av.id for av in related_avatars],
            is_major=True
        )
