"""
Tests for LLM failure scenarios and error handling.

## What's Tested

- HTTP error handling (401, 403, 404, 500, timeout)
- Parse error handling (invalid JSON, empty response)
- Retry logic (retry on parse failure, max retries exceeded)
- Connectivity test (llm_test_connectivity returns friendly error messages)
- Configuration validation (missing API key, missing base URL)

## Why These Tests Matter

LLM calls are critical to the game's AI decision making. When LLM fails:
1. The game should handle errors gracefully, not crash.
2. Users should see friendly error messages, not raw exceptions.
3. Retry logic should work correctly for transient failures.
"""

import pytest
import json
import urllib.error
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO

from src.utils.llm.client import (
    call_llm,
    call_llm_json,
    call_llm_with_template,
    call_llm_with_task_name,
    test_connectivity as llm_test_connectivity,
    _call_with_requests,
    LLMMode,
)
from src.utils.llm.config import LLMConfig
from src.utils.llm.parser import parse_json
from src.utils.llm.exceptions import LLMError, ParseError


def make_http_error(url: str, code: int, msg: str, body: bytes) -> urllib.error.HTTPError:
    """Create an HTTPError for testing. The hdrs param type is incorrectly typed in stubs."""
    return urllib.error.HTTPError(
        url=url,
        code=code,
        msg=msg,
        hdrs=None,  # type: ignore[arg-type]
        fp=BytesIO(body)
    )


class TestHTTPErrors:
    """Tests for HTTP error handling in LLM client."""

    def test_401_unauthorized(self):
        """Test handling of 401 Unauthorized (invalid API key)."""
        config = LLMConfig(
            model_name="test-model",
            api_key="invalid-key",
            base_url="http://test.api/v1"
        )

        # Create a mock HTTPError for 401.
        http_error = make_http_error(
            url="http://test.api/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            body=b'{"error": {"message": "Invalid API key"}}'
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            with pytest.raises(Exception) as exc_info:
                _call_with_requests(config, "test prompt")

            assert "401" in str(exc_info.value)
            assert "Invalid API key" in str(exc_info.value)

    def test_403_forbidden(self):
        """Test handling of 403 Forbidden (access denied)."""
        config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        http_error = make_http_error(
            url="http://test.api/v1/chat/completions",
            code=403,
            msg="Forbidden",
            body=b'{"error": {"message": "Access denied"}}'
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            with pytest.raises(Exception) as exc_info:
                _call_with_requests(config, "test prompt")

            assert "403" in str(exc_info.value)

    def test_404_not_found(self):
        """Test handling of 404 Not Found (wrong URL)."""
        config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/wrong-path"
        )

        http_error = make_http_error(
            url="http://test.api/wrong-path/chat/completions",
            code=404,
            msg="Not Found",
            body=b'{"error": {"message": "Not found"}}'
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            with pytest.raises(Exception) as exc_info:
                _call_with_requests(config, "test prompt")

            assert "404" in str(exc_info.value)

    def test_500_server_error(self):
        """Test handling of 500 Internal Server Error."""
        config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        http_error = make_http_error(
            url="http://test.api/v1/chat/completions",
            code=500,
            msg="Internal Server Error",
            body=b'{"error": {"message": "Internal server error"}}'
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            with pytest.raises(Exception) as exc_info:
                _call_with_requests(config, "test prompt")

            assert "500" in str(exc_info.value)

    def test_timeout_error(self):
        """Test handling of connection timeout."""
        config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        timeout_error = TimeoutError("Connection timed out")

        with patch("urllib.request.urlopen", side_effect=timeout_error):
            with pytest.raises(Exception) as exc_info:
                _call_with_requests(config, "test prompt")

            assert "timed out" in str(exc_info.value).lower()

    def test_connection_refused(self):
        """Test handling of connection refused error."""
        config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://localhost:9999"
        )

        connection_error = ConnectionRefusedError("Connection refused")

        with patch("urllib.request.urlopen", side_effect=connection_error):
            with pytest.raises(Exception) as exc_info:
                _call_with_requests(config, "test prompt")

            assert "Connection refused" in str(exc_info.value)


class TestParseErrors:
    """Tests for JSON parse error handling."""

    def test_invalid_json_response(self):
        """Test handling of invalid JSON in LLM response."""
        text = "This is not valid JSON at all"

        with pytest.raises(ParseError) as exc_info:
            parse_json(text)

        assert "无法解析 JSON" in str(exc_info.value)

    def test_empty_response(self):
        """Test handling of empty response."""
        result = parse_json("")
        assert result == {}

        result = parse_json("   ")
        assert result == {}

    def test_json_array_instead_of_object(self):
        """Test handling of JSON array when object expected."""
        text = '[1, 2, 3]'

        with pytest.raises(ParseError):
            parse_json(text)

    def test_partial_json(self):
        """Test handling of incomplete/truncated JSON."""
        text = '{"key": "value", "incomplete'

        with pytest.raises(ParseError):
            parse_json(text)

    def test_json_with_markdown_but_invalid_content(self):
        """Test handling of markdown code block with invalid JSON."""
        text = """
        Here is the response:
        ```json
        {not valid json}
        ```
        """

        with pytest.raises(ParseError):
            parse_json(text)


class TestRetryLogic:
    """Tests for LLM retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_parse_failure_then_success(self):
        """Test that retry works when first response is unparseable."""
        with patch("src.utils.llm.client.call_llm", new_callable=AsyncMock) as mock_call:
            # First call returns invalid JSON, second returns valid JSON.
            mock_call.side_effect = [
                "Invalid JSON response",
                '{"success": true}'
            ]

            result = await call_llm_json("prompt", max_retries=1)

            assert result == {"success": True}
            assert mock_call.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that LLMError is raised after max retries."""
        with patch("src.utils.llm.client.call_llm", new_callable=AsyncMock) as mock_call:
            # All calls return invalid JSON.
            mock_call.return_value = "Always invalid"

            with pytest.raises(LLMError) as exc_info:
                await call_llm_json("prompt", max_retries=2)

            # Should have tried 3 times (initial + 2 retries).
            assert mock_call.call_count == 3
            assert "重试" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_retry_when_max_retries_zero(self):
        """Test that no retry happens when max_retries=0."""
        with patch("src.utils.llm.client.call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Invalid JSON"

            with pytest.raises(LLMError):
                await call_llm_json("prompt", max_retries=0)

            # Should only try once.
            assert mock_call.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_preserves_mode(self):
        """Test that retry uses the same LLM mode."""
        with patch("src.utils.llm.client.call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                "Invalid",
                '{"ok": true}'
            ]

            await call_llm_json("prompt", mode=LLMMode.FAST, max_retries=1)

            # Both calls should use FAST mode.
            for call in mock_call.call_args_list:
                assert call.kwargs.get("mode") == LLMMode.FAST or call.args[1] == LLMMode.FAST


class TestConnectivityTest:
    """Tests for llm_test_connectivity function."""

    def test_connectivity_success(self):
        """Test successful connectivity check."""
        mock_response_content = json.dumps({
            "choices": [{"message": {"content": "OK"}}]
        }).encode('utf-8')

        mock_response = MagicMock()
        mock_response.read.return_value = mock_response_content
        mock_response.__enter__.return_value = mock_response

        mock_config = LLMConfig(
            model_name="test-model",
            api_key="valid-key",
            base_url="http://test.api/v1"
        )

        with patch("urllib.request.urlopen", return_value=mock_response):
            success, error = llm_test_connectivity(config=mock_config)

        assert success is True
        assert error == ""

    def test_connectivity_invalid_api_key(self):
        """Test connectivity check with invalid API key."""
        http_error = make_http_error(
            url="http://test.api/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            body=b'{"error": {"message": "Incorrect API key"}}'
        )

        mock_config = LLMConfig(
            model_name="test-model",
            api_key="invalid-key",
            base_url="http://test.api/v1"
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            success, error = llm_test_connectivity(config=mock_config)

        assert success is False
        assert "API Key 无效" in error

    def test_connectivity_forbidden(self):
        """Test connectivity check with 403 Forbidden."""
        http_error = make_http_error(
            url="http://test.api/v1/chat/completions",
            code=403,
            msg="Forbidden",
            body=b'{"error": {"message": "Forbidden"}}'
        )

        mock_config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            success, error = llm_test_connectivity(config=mock_config)

        assert success is False
        assert "访问被拒绝" in error

    def test_connectivity_not_found(self):
        """Test connectivity check with 404 Not Found."""
        http_error = make_http_error(
            url="http://test.api/wrong/chat/completions",
            code=404,
            msg="Not Found",
            body=b'{"error": {"message": "Not found"}}'
        )

        mock_config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/wrong"
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            success, error = llm_test_connectivity(config=mock_config)

        assert success is False
        assert "服务地址不存在" in error

    def test_connectivity_timeout(self):
        """Test connectivity check with timeout."""
        mock_config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            success, error = llm_test_connectivity(config=mock_config)

        assert success is False
        assert "超时" in error

    def test_connectivity_connection_error(self):
        """Test connectivity check with connection error."""
        mock_config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://localhost:9999"
        )

        with patch("urllib.request.urlopen", side_effect=ConnectionError("Connection refused")):
            success, error = llm_test_connectivity(config=mock_config)

        assert success is False
        assert "无法连接" in error

    def test_connectivity_with_mode_instead_of_config(self):
        """Test connectivity using mode parameter (config=None path)."""
        mock_config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        mock_response_content = json.dumps({
            "choices": [{"message": {"content": "OK"}}]
        }).encode('utf-8')

        mock_response = MagicMock()
        mock_response.read.return_value = mock_response_content
        mock_response.__enter__.return_value = mock_response

        with patch("src.utils.llm.client.LLMConfig.from_mode", return_value=mock_config) as mock_from_mode, \
             patch("urllib.request.urlopen", return_value=mock_response):
            # Pass mode, not config - this exercises line 161.
            success, error = llm_test_connectivity(mode=LLMMode.FAST)

        assert success is True
        mock_from_mode.assert_called_once_with(LLMMode.FAST)

    def test_connectivity_unknown_error(self):
        """Test connectivity with unknown error returns raw message."""
        mock_config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        # An error that doesn't match any known pattern.
        unknown_error = Exception("Some weird error xyz123")

        with patch("urllib.request.urlopen", side_effect=unknown_error):
            success, error = llm_test_connectivity(config=mock_config)

        assert success is False
        # Should return the raw error message.
        assert "Some weird error xyz123" in error


class TestConfigurationValidation:
    """Tests for configuration validation."""

    def test_missing_base_url(self):
        """Test error when base URL is missing."""
        config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url=""
        )

        with pytest.raises(ValueError) as exc_info:
            _call_with_requests(config, "test prompt")

        assert "Base URL is required" in str(exc_info.value)

    def test_url_normalization_adds_chat_completions(self):
        """Test that URL is normalized to include chat/completions."""
        config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        mock_response_content = json.dumps({
            "choices": [{"message": {"content": "OK"}}]
        }).encode('utf-8')

        mock_response = MagicMock()
        mock_response.read.return_value = mock_response_content
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            _call_with_requests(config, "test")

            # Verify URL was normalized.
            args, _ = mock_urlopen.call_args
            request_obj = args[0]
            assert request_obj.full_url == "http://test.api/v1/chat/completions"

    def test_url_normalization_preserves_existing_path(self):
        """Test that URL already containing chat/completions is not modified."""
        config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1/chat/completions"
        )

        mock_response_content = json.dumps({
            "choices": [{"message": {"content": "OK"}}]
        }).encode('utf-8')

        mock_response = MagicMock()
        mock_response.read.return_value = mock_response_content
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            _call_with_requests(config, "test")

            args, _ = mock_urlopen.call_args
            request_obj = args[0]
            # Should not double the path.
            assert request_obj.full_url == "http://test.api/v1/chat/completions"


class TestAsyncCallLLM:
    """Tests for async call_llm function."""

    @pytest.mark.asyncio
    async def test_call_llm_success(self):
        """Test successful async LLM call."""
        mock_response_content = json.dumps({
            "choices": [{"message": {"content": "Hello from LLM"}}]
        }).encode('utf-8')

        mock_response = MagicMock()
        mock_response.read.return_value = mock_response_content
        mock_response.__enter__.return_value = mock_response

        mock_config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        with patch("src.utils.llm.client.LLMConfig.from_mode", return_value=mock_config), \
             patch("urllib.request.urlopen", return_value=mock_response):
            result = await call_llm("test prompt")

        assert result == "Hello from LLM"

    @pytest.mark.asyncio
    async def test_call_llm_propagates_error(self):
        """Test that errors from _call_with_requests propagate."""
        mock_config = LLMConfig(
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.api/v1"
        )

        http_error = make_http_error(
            url="http://test.api/v1/chat/completions",
            code=500,
            msg="Internal Server Error",
            body=b'{"error": "Server error"}'
        )

        with patch("src.utils.llm.client.LLMConfig.from_mode", return_value=mock_config), \
             patch("urllib.request.urlopen", side_effect=http_error):
            with pytest.raises(Exception) as exc_info:
                await call_llm("test prompt")

            assert "500" in str(exc_info.value)


class TestLLMErrorException:
    """Tests for LLMError exception class."""

    def test_llm_error_with_cause(self):
        """Test LLMError preserves cause exception."""
        cause = ParseError("Parse failed", raw_text="bad json")
        error = LLMError("LLM call failed", cause=cause)

        assert error.cause is cause
        assert "LLM call failed" in str(error)

    def test_llm_error_with_context(self):
        """Test LLMError stores context."""
        error = LLMError("Failed", prompt="test", retries=3)

        assert error.context["prompt"] == "test"
        assert error.context["retries"] == 3

    def test_parse_error_stores_raw_text(self):
        """Test ParseError stores raw text."""
        error = ParseError("Invalid JSON", raw_text="not json")

        assert error.raw_text == "not json"


class TestCallLLMWithTemplate:
    """Tests for call_llm_with_template function."""

    @pytest.mark.asyncio
    async def test_call_with_template_success(self):
        """Test successful call with template."""
        with patch("src.utils.llm.client.load_template", return_value="Hello {name}!"), \
             patch("src.utils.llm.client.call_llm_json", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"greeting": "Hello World!"}

            result = await call_llm_with_template(
                template_path="test.txt",
                infos={"name": "World"}
            )

            assert result == {"greeting": "Hello World!"}
            # Verify prompt was built correctly.
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert "Hello World!" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_call_with_template_passes_mode(self):
        """Test that mode is passed through."""
        with patch("src.utils.llm.client.load_template", return_value="Test"), \
             patch("src.utils.llm.client.call_llm_json", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {}

            await call_llm_with_template(
                template_path="test.txt",
                infos={},
                mode=LLMMode.FAST
            )

            call_args = mock_call.call_args
            assert call_args[0][1] == LLMMode.FAST

    @pytest.mark.asyncio
    async def test_call_with_template_passes_max_retries(self):
        """Test that max_retries is passed through."""
        with patch("src.utils.llm.client.load_template", return_value="Test"), \
             patch("src.utils.llm.client.call_llm_json", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {}

            await call_llm_with_template(
                template_path="test.txt",
                infos={},
                max_retries=5
            )

            call_args = mock_call.call_args
            assert call_args[0][2] == 5


class TestCallLLMWithTaskName:
    """Tests for call_llm_with_task_name function."""

    @pytest.mark.asyncio
    async def test_call_with_task_name_uses_task_mode(self):
        """Test that task mode is determined from task name."""
        with patch("src.utils.llm.client.get_task_mode", return_value=LLMMode.FAST) as mock_get_mode, \
             patch("src.utils.llm.client.call_llm_with_template", new_callable=AsyncMock) as mock_call, \
             patch("src.utils.llm.client.CONFIG") as mock_config:
            mock_config.llm.mode = "default"
            mock_call.return_value = {}

            await call_llm_with_task_name(
                task_name="test_task",
                template_path="test.txt",
                infos={}
            )

            mock_get_mode.assert_called_once_with("test_task")
            # call_llm_with_template(template_path, infos, mode, max_retries)
            call_args = mock_call.call_args[0]
            assert call_args[2] == LLMMode.FAST

    @pytest.mark.asyncio
    async def test_call_with_task_name_global_mode_override(self):
        """Test that global mode overrides task mode."""
        with patch("src.utils.llm.client.get_task_mode", return_value=LLMMode.FAST), \
             patch("src.utils.llm.client.call_llm_with_template", new_callable=AsyncMock) as mock_call, \
             patch("src.utils.llm.client.CONFIG") as mock_config:
            # Global mode is "normal", should override task mode "fast".
            mock_config.llm.mode = "normal"
            mock_call.return_value = {}

            await call_llm_with_task_name(
                task_name="test_task",
                template_path="test.txt",
                infos={}
            )

            call_args = mock_call.call_args
            # Should use NORMAL due to global override.
            assert call_args[0][2] == LLMMode.NORMAL

    @pytest.mark.asyncio
    async def test_call_with_task_name_passes_max_retries(self):
        """Test that max_retries is passed through."""
        with patch("src.utils.llm.client.get_task_mode", return_value=LLMMode.NORMAL), \
             patch("src.utils.llm.client.call_llm_with_template", new_callable=AsyncMock) as mock_call, \
             patch("src.utils.llm.client.CONFIG") as mock_config:
            mock_config.llm.mode = "default"
            mock_call.return_value = {}

            await call_llm_with_task_name(
                task_name="test_task",
                template_path="test.txt",
                infos={},
                max_retries=3
            )

            call_args = mock_call.call_args
            assert call_args[0][3] == 3
