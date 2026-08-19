import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_user
from .. import models, schemas
from ..services.checkin_service import CheckInService

logger = logging.getLogger("DinoRoar.routers.checkin")

router = APIRouter(
    prefix="/api/checkin",
    tags=["Check-in"]
)


@router.get("/status", response_model=schemas.CheckInStatusResponse)
def get_checkin_status(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户今日签到状态与连续签到打卡周历
    """
    return CheckInService.get_user_checkin_status(db, current_user.id)


@router.post("", response_model=schemas.CheckInResultResponse)
def perform_checkin(
    request: schemas.CheckInRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    执行每日敲蛋签到 (100% 服务端权威随机计算与原子入库)
    """
    if not request.request_uuid or len(request.request_uuid.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少有效的 request_uuid 幂等标识"
        )

    return CheckInService.perform_user_checkin(
        db=db,
        user_id=current_user.id,
        request_uuid=request.request_uuid.strip()
    )
