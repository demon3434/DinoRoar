import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import DinoConfig, User
from ..schemas import DinoConfigResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/dino/config", tags=["DinoConfig"])
logger = logging.getLogger("DinoRoar.dino_config")

@router.get("", response_model=List[DinoConfigResponse])
async def get_dino_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the full list of active dinosaur configs sorted by sort_order.
    """
    configs = db.query(DinoConfig).filter(
        DinoConfig.is_active == True
    ).order_by(DinoConfig.sort_order.asc()).all()
    
    return configs
