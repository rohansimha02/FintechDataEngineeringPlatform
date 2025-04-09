"""
Authentication router for FinTech Data Platform
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import auth_manager, get_current_active_user
from app.core.database import get_db_session
from app.core.config import settings
from app.models.schemas import Token, User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
):
    """Login endpoint to get access token"""
    # In production, you would validate against actual user database
    # For demo purposes, we'll use simple validation
    if form_data.username == "admin" and form_data.password == "admin123":
        user = {
            "id": 1,
            "username": "admin",
            "email": "admin@fintech.com",
            "roles": ["admin", "analyst"]
        }
    elif form_data.username == "analyst" and form_data.password == "analyst123":
        user = {
            "id": 2,
            "username": "analyst",
            "email": "analyst@fintech.com",
            "roles": ["analyst"]
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    access_token = auth_manager.create_access_token(
        data={"sub": user["username"], "roles": user["roles"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@router.post("/refresh")
async def refresh_token(current_user: dict = Depends(get_current_active_user)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    access_token = auth_manager.create_access_token(
        data={"sub": current_user["username"], "roles": current_user["roles"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
