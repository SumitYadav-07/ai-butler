from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DailyBalance, EmergencyFund, FinancialGoal, User
from app.routes.deps import get_current_user
from app.schemas.planning import DailyBalanceIn, EmergencyIn, EmiCalcIn, GoalIn
from app.services import calculators
from app.services.common import f
from app.services.financial import emergency_status
from app.utils.errors import AppError

router = APIRouter(prefix="/api", tags=["tools"])


# ---- EMI ----
@router.post("/emi/calculate")
def emi_calculate(payload: EmiCalcIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return calculators.calculate_emi_affordability(db, user, payload)


# ---- Emergency fund ----
@router.get("/emergency-fund")
def get_emergency(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return emergency_status(db, user)


@router.put("/emergency-fund")
def put_emergency(payload: EmergencyIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(EmergencyFund).where(EmergencyFund.user_id == user.id))
    if row is None:
        row = EmergencyFund(user_id=user.id, current_amount=0)
        db.add(row)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, 0 if (key == "current_amount" and value is None) else value)
    db.commit()
    return emergency_status(db, user)


# ---- Goals ----
def _get_goal(db: Session, user: User, goal_id: int) -> FinancialGoal:
    goal = db.scalar(select(FinancialGoal).where(FinancialGoal.id == goal_id, FinancialGoal.user_id == user.id))
    if goal is None:
        raise AppError("That goal was not found.", 404, "not_found")
    return goal


@router.post("/goals", status_code=201)
def create_goal(payload: GoalIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    goal = FinancialGoal(user_id=user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return calculators.goal_view(goal, date.today())


@router.get("/goals")
def list_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    goals = db.scalars(select(FinancialGoal).where(FinancialGoal.user_id == user.id)
                       .order_by(FinancialGoal.target_date)).all()
    return [calculators.goal_view(g, date.today()) for g in goals]


@router.put("/goals/{goal_id}")
def update_goal(goal_id: int, payload: GoalIn, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    goal = _get_goal(db, user, goal_id)
    for key, value in payload.model_dump().items():
        setattr(goal, key, value)
    db.commit()
    db.refresh(goal)
    return calculators.goal_view(goal, date.today())


@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(_get_goal(db, user, goal_id))
    db.commit()
    return {"message": "Goal deleted."}


# ---- Daily balance (end-of-day Butler check) ----
@router.get("/daily-balance/prompt")
def daily_prompt(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(DailyBalance).where(DailyBalance.user_id == user.id,
                                               DailyBalance.balance_date == date.today()))
    return {"question": "How much money do you have left at the end of today?",
            "already_submitted": row is not None,
            "reported_balance": f(row.reported_balance) if row else None}


@router.post("/daily-balance")
def submit_daily_balance(payload: DailyBalanceIn, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    return calculators.record_daily_balance(db, user, payload)


@router.get("/daily-balance")
def daily_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(DailyBalance).where(DailyBalance.user_id == user.id)
                      .order_by(DailyBalance.balance_date.desc()).limit(30)).all()
    return [{"date": r.balance_date.isoformat(), "calculated_balance": f(r.calculated_balance),
             "reported_balance": f(r.reported_balance),
             "difference": f(r.reported_balance - r.calculated_balance), "note": r.note} for r in rows]