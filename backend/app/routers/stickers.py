import os
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import User, StickerConfig
from ..schemas import (
    StickerSyncPayload, 
    StickerInventoryResponse, 
    StickerConfigResponse, 
    StickerSeriesResponse, 
    StickerExchangeRequest,
    StickerSeriesCreate,
    StickerSortRequest,
    StickerSeriesRenameRequest,
    StickerSeriesToggleActiveRequest,
    StickerSeriesSortRequest,
    StickerUpdateRequest,
    StickerImportConfirmRequest,
    StickerBatchDeleteRequest
)
from ..auth import get_current_user
from ..services import stickers as stickers_service

router = APIRouter(prefix="/api/stickers", tags=["Stickers"])

@router.get("/config", response_model=List[StickerSeriesResponse])
async def get_stickers_config(
    for_admin: bool = False,
    db: Session = Depends(get_db)
):
    """
    获取系统中所有可用的贴纸系列及内部嵌套的贴纸基础配置清单
    """
    return stickers_service.get_nested_stickers_config(db, apply_promo=not for_admin)


@router.get("/inventory", response_model=StickerInventoryResponse)
async def get_sticker_inventory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前登录账户的游戏资产（贴纸库存和蛋能量）
    """
    try:
        user = stickers_service.get_user_inventory(db, user_id=current_user.id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/inventory", response_model=StickerInventoryResponse)
async def sync_sticker_inventory(
    payload: StickerSyncPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    同步客户端上报的贴纸进销存持有限量
    """
    try:
        user = stickers_service.update_user_sticker_inventory(db, user_id=current_user.id, new_inventory=payload.sticker_inventory)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/exchange", response_model=StickerInventoryResponse)
async def exchange_sticker(
    payload: StickerExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    自主消耗蛋能量兑换贴纸（向后兼容适配层，内部代理至统一 ShopService 计价与结算）
    """
    from ..services.shop.items import sync_asset_shop_item, exchange_shop_items
    from ..models import StickerConfig
    
    sticker = db.query(StickerConfig).filter(StickerConfig.id == payload.sticker_id, StickerConfig.is_deleted == False).first()
    if not sticker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="贴纸未找到或已删除")
    
    # 确保 ShopItem 存在
    shop_item = sync_asset_shop_item(
        db=db,
        item_type="STICKER",
        target_id=sticker.id,
        original_price=sticker.exchange_price or 20,
        sort_order=sticker.sort_order,
        is_active=sticker.is_active
    )
    
    res = exchange_shop_items(db, user_id=current_user.id, shop_item_ids=[shop_item.id])
    db.refresh(current_user)
    return {
        "sticker_inventory": current_user.sticker_inventory,
        "egg_energy": current_user.egg_energy
    }


@router.post("/admin/series", response_model=StickerSeriesResponse)
async def create_sticker_series(
    payload: StickerSeriesCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    新建贴纸系列分类 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅限管理员操作"
        )
    
    from ..models import StickerSeries
    max_id = db.query(StickerSeries.id).order_by(StickerSeries.id.desc()).first()
    next_id = 101
    if max_id and max_id[0] >= 101:
        next_id = max_id[0] + 1
        
    series = StickerSeries(
        id=next_id,
        name=payload.name,
        sort_order=payload.sort_order,
        is_active=True
    )
    db.add(series)
    db.commit()
    db.refresh(series)
    series.stickers = []
    return series

@router.post("/admin/upload", response_model=StickerConfigResponse)
async def upload_sticker(
    file: UploadFile,
    series_id: int = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    sort_order: int = Form(0),
    exchange_price: int = Form(20),
    remove_background: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传贴纸图片并绑定系列分类 (仅限管理员)，支持可选 remove_background 去背景。
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅限管理员操作"
        )
    if len(name) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="贴纸名称最多限制 6 个汉字/字符"
        )
        
    from ..models import StickerSeries, StickerConfig
    series = db.query(StickerSeries).filter(StickerSeries.id == series_id).first()
    if not series:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的贴纸系列不存在"
        )
        
    file_ext = os.path.splitext(file.filename)[1] or ".png"
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"

    try:
        content = await file.read()
        image_url = stickers_service.save_sticker_image_file(series_id, unique_filename, content, remove_background=remove_background)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片写入磁盘失败: {str(e)}"
        )
    
    sticker_cfg = StickerConfig(
        series_id=series_id,
        name=name,
        image_url=image_url,
        description=description,
        sort_order=sort_order,
        exchange_price=exchange_price,
        is_active=True
    )
    db.add(sticker_cfg)
    db.flush()
    stickers_service.reorder_stickers_in_series(db, series_id, sticker_cfg.id, sort_order)
    
    # 同步写入统一商品销售表
    from ..services.shop.items import sync_asset_shop_item
    sync_asset_shop_item(
        db=db,
        item_type="STICKER",
        target_id=sticker_cfg.id,
        original_price=exchange_price,
        sort_order=sort_order,
        is_active=True
    )
    
    db.commit()
    db.refresh(sticker_cfg)
    return sticker_cfg

@router.put("/admin/sort")
async def sort_admin_stickers(
    payload: StickerSortRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新一系列贴纸的展示排序 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    stickers_service.sort_stickers(db, payload.sticker_ids)
    return {"status": "success", "message": "重排序保存成功"}

@router.put("/admin/series/sort")
async def sort_admin_series(
    payload: StickerSeriesSortRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新分类文件夹之间的展示排序 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    stickers_service.sort_sticker_series(db, payload.series_ids)
    return {"status": "success", "message": "分类重排序保存成功"}

@router.put("/admin/series/{series_id}", response_model=StickerSeriesResponse)
async def rename_admin_series(
    series_id: int,
    payload: StickerSeriesRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改系列分类的名称 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        series = stickers_service.rename_sticker_series(db, series_id, payload.name)
        active_stickers = db.query(StickerConfig).filter(
            StickerConfig.series_id == series_id,
            StickerConfig.is_deleted == False
        ).order_by(StickerConfig.sort_order.asc()).all()
        series.stickers = active_stickers
        return series
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/admin/series/{series_id}/toggle-active", response_model=StickerSeriesResponse)
async def toggle_active_admin_series(
    series_id: int,
    payload: StickerSeriesToggleActiveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    停用/启用贴纸分类系列 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        series = stickers_service.toggle_sticker_series_active(db, series_id, payload.is_active)
        active_stickers = db.query(StickerConfig).filter(
            StickerConfig.series_id == series_id,
            StickerConfig.is_deleted == False
        ).order_by(StickerConfig.sort_order.asc()).all()
        series.stickers = active_stickers
        return series
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/admin/{sticker_id}")
async def delete_admin_sticker(
    sticker_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    软删除特定贴纸 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        stickers_service.soft_delete_sticker(db, sticker_id)
        from ..models import ShopItem
        db.query(ShopItem).filter(ShopItem.item_type == "STICKER", ShopItem.target_id == sticker_id).update({"is_deleted": True, "is_active": False})
        db.commit()
        return {"status": "success", "message": "贴纸已成功软删除"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/admin/series/{series_id}")
async def delete_admin_series(
    series_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    软删除分类系列，若有未删除贴纸则抛 400 阻断 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        stickers_service.soft_delete_sticker_series(db, series_id)
        return {"status": "success", "message": "分类系列已成功软删除"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/admin/{sticker_id}", response_model=StickerConfigResponse)
async def update_admin_sticker(
    sticker_id: int,
    name: str = Form(...),
    exchange_price: int = Form(...),
    sort_order: int = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改单个贴纸的配置与字段属性 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    if len(name) > 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="贴纸名称最多限制 6 个汉字/字符")
        
    image_url = None
    if file is not None and file.filename:
        st_obj = db.query(StickerConfig).filter(StickerConfig.id == sticker_id).first()
        if not st_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定贴纸配置不存在")
        file_ext = os.path.splitext(file.filename)[1] or ".png"
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"

        try:
            content = await file.read()
            image_url = stickers_service.save_sticker_image_file(st_obj.series_id, unique_filename, content)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"图片写入磁盘失败: {str(e)}")
            
    try:
        sticker = stickers_service.update_sticker(
            db, 
            sticker_id, 
            name, 
            exchange_price, 
            sort_order, 
            description, 
            image_url
        )
        # 同步更新统一商品销售表
        from ..services.shop.items import sync_asset_shop_item
        sync_asset_shop_item(
            db=db,
            item_type="STICKER",
            target_id=sticker.id,
            original_price=exchange_price,
            sort_order=sort_order,
            is_active=sticker.is_active
        )
        return sticker
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/export")
async def export_stickers(
    series_ids: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    导出指定系列为符合标准规范的 Zip 打包流 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        ids = [int(x.strip()) for x in series_ids.split(",") if x.strip()]
        zip_io = stickers_service.export_sticker_series_zip(db, ids)
        time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"dinoroar_stickers_export_{time_str}.zip"
        return StreamingResponse(
            zip_io,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/import/preview")
async def preview_import_stickers(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传贴纸包解压预检解析 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        content = await file.read()
        res = stickers_service.preview_import_zip(content, db)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/import/confirm")
async def confirm_import_stickers(
    payload: StickerImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    确认精细化导入贴纸包 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        res = stickers_service.confirm_import_stickers(
            temp_token=payload.temp_token,
            selected_series_names=payload.selected_series_names,
            conflict_resolution=payload.conflict_resolution,
            db=db
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/admin/series/{series_id}/cascade")
async def cascade_delete_series(
    series_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    级联删除贴纸系列及其下的所有贴纸与图片 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        stickers_service.cascade_delete_series(db, series_id)
        return {"message": "系列及其下关联贴纸已成功级联删除"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/admin/batch-delete")
async def batch_delete_stickers(
    payload: StickerBatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量物理清理并删除贴纸 (仅限管理员)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅限管理员操作")
    try:
        count = stickers_service.batch_delete_stickers(db, payload.sticker_ids)
        return {"deleted_count": count}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))






