from typing import Any, Dict, List, TYPE_CHECKING, Tuple, Optional, Callable
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
                choice = clean_result
        else:
            choice = clean_result

    # 验证 choice 是否在 options key 中
    valid_keys = {opt["key"] for opt in options}
    # 简单的容错
    if choice not in valid_keys:
        for k in valid_keys:
            if k in choice:
                choice = k
                break
    
    if choice not in valid_keys:
         choice = options[0]["key"]

    return choice


def _get_item_ops(avatar: "Avatar", item_type: str) -> dict:
    """根据物品类型返回对应的操作函数和标签"""
    if item_type == "weapon":
        return {
            "label": "兵器",
            "get_current": lambda: avatar.weapon,
            "equip": avatar.change_weapon,
            "sell": avatar.sell_weapon
        }
    elif item_type == "auxiliary":
        return {
            "label": "辅助装备",
            "get_current": lambda: avatar.auxiliary,
            "equip": avatar.change_auxiliary,
            "sell": avatar.sell_auxiliary
        }
    elif item_type == "technique":
        return {
            "label": "功法",
            "get_current": lambda: avatar.technique,
            "equip": lambda x: setattr(avatar, 'technique', x),
            "sell": None  # 功法通常不能卖
        }
    else:
        raise ValueError(f"Unsupported item type: {item_type}")


async def handle_item_exchange(
    avatar: "Avatar",
    new_item: Any,
    item_type: str, # "weapon", "auxiliary", "technique"
    context_intro: str,
    can_sell_new: bool = False
) -> Tuple[bool, str]:
    """
    通用处理物品（装备/功法）的获取、替换与决策逻辑。
    
    Args:
        avatar: 角色对象
        new_item: 新获得的物品
        item_type: 物品类型键值 ("weapon", "auxiliary", "technique")
        context_intro: 决策背景描述
        can_sell_new: 如果拒绝装备，是否允许卖掉新物品换灵石

    Returns:
        (swapped, result_text)
    """
    ops = _get_item_ops(avatar, item_type)
    label = ops["label"]
    current_item = ops["get_current"]()
    
    new_name = new_item.name
    new_grade = getattr(new_item, "realm", getattr(new_item, "grade", None)).value
    
    # 1. 自动装备：当前无装备且不强制考虑卖新
    if current_item is None and not can_sell_new:
        ops["equip"](new_item)
        return True, f"{avatar.name} 获得了{new_grade}{label}『{new_name}』并装备。"

    # 2. 需要决策：准备描述
    old_name = current_item.name if current_item else ""
    new_info = new_item.get_info(detailed=True)
    
    swap_desc = f"新{label}：{new_info}"
    if current_item:
        old_info = current_item.get_info(detailed=True)
        swap_desc = f"现有{label}：{old_info}\n{swap_desc}"
        if ops["sell"]:
            swap_desc += f"\n（选择替换将卖出旧{label}）"

    # 3. 构建选项
    # Option A: 装备新物品
    opt_a_text = f"装备新{label}『{new_name}』"
    if current_item and ops["sell"]:
        opt_a_text += f"，卖掉旧{label}『{old_name}』"
    elif current_item:
        opt_a_text += f"，替换旧{label}『{old_name}』"

    # Option B: 拒绝新物品
    if can_sell_new and ops["sell"]:
        opt_b_text = f"卖掉新{label}『{new_name}』换取灵石，保留现状"
    else:
        opt_b_text = f"放弃『{new_name}』"
        if current_item:
            opt_b_text += f"，保留身上的『{old_name}』"

    options = [
        {"key": "A", "desc": opt_a_text},
        {"key": "B", "desc": opt_b_text}
    ]

    full_context = f"{context_intro}\n{swap_desc}"
    choice = await make_decision(avatar, full_context, options)

    # 4. 执行决策
    if choice == "A":
        # 卖旧（如果有且能卖）
        if current_item and ops["sell"]:
            ops["sell"](current_item)
        # 装新
        ops["equip"](new_item)
        return True, f"{avatar.name} 换上了{new_grade}{label}『{new_name}』。"
    else:
        # 卖新（如果被要求且能卖）
        if can_sell_new and ops["sell"]:
            sold_price = ops["sell"](new_item)
            return False, f"{avatar.name} 卖掉了新获得的{new_name}，获利 {sold_price} 灵石。"
        else:
            return False, f"{avatar.name} 放弃了{new_name}。"
