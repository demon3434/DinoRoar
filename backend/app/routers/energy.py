import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_user, get_current_admin
from .. import models, schemas
from ..services.energy_service import EnergyEngineService

logger = logging.getLogger("DinoRoar.routers.energy")

router = APIRouter(
    prefix="/api",
    tags=["Energy Ledger"]
)


@router.get("/energy/transactions", response_model=schemas.EnergyTransactionPageResponse)
def get_energy_transactions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    filter_type: str = Query("all", description="收支过滤: all | income | expense"),
    month: Optional[str] = Query(None, description="按月过滤: YYYY-MM"),
    time_range: Optional[str] = Query("all", description="时间段过滤: all | today | week | month | last_month | year"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分页查询当前用户的蛋能量变动流水账本（含生动商品与日记图鉴解析、多维时间段与收支聚合）
    """
    return EnergyEngineService.get_user_transactions(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        filter_type=filter_type,
        month=month,
        time_range=time_range
    )


@router.get("/admin/energy/transactions", response_model=schemas.AdminEnergyTransactionPageResponse)
def get_admin_energy_transactions(
    user_id: Optional[int] = Query(None, description="指定用户ID"),
    event_type_id: Optional[int] = Query(None, description="事件类型ID"),
    start_date: Optional[str] = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="截止日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    管理员全局对账审计：查询全系统或指定用户的蛋能量流水账本与资金总量
    """
    return EnergyEngineService.get_admin_transactions(
        db=db,
        user_id=user_id,
        event_type_id=event_type_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )

