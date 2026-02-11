from typing import List, Dict, Optional
import random
from src.classes.core.avatar import Avatar
from src.classes.core.world import World
from src.systems.time import MonthStamp
from src.classes.relation.relation import Relation
from src.sim.avatar_init import create_avatar_from_request

# ==========================================
# 1. 主角与配角配置列表
# ==========================================
protagonist_configs = [
    # ------------------- 赤心巡天 -------------------
    {
        "key": "jiang_wang",
        "name": "姜望",
        "params": {
            "gender": "男",
            "age": 22,
            "level": 60,         # 金丹/外楼
            "sect": 1,           # 明心剑宗
            "technique": 30,     # 草字剑诀 (剑道至高)
            "weapon": 1057,      # 诛仙剑 (长相思)
            "auxiliary": 2061,   # 六道剑匣 (随身剑匣)
            "personas": ["心机深沉", "极端正义", "剑痴"],
            "appearance": 8,     # 姜望：相貌清秀，气质极佳
        }
    },
    # ------------------- 凡人修仙传 -------------------
    {
        "key": "han_li",
        "name": "韩立",
        "params": {
            "gender": "男",
            "age": 120,
            "level": 90,         # 合体/大乘
            "sect": 9,           # 千帆城 (商会/散修流)
            "technique": 33,     # 青帝长生诀 (木系至高)
            "weapon": 1051,      # 青竹蜂云剑 (本命法宝)
            "auxiliary": 2053,   # 掌天瓶 (催熟万物)
            "personas": ["惜命", "心机深沉", "苟"],
            "appearance": 6,     # 韩立：相貌平平，皮肤黝黑（后期气质加成）
        }
    },
    {
        "key": "nangong_wan",
        "name": "南宫婉",
        "params": {
            "gender": "女",
            "age": 150,
            "level": 80,         # 元婴后期
            "sect": 12,          # 不夜城 (掩月宗/素女功)
            "technique": 47,     # 凌波微步 (素女轮回功)
            "weapon": 1059,      # 芭蕉扇 (朱雀环)
            "auxiliary": 2054,   # 龙凤呈祥戒
            "personas": ["淡漠", "理性", "修行痴迷"],
            "appearance": 9,     # 南宫婉：绝色美人，成熟韵味
        }
    },
    {
        "key": "li_fei_yu",
        "name": "厉飞雨",
        "params": {
            "gender": "男",
            "age": 25,           # 英年早逝形象
            "level": 30,         # 筑基期 (对应凡人武学巅峰+修仙入门)
            "sect": 14,          # 噬魔宗 (透支潜力，杀伐果断)
            "technique": 28,     # 燃血大法 (燃烧气血)
            "weapon": 1031,      # 血饮狂刀 (杀气腾腾)
            "auxiliary": 2003,   # 人参果(伪) (增加寿命)
            "personas": ["狠辣", "好斗", "忠诚"],
            "appearance": 8,     # 厉飞雨：英俊潇洒，杀伐果断
        }
    },
    # ------------------- 斗破苍穹 -------------------
    {
        "key": "xiao_yan",
        "name": "萧炎",
        "params": {
            "gender": "男",
            "age": 30,
            "level": 110,        # 斗帝
            "sect": 5,           # 朱勾宗 (火系/炼器/暗杀)
            "technique": 42,     # 焚决 (吞噬异火)
            "weapon": 1032,      # 玄铁重剑 (玄重尺)
            "auxiliary": 2058,   # 八卦炉 (药老/炼药)
            "personas": ["炼丹师", "气运之子", "复仇"],
            "appearance": 7,     # 萧炎：清秀，耐看
        }
    },
    {
        "key": "xiao_xun_er",
        "name": "萧薰儿",
        "params": {
            "gender": "女",
            "age": 25,
            "level": 85,
            "sect": 13,          # 天行健宗 (远古族)
            "technique": 11,     # 纯阳无极功 (金帝焚天炎)
            "weapon": 1055,      # 赤锋矛
            "auxiliary": 2062,   # 传国玉玺 (族长信物)
            "personas": ["气运之子", "霸道", "友爱"],
            "appearance": 10,    # 萧薰儿：神品血脉，绝世容颜
        }
    },
    {
        "key": "nalan_yanran",
        "name": "纳兰嫣然",
        "params": {
            "gender": "女",
            "age": 28,
            "level": 70,         # 斗皇/斗宗
            "sect": 1,           # 明心剑宗 (云岚宗对应)
            "technique": 56,     # 纵地金光 (风系身法)
            "weapon": 1033,      # 紫薇软剑 (轻灵剑法)
            "auxiliary": 2007,   # 踏云靴 (身法加成)
            "personas": ["霸道", "剑修", "刻薄"],
            "appearance": 9,     # 纳兰嫣然：云岚宗少宗主，美貌御姐
        }
    },
    # ------------------- 一世之尊 -------------------
    {
        "key": "meng_qi",
        "name": "孟奇",
        "params": {
            "gender": "男",
            "age": 25,
            "level": 80,
            "sect": 7,           # 镇魂宗 (肉身/禅意)
            "technique": 49,     # 神霄雷法 (雷法正宗)
            "weapon": 1031,      # 血饮狂刀 (雷刀/霸王绝刀)
            "auxiliary": 2008,   # 菩提子 (悟性/诸果之因)
            "personas": ["穿越者", "好斗", "外向"],
            "appearance": 9,     # 孟奇：俊秀出尘，元始天尊
        }
    },
    {
        "key": "gu_xiao_sang",
        "name": "顾小桑",
        "params": {
            "gender": "女",
            "age": 24,
            "level": 75,
            "sect": 8,           # 幽魂噬影宗 (圣女/诡秘)
            "technique": 36,     # 虚空经 (无生老母/空间)
            "weapon": 1025,      # 桃花扇 (无生指/美貌)
            "auxiliary": 2011,   # 无相面具 (千变万化)
            "personas": ["心机深沉", "随性", "狠辣"],
            "appearance": 10,    # 顾小桑：罗教圣女，绝美精灵
        }
    },
    {
        "key": "jiang_zhi_wei",
        "name": "江芷微",
        "params": {
            "gender": "女",
            "age": 25,
            "level": 70,
            "sect": 1,           # 明心剑宗 (洗剑阁)
            "technique": 30,     # 草字剑诀 (截天七剑)
            "weapon": 1057,      # 诛仙剑 (太解剑)
            "auxiliary": 2061,   # 六道剑匣
            "personas": ["剑痴", "好斗", "极端正义"],
            "appearance": 9,     # 江芷微：英气勃发，剑眉星目
        }
    },
    # ------------------- 掌门路 -------------------
    {
        "key": "qi_xiu",
        "name": "齐休",
        "params": {
            "gender": "男",
            "age": 150,
            "level": 70,
            "sect": 3,           # 水镜宗 (全知/观测)
            "technique": 36,     # 虚空经 (全知观测)
            "weapon": 1025,      # 桃花扇 (本命物)
            "auxiliary": 2052,   # 昆仑镜 (全知之眼)
            "personas": ["心机深沉", "疑心重", "穿越者"],
            "appearance": 5,     # 齐休：外貌普通，气质深沉
        }
    },
    # ------------------- 神秘复苏 -------------------
    {
        "key": "yang_jian",
        "name": "杨间",
        "params": {
            "gender": "男",
            "age": 20,
            "level": 75,
            "sect": 8,           # 幽魂噬影宗 (鬼影/灵异)
            "technique": 51,     # 幽冥鬼爪 (鬼影袭击)
            "weapon": 1054,      # 弑神枪 (发裂长枪/棺材钉)
            "auxiliary": 2006,   # 源天神眼 (鬼眼)
            "personas": ["淡漠", "心机深沉", "狠辣"],
            "appearance": 7,     # 杨间：眼神冷冽，相貌尚可
        }
    },
    # ------------------- 道诡异仙 -------------------
    {
        "key": "li_huo_wang",
        "name": "李火旺",
        "params": {
            "gender": "男",
            "age": 19,
            "level": 65,
            "sect": 14,          # 噬魔宗
            "technique": 28,     # 燃血大法 (自残修仙)
            "weapon": 1001,      # 练气剑 (红中)
            "auxiliary": 2008,   # 菩提子 (清心压制)
            "personas": ["无常", "好斗", "忠诚"],
            "appearance": 6,     # 李火旺：神情癫狂，相貌普通
        }
    },
    {
        "key": "bai_ling_miao",
        "name": "白灵淼",
        "params": {
            "gender": "女",
            "age": 18,
            "level": 55,
            "sect": 3,           # 水镜宗 (白莲教/幻象)
            "technique": 16,     # 冰心诀 (纯净/白毛)
            "weapon": 1027,      # 天魔琴 (煞气/掌控)
            "auxiliary": 2008,   # 菩提子 (压制疯狂)
            "personas": ["友爱", "忠诚", "腼腆"],
            "appearance": 9,     # 白灵淼：白化病美少女，圣洁
        }
    },
    # ------------------- 遮天 -------------------
    {
        "key": "ruthless_empress",
        "name": "狠人大帝",
        "params": {
            "gender": "女",
            "age": 450,
            "level": 91,         # 元婴
            "sect": 4,           # 冥王宗 (吞天/死亡)
            "technique": 39,     # 吞天魔功
            "weapon": 1054,      # 弑神枪 (龙纹黑金鼎)
            "auxiliary": 2011,   # 无相面具 (青铜面具)
            "personas": ["修行痴迷", "淡漠", "狠辣"],
            "appearance": 10,    # 狠人大帝：风华绝代，万古第一
        }
    },
    # ------------------- 诛仙 -------------------
    {
        "key": "lu_xue_qi",
        "name": "陆雪琪",
        "params": {
            "gender": "女",
            "age": 28,
            "level": 65,
            "sect": 1,           # 明心剑宗 (青云门)
            "technique": 31,     # 神剑御雷真诀
            "weapon": 1057,      # 诛仙剑 (天琊)
            "auxiliary": 2010,   # 寒玉床 (静坐修行)
            "personas": ["淡漠", "修行痴迷", "极端正义"],
            "appearance": 10,    # 陆雪琪：绝世容颜，冰山美人
        }
    },
    # ------------------- 玄鉴仙族 -------------------
    {
        "key": "li_tong_ya",
        "name": "李通崖",
        "params": {
            "gender": "男",
            "age": 80,
            "level": 50,
            "sect": 3,           # 水镜宗
            "technique": 32,     # 大河剑意 (水系剑修)
            "weapon": 1033,      # 紫薇软剑
            "auxiliary": 2052,   # 昆仑镜 (鉴子)
            "personas": ["友爱", "沉思", "剑修"],
            "appearance": 6,     # 李通崖：普通农家子弟，气质修仙
        }
    },
    {
        "key": "li_xi_ming",
        "name": "李曦明",
        "params": {
            "gender": "男",
            "age": 25,
            "level": 40,
            "sect": 3,           # 水镜宗
            "technique": 38,     # 逍遥游 (身法)
            "weapon": 1059,      # 芭蕉扇 (术法)
            "auxiliary": 2006,   # 源天神眼 (明阳神通)
            "personas": ["死宅", "惜命", "沉思"],
            "appearance": 7,     # 李曦明：世家子弟，相貌尚可
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
    
    # 【凡人组】
    if "han_li" in created_avatars:
        han = created_avatars["han_li"]
        if "li_fei_yu" in created_avatars:
            han.make_friend_with(created_avatars["li_fei_yu"])
        if "nangong_wan" in created_avatars:
            han.become_lovers_with(created_avatars["nangong_wan"])

    # 【斗破组】
    if "xiao_yan" in created_avatars:
        xiao = created_avatars["xiao_yan"]
        if "nalan_yanran" in created_avatars:
            xiao.make_enemy_of(created_avatars["nalan_yanran"])
        if "xiao_xun_er" in created_avatars:
            xiao.become_lovers_with(created_avatars["xiao_xun_er"])

    # 【一世组】
    if "meng_qi" in created_avatars:
        meng = created_avatars["meng_qi"]
        if "gu_xiao_sang" in created_avatars:
            meng.become_lovers_with(created_avatars["gu_xiao_sang"])
        if "jiang_zhi_wei" in created_avatars:
            meng.make_friend_with(created_avatars["jiang_zhi_wei"])

    # 【道诡组】
    if "li_huo_wang" in created_avatars and "bai_ling_miao" in created_avatars:
        created_avatars["li_huo_wang"].become_lovers_with(created_avatars["bai_ling_miao"])

    # 【玄鉴组】李通崖 <-> 李曦明 (长辈)
    if "li_tong_ya" in created_avatars and "li_xi_ming" in created_avatars:
        # 李通崖是长辈，认李曦明为子（虽然原著是孙辈，这里简化为父子或需要 IS_GRAND_CHILD）
        # 假设这里用 PARENT 表示长辈
        created_avatars["li_tong_ya"].acknowledge_child(created_avatars["li_xi_ming"])

    # 返回 ID -> Avatar 字典，方便合并
    return {av.id: av for av in created_avatars.values()}
