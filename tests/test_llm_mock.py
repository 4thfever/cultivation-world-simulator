import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from src.utils.llm.prompt import build_prompt
from src.utils.llm.parser import parse_json, try_parse_code_blocks, try_parse_balanced_json
from src.utils.llm.client import call_llm_json, LLMMode
from src.utils.llm.exceptions import ParseError, LLMError

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

def test_parse_nested_braces():
    text = 'some text {"a": {"b": 1}} some more text'
    result = parse_json(text)
    assert result == {"a": {"b": 1}}

def test_parse_fail():
    text = "Not a json"
    with pytest.raises(ParseError):
        parse_json(text)

def test_extract_from_text_with_noise():
    text = "Sure! Here is the JSON you requested: {\"a\": 1} Hope this helps."
    result = parse_json(text)
    assert result == {"a": 1}

# ================= Client Mock Tests =================
@pytest.mark.asyncio
async def test_call_llm_json_success():
    # Mock call_llm to return a valid JSON string
    with patch("src.utils.llm.client.call_llm", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = '{"success": true}'
        
        result = await call_llm_json("prompt", mode=LLMMode.NORMAL)
        assert result == {"success": True}
        mock_call.assert_called_once()

@pytest.mark.asyncio
async def test_call_llm_json_retry_success():
    # Mock call_llm to fail once (bad json) then succeed
    with patch("src.utils.llm.client.call_llm", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = ["Bad JSON", '{"success": true}']
        
        # We need to make sure config max_retries is at least 1
        # pass max_retries explicitly
        result = await call_llm_json("prompt", mode=LLMMode.NORMAL, max_retries=1)
        
        assert result == {"success": True}
        assert mock_call.call_count == 2

@pytest.mark.asyncio
async def test_call_llm_json_all_fail():
    with patch("src.utils.llm.client.call_llm", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "Bad JSON"
        
        with pytest.raises(LLMError):
            await call_llm_json("prompt", mode=LLMMode.NORMAL, max_retries=1)
        
        assert mock_call.call_count == 2 # Initial + 1 retry

