"""助手设定：读取与更新运行时参数。"""
from fastapi import APIRouter

from backend.runtime import load_runtime, save_runtime
from backend.schemas.settings import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings_api() -> SettingsOut:
    """返回当前生效的助手设定。"""
    runtime = load_runtime()
    return SettingsOut(**runtime.model_dump())


@router.put("", response_model=SettingsOut)
def update_settings_api(body: SettingsUpdate) -> SettingsOut:
    """更新设定并立即生效（下次问答起）。"""
    patch = body.model_dump(exclude_unset=True)
    runtime = save_runtime(patch)
    return SettingsOut(**runtime.model_dump())
