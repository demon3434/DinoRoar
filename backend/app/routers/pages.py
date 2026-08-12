import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(tags=["Web Pages"])

# Setup Jinja2 templates directory
app_dir = Path(__file__).resolve().parent.parent
templates_dir = app_dir / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@router.get("/admin")
async def get_admin_page(request: Request):
    return RedirectResponse(url="/admin/users")

@router.get("/admin/users", response_class=HTMLResponse)
async def get_admin_users_page(request: Request):
    return templates.TemplateResponse(request, "admin_users.html", {"active_tab": "admin-users-list"})

@router.get("/admin/settings", response_class=HTMLResponse)
async def get_admin_settings_page(request: Request):
    return templates.TemplateResponse(request, "admin_settings.html", {"active_tab": "admin-system-settings"})

@router.get("/admin/maintenance", response_class=HTMLResponse)
async def get_admin_maintenance_page(request: Request):
    return templates.TemplateResponse(request, "admin_maintenance.html", {"active_tab": "admin-system-maintenance"})

@router.get("/admin/personal")
async def get_admin_personal_page(request: Request):
    return RedirectResponse(url="/admin/password")

@router.get("/admin/password", response_class=HTMLResponse)
async def get_admin_password_page(request: Request):
    return templates.TemplateResponse(request, "admin_password.html", {"active_tab": "admin-personal-password"})

@router.get("/admin/theme", response_class=HTMLResponse)
async def get_admin_theme_page(request: Request):
    return templates.TemplateResponse(request, "admin_theme.html", {"active_tab": "admin-personal-theme"})

@router.get("/", response_class=HTMLResponse)
async def get_dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"active_tab": "dashboard"})

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard_tab_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"active_tab": "dashboard"})

@router.get("/diary", response_class=HTMLResponse)
async def get_diary_page(request: Request):
    return templates.TemplateResponse(request, "diary.html", {"active_tab": "diary"})

@router.get("/settings/persons", response_class=HTMLResponse)
async def get_settings_persons_page(request: Request):
    return templates.TemplateResponse(request, "settings_persons.html", {"active_tab": "settings-persons"})

@router.get("/settings/personal", response_class=HTMLResponse)
async def get_settings_personal_page(request: Request):
    return templates.TemplateResponse(request, "settings_personal.html", {"active_tab": "settings-personal"})

@router.get("/diary/detail", response_class=HTMLResponse)
async def get_diary_detail_page(request: Request):
    return templates.TemplateResponse(request, "diary_detail.html", {"active_tab": "diary"})

@router.get("/stickers", response_class=HTMLResponse)
async def get_stickers_page(request: Request):
    return templates.TemplateResponse(request, "stickers.html", {"active_tab": "mall"})

@router.get("/admin/stickers", response_class=HTMLResponse)
async def get_admin_stickers_page(request: Request):
    return templates.TemplateResponse(request, "admin_stickers.html", {"active_tab": "admin-stickers-list"})

@router.get("/mall", response_class=HTMLResponse)
async def get_mall_page(request: Request):
    return templates.TemplateResponse(request, "mall.html", {"active_tab": "mall"})

@router.get("/canvases", response_class=HTMLResponse)
async def get_canvases_page(request: Request):
    return templates.TemplateResponse(request, "canvases.html", {"active_tab": "mall"})

@router.get("/admin/canvases", response_class=HTMLResponse)
async def get_admin_canvases_page(request: Request):
    return templates.TemplateResponse(request, "admin_canvases.html", {"active_tab": "admin-canvases-list"})



