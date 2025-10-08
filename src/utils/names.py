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
    "逍遥", "无极", "天行", "凌云", "破晓", "斩风", "御剑", "追星", "问天", "寻仙",
    "玄机", "天骄", "无双", "惊鸿", "绝尘", "傲天", "剑心", "风华", "无尘", "天启",
    "墨染", "凌霄", "天羽", "星辰", "飞雪", "幽冥", "天籁", "破军", "神威", "无痕",
    "天策", "剑魂", "风流", "绝世", "天命", "无敌", "傲骨", "星河", "天机", "风云",
    "天成", "无忧", "破空", "凌波", "天涯", "风尘", "玄武", "天阙", "无量", "剑仙",
    # 新增的50个平凡仙侠名字
    "云舒", "风平", "志远", "明轩", "建安", "文昭", "德华", "志明", "文涛", "建国",
    "石坚", "水清", "木华", "火旺", "土安", "金贵", "银河", "铜山", "铁柱", "钢强",
    "春生", "夏华", "秋实", "冬雪", "东升", "西落", "南飞", "北望", "中正", "和平",
    "安然", "从容", "淡然", "自在", "清净", "宁静", "平和", "温良", "恭俭", "让人",
    "文雅", "斯文", "儒雅", "温文", "和善", "慈祥", "宽厚", "敦厚", "朴实", "忠厚"
]

FEMALE_GIVEN_NAMES = [
    # 女性名字 (100个)
    "如雪", "若梦", "凝香", "紫霞", "月华", "清音", "蝶舞", "花颜", "雅韵", "诗涵",
    "静雯", "慕蓉", "婉儿", "柔情", "倾城", "红颜", "如烟", "妙音", "冰心", "玉颜",
    "如玉", "清影", "梦瑶", "紫嫣", "霜华", "若水", "青莲", "雪儿", "慧心", "素手",
    "如意", "诗雨", "梦蝶", "紫萱", "冰莲", "若兰", "清雅", "雪梅", "慕雪", "天音",
    "如风", "诗韵", "梦云", "紫烟", "冰雪", "若霜", "清秋", "雪莲", "慕凝", "天香",
    # 新增的50个平凡仙侠名字
    "小雨", "春花", "夏草", "秋叶", "冬梅", "东篱", "西园", "南风", "北雁", "中庭",
    "翠云", "红梅", "绿柳", "黄菊", "白莲", "紫薇", "粉桃", "青竹", "蓝兰", "银杏",
    "静好", "安然", "从容", "淡雅", "温柔", "贤慧", "端庄", "淑雅", "文静", "秀丽",
    "春兰", "夏荷", "秋菊", "冬梅", "晨曦", "暮霞", "朝阳", "夕阳", "正午", "子夜",
    "小芸", "小娟", "小红", "小翠", "小兰", "小梅", "小雪", "小霞", "小燕", "小凤"
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