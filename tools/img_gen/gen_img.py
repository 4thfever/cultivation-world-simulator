import os
import base64
import random
from datetime import datetime

import requests

# 全局配置：请在此处填入你的 DashScope API Key
API_KEY = "sk-26818d3a4eb14b41a71f4d0319e4edfa"  # <-- 在此处粘贴你的 API Key
BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = "qwen-image-plus"


def generate_qwen_image(prompt: str, *, size: str = "1328*1328") -> str:
    """调用 DashScope 原生接口生成图片，返回 base64 字符串。

    入参:
        prompt: 生成图片的提示词
        size:   图片尺寸，形如 "宽*高"（例如 "1328*1328"）

    返回:
        base64 字符串（不带 data: 前缀），可自行解码保存为图片
    """

    if not API_KEY:
        raise RuntimeError("请先在代码顶部设置 API_KEY")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    
    seed = random.randint(1, 4294967290)
    
    payload = {
        "model": MODEL,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": prompt}
                    ],
                }
            ]
        },
        "parameters": {
            "negative_prompt": "",
            "prompt_extend": True,
            "watermark": True,
            "size": size,
            "seed": seed,
        },
    }

    r = requests.post(BASE_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()

    def extract_image_from_content(content_list):
        """从 content 列表中提取图片，优先 URL 后 base64"""
        for item in content_list:
            if not isinstance(item, dict):
                continue
            # 尝试提取 URL
            url = item.get("image") or item.get("image_url") or item.get("url")
            if isinstance(url, str) and url.startswith("http"):
                img_bytes = requests.get(url, timeout=120).content
                return base64.b64encode(img_bytes).decode("utf-8")
            # 尝试提取 base64
            b64 = item.get("b64") or item.get("b64_json") or item.get("image_base64")
            if isinstance(b64, str) and len(b64) > 100:
                return b64
        return None

    output = data.get("output", {})
    
    # 尝试路径1：output.choices[0].message.content[*]
    choices = output.get("choices", [])
    if choices:
        content_list = choices[0].get("message", {}).get("content", [])
        result = extract_image_from_content(content_list)
        if result:
            return result
    
    # 尝试路径2：output.results[0].content[*]
    results = output.get("results", [])
    if results:
        content_list = results[0].get("content", [])
        result = extract_image_from_content(content_list)
        if result:
            return result

    raise RuntimeError("未获得图片结果")


def save_generated_image(query: str, folder: str = "tools/img_gen/tmp/raw") -> str:
    """根据查询生成图片并保存到 result 目录。
    
    入参:
        query: 图片生成的提示词
        
    返回:
        保存的图片文件路径
    """
    b64 = generate_qwen_image(query)
    img_bytes = base64.b64decode(b64)
    
    result_dir = folder
    os.makedirs(result_dir, exist_ok=True)
    
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
    out_path = os.path.join(result_dir, filename)
    
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    
    print(f"图片已保存: {out_path}")
    return out_path


if __name__ == "__main__":
    female_prompt_base = "一个好看的仙侠女性头像。只有头部和面部且完整露出头部。二次元风格的漫画图片，略微Q版，正面看镜头。纯白背景。像素风格，细节别太多。"
    # female_affixes = [
    #     "紫色长发，表情嗔怒，带有一丝冷峻，有一个簪子。",
    #     "乌黑直发，眉心一点红砂，清冷淡漠，镶玉步摇。",
    #     "银白短发，英气微笑，发梢轻卷，耳坠为小灵铃。",
    #     "墨绿长发，高马尾，目光坚毅，额前碎发，佩青竹簪。",
    #     "渐变粉蓝长卷发，眸有星点，温柔含笑，薄纱额饰。",
    #     "赤红披发，英气冷艳，眉尾上挑，凤羽发冠。",
    #     "浅金长发，缎带系发，气质圣洁，流苏步摇。",
    #     "乌青长发，微皱眉，眼尾红妆，一枚冰晶发卡。",
    #     "白发如雪，神情淡然，眉心月印，玉质头箍。",
    #     "靛蓝长发，俏皮眨眼，脸颊淡粉，葫芦小发簪。",
    #     "茶棕双丸子头，活泼微笑，脸上淡淡雀斑，小葵花发卡。",
    #     "青丝长发半披半挽，清雅端庄，蝶形玉簪。",
    #     "淡紫短波浪发，俏皮吐舌，星月耳饰。",
    #     "墨发低侧马尾，冷静专注，细链额饰垂坠。",
    #     "湖绿挑染长发，狡黠微笑，狐耳发饰点缀。",
    #     "灰蓝长直发，平刘海，面无表情，银环头饰。",
    # ]
    female_affixes = [
        "墨黑长发，眼神清澈，嘴角微扬，佩戴白花发饰。",
        "银灰卷发，神情慵懒，眼角泪痣，水晶耳坠。",
        "酒红短发，英气勃发，剑眉入鬓，金色额饰。",
        "浅紫双马尾，活泼可爱，笑眼弯弯，铃铛发带。",
        "青色长直发，面容清冷，毫无表情，玉簪挽发。",
        "金棕波浪发，温柔婉约，眉目含情，珍珠步摇。",
        "深蓝盘发，端庄典雅，气质高贵，凤凰发冠。",
        "纯白长发，双瞳异色，神秘莫测，银链额饰。",
        "粉色丸子头，天真烂漫，脸颊红晕，桃花发卡。",
        "亚麻色碎发，眼神坚毅，嘴角紧抿，简约发带。",
        "橙红长发，热情似火，笑容灿烂，火焰纹饰。",
        "墨绿麻花辫，恬静自然，怀抱书卷，木质发簪。",
        "灰白短发，凌厉眼神，左脸刺青，金属耳环。",
        "栗色长卷发，妩媚动人，红唇烈焰，玫瑰发饰。",
        "藏蓝束发，干练利落，目光如炬，黑色头巾。",
        "浅黄披发，病若西子，楚楚可怜，素色发带。",
        "七彩流光发，宛如神女，双眸含光，云雾缭绕。",
        "乌黑姬发式，乖巧文静，低眉顺眼，丝绸蝴蝶结。",
        "浅褐盘发，娇俏可人，插着糖葫芦，红绳发饰。",
        "银白长辫，圣洁高雅，闭目祈祷，柔和光环。",
        "深紫直发，冷艳高傲，下巴微扬，紫晶皇冠。",
        "翠绿双环髻，灵动活泼，手持折扇，翡翠流苏。",
        "铂金长发，冷漠疏离，如冰山雪莲，冰凌耳饰。",
        "蓬松红发，野性难驯，兽皮衣饰，骨牙项链。",
        "靛青垂鬟，知书达理，手持毛笔，书卷气息。",
        "绯红长发，傲娇神情，双手抱胸，猫耳发箍。",
        "墨蓝劲装，女扮男装，英姿飒爽，腰间佩剑。",
        "米色散发，睡眼惺忪，慵懒倚靠，云纹抱枕。",
        "黛青盘发，成熟稳重，慈眉善目，祥云发簪。",
        "碧绿长发，鬼气森森，面色苍白，幽冥鬼火。",
        "玫瑰金长发，公主气质，甜美微笑，蕾丝发带。",
        "漆黑长直，遮住单眼，阴郁神秘，骷髅发夹。",
    ]
    male_prompt_base = "一个英俊的的仙侠男性头像。只有头部和面部且完整露出头部。二次元风格的漫画图片，略微Q版，正面看镜头。纯白背景。像素风格，细节别太多。"
    # male_affixes = [
    #     "乌发高束，剑眉星目，气质冷峻，青玉发冠。",
    #     "银白长发，淡笑从容，额间玄纹，流苏头箍。",
    #     "墨发披肩，脸上一抹浅疤，坚毅沉稳，黑金发簪。",
    #     "深棕短发，目光凌厉，薄唇紧抿，皮绳束发。",
    #     "蓝黑长发，发尾微卷，温润如玉，白玉簪。",
    #     "赤褐长发，桀骜挑眉，轻笑不羁，耳坠小铜铃。",
    #     "玄青半束发，沉静内敛，额前碎发，银纹额饰。",
    #     "白发如雪，清隽淡笑，眉心一点冰蓝印，细环头饰。",
    #     "墨发高马尾，目如寒星，英气逼人，羽纹发冠。",
    #     "亚麻色短发，随性浅笑，轻胡茬，细革头环。",
    #     "乌青长发，神情冷淡，眼神专注，剑形耳坠。",
    #     "银灰长直发，肃杀气质，额缠黑带，简洁利落。",
    #     "深紫挑染长发，狡黠微笑，眸底流光，狐尾发饰。",
    #     "墨发半披，眼神温和从容，玉串发夹。",
    #     "金棕长发，爽朗大笑，额前碎发，兽牙发簪。",
    #     "青黑短发，专注坚定，线条硬朗，细链发饰垂坠。",
    # ]
    male_affixes = [
        "墨黑长发，剑眉入鬓，眼神如电，束发金冠。",
        "银白散发，仙风道骨，捻须微笑，木质道簪。",
        "酒红短发，狂放不羁，嘴角轻挑，墨玉耳扣。",
        "深蓝马尾，冷若冰霜，目光锐利，银色护额。",
        "棕褐寸头，憨厚老实，笑容淳朴，粗布麻衣。",
        "金黄卷发，风流倜傥，桃花眼，折扇轻摇。",
        "灰白长发，面容枯槁，眼神阴鸷，骨质发饰。",
        "纯黑碎发，少年意气，眼神清澈，红色抹额。",
        "紫发披肩，妖异俊美，邪魅一笑，蛇形耳坠。",
        "青丝半束，书卷气息，温文尔雅，玉佩腰饰。",
        "赤发冲天，怒目圆睁，气势汹汹，火焰纹身。",
        "亚麻长发，忧郁深沉，低头沉思，素色发带。",
        "墨绿短发，干练果决，面无表情，单片琉璃镜。",
        "栗色微卷，温柔体贴，眼神宠溺，宽松道袍。",
        "藏蓝长辫，异域风情，肤色古铜，图腾面纹。",
        "浅灰中分，斯文败类，金边叆叇，嘴角冷笑。",
        "狂傲琴师，长发如瀑，抚琴长啸，音波缭绕。",
        "乌黑背头，一方霸主，目光审视，龙纹扳指。",
        "焦糖色蓬松，阳光开朗，露齿大笑，锦织抹额。",
        "银发遮眼，神秘莫测，嘴角微勾，面罩遮脸。",
        "深紫长直，高贵冷艳，不可一世，紫金皇冠。",
        "翠绿短发，灵动狡黠，吹着口哨，草叶衔嘴。",
        "铂金长发，正义凛然，手持长剑，玉石护符。",
        "棕红乱发，落魄浪人，胡渣唏嘘，酒葫芦。",
        "靛青束发，忠诚护卫，如影随形，蒙面黑巾。",
        "绯红短发，热血少年，握拳加油，脸颊伤痕。",
        "墨蓝狼尾，野性难驯，眼神凶狠，兽牙项链。",
        "米白长卷，慵懒贵族，品着灵茶，丝绸法袍。",
        "黛青道髻，严严肃穆，手持拂尘，八卦道袍。",
        "乱发蓬松，机关大师，佩戴透镜，摆弄零件。",
        "玫瑰金分头，花花公子，抛个媚眼，玫瑰花。",
        "漆黑长发，入魔之相，双目赤红，魔气缭绕。",
    ]
    sect_prompt_base = "像素化的仙侠宗门场景图片，极度像素化，颗粒感强，线条轮廓粗，极简主义，二次元风格漫画图片。"
    sect_affixes = [
        # "山巅飘渺云海，云纹阵法光芒环绕，远处群峰。",
        # "灵兽栖地，兽栏密布，岩石兽穴。",
        # "湖面倒影，中央悬浮巨大水镜，镜面波光粼粼，雾气弥漫。",
        # "幽冥宗门，阴暗昏沉，黑雾弥漫，冷厉气息，幽蓝鬼火点点。",
        # "炼器工坊，机关密布，熔炉火光。",
        # "合欢宫殿，粉红雾气，花瓣飘舞，柔和光晕，纱幔轻垂。",
        # "镇魂大殿，铁血肃杀，封印符文，镇压法阵，黑铁锁链。",
        # "幽影之地，暗影重重，光影交错，幽冥之气，黑雾吞噬轮廓。",
        # "船帆如云，炼器炉火。",
        "雅致园林，丝竹管弦，百花盛开，隐约音律符文，春意盎然。",  # 妙化宗
        "云雾缭绕山峰，无数阵法光阵层叠，晦暗不明，神秘莫测。",  # 回玄宗
        "极光绚丽，万年寒冰城墙，流光溢彩，如梦似幻，不夜之城。",  # 不夜城
        "雄奇山峰，紫气东来，浩然正气光柱冲天，书声琅琅幻象。",  # 天行健宗
        "险恶山脉，血雾弥漫，怪石嶙峋，白骨累累，狂野血腥。",  # 噬魔宗
    ]
    # for affix in male_affixes:
    #     prompt_text = male_prompt_base + affix
    #     save_generated_image(prompt_text, folder="tools/img_gen/tmp/males")
    # for affix in female_affixes:
    #     prompt_text = female_prompt_base + affix
    #     save_generated_image(prompt_text, folder="tools/img_gen/tmp/females")
    for i, affix in enumerate(sect_affixes):
        prompt_text = sect_prompt_base + affix
        save_generated_image(prompt_text, folder="tools/img_gen/tmp/sects")