from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routes.deps import get_current_user
from app.services import analytics, financial

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return financial.build_dashboard(db, user, date.today())


@router.get("/analytics")
def analytics_view(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return analytics.get_analytics(db, user, date.today())