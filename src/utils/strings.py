def to_json_str_with_intent(data, unescape_newlines: bool = True) -> str:
    """
    将任意数据包装为带有 intent 的 JSON 字符串，便于在 Prompt 中明确语义。

    结构：{"intent": intent, "data": data}
    - 使用缩进与 ensure_ascii=False，保证可读性与中文不转义
    """
    import json
    s = json.dumps(data, ensure_ascii=False, indent=2)
    if unescape_newlines:
        s = s.replace("\\n", "\n")
    return s


def intentify_prompt_infos(infos: dict) -> dict:
    processed: dict = dict(infos or {})
    if "avatar_infos" in processed:
        processed["avatar_infos"] = to_json_str_with_intent(processed["avatar_infos"])
    if "global_info" in processed:
        processed["global_info"] = to_json_str_with_intent(processed["global_info"])
    if "general_action_infos" in processed:
        processed["general_action_infos"] = to_json_str_with_intent(processed["general_action_infos"])
    if "expanded_info" in processed:
        processed["expanded_info"] = to_json_str_with_intent(processed["expanded_info"])
    return processed

