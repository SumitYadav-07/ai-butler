from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Emi, FinancialProfile, RecurringExpense, Saving, Transaction, User

ZERO = Decimal("0")


def D(value) -> Decimal:
    return ZERO if value is None else Decimal(str(value))


def f(value) -> float | None:
    return None if value is None else round(float(value), 2)


def days_in_month(day: date) -> int:
    return monthrange(day.year, day.month)[1]


def month_bounds(day: date) -> tuple[date, date]:
    return day.replace(day=1), day.replace(day=days_in_month(day))


def due_date_in_month(day: date, due_day: int) -> date:
    return day.replace(day=min(due_day, days_in_month(day)))


def get_profile(db: Session, user: User) -> FinancialProfile:
    profile = db.scalar(select(FinancialProfile).where(FinancialProfile.user_id == user.id))
    if profile is None:
        profile = FinancialProfile(user_id=user.id, emergency_reserve=0, setup_completed=False)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def sum_transactions(db: Session, user_id: int, txn_type: str, start: date | None = None,
                     end: date | None = None, category: str | None = None,
                     exclude_categories: tuple[str, ...] = ()) -> Decimal:
    query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id, Transaction.type == txn_type
    )
    if start:
        query = query.where(Transaction.txn_date >= start)
    if end:
        query = query.where(Transaction.txn_date <= end)
    if category:
        query = query.where(Transaction.category == category)
    if exclude_categories:
        query = query.where(Transaction.category.not_in(exclude_categories))
    return Decimal(db.scalar(query))


def fixed_expenses_total(db: Session, user: User) -> Decimal | None:
    """Monthly fixed expenses (excluding EMIs): profile value, else sum of recurring items."""
    profile = get_profile(db, user)
    if profile.monthly_fixed_expenses is not None:
        return Decimal(profile.monthly_fixed_expenses)
    total = db.scalar(select(func.sum(RecurringExpense.amount)).where(
        RecurringExpense.user_id == user.id, RecurringExpense.is_active.is_(True)))
    return Decimal(total) if total is not None else None


def emi_total(db: Session, user: User) -> Decimal:
    total = db.scalar(select(func.coalesce(func.sum(Emi.monthly_amount), 0)).where(
        Emi.user_id == user.id, Emi.is_active.is_(True)))
    return Decimal(total)


def savings_total(db: Session, user: User, start: date | None = None) -> Decimal:
    query = select(func.coalesce(func.sum(Saving.amount), 0)).where(Saving.user_id == user.id)
    if start:
        query = query.where(Saving.saved_on >= start)
    return Decimal(db.scalar(query))