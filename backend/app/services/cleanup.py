import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Attachment
from ..config import settings

logger = logging.getLogger("DinoRoar.cleanup")

def perform_orphan_cleanup(db: Session) -> dict:
    """
    Recursively scans the attachments directory (including YYYY/MM subdirectories)
    and database records to identify and delete:
    1. Files on disk that do not have a matching Attachment record in the DB.
    2. Attachment records in the DB (and their disk files) that have no parent log_id
       and were created more than 24 hours ago (stale/broken uploads).
    3. Empty subdirectories left after file deletion.
    """
    attachments_dir = os.path.join(settings.upload_dir, "attachments")
    if not os.path.exists(attachments_dir):
        return {"deleted_files": [], "freed_bytes": 0}

    # Gather database files
    all_db_attachments = db.query(Attachment).all()
    db_file_paths = {os.path.normpath(att.file_path) for att in all_db_attachments}
    
    deleted_files = []
    freed_bytes = 0

    # 1. Clean up untracked files recursively with os.walk
    try:
        for root, dirs, files in os.walk(attachments_dir, topdown=False):
            for filename in files:
                file_path = os.path.normpath(os.path.join(root, filename))
                
                # If not tracked in DB, it is an orphan
                if file_path not in db_file_paths:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        rel_name = os.path.relpath(file_path, attachments_dir)
                        deleted_files.append(rel_name)
                        freed_bytes += file_size
                        logger.info(f"Cleanup: Removed untracked disk file {rel_name} ({file_size} bytes)")
                    except Exception as e:
                        logger.error(f"Cleanup: Failed to remove untracked disk file {file_path}: {e}")

            # Clean up empty subdirectories
            if root != attachments_dir and os.path.exists(root):
                try:
                    if not os.listdir(root):
                        os.rmdir(root)
                        logger.info(f"Cleanup: Removed empty directory {root}")
                except Exception as dir_e:
                    logger.debug(f"Cleanup: Directory {root} not empty or cannot remove: {dir_e}")
    except Exception as e:
        logger.error(f"Cleanup: Recursive directory scan failed: {e}")

    # 2. Clean up database records with null log_id older than 24 hours (stale uploads)
    stale_threshold = datetime.utcnow() - timedelta(hours=24)
    stale_attachments = db.query(Attachment).filter(
        Attachment.log_id.is_(None),
        Attachment.created_at < stale_threshold
    ).all()

    for att in stale_attachments:
        file_path = att.file_path
        filename = att.file_name
        file_size = att.file_size
        
        # Delete file from disk if it exists
        if os.path.exists(file_path):
            try:
                parent_dir = os.path.dirname(file_path)
                os.remove(file_path)
                deleted_files.append(f"{att.uuid}_{filename} (stale)")
                freed_bytes += file_size
                logger.info(f"Cleanup: Removed stale file {filename} from disk")

                # Remove parent directory if empty
                if parent_dir != attachments_dir and os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    try:
                        os.rmdir(parent_dir)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Cleanup: Failed to remove stale file {filename} from disk: {e}")

        # Delete database record
        try:
            db.delete(att)
            logger.info(f"Cleanup: Deleted stale attachment database record: {att.uuid}")
        except Exception as e:
            logger.error(f"Cleanup: Failed to delete stale database record: {e}")

    if deleted_files:
        db.commit()

    return {
        "deleted_files": deleted_files,
        "freed_bytes": freed_bytes
    }
