import random
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Union

from src.classes.core.world import World
from src.classes.core.avatar import Avatar, Gender
from src.classes.appearance import get_appearance_by_level
from src.systems.time import MonthStamp
from src.classes.environment.region import Region
from src.utils.resolution import resolve_query
from src.systems.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.age import Age
from src.utils.name_generator import get_random_name_for_sect, pick_surname_for_sect, get_random_name_with_surname
from src.utils.id_generator import get_avatar_id
from src.classes.core.sect import Sect, sects_by_id, sects_by_name
from src.classes.relation.relation import Relation
from src.classes.technique import get_technique_by_sect, attribute_to_root, Technique, techniques_by_id, techniques_by_name
from src.classes.items.weapon import Weapon, weapons_by_id, weapons_by_name
from src.classes.items.auxiliary import Auxiliary, auxiliaries_by_id, auxiliaries_by_name
from src.classes.persona import Persona, personas_by_id, personas_by_name
from src.classes.items.magic_stone import MagicStone
from src.utils.born_region import get_born_region_id


# —— 参数常量（便于调参）——
SECT_MEMBER_RATIO: float = 2 / 3

AGE_MIN: int = 16
AGE_MAX: int = 150
LEVEL_MIN: int = 0
LEVEL_MAX: int = 120

FAMILY_PAIR_CAP_DIV: int = 6            # 家庭上限：n // 6
FAMILY_TRIGGER_PROB: float = 0.35       # 生成家庭对概率
FATHER_CHILD_PROB: float = 0.60         # 家庭为父子（同姓、父为男）的概率；否则母子（异姓、母为女）

LOVERS_PAIR_CAP_DIV: int = 5            # 道侣两两预算：n // 5
LOVERS_TRIGGER_PROB: float = 0.25       # 生成一对道侣的概率（强制异性）

MASTER_PAIR_PROB: float = 0.30          # 同宗门内生成一对师徒的概率

FRIEND_PROB: float = 0.18               # 朋友概率
ENEMY_PROB: float = 0.10                # 仇人概率（与朋友互斥）

PARENT_MIN_DIFF: int = 16               # 父母与子女最小年龄差
PARENT_MAX_DIFF: int = 80               # 父母与子女最大年龄差（用于生成目标差值）
PARENT_AGE_CAP: int = 120               # 父母年龄上限（修仙世界放宽）

MASTER_LEVEL_MIN_DIFF: int = 20         # 师傅与徒弟最小等级差
MASTER_LEVEL_EXTRA_MAX: int = 10        # 在最小等级差基础上的额外浮动

# 父母-子女等级差（修仙世界中通常父母更强）
PARENT_LEVEL_MIN_DIFF: int = 10         # 父母与子女最小等级差
PARENT_LEVEL_EXTRA_MAX: int = 10        # 在最小等级差基础上的额外浮动

# —— 新凡人（单个）生成相关概率与范围 ——
NEW_MORTAL_PARENT_PROB: float = 0.30    # 有概率是某个既有角色的子女
NEW_MORTAL_SECT_PROB: float = 0.50      # 有概率成为某个“已有宗门”的弟子
NEW_MORTAL_MASTER_PROB: float = 0.40    # 若成为宗门弟子，有概率拜该宗门现有人物为师
NEW_MORTAL_LEVEL_MAX: int = 40          # 新凡人默认偏低等级上限


def random_gender() -> Gender:
    return Gender.MALE if random.random() < 0.5 else Gender.FEMALE


class EquipmentAllocator:
    """
    负责所有初始装备分配逻辑，提供兵器与辅助装备的统一接口。
    （仅用于世界生成或完整角色生成，觉醒逻辑使用简化配置）
    """

    @staticmethod
    def assign_weapon(avatar: Avatar) -> None:
        """
        初始兵器逻辑：
        - 80% 继承宗门偏好兵器类型，否则完全随机
        - 根据境界随机生成一把兵器
        """
        from src.classes.items.weapon import get_random_weapon_by_realm
        from src.classes.weapon_type import WeaponType

        weapon_type = None
        if avatar.sect is not None and avatar.sect.preferred_weapon:
            if random.random() < 0.8:
                for wt in WeaponType:
                    if wt.value == avatar.sect.preferred_weapon:
                        weapon_type = wt
                        break
        
        avatar.weapon = get_random_weapon_by_realm(avatar.cultivation_progress.realm, weapon_type)

    @staticmethod
    def assign_auxiliary(avatar: Avatar) -> None:
        """
        初始辅助装备逻辑：
        - 根据境界随机生成一件辅助装备
        """
        from src.classes.items.auxiliary import get_random_auxiliary_by_realm
        
        avatar.auxiliary = get_random_auxiliary_by_realm(avatar.cultivation_progress.realm)


@dataclass
class MortalPlan:
    gender: Optional[Gender] = None
    sect: Optional[Sect] = None
    surname: Optional[str] = None
    parent_avatar: Optional[Avatar] = None
    master_avatar: Optional[Avatar] = None
    level: int = 1
    pos_x: int = 0
    pos_y: int = 0


@dataclass
class PopulationPlan:
    sects: List[Optional[Sect]]
    genders: List[Optional[Gender]]
    surnames: List[Optional[str]]
    relations: Dict[Tuple[int, int], Relation]

class MortalPlanner:
    """
    负责单个角色的前期规划（宗门、性别、关系、出生点等）。
    """

    @staticmethod
    def plan(
        world: World,
        name: str,
        age: Age,
        *,
        existed_sects: Optional[List[Sect]] = None,
        existing_avatars: Optional[List[Avatar]] = None,
        level: int = 1,
        allow_relations: bool = True,
    ) -> MortalPlan:
        plan = MortalPlan(level=level)

        plan.gender = random_gender()
        plan.pos_x = random.randint(0, world.map.width - 1)
        plan.pos_y = random.randint(0, world.map.height - 1)

        if existing_avatars is None:
            existing_avatars = world.avatar_manager.get_living_avatars()
        else:
            existing_avatars = [av for av in existing_avatars if not av.is_dead]
            
        if existed_sects is None:
            try:
                from src.classes.core.sect import sects_by_id as _sects_by_id
                existed_sects = list(_sects_by_id.values())
            except Exception:
                existed_sects = []

        if random.random() < NEW_MORTAL_SECT_PROB:
            picked = PopulationPlanner._pick_sects_balanced(existed_sects or [], 1)
            plan.sect = picked[0] if picked else None

        if allow_relations and existing_avatars:
            if random.random() < NEW_MORTAL_PARENT_PROB:
                candidates: list[Avatar] = [
                    av for av in existing_avatars if av.age.age >= age.age + PARENT_MIN_DIFF
                ]
                if candidates:
                    parent = random.choice(candidates)
                    plan.parent_avatar = parent
                    if not name:
                        if parent.gender is Gender.MALE:
                            plan.surname = pick_surname_for_sect(plan.sect or parent.sect)
                        else:
                            mom_surname = pick_surname_for_sect(plan.sect or parent.sect)
                            for _ in range(5):
                                s = pick_surname_for_sect(plan.sect)
                                if s != mom_surname:
                                    plan.surname = s
                                    break
            if plan.sect is not None and random.random() < NEW_MORTAL_MASTER_PROB:
                same_sect = [av for av in existing_avatars if av.sect is plan.sect]
                if same_sect:
                    stronger = [
                        av
                        for av in same_sect
                        if av.cultivation_progress.level >= plan.level + MASTER_LEVEL_MIN_DIFF
                    ]
                    if stronger:
                        plan.master_avatar = random.choice(stronger)

        return plan


class PopulationPlanner:
    """
    负责批量角色的宗门/关系规划。
    """

    @staticmethod
    def plan_group(n: int, existed_sects: Optional[List[Sect]]) -> PopulationPlan:
        n = int(max(0, n))
        use_sects = bool(existed_sects)
        planned_sect: list[Optional[Sect]] = [None] * n
        if n == 0:
            return PopulationPlan(planned_sect, [None] * 0, [None] * 0, {})

        if use_sects and existed_sects:
            sect_member_target = int(n * SECT_MEMBER_RATIO)
            planned_sect[:sect_member_target] = PopulationPlanner._pick_sects_balanced(existed_sects, sect_member_target)
            paired = list(zip(planned_sect, list(range(n))))
            random.shuffle(paired)
            planned_sect = [p[0] for p in paired]

        planned_gender: list[Optional[Gender]] = [None] * n
        planned_surname: list[Optional[str]] = [None] * n
        planned_relations: dict[tuple[int, int], Relation] = {}

        # — 家庭 —
        unused_indices = list(range(n))
        random.shuffle(unused_indices)

        def _reserve_pair() -> tuple[int, int] | None:
            if len(unused_indices) < 2:
                return None
            a = unused_indices.pop()
            b = unused_indices.pop()
            return (a, b)

        family_pairs_budget = max(0, n // FAMILY_PAIR_CAP_DIV)
        for _ in range(family_pairs_budget):
            if random.random() < FAMILY_TRIGGER_PROB:
                pair = _reserve_pair()
                if pair is None:
                    break
                a, b = pair
                if random.random() < FATHER_CHILD_PROB:
                    surname = pick_surname_for_sect(planned_sect[a] or planned_sect[b])
                    planned_surname[a] = surname
                    planned_surname[b] = surname
                    planned_gender[a] = Gender.MALE
                    # 设定 a 为父，b 为子
                    planned_relations[(a, b)] = Relation.IS_CHILD_OF
                else:
                    mother = a if random.random() < 0.5 else b
                    child = b if mother == a else a
                    planned_gender[mother] = Gender.FEMALE
                    mom_surname = pick_surname_for_sect(planned_sect[mother])
                    planned_surname[mother] = mom_surname
                    for _ in range(5):
                        s = pick_surname_for_sect(planned_sect[child])
                        if s != mom_surname:
                            planned_surname[child] = s
                            break
                    planned_relations[(mother, child)] = Relation.IS_CHILD_OF

        leftover = unused_indices[:]

        # — 道侣 —
        random.shuffle(leftover)
        lovers_budget = max(0, n // LOVERS_PAIR_CAP_DIV)
        i = 0
        while i + 1 < len(leftover) and lovers_budget > 0:
            if random.random() < LOVERS_TRIGGER_PROB:
                a = leftover[i]
                b = leftover[i + 1]
                if (a, b) not in planned_relations and (b, a) not in planned_relations:
                    if planned_gender[a] is None and planned_gender[b] is None:
                        planned_gender[a] = Gender.MALE if random.random() < 0.5 else Gender.FEMALE
                        planned_gender[b] = Gender.FEMALE if planned_gender[a] is Gender.MALE else Gender.MALE
                    elif planned_gender[a] is None:
                        planned_gender[a] = Gender.MALE if planned_gender[b] is Gender.FEMALE else Gender.FEMALE
                    elif planned_gender[b] is None:
                        planned_gender[b] = Gender.MALE if planned_gender[a] is Gender.FEMALE else Gender.FEMALE
                    if planned_gender[a] != planned_gender[b]:
                        planned_relations[(a, b)] = Relation.IS_LOVER_OF
                lovers_budget -= 1
            i += 2

        # — 师徒（同宗门）—
        if use_sects and existed_sects:
            members_by_sect: dict[int, list[int]] = {s.id: [] for s in existed_sects}
            for idx, sect in enumerate(planned_sect):
                if sect is not None:
                    members_by_sect.setdefault(sect.id, []).append(idx)
            for members in members_by_sect.values():
                random.shuffle(members)
                j = 0
                while j + 1 < len(members):
                    if random.random() < MASTER_PAIR_PROB:
                        master, apprentice = members[j], members[j + 1]
                        if (master, apprentice) not in planned_relations and (apprentice, master) not in planned_relations:
                            planned_relations[(master, apprentice)] = Relation.IS_DISCIPLE_OF
                    j += 2

        # — 朋友/仇人 —
        all_indices = list(range(n))
        random.shuffle(all_indices)
        k = 0
        while k + 1 < len(all_indices):
            a, b = all_indices[k], all_indices[k + 1]
            if (a, b) in planned_relations or (b, a) in planned_relations:
                k += 2
                continue
            r = random.random()
            if r < FRIEND_PROB:
                planned_relations[(a, b)] = Relation.IS_FRIEND_OF
            elif r < FRIEND_PROB + ENEMY_PROB:
                planned_relations[(a, b)] = Relation.IS_ENEMY_OF
            k += 2

        for idx in range(n):
            if planned_gender[idx] is None:
                planned_gender[idx] = random_gender()

        return PopulationPlan(planned_sect, planned_gender, planned_surname, planned_relations)

    @staticmethod
    def _pick_sects_balanced(existed_sects: List[Sect], k: int) -> list[Optional[Sect]]:
        if not existed_sects or k <= 0:
            return []
        counts: dict[int, int] = {s.id: 0 for s in existed_sects}
        chosen: list[Optional[Sect]] = []
        for _ in range(k):
            min_count = min(counts.values()) if counts else 0
            candidates = [s for s in existed_sects if counts.get(s.id, 0) == min_count]
            s = random.choice(candidates)
            counts[s.id] = counts.get(s.id, 0) + 1
            chosen.append(s)
        return chosen


class RelationApplier:
    """
    负责将规划关系写入 Avatar 实例。
    """

    @staticmethod
    def apply(avatars_by_index: List[Optional[Avatar]], relations: dict[tuple[int, int], Relation]) -> None:
        for (a, b), relation in relations.items():
            if a >= len(avatars_by_index) or b >= len(avatars_by_index):
                continue
            av_a = avatars_by_index[a]
            av_b = avatars_by_index[b]
            if av_a is None or av_b is None or av_a is av_b:
                continue
            av_a.set_relation(av_b, relation)


class SectRankAssigner:
    """
    负责宗门职位的分配，保证掌门唯一。
    """

    @staticmethod
    def assign_one(avatar: Avatar, world: World) -> None:
        if avatar.sect is None:
            avatar.sect_rank = None
            return

        from src.classes.sect_ranks import get_rank_from_realm, sect_has_patriarch, SectRank

        rank = get_rank_from_realm(avatar.cultivation_progress.realm)
        if rank == SectRank.Patriarch and sect_has_patriarch(avatar):
            rank = SectRank.Elder
        avatar.sect_rank = rank

    @staticmethod
    def assign_batch(avatars: List[Avatar], world: World) -> None:
        from src.classes.sect_ranks import get_rank_from_realm, SectRank

        for avatar in avatars:
            if avatar is None:
                continue
            if avatar.sect is None:
                avatar.sect_rank = None
            else:
                avatar.sect_rank = get_rank_from_realm(avatar.cultivation_progress.realm)

        sect_nascent_souls: Dict[int, List[Avatar]] = {}
        for avatar in avatars:
            if avatar is None or avatar.sect is None:
                continue
            if avatar.sect_rank == SectRank.Patriarch:
                sect_id = avatar.sect.id
                if sect_id not in sect_nascent_souls:
                    sect_nascent_souls[sect_id] = []
                sect_nascent_souls[sect_id].append(avatar)

        existing_patriarchs: Dict[int, bool] = {}
        for other in world.avatar_manager.avatars.values():
            if other.sect is not None and other.sect_rank == SectRank.Patriarch:
                existing_patriarchs[other.sect.id] = True

        for sect_id, candidates in sect_nascent_souls.items():
            if existing_patriarchs.get(sect_id, False):
                for avatar in candidates:
                    avatar.sect_rank = SectRank.Elder
            else:
                candidates.sort(key=lambda av: av.cultivation_progress.level, reverse=True)
                for avatar in candidates[1:]:
                    avatar.sect_rank = SectRank.Elder


class AvatarFactory:
    """
    根据规划产出 Avatar，对装备、宗门职位和关系进行统一处理。
    """

    @staticmethod
    def build_from_plan(
        world: World,
        current_month_stamp: MonthStamp,
        *,
        name: str,
        age: Age,
        plan: MortalPlan,
        attach_relations: bool = True,
        overrides: Optional[Dict[str, object]] = None,
    ) -> Avatar:
        if name:
            final_name = name
        else:
            if plan.surname:
                final_name = get_random_name_with_surname(plan.gender, plan.surname, plan.sect)
            else:
                final_name = get_random_name_for_sect(plan.gender, plan.sect)

        birth_month_stamp = current_month_stamp - age.age * 12 + random.randint(0, 11)

        avatar = Avatar(
            world=world,
            name=final_name,
            id=get_avatar_id(),
            birth_month_stamp=MonthStamp(birth_month_stamp),
            age=age,
            gender=plan.gender,
            cultivation_progress=CultivationProgress(plan.level),
            pos_x=plan.pos_x,
            pos_y=plan.pos_y,
            sect=plan.sect,
        )

        avatar.magic_stone = MagicStone(50)
        avatar.tile = world.map.get_tile(avatar.pos_x, avatar.pos_y)

        # 确定出生地
        parents_list = []
        if plan.parent_avatar:
            parents_list.append(plan.parent_avatar)
        avatar.born_region_id = get_born_region_id(world, parents=parents_list, sect=plan.sect)

        SectRankAssigner.assign_one(avatar, world)
        EquipmentAllocator.assign_weapon(avatar)
        EquipmentAllocator.assign_auxiliary(avatar)

        if attach_relations:
            if plan.parent_avatar is not None:
                plan.parent_avatar.acknowledge_child(avatar)
            if plan.master_avatar is not None:
                plan.master_avatar.accept_disciple(avatar)

        if avatar.technique is not None:
            mapped = attribute_to_root(avatar.technique.attribute)
            if mapped is not None:
                avatar.root = mapped

        if overrides:
            AvatarFactory._apply_overrides(avatar, overrides)

        return avatar

    @staticmethod
    def build_group(
        world: World,
        current_month_stamp: MonthStamp,
        population_plan: PopulationPlan,
    ) -> dict[str, Avatar]:
        planned_sect = population_plan.sects
        planned_gender = population_plan.genders
        planned_surname = population_plan.surnames
        planned_relations = population_plan.relations

        n = len(planned_sect)
        width, height = world.map.width, world.map.height

        ages: list[int] = [random.randint(AGE_MIN, AGE_MAX) for _ in range(n)]
        levels: list[int] = [random.randint(LEVEL_MIN, LEVEL_MAX) for _ in range(n)]

        for (a, b), rel in list(planned_relations.items()):
            if rel is Relation.IS_CHILD_OF:
                if ages[a] <= ages[b] + (PARENT_MIN_DIFF - 1):
                    ages[a] = min(PARENT_AGE_CAP, ages[b] + random.randint(PARENT_MIN_DIFF, PARENT_MAX_DIFF))

        for (a, b), rel in list(planned_relations.items()):
            if rel is Relation.IS_CHILD_OF:
                if levels[a] <= levels[b]:
                    levels[a] = min(LEVEL_MAX, levels[b] + 1)
                if levels[a] < levels[b] + PARENT_LEVEL_MIN_DIFF:
                    levels[a] = min(LEVEL_MAX, levels[b] + PARENT_LEVEL_MIN_DIFF + random.randint(0, PARENT_LEVEL_EXTRA_MAX))

        for (a, b), rel in list(planned_relations.items()):
            if rel is Relation.IS_DISCIPLE_OF:
                if levels[a] < levels[b] + MASTER_LEVEL_MIN_DIFF:
                    levels[a] = min(LEVEL_MAX, levels[b] + MASTER_LEVEL_MIN_DIFF + random.randint(0, MASTER_LEVEL_EXTRA_MAX))

        for i in range(n):
            realm = CultivationProgress(levels[i]).realm
            max_lifespan = Age.REALM_LIFESPAN.get(realm, 100)
            if ages[i] >= max_lifespan:
                ages[i] = int(max_lifespan * random.uniform(0.8, 0.95))

        avatars_by_index: list[Avatar] = [None] * n  # type: ignore
        avatars_by_id: dict[str, Avatar] = {}

        for i in range(n):
            gender = planned_gender[i] or random_gender()
            sect = planned_sect[i]

            if planned_surname[i]:
                name = get_random_name_with_surname(gender, planned_surname[i] or "", sect)
            else:
                name = get_random_name_for_sect(gender, sect)

            level = levels[i]
            cultivation_progress = CultivationProgress(level)
            age_years = ages[i]
            age = Age(age_years, cultivation_progress.realm)

            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            birth_month_stamp = current_month_stamp - age_years * 12 + random.randint(0, 11)

            avatar = Avatar(
                world=world,
                name=name,
                id=get_avatar_id(),
                birth_month_stamp=MonthStamp(birth_month_stamp),
                age=age,
                gender=gender,
                cultivation_progress=cultivation_progress,
                pos_x=x,
                pos_y=y,
                root=random.choice(list(Root)),
                sect=sect,
            )

            avatar.magic_stone = MagicStone(50)
            avatar.tile = world.map.get_tile(x, y)

            # 确定出生地
            current_parents = []
            for (p_idx, c_idx), rel in planned_relations.items():
                 if rel == Relation.IS_CHILD_OF and c_idx == i:
                     # 只有当父母已经被创建时才能作为参考（通常索引较小的先创建）
                     if p_idx < len(avatars_by_index) and avatars_by_index[p_idx]:
                         current_parents.append(avatars_by_index[p_idx])
            
            avatar.born_region_id = get_born_region_id(world, parents=current_parents, sect=sect)

            if sect is not None:
                avatar.alignment = sect.alignment
                avatar.technique = get_technique_by_sect(sect)

            EquipmentAllocator.assign_weapon(avatar)
            EquipmentAllocator.assign_auxiliary(avatar)

            if avatar.technique is not None:
                mapped = attribute_to_root(avatar.technique.attribute)
                if mapped is not None:
                    avatar.root = mapped

            avatars_by_index[i] = avatar
            avatars_by_id[avatar.id] = avatar

        SectRankAssigner.assign_batch(avatars_by_index, world)
        RelationApplier.apply(avatars_by_index, planned_relations)

        return avatars_by_id

    @staticmethod
    def _apply_overrides(avatar: Avatar, overrides: Dict[str, object]) -> None:
        technique = overrides.get("technique")
        if isinstance(technique, Technique):
            avatar.technique = technique
            mapped = attribute_to_root(technique.attribute)
            if mapped is not None:
                avatar.root = mapped

        weapon = overrides.get("weapon")
        if isinstance(weapon, Weapon):
            avatar.weapon = weapon

        auxiliary = overrides.get("auxiliary")
        if isinstance(auxiliary, Auxiliary):
            avatar.auxiliary = auxiliary

        personas = overrides.get("personas")
        if isinstance(personas, list) and personas:
            avatar.personas = personas  # type: ignore[assignment]

        appearance = overrides.get("appearance")
        if isinstance(appearance, int):
            avatar.appearance = get_appearance_by_level(appearance)


def create_random_mortal(world: World, current_month_stamp: MonthStamp, name: str, age: Age, level: int = 1) -> Avatar:
    """
    创建一个完全随机的新修士，包含可能的亲属/师徒关系。
    """
    plan = MortalPlanner.plan(world, name=name, age=age, level=level, allow_relations=True)
    return AvatarFactory.build_from_plan(world, current_month_stamp, name=name, age=age, plan=plan)


def make_avatars(
    world: World,
    count: int = 12,
    current_month_stamp: MonthStamp = MonthStamp(100 * 12),
    existed_sects: Optional[List[Sect]] = None,
) -> dict[str, Avatar]:
    population_plan = PopulationPlanner.plan_group(count, existed_sects)
    random_avatars = AvatarFactory.build_group(world, current_month_stamp, population_plan)
    return random_avatars

# —— 指定参数创建：支持传入字符串并解析为对象 ——
def _parse_gender(value: Union[str, Gender, None]) -> Optional[Gender]:
    if value is None:
        return None
    if isinstance(value, Gender):
        return value
    s = str(value).strip()
    if s == "男":
        return Gender.MALE
    if s == "女":
        return Gender.FEMALE
    return None


def _parse_sect(value: Union[str, int, Sect, None]) -> Optional[Sect]:
    if value is None:
        return None
    if isinstance(value, Sect):
        return value
    # 纯数字视为 id
    if isinstance(value, int):
        return sects_by_id.get(value)
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        return sects_by_id.get(int(s))
    return sects_by_name.get(s)


def _parse_technique(value: Union[str, int, Technique, None]) -> Optional[Technique]:
    if value is None:
        return None
    if isinstance(value, Technique):
        return value
    if isinstance(value, int):
        return techniques_by_id.get(value)
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        return techniques_by_id.get(int(s))
    return techniques_by_name.get(s)


def _parse_weapon(value: Union[str, int, Weapon, None]) -> Optional[Weapon]:
    if value is None:
        return None
    if isinstance(value, Weapon):
        return value
    if isinstance(value, int):
        return weapons_by_id.get(value)
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        return weapons_by_id.get(int(s))
    return weapons_by_name.get(s)


def _parse_auxiliary(value: Union[str, int, Auxiliary, None]) -> Optional[Auxiliary]:
    if value is None:
        return None
    if isinstance(value, Auxiliary):
        return value
    if isinstance(value, int):
        return auxiliaries_by_id.get(value)
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        return auxiliaries_by_id.get(int(s))
    return auxiliaries_by_name.get(s)


def _parse_personas(value: Union[str, int, Persona, List[Union[str, int, Persona]], None]) -> Optional[List[Persona]]:
    if value is None:
        return None

    # 统一展开为列表，兼容 OmegaConf 的 ListConfig
    def _as_list(v: object) -> List[object]:
        # Persona 自身视为标量
        if isinstance(v, Persona):
            return [v]
        # 原生序列
        if isinstance(v, (list, tuple, set)):
            return list(v)
        # 兼容 OmegaConf.ListConfig（若存在）
        try:
            from omegaconf import ListConfig  # type: ignore
            if isinstance(v, ListConfig):
                return list(v)
        except Exception:
            pass
        # 其它可迭代但非字符串：尽量展开
        if hasattr(v, "__iter__") and not isinstance(v, (str, bytes)):
            try:
                return list(v)  # type: ignore
            except Exception:
                return [v]
        return [v]

    raw_values = _as_list(value)
    values: List[Union[str, int, Persona]] = raw_values  # type: ignore
    result: List[Persona] = []
    for v in values:
        if isinstance(v, Persona):
            result.append(v)
            continue
        if isinstance(v, int):
            p = personas_by_id.get(v)
            if p is not None:
                result.append(p)
            continue
        s = str(v).strip()
        if not s:
            continue
        if s.isdigit():
            p = personas_by_id.get(int(s))
            if p is not None:
                result.append(p)
        else:
            p = personas_by_name.get(s)
            if p is not None:
                result.append(p)
    # 去重，保持顺序
    seen: set[int] = set()
    unique: List[Persona] = []
    for p in result:
        if p.id in seen:
            continue
        seen.add(p.id)
        unique.append(p)
    return unique if unique else None


def create_avatar_from_request(
    world: World,
    current_month_stamp: MonthStamp,
    *,
    name: Optional[str] = None,
    age: Union[int, Age, None] = None,
    gender: Union[str, Gender, None] = None,
    sect: Union[str, int, Sect, None] = None,
    level: Optional[int] = None,
    pos: Optional[Tuple[int, int]] = None,
    technique: Union[str, int, Technique, None] = None,
    weapon: Union[str, int, Weapon, None] = None,
    auxiliary: Union[str, int, Auxiliary, None] = None,
    personas: Union[str, int, Persona, List[Union[str, int, Persona]], None] = None,
    appearance: Optional[int] = None,
    relations: Optional[List[Dict[str, str]]] = None,
) -> Avatar:
    """
    供前端使用的角色创建入口：支持字符串/ID 参数，且默认不生成亲友关系。
    """
    # 年龄（先取整数年龄，规划阶段只用到 age.age，不依赖 realm）
    if isinstance(age, Age):
        age_years = age.age
    elif isinstance(age, int):
        age_years = max(AGE_MIN, age)
    else:
        age_years = random.randint(AGE_MIN, AGE_MAX)

    tmp_age_for_plan = Age(age_years, CultivationProgress(LEVEL_MIN).realm)
    plan = MortalPlanner.plan(world, name=name or "", age=tmp_age_for_plan, allow_relations=False)

    # 覆盖：性别
    g = _parse_gender(gender)
    if g is not None:
        plan.gender = g

    # 覆盖：宗门
    s = _parse_sect(sect)
    if s is not None:
        plan.sect = s

    # 覆盖：等级
    if isinstance(level, int):
        plan.level = max(LEVEL_MIN, min(LEVEL_MAX, level))

    # 覆盖：坐标
    if isinstance(pos, tuple) and len(pos) == 2:
        x, y = int(pos[0]), int(pos[1])
        # 夹在地图范围内
        x = max(0, min(world.map.width - 1, x))
        y = max(0, min(world.map.height - 1, y))
        plan.pos_x, plan.pos_y = x, y

    # 根据最终等级推导境界，再构造 Age
    final_realm = CultivationProgress(plan.level).realm
    final_age = Age(age_years, final_realm)

    # 生成
    overrides: Dict[str, object] = {}
    tech_obj = _parse_technique(technique)
    if tech_obj is not None:
        overrides["technique"] = tech_obj
    weapon_obj = _parse_weapon(weapon)
    if weapon_obj is not None:
        overrides["weapon"] = weapon_obj
    auxiliary_obj = _parse_auxiliary(auxiliary)
    if auxiliary_obj is not None:
        overrides["auxiliary"] = auxiliary_obj
    pers_list = _parse_personas(personas)
    if pers_list:
        overrides["personas"] = pers_list
    if isinstance(appearance, int):
        overrides["appearance"] = appearance
    
    avatar = AvatarFactory.build_from_plan(
        world,
        current_month_stamp,
        name=name or "",
        age=final_age,
        plan=plan,
        attach_relations=False,
        overrides=overrides if overrides else None,
    )
    
    if relations:
        for rel_item in relations:
            target_id = rel_item.get('target_id')
            rel_type = rel_item.get('relation')
            
            if not target_id or not rel_type:
                continue
                
            # 尝试转为字符串ID
            t_id_str = str(target_id)
            target = world.avatar_manager.avatars.get(t_id_str)
            if not target:
                continue
            
            # 解析关系
            rel_enum = None
            for r in Relation:
                if r.value == rel_type:
                    rel_enum = r
                    break
            
            if rel_enum:
                avatar.set_relation(target, rel_enum)

    return avatar
