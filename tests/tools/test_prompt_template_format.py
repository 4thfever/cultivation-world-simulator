from pathlib import Path

from src.utils.llm.prompt import build_prompt, load_template
from src.i18n.locale_registry import get_source_locale


def test_sect_random_event_template_can_be_formatted() -> None:
    source_locale = get_source_locale()
    template_path = Path(f"static/locales/{source_locale}/templates/sect_random_event.txt")
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
    template_path = Path(f"static/locales/{get_source_locale()}/templates/sect_decider.txt")
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
    template_path = Path(f"static/locales/{source_locale}/templates/custom_goldfinger.txt")
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
