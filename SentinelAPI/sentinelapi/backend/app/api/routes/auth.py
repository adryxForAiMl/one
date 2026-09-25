from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.auth_service import AuthService
from app.core.security import create_access_token, verify_password

router = APIRouter()

class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
async def login(user: User, auth_service: AuthService = Depends()):
    db_user = await auth_service.get_user(user.username)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=Token)
async def register(user: User, auth_service: AuthService = Depends()):
    db_user = await auth_service.create_user(user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}