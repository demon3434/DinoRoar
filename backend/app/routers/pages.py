from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(tags=["Web Pages"])

# Setup SPA dist file path
app_dir = Path(__file__).resolve().parent.parent
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

@router.get("/login")
async def get_login_page(request: Request):
    """登录单页入口"""
    return _serve_spa()

@router.get("/admin")
async def get_admin_page(request: Request):
    """管理控制台主页入口"""
    return _serve_spa()

@router.get("/admin/{subpath:path}")
async def get_admin_subpaths(request: Request, subpath: str):
    """管理控制台所有子路由入口（stickers, canvases, promotions, checkin, energy/ledger 等）"""
    return _serve_spa()

@router.get("/")
async def get_root_page(request: Request):
    """根路径入口（由前端 Vue Router 自动重定向至 /admin/stickers）"""
    return _serve_spa()
