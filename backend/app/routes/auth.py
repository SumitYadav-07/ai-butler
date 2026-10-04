from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FinancialProfile, User
from app.routes.deps import get_current_user
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.utils.errors import AppError
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise AppError("An account with this email already exists.", 409, "email_taken")
    user = User(name=payload.name, email=email, password_hash=hash_password(payload.password))
    user.profile = FinancialProfile(emergency_reserve=0, setup_completed=False)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError("An account with this email already exists.", 409, "email_taken")
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError("Incorrect email or password.", 401, "invalid_credentials")
    return TokenOut(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/logout")
def logout(_: User = Depends(get_current_user)):
    # Tokens are stateless; the client discards its token. Nothing is stored server-side.
    return {"message": "You have been logged out."}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user