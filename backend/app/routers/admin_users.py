from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ..database import get_db
from ..models import User
from ..schemas import UserResponse, UserCreate, UserResetLock
from ..auth import get_current_admin, get_password_hash
from ..services.cleanup import perform_orphan_cleanup

router = APIRouter(prefix="/api/admin", tags=["Admin Management"])

class AdminPasswordReset(BaseModel):
    new_password: str

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Lists all users. Requires admin privileges.
    """
    return db.query(User).all()

@router.post("/users", response_model=UserResponse)
async def create_user(
    payload: UserCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Creates a new user. Requires admin privileges.
    """
    existing_user = db.query(User).filter(User.username == payload.username.strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    raw_password = payload.password
    if not raw_password or not raw_password.strip():
        raw_password = "123456"
        
    hashed = get_password_hash(raw_password)
    new_user = User(
        username=payload.username.strip(),
        nickname=payload.nickname.strip() if payload.nickname else None,
        hashed_password=hashed,
        is_admin=False,
        egg_energy=100
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

class UserUpdatePayload(BaseModel):
    username: str
    nickname: Optional[str] = None

@router.post("/users/{user_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivates a user by ID. Requires admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate admin user"
        )
    user.is_active = False
    db.commit()
    return {"message": f"User {user.username} deactivated successfully"}

@router.post("/users/{user_id}/activate", status_code=status.HTTP_200_OK)
async def activate_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Activates a deactivated user by ID. Requires admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user.is_active = True
    db.commit()
    return {"message": f"User {user.username} activated successfully"}

@router.post("/users/{user_id}/update", status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    payload: UserUpdatePayload,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Updates the username and nickname of a user with uniqueness validation.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update admin user"
        )

    username_cleaned = payload.username.strip()
    if not username_cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名不能为空"
        )

    # Check unique username
    existing_username = db.query(User).filter(User.username == username_cleaned, User.id != user_id).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被其他账户占用"
        )

    # Check unique nickname if set
    if payload.nickname and payload.nickname.strip():
        nickname_cleaned = payload.nickname.strip()
        existing_nickname = db.query(User).filter(User.nickname == nickname_cleaned, User.id != user_id, User.is_admin == False).first()
        if existing_nickname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="昵称已被其他账户占用"
            )
        user.nickname = nickname_cleaned
    else:
        user.nickname = None

    user.username = username_cleaned
    db.commit()
    return {"message": f"User {user.username} updated successfully"}

@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Soft-deactivates the user instead of deleting physical files.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user.is_active = False
    db.commit()
    return {"message": f"User {user.username} deactivated successfully"}

@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_200_OK)
async def reset_user_password(
    user_id: int,
    payload: AdminPasswordReset,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Resets the password for a child user. Requires admin privileges.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": f"Password reset successfully for user {user.username}"}

@router.post("/users/{user_id}/reset-lock", status_code=status.HTTP_200_OK)
async def reset_user_lock_pattern(
    user_id: int,
    payload: UserResetLock,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Marks the child's pattern lock reset status to 'default_requested' and updates lock_pattern.
    On the next sync, the mobile device will clear its gesture sequence.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    pattern = payload.lock_pattern.strip()
    parts = pattern.split(",")
    if len(parts) != 3 or not all(p.isdigit() and 1 <= int(p) <= 5 for p in parts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="解锁码格式不正确，必须为 3 个 1 到 5 之间的数字并由逗号分隔"
        )
    
    user.lock_pattern = pattern
    user.lock_reset_flag = "default_requested"
    db.commit()
    return {"message": f"Mobile pattern lock reset flag set to default_requested and pattern updated for {user.username}"}

@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def run_cleanup(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Triggers the manual scan and deletion of orphaned/broken attachments.
    """
    result = perform_orphan_cleanup(db)
    return result

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_admin_password(
    payload: ChangePasswordRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Changes the password for the current administrator.
    """
    from ..auth import verify_password
    if not verify_password(payload.current_password, current_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_admin.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Administrator password changed successfully"}
