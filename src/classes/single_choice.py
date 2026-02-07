from typing import Any, Dict, List, TYPE_CHECKING, Tuple, Optional, Callable
import json

from src.i18n import t
from src.utils.llm import call_llm_with_task_name
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

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
    full_choices_str = t("【Current Situation】: {context}\n\n{choices}", 
                         context=context_desc, choices=choices_str)

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
            "label": t("item_label_weapon"),
            "get_current": lambda: avatar.weapon,
            "use_func": avatar.change_weapon,
            "sell_func": avatar.sell_weapon,
            "verbs": {
                "action": t("item_verb_equip"),
                "done": t("item_verb_equipped"),
                "replace": t("item_verb_replace")
            }
        }
    elif item_type == "auxiliary":
        return {
            "label": t("item_label_auxiliary"),
            "get_current": lambda: avatar.auxiliary,
            "use_func": avatar.change_auxiliary,
            "sell_func": avatar.sell_auxiliary,
            "verbs": {
                "action": t("item_verb_equip"),
                "done": t("item_verb_equipped"),
                "replace": t("item_verb_replace")
            }
        }
    elif item_type == "technique":
        return {
            "label": t("item_label_technique"),
            "get_current": lambda: avatar.technique,
            "use_func": lambda x: setattr(avatar, 'technique', x),
            "sell_func": None,  # 功法通常不能卖
            "verbs": {
                "action": t("item_verb_practice"),
                "done": t("item_verb_switched"),
                "replace": t("item_verb_replace")
            }
        }
    elif item_type == "elixir":
        return {
            "label": t("item_label_elixir"),
            "get_current": lambda: None, # 丹药没有"当前装备"的概念，都是新获得的
            "use_func": avatar.consume_elixir,
            "sell_func": avatar.sell_elixir,
            "verbs": {
                "action": t("item_verb_consume"),
                "done": t("item_verb_consumed"),
                "replace": t("item_verb_replace")
            }
        }
    else:
        raise ValueError(t("Unsupported item type: {item_type}", item_type=item_type))


async def handle_item_exchange(
    avatar: "Avatar",
    new_item: Any,
    item_type: str, # "weapon", "auxiliary", "technique", "elixir"
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
    verbs = ops["verbs"]
    current_item = ops["get_current"]()
    
    new_name = new_item.name
    # 使用 str() 来触发 Realm/Stage 的 __str__ 方法进行 i18n 翻译。
    new_grade = str(getattr(new_item, "realm", getattr(new_item, "grade", None)))
    
    # 1. 自动装备：当前无装备且不强制考虑卖新
    if current_item is None and not can_sell_new:
        ops["use_func"](new_item)
        return True, t("{avatar_name} obtained {grade} {label}『{item_name}』and {action}.",
                      avatar_name=avatar.name, grade=new_grade, 
                      label=label, item_name=new_name, action=verbs['action'])

    # 2. 需要决策：准备描述
    old_name = current_item.name if current_item else ""
    new_info = new_item.get_info(detailed=True)
    
    swap_desc = t("New {label}: {info}", label=label, info=new_info)
    if current_item:
        old_info = current_item.get_info(detailed=True)
        swap_desc = t("Current {label}: {old_info}\n{new_desc}",
                     label=label, old_info=old_info, new_desc=swap_desc)
        if ops["sell_func"]:
            swap_desc += t("\n(Selecting {replace} will sell old {label})",
                          replace=verbs['replace'], label=label)

    # 3. 构建选项
    # Option A: 装备/服用新物品
    opt_a_text = t("{action} new {label}『{new_name}』",
                  action=verbs['action'], label=label, new_name=new_name)
    if current_item and ops["sell_func"]:
        opt_a_text += t(", sell old {label}『{old_name}』",
                       label=label, old_name=old_name)
    elif current_item:
        opt_a_text += t(", {replace} old {label}『{old_name}』",
                       replace=verbs['replace'], label=label, old_name=old_name)

    # Option B: 拒绝新物品
    if can_sell_new and ops["sell_func"]:
        opt_b_text = t("Sell new {label}『{new_name}』for spirit stones, keep current status",
                      label=label, new_name=new_name)
    else:
        opt_b_text = t("Abandon『{new_name}』", new_name=new_name)
        if current_item:
            opt_b_text += t(", keep current『{old_name}』", old_name=old_name)

    options = [
        {"key": "A", "desc": opt_a_text},
        {"key": "B", "desc": opt_b_text}
    ]

    full_context = f"{context_intro}\n{swap_desc}"
    choice = await make_decision(avatar, full_context, options)

    # 4. 执行决策
    if choice == "A":
        # 卖旧（如果有且能卖）
        if current_item and ops["sell_func"]:
            ops["sell_func"](current_item)
        # 装新/服用
        ops["use_func"](new_item)
        return True, t("{avatar_name} {done} {grade} {label}『{item_name}』.",
                      avatar_name=avatar.name, done=verbs['done'],
                      grade=new_grade, label=label, item_name=new_name)
    else:
        # 卖新（如果被要求且能卖）
        if can_sell_new and ops["sell_func"]:
            sold_price = ops["sell_func"](new_item)
            return False, t("{avatar_name} sold newly obtained {item_name}, gained {price} spirit stones.",
                          avatar_name=avatar.name, item_name=new_name, price=sold_price)
        else:
            return False, t("{avatar_name} abandoned {item_name}.",
                          avatar_name=avatar.name, item_name=new_name)
