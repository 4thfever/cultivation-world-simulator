import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from src.utils.llm.prompt import build_prompt
from src.utils.llm.parser import parse_json
from src.utils.llm.client import call_llm_json, call_llm, LLMMode
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

def test_parse_fail():
    text = "Not a json"
    with pytest.raises(ParseError):
        parse_json(text)

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
async def test_call_llm_with_urllib():
    """测试使用 urllib 调用 OpenAI 兼容接口"""
    
    # 模拟 HTTP 响应内容
    mock_response_content = json.dumps({
        "choices": [{"message": {"content": "Response from API"}}]
    }).encode('utf-8')
    
    # Mock response object
    mock_response = MagicMock()
    mock_response.read.return_value = mock_response_content
    mock_response.__enter__.return_value = mock_response
    
    # Mock Config
    mock_config = MagicMock()
    mock_config.api_key = "test_key"
    mock_config.base_url = "http://test.api/v1"
    mock_config.model_name = "test-model"

    # Patch 多个对象
    with patch("src.utils.llm.client.LLMConfig.from_mode", return_value=mock_config), \
         patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        
        result = await call_llm("hello", mode=LLMMode.NORMAL)
        
        assert result == "Response from API"
        
        # 验证 urlopen 被调用
        mock_urlopen.assert_called_once()
        
        # 验证请求参数
        args, _ = mock_urlopen.call_args
        request_obj = args[0]
        # client.py 逻辑会把 http://test.api/v1 变成 http://test.api/v1/chat/completions
        assert request_obj.full_url == "http://test.api/v1/chat/completions"
