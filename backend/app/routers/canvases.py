import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..models import User, CanvasSeries, CanvasSet, CanvasInstance
from ..schemas import (
    CanvasSeriesResponse,
    CanvasSetResponse,
    CanvasInstanceResponse,
    CanvasSyncPayload
)
from ..auth import get_current_user
from ..services import canvases_service

router = APIRouter(prefix="/api/canvases", tags=["Canvases"])

class CanvasExchangeRequest(BaseModel):
    canvas_set_id: int

class CanvasSeriesCreate(BaseModel):
    name: str
    sort_order: int = 0

class CanvasSetCreate(BaseModel):
    series_id: int
    name: str
    description: Optional[str] = None
    exchange_price: int = 50
    sort_order: int = 0

class CanvasSeriesUpdate(BaseModel):
    name: str
    sort_order: int

class CanvasSetUpdate(BaseModel):
    series_id: int
    name: str
    description: Optional[str] = None
    exchange_price: int = 50
    sort_order: int = 0

class CanvasSeriesSortPayload(BaseModel):
    series_ids: List[int]

class CanvasSetSortPayload(BaseModel):
    set_ids: List[int]


@router.get("/config", response_model=List[CanvasSeriesResponse])
async def get_canvases_config(db: Session = Depends(get_db)):
    """
    获取系统中所有可用的画布系列及内部嵌套的画布套、图片实例列表
    """
    return canvases_service.get_canvases_config(db, only_active=True)


@router.get("/inventory", response_model=CanvasSyncPayload)
async def get_canvas_inventory(current_user: User = Depends(get_current_user)):
    """
    获取当前登录账户的背景画布资产（已购画布套件列表和蛋能量）
    """
    return {
        "canvas_inventory": current_user.canvas_inventory,
        "egg_energy": current_user.egg_energy
    }


@router.post("/inventory", response_model=CanvasSyncPayload)
async def sync_canvas_inventory(
    payload: CanvasSyncPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    同步客户端上报的背景画布持有库
    """
    current_user.canvas_inventory = payload.canvas_inventory
    if payload.egg_energy > current_user.egg_energy:
        current_user.egg_energy = payload.egg_energy
    db.commit()
    db.refresh(current_user)
    return {
        "canvas_inventory": current_user.canvas_inventory,
        "egg_energy": current_user.egg_energy
    }


@router.post("/exchange", response_model=CanvasSyncPayload)
async def exchange_canvas(
    payload: CanvasExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    自主消耗蛋能量购买兑换整套背景画布
    """
    cset = db.query(CanvasSet).filter(CanvasSet.id == payload.canvas_set_id, CanvasSet.is_deleted == False, CanvasSet.is_active == True).first()
    if not cset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="背景画布不存在或已被下架"
        )

    inventory_list = [x.strip() for x in current_user.canvas_inventory.split(",") if x.strip()]
    if str(cset.id) in inventory_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已拥有该背景画布套件，无需重复兑换"
        )

    if current_user.egg_energy < cset.exchange_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"能量不足！兑换需要 {cset.exchange_price} 蛋能量，当前仅有 {current_user.egg_energy}"
        )

    current_user.egg_energy -= cset.exchange_price
    inventory_list.append(str(cset.id))
    current_user.canvas_inventory = ",".join(inventory_list)

    db.commit()
    db.refresh(current_user)
    return {
        "canvas_inventory": current_user.canvas_inventory,
        "egg_energy": current_user.egg_energy
    }


# ==================== 管理员后台配置接口 ====================

@router.get("/admin/config", response_model=List[CanvasSeriesResponse])
async def get_admin_canvases_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员获取系统中所有未被删除的画布系列、套件及图片列表 (包含启用的与停用的)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    return canvases_service.get_canvases_config(db, only_active=False)


@router.post("/admin/series", response_model=CanvasSeriesResponse)
async def create_canvas_series(
    payload: CanvasSeriesCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    新建画布系列分类 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    return canvases_service.create_canvas_series(db, payload.name, payload.sort_order)


@router.put("/admin/series/sort")
async def sort_canvas_series(
    payload: CanvasSeriesSortPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    对画布分类系列进行拖拽重新排序 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    canvases_service.sort_canvas_series(db, payload.series_ids)
    return {"detail": "分类系列排序更新成功"}


@router.put("/admin/series/{series_id}", response_model=CanvasSeriesResponse)
async def update_canvas_series(
    series_id: int,
    payload: CanvasSeriesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改画布系列分类 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    return canvases_service.update_canvas_series(db, series_id, payload.name, payload.sort_order)


@router.post("/admin/series/{series_id}/toggle-active", response_model=CanvasSeriesResponse)
async def toggle_canvas_series_active(
    series_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    切换系列启用/停用状态 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    return canvases_service.toggle_canvas_series_active(db, series_id)


@router.delete("/admin/series/{series_id}/cascade")
async def delete_canvas_series_cascade(
    series_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    级联软删除画布分类系列及内部套件、图片实例 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    canvases_service.delete_canvas_series_cascade(db, series_id)
    return {"detail": "已级联软删除该系列分类及下属套件、图片"}


@router.post("/admin/sets", response_model=CanvasSetResponse)
async def create_canvas_set(
    payload: CanvasSetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    新建画布套件商品 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    return canvases_service.create_canvas_set(
        db,
        payload.series_id,
        payload.name,
        payload.description,
        payload.exchange_price,
        payload.sort_order
    )


@router.put("/admin/sets/sort")
async def sort_canvas_sets(
    payload: CanvasSetSortPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    对系列内的画布商品套进行拖拽重新排序 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    canvases_service.sort_canvas_sets(db, payload.set_ids)
    return {"detail": "商品套件排序更新成功"}


@router.put("/admin/sets/{set_id}", response_model=CanvasSetResponse)
async def update_canvas_set(
    set_id: int,
    payload: CanvasSetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改商品套基本信息 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    return canvases_service.update_canvas_set(
        db,
        set_id,
        payload.series_id,
        payload.name,
        payload.description,
        payload.exchange_price,
        payload.sort_order
    )


@router.post("/admin/sets/{set_id}/toggle-active", response_model=CanvasSetResponse)
async def toggle_canvas_set_active(
    set_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    切换商品套启用/停用状态 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    return canvases_service.toggle_canvas_set_active(db, set_id)


@router.delete("/admin/sets/{set_id}")
async def delete_canvas_set(
    set_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    软删除画布商品套件 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    canvases_service.delete_canvas_set(db, set_id)
    return {"detail": "商品套件及内部图片实例已成功软删除"}


@router.post("/admin/upload", response_model=CanvasInstanceResponse)
async def upload_canvas_instance(
    canvas_set_id: int = Form(...),
    aspect_ratio: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员上传特定宽高比的裁剪画布图片 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")

    if aspect_ratio not in ["16:9", "4:3", "1:1", "2:1"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的长宽比，限定为 16:9, 4:3, 1:1, 2:1")

    return await canvases_service.process_and_save_canvas_instance(db, canvas_set_id, aspect_ratio, file)


@router.post("/admin/instances/{instance_id}/toggle-active", response_model=CanvasInstanceResponse)
async def toggle_canvas_instance_active(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    切换单个图片实例的启用/停用状态 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    return canvases_service.toggle_canvas_instance_active(db, instance_id)


@router.delete("/admin/instances/{instance_id}")
async def delete_canvas_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    软删除单个画布图片实例 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    canvases_service.delete_canvas_instance(db, instance_id)
    return {"detail": "画布图片实例已成功软删除"}


from fastapi.responses import StreamingResponse
from ..services.canvases import import_export as canvases_import_export

class CanvasImportConfirmRequest(BaseModel):
    temp_token: str
    selected_series_names: List[str]
    conflict_resolution: str

@router.get("/admin/export")
async def export_canvases(
    series_ids: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出所选系列的画布为 Zip 压缩包 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        id_list = [int(x) for x in series_ids.split(",") if x.strip()]
    except Exception:
        raise HTTPException(status_code=400, detail="非法的 series_ids 格式")
        
    try:
        zip_file = canvases_import_export.export_canvas_series_zip(db, id_list)
        import datetime
        time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"dinoroar_canvases_export_{time_str}.zip"
        return StreamingResponse(
            zip_file,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/import/preview")
async def import_canvases_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传画布压缩包进行安全性检验和预览 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        content = await file.read()
        res = canvases_import_export.preview_import_canvas_zip(content, db)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/import/confirm")
async def import_canvases_confirm(
    payload: CanvasImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    确认从临时目录导入画布包并应用冲突策略规避后正式落库 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        res = canvases_import_export.confirm_import_canvases(
            temp_token=payload.temp_token,
            selected_series_names=payload.selected_series_names,
            conflict_resolution=payload.conflict_resolution,
            db=db
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
