import os
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Attachment, Log, User
from ..schemas import AttachmentResponse
from ..auth import get_current_user
from ..config import settings

router = APIRouter(prefix="/api/attachments", tags=["Attachments"])

# Ensure attachments folder exists
ATTACHMENTS_DIR = os.path.join(settings.upload_dir, "attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

from pydantic import BaseModel

class CheckMd5Request(BaseModel):
    md5: str
    uuid: str
    log_uuid: Optional[str] = None
    title: Optional[str] = None

@router.post("/check-md5")
async def check_md5(
    payload: CheckMd5Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Checks if a file with the given MD5 already exists on the server.
    If it exists, clones a new attachment record to support offline-first/fast-upload
    without writing duplicate files on disk.
    """
    existing = db.query(Attachment).filter(Attachment.md5 == payload.md5).first()
    if not existing:
        return {"status": "not_found", "message": "MD5 check failed, upload is required"}
        
    # Resolve log_id if log_uuid is provided
    log_id = None
    if payload.log_uuid:
        log = db.query(Log).filter(Log.uuid == payload.log_uuid, Log.user_id == current_user.id).first()
        if log:
            log_id = log.id

    existing_new = db.query(Attachment).filter(Attachment.uuid == payload.uuid).first()
    if existing_new:
        existing_new.log_id = log_id
        existing_new.log_uuid = payload.log_uuid
        existing_new.file_path = existing.file_path
        existing_new.file_name = existing.file_name
        existing_new.mime_type = existing.mime_type
        existing_new.file_size = existing.file_size
        existing_new.md5 = payload.md5
        existing_new.title = payload.title or existing.title
        db.commit()
        db.refresh(existing_new)
        return {"status": "exists", "id": existing_new.id, "uuid": existing_new.uuid, "remote_url": f"/api/attachments/download/{existing_new.uuid}"}
    else:
        new_attachment = Attachment(
            uuid=payload.uuid,
            log_id=log_id,
            log_uuid=payload.log_uuid,
            file_path=existing.file_path,
            file_name=existing.file_name,
            mime_type=existing.mime_type,
            file_size=existing.file_size,
            md5=payload.md5,
            title=payload.title or existing.title
        )
        db.add(new_attachment)
        db.commit()
        db.refresh(new_attachment)
        return {"status": "exists", "id": new_attachment.id, "uuid": new_attachment.uuid, "remote_url": f"/api/attachments/download/{new_attachment.uuid}"}

@router.post("/upload", response_model=AttachmentResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    uuid: str = Form(...),
    log_uuid: Optional[str] = Form(None),
    md5: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Uploads a media attachment (compressed WebP image, H.265 video, etc.)
    and links it to a log by uuid if it exists.
    """
    # Clean file name and generate local path
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-").strip()
    file_ext = os.path.splitext(safe_filename)[1]
    
    # Target file path with YYYY/MM subfolder
    now_year_month = datetime.utcnow().strftime("%Y/%m")
    target_dir = os.path.join(ATTACHMENTS_DIR, now_year_month)
    os.makedirs(target_dir, exist_ok=True)
    target_filename = f"{uuid}{file_ext}"
    target_path = os.path.join(target_dir, target_filename)
 
    # Resolve log_id if log already exists
    log_id = None
    if log_uuid:
        log = db.query(Log).filter(Log.uuid == log_uuid, Log.user_id == current_user.id).first()
        if log:
            log_id = log.id
 
    # Check if attachment record already exists
    existing_attachment = db.query(Attachment).filter(Attachment.uuid == uuid).first()
    if existing_attachment:
        # Delete old file if exists
        if os.path.exists(existing_attachment.file_path):
            try:
                os.remove(existing_attachment.file_path)
            except Exception:
                pass
 
    # Save uploaded file chunk by chunk to disk
    temp_size = 0
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        temp_size = os.path.getsize(target_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write attachment file to disk: {e}"
        )
    finally:
        await file.close()

    # 自动优化 MP4 视频，将 moov atom 移动至文件头部 (FastStart)
    if (file.content_type == "video/mp4" or target_path.endswith(".mp4")) and temp_size > 0:
        import subprocess
        temp_fast_path = target_path + ".fast.mp4"
        try:
            res = subprocess.run(
                ["ffmpeg", "-y", "-i", target_path, "-c", "copy", "-movflags", "+faststart", temp_fast_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            if res.returncode == 0 and os.path.exists(temp_fast_path) and os.path.getsize(temp_fast_path) > 0:
                os.replace(temp_fast_path, target_path)
                temp_size = os.path.getsize(target_path)
        except Exception:
            if os.path.exists(temp_fast_path):
                try:
                    os.remove(temp_fast_path)
                except Exception:
                    pass
 
    if existing_attachment:
        existing_attachment.file_path = target_path
        existing_attachment.file_name = file.filename
        existing_attachment.mime_type = file.content_type or "application/octet-stream"
        existing_attachment.file_size = temp_size
        existing_attachment.log_id = log_id
        existing_attachment.log_uuid = log_uuid
        existing_attachment.md5 = md5
        if title is not None:
            existing_attachment.title = title
        db.commit()
        db.refresh(existing_attachment)
        return existing_attachment
    else:
        new_attachment = Attachment(
            uuid=uuid,
            log_id=log_id,
            log_uuid=log_uuid,
            file_path=target_path,
            file_name=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            file_size=temp_size,
            md5=md5,
            title=title
        )
        db.add(new_attachment)
        db.commit()
        db.refresh(new_attachment)
        return new_attachment

@router.get("/download/{uuid}")
async def download_attachment(
    uuid: str,
    download: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Downloads an uploaded media attachment by UUID. Requires authentication.
    """
    attachment = db.query(Attachment).filter(Attachment.uuid == uuid).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Eagerly verify the parent log belongs to the current user (if linked)
    if attachment.log_id:
        log = db.query(Log).filter(Log.id == attachment.log_id).first()
        if log and log.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )

    if not os.path.exists(attachment.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found on server disk"
        )

    return FileResponse(
        path=attachment.file_path,
        media_type=attachment.mime_type,
        filename=attachment.file_name if download else None,
        content_disposition_type="attachment" if download else "inline"
    )

@router.delete("/{uuid}")
async def delete_attachment(
    uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes an uploaded media attachment by UUID.
    """
    attachment = db.query(Attachment).filter(Attachment.uuid == uuid).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Eagerly verify the parent log belongs to the current user (if linked)
    if attachment.log_id:
        log = db.query(Log).filter(Log.id == attachment.log_id).first()
        if log and log.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this file"
            )

    # Delete physical file on disk
    if os.path.exists(attachment.file_path):
        try:
            os.remove(attachment.file_path)
        except Exception:
            pass

    db.delete(attachment)
    db.commit()
    return {"status": "success", "message": "Attachment deleted successfully"}

