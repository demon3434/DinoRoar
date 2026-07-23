import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    app_name: str = "DinoRoar"
    debug: bool = False
    secret_key: str = "dinoroar-super-secret-default-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 30  # 30 days for mobile clients

    # Database
    # Default to sqlite relative to workspace/mount root in ./data/
    data_dir: str = "./data"
    database_url: str = "sqlite:///./data/dinoroar.db"

    # LAN Discovery (mDNS) defaults
    service_discovery_name: str = "DinoRoar"
    service_discovery_type: str = "_dinoroar._tcp.local."
    service_advertise_host: str = ""
    service_advertise_port: int = 8080

    # STT Service API
    # Deployed as stt container in same compose network
    stt_api_url: str = "http://stt:18000/api/transcribe"


    # Default Admin (Father)
    default_admin_username: str = "admin"
    default_admin_password: str = "admin_123"



    # Uploads Dir
    upload_dir: str = "./uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure data and uploads directories exist
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.upload_dir, exist_ok=True)
