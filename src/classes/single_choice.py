from typing import Any, Dict, List, TYPE_CHECKING
from src.utils.llm import call_llm_with_task_name
from src.utils.config import CONFIG
import json

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

async def make_decision(
    avatar: "Avatar", 
    context_desc: str, 
    options: List[Dict[str, Any]]
) -> str:
    """
    让角色在多个选项中做出单选决策。
    
    Args:
        avatar: 做出决策的角色
        context_desc: 决策背景描述
        options: 选项列表，每个选项是一个字典，必须包含 'key' 和 'desc' 字段
                 例如: [{'key': 'A', 'desc': '...'}, {'key': 'B', 'desc': '...'}]
    
    Returns:
        str: AI 选择的选项 Key (如 'A' 或 'B')
    """
    # 1. 获取角色信息 (详细模式)
    avatar_infos = str(avatar.get_info(detailed=True))
    
    # 2. 格式化选项字符串
    choices_list = [f"{opt.get('key', '')}: {opt.get('desc', '')}" for opt in options]
    choices_str = "\n".join(choices_list)
    full_choices_str = f"【当前情境】：{context_desc}\n\n{choices_str}"

    # 3. 调用 AI
    template_path = CONFIG.paths.templates / "single_choice.txt"
    world_info = avatar.world.static_info
    result = await call_llm_with_task_name(
        "single_choice",
        template_path, 
        infos={
            "world_info": world_info,
            "avatar_infos": avatar_infos,
            "choices": full_choices_str
        }
    )
    
    # 4. 解析结果
    choice = ""
    if isinstance(result, dict):
        choice = result.get("choice", "").strip()
    elif isinstance(result, str):
        clean_result = result.strip()
        # 尝试解析可能包含 markdown 的 json
        if "{" in clean_result and "}" in clean_result:
            try:
                # 提取可能的 json 部分
                start = clean_result.find("{")
                end = clean_result.rfind("}") + 1
                json_str = clean_result[start:end]
                data = json.loads(json_str)
                choice = data.get("choice", "").strip()
            except (json.JSONDecodeError, ValueError):
                # 如果 JSON 解析失败，直接看字符串内容是否就是选项 key
                choice = clean_result
            # 有时候 llm 会输出 "choice: A"，这里做个兼容
        else:
            choice = clean_result

    # 验证 choice 是否在 options key 中
    valid_keys = {opt["key"] for opt in options}
    # 简单的容错：如果返回的是 "A." 或者 "A "
    if choice not in valid_keys:
        for k in valid_keys:
            if k in choice:
                choice = k
                break
    
    if choice not in valid_keys:
         # 兜底：默认选第一个
         choice = options[0]["key"]

    return choice
