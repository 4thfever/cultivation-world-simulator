import random
from typing import List, Optional, Dict

from src.classes.world import World
from src.classes.map import Map
from src.classes.tile import TileType
from src.classes.avatar import Avatar, Gender
from src.classes.calendar import MonthStamp
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.age import Age
from src.utils.names import get_random_name_for_sect, pick_surname_for_sect, get_random_name_with_surname
from src.utils.id_generator import get_avatar_id
from src.classes.sect import Sect
from src.classes.alignment import Alignment
from src.classes.relation import Relation
from src.classes.technique import get_technique_by_sect, attribute_to_root
from src.classes.treasure import treasures_by_sect_id


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


def random_gender() -> Gender:
    return Gender.MALE if random.random() < 0.5 else Gender.FEMALE


def get_new_avatar_from_mortal(world: World, current_month_stamp: MonthStamp, name: str, age: Age) -> Avatar:
    """
    从凡人中来的新修士：最低境界、随机位置，不分配宗门/法宝。
    """
    avatar_id = get_avatar_id()
    birth_month_stamp = current_month_stamp - age.age * 12 + random.randint(0, 11)
    cultivation_progress = CultivationProgress(0)
    pos_x = random.randint(0, world.map.width - 1)
    pos_y = random.randint(0, world.map.height - 1)
    gender = random.choice(list(Gender))
    return Avatar(
        world=world,
        name=name,
        id=avatar_id,
        birth_month_stamp=MonthStamp(birth_month_stamp),
        age=age,
        gender=gender,
        cultivation_progress=cultivation_progress,
        pos_x=pos_x,
        pos_y=pos_y,
    )


def plan_sects_and_relations(n: int, existed_sects: Optional[List[Sect]]) -> tuple[list[Optional[Sect]], list[Optional[Gender]], list[Optional[str]], dict[tuple[int, int], Relation]]:
    """
    规划：
    - 每个索引对应的宗门（可为空，表示散修）；
    - 性别（部分在后续阶段才确定）；
    - 姓氏（用于生成父子同姓/母子异姓等）；
    - 预设关系 (i,j)->Relation（方向遵循 set_relation 的方向）。
    """
    n = int(max(0, n))
    use_sects = bool(existed_sects)
    planned_sect: list[Optional[Sect]] = [None] * n
    if n == 0:
        return planned_sect, [None]*0, [None]*0, {}

    # 宗门均衡分配（约 2/3 成为宗门弟子）
    if use_sects and existed_sects:
        sect_member_target = int(n * SECT_MEMBER_RATIO)  # 目标配额：约2/3为宗门弟子；其余散修
        sect_member_counts_by_id: dict[int, int] = {s.id: 0 for s in existed_sects}
        for i in range(sect_member_target):
            min_count = min(sect_member_counts_by_id.values()) if sect_member_counts_by_id else 0  # 轮转均衡：优先填充人数最少的宗门
            candidates = [s for s in existed_sects if sect_member_counts_by_id.get(s.id, 0) == min_count]
            s = random.choice(candidates)
            sect_member_counts_by_id[s.id] += 1
            planned_sect[i] = s
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

    family_pairs_budget = max(0, n // FAMILY_PAIR_CAP_DIV)  # 家庭上限：约每6人1对；触发概率见常量
    for _ in range(family_pairs_budget):
        if random.random() < FAMILY_TRIGGER_PROB:
            pair = _reserve_pair()
            if pair is None:
                break
            a, b = pair
            if random.random() < FATHER_CHILD_PROB:
                # 父子：同姓；父为男
                surname = pick_surname_for_sect(planned_sect[a] or planned_sect[b])
                planned_surname[a] = surname
                planned_surname[b] = surname
                planned_gender[a] = Gender.MALE
                planned_relations[(a, b)] = Relation.PARENT
            else:
                # 母子：异姓；母为女
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
                planned_relations[(mother, child)] = Relation.PARENT

    leftover = unused_indices[:]

    # — 道侣 —
    random.shuffle(leftover)
    lovers_budget = max(0, n // LOVERS_PAIR_CAP_DIV)  # 道侣预算，两两配对，强制异性
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
                    planned_relations[(a, b)] = Relation.LOVERS
            lovers_budget -= 1
        i += 2

    # — 师徒（同宗门）—
    if use_sects and existed_sects:
        members_by_sect: dict[int, list[int]] = {s.id: [] for s in existed_sects}
        for idx, sect in enumerate(planned_sect):
            if sect is not None:
                members_by_sect.setdefault(sect.id, []).append(idx)
        for _sect_id, members in members_by_sect.items():
            random.shuffle(members)
            j = 0
            while j + 1 < len(members):
                if random.random() < MASTER_PAIR_PROB:  # 师徒：同宗门内指定概率，两两配对
                    master, apprentice = members[j], members[j + 1]
                    if (master, apprentice) not in planned_relations and (apprentice, master) not in planned_relations:
                        planned_relations[(master, apprentice)] = Relation.MASTER
                j += 2

    # — 朋友/仇人 —
    all_indices = list(range(n))
    random.shuffle(all_indices)
    k = 0
    while k + 1 < len(all_indices):  # 朋友/仇人互斥
        a, b = all_indices[k], all_indices[k + 1]
        if (a, b) in planned_relations or (b, a) in planned_relations:
            k += 2
            continue
        r = random.random()
        if r < FRIEND_PROB:
            planned_relations[(a, b)] = Relation.FRIEND
        elif r < FRIEND_PROB + ENEMY_PROB:
            planned_relations[(a, b)] = Relation.ENEMY
        k += 2

    # 性别兜底
    for i in range(n):
        if planned_gender[i] is None:
            planned_gender[i] = random_gender()

    return planned_sect, planned_gender, planned_surname, planned_relations


def build_avatars_from_plan(
    world: World,
    current_month_stamp: MonthStamp,
    planned_sect: list[Optional[Sect]],
    planned_gender: list[Optional[Gender]],
    planned_surname: list[Optional[str]],
    planned_relations: dict[tuple[int, int], Relation],
) -> dict[str, Avatar]:
    """
    根据规划生成实际 Avatar，并写入关系与宗门法宝/灵根映射。
    """
    n = len(planned_sect)
    width, height = world.map.width, world.map.height

    ages: list[int] = [random.randint(AGE_MIN, AGE_MAX) for _ in range(n)]
    levels: list[int] = [random.randint(LEVEL_MIN, LEVEL_MAX) for _ in range(n)]

    # 调整父子年龄差（父母比子女至少大PARENT_MIN_DIFF，最大PARENT_AGE_CAP）
    for (a, b), rel in list(planned_relations.items()):
        if rel is Relation.PARENT:
            if ages[a] <= ages[b] + (PARENT_MIN_DIFF - 1):
                ages[a] = min(PARENT_AGE_CAP, ages[b] + random.randint(PARENT_MIN_DIFF, PARENT_MAX_DIFF))

    # 调整父母-子女等级差（通常父母更强）
    for (a, b), rel in list(planned_relations.items()):
        if rel is Relation.PARENT:
            # 至少略高于子女
            if levels[a] <= levels[b]:
                levels[a] = min(LEVEL_MAX, levels[b] + 1)
            # 满足最小差值要求
            if levels[a] < levels[b] + PARENT_LEVEL_MIN_DIFF:
                levels[a] = min(LEVEL_MAX, levels[b] + PARENT_LEVEL_MIN_DIFF + random.randint(0, PARENT_LEVEL_EXTRA_MAX))

    # 调整师徒级差（师傅≥徒弟 MASTER_LEVEL_MIN_DIFF）
    for (a, b), rel in list(planned_relations.items()):
        if rel is Relation.MASTER:
            if levels[a] < levels[b] + MASTER_LEVEL_MIN_DIFF:
                levels[a] = min(LEVEL_MAX, levels[b] + MASTER_LEVEL_MIN_DIFF + random.randint(0, MASTER_LEVEL_EXTRA_MAX))

    avatars_by_index: list[Avatar] = [None] * n  # type: ignore
    avatars_by_id: dict[str, Avatar] = {}

    sect_treasure_assigned: Dict[int, bool] = {}

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

        avatar.tile = world.map.get_tile(x, y)

        if sect is not None:
            avatar.alignment = sect.alignment
            avatar.technique = get_technique_by_sect(sect)
            treasure = treasures_by_sect_id.get(sect.id)
            if treasure is not None and not sect_treasure_assigned.get(sect.id, False):  # 每宗门仅发放一次所属法宝
                avatar.treasure = treasure
                sect_treasure_assigned[sect.id] = True

        if avatar.technique is not None:
            mapped = attribute_to_root(avatar.technique.attribute)
            if mapped is not None:  # 功法属性→默认灵根映射（邪不映射）
                avatar.root = mapped

        avatars_by_index[i] = avatar
        avatars_by_id[avatar.id] = avatar

    for (a, b), relation in planned_relations.items():
        av_a = avatars_by_index[a]
        av_b = avatars_by_index[b]
        if av_a is None or av_b is None or av_a is av_b:
            continue
        av_a.set_relation(av_b, relation)

    return avatars_by_id


def make_avatars(
    world: World,
    count: int = 12,
    current_month_stamp: MonthStamp = MonthStamp(100 * 12),
    existed_sects: Optional[List[Sect]] = None,
) -> dict[str, Avatar]:
    n = int(max(0, count))
    if n == 0:
        return {}
    # 只负责编排：先规划，再生成
    planned_sect, planned_gender, planned_surname, planned_relations = plan_sects_and_relations(n, existed_sects)
    return build_avatars_from_plan(world, current_month_stamp, planned_sect, planned_gender, planned_surname, planned_relations)


