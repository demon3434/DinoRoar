import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import PersonCategory, User
from ..schemas import PersonCategorySyncPayload, PersonCategoryResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/categories", tags=["Categories"])
logger = logging.getLogger("DinoRoar.categories")

@router.post("/sync", response_model=List[PersonCategoryResponse])
async def sync_categories(
    payload: PersonCategorySyncPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Offline-first synchronization endpoint for Person Categories.
    Merges local client modifications and hard-deletes removed categories.
    Returns the complete list of active categories for the user.
    """
    # 1. Process client deletions (Logical Soft Delete)
    if payload.deleted_uuids:
        to_delete = db.query(PersonCategory).filter(
            PersonCategory.uuid.in_(payload.deleted_uuids),
            PersonCategory.user_id == current_user.id
        ).all()
        
        for category in to_delete:
            category.is_deleted = True
        db.commit()
        logger.info(f"Sync: Soft deleted {len(to_delete)} categories for user {current_user.username}")

    # 2. Process client additions/updates
    for category_data in payload.categories:
        existing_category = db.query(PersonCategory).filter(
            PersonCategory.uuid == category_data.uuid,
            PersonCategory.user_id == current_user.id
        ).first()

        if existing_category:
            # Update fields
            existing_category.name = category_data.name
            existing_category.sort_order = category_data.sort_order
            existing_category.is_deleted = category_data.is_deleted
        else:
            # Create new category record
            new_category = PersonCategory(
                user_id=current_user.id,
                uuid=category_data.uuid,
                name=category_data.name,
                sort_order=category_data.sort_order,
                is_deleted=category_data.is_deleted
            )
            db.add(new_category)
            
    db.commit()

    # 3. Fetch all categories of the user (including logical deleted ones)
    active_categories = db.query(PersonCategory).filter(
        PersonCategory.user_id == current_user.id
    ).order_by(PersonCategory.sort_order.asc()).all()

    return active_categories
