import random
from typing import Optional
from src.classes.avatar import Gender
from src.classes.sect import Sect

"""
仙侠风格姓名数据库
包含50个姓氏和200个名字（男女各100个）
"""

# 50个仙侠风格的姓氏
SURNAMES = [
    "司马", "慕容", "上官", "独孤", "东方", "南宫", "西门", "北冥", "欧阳", "夏侯",
    "令狐", "诸葛", "皇甫", "公孙", "轩辕", "百里", "呼延", "闻人", "长孙", "段干",
    "云", "叶", "夜", "风", "霜", "雪", "星", "月", "冷", "凌",
    "苏", "陆", "萧", "林", "君", "墨", "白", "顾", "秦", "楚",
    "赵", "唐", "韩", "魏", "宋", "齐", "燕", "晋", "陈", "李"
]

# 200个仙侠风格的名字
MALE_GIVEN_NAMES = [
    # 男性名字 (100个)
    "逍遥", "无极", "天行", "凌云", "破晓", "斩风", "御风", "追星", "景天", "清源",
    "玄机", "天骄", "无双", "惊鸿", "绝尘", "傲天", "剑心", "风华", "无尘", "天启",
    "墨染", "凌霄", "天羽", "星辰", "飞雪", "幽冥", "天籁", "破军", "神威", "无痕",
    "天策", "剑魂", "风流", "绝世", "天命", "扶摇", "傲骨", "星河", "天机", "风云",
    "天成", "无忧", "破空", "凌波", "天涯", "风尘", "玄凌", "天阙", "元衡", "剑尘",
    # 新增的50个仙侠风格名字
    "云霄", "青玄", "玄霄", "沧澜", "断尘", "清尘", "承影", "寒月", "晨旭", "破阵",
    "北辰", "南斗", "青冥", "太虚", "玄空", "长生", "寒川", "寒星", "惊雷", "苍穹",
    "辰渊", "赤霄", "炎霆", "逐霜", "啸月", "逐风", "青穹", "玄霜", "白羽", "青羽",
    "紫霄", "云衡", "星衡", "沧海", "霆骁", "擎天", "孤川", "孤鸿", "墨白", "清越",
    "青霖", "驭风", "重楼", "寒洲", "星阑", "子陵", "元诚", "行舟", "凌寒", "青霜"
]

FEMALE_GIVEN_NAMES = [
    # 女性名字 (100个)
    "如雪", "若梦", "凝香", "紫霞", "月华", "清音", "蝶舞", "花颜", "雅韵", "诗涵",
    "静雯", "慕蓉", "婉儿", "柔情", "霓裳", "晚颜", "如烟", "妙音", "冰心", "玉颜",
    "如玉", "清影", "梦瑶", "紫嫣", "霜华", "若水", "青莲", "雪儿", "慧心", "素衣",
    "如意", "诗雨", "梦蝶", "紫萱", "冰莲", "若兰", "清雅", "雪梅", "慕雪", "天音",
    "如风", "诗韵", "梦云", "紫烟", "冰雪", "若霜", "清秋", "雪莲", "慕凝", "天香",
    # 新增的50个仙侠风格名字
    "月影", "青衣", "素心", "霜凝", "清欢", "暮雪", "月灵", "云岚", "灵汐", "冷月",
    "冰瑶", "玄月", "青璇", "紫凝", "雪鸢", "绛霓", "绯烟", "流苏", "墨琴", "断晴",
    "雨霖", "归晚", "临渊", "婵娟", "听雪", "凝霜", "岚烟", "疏影", "清宵", "流萤",
    "夜阑", "素锦", "锦瑟", "孤鸢", "青萝", "碧落", "飞霜", "无霜", "明玥", "皎月",
    "醉花", "半夏", "初霁", "白芷", "青黛", "灵芸", "绮罗", "初晴", "寒烟", "月珑"
]

def get_random_male_name():
    """
    获取随机男性全名
    """
    return random.choice(SURNAMES) + random.choice(MALE_GIVEN_NAMES)

def get_random_female_name():
    """
    获取随机女性全名
    """
    return random.choice(SURNAMES) + random.choice(FEMALE_GIVEN_NAMES)

def get_random_name(gender: Gender) -> str:
    """
    获取随机全名
    """
    if gender == Gender.MALE:
        return get_random_male_name()
    else:
        return get_random_female_name()


def get_random_name_for_sect(gender: Gender, sect: Optional[Sect]) -> str:
    """
    基于宗门生成姓名：优先使用宗门常见姓与性别对应名，若缺失则回退到全局库。
    """
    if sect is None:
        return get_random_name(gender)
    surnames = sect.sect_surnames or SURNAMES
    if gender == Gender.MALE:
        given_pool = sect.male_sect_given_names or MALE_GIVEN_NAMES
    else:
        given_pool = sect.female_sect_given_names or FEMALE_GIVEN_NAMES
    return random.choice(surnames) + random.choice(given_pool)