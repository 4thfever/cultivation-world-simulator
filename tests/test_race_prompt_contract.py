from pathlib import Path


LOCALES = ("zh-CN", "zh-TW", "en-US", "vi-VN", "ja-JP")


def _template(locale: str, name: str) -> str:
    return Path("static/locales", locale, "templates", name).read_text(encoding="utf-8")


def test_action_decision_templates_prioritize_race_over_persona():
    expected = {
        "zh-CN": ("种族天性", "persona"),
        "zh-TW": ("種族天性", "persona"),
        "en-US": ("racial instinct", "persona"),
        "vi-VN": ("bản năng chủng tộc", "persona"),
        "ja-JP": ("種族本能", "persona"),
    }
    for locale, markers in expected.items():
        text = _template(locale, "ai.txt")
        for marker in markers:
            assert marker in text


def test_goal_conversation_and_story_templates_require_yao_race_expression():
    expected = {
        "zh-CN": ("妖族", "种族"),
        "zh-TW": ("妖族", "種族"),
        "en-US": ("yao", "racial"),
        "vi-VN": ("yêu tộc", "chủng tộc"),
        "ja-JP": ("妖族", "種族"),
    }
    template_names = (
        "long_term_objective.txt",
        "conversation.txt",
        "story_single.txt",
        "story_dual.txt",
        "story_gathering.txt",
    )

    for locale, markers in expected.items():
        for template_name in template_names:
            text = _template(locale, template_name)
            for marker in markers:
                assert marker.lower() in text.lower()
