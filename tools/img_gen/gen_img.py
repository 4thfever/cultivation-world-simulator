import os
import base64
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
    female_prompt_base = "一个好看的仙侠女性头像。只有头部和面部。二次元风格的漫画图片，略微Q版，正面看镜头。纯白背景。像素风格，细节别太多。"
    female_affixes = [
        "紫色长发，表情嗔怒，带有一丝冷峻，有一个簪子。",
        "乌黑直发，眉心一点红砂，清冷淡漠，镶玉步摇。",
        "银白短发，英气微笑，发梢轻卷，耳坠为小灵铃。",
        "墨绿长发，高马尾，目光坚毅，额前碎发，佩青竹簪。",
        "渐变粉蓝长卷发，眸有星点，温柔含笑，薄纱额饰。",
        "赤红披发，英气冷艳，眉尾上挑，凤羽发冠。",
        "浅金长发，缎带系发，气质圣洁，流苏步摇。",
        "乌青长发，微皱眉，眼尾红妆，一枚冰晶发卡。",
        "白发如雪，神情淡然，眉心月印，玉质头箍。",
        "靛蓝长发，俏皮眨眼，脸颊淡粉，葫芦小发簪。",
        "茶棕双丸子头，活泼微笑，脸上淡淡雀斑，小葵花发卡。",
        "青丝长发半披半挽，清雅端庄，蝶形玉簪。",
        "淡紫短波浪发，俏皮吐舌，星月耳饰。",
        "墨发低侧马尾，冷静专注，细链额饰垂坠。",
        "湖绿挑染长发，狡黠微笑，狐耳发饰点缀。",
        "灰蓝长直发，平刘海，面无表情，银环头饰。",
    ]
    male_prompt_base = "一个英俊的的仙侠男性头像。只有头部和面部。二次元风格的漫画图片，略微Q版，正面看镜头。纯白背景。像素风格，细节别太多。"
    male_affixes = [
        "乌发高束，剑眉星目，气质冷峻，青玉发冠。",
        "银白长发，淡笑从容，额间玄纹，流苏头箍。",
        "墨发披肩，脸上一抹浅疤，坚毅沉稳，黑金发簪。",
        "深棕短发，目光凌厉，薄唇紧抿，皮绳束发。",
        "蓝黑长发，发尾微卷，温润如玉，白玉簪。",
        "赤褐长发，桀骜挑眉，轻笑不羁，耳坠小铜铃。",
        "玄青半束发，沉静内敛，额前碎发，银纹额饰。",
        "白发如雪，清隽淡笑，眉心一点冰蓝印，细环头饰。",
        "墨发高马尾，目如寒星，英气逼人，羽纹发冠。",
        "亚麻色短发，随性浅笑，轻胡茬，细革头环。",
        "乌青长发，神情冷淡，眼神专注，剑形耳坠。",
        "银灰长直发，肃杀气质，额缠黑带，简洁利落。",
        "深紫挑染长发，狡黠微笑，眸底流光，狐尾发饰。",
        "墨发半披，眼神温和从容，玉串发夹。",
        "金棕长发，爽朗大笑，额前碎发，兽牙发簪。",
        "青黑短发，专注坚定，线条硬朗，细链发饰垂坠。",
    ]

    for affix in male_affixes:
        prompt_text = male_prompt_base + affix
        save_generated_image(prompt_text, folder="tools/img_gen/tmp/males")
    for affix in female_affixes:
        prompt_text = female_prompt_base + affix
        save_generated_image(prompt_text, folder="tools/img_gen/tmp/females")