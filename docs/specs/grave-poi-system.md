# 墓碑与 POI 系统 Spec

本文档描述“修士死亡后生成墓碑”以及由此引出的点位兴趣点（Point of Interest, POI）系统设计。

当前状态：待实现设计。本文档不是已落地系统说明。实现时应优先遵守本 spec，并在落地后把“代码地图”和测试命令补齐为真实入口。

## 背景

现有地图系统以 region 为主语义，region 代表一个区域，占据多个 tile；地图上当前可点击对象主要是 region 与存活角色。

墓碑与 region 不同：

1. 墓碑绑定具体坐标点 `x/y`，不是绑定 region。
2. 任意地点死亡都应留下墓碑，包括荒野、无 region tile、城市、洞府、宗门、普通野外。
3. 墓碑有运行时生命周期，会过期、被发现、被掘墓、被挖空。
4. 墓碑只是第一种 POI；未来可能还有古碑、阵眼、临时秘境入口、遗落法器、任务线索等。

因此不应把墓碑做成：

1. 死者 Avatar 的另一种地图表现。
2. 某个 region 的附属字段。
3. 只服务墓碑的一次性列表。

应建立通用 POI 系统，墓碑作为 `grave` 类型接入。

## 目标

1. 修士角色死亡后，在死亡坐标生成墓碑 POI。
2. 墓碑保留 50 年；对应死者信息也在 50 年后消失。
3. 墓碑可以点击，点击展示对应死者信息与墓碑状态。
4. 墓碑中只可能保留死者死亡时仍持有的武器与辅助装备；功法不进入墓碑。
5. 若死者在战斗中被杀人夺宝，墓碑只保留夺宝后剩下的装备。
6. 知悉 POI 的角色可以执行移动到 POI 的动作。
7. 墓碑在角色交互范围内时必定被发现。
8. 角色可以掘墓；掘墓可能成功、失败、空手而归，甚至受伤。
9. 掘墓会扣少量气运；正派微微不愿意掘墓，反派不受行为倾向惩罚，但仍扣气运。
10. 第一阶段先完成墓碑图片资产，不接入运行时逻辑。

## 非目标

1. 第一版不做同 tile 多墓碑聚合展示。
2. 第一版墓碑不阻挡移动。
3. 第一版不做“亲友发现墓被掘后产生仇恨”等复杂社交后果。
4. 第一版不做墓碑作为地形、region overlay 或可占领对象。
5. 第一版不要求向前兼容旧存档；开发阶段以新结构清晰为先。
6. 第一版不做角色扮演模式下的视野隔离；上帝视角前端可展示当前有效 POI，角色行动参数只展示该角色已知 POI。

## Phase 规划

### Phase 1：墓碑图片资产

目标：建立墓碑图标资产，不接入后端和前端运行时。

产物：

1. 生成 3x3 墓碑图标预览图。
2. 人工挑选并切分为 9 个独立墓碑图标。
3. 放入前端资产目录，例如：

```text
web/src/assets/icons/pois/
  grave_01.png
  grave_02.png
  grave_03.png
  grave_04.png
  grave_05.png
  grave_06.png
  grave_07.png
  grave_08.png
  grave_09.png
  fallback_poi.png
```

4. 建立 POI 图标解析 helper，例如 `web/src/utils/poiIcons.ts`，但可以先不被运行时使用。
5. 墓碑图标风格应与现有物品 icon 协调：像素化、低细节、清晰轮廓、可在 32x32 与 64x64 下识别。

当前 image API 不可用时，先保存 prompt，由人工运行图片生成工具，再把结果贴回仓库处理。

推荐 prompt：

```text
Create a 3x3 sprite sheet of nine different tombstone icons for a pixel-art xianxia cultivation world game.

Style requirements:
- Pixel art game item icon style, matching small inventory icons.
- Each icon should be a separate square tile with a clean transparent or pure white background.
- Low detail, readable at 32x32 and 64x64.
- Ancient Chinese fantasy cultivation atmosphere.
- Weathered stone tombstones, small spirit marks, faint jade cracks, old talisman paper, subtle moss, carved runes, small incense ash, or a tiny spiritual glow.
- Somber but not horror-like.
- No skulls, no gore, no realistic corpse elements.
- Avoid modern cemetery shapes; use ancient stone stele forms, rough carved tablets, worn memorial stones.
- Keep silhouettes distinct across all nine variants.
- Palette: muted stone gray, dark ink lines, small accents of aged jade green, faded cinnabar red, or pale spiritual blue.
- Crisp pixel edges, no blur, no painterly rendering, no 3D, no photorealism.

Composition:
- A single 3 by 3 grid.
- Nine icons, evenly spaced.
- Each icon centered and fully visible.
- No text labels outside the icons.
- No UI frame, no decorative background scene.

Output:
- One square image containing the 3x3 sheet.
```

Negative prompt：

```text
photorealistic, high detail, 3D render, anime character, corpse, skull, blood, horror, modern graveyard, large background scene, blurry, soft gradients, vector logo, text, watermark
```

### Phase 2：POI 领域模型与存读档

目标：建立后端 POI 抽象、墓碑 POI、POIManager，并纳入存档。

不接前端地图渲染也可以，但应能在测试中创建、保存、读取、过期清理。

### Phase 3：死亡生成墓碑与 50 年清理

目标：所有死亡入口统一生成墓碑，并统一死者、墓碑生命周期。

### Phase 4：发现、移动到 POI 与 API

目标：角色能发现墓碑，行动参数能选择已知 POI，地图/detail API 能返回 POI 数据。

### Phase 5：前端点击与墓碑详情

目标：地图渲染墓碑，点击墓碑打开详情。

### Phase 6：掘墓动作

目标：实现掘墓、装备获取、失败/受伤、气运扣减、事件记录。

## 领域模型

### PointOfInterest 抽象

建议新增包：

```text
src/classes/poi/
  __init__.py
  poi.py
  grave.py
  manager.py
  serialization.py
```

基础抽象建议：

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PointOfInterest(ABC):
    id: str
    kind: str
    x: int
    y: int
    name: str
    desc: str = ""
    created_month: int = 0
    expires_month: int | None = None
    discovered_by: set[str] = field(default_factory=set)
    icon_key: str = ""
    is_clickable: bool = True

    @property
    def loc(self) -> tuple[int, int]:
        return self.x, self.y

    def is_expired(self, current_month: int) -> bool:
        return self.expires_month is not None and current_month >= self.expires_month

    def is_discoverable_by(self, avatar: Any) -> bool:
        return True

    def discover(self, avatar: Any) -> bool:
        avatar_id = str(getattr(avatar, "id", ""))
        if not avatar_id or avatar_id in self.discovered_by:
            return False
        self.discovered_by.add(avatar_id)
        return True

    def is_known_by(self, avatar: Any) -> bool:
        return str(getattr(avatar, "id", "")) in self.discovered_by

    @abstractmethod
    def get_detail_payload(self, world: Any) -> dict[str, Any]:
        ...

    @abstractmethod
    def to_save_dict(self) -> dict[str, Any]:
        ...
```

说明：

1. `id` 是稳定 ID，不使用名称解析。
2. `kind` 用于区分 `grave`、未来古碑、阵眼等。
3. `x/y` 是 tile 坐标。
4. `discovered_by` 保存知道该 POI 的角色 ID。
5. 第一版可以只在 POI 上保存发现关系，不必同步维护 `avatar.known_poi_ids`，避免双写不一致。

### GravePOI

墓碑字段建议：

```python
@dataclass
class GravePOI(PointOfInterest):
    kind: str = "grave"
    deceased_avatar_id: str = ""
    deceased_name: str = ""
    death_reason: str = ""
    death_month: int = 0
    realm_at_death: str = ""
    stage_at_death: str = ""
    sect_name_at_death: str = ""
    alignment_at_death: str = ""
    grave_icon_id: str = "grave_01"
    weapon_payload: dict[str, Any] | None = None
    auxiliary_payload: dict[str, Any] | None = None
    weapon_looted: bool = False
    auxiliary_looted: bool = False
    dig_attempt_count: int = 0
```

墓碑应保存轻量死者快照，避免 50 年内因为 Avatar 对象被清理或索引变化导致墓碑详情无法展示。

装备 payload 只保存 JSON 基础类型：

```json
{
  "kind": "weapon",
  "item_id": 1001,
  "name": "练气剑",
  "realm": "Qi_Refinement",
  "special_data": {}
}
```

辅助装备同理：

```json
{
  "kind": "auxiliary",
  "item_id": 2001,
  "name": "聚灵珠",
  "realm": "Qi_Refinement",
  "special_data": {}
}
```

墓碑不保存：

1. 功法。
2. 材料。
3. 灵石。
4. 丹药。
5. 复杂 Avatar 对象引用。
6. Weapon / Auxiliary 对象引用。

## POIManager

建议挂在 `World` 上：

```python
@dataclass
class World:
    ...
    poi_manager: POIManager = field(default_factory=POIManager)
```

原因：

1. POI 是运行时世界状态，不是静态地图配置。
2. POI 依赖世界时间、死亡、事件、存档。
3. `Map` 应继续主要负责 tile、region、landmark、formation 等地图结构。

`POIManager` 建议职责：

```python
@dataclass
class POIManager:
    pois: dict[str, PointOfInterest] = field(default_factory=dict)

    def add(self, poi: PointOfInterest) -> None: ...
    def get(self, poi_id: str) -> PointOfInterest | None: ...
    def remove(self, poi_id: str) -> None: ...
    def get_all_active(self, current_month: int | None = None) -> list[PointOfInterest]: ...
    def get_known_by(self, avatar: Any) -> list[PointOfInterest]: ...
    def get_within_observation(self, avatar: Any) -> list[PointOfInterest]: ...
    def discover_nearby(self, avatar: Any) -> list[PointOfInterest]: ...
    def cleanup_expired(self, current_month: int) -> int: ...
    def create_grave_from_avatar(self, avatar: Any, current_month: int) -> GravePOI: ...
    def to_save_list(self) -> list[dict[str, Any]]: ...
    def load_from_list(self, data: list[dict[str, Any]]) -> None: ...
```

## 墓碑生成

统一入口应在 `src/classes/death.py -> handle_death(...)`。

推荐顺序：

```python
def handle_death(world: World, avatar: Avatar, reason: Union[str, DeathReason]) -> None:
    reason_str = str(reason)
    avatar.set_dead(reason_str, world.month_stamp)
    world.poi_manager.create_grave_from_avatar(avatar, current_month=int(world.month_stamp))
    world.avatar_manager.handle_death(avatar.id)
    world.deceased_manager.record_death(avatar)
```

顺序说明：

1. `avatar.set_dead(...)` 会记录 `death_info`，包括死亡时间、死因、死亡坐标、宗门快照、阵营快照。
2. 墓碑生成必须使用 `avatar.pos_x/pos_y` 或 `death_info.location`，不要使用 `avatar.tile`。
3. `avatar_manager.handle_death(...)` 会把死者移入 `dead_avatars`，并将 `avatar.tile = None`。
4. 战斗中的杀人夺宝当前发生在 `handle_death(...)` 之前，因此墓碑生成时 `avatar.weapon/auxiliary` 已经是夺宝后的剩余装备。

墓碑 ID 建议：

```text
grave:<avatar_id>:<death_month>
```

墓碑名称建议：

```text
{deceased_name}之墓
```

墓碑图标：

1. 从 `grave_01` 到 `grave_09` 随机选一个。
2. 选中后写入 `grave_icon_id` 并随存档保存。
3. 读档后不重新随机，确保视觉稳定。

## 发现机制

角色交互范围沿用现有观察范围：

1. `src/classes/observe.py -> get_avatar_observation_radius(...)`
2. 曼哈顿距离：`abs(poi.x - avatar.pos_x) + abs(poi.y - avatar.pos_y)`

规则：

1. POI 在角色交互范围内时必定发现。
2. 已发现的 POI 写入 `poi.discovered_by`。
3. 过期 POI 不再被发现。
4. 第一版不做隐藏难度、陷阱感知、传闻发现、情报传播。

建议新增模拟器相位：

```text
src/sim/simulator_engine/phases/poi.py
```

放在角色行动推进之后、年度维护之前，使角色移动后能在同一 tick 发现附近墓碑。

发现事件：

1. 普通发现墓碑为小事件。
2. 如果未来 POI 稀有度更高，可按 POI 类型决定 `is_major`。
3. 事件 `related_avatars` 包含发现者；墓碑死者是否进入 `related_avatars` 可暂不加入，避免 50 年后事件 subject 退化影响过大。

## 移动到 POI

建议新增两个动作：

1. `MoveToPoint`：底层动作，按 `x/y` 移动，不一定暴露给 AI。
2. `MoveToPOI`：实际暴露动作，参数为 `poi_id`。

`MoveToPOI`：

```python
class MoveToPOI(DefineAction, ActualActionMixin):
    ACTION_NAME_ID = "move_to_poi_action_name"
    DESC_ID = "move_to_poi_description"
    REQUIREMENTS_ID = "move_to_poi_requirements"
    EMOJI = "🏃"
    PARAMS = {"poi_id": "poi_id"}
    PARAM_OPTION_SOURCES = {"poi_id": ParamOptionSource.KNOWN_POI_ID}
```

参数设计：

1. `value` 必须是 `poi.id`。
2. 不使用名称作为执行参数。
3. `param_options` 可展示 `name`、`kind`、`x/y`、距离。

示例：

```json
{
  "value": "grave:avatar-123:600",
  "id": "grave:avatar-123:600",
  "name": "李青之墓",
  "type": "grave",
  "x": 12,
  "y": 8,
  "distance": 5
}
```

`can_start(...)` 检查：

1. POI 存在。
2. POI 未过期。
3. 角色已知该 POI。
4. 目标坐标在地图范围内。

执行逻辑可参考 `MoveToRegion`，但目标点固定为 `poi.x/poi.y`。

完成条件：

```python
avatar.pos_x == poi.x and avatar.pos_y == poi.y
```

## 掘墓动作

建议新增动作：

```text
src/classes/action/dig_grave.py
```

动作定义：

```python
class DigGrave(InstantAction):
    ACTION_NAME_ID = "dig_grave_action_name"
    DESC_ID = "dig_grave_description"
    REQUIREMENTS_ID = "dig_grave_requirements"
    EMOJI = "⛏"
    PARAMS = {"poi_id": "poi_id"}
    PARAM_OPTION_SOURCES = {"poi_id": ParamOptionSource.KNOWN_GRAVE_POI_ID}
```

`can_start(...)`：

1. `poi_id` 必须指向存在的 POI。
2. POI 必须是 `grave`。
3. 墓碑未过期。
4. 角色必须知道该墓碑。
5. 角色必须在墓碑交互范围内，或更严格地要求处于同 tile。第一版建议要求同 tile，行动链由 `MoveToPOI -> DigGrave` 完成。
6. 无装备墓碑也允许启动，但结果必定不会成功获得物品。

成功率建议：

```text
base_success = 0.45
realm_delta = digger_realm_rank - deceased_realm_rank
success_rate = clamp(base_success + realm_delta * 0.15, 0.05, 0.85)
injury_rate = clamp(0.10 - realm_delta * 0.05, 0.02, 0.50)
```

说明：

1. 掘墓者境界越高，相对越容易成功。
2. 死者境界越高，墓中残留禁制越危险。
3. 没有武器/辅助时，不进行成功掉落，只生成空墓结果。
4. 可以多次掘墓；每次增加 `dig_attempt_count`。
5. 每件装备只能被挖走一次；挖走后对应 payload 置空或 looted 标记为 True。

物品选择：

1. 若武器与辅助都存在，优先选择境界更高的装备。
2. 同境界随机。
3. 成功后复用 `resolve_item_exchange(...)`，让角色决定是否替换已有装备。
4. 如果玩家/AI 拒绝新装备，视为本次未取走，墓碑装备仍保留；若实现复杂，第一版也可以按 `auto_accept_when_empty` 仅在空装备槽自动接受，有旧装备时事件说明“未能带走”。

气运：

1. 每次掘墓都扣少量气运，例如 `luck_base -= 0.2` 或配置化为 `game.grave.dig_luck_penalty`。
2. 正派与反派都扣。
3. 正派的“微微不愿意”体现在 AI 行为倾向、prompt 描述或行动评分上，不体现在 `can_start` 禁止。
4. 反派不受行为倾向惩罚，但仍扣气运。

受伤：

1. 失败时可能受伤。
2. 受伤量按死者境界与掘墓者境界差决定。
3. 受伤导致 HP 降至 0 以下时，走现有死亡结算，不在掘墓动作内手写死亡归档。

事件：

1. 掘墓成功获得装备：`is_major=True`。
2. 掘墓失败但受伤：`is_major=True` 或按伤害严重程度决定。
3. 空墓、普通失败：`is_major=False`。
4. 事件 `related_avatars` 至少包含掘墓者。
5. 第一版不把死者亲友关系纳入事件影响。

## 前端接口与渲染

### Map API

扩展 `/api/v1/query/world/map`，增加 `pois`：

```json
{
  "pois": [
    {
      "id": "grave:avatar-123:600",
      "kind": "grave",
      "name": "李青之墓",
      "x": 12,
      "y": 8,
      "icon_key": "grave_01",
      "clickable": true
    }
  ]
}
```

第一版上帝视角可以返回所有未过期 POI。角色动作参数仍按角色已知 POI 过滤。

### Detail API

扩展现有 detail 查询：

```text
GET /api/v1/query/detail?type=poi&id=<poi_id>
```

`target_type == "poi"` 时：

1. 从 `world.poi_manager.get(target_id)` 读取 POI。
2. 不存在或过期时返回 404。
3. 调用 `poi.get_detail_payload(world)`。

墓碑详情 payload 示例：

```json
{
  "id": "grave:avatar-123:600",
  "kind": "grave",
  "name": "李青之墓",
  "desc": "一方古旧墓碑，碑面仍残留淡淡灵光。",
  "x": 12,
  "y": 8,
  "icon_key": "grave_01",
  "deceased": {
    "id": "avatar-123",
    "name": "李青",
    "age_at_death": 73,
    "realm_at_death": "Foundation_Establishment",
    "stage_at_death": "Middle_Stage",
    "death_reason": "被王五杀害",
    "death_time": 600,
    "sect_name_at_death": "青云宗",
    "alignment_at_death": "正派"
  },
  "grave_goods": {
    "weapon": null,
    "auxiliary": {
      "id": 2001,
      "name": "聚灵珠",
      "realm": "Qi_Refinement"
    }
  },
  "dig_attempt_count": 1
}
```

### WebSocket 增量

为了避免“死亡后墓碑要刷新页面才出现”，tick payload 建议增加 POI 增量：

```json
{
  "poi_updates": [
    {"op": "upsert", "poi": {"id": "...", "kind": "grave", "x": 1, "y": 2}},
    {"op": "remove", "id": "..."}
  ]
}
```

若第一版暂不做增量，也必须在死亡后让前端能触发重新拉取 map/pois，避免墓碑不同步。

### 前端类型与 Store

新增类型：

```ts
export interface POISummary extends EntityBase, Coordinates {
  kind: string
  icon_key?: string
  clickable?: boolean
}
```

`MapResponseDTO` 增加：

```ts
pois?: Array<{
  id: string
  kind: string
  name: string
  x: number
  y: number
  icon_key?: string
  clickable?: boolean
}>
```

`map` store 增加 `pois = shallowRef<Map<string, POISummary>>(new Map())`。

### POILayer

建议新增：

```text
web/src/components/game/POILayer.vue
```

并在 `GameCanvas.vue` 中插入：

```text
MapLayer
SectInfluenceLayer
POILayer
EntityLayer
PerceptionLayer
CloudLayer
```

点击事件：

```ts
(e: 'poiSelected', payload: { type: 'poi'; id: string; kind: string; name?: string }): void
```

墓碑详情显示建议新增：

```text
web/src/components/game/panels/info/POIDetail.vue
```

由 `InfoPanelContainer` 按 `type === 'poi'` 分发。

## 存档与读档

开发阶段不要求向前兼容旧存档，可以直接新增字段并让新代码以清晰结构读取。

### World 存档字段

建议在 world section 中新增：

```json
{
  "pois": [
    {
      "schema_version": 1,
      "id": "grave:avatar-123:600",
      "kind": "grave",
      "x": 12,
      "y": 8,
      "name": "李青之墓",
      "desc": "一方古旧墓碑，碑面仍残留淡淡灵光。",
      "created_month": 600,
      "expires_month": 1200,
      "discovered_by": ["avatar-456"],
      "icon_key": "grave_01",
      "is_clickable": true,
      "deceased_avatar_id": "avatar-123",
      "deceased_name": "李青",
      "death_reason": "被王五杀害",
      "death_month": 600,
      "realm_at_death": "Foundation_Establishment",
      "stage_at_death": "Middle_Stage",
      "sect_name_at_death": "青云宗",
      "alignment_at_death": "正派",
      "grave_icon_id": "grave_01",
      "weapon_payload": null,
      "auxiliary_payload": {
        "kind": "auxiliary",
        "item_id": 2001,
        "name": "聚灵珠",
        "realm": "Qi_Refinement",
        "special_data": {}
      },
      "weapon_looted": true,
      "auxiliary_looted": false,
      "dig_attempt_count": 1
    }
  ]
}
```

### 序列化约束

1. 只保存 JSON 基础类型。
2. 跨对象引用只保存 ID。
3. 装备保存 `item_id + special_data`，读档时从全局 registry 恢复实例。
4. `discovered_by` 保存字符串列表，读档时转回 set。
5. 读档后 `grave_icon_id/icon_key` 保持不变，不重新随机。

### 读档恢复

读档时：

1. 创建 `world.poi_manager`。
2. 从 `world_data["pois"]` 恢复所有 POI。
3. 根据 `kind` 分发到具体类，例如 `GravePOI.from_save_dict(...)`。
4. 恢复后不依赖死者 Avatar 对象存在。
5. 恢复后可通过 `world.deceased_manager.get_record(...)` 补充死者详情；若记录不存在，使用墓碑内置快照。

### 清理

年度维护时同步清理：

1. `world.avatar_manager.cleanup_long_dead_avatars(..., threshold_years=50)`
2. `world.deceased_manager.cleanup_expired_records(..., threshold_years=50)`
3. `world.poi_manager.cleanup_expired(current_month)`

配置：

```yaml
world:
  long_dead_cleanup_years: 50
```

可以新增：

```yaml
game:
  grave:
    retention_years: 50
    dig_luck_penalty: 0.2
```

但第一版也可以先复用 `world.long_dead_cleanup_years`，保证死者与墓碑生命周期一致。

## i18n

当前日常开发仍按 Phase 1，只需保证 `zh-CN` 可用。

需要新增的 key 归属：

1. 后端 action 文案：`static/locales/zh-CN/modules/action.po` 或相关 action 模块。
2. 后端事件文案：按现有事件/动作模块放置。
3. 前端 UI 文案：`web/src/locales/zh-CN/game.json` 或新增 `poi.json`。

`.po` 中 `msgid` 不得直接写中文；中文只放 `msgstr`。

短槽位建议：

1. `poi.grave.title_short`: `墓碑`
2. `poi.grave.goods`: `墓中遗物`
3. `poi.grave.dig`: `掘墓`
4. `poi.grave.empty`: `墓中已无可取之物`

## 测试策略

### 后端单元与集成

1. POIManager 增删查、过期清理。
2. GravePOI `to_save_dict/from_save_dict` 保持字段完整。
3. `handle_death()` 生成墓碑，坐标等于死亡坐标。
4. 任意地点死亡都生成墓碑，包括无 region tile。
5. 战斗杀死并夺宝后，墓碑只保存剩余装备。
6. 非战斗死亡时，墓碑保存武器与辅助装备，不保存功法。
7. 墓碑图标随机后随存档保存，读档不变化。
8. 死者、墓碑、已故档案 49 年仍在，50 年被清理。
9. 清理死者后，墓碑详情在 50 年内仍可依赖自身快照展示。
10. `discover_nearby()`：范围内必发现，范围外不发现。
11. `MoveToPOI`：只能移动到已知、未过期 POI。
12. `MoveToPOI` 参数选项 value 是 poi id，不是名称。
13. `DigGrave`：未知 POI、非墓碑、过期墓碑、距离不满足时不能开始。
14. `DigGrave`：空墓可执行但不会成功获得装备。
15. `DigGrave`：成功后对应装备从墓碑详情消失。
16. `DigGrave`：每次执行扣气运；正派/反派都扣。
17. `DigGrave`：失败可能受伤，HP 变化正确。
18. `DigGrave`：受伤致死时走现有死亡结算。

### 前端

1. `MapResponseDTO` 与 mapper 正确接收 `pois`。
2. map store 使用 `shallowRef` 保存 POI 集合。
3. `POILayer` 渲染墓碑图标并 emit `poiSelected`。
4. `GameCanvas` 透传 `poiSelected`。
5. `InfoPanelContainer` 能打开 `POIDetail`。
6. 墓碑详情展示死者信息、死亡时间、死因、墓中遗物。
7. 装备被挖走后，对应信息不再展示。
8. 墓碑图标缺失时使用 fallback。

## 需要修改的代码区域

预计涉及：

```text
src/classes/death.py
src/classes/core/world.py
src/classes/poi/**
src/classes/action/param_options.py
src/classes/action/move_to_poi.py
src/classes/action/dig_grave.py
src/classes/action/__init__.py
src/sim/simulator_engine/phases/**
src/sim/save/sections/**
src/server/services/game_queries.py
src/server/loop_runtime.py
web/src/types/api.ts
web/src/types/core.ts
web/src/api/mappers/world.ts
web/src/stores/map.ts
web/src/components/game/GameCanvas.vue
web/src/components/game/POILayer.vue
web/src/components/game/panels/info/**
web/src/utils/poiIcons.ts
web/src/assets/icons/pois/**
static/config.yml
static/locales/zh-CN/modules/**
web/src/locales/zh-CN/**
tests/**
web/src/__tests__/**
```

新增动作必须：

1. 在 `src/classes/action/__init__.py` 导入并注册。
2. 补 `can_possibly_start` 测试，尤其是无已知墓碑、范围内墓碑、空墓碑等分支。
3. 补参数选项测试，确保 `param_options.value` 可被动作执行层解析。

## 验证命令

后端按改动范围运行：

```powershell
pytest tests/test_death.py tests/test_save_load_death.py tests/test_deceased_manager.py
pytest tests/test_action_param_options.py tests/test_action_can_possibly_start.py
pytest tests/test_public_api_v1.py tests/test_websocket_handlers.py
```

新增 POI 测试后可单独运行：

```powershell
pytest tests/test_poi_system.py tests/test_grave_poi.py tests/test_action_dig_grave.py tests/test_action_move_to_poi.py
```

前端按改动范围运行：

```powershell
cd web; npm run type-check
cd web; npm run test -- --run
```

如果只做 Phase 1 图片资产，至少人工检查：

1. PNG 文件尺寸一致。
2. 墓碑主体非空。
3. 小尺寸下仍可辨识。
4. 背景透明或与现有图标系统一致。
5. 文件名与 `poiIcons.ts` 映射一致。

## 设计取舍记录

1. 掘墓仍扣气运，正派/反派都扣。
2. 反派不受“微微不愿意掘墓”的行为倾向惩罚。
3. 第一版不做多墓碑聚合。
4. 第一版允许重复掘墓，但装备只能被挖走一次。
5. 掘墓成功或严重失败可作为重大事件。
6. 墓碑不阻挡移动。
7. 第一版不做亲友复仇、宗门声望惩罚等复杂后果。
8. 任意地图点死亡都生成墓碑。
9. 死者信息 50 年后消失，旧事件 subject 可能退化为 ID，这是可接受结果。

## 后续留白

未来可以扩展：

1. 同 tile 多 POI 聚合显示。
2. 墓碑被掘后的社交传播和仇恨。
3. 墓碑风水、气运、怨气、尸变等特殊事件。
4. 高境界墓碑的禁制、阵法、守墓灵。
5. POI 情报交易、传闻发现、地图标记分享。
6. 角色扮演模式下按受控角色过滤可见 POI。
7. 外接控制 API 查询与命令接口，例如 `query/poi/list`、`command/avatar/move-to-poi`。
8. 其他 POI 类型：古碑、阵眼、秘境入口、遗落法器、战场遗迹。
