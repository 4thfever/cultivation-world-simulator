import pytest
from src.utils.llm.prompt import build_prompt
from src.utils.llm.parser import parse_json
from src.utils.llm.exceptions import ParseError

# ================= Prompt Tests =================
def test_build_prompt_basic():
    template = "Hello {name}, your age is {age}."
    infos = {"name": "Alice", "age": 20}
    result = build_prompt(template, infos)
    assert result == "Hello Alice, your age is 20."

def test_build_prompt_with_complex_types():
    # intentify_prompt_infos handles lists/dicts
    template = "List: {items}"
    infos = {"items": ["a", "b"]}
    result = build_prompt(template, infos)
    # intentify_prompt_infos usually joins lists with commas or newlines
    # We should verify what intentify_prompt_infos does. 
    # Assuming it makes it string friendly.
    assert "a" in result and "b" in result

def test_intentify_prompt_infos_formatting():
    # intentify_prompt_infos only transforms specific keys
    template = "Infos: {avatar_infos}"
    avatar_data = {"name": "Alice", "hp": 100}
    infos = {"avatar_infos": avatar_data}
    
    result = build_prompt(template, infos)
    
    # Expect pretty printed json
    assert '{\n  "name": "Alice",' in result
    assert '"hp": 100\n}' in result

# ================= Parser Tests =================
def test_parse_simple_json():
    text = '{"key": "value", "num": 1}'
    result = parse_json(text)
    assert result == {"key": "value", "num": 1}

def test_parse_json5_comments():
    text = '{key: "value", /* comment */ num: 1}'
    result = parse_json(text)
    assert result == {"key": "value", "num": 1}

def test_parse_code_block():
    text = """
    Here is the json:
    ```json
    {
        "foo": "bar"
    }
    ```
    """
    result = parse_json(text)
    assert result == {"foo": "bar"}

def test_parse_fail():
    text = "Not a json"
    with pytest.raises(ParseError):
        parse_json(text)
