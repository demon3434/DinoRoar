from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Union

from ..database import get_db
from ..models import User
from ..schemas import Token, UserResponse, UserCreate, UserUpdateLock
from ..auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Standard OAuth2 password flow login. Supports form-data input.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact the administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile and status of the currently authenticated user.
    """
    return current_user

from pydantic import BaseModel

class ThemeUpdateRequest(BaseModel):
    theme: str

@router.post("/theme", status_code=status.HTTP_200_OK)
async def update_my_theme(
    payload: ThemeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the theme preference for the current user.
    """
    theme_name = payload.theme.strip()
    # Validate theme name
    if theme_name not in ["dark-neon", "light-warm", "nordic-cool", "deep-forest", "aurora-night", "violet-dream", "sakura-peach", "autumn-maple", "macaron-pink", "macaron-blue", "macaron-green", "macaron-yellow", "macaron-purple", "macaron-orange", "dark-cyber", "dark-obsidian"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid theme name"
        )
    current_user.theme = theme_name
    db.commit()
    return {"message": f"Theme updated to {theme_name} successfully"}

@router.post("/lock", response_model=UserResponse)
async def update_lock_pattern(
    payload: UserUpdateLock,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the pattern lock sequence for the current user and clears the reset flag.
    """
    current_user.lock_pattern = payload.lock_pattern.strip()
    current_user.lock_reset_flag = "none"
    db.commit()
    db.refresh(current_user)
    return current_user

class UserChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_user_password(
    payload: UserChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Changes the password for the current authenticated user.
    """
    from ..auth import get_password_hash
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}



