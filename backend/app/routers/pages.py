from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Web Pages"])

# Setup Jinja2 templates directory
app_dir = Path(__file__).resolve().parent.parent
templates_dir = app_dir / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Setup SPA dist file path
spa_index_file = app_dir / "static" / "dist" / "index.html"

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

def _serve_spa():
    if spa_index_file.exists():
        return FileResponse(str(spa_index_file), headers=NO_CACHE_HEADERS)
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>DinoRoar - 前端资源未就绪</title></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px; background: #070f1e; color: #fff;">
            <h1>🦕 DinoRoar SPA 前端构建产物未就绪</h1>
            <p>请先在 <code>frontend/</code> 目录执行 <code>npm run build</code> 并将产物同步至 <code>backend/app/static/dist/</code>。</p>
        </body>
        </html>
        """,
        status_code=503
    )

# 1. 统一登录入口 (SPA 现代酷炫登录页)
@router.get("/login")
async def get_login_page(request: Request):
    """登录单页入口"""
    return _serve_spa()

# 2. 管理员控制台入口 (SPA 接管)
@router.get("/admin")
async def get_admin_page(request: Request):
    """管理控制台主页入口"""
    return _serve_spa()

@router.get("/admin/{subpath:path}")
async def get_admin_subpaths(request: Request, subpath: str):
    """管理控制台所有子路由入口（stickers, canvases, promotions, checkin, energy/ledger 等）"""
    return _serve_spa()

# 3. 面向普通用户（孩子端账号）的专属前台主页与完整功能
@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard_page(request: Request):
    """孩子端主控台看板"""
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"active_tab": "dashboard"})

@router.get("/diary", response_class=HTMLResponse)
async def get_diary_page(request: Request):
    """孩子日记时间轴列表"""
    return templates.TemplateResponse(request=request, name="diary.html", context={"active_tab": "diary"})

@router.get("/diary/detail", response_class=HTMLResponse)
async def get_diary_detail_page(request: Request):
    """孩子日记详情与全屏信纸大图预览"""
    return templates.TemplateResponse(request=request, name="diary_detail.html", context={"active_tab": "diary"})

@router.get("/stickers", response_class=HTMLResponse)
async def get_stickers_page(request: Request):
    """孩子贴纸背包与收集图鉴"""
    return templates.TemplateResponse(request=request, name="stickers.html", context={"active_tab": "mall"})

@router.get("/canvases", response_class=HTMLResponse)
async def get_canvases_page(request: Request):
    """孩子画布展馆"""
    return templates.TemplateResponse(request=request, name="canvases.html", context={"active_tab": "mall"})

@router.get("/mall", response_class=HTMLResponse)
async def get_mall_page(request: Request):
    """蛋能量商城与兑换"""
    return templates.TemplateResponse(request=request, name="mall.html", context={"active_tab": "mall"})

@router.get("/settings/persons", response_class=HTMLResponse)
async def get_settings_persons_page(request: Request):
    """孩子亲友羁绊卡片"""
    return templates.TemplateResponse(request=request, name="settings_persons.html", context={"active_tab": "settings-persons"})

@router.get("/settings/personal", response_class=HTMLResponse)
async def get_settings_personal_page(request: Request):
    """孩子个人偏好与恐龙九宫格设置"""
    return templates.TemplateResponse(request=request, name="settings_personal.html", context={"active_tab": "settings-personal"})

@router.get("/")
async def get_root_page(request: Request):
    """根路径入口"""
    return _serve_spa()
