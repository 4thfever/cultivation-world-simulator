from __future__ import annotations

from urllib.parse import urlparse


LOCAL_LLM_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def is_local_llm_endpoint(base_url: str) -> bool:
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    return host in LOCAL_LLM_HOSTS


def llm_requires_api_key(*, base_url: str, api_format: str = "openai") -> bool:
    if (api_format or "openai").lower() == "anthropic":
        return True
    return not is_local_llm_endpoint(base_url)


def is_llm_runtime_configured(profile, api_key: str) -> bool:
    if not profile.base_url or not profile.model_name:
        return False
    if llm_requires_api_key(base_url=profile.base_url, api_format=profile.api_format):
        return bool(api_key)
    return True
