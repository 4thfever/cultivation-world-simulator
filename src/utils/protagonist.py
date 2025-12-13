from typing import List, Dict, Optional
import random
from src.classes.avatar import Avatar
from src.classes.world import World
from src.classes.calendar import MonthStamp
from src.classes.relation import Relation
from src.sim.new_avatar import create_avatar_from_request

# ==========================================
# 1. 主角与配角配置列表
# ==========================================
protagonist_configs = [
    # ------------------- 赤心巡天 -------------------
    {
        "key": "jiang_wang",
        "name": "姜望",
        "desc": "《赤心巡天》主角，赤心剑修",
        "params": {
            "gender": "男",
            "age": 22,
            "level": 60,         # 金丹/外楼
            "sect": 1,           # 明心剑宗
            "technique": 30,     # 草字剑诀 (剑道至高)
            "weapon": 3007,      # 诛仙剑 (长相思)
            "auxiliary": 3011,   # 六道剑匣 (随身剑匣)
            "personas": ["心机深沉", "极端正义", "剑痴"],
            "appearance": 8,
        }
    },
    # ------------------- 凡人修仙传 -------------------
    {
        "key": "han_li",
        "name": "韩立",
        "desc": "《凡人修仙传》主角，韩老魔",
        "params": {
            "gender": "男",
            "age": 120,
            "level": 90,         # 合体/大乘
            "sect": 9,           # 千帆城 (商会/散修流)
            "technique": 33,     # 青帝长生诀 (木系至高)
            "weapon": 3001,      # 青竹蜂云剑 (本命法宝)
            "auxiliary": 3003,   # 掌天瓶 (催熟万物)
            "personas": ["惜命", "心机深沉", "药师"],
            "appearance": 15,
        }
    },
    {
        "key": "li_fei_yu",
        "name": "厉飞雨",
        "desc": "《凡人修仙传》韩立挚友，杀人放火厉飞雨",
        "params": {
            "gender": "男",
            "age": 25,           # 英年早逝形象
            "level": 30,         # 筑基期 (对应凡人武学巅峰+修仙入门)
            "sect": 14,          # 噬魔宗 (透支潜力，杀伐果断)
            "technique": 28,     # 燃血大法 (燃烧气血)
            "weapon": 2011,      # 血饮狂刀 (杀气腾腾)
            "auxiliary": 2003,   # 人参果(伪) (增加寿命)
            "personas": ["狠辣", "好斗", "忠诚"],
            "appearance": 10,
        }
    },
    # ------------------- 斗破苍穹 -------------------
    {
        "key": "xiao_yan",
        "name": "萧炎",
        "desc": "《斗破苍穹》主角，炎帝",
        "params": {
            "gender": "男",
            "age": 30,
            "level": 110,        # 斗帝
            "sect": 5,           # 朱勾宗 (火系/炼器/暗杀)
            "technique": 42,     # 焚决 (吞噬异火)
            "weapon": 2012,      # 玄铁重剑 (玄重尺)
            "auxiliary": 3008,   # 八卦炉 (药老/炼药)
            "personas": ["炼丹师", "气运之子", "复仇"],
            "appearance": 10,
        }
    },
    {
        "key": "nalan_yanran",
        "name": "纳兰嫣然",
        "desc": "《斗破苍穹》云岚宗少宗主，退婚女",
        "params": {
            "gender": "女",
            "age": 28,
            "level": 70,         # 斗皇/斗宗
            "sect": 1,           # 明心剑宗 (云岚宗对应)
            "technique": 56,     # 纵地金光 (风系身法)
            "weapon": 2013,      # 紫薇软剑 (轻灵剑法)
            "auxiliary": 2007,   # 踏云靴 (身法加成)
            "personas": ["霸道", "剑修", "刻薄"],
            "appearance": 35,    # 美貌御姐
        }
    },
    # ------------------- 一世之尊 -------------------
    {
        "key": "meng_qi",
        "name": "孟奇",
        "desc": "《一世之尊》主角，雷刀狂僧",
        "params": {
            "gender": "男",
            "age": 25,
            "level": 80,
            "sect": 7,           # 镇魂宗 (肉身/禅意)
            "technique": 49,     # 神霄雷法 (雷法正宗)
            "weapon": 2011,      # 血饮狂刀 (雷刀/霸王绝刀)
            "auxiliary": 2008,   # 菩提子 (悟性/诸果之因)
            "personas": ["穿越者", "好斗", "外向"],
            "appearance": 12,
        }
    },
    # ------------------- 掌门路 -------------------
    {
        "key": "qi_xiu",
        "name": "齐休",
        "desc": "《掌门路》主角，全知掌门",
        "params": {
            "gender": "男",
            "age": 150,
            "level": 70,
            "sect": 3,           # 水镜宗 (全知/观测)
            "technique": 36,     # 虚空经 (全知观测)
            "weapon": 2005,      # 桃花扇 (本命物)
            "auxiliary": 3002,   # 昆仑镜 (全知之眼)
            "personas": ["心机深沉", "疑心重", "穿越者"],
            "appearance": 25,
        }
    },
    # ------------------- 神秘复苏 -------------------
    {
        "key": "yang_jian",
        "name": "杨间",
        "desc": "《神秘复苏》主角，鬼眼",
        "params": {
            "gender": "男",
            "age": 20,
            "level": 75,
            "sect": 8,           # 幽魂噬影宗 (鬼影/灵异)
            "technique": 51,     # 幽冥鬼爪 (鬼影袭击)
            "weapon": 3004,      # 弑神枪 (发裂长枪/棺材钉)
            "auxiliary": 2006,   # 源天神眼 (鬼眼)
            "personas": ["淡漠", "心机深沉", "狠辣"],
            "appearance": 18,
        }
    },
    # ------------------- 道诡异仙 -------------------
    {
        "key": "li_huo_wang",
        "name": "李火旺",
        "desc": "《道诡异仙》主角，心素",
        "params": {
            "gender": "男",
            "age": 19,
            "level": 65,
            "sect": 14,          # 噬魔宗
            "technique": 28,     # 燃血大法 (自残修仙)
            "weapon": 1001,      # 凡品剑 (红中)
            "auxiliary": 2008,   # 菩提子 (清心压制)
            "personas": ["无常", "好斗", "忠诚"],
            "appearance": 20,
        }
    },
    # ------------------- 玄鉴仙族 -------------------
    {
        "key": "li_tong_ya",
        "name": "李通崖",
        "desc": "《玄鉴仙族》老祖",
        "params": {
            "gender": "男",
            "age": 80,
            "level": 50,
            "sect": 3,           # 水镜宗
            "technique": 32,     # 大河剑意 (水系剑修)
            "weapon": 2013,      # 紫薇软剑
            "auxiliary": 3002,   # 昆仑镜 (鉴子)
            "personas": ["友爱", "沉思", "剑修"],
            "appearance": 30,
        }
    },
    {
        "key": "li_xi_ming",
        "name": "李曦明",
        "desc": "《玄鉴仙族》后辈",
        "params": {
            "gender": "男",
            "age": 25,
            "level": 40,
            "sect": 3,           # 水镜宗
            "technique": 38,     # 逍遥游 (身法)
            "weapon": 3009,      # 芭蕉扇 (术法)
            "auxiliary": 2006,   # 源天神眼 (明阳神通)
            "personas": ["死宅", "惜命", "沉思"],
            "appearance": 5,
        }
    }
]

# ==========================================
# 2. 执行生成与关系绑定逻辑
# ==========================================

def spawn_protagonists(
    world: World, 
    current_month_stamp: MonthStamp, 
    probability: float = 1.0
) -> Dict[str, Avatar]:
    """
    遍历配置生成角色，并处理特殊关系。
    :param probability: 每个角色生成的概率 (0.0 - 1.0)。
    """
    created_avatars = {}
    
    # 1. 批量生成
    for config in protagonist_configs:
        # 概率判定
        if probability < 1.0 and random.random() > probability:
            continue
            
        try:
            avatar = create_avatar_from_request(
                world=world,
                current_month_stamp=current_month_stamp,
                name=config["name"],
                **config["params"]
            )
            created_avatars[config["key"]] = avatar
        except Exception:
            pass # 忽略生成错误，避免中断

    # 2. 绑定关系
    # 注意：需要确保双方都已生成
    
    # 【凡人组】韩立 <-> 厉飞雨 (挚友)
    if "han_li" in created_avatars and "li_fei_yu" in created_avatars:
        han = created_avatars["han_li"]
        li = created_avatars["li_fei_yu"]
        han.set_relation(li, Relation.FRIEND)

    # 【斗破组】萧炎 <-> 纳兰嫣然 (仇敌/退婚)
    if "xiao_yan" in created_avatars and "nalan_yanran" in created_avatars:
        xiao = created_avatars["xiao_yan"]
        nalan = created_avatars["nalan_yanran"]
        xiao.set_relation(nalan, Relation.ENEMY)

    # 【玄鉴组】李通崖 <-> 李曦明 (长辈)
    if "li_tong_ya" in created_avatars and "li_xi_ming" in created_avatars:
        tong_ya = created_avatars["li_tong_ya"]
        xi_ming = created_avatars["li_xi_ming"]
        tong_ya.set_relation(xi_ming, Relation.PARENT)

    # 返回 ID -> Avatar 字典，方便合并
    return {av.id: av for av in created_avatars.values()}
