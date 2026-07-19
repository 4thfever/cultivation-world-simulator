from __future__ import annotations

from collections.abc import Callable

from .config import LLMConfig
from .validation import llm_requires_api_key


def check_llm_profile_connectivity(
    *,
    profile,
    api_key: str,
    test_connectivity: Callable[..., tuple[bool, str]],
) -> tuple[bool, str]:
    base_url = (profile.base_url or "").strip()
    api_format = (profile.api_format or "openai").strip() or "openai"
    model_name = (profile.model_name or "").strip()
    fast_model_name = (profile.fast_model_name or "").strip()

    if not base_url:
        return False, "LLM 配置不完整：请填写 Base URL"
    if not model_name:
        return False, "LLM 配置不完整：请填写智能模型名称"
    if not fast_model_name:
        return False, "LLM 配置不完整：请填写快速模型名称"
    if llm_requires_api_key(base_url=base_url, api_format=api_format) and not api_key:
        return False, "LLM 配置不完整：请填写 API Key"

    normal_config = LLMConfig(
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
        api_format=api_format,
    )
    success, error_msg = test_connectivity(config=normal_config)
    if not success:
        return False, f"智能模型连接失败：{error_msg}"

    if fast_model_name == model_name:
        return True, ""

    fast_config = LLMConfig(
        base_url=base_url,
        api_key=api_key,
        model_name=fast_model_name,
        api_format=api_format,
    )
    success, error_msg = test_connectivity(config=fast_config)
    if not success:
        return False, f"快速模型连接失败：{error_msg}"

    return True, ""
