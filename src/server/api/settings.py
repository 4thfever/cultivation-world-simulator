from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import APIRouter, HTTPException

from src.config import AppSettingsPatch, LLMSettingsUpdate
from src.utils.llm.config import LLMConfig


def create_settings_router(
    *,
    model_to_dict: Callable[[object], dict],
    get_settings_view: Callable[[], object],
    patch_settings: Callable[[AppSettingsPatch], object],
    reset_settings: Callable[[], object],
    get_llm_view: Callable[[], object],
    get_llm_runtime_config: Callable[[], tuple[object, str]],
    get_llm_test_payload: Callable[[LLMSettingsUpdate], tuple[object, str]],
    test_connectivity: Callable[..., tuple[bool, str]],
    update_llm: Callable[[LLMSettingsUpdate], object],
    on_llm_updated: Callable[[], Awaitable[None]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/settings")
    def get_settings():
        return model_to_dict(get_settings_view())

    @router.patch("/api/settings")
    def patch_settings_endpoint(req: AppSettingsPatch):
        updated = patch_settings(req)
        return model_to_dict(updated)

    @router.post("/api/settings/reset")
    def reset_settings_endpoint():
        updated = reset_settings()
        return model_to_dict(updated)

    @router.get("/api/settings/llm")
    def get_llm_settings():
        return model_to_dict(get_llm_view())

    @router.get("/api/settings/llm/status")
    def get_llm_status():
        profile, api_key = get_llm_runtime_config()
        configured = bool(profile.base_url and profile.model_name and api_key)
        return {"configured": configured}

    @router.post("/api/settings/llm/test")
    def test_llm_connection(req: LLMSettingsUpdate):
        try:
            profile, api_key = get_llm_test_payload(req)
            config = LLMConfig(
                base_url=profile.base_url,
                api_key=api_key,
                model_name=profile.model_name,
                api_format=profile.api_format,
            )
            success, error_msg = test_connectivity(config=config)
            if success:
                return {"status": "ok", "message": "连接成功"}
            raise HTTPException(status_code=400, detail=error_msg)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"测试出错: {str(exc)}")

    @router.put("/api/settings/llm")
    async def save_llm_config(req: LLMSettingsUpdate):
        try:
            updated = update_llm(req)
            await on_llm_updated()
            return {"status": "ok", "message": "配置已保存", "config": model_to_dict(updated)}
        except Exception as exc:
            import traceback

            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"保存失败: {str(exc)}")

    return router
