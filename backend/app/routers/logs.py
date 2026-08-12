import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm import Session, selectinload
from ..database import get_db
from ..models import Log, Attachment, User, Person
from ..schemas import LogSyncPayload, LogResponse, PaginatedLogResponse
from ..auth import get_current_user
from ..services.log_service import sync_logs_service, get_logs_stats_overview_service

logger = logging.getLogger("DinoRoar.logs")

router = APIRouter(prefix="/api/logs", tags=["Logs"])

@router.post("/sync", response_model=List[LogResponse])
async def sync_logs(
    payload: LogSyncPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Offline-first synchronization endpoint.
    Merges local client modifications and hard-deletes removed logs.
    Returns the complete list of active logs for the user.
    """
    return sync_logs_service(db, current_user, payload)


@router.get("/list", response_model=PaginatedLogResponse)
async def list_logs(
    page: int = 1,
    limit: int = 10,
    query: Optional[str] = None,
    mood_dino: Optional[str] = None,
    mood_dino_id: Optional[int] = None,
    incident_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    person_uuid: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Paginated logs endpoint with query, mood, month, date range, and person filters for the Web dashboard.
    """
    if page < 1:
        page = 1
    offset = (page - 1) * limit

    db_query = db.query(Log).filter(
        Log.user_id == current_user.id,
        Log.is_deleted == False
    )

    if query:
        # Match title or content
        db_query = db_query.filter(
            or_(
                Log.title.like(f"%{query}%"),
                Log.content.like(f"%{query}%")
            )
        )

    if mood_dino_id is not None:
        db_query = db_query.filter(Log.mood_dino_id == mood_dino_id)

    if incident_date:
        # Match year-month or full date string in database
        db_query = db_query.filter(Log.incident_date.like(f"%{incident_date}%"))

    if start_date:
        # incident_date string is stored as "2026-07-12T16:00:00"
        # We can directly do lexicographical comparison since ISO 8601 format matches date ordering
        db_query = db_query.filter(Log.incident_date >= start_date)

    if end_date:
        # Compare to end of day to include all entries on the end day
        db_query = db_query.filter(Log.incident_date <= f"{end_date}T23:59:59")

    if person_uuid:
        db_query = db_query.filter(Log.persons.any(Person.uuid == person_uuid))

    total = db_query.count()

    items = db_query.order_by(desc(Log.incident_date))\
        .offset(offset)\
        .limit(limit)\
        .options(selectinload(Log.attachments), selectinload(Log.persons))\
        .all()

    from ..services.log_service import populate_log_canvas_details
    populate_log_canvas_details(db, items)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }

@router.get("/detail/{uuid}", response_model=LogResponse)
async def get_log_detail(
    uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    log = db.query(Log).filter(
        Log.uuid == uuid,
        Log.user_id == current_user.id,
        Log.is_deleted == False
    ).options(selectinload(Log.attachments), selectinload(Log.persons)).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
        
    from ..services.log_service import populate_log_canvas_details
    populate_log_canvas_details(db, [log])
    
    return log

@router.get("/stats/overview")
async def get_logs_stats_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggregation statistics overview endpoint for the Web dashboard.
    Returns:
    - mood_heatmap: grid data of last 30 days
    - relationship_galaxy: topological graph data
    - friend_mood_stats: best happy buddies & warm hug buddies
    - ai_word_cloud_tips: words frequency & smart coping tips
    """
    return get_logs_stats_overview_service(db, current_user)

