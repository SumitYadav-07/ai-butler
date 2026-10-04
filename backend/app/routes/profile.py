from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routes.deps import get_current_user
from app.schemas.profile import ProfileIn, ProfileOut
from app.services.common import f, get_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _out(user: User, p) -> ProfileOut:
    return ProfileOut(
        name=user.name, email=user.email, monthly_income=f(p.monthly_income),
        opening_balance=f(p.opening_balance), monthly_fixed_expenses=f(p.monthly_fixed_expenses),
        monthly_savings_target=f(p.monthly_savings_target), emergency_fund_target=f(p.emergency_fund_target),
        emergency_reserve=f(p.emergency_reserve) or 0.0, setup_completed=p.setup_completed,
    )


@router.get("", response_model=ProfileOut)
def read_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _out(user, get_profile(db, user))


@router.put("", response_model=ProfileOut)
def update_profile(payload: ProfileIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = get_profile(db, user)
    data = payload.model_dump(exclude_unset=True)
    name = data.pop("name", None)
    if name:
        user.name = name.strip()
    if data.get("emergency_reserve", 0) is None:
        data["emergency_reserve"] = 0
    for key, value in data.items():
        setattr(profile, key, value)
    profile.setup_completed = profile.monthly_income is not None and profile.opening_balance is not None
    db.commit()
    db.refresh(profile)
    return _out(user, profile)