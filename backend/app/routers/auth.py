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
