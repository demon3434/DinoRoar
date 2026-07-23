import os
import shutil
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import Attachment
from ..config import settings

logger = logging.getLogger("DinoRoar.migrate")

def perform_attachment_migration(db: Session) -> dict:
    """
    Comprehensively migrates all existing diary attachment files and DB records:
    1. Scans DB Attachment table: updates file_path column and moves physical files to YYYY/MM subdirectories.
    2. Scans root uploads/attachments/ directory: moves any remaining flat legacy files to YYYY/MM subdirectories and updates DB records.
    """
    raw_dir = os.path.join(settings.upload_dir, "attachments")
    attachments_dir = os.path.normpath(raw_dir).replace("\\", "/")
    
    if not os.path.exists(attachments_dir):
        return {"migrated_count": 0, "errors": []}

    migrated_count = 0
    errors = []

    # --- Phase 1: DB-Driven Migration for Existing Diary Attachments ---
    try:
        all_attachments = db.query(Attachment).all()
        for att in all_attachments:
            if not att.file_path:
                continue

            current_path = os.path.normpath(att.file_path).replace("\\", "/")
            current_dir = os.path.dirname(current_path)

            # Check if file_path is directly under root attachments_dir (flat structure)
            if current_dir == attachments_dir:
                created_dt = att.created_at or datetime.utcnow()
                year_month = created_dt.strftime("%Y/%m")
                target_dir = os.path.join(attachments_dir, year_month).replace("\\", "/")
                os.makedirs(target_dir, exist_ok=True)

                filename = os.path.basename(current_path)
                new_path = os.path.join(target_dir, filename).replace("\\", "/")

                # Move physical file if it exists at old root location
                if os.path.exists(current_path) and current_path != new_path:
                    try:
                        shutil.move(current_path, new_path)
                        logger.info(f"Attachment migration DB-phase: Moved file {filename} -> {year_month}/{filename}")
                    except Exception as move_err:
                        logger.error(f"Failed to move physical file {current_path}: {move_err}")

                # Update database column file_path unconditionally for existing diary attachments
                att.file_path = new_path
                db.commit()
                migrated_count += 1
    except Exception as e:
        err_msg = f"DB-driven migration failed: {e}"
        logger.error(err_msg)
        errors.append(err_msg)
        db.rollback()

    # --- Phase 2: Disk-Driven Migration for Remaining Root Legacy Files ---
    try:
        entries = os.listdir(attachments_dir)
        for item in entries:
            old_path = os.path.join(attachments_dir, item).replace("\\", "/")
            # Skip directories (already hierarchical)
            if os.path.isdir(old_path):
                continue

            uuid_candidate = os.path.splitext(item)[0]
            db_attachments = db.query(Attachment).filter(
                (Attachment.file_path == old_path) | (Attachment.uuid == uuid_candidate)
            ).all()

            target_year_month = None
            if db_attachments and db_attachments[0].created_at:
                target_year_month = db_attachments[0].created_at.strftime("%Y/%m")
            else:
                mtime = os.path.getmtime(old_path)
                target_year_month = datetime.utcfromtimestamp(mtime).strftime("%Y/%m")

            target_dir = os.path.join(attachments_dir, target_year_month).replace("\\", "/")
            os.makedirs(target_dir, exist_ok=True)
            new_path = os.path.join(target_dir, item).replace("\\", "/")

            if old_path != new_path:
                shutil.move(old_path, new_path)
                logger.info(f"Attachment migration Disk-phase: Moved {item} -> {target_year_month}/{item}")

                if db_attachments:
                    for att in db_attachments:
                        att.file_path = new_path
                    db.commit()

                migrated_count += 1
    except Exception as e:
        err_msg = f"Disk-driven migration failed: {e}"
        logger.error(err_msg)
        errors.append(err_msg)
        db.rollback()

    return {
        "migrated_count": migrated_count,
        "errors": errors
    }
