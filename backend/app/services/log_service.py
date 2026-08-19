import os
import re
import datetime
import logging
from typing import List, Optional
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm import Session, selectinload
from ..models import Log, Attachment, User, Person, PersonCategory, DinoConfig
from ..schemas import LogSyncPayload

logger = logging.getLogger("DinoRoar.logs")

def sync_logs_service(db: Session, current_user: User, payload: LogSyncPayload) -> List[Log]:
    # 1. Process client deletions (Hard Delete)
    if payload.deleted_uuids:
        to_delete = db.query(Log).filter(
            Log.uuid.in_(payload.deleted_uuids),
            Log.user_id == current_user.id
        ).all()
        
        for log in to_delete:
            for attachment in log.attachments:
                if os.path.exists(attachment.file_path):
                    try:
                        os.remove(attachment.file_path)
                    except Exception:
                        pass
            db.delete(log)
        db.commit()

    # 2. Process client additions/updates
    for log_data in payload.logs:
        existing_log = db.query(Log).filter(
            Log.uuid == log_data.uuid,
            Log.user_id == current_user.id
        ).first()

        associated_persons = []
        if log_data.person_uuids:
            associated_persons = db.query(Person).filter(
                Person.uuid.in_(log_data.person_uuids),
                Person.user_id == current_user.id
            ).all()

        if existing_log:
            if existing_log.version > log_data.version:
                logger.warning(f"Sync conflict: Server version ({existing_log.version}) is higher than client base version ({log_data.version}) for UUID {log_data.uuid}. Skipping client update.")
                continue

            client_updated_at = log_data.updated_at
            if client_updated_at and client_updated_at.tzinfo is not None:
                client_updated_at = client_updated_at.replace(tzinfo=None)
                
            db_updated_at = existing_log.updated_at
            if db_updated_at and db_updated_at.tzinfo is not None:
                db_updated_at = db_updated_at.replace(tzinfo=None)

            if db_updated_at and client_updated_at and db_updated_at > client_updated_at:
                logger.info(f"Sync logs LWW: Skipped stale client update for UUID {log_data.uuid}")
                continue

            existing_log.incident_date = log_data.incident_date.replace(tzinfo=None) if log_data.incident_date.tzinfo is not None else log_data.incident_date
            existing_log.mood_dino_id = log_data.mood_dino_id
            existing_log.content = log_data.content
            existing_log.own_thoughts = log_data.own_thoughts
            existing_log.title = log_data.title[:10] if log_data.title else None
            existing_log.updated_at = client_updated_at or datetime.datetime.utcnow()
            existing_log.version = max(existing_log.version, log_data.version) + 1
            
            existing_log.persons = associated_persons

            # 更新/保存背景画布关联
            from ..models import LogCanvas
            log_canvas = db.query(LogCanvas).filter(LogCanvas.log_uuid == existing_log.uuid).first()
            if log_canvas:
                log_canvas.canvas_instance_id = log_data.canvas_instance_id
                log_canvas.canvas_aspect_ratio = log_data.canvas_aspect_ratio
            else:
                log_canvas = LogCanvas(
                    log_uuid=existing_log.uuid,
                    canvas_instance_id=log_data.canvas_instance_id,
                    canvas_aspect_ratio=log_data.canvas_aspect_ratio
                )
                db.add(log_canvas)
        else:
            client_updated_at = log_data.updated_at
            if client_updated_at and client_updated_at.tzinfo is not None:
                client_updated_at = client_updated_at.replace(tzinfo=None)
                
            new_log = Log(
                user_id=current_user.id,
                uuid=log_data.uuid,
                title=log_data.title[:10] if log_data.title else None,
                incident_date=log_data.incident_date.replace(tzinfo=None) if log_data.incident_date.tzinfo is not None else log_data.incident_date,
                mood_dino_id=log_data.mood_dino_id,
                content=log_data.content,
                own_thoughts=log_data.own_thoughts,
                updated_at=client_updated_at or datetime.datetime.utcnow(),
                version=log_data.version or 1
            )
            new_log.persons = associated_persons
            db.add(new_log)

            # 新增背景画布关联
            from ..models import LogCanvas
            log_canvas = LogCanvas(
                log_uuid=new_log.uuid,
                canvas_instance_id=log_data.canvas_instance_id,
                canvas_aspect_ratio=log_data.canvas_aspect_ratio
            )
            db.add(log_canvas)
            
            earned_energy = 10
            has_media = db.query(Attachment).filter(Attachment.log_uuid == log_data.uuid).first() is not None
            if has_media:
                earned_energy += 20
                new_log.media_rewarded = True
            else:
                new_log.media_rewarded = False
                
            db.flush() # 确保生成 new_log.id 物理主键

            # 通过统一能量引擎写入流水事实并更新余额
            from .energy_service import EnergyEngineService
            EnergyEngineService.apply_transaction(
                db=db,
                user_id=current_user.id,
                event_type_id=201, # LOG_REWARD
                change_amount=earned_energy,
                target_type_id=3,  # LOG
                target_id=new_log.id, # 严格强类型整型主键
                request_uuid=f"log_reward_{new_log.uuid}",
                commit=False
            )
            logger.info(f"Sticker Economy: User {current_user.id} earned {earned_energy} energy for new log {new_log.id} (uuid={log_data.uuid}, media_rewarded={new_log.media_rewarded})")



            stickers_in_log = re.findall(r'\[sticker:([^:]+):[0-9.-]+,[0-9.-]+\]', log_data.content)
            if stickers_in_log:
                stickers_to_deduct = {}
                for st in stickers_in_log:
                    try:
                        s_id = int(st.strip())
                        stickers_to_deduct[s_id] = stickers_to_deduct.get(s_id, 0) + 1
                    except ValueError:
                        continue
                
                if stickers_to_deduct:
                    inventory = {}
                    inv_str = current_user.sticker_inventory or ""
                    for item in inv_str.split(','):
                        parts = item.split(':')
                        if len(parts) == 2:
                            try:
                                inventory[int(parts[0])] = int(parts[1])
                            except ValueError:
                                pass
                    for s_id, count in stickers_to_deduct.items():
                        if s_id in inventory:
                            inventory[s_id] = max(0, inventory[s_id] - count)
                      
                    current_user.sticker_inventory = ",".join(f"{k}:{v}" for k, v in inventory.items())
                    logger.info(f"Sticker Economy: User {current_user.id} sticker inventory updated after sync: {current_user.sticker_inventory}")

    db.commit()

    active_logs = db.query(Log).filter(
        Log.user_id == current_user.id,
        Log.is_deleted == False
    ).all()
    
    log_uuids = [log.uuid for log in active_logs]
    orphans = db.query(Attachment).filter(
        Attachment.log_uuid.in_(log_uuids),
        Attachment.log_id.is_(None)
    ).all()
    
    if orphans:
        log_map = {log.uuid: log.id for log in active_logs}
        for attachment in orphans:
            attachment.log_id = log_map.get(attachment.log_uuid)
        db.commit()

    active_logs_loaded = db.query(Log).filter(
        Log.user_id == current_user.id,
        Log.is_deleted == False
    ).options(selectinload(Log.attachments), selectinload(Log.persons)).all()

    populate_log_canvas_details(db, active_logs_loaded)
    return active_logs_loaded


def populate_log_canvas_details(db: Session, logs: List[Log]):
    """
    辅助函数：从独立的 log_canvases 关联表和 canvas_instances 实例表中查询，
    为 logs 列表的各个元素动态填入 canvas_instance_id、canvas_aspect_ratio、canvas_image_url
    """
    if not logs:
        return
    from ..models import LogCanvas, CanvasInstance
    log_uuids = [log.uuid for log in logs]
    log_canvases = db.query(LogCanvas).filter(LogCanvas.log_uuid.in_(log_uuids)).all()
    log_canvas_map = {lc.log_uuid: lc for lc in log_canvases}

    instance_ids = [lc.canvas_instance_id for lc in log_canvases if lc.canvas_instance_id]
    instance_url_map = {}
    if instance_ids:
        canvas_instances = db.query(CanvasInstance).filter(CanvasInstance.id.in_(instance_ids)).all()
        instance_url_map = {inst.id: inst.image_url for inst in canvas_instances}

    for log in logs:
        lc = log_canvas_map.get(log.uuid)
        if lc:
            log.canvas_instance_id = lc.canvas_instance_id
            log.canvas_aspect_ratio = lc.canvas_aspect_ratio
            log.canvas_image_url = instance_url_map.get(lc.canvas_instance_id) if lc.canvas_instance_id else None
        else:
            log.canvas_instance_id = None
            log.canvas_aspect_ratio = "2:1"
            log.canvas_image_url = None


from .log_helpers import get_logs_stats_overview_service

