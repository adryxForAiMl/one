from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import User
from app.core.security import verify_password, create_access_token
from app.schemas import Token, UserCreate
from app.database import get_db

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_create: UserCreate) -> User:
        user = User(**user_create.dict())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str) -> Token:
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(data={"sub": user.username})
        return Token(access_token=access_token, token_type="bearer")

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)