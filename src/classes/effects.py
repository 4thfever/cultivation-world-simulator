"""
Effects 效果系统
================

本文件定义了游戏中所有合法的 effect 字段。
Effects 通过角色的 avatar.effects 属性合并并生效。

Effect 来源：
- 宗门 (sect)
- 功法 (technique)
- 灵根 (root)
- 特质 (persona)
- 兵器和辅助装备 (weapon, auxiliary)
"""

# =============================================================================
# Effect 常量定义
# =============================================================================

# --- 战斗相关 ---
EXTRA_BATTLE_STRENGTH_POINTS = "extra_battle_strength_points"
"""
额外战斗力点数
类型: int
结算: src/classes/battle.py
说明: 直接增加角色的战斗力数值
"""

EXTRA_MAX_HP = "extra_max_hp"
"""
额外最大生命值
类型: int
结算: src/classes/avatar.py (__post_init__)
说明: 增加角色的最大生命值上限
"""

EXTRA_MAX_MP = "extra_max_mp"
"""
额外最大灵力值
类型: int
结算: src/classes/avatar.py (__post_init__)
说明: 增加角色的最大灵力值上限
"""

EXTRA_OBSERVATION_RADIUS = "extra_observation_radius"
"""
额外观察半径
类型: int
结算: [待实现]
说明: 增加角色的观察范围
"""

# --- 修炼相关 ---
EXTRA_CULTIVATE_EXP = "extra_cultivate_exp"
"""
额外修炼经验
类型: int
结算: src/classes/action/cultivate.py
说明: 每次修炼时额外获得的经验值
"""

CULTIVATE_DURATION_REDUCTION = "cultivate_duration_reduction"
"""
修炼时长缩减
类型: float (范围: 0.0 ~ 0.9，建议不超过0.5)
结算: src/classes/action/cultivate.py
说明: 修炼动作的时长缩减比例（如 0.2 表示缩减20%，10个月变为8个月）
"""

EXTRA_BREAKTHROUGH_SUCCESS_RATE = "extra_breakthrough_success_rate"
"""
额外突破成功率
类型: float (范围: -1.0 ~ 1.0)
结算: src/classes/action/breakthrough.py
说明: 修改突破时的成功率，可以为负值降低成功率
"""

# --- 双修相关 ---
EXTRA_DUAL_CULTIVATION_EXP = "extra_dual_cultivation_exp"
"""
额外双修经验
类型: int
结算: src/classes/mutual_action/dual_cultivation.py
说明: 双修时发起者额外获得的经验值
"""

# --- 采集相关 ---
EXTRA_HARVEST_ITEMS = "extra_harvest_items"
"""
额外采集物品数量
类型: int
结算: src/classes/action/harvest.py
说明: 采集植物时额外获得的物品数量
"""

EXTRA_HUNT_ITEMS = "extra_hunt_items"
"""
额外狩猎物品数量
类型: int
结算: src/classes/action/hunt.py
说明: 狩猎动物时额外获得的物品数量
"""

# --- 移动相关 ---
EXTRA_MOVE_STEP = "extra_move_step"
"""
额外移动步数
类型: int
结算: [待实现]
说明: 每次移动时可以多移动的步数
"""

# --- 捕捉相关 ---
EXTRA_CATCH_SUCCESS_RATE = "extra_catch_success_rate"
"""
额外捕捉成功率
类型: float (范围: 0.0 ~ 1.0)
结算: src/classes/action/catch.py
说明: 捕捉灵兽时增加的成功率
"""

# --- 逃跑相关 ---
EXTRA_ESCAPE_SUCCESS_RATE = "extra_escape_success_rate"
"""
额外逃跑成功率
类型: float (范围: 0.0 ~ 1.0)
结算: src/classes/battle.py
说明: 从对方身边逃离时增加的成功率
"""

# --- 奇遇相关 ---
EXTRA_FORTUNE_PROBABILITY = "extra_fortune_probability"
"""
额外奇遇概率
类型: float (范围: 0.0 ~ 1.0)
结算: src/classes/fortune.py
说明: 增加触发奇遇事件的概率
"""

# --- 兵器相关 ---
EXTRA_WEAPON_PROFICIENCY_GAIN = "extra_weapon_proficiency_gain"
"""
额外兵器熟练度增长速度
类型: float (倍率，如 0.5 表示增加50%，1.0 表示翻倍)
结算: src/classes/action/nurture_weapon.py 和战斗相关代码
说明: 提升兵器熟练度增长速度的倍率
"""

EXTRA_WEAPON_UPGRADE_CHANCE = "extra_weapon_upgrade_chance"
"""
额外兵器升华概率
类型: float (范围: 0.0 ~ 1.0)
结算: src/classes/action/nurture_weapon.py
说明: 温养兵器时升华为宝物的概率提升
"""

# --- 生存与恢复相关 ---
EXTRA_MAX_LIFESPAN = "extra_max_lifespan"
"""
额外最大寿元
类型: int (年)
结算: src/classes/age.py
说明: 增加角色的最大寿命上限（年）
"""

EXTRA_HP_RECOVERY_RATE = "extra_hp_recovery_rate"
"""
额外HP恢复速率
类型: float (倍率，如 0.5 表示增加50%，1.0 表示翻倍)
结算: src/classes/action/self_heal.py
说明: 疗伤时的HP恢复效率倍率
"""

DAMAGE_REDUCTION = "damage_reduction"
"""
伤害减免
类型: float (范围: 0.0 ~ 1.0)
结算: src/classes/battle.py
说明: 受到伤害的减免比例（如 0.1 表示减少10%伤害）
"""

REALM_SUPPRESSION_BONUS = "realm_suppression_bonus"
"""
境界压制加成
类型: float (倍率，如 0.15 表示每高一个大境界获得15%战斗力加成)
结算: src/classes/battle.py
说明: 当角色境界高于对手时，每高一个大境界额外增加战斗力点数
"""

# --- 经济相关 ---
EXTRA_ITEM_SELL_PRICE_MULTIPLIER = "extra_item_sell_price_multiplier"
"""
额外物品出售价格倍率
类型: float (倍率，如 0.2 表示增加20%，1.0 表示翻倍)
结算: src/classes/action/sold.py
说明: 出售物品时的价格倍率
"""

EXTRA_PLUNDER_MULTIPLIER = "extra_plunder_multiplier"
"""
额外搜刮收益倍率
类型: float (倍率，如 0.5 表示增加50%，1.0 表示翻倍)
结算: src/classes/action/plunder_mortals.py
说明: 搜刮凡人时的灵石收益倍率
"""

# --- 特殊权限 ---
LEGAL_ACTIONS = "legal_actions"
"""
合法动作列表
类型: list[str]
结算: 各个 action 的权限检查
说明: 允许角色执行的特殊动作列表
可用值:
  - "DualCultivation": 双修（合欢宗专属）
  - "DevourMortals": 吞噬凡人（邪道法宝）
"""

# =============================================================================
# CSV 配置格式规范
# =============================================================================

"""
CSV 中 effects 列的写法（支持宽松JSON格式）:

基础格式（推荐无引号key）:
  {extra_battle_strength_points: 3}
  {extra_battle_strength_points: 2, extra_max_hp: 50}
  {legal_actions: ['DevourMortals']}

条件effect（when字段）:
  [{when: 'avatar.weapon.type == WeaponType.SWORD', extra_battle_strength_points: 3}]
  可访问: avatar, WeaponType, EquipmentGrade, Alignment

动态值（字符串表达式会被eval）:
  {extra_battle_strength_points: 'avatar.weapon.special_data.get("souls", 0) * 0.1'}

注意: CSV中包含逗号的effects值需要用双引号包裹，避免被误认为列分隔符
"""

# =============================================================================
# Effect 合并规则
# =============================================================================

"""
Effects 通过 src/classes/effect.py 中的 _merge_effects() 函数合并。

合并规则:
1. 列表类型 (如 legal_actions): 取并集（去重）
2. 数值类型 (如 extra_*): 累加
3. 其他类型: 后者覆盖前者
4. 动态表达式 (字符串形式): 在 Avatar.effects property 中 eval 计算

合并顺序（从低到高优先级）:
1. 宗门 (sect)
2. 功法 (technique)
3. 灵根 (root)
4. 特质 (persona) - 遍历所有 personas
5. 兵器和辅助装备 (weapon, auxiliary)

最终结果通过 Avatar.effects 属性获取（实时计算）。
"""

# =============================================================================
# 所有合法 Effect 字段清单
# =============================================================================

ALL_EFFECTS = [
    # 战斗相关
    "extra_battle_strength_points",      # int - 额外战斗力
    "extra_max_hp",                      # int - 额外最大生命值
    "extra_max_mp",                      # int - 额外最大灵力值
    "extra_observation_radius",          # int - 额外观察半径
    "damage_reduction",                  # float - 伤害减免
    "realm_suppression_bonus",           # float - 境界压制加成
    
    # 修炼相关
    "extra_cultivate_exp",               # int - 额外修炼经验
    "cultivate_duration_reduction",      # float - 修炼时长缩减
    "extra_breakthrough_success_rate",   # float - 额外突破成功率
    
    # 双修相关
    "extra_dual_cultivation_exp",        # int - 额外双修经验
    
    # 采集相关
    "extra_harvest_items",               # int - 额外采集物品数量
    "extra_hunt_items",                  # int - 额外狩猎物品数量
    
    # 移动相关
    "extra_move_step",                   # int - 额外移动步数
    
    # 捕捉相关
    "extra_catch_success_rate",          # float - 额外捕捉成功率
    
    # 逃跑相关
    "extra_escape_success_rate",         # float - 额外逃跑成功率
    
    # 奇遇相关
    "extra_fortune_probability",         # float - 额外奇遇概率
    
    # 兵器相关
    "extra_weapon_proficiency_gain",     # float - 额外兵器熟练度增长倍率
    "extra_weapon_upgrade_chance",       # float - 额外兵器升华概率
    
    # 生存与恢复相关
    "extra_max_lifespan",                # int - 额外最大寿元（年）
    "extra_hp_recovery_rate",            # float - 额外HP恢复速率倍率
    
    # 经济相关
    "extra_item_sell_price_multiplier",  # float - 额外物品出售价格倍率
    "extra_plunder_multiplier",          # float - 额外搜刮收益倍率
    
    # 特殊权限
    "legal_actions",                     # list[str] - 合法动作列表
]
