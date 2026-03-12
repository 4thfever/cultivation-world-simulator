from pathlib import Path

from src.utils.llm.prompt import build_prompt, load_template


def test_sect_random_event_template_can_be_formatted() -> None:
    template_path = Path("static/locales/zh-CN/templates/sect_random_event.txt")
    template = load_template(template_path)

    infos = {
        "language": "zh-CN",
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
