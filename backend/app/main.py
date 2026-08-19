import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base, SessionLocal
from .services.mdns_discovery import broadcaster, get_mdns_settings_and_start
from .services.system_init import init_system_data

# Configure root logger
logger = logging.getLogger("DinoRoar")
logger.setLevel(logging.INFO)

# Setup Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables & seed default data
    try:
        from . import models
        Base.metadata.create_all(bind=engine)
        logger.info("Database: Tables verified/created successfully.")
        
        db = SessionLocal()
        try:
            init_system_data(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database: Failed to check/create tables or seed default data: {e}")

    # Start mDNS Broadcaster in background thread to avoid blocking main event loop
    try:
        import asyncio
        await asyncio.to_thread(get_mdns_settings_and_start)
    except Exception as mdns_err:
        logger.error(f"Lifespan: Error starting mDNS broadcaster: {mdns_err}")

    # Start background task to compress historical uploads (lossless optimization)
    try:
        from .services.compress_historical import start_historical_compression
        start_historical_compression()
    except Exception as compress_err:
        logger.error(f"Error starting historical image compression: {compress_err}")
    
    yield
    
    # Shutdown: Stop mDNS Broadcaster
    logger.info("Lifespan: Stopping mDNS broadcaster...")
    try:
        import asyncio
        await asyncio.to_thread(broadcaster.stop)
    except Exception as mdns_stop_err:
        logger.error(f"Lifespan: Error stopping mDNS broadcaster: {mdns_stop_err}")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan
)

# Register Routers
from .routers import (
    auth, logs, attachments, admin_users, 
    pages, persons, categories, dino_config, stickers, stt, canvases, shop,
    checkin, energy
)
app.include_router(auth.router)
app.include_router(logs.router)
app.include_router(attachments.router)
app.include_router(admin_users.router)
app.include_router(pages.router)
app.include_router(persons.router)
app.include_router(categories.router)
app.include_router(dino_config.router)
app.include_router(stickers.router)
app.include_router(stt.router)
app.include_router(canvases.router)
app.include_router(shop.router)
app.include_router(checkin.router)
app.include_router(energy.router)


# Mount Static Files
from pathlib import Path
uploads_dir = Path(settings.upload_dir)
uploads_dir.mkdir(parents=True, exist_ok=True)
static_dir = Path(__file__).resolve().parent / "static"
dist_assets_dir = static_dir / "dist" / "assets"
if dist_assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(dist_assets_dir)), name="assets")

app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """
    系统健康检查接口
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "mdns_active": broadcaster.zc is not None,
        "advertised_address": f"{broadcaster.active_host}:{broadcaster.active_port}" if broadcaster.active_host else None
    }
