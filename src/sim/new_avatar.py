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
from src.utils.names import get_random_name_for_sect
from src.utils.id_generator import get_avatar_id
from src.classes.sect import Sect
from src.classes.alignment import Alignment
from src.classes.relation import Relation
from src.classes.technique import get_technique_by_sect, attribute_to_root
from src.classes.treasure import treasures_by_sect_id


def random_gender() -> Gender:
    return Gender.MALE if random.random() < 0.5 else Gender.FEMALE


def get_new_avatar_from_ordinary(world: World, current_month_stamp: MonthStamp, name: str, age: Age) -> Avatar:
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


def make_avatars(
    world: World,
    count: int = 12,
    current_month_stamp: MonthStamp = MonthStamp(100 * 12),
    existed_sects: Optional[List[Sect]] = None,
) -> dict[str, Avatar]:
    avatars: dict[str, Avatar] = {}
    width, height = world.map.width, world.map.height

    num_total = int(count)
    use_sects = bool(existed_sects)
    # 约 2/3 为宗门弟子，1/3 为散修
    sect_member_target = int(num_total * 2 / 3) if use_sects else 0

    # 统计将要分配的宗门成员数量（用于均分）
    sect_member_count = 0
    sect_member_counts_by_id: dict[int, int] = {s.id: 0 for s in existed_sects} if existed_sects else {}

    # 本局中“已给出宗门法宝”的标记，确保每个宗门最多一件且仅首次分配
    sect_treasure_assigned: Dict[int, bool] = {}

    for i in range(count):
        age_years = random.randint(16, 60)
        birth_month_stamp = current_month_stamp - age_years * 12 + random.randint(0, 11)
        gender = random_gender()

        # 分配宗门或散修
        assigned_sect: Optional[Sect] = None
        if use_sects and sect_member_count < sect_member_target and existed_sects:
            min_count = min(sect_member_counts_by_id.values()) if sect_member_counts_by_id else 0
            candidates = [s for s in existed_sects if sect_member_counts_by_id.get(s.id, 0) == min_count]
            assigned_sect = random.choice(candidates)
            sect_member_counts_by_id[assigned_sect.id] = sect_member_counts_by_id.get(assigned_sect.id, 0) + 1
            sect_member_count += 1

        name = get_random_name_for_sect(gender, assigned_sect)

        level = random.randint(0, 120)
        cultivation_progress = CultivationProgress(level)
        age = Age(age_years, cultivation_progress.realm)

        # 出生点：
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)

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
            sect=assigned_sect,
        )

        avatar.tile = world.map.get_tile(x, y)

        if assigned_sect is not None:
            avatar.alignment = assigned_sect.alignment
            avatar.technique = get_technique_by_sect(assigned_sect)

            # 若该宗门有法宝，且本局尚未分配过，则给该宗门第一个生成的弟子分配法宝
            treasure = treasures_by_sect_id.get(assigned_sect.id)
            if treasure is not None and not sect_treasure_assigned.get(assigned_sect.id, False):
                avatar.treasure = treasure
                sect_treasure_assigned[assigned_sect.id] = True

        mapped_root = attribute_to_root(avatar.technique.attribute)
        if mapped_root is not None:
            avatar.root = mapped_root

        avatars[avatar.id] = avatar

    # 简单关系样例
    avatar_list = list(avatars.values())
    if len(avatar_list) >= 2:
        avatar_list[0].set_relation(avatar_list[1], Relation.ENEMY)
    if len(avatar_list) >= 4:
        avatar_list[2].set_relation(avatar_list[3], Relation.FRIEND)
    if len(avatar_list) >= 6:
        avatar_list[4].set_relation(avatar_list[5], Relation.MASTER)
    if len(avatar_list) >= 8:
        avatar_list[6].set_relation(avatar_list[7], Relation.LOVERS)

    return avatars


