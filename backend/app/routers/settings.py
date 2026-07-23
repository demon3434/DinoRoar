import logging
import os
from fastapi import APIRouter, Depends, BackgroundTasks
from ..models import User
from ..schemas import SystemSettingResponse, SystemSettingUpdate
from ..auth import get_current_admin
from ..system_settings_manager import load_system_settings, update_system_settings

logger = logging.getLogger("DinoRoar.settings")

router = APIRouter(prefix="/api/settings", tags=["System Settings"])

@router.get("", response_model=SystemSettingResponse)
async def get_settings():
    """
    Retrieves the system settings from data/settings.json.
    Accessible by logged-in users and public client discovery checks.
    """
    return load_system_settings()

@router.put("", response_model=SystemSettingResponse)
async def update_settings(
    payload: SystemSettingUpdate,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin)
):
    """
    Updates system settings in data/settings.json and dynamically updates
    the mDNS Zeroconf service broadcast in background.
    Requires administrator privileges.
    """
    current_settings = load_system_settings()
    new_ip = payload.host_ip.strip()
    new_port = payload.host_port

    ip_or_port_changed = (current_settings.get("host_ip") != new_ip) or (current_settings.get("host_port") != new_port)

    env_stt_url = os.environ.get("STT_API_URL")
    if env_stt_url and "stt:" not in env_stt_url:
        stt_url = env_stt_url.strip()
    elif payload.stt_url and payload.stt_url.strip():
        stt_url = payload.stt_url.strip()
    else:
        stt_url = f"http://{new_ip}:18000/api/transcribe"

    updated = update_system_settings(
        host_ip=new_ip,
        host_port=new_port,
        stt_url=stt_url
    )

    # Dynamic reload of mDNS broadcaster via background tasks if IP or Port changed
    if ip_or_port_changed:
        try:
            from ..main import broadcaster
            if new_ip:
                background_tasks.add_task(broadcaster.start, new_ip, new_port)
            else:
                background_tasks.add_task(broadcaster.stop)
        except Exception as e:
            logger.warning(f"Failed to queue mDNS broadcast update: {e}")

    return updated
