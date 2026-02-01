"""
Avatar存档序列化Mixin

将Avatar的序列化逻辑从avatar.py分离出来，保持核心类的清晰性。

存档策略：
- 引用对象（Technique, Material等）：保存id，加载时从全局字典获取
- relations：转换为dict[str, str]（avatar_id -> relation_value）
- materials：转换为dict[int, int]（material_id -> quantity）
- current_action：保存动作类名和参数
- weapon/auxiliary：需要深拷贝（因为special_data是实例特有的）
"""


class AvatarSaveMixin:
    """Avatar存档序列化Mixin
    
    提供to_save_dict方法，将Avatar转换为可JSON序列化的字典
    """
    
    def to_save_dict(self) -> dict:
        """转换为可序列化的字典（用于存档）
        
        Returns:
            包含Avatar完整状态的字典，可直接JSON序列化
        """
        # 序列化relations: dict[Avatar, Relation] -> dict[str, str]
        relations_dict = {
            other.id: relation.value
            for other, relation in self.relations.items()
        }
        
        # 序列化materials: dict[Material, int] -> dict[int, int]
        materials_dict = {
            material.id: quantity
            for material, quantity in self.materials.items()
        }
        
        # 序列化current_action
        current_action_dict = None
        if self.current_action is not None:
            current_action_dict = {
                "action_name": self.current_action.action.__class__.__name__,
                "params": self.current_action.params,
                "status": self.current_action.status,
                "state": self.current_action.action.get_save_data()
            }
        
        # 序列化planned_actions
        planned_actions_list = [plan.to_dict() for plan in self.planned_actions]
        
        # 序列化spirit_animal
        spirit_animal_dict = None
        if self.spirit_animal is not None:
            spirit_animal_dict = {
                "name": self.spirit_animal.name,
                "realm": self.spirit_animal.realm.name
            }
        
        return {
            # 基础信息
            "id": self.id,
            "name": self.name,
            "birth_month_stamp": int(self.birth_month_stamp),
            "gender": self.gender.value,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            
            # 修炼相关
            "age": self.age.to_dict(),
            "cultivation_progress": self.cultivation_progress.to_dict(),
            "root": self.root.name,
            "technique_id": self.technique.id if self.technique else None,
            "hp": self.hp.to_dict(),
            
            # 物品与资源
            "magic_stone": self.magic_stone.value,
            "materials": materials_dict,
            "weapon_id": self.weapon.id if self.weapon else None,
            "weapon_special_data": self.weapon.special_data if self.weapon else {},
            "weapon_proficiency": self.weapon_proficiency,
            "auxiliary_id": self.auxiliary.id if self.auxiliary else None,
            "auxiliary_special_data": self.auxiliary.special_data if self.auxiliary else {},
            "spirit_animal": spirit_animal_dict,
            
            # 社交与状态
            "relations": relations_dict,
            "sect_id": self.sect.id if self.sect else None,
            "sect_rank": self.sect_rank.value if self.sect_rank else None,
            "alignment": self.alignment.name if self.alignment else None,
            "persona_ids": [p.id for p in self.personas] if self.personas else [],
            "appearance": self.appearance.level,
            "nickname": self.nickname.to_dict() if self.nickname else None,
            "emotion": self.emotion.value,
            "is_dead": self.is_dead,
            "death_info": self.death_info,
            
            # 行动与AI
            "current_action": current_action_dict,
            "planned_actions": planned_actions_list,
            "thinking": self.thinking,
            "short_term_objective": self.short_term_objective,
            "long_term_objective": {
                "content": self.long_term_objective.content,
                "origin": self.long_term_objective.origin,
                "set_year": self.long_term_objective.set_year
            } if self.long_term_objective else None,
            "_action_cd_last_months": self._action_cd_last_months,
            "known_regions": list(self.known_regions),

            # 状态追踪
            "metrics_history": [
                metrics.to_save_dict()
                for metrics in self.metrics_history
            ] if self.enable_metrics_tracking else [],
            "enable_metrics_tracking": self.enable_metrics_tracking,

            # 丹药
            "elixirs": [
                {
                    "id": consumed.elixir.id,
                    "time": consumed.consume_time
                }
                for consumed in self.elixirs
            ],
            "temporary_effects": self.temporary_effects,
        }

