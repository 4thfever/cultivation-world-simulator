from pathlib import Path

from src.utils.llm.prompt import build_prompt, load_template
from src.i18n.locale_registry import get_project_root, get_source_locale


def test_sect_random_event_template_can_be_formatted() -> None:
    source_locale = get_source_locale()
    template_path = get_project_root() / "static" / "locales" / source_locale / "templates" / "sect_random_event.txt"
    template = load_template(template_path)

    infos = {
        "language": source_locale,
        "event_type": "relation_down",
        "sect_a_name": "A宗",
        "sect_b_name": "B宗",
        "sect_a_detail": "A sect detail",
        "sect_b_detail": "B sect detail",
        "value": 12,
        "duration_months": 60,
        "target_chars": 20,
    }

    prompt = build_prompt(template, infos)

    assert "reason_fragment" in prompt
    assert "A宗" in prompt
    assert "B宗" in prompt


def test_sect_decider_template_can_be_formatted() -> None:
    template_path = get_project_root() / "static" / "locales" / get_source_locale() / "templates" / "sect_decider.txt"
    template = load_template(template_path)

    infos = {
        "sect_name": "A宗",
        "world_info": "{}",
        "world_lore": "",
        "decision_context_info": "{}",
        "recruit_cost": 500,
        "support_amount": 300,
    }

    prompt = build_prompt(template, infos)

    assert "recruit_avatar_ids" in prompt
    assert "A宗" in prompt


def test_custom_goldfinger_template_can_be_formatted() -> None:
    source_locale = get_source_locale()
    template_path = get_project_root() / "static" / "locales" / source_locale / "templates" / "custom_goldfinger.txt"
    template = load_template(template_path)

    infos = {
        "allowed_effects": "- extra_luck: 气运, 值类型 int, 示例 2",
        "user_prompt": "我想要一个偏签到流、数值稍强的外挂",
    }

    prompt = build_prompt(template, infos)

    assert "外挂" in prompt or "goldfinger" in prompt
    assert "\"thinking\"" in prompt
    assert "extra_luck" in prompt
    assert "我想要一个偏签到流、数值稍强的外挂" in prompt


def test_roleplay_conversation_turn_template_can_be_formatted() -> None:
    source_locale = get_source_locale()
    template_path = get_project_root() / "static" / "locales" / source_locale / "templates" / "roleplay_conversation_turn.txt"
    template = load_template(template_path)

    infos = {
        "avatar_name": "闻人雾",
        "target_avatar_name": "叶明",
        "world_info": "仙道昌盛，宗门林立。",
        "avatar_infos": "{\"闻人雾\": \"散修\", \"叶明\": \"宗门弟子\"}",
        "conversation_history": "闻人雾：道友安好。\n叶明：有何贵干？",
    }

    prompt = build_prompt(template, infos)

    assert "闻人雾" in prompt
    assert "叶明" in prompt
    assert "reply_content" in prompt
    assert "speaker_thinking" in prompt


def test_relation_delta_template_can_be_formatted() -> None:
    source_locale = get_source_locale()
    template_path = get_project_root() / "static" / "locales" / source_locale / "templates" / "relation_delta.txt"
    template = load_template(template_path)

    infos = {
        "min_delta": -5,
        "max_delta": 5,
        "avatar_a_name": "闻人雾",
        "avatar_a_personas": "谨慎, 好胜",
        "avatar_a_to_b_friendliness": "普通",
        "avatar_a_to_b_numeric_relation": 3,
        "avatar_b_name": "叶明",
        "avatar_b_personas": "冷静, 寡言",
        "avatar_b_to_a_friendliness": "中立",
        "avatar_b_to_a_numeric_relation": 1,
        "identity_relations": "同道",
        "event_text": "两人偶遇后寒暄数句，气氛尚算平和。",
    }

    prompt = build_prompt(template, infos)

    assert "delta_a_to_b" in prompt
    assert "delta_b_to_a" in prompt
    assert "闻人雾" in prompt
    assert "叶明" in prompt
