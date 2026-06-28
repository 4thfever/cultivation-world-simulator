# 阵法系统 Spec

本文档记录阵法系统的第一版设计目标与落地约束。阵法系统应与现有动作、辅助装备、region-first 地图、effect、存档结构协同，但不应把区域效果强行塞进角色临时效果链。

## 目标

阵法是一种通过阵盘在当前区域布置的限时区域效果：

1. 阵盘是一种辅助装备。
2. 装备阵盘后，角色可以执行“布置阵法”动作。
3. 布阵只能作用于角色当前所在的 region，不支持远程布阵，也不绑定 tile。
4. 阵法绑定 region，不绑定 avatar。
5. 一个 region 同时只能存在一个阵法。
6. 新布置的阵法会自动替换该 region 原有阵法。
7. 阵法消耗灵石，不消耗阵盘。
8. 阵法不设置失败率，满足条件则成功。
9. 阵法持续一段时间，到期自动结束。
10. 第一版不做撤回、破阵、维护费、阵眼争夺、多阵法叠加或城市经济阵法。

阵法和蛊在结构上相似，但目标不同：

| 系统 | 工具 | 动作 | 目标 | 状态承载 | 玩法定位 |
|---|---|---|---|---|---|
| 蛊 | 蛊具 auxiliary | 下蛊 | avatar | avatar temporary effects | 暗中影响单人 |
| 阵法 | 阵盘 auxiliary | 布置阵法 | 当前 region | map/region formation state | 改造一片区域 |

## 设计原则

### 1. 阵法是区域光环，不是角色临时效果

阵法没有单个 avatar 受体，因此不应写入：

```python
avatar.temporary_effects
```

角色只有位于该 region 内，并执行与阵法相关的动作或参与该 region 内的战斗时，才临时享受阵法效果。

建议由 `src/systems/formation.py` 提供统一查询函数，例如：

```python
get_active_region_formation(world, region_id)
get_active_region_formation_effects(world, region_id)
get_current_region_formation_effects(avatar)
```

具体动作和系统在结算时读取当前 region 的 active formation effects，并与角色自身 `avatar.effects` 叠加计算。

### 2. 只给当前所在地布阵

“布置阵法”动作不需要 region 参数。动作直接读取：

```python
region = avatar.tile.region
```

这能保持动作简单，也符合“阵师亲临地脉布阵”的玩法语义。

### 3. 覆盖旧阵，不做撤回

每个 region 同时最多一个 active formation。若当前 region 已有阵法，新阵法直接覆盖旧阵法。

覆盖不返还灵石，也不保留旧阵剩余时间。

### 4. 动作说明使用说明文

阵法动作的描述用于玩家和 LLM AI 理解行为边界，应保持纯说明文，不写文学性渲染。

推荐说明：

```text
在当前区域布置一个阵法。需要装备阵盘并消耗灵石。每个区域同时只能存在一个阵法，新阵法会替换该区域原有阵法。聚灵阵提升吐纳收益，适合修炼区域和宗门总部。护山阵提升阵内战斗能力，适合宗门总部和修炼区域。疗愈阵提升疗伤恢复，适合宗门总部、修炼区域和城市。清心阵提升闭关和突破稳定性，适合修炼区域和宗门总部。寻脉阵提升挖矿收益，适合有矿脉的普通区域。丰木阵提升采集收益，适合有植物的普通区域。驱兽阵提升狩猎收益，适合有动物的普通区域。
```

小故事由故事模块自行发挥，阵法动作本身只负责基础事实事件。

## 数据模型

第一版建议在运行时 `Map` 上维护 region formation 字典：

```python
world.map.region_formations = {
    301: {
        "formation_type": "spirit_gathering",
        "caster_id": "avatar_1",
        "disk_item_id": 2082,
        "start_month": 120,
        "duration": 28,
        "effects": {
            "extra_respire_exp_multiplier": 0.18
        },
        "cost": 220
    }
}
```

字段说明：

1. `formation_type`：阵法类型 key。
2. `caster_id`：布阵角色 ID，只保存 ID，不保存对象引用。
3. `disk_item_id`：使用的阵盘物品 ID。
4. `start_month`：布阵开始月份。
5. `duration`：持续月份。
6. `effects`：该阵法提供的区域效果，使用 JSON 基础类型。
7. `cost`：本次布阵消耗灵石，主要用于展示和调试。

过期判断：

```python
current_month >= start_month + duration
```

过期后从 `region_formations` 删除。

## 阵盘

阵盘作为 `Auxiliary` 配置。阵盘本身提供动作权限：

```text
{legal_actions: ['SetFormation']}
```

建议阵盘等级：

| 阵盘 | 对应境界 | 基础持续 | 基础成本 | 说明 |
|---|---|---:|---:|---|
| 下品阵盘 | 练气 | 18 个月 | 80 | 入门阵盘 |
| 中品阵盘 | 筑基 | 24 个月 | 200 | 稳定阵盘 |
| 上品阵盘 | 金丹 | 30 个月 | 600 | 高阶阵盘 |
| 极品阵盘 | 元婴 | 36 个月 | 1800 | 顶级阵盘 |

阵盘不作为一次性消耗品。布阵只消耗灵石。

## Persona

第一版新增两个和阵法相关的 persona：

### 阵师

阵师是较稀有的布阵专长 persona。

建议效果：

```python
{
    "extra_formation_power": 0.15,
    "extra_formation_duration_months": 6,
    "formation_cost_reduction": 0.10
}
```

### 阵仙

阵仙是更稀有、更强效的布阵专长 persona。

建议效果：

```python
{
    "extra_formation_power": 0.35,
    "extra_formation_duration_months": 12,
    "formation_cost_reduction": 0.25
}
```

计算方式：

```text
final_effect = base_effect * (1 + extra_formation_power)
duration = base_duration + extra_formation_duration_months + random_delta
cost = base_cost * (1 - formation_cost_reduction)
```

若角色同时拥有多个相关 persona，按现有 effect 合并规则累加即可。由于阵仙应足够稀有，第一版不需要额外做互斥逻辑。

## 阵法类型

第一版包含以下阵法。不包含聚市阵和血煞阵。

| 阵法 key | 中文名 | 效果 | 允许 region |
|---|---|---|---|
| `spirit_gathering` | 聚灵阵 | 提升吐纳收益 | 修炼区域、宗门总部 |
| `mountain_guard` | 护山阵 | 提升阵内战斗能力 | 宗门总部、修炼区域 |
| `healing` | 疗愈阵 | 提升疗伤恢复 | 宗门总部、修炼区域、城市 |
| `clarity` | 清心阵 | 提升闭关和突破稳定性 | 修炼区域、宗门总部 |
| `vein_seeking` | 寻脉阵 | 提升挖矿收益 | 有矿脉的普通区域 |
| `wood_growth` | 丰木阵 | 提升采集收益 | 有植物的普通区域 |
| `beast_driving` | 驱兽阵 | 提升狩猎收益 | 有动物的普通区域 |

### 效果建议

聚灵阵：

```python
{"extra_respire_exp_multiplier": 0.10 / 0.18 / 0.28 / 0.40}
```

护山阵：

```python
{"extra_battle_strength_points": 1 / 2 / 4 / 7}
```

疗愈阵：

```python
{"extra_hp_recovery_rate": 0.20 / 0.35 / 0.55 / 0.80}
```

清心阵：

```python
{
    "extra_breakthrough_success_rate": 0.03 / 0.05 / 0.08 / 0.12,
    "extra_retreat_success_rate": 0.03 / 0.05 / 0.08 / 0.12
}
```

寻脉阵：

```python
{"extra_mine_materials": 1 / 1 / 2 / 3}
```

丰木阵：

```python
{"extra_harvest_materials": 1 / 1 / 2 / 3}
```

驱兽阵：

```python
{"extra_hunt_materials": 1 / 1 / 2 / 3}
```

数值顺序对应下品、中品、上品、极品阵盘。最终数值再受 `extra_formation_power` 加成。

## 成本与持续时间

基础成本由阵盘等级决定，再乘阵法类型倍率和 region 类型倍率。

阵法类型倍率：

| 阵法 | 倍率 |
|---|---:|
| 聚灵阵 | 1.2 |
| 护山阵 | 1.4 |
| 疗愈阵 | 1.0 |
| 清心阵 | 1.3 |
| 寻脉阵 | 0.8 |
| 丰木阵 | 0.8 |
| 驱兽阵 | 0.8 |

region 类型倍率：

| region | 倍率 |
|---|---:|
| 普通区域 | 1.0 |
| 城市 | 1.1 |
| 修炼区域 | 1.3 |
| 宗门总部 | 1.5 |

最终成本：

```text
cost = disk_base_cost * formation_multiplier * region_multiplier * (1 - formation_cost_reduction)
```

最终持续时间：

```text
duration = disk_base_duration + extra_formation_duration_months + random_delta
```

`random_delta` 建议控制在小范围，例如 `-3` 到 `+6` 个月，保持结果可预期。

## 动作设计

新增动作：

```python
SetFormation
```

中文名：

```text
布置阵法
```

动作参数：

```python
PARAMS = {
    "formation_type": "FormationType",
}
```

参数来源：

```python
PARAM_OPTION_SOURCES = {
    "formation_type": ParamOptionSource.AVAILABLE_FORMATION_TYPE,
}
```

`AVAILABLE_FORMATION_TYPE` 应只返回当前 region 可布置的阵法，避免 LLM AI 选择明显无效的阵法。

`can_possibly_start` 建议检查：

1. 角色装备了阵盘。
2. 角色当前在有效 region 内。
3. 当前 region 至少有一种可布置阵法。
4. 角色拥有布置任意可用阵法的最低灵石。

`can_start(formation_type)` 建议检查：

1. 已装备阵盘。
2. `formation_type` 合法。
3. 当前 region 允许该阵法。
4. 角色灵石足够。

`_execute` 建议流程：

1. 计算成本。
2. 扣除灵石。
3. 构造 formation 记录。
4. 覆盖写入 `world.map.region_formations[region.id]`。

`finish` 基础事件建议使用说明文：

```text
{avatar}在{region}布置了{formation}。
```

若覆盖旧阵：

```text
{avatar}在{region}布置了{formation}，该区域原有阵法已被替换。
```

## 结算接入点

阵法效果在具体结算点读取，不进入 avatar 自身 effect 主链。

建议接入：

1. `src/classes/action/respire.py`
   - 聚灵阵：吐纳经验倍率。
2. `src/classes/action/self_heal.py`
   - 疗愈阵：疗伤恢复倍率。
3. `src/systems/battle.py`
   - 护山阵：阵内战斗力加成。
   - 第一版可只在双方位于同一 region 时生效。
4. `src/classes/action/breakthrough.py`
   - 清心阵：突破成功率加成。
5. `src/classes/action/retreat.py`
   - 清心阵：闭关成功率加成。
6. `src/classes/action/mine.py`
   - 寻脉阵：挖矿收益。
7. `src/classes/action/harvest.py`
   - 丰木阵：采集收益。
8. `src/classes/action/hunt.py`
   - 驱兽阵：狩猎收益。

后续若驱兽阵需要影响捕捉，可再接入 `src/classes/action/catch.py`，但第一版不要求。

## 存档

阵法是世界状态，应随存档保存。

推荐保存到 map/world 相关状态中：

```json
{
  "region_formations": {
    "301": {
      "formation_type": "spirit_gathering",
      "caster_id": "avatar_1",
      "disk_item_id": 2082,
      "start_month": 120,
      "duration": 28,
      "effects": {
        "extra_respire_exp_multiplier": 0.18
      },
      "cost": 220
    }
  }
}
```

加载时按当前模型恢复为 `dict[int, dict]` 即可，不需要恢复为复杂对象。

遵守存档约束：

1. 只保存 JSON 基础类型。
2. 跨对象引用只保存 ID。
3. 不保存 avatar、region、auxiliary 对象引用。

## 展示

第一版展示应保持克制：

1. region 详情显示当前阵法名称、剩余时间、效果说明。
2. 地图 region tooltip 可显示当前阵法简述。
3. 角色动作列表出现“布置阵法”动作。
4. 不新增专门阵法管理页面。

因为第一版没有撤回、破阵、维护和多阵法叠加，region 详情展示已足够。

## 测试建议

后端测试至少覆盖：

1. 未装备阵盘时不能布阵。
2. 装备阵盘后出现 `SetFormation` 权限。
3. `param_options` 只返回当前 region 可布置的阵法。
4. 当前 region 无可用阵法时 `can_possibly_start` 为 false。
5. 灵石不足时不能布阵。
6. 布阵成功后扣除灵石并写入 `region_formations`。
7. 同一 region 新阵法覆盖旧阵法。
8. 阵法到期自动删除。
9. 存档保存并恢复 `region_formations`。
10. 聚灵阵影响吐纳收益。
11. 护山阵影响阵内战斗力。
12. 疗愈阵影响疗伤恢复。
13. 清心阵影响闭关或突破成功率。
14. 寻脉阵、丰木阵、驱兽阵分别影响对应采集动作。
15. 阵师和阵仙影响阵法强度、持续时间和成本。

前端测试按实际展示范围补充：

1. region detail 能展示当前阵法。
2. 首次打开 region detail 时可加载阵法信息。
3. 类型定义和 mapper 不使用 `any` 扩散。

## 暂不包含

第一版明确不包含：

1. 聚市阵。
2. 血煞阵。
3. 远程布阵。
4. 布阵失败率。
5. 撤回阵法。
6. 破阵动作。
7. 阵法维护费。
8. 多阵法叠加。
9. tile 级阵法。
10. 阵法对不在该 region 的角色生效。
11. 专门阵法管理 UI。

