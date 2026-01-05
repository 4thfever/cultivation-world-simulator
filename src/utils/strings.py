def to_json_str_with_intent(data, unescape_newlines: bool = True) -> str:
    """
    将 Python 对象转为格式化的 JSON 字符串，用于 LLM prompt 模板填充。

    Args:
        data: 任意可 JSON 序列化的对象（dict, list 等）。
        unescape_newlines: 是否将 JSON 中的 '\\n' 转为真正的换行符，默认 True。

    Returns:
        格式化的 JSON 字符串，带缩进，中文保持原样（不转为 \\uXXXX）。

    Note:
        返回的字符串可安全用于 str.format()，因为 format() 不会递归解析已替换的内容。
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
    if "world_info" in processed:
        processed["world_info"] = to_json_str_with_intent(processed["world_info"])
    if "general_action_infos" in processed:
        processed["general_action_infos"] = to_json_str_with_intent(processed["general_action_infos"])
    if "expanded_info" in processed:
        processed["expanded_info"] = to_json_str_with_intent(processed["expanded_info"])
    return processed

