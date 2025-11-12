import random
from typing import List, Optional, Dict, Tuple, Union

from src.classes.world import World
from src.classes.map import Map
from src.classes.tile import TileType
from src.classes.avatar import Avatar, Gender
from src.classes.appearance import get_appearance_by_level
from src.classes.calendar import MonthStamp
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.age import Age
from src.classes.name import get_random_name_for_sect, pick_surname_for_sect, get_random_name_with_surname
from src.utils.id_generator import get_avatar_id
from src.classes.sect import Sect, sects_by_id, sects_by_name
from src.classes.alignment import Alignment
from src.classes.relation import Relation
from src.classes.technique import get_technique_by_sect, attribute_to_root, Technique, techniques_by_id, techniques_by_name
from src.classes.weapon import Weapon, weapons_by_id, weapons_by_name
from src.classes.auxiliary import Auxiliary, auxiliaries_by_id, auxiliaries_by_name
from src.classes.persona import Persona, personas_by_id, personas_by_name


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


def get_new_avatar_from_mortal(world: World, current_month_stamp: MonthStamp, name: str, age: Age) -> Avatar:
    """
    从凡人中来的新修士：先规划宗门/关系，再生成实际角色；不分配宗门法宝。
    """
    # 规划
    plan = plan_mortal(world, name=name, age=age)
    # 生成
    return build_mortal_from_plan(world, current_month_stamp, name=name, age=age, plan=plan)


class MortalPlan:
    def __init__(self):
        self.gender: Optional[Gender] = None
        self.sect: Optional[Sect] = None
        self.surname: Optional[str] = None
        self.parent_avatar: Optional[Avatar] = None
        self.master_avatar: Optional[Avatar] = None
        self.level: int = max(LEVEL_MIN, random.randint(LEVEL_MIN, NEW_MORTAL_LEVEL_MAX))
        self.pos_x: int = 0
        self.pos_y: int = 0


def _pick_any_sect(existed_sects: Optional[List[Sect]]) -> Optional[Sect]:
    if not existed_sects:
        return None
    return random.choice(existed_sects)


def _pick_sects_balanced(existed_sects: List[Sect], k: int) -> list[Optional[Sect]]:
    """
    从宗门列表中“均衡”挑选 k 个位置的宗门引用：
    - 每次选择当前计数最少的宗门之一；
    - 返回长度为 k 的列表；
    """
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


def plan_mortal(world: World, name: str, age: Age, *, existed_sects: Optional[List[Sect]] = None, existing_avatars: Optional[List[Avatar]] = None) -> MortalPlan:
    """
    规划新凡人的宗门与关系（父母/师徒），以及取名所需的姓氏等。
    """
    plan = MortalPlan()

    # 性别与位置
    plan.gender = random_gender()
    plan.pos_x = random.randint(0, world.map.width - 1)
    plan.pos_y = random.randint(0, world.map.height - 1)

    # 数据源
    if existing_avatars is None:
        existing_avatars = list(world.avatar_manager.avatars.values())
    if existed_sects is None:
        # 若 run 层已抽样，可传入；否则直接从世界可见宗门中随机（此处简单选择）
        try:
            from src.classes.sect import sects_by_id as _sects_by_id
            existed_sects = list(_sects_by_id.values())
        except Exception:
            existed_sects = []

    # 5.b 宗门（先于关系确定，便于后续取名/师徒）
    if random.random() < NEW_MORTAL_SECT_PROB:
        # 单人场景：挑1个宗门，复用均衡逻辑的退化形式
        picked = _pick_sects_balanced(existed_sects or [], 1)
        plan.sect = picked[0] if picked else None

    # 5.a 父/母：从现有角色中挑选足够年长者
    if random.random() < NEW_MORTAL_PARENT_PROB and existing_avatars:
        candidates: list[Avatar] = []
        for av in existing_avatars:
            if av.age.age >= age.age + PARENT_MIN_DIFF:
                candidates.append(av)
        if candidates:
            parent = random.choice(candidates)
            plan.parent_avatar = parent
            # 姓氏偏好：父男同姓，母女异姓（仅在 name 为空时影响）
            if not name:
                if parent.gender is Gender.MALE:
                    plan.surname = pick_surname_for_sect(plan.sect or parent.sect)
                else:
                    # 母为女：尽量不同姓
                    mom_surname = pick_surname_for_sect(plan.sect or parent.sect)
                    # 迭代挑一个不同姓
                    for _ in range(5):
                        s = pick_surname_for_sect(plan.sect)
                        if s != mom_surname:
                            plan.surname = s
                            break

            # 父母更强的趋势：控制新人的 level 不超过父母太多
            if parent.cultivation_progress.level + PARENT_LEVEL_MIN_DIFF > plan.level:
                plan.level = max(LEVEL_MIN, min(parent.cultivation_progress.level - 1, NEW_MORTAL_LEVEL_MAX))

    # 5.c 师徒（仅当选中了宗门）
    if plan.sect is not None and random.random() < NEW_MORTAL_MASTER_PROB and existing_avatars:
        same_sect = [av for av in existing_avatars if av.sect is plan.sect]
        if same_sect:
            stronger = [av for av in same_sect if av.cultivation_progress.level >= plan.level + MASTER_LEVEL_MIN_DIFF]
            if stronger:
                plan.master_avatar = random.choice(stronger)

    return plan


def build_mortal_from_plan(world: World, current_month_stamp: MonthStamp, *, name: str, age: Age, plan: MortalPlan) -> Avatar:
    """
    根据规划创建新凡人，并写入父母/师徒关系；不分配宗门法宝。
    取名规则：尊重传入 name；若为空，则按规划的 sect/surname 生成。
    """
    # 名称
    if name:
        final_name = name
    else:
        if plan.surname:
            final_name = get_random_name_with_surname(plan.gender, plan.surname, plan.sect)
        else:
            final_name = get_random_name_for_sect(plan.gender, plan.sect)

    # 出生时间与位置
    birth_month_stamp = current_month_stamp - age.age * 12 + random.randint(0, 11)

    # 基础对象
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

    # 位置刷新
    avatar.tile = world.map.get_tile(avatar.pos_x, avatar.pos_y)
    
    # 分配宗门职位（根据境界）
    _assign_sect_rank(avatar, world)

    # 写关系（父母/师徒）；不发放宗门法宝
    if plan.parent_avatar is not None:
        plan.parent_avatar.set_relation(avatar, Relation.PARENT)
    if plan.master_avatar is not None:
        plan.master_avatar.set_relation(avatar, Relation.MASTER)

    # 功法将由 __post_init__ 自动基于 sect 设置；灵根映射同 make_avatars 流程
    if avatar.technique is not None:
        mapped = attribute_to_root(avatar.technique.attribute)
        if mapped is not None:
            avatar.root = mapped

    return avatar


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
        planned_sect[:sect_member_target] = _pick_sects_balanced(existed_sects, sect_member_target)
        # 打散次序，避免前段集中
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
            # 每个宗门只分配一个法宝级兵器给最强者（但不在这里分配，而是让奇遇系统处理）
            # 宗门成员初始都是普通兵器

        if avatar.technique is not None:
            mapped = attribute_to_root(avatar.technique.attribute)
            if mapped is not None:  # 功法属性→默认灵根映射（邪不映射）
                avatar.root = mapped

        avatars_by_index[i] = avatar
        avatars_by_id[avatar.id] = avatar
    
    # 批量分配宗门职位（需要在所有avatar创建后统一处理，以正确检查掌门唯一性）
    _assign_sect_ranks_batch(avatars_by_index, world)

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
    from src.utils.config import CONFIG

    n = int(max(0, count))
    if n == 0:
        return {}

    avatars: dict[str, Avatar] = {}

    # 先生成一个“defined_avatar”（若配置存在）
    defined = getattr(CONFIG, "defined_avatar", None)
    used = 0
    if defined is not None:
        surname = str(getattr(defined, "surname", "") or "").strip()
        given_name = str(getattr(defined, "given_name", "") or "").strip()
        defined_name = f"{surname}{given_name}"
        da = get_new_avatar_with_config(
            world,
            current_month_stamp,
            name=defined_name,
            age=int(getattr(defined, "age", 0) or 0) if str(getattr(defined, "age", "")).strip() else None,
            gender=str(getattr(defined, "gender", "")).strip() or None,
            sect=getattr(defined, "sect", None),
            level=int(getattr(defined, "level", 0) or 0) if str(getattr(defined, "level", "")).strip() else None,
            appearance=int(getattr(defined, "appearance", 0) or 0) if str(getattr(defined, "appearance", "")).strip() else None,
            technique=getattr(defined, "technique", None),
            weapon=getattr(defined, "weapon", None),
            auxiliary=getattr(defined, "auxiliary", None),
            personas=getattr(defined, "personas", None),
        )
        avatars[da.id] = da
        used = 1


    # 剩余随机编排
    rest = max(0, n - used)
    if rest > 0:
        planned_sect, planned_gender, planned_surname, planned_relations = plan_sects_and_relations(rest, existed_sects)
        random_avatars = build_avatars_from_plan(world, current_month_stamp, planned_sect, planned_gender, planned_surname, planned_relations)
        avatars.update(random_avatars)

    return avatars



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


def get_new_avatar_with_config(
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
) -> Avatar:
    """
    创建一个可配置的新角色：
    - 若未提供参数，则复用 get_new_avatar_from_mortal 的随机策略（通过 plan_mortal 实现）。
    - 支持字符串参数：gender 仅支持 "男/女"；sect/technique/weapon/auxiliary/persona 可用名称或数字ID。

    参数：
    - name: 角色名；为空则根据宗门与姓氏自动生成
    - age: 年龄（int）或 Age；未提供时随机
    - gender: 性别（Gender 或 字符串）
    - sect: 宗门（Sect 或 名称/ID）
    - level: 等级（0~120）；未提供时随机
    - pos: 初始坐标 (x, y)；未提供时随机
    - technique: 指定功法
    - weapon: 指定兵器
    - auxiliary: 指定辅助装备
    - personas: 指定个性（单个或列表）
    """
    # 年龄（先取整数年龄，规划阶段只用到 age.age，不依赖 realm）
    if isinstance(age, Age):
        age_years = age.age
    elif isinstance(age, int):
        age_years = max(AGE_MIN, age)
    else:
        age_years = random.randint(AGE_MIN, AGE_MAX)

    # 先做一次规划，之后用传入参数覆盖
    tmp_age_for_plan = Age(age_years, CultivationProgress(LEVEL_MIN).realm)
    plan = plan_mortal(world, name=name or "", age=tmp_age_for_plan)

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
    avatar = build_mortal_from_plan(world, current_month_stamp, name=name or "", age=final_age, plan=plan)

    # 覆盖：功法/兵器/辅助装备/个性
    tech_obj = _parse_technique(technique)
    if tech_obj is not None:
        avatar.technique = tech_obj
        mapped = attribute_to_root(tech_obj.attribute)
        if mapped is not None:
            avatar.root = mapped

    weapon_obj = _parse_weapon(weapon)
    if weapon_obj is not None:
        avatar.weapon = weapon_obj

    auxiliary_obj = _parse_auxiliary(auxiliary)
    if auxiliary_obj is not None:
        avatar.auxiliary = auxiliary_obj

    pers_list = _parse_personas(personas)
    if pers_list is not None and len(pers_list) > 0:
        avatar.personas = pers_list

    # 覆盖：外貌/颜值
    if isinstance(appearance, int):
        avatar.appearance = get_appearance_by_level(appearance)

    return avatar


def _assign_sect_rank(avatar: Avatar, world: World) -> None:
    """
    为单个avatar分配宗门职位（根据境界）
    处理掌门唯一性：如果该宗门已有掌门，元婴修士只能当长老
    
    Args:
        avatar: 要分配职位的角色
        world: 世界对象
    """
    # 散修无职位
    if avatar.sect is None:
        avatar.sect_rank = None
        return
    
    from src.classes.sect_ranks import get_rank_from_realm, sect_has_patriarch, SectRank
    
    # 根据境界获取对应职位
    rank = get_rank_from_realm(avatar.cultivation_progress.realm)
    
    # 如果是掌门，检查该宗门是否已有掌门
    if rank == SectRank.Patriarch:
        if sect_has_patriarch(avatar):
            # 已有掌门，降为长老
            rank = SectRank.Elder
    
    avatar.sect_rank = rank


def _assign_sect_ranks_batch(avatars: List[Avatar], world: World) -> None:
    """
    批量为avatars分配宗门职位
    确保每个宗门只有一个掌门（按境界等级优先，同境界随机）
    
    Args:
        avatars: 要分配职位的角色列表
        world: 世界对象
    """
    from src.classes.sect_ranks import get_rank_from_realm, SectRank
    
    # 先为所有人分配基础职位
    for avatar in avatars:
        if avatar is None:
            continue
        if avatar.sect is None:
            avatar.sect_rank = None
        else:
            avatar.sect_rank = get_rank_from_realm(avatar.cultivation_progress.realm)
    
    # 收集每个宗门的元婴修士（应为掌门的候选人）
    sect_nascent_souls: Dict[int, List[Avatar]] = {}
    for avatar in avatars:
        if avatar is None or avatar.sect is None:
            continue
        if avatar.sect_rank == SectRank.Patriarch:
            sect_id = avatar.sect.id
            if sect_id not in sect_nascent_souls:
                sect_nascent_souls[sect_id] = []
            sect_nascent_souls[sect_id].append(avatar)
    
    # 检查world中已存在的掌门
    existing_patriarchs: Dict[int, bool] = {}
    for other in world.avatar_manager.avatars.values():
        if other.sect is not None and other.sect_rank == SectRank.Patriarch:
            existing_patriarchs[other.sect.id] = True
    
    # 为每个宗门选择唯一掌门
    for sect_id, candidates in sect_nascent_souls.items():
        # 如果world中已有掌门，所有候选人都降为长老
        if existing_patriarchs.get(sect_id, False):
            for avatar in candidates:
                avatar.sect_rank = SectRank.Elder
        else:
            # 选择等级最高的作为掌门，其余降为长老
            candidates.sort(key=lambda av: av.cultivation_progress.level, reverse=True)
            # 第一个保持掌门
            for avatar in candidates[1:]:
                avatar.sect_rank = SectRank.Elder

