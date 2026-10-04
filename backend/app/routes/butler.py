from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import butler
from app.database import get_db
from app.models import User
from app.routes.deps import get_current_user
from app.schemas.butler import ChatIn

router = APIRouter(prefix="/api/butler", tags=["butler"])


@router.post("/chat")
def chat(payload: ChatIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return butler.answer(db, user, payload.message, date.today())


@router.get("/history")
def get_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return butler.history(db, user)


@router.delete("/history")
def delete_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    butler.clear_history(db, user)
    return {"message": "Chat history cleared."}