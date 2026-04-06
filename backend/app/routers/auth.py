from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models.schemas import UserCreate, UserProfileUpdate, UserPasswordUpdate, User, Token
from app.services.auth_service import AuthService
from app.repositories.sql_repos import SqlUserRepository
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(db: Session = Depends(get_db)):
    repo = SqlUserRepository(db)
    return AuthService(repo)

@router.post("/register", response_model=User)
async def register(user_in: UserCreate, service: AuthService = Depends(get_auth_service)):
    return service.register_user(user_in)

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    if not service.authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    return {"access_token": "mocked_jwt_token_123", "token_type": "bearer"}

@router.get("/profile", response_model=User)
async def get_profile(email: str, service: AuthService = Depends(get_auth_service)):
    user = service.get_profile(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/profile", response_model=User)
async def update_profile(email: str, update_data: UserProfileUpdate, service: AuthService = Depends(get_auth_service)):
    user = service.update_profile(email, update_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/password")
async def update_password(email: str, update_data: UserPasswordUpdate, service: AuthService = Depends(get_auth_service)):
    result = service.update_password(email, update_data)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    if result is False:
        raise HTTPException(status_code=400, detail="Incorrect current password")
    return {"message": "Password updated successfully"}

from fastapi import File, UploadFile
import os
import shutil

@router.post("/upload-avatar")
async def upload_avatar(email: str, file: UploadFile = File(...), service: AuthService = Depends(get_auth_service)):
    # 1. Save file to uploads folder
    upload_dir = os.path.join("uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{email.replace('@', '_').replace('.', '_')}{file_extension}"
    file_path = os.path.join(upload_dir, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Update user avatar_url in DB
    avatar_url = f"http://localhost:8001/uploads/avatars/{file_name}"
    user = service.update_profile(email, UserProfileUpdate(avatar_url=avatar_url))
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}

# Theme endpoint for light/dark mode
@router.post("/theme")
async def update_theme(email: str, theme: str, service: AuthService = Depends(get_auth_service)):
    """Update user theme preference ('dark' or 'light')"""
    if theme not in ["dark", "light"]:
        raise HTTPException(status_code=400, detail="Theme must be 'dark' or 'light'")
    
    from app.models.schemas import UserProfileUpdate
    user = service.update_profile(email, UserProfileUpdate(theme=theme))
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"theme": theme, "message": "Theme updated successfully"}

@router.get("/theme")
async def get_theme(email: str, service: AuthService = Depends(get_auth_service)):
    """Get user theme preference"""
    user = service.get_profile(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"theme": user.theme or "dark"}
