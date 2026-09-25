from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import UserCreate, UserOut
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service

router = APIRouter()

@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    existing_user = await auth_service.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await auth_service.create_user(user)

@router.post("/login", response_model=str)
async def login_user(user: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    token = await auth_service.authenticate_user(user.email, user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return token

@router.get("/me", response_model=UserOut)
async def get_current_user(auth_service: AuthService = Depends(get_auth_service)):
    user = await auth_service.get_current_user()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user