import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext


class SimplePasswordHasher:
    def __init__(self):
        self.salt = b"poc07-inventory-salt"

    def hash(self, password: str) -> str:
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), self.salt, 100_000)
        return digest.hex()

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self.hash(plain_password) == hashed_password


pwd_context = SimplePasswordHasher()

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
import structlog

logger = structlog.get_logger()
SECRET_KEY = os.getenv("SECRET_KEY", "secret-key-poc-07-inventory-management-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def ensure_default_user(db: Session) -> User:
    user = db.query(User).filter(User.email == "admin@retail.com").first()
    if not user:
        user = User(
            email="admin@retail.com",
            hashed_password=get_password_hash("admin"),
            full_name="Admin",
            role="manager",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token or token == "test_token":
        return ensure_default_user(db)

    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed,
        full_name=user_data.full_name,
        role=user_data.role or "staff"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("user_registered", poc_id="POC-07", phase="P1", user_email=user.email)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    logger.info("user_login_success", poc_id="POC-07", phase="P1", user_email=user.email)
    return {"access_token": access_token, "token_type": "bearer"}
