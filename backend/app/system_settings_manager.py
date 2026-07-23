import os
import json
import logging
from pathlib import Path
from threading import Lock
from .config import settings

logger = logging.getLogger("DinoRoar.system_settings_manager")

_SETTINGS_LOCK = Lock()

def get_settings_file_path() -> Path:
    # Resolves data/settings.json relative to app working dir or config data_dir
    data_dir = getattr(settings, "data_dir", "./data")
    path = Path(data_dir) / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def get_default_settings() -> dict:
    host_ip = settings.service_advertise_host or ""
    host_port = settings.service_advertise_port or 8080
    
    # 尝试自动获取本机局域网 IP 作为初始默认 IP
    if not host_ip:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            detected = s.getsockname()[0]
            if detected and detected != '127.0.0.1' and not detected.startswith("172."):
                host_ip = detected
        except Exception:
            pass
        finally:
            s.close()

    env_stt_url = os.environ.get("STT_API_URL")
    if env_stt_url and "stt:" not in env_stt_url:
        stt_url = env_stt_url.strip()
    else:
        if host_ip:
            stt_url = f"http://{host_ip}:18000/api/transcribe"
        else:
            stt_url = "http://stt:18000/api/transcribe"

    return {
        "host_ip": host_ip,
        "host_port": host_port,
        "stt_url": stt_url
    }

def load_system_settings() -> dict:
    """
    Loads system settings from data/settings.json.
    If file doesn't exist, initializes it with environment defaults.
    """
    file_path = get_settings_file_path()
    defaults = get_default_settings()

    with _SETTINGS_LOCK:
        if not file_path.exists():
            save_system_settings_internal(defaults, file_path)
            return defaults

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Fill missing keys with defaults
            updated = False
            for k, v in defaults.items():
                if k not in data:
                    data[k] = v
                    updated = True

            if updated:
                save_system_settings_internal(data, file_path)
                
            return data
        except Exception as e:
            logger.error(f"Error loading {file_path}, falling back to defaults: {e}")
            save_system_settings_internal(defaults, file_path)
            return defaults

def save_system_settings_internal(data: dict, file_path: Path):
    tmp_path = file_path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, file_path)

def update_system_settings(host_ip: str, host_port: int, stt_url: str) -> dict:
    """
    Atomically updates system settings in data/settings.json.
    """
    file_path = get_settings_file_path()
    new_data = {
        "host_ip": host_ip.strip(),
        "host_port": int(host_port),
        "stt_url": stt_url.strip()
    }
    with _SETTINGS_LOCK:
        save_system_settings_internal(new_data, file_path)
    return new_data
