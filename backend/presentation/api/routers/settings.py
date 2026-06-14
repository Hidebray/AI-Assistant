from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from backend.presentation.api.dependencies import get_current_user
from backend.infrastructure.database.session import get_db_session
from backend.infrastructure.database.models import User, UserSetting
from backend.application.encryption import encrypt_value, decrypt_value
from backend.domain.events.base_events import SystemEvent

router = APIRouter(prefix="/api/settings", tags=["settings"])

SENSITIVE_KEYS = ["llm.openai_key", "llm.gemini_key"]

@router.get("/")
async def get_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    # Fetch user settings from DB
    stmt = select(UserSetting).where(UserSetting.user_id == current_user.id)
    result = await db.execute(stmt)
    db_settings = result.scalars().all()
    
    # Organize settings into a dict
    settings_dict = {
        "llm.openai_key": "",
        "llm.gemini_key": "",
        "llm.ollama_url": "http://localhost:11434",
        "general.theme": "dark",
        "general.language": "vi"
    }
    
    plugin_states = {}
    
    for s in db_settings:
        val = s.setting_value
        if s.setting_key in SENSITIVE_KEYS:
            val = decrypt_value(val)
            
        if s.setting_key.startswith("plugins.") and s.setting_key.endswith(".active"):
            plugin_id = s.setting_key.split(".")[1]
            plugin_states[plugin_id] = (val.lower() == "true")
        else:
            settings_dict[s.setting_key] = val

    # Merge with active plugins from PluginManager
    plugin_manager = getattr(request.app.state, "plugin_manager", None)
    plugins_data = []
    if plugin_manager:
        for p_name, p_instance in plugin_manager.loaded_plugins.items():
            meta = p_instance.get_metadata()
            is_active = plugin_states.get(p_name, False)
            plugins_data.append({
                "id": p_name,
                "name": meta.get("name", p_name),
                "version": meta.get("version", "1.0.0"),
                "source": "Local",
                "description": meta.get("description", ""),
                "isActive": is_active,
                "hasConfig": bool(meta.get("config_schema"))
            })
            
    return {
        "llm": {
            "openaiKey": settings_dict.get("llm.openai_key", ""),
            "geminiKey": settings_dict.get("llm.gemini_key", ""),
            "ollamaBaseUrl": settings_dict.get("llm.ollama_url", "http://localhost:11434")
        },
        "general": {
            "theme": settings_dict.get("general.theme", "dark"),
            "language": settings_dict.get("general.language", "vi")
        },
        "plugins": plugins_data
    }

@router.put("/")
async def update_settings(
    request: Request,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    # Expects flat key-value pairs, e.g. {"llm.openai_key": "sk-...", "plugins.mock_calendar.active": "true"}
    
    for key, value in payload.items():
        val_str = str(value)
        if key in SENSITIVE_KEYS:
            val_str = encrypt_value(val_str)
            
        stmt = select(UserSetting).where(
            UserSetting.user_id == current_user.id,
            UserSetting.setting_key == key
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.setting_value = val_str
        else:
            new_setting = UserSetting(
                user_id=current_user.id,
                setting_key=key,
                setting_value=val_str
            )
            db.add(new_setting)
            
    await db.commit()
    
    # Phát sự kiện Hot-Reload
    event_bus = getattr(request.app.state, "event_bus", None)
    if event_bus:
        try:
            hot_reload_event = SystemEvent(
                source_origin="settings_api",
                event_type="User.SettingsChanged",
                status="success",
                message=f"Settings updated: {', '.join(payload.keys())}"
            )
            await event_bus.publish(hot_reload_event)
        except Exception as e:
            # Không cho lỗi event bus phá hỏng việc save settings
            import logging
            logging.getLogger(__name__).warning(f"Failed to publish settings change event: {e}")
        
    return {"status": "success", "updated_keys": list(payload.keys())}
