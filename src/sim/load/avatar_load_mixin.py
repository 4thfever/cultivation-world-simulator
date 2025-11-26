"""
Avatar读档反序列化Mixin

将Avatar的反序列化逻辑从avatar.py分离出来。

读档策略：
- 两阶段加载：先加载所有Avatar（relations留空），再重建relations网络
- 引用对象：通过id从全局字典获取（如techniques_by_id）
- weapon/auxiliary：深拷贝后恢复special_data
- 错误容错：缺失的引用对象会跳过而不是崩溃
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.world import World


class AvatarLoadMixin:
    """Avatar读档反序列化Mixin
    
    提供from_save_dict类方法，从字典重建Avatar对象
    """
    
    @classmethod
    def from_save_dict(cls, data: dict, world: "World") -> "AvatarLoadMixin":
        """从字典重建Avatar（用于读档）
        
        注意：relations需要在所有Avatar加载完成后单独重建
        
        Args:
            data: 存档数据字典
            world: 世界对象引用
            
        Returns:
            重建的Avatar对象（relations为空，需要外部第二阶段填充）
        """
        from src.classes.avatar import Gender
        from src.classes.calendar import MonthStamp
        from src.classes.cultivation import Realm, CultivationProgress
        from src.classes.age import Age
        from src.classes.hp_and_mp import HP
        from src.classes.technique import techniques_by_id
        from src.classes.item import items_by_id
        from src.classes.weapon import weapons_by_id
        from src.classes.auxiliary import auxiliaries_by_id
        from src.classes.sect import sects_by_id
        from src.classes.sect_ranks import SectRank
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.classes.persona import personas_by_id
        from src.classes.appearance import get_appearance_by_level
        from src.classes.magic_stone import MagicStone
        from src.classes.action_runtime import ActionPlan
        
        # 重建基本对象
        gender = Gender(data["gender"])
        birth_month_stamp = MonthStamp(data["birth_month_stamp"])
        
        # 重建修炼进度
        cultivation_progress = CultivationProgress.from_dict(data["cultivation_progress"])
        realm = cultivation_progress.realm
        
        # 重建age
        age = Age.from_dict(data["age"], realm)
        
        # 创建Avatar（不完整，需要后续填充）
        avatar = cls(
            world=world,
            name=data["name"],
            id=data["id"],
            birth_month_stamp=birth_month_stamp,
            age=age,
            gender=gender,
            cultivation_progress=cultivation_progress,
            pos_x=data["pos_x"],
            pos_y=data["pos_y"],
        )
        
        # 设置灵根
        avatar.root = Root[data["root"]]
        
        # 设置功法
        technique_id = data.get("technique_id")
        if technique_id is not None:
            avatar.technique = techniques_by_id.get(technique_id)
        
        # 设置HP
        avatar.hp = HP.from_dict(data["hp"])
        
        # 设置物品与资源
        avatar.magic_stone = MagicStone(data.get("magic_stone", 0))
        
        # 重建items
        items_dict = data.get("items", {})
        avatar.items = {}
        for item_id_str, quantity in items_dict.items():
            item_id = int(item_id_str)
            if item_id in items_by_id:
                avatar.items[items_by_id[item_id]] = quantity
        
        # 重建weapon（深拷贝因为special_data是实例特有的）
        weapon_id = data.get("weapon_id")
        if weapon_id is not None and weapon_id in weapons_by_id:
            import copy
            avatar.weapon = copy.deepcopy(weapons_by_id[weapon_id])
            avatar.weapon.special_data = data.get("weapon_special_data", {})
        
        # 恢复兵器熟练度
        avatar.weapon_proficiency = float(data.get("weapon_proficiency", 0.0))
        
        # 重建auxiliary（深拷贝因为special_data是实例特有的）
        auxiliary_id = data.get("auxiliary_id")
        if auxiliary_id is not None and auxiliary_id in auxiliaries_by_id:
            import copy
            avatar.auxiliary = copy.deepcopy(auxiliaries_by_id[auxiliary_id])
            avatar.auxiliary.special_data = data.get("auxiliary_special_data", {})
        
        # 重建spirit_animal
        spirit_animal_data = data.get("spirit_animal")
        if spirit_animal_data is not None:
            from src.classes.spirit_animal import SpiritAnimal
            spirit_realm = Realm[spirit_animal_data["realm"]]
            avatar.spirit_animal = SpiritAnimal(
                name=spirit_animal_data["name"],
                realm=spirit_realm
            )
        
        # 设置社交与状态
        sect_id = data.get("sect_id")
        if sect_id is not None:
            avatar.sect = sects_by_id.get(sect_id)
        
        sect_rank_value = data.get("sect_rank")
        if sect_rank_value is not None:
            avatar.sect_rank = SectRank(sect_rank_value)
        
        alignment_name = data.get("alignment")
        if alignment_name is not None:
            avatar.alignment = Alignment[alignment_name]
        
        # 重建personas
        persona_ids = data.get("persona_ids", [])
        avatar.personas = [personas_by_id[pid] for pid in persona_ids if pid in personas_by_id]
        
        # 设置外貌（通过level获取完整的Appearance对象）
        avatar.appearance = get_appearance_by_level(data.get("appearance", 5))

        # 恢复绰号
        from src.classes.nickname_data import Nickname
        avatar.nickname = Nickname.from_dict(data.get("nickname"))
        
        # 设置行动与AI
        avatar.thinking = data.get("thinking", "")
        avatar.short_term_objective = data.get("short_term_objective", "")
        avatar._action_cd_last_months = data.get("_action_cd_last_months", {})
        
        # 加载长期目标
        long_term_objective_data = data.get("long_term_objective")
        if long_term_objective_data:
            from src.classes.long_term_objective import LongTermObjective
            avatar.long_term_objective = LongTermObjective(
                content=long_term_objective_data.get("content", ""),
                origin=long_term_objective_data.get("origin", "llm"),
                set_year=long_term_objective_data.get("set_year", 100)
            )
        else:
            avatar.long_term_objective = None
        
        # 重建planned_actions
        planned_actions_data = data.get("planned_actions", [])
        avatar.planned_actions = [ActionPlan.from_dict(plan_data) for plan_data in planned_actions_data]
        
        # 重建current_action（如果有）
        current_action_data = data.get("current_action")
        if current_action_data is not None:
            try:
                action = avatar.create_action(current_action_data["action_name"])
                from src.classes.action_runtime import ActionInstance
                avatar.current_action = ActionInstance(
                    action=action,
                    params=current_action_data["params"],
                    status=current_action_data["status"]
                )
            except Exception:
                # 如果动作无法重建，跳过（容错）
                avatar.current_action = None
        
        # relations需要在外部单独重建（因为需要所有avatar都加载完成）
        avatar.relations = {}
        
        # 加载完成后重新计算effects（确保数值正确）
        avatar.recalc_effects()
        
        return avatar

