from src.server.services.custom_content_service import _extract_reference_text


def test_extract_reference_text_returns_generalized_ranges():
    doc = """
类型: int
数值参考:
  - 微量: 1~2 (相当于提升1-2个小境界)
  - 中量: 3~5 (相当于提升半个大境界)
  - 大量: 8+ (相当于提升一个大境界)
"""

    result = _extract_reference_text(doc)

    assert result == "small: 1 to 2; medium: 3 to 5; large: 8+"


def test_extract_reference_text_handles_non_range_labels():
    doc = """
类型: int
数值参考:
  - 普通人: 0
  - 有福缘: 5~10
  - 主角模板: 15~25
  - 倒霉体质: -5~-10
"""

    result = _extract_reference_text(doc)

    assert result == "ordinary: 0; fortunate: 5 to 10; protagonist-tier: 15 to 25; unlucky: -5 to -10"


def test_extract_reference_text_drops_parenthetical_chinese_notes():
    doc = """
类型: float
数值参考:
  - 基础概率: 0.05 (5%)
  - 微量: 0.05 (+5%)
  - 中量: 0.1 (10%)
"""

    result = _extract_reference_text(doc)

    assert result == "base chance: 0.05; small: 0.05; medium: 0.1"
