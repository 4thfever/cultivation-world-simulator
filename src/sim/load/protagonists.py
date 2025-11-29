from typing import List, Dict, Optional
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
            "technique": 30,     # 明心归一剑典
            "weapon": 3007,      # 剑宗诛邪剑 (长相思)
            "auxiliary": 3011,   # 明心剑匣
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
            "age": 200,
            "level": 90,         # 合体/大乘
            "sect": 9,           # 千帆城 (商会/散修流)
            "technique": 5,      # 碧林长生法 (青元剑诀)
            "weapon": 3001,      # 本命剑匣 (青竹蜂云剑)
            "auxiliary": 2002,   # 回春石 (掌天瓶/小绿瓶)
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
            "technique": 28,     # 血神噬魂大法 (燃烧气血/损阴德)
            "weapon": 2002,      # 破军刀 (江湖刀客)
            "auxiliary": 2003,   # 延寿宝珠 (最渴望之物)
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
            "technique": 42,     # 赤狱炼锋诀 (焚决)
            "weapon": 2012,      # 玄铁重剑 (玄重尺)
            "auxiliary": 3010,   # 九转炼器炉 (药老能力)
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
            "technique": 56,     # 飞翼乘风术 (风属性斗气)
            "weapon": 2013,      # 碧波软剑 (轻灵剑法)
            "auxiliary": 2007,   # 轻灵羽衣 (身法加成)
            "personas": ["霸道", "剑修", "沉思"],
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
            "technique": 25,     # 九天淬体雷诀 (八九玄功)
            "weapon": 2011,      # 赤焰战刀 (雷刀)
            "auxiliary": 2009,   # 护元宝甲
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
            "technique": 36,     # 彻天水镜观
            "weapon": 2005,      # 紫罗扇
            "auxiliary": 3002,   # 千里镜
            "personas": ["心机深沉", "疑心重", "贪财"],
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
            "technique": 53,     # 冥狱吞魄经
            "weapon": 2002,      # 破军刀 (柴刀)
            "auxiliary": 2006,   # 洞察神瞳 (鬼眼)
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
            "technique": 28,     # 血神噬魂大法
            "weapon": 1001,      # 凡品剑
            "auxiliary": 2008,   # 炼心佛珠
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
            "technique": 8,      # 玄水化海术
            "weapon": 2013,      # 碧波软剑
            "auxiliary": 3002,   # 千里镜
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
            "technique": 38,     # 镜花游身步
            "weapon": 3009,      # 虚空之扇
            "auxiliary": 2006,   # 洞察神瞳
            "personas": ["友爱", "惜命", "沉思"],
            "appearance": 5,
        }
    }
]

# ==========================================
# 2. 执行生成与关系绑定逻辑
# ==========================================

def spawn_protagonists(world: World, current_month_stamp: MonthStamp) -> Dict[str, Avatar]:
    """
    遍历配置生成角色，并处理特殊关系。
    """
    created_avatars = {}
    
    # 1. 批量生成
    for config in protagonist_configs:
        try:
            avatar = create_avatar_from_request(
                world=world,
                current_month_stamp=current_month_stamp,
                name=config["name"],
                **config["params"]
            )
            created_avatars[config["key"]] = avatar
        except Exception as e:
            pass # 忽略生成错误，避免中断

    # 2. 绑定关系
    
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
