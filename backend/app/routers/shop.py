"""
统一手账商城与促销活动路由接口
负责请求参数验证、权限控制与响应格式封装，业务逻辑下沉至服务层
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_current_user, get_optional_current_user, get_current_admin_user

from ..schemas import (
    ShopItemResponse, ShopExchangeRequest,
    PromotionCreateRequest, PromotionUpdateRequest,
    PromotionToggleActiveRequest, PromotionResponse,
    PromotionPaginationResponse
)
from ..services.shop.items import list_shop_items, exchange_shop_items
from ..services.shop.promotions import (
    list_all_promotions, get_promotion_by_id,
    create_promotion, update_promotion,
    toggle_promotion_active, delete_promotion,
    get_active_promotions_summary
)


router = APIRouter(prefix="/api", tags=["Shop & Promotions"])


# ==========================================
# 统一手账商城 (Shop) 客户端接口
# ==========================================

@router.get("/shop/items", response_model=List[ShopItemResponse])
def api_list_shop_items(
    item_type: Optional[str] = Query(None, description="商品类型: STICKER | CANVAS_SET"),
    series_id: Optional[int] = Query(None, description="系列 ID 筛选"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):

    """
    获取手账商城商品列表（附带实付价与资产详情，支持零转换直传）
    """
    return list_shop_items(
        db=db,
        item_type=item_type,
        series_id=series_id,
        user=current_user,
        admin_view=False
    )


@router.post("/shop/exchange")
def api_exchange_shop_items(
    payload: ShopExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    统一兑换结算接口：校验余额、扣除蛋能量并在单个事务中自动分发资产到背包
    """
    return exchange_shop_items(
        db=db,
        user_id=current_user.id,
        shop_item_ids=payload.shop_item_ids
    )


@router.get("/promotions/active-summary")
def api_get_active_promotions_summary(
    db: Session = Depends(get_db)
):
    """
    获取当前正在生效的促销活动概要（供 Android 首页看板挂件与 Web 顶部横幅展示）
    """
    return get_active_promotions_summary(db)


# ==========================================
# 促销活动管理 (Admin Promotion Management) 接口
# ==========================================

@router.get("/admin/promotions", response_model=PromotionPaginationResponse)
def api_admin_list_promotions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="搜索关键字（活动名称/说明）"),
    status: Optional[str] = Query(None, description="状态筛选: active | upcoming | ended | disabled"),
    start_date: Optional[str] = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="截止日期 YYYY-MM-DD"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin 获取全部促销活动分页列表（支持关键字、状态及日期范围组合筛选）
    """
    return list_all_promotions(
        db=db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        start_date=start_date,
        end_date=end_date
    )



@router.post("/admin/promotions", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
def api_admin_create_promotion(
    payload: PromotionCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin 创建新的促销活动与多维度规则
    """
    targets_data = [t.model_dump() for t in payload.targets]
    return create_promotion(
        db=db,
        name=payload.name,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
        is_active=payload.is_active,
        targets_data=targets_data
    )


@router.put("/admin/promotions/{promotion_id}", response_model=PromotionResponse)
def api_admin_update_promotion(
    promotion_id: int,
    payload: PromotionUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin 更新促销活动信息与重设规则
    """
    targets_data = [t.model_dump() for t in payload.targets] if payload.targets is not None else None
    updated = update_promotion(
        db=db,
        promotion_id=promotion_id,
        name=payload.name,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
        is_active=payload.is_active,
        targets_data=targets_data
    )
    if not updated:
        raise HTTPException(status_code=404, detail="促销活动不存在")
    return updated


@router.patch("/admin/promotions/{promotion_id}/toggle-active", response_model=PromotionResponse)
@router.post("/admin/promotions/{promotion_id}/toggle-active", response_model=PromotionResponse)
def api_admin_toggle_promotion_active(
    promotion_id: int,
    payload: PromotionToggleActiveRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin 快捷启停促销活动
    """
    updated = toggle_promotion_active(db, promotion_id=promotion_id, is_active=payload.is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="促销活动不存在")
    return updated


@router.delete("/admin/promotions/{promotion_id}")
def api_admin_delete_promotion(
    promotion_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin 软删除促销活动
    """
    success = delete_promotion(db, promotion_id=promotion_id)
    if not success:
        raise HTTPException(status_code=404, detail="促销活动不存在")
    return {"success": True, "message": "促销活动已删除"}
