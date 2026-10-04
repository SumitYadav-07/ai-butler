from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Emi, EmergencyFund, RecurringExpense, User
from app.services import analytics
from app.services.common import (D, ZERO, days_in_month, due_date_in_month, emi_total, f,
                                 fixed_expenses_total, get_profile, month_bounds, savings_total,
                                 sum_transactions)
from app.utils.errors import MissingFinancialData
from app.utils.formatting import inr

LUMPY_CATEGORIES = ("Rent", "EMI")  # excluded from the "variable spending" daily average


def calculated_balance(db: Session, user: User, as_of: date | None = None) -> Decimal:
    profile = get_profile(db, user)
    if profile.opening_balance is None:
        raise MissingFinancialData("current balance")
    income = sum_transactions(db, user.id, "income", end=as_of)
    expense = sum_transactions(db, user.id, "expense", end=as_of)
    return Decimal(profile.opening_balance) + income - expense


def upcoming_items(db: Session, user: User, today: date, include_today: bool = True) -> list[dict]:
    """Recurring expenses and EMIs the user entered whose due date is still ahead this month."""
    items = []
    expenses = db.scalars(select(RecurringExpense).where(
        RecurringExpense.user_id == user.id, RecurringExpense.is_active.is_(True))).all()
    emis = db.scalars(select(Emi).where(Emi.user_id == user.id, Emi.is_active.is_(True))).all()
    for e in expenses:
        items.append({"name": e.name, "kind": "expense", "amount": D(e.amount),
                      "due_date": due_date_in_month(today, e.due_day)})
    for m in emis:
        items.append({"name": m.name, "kind": "emi", "amount": D(m.monthly_amount),
                      "due_date": due_date_in_month(today, m.due_day)})
    items = [i for i in items if (i["due_date"] >= today if include_today else i["due_date"] > today)]
    return sorted(items, key=lambda i: i["due_date"])


def safe_daily_spending(db: Session, user: User, today: date, balance: Decimal) -> dict:
    profile = get_profile(db, user)
    upcoming_total = sum((i["amount"] for i in upcoming_items(db, user, today)), ZERO)
    reserve = D(profile.emergency_reserve)
    savings_target = D(profile.monthly_savings_target)
    usable = balance - upcoming_total - reserve - savings_target
    days_left = days_in_month(today) - today.day + 1  # includes today
    safe = max(usable, ZERO) / days_left
    assumptions = []
    if profile.monthly_savings_target is None:
        assumptions.append("No monthly savings target entered, so none was set aside.")
    if not profile.emergency_reserve:
        assumptions.append("No emergency reserve entered, so none was set aside.")
    explanation = (
        f"Current balance {inr(balance)} − upcoming bills and EMIs {inr(upcoming_total)} − "
        f"emergency reserve {inr(reserve)} − savings target {inr(savings_target)} = "
        f"usable money {inr(usable)}. Divided by {days_left} remaining days (including today) "
        f"≈ {inr(safe)} per day."
    )
    if usable < 0:
        explanation += " Your usable amount is below zero, so the safe daily amount is shown as ₹0."
    return {
        "current_balance": f(balance), "upcoming_total": f(upcoming_total),
        "emergency_reserve": f(reserve), "savings_target": f(savings_target),
        "usable_money": f(usable), "days_remaining": days_left,
        "safe_daily_amount": f(safe), "assumptions": assumptions, "explanation": explanation,
    }


def spending_forecast(db: Session, user: User, today: date, balance: Decimal) -> dict:
    """Estimate only; based on expenses entered so far this month."""
    profile = get_profile(db, user)
    start, _ = month_bounds(today)
    spent = sum_transactions(db, user.id, "expense", start, today)
    if spent == 0:
        return {"available": False,
                "message": "I need at least one expense entered this month before I can estimate."}
    lumpy = sum_transactions(db, user.id, "expense", start, today, exclude_categories=())
    variable = sum_transactions(db, user.id, "expense", start, today, exclude_categories=LUMPY_CATEGORIES)
    daily_variable = variable / today.day
    days_after_today = days_in_month(today) - today.day
    future_variable = daily_variable * days_after_today
    future_fixed = sum((i["amount"] for i in upcoming_items(db, user, today, include_today=False)), ZERO)
    estimated_spending = spent + future_variable + future_fixed
    estimated_balance = balance - future_variable - future_fixed
    estimated_savings = None
    if profile.monthly_income is not None:
        estimated_savings = Decimal(profile.monthly_income) - estimated_spending
    return {
        "available": True,
        "is_estimate": True,
        "spent_so_far": f(spent),
        "estimated_monthly_spending": f(estimated_spending),
        "estimated_remaining_balance": f(estimated_balance),
        "estimated_savings": f(estimated_savings),
        "message": (f"Based on your spending entered so far this month, your estimated monthly "
                    f"spending is {inr(estimated_spending)}. This is an estimate, not a guarantee."),
    }


def assess_health(balance: Decimal | None, income, upcoming_total: Decimal, usable: Decimal | None,
                  savings_target, forecast: dict | None) -> dict:
    """Simple status indicator. This is NOT an official financial score."""
    if balance is None or income is None:
        return {"status": "Unknown",
                "reason": "Enter your current balance and monthly income to see your financial health."}
    income, target = D(income), D(savings_target)
    if balance < 0:
        return {"status": "Critical",
                "reason": f"Your recorded balance is {inr(balance)}, which is below zero. "
                          "Check your entries for anything missing or entered twice."}
    if balance < upcoming_total:
        return {"status": "Critical",
                "reason": f"Your balance ({inr(balance)}) is lower than the {inr(upcoming_total)} "
                          "you have due for the rest of this month."}
    if usable is not None and usable < 0:
        return {"status": "Warning",
                "reason": f"After upcoming bills, your emergency reserve and your savings target, "
                          f"you are about {inr(abs(usable))} short for this month."}
    if forecast and forecast.get("available"):
        est = D(forecast["estimated_monthly_spending"])
        if est > income:
            return {"status": "Warning",
                    "reason": f"Your estimated spending this month ({inr(est)}) is higher than your "
                              f"monthly income ({inr(income)})."}
        if est > income - target:
            return {"status": "Watch",
                    "reason": "Your spending this month is currently higher than the pace needed to "
                              f"reach your {inr(target)} savings target."}
    return {"status": "Safe",
            "reason": "Based on what you've entered, your balance covers upcoming bills and your "
                      "spending is on pace with your plan."}


def emergency_status(db: Session, user: User) -> dict:
    profile = get_profile(db, user)
    row = db.scalar(select(EmergencyFund).where(EmergencyFund.user_id == user.id))
    current = D(row.current_amount) if row else ZERO
    essential = row.monthly_essential_expenses if row else None
    months = row.target_months if row else None
    target, source = None, None
    if essential is not None and months:
        target, source = Decimal(essential) * months, "monthly essential expenses × months"
    elif profile.emergency_fund_target is not None:
        target, source = Decimal(profile.emergency_fund_target), "target entered in your profile"
    if target is None or target <= 0:
        return {"current_amount": f(current), "monthly_essential_expenses": f(essential),
                "target_months": months, "target": None, "remaining": None, "progress_percent": None,
                "message": "I don't have enough information to calculate that. Please enter your "
                           "monthly essential expenses and the number of months you want covered."}
    remaining = max(target - current, ZERO)
    progress = min(float(current / target * 100), 100.0)
    return {"current_amount": f(current), "monthly_essential_expenses": f(essential),
            "target_months": months, "target": f(target), "target_source": source,
            "remaining": f(remaining), "progress_percent": round(progress, 1),
            "message": f"You have {inr(current)} of your {inr(target)} target ({progress:.0f}%)."}


def _butler_message(status: str, safe_daily: float | None) -> str:
    openers = {
        "Safe": "Your spending is under control.",
        "Watch": "Your spending is a little ahead of your plan.",
        "Warning": "Spending is running ahead of your plan this month.",
        "Critical": "Your balance is tight right now.",
        "Unknown": "Let's get your numbers in first.",
    }
    if safe_daily is None:
        return openers[status] + " Enter your current balance and income so I can calculate a daily amount."
    return (f"{openers[status]} You can safely spend approximately {inr(safe_daily)}/day "
            f"based on the information you've entered.")


def build_dashboard(db: Session, user: User, today: date) -> dict:
    profile = get_profile(db, user)
    month_start, _ = month_bounds(today)
    week_start = today - timedelta(days=today.weekday())

    missing = []
    if profile.opening_balance is None:
        missing.append("current balance")
    if profile.monthly_income is None:
        missing.append("monthly income")

    try:
        balance = calculated_balance(db, user)
    except MissingFinancialData:
        balance = None

    upcoming = upcoming_items(db, user, today)
    upcoming_total = sum((i["amount"] for i in upcoming), ZERO)
    safe = forecast = None
    if balance is not None:
        safe = safe_daily_spending(db, user, today, balance)
        forecast = spending_forecast(db, user, today, balance)

    health = assess_health(balance, profile.monthly_income, upcoming_total,
                           D(safe["usable_money"]) if safe else None,
                           profile.monthly_savings_target, forecast)
    return {
        "name": user.name,
        "missing_fields": missing,
        "current_balance": f(balance),
        "today_spending": f(sum_transactions(db, user.id, "expense", today, today)),
        "week_spending": f(sum_transactions(db, user.id, "expense", week_start, today)),
        "month_spending": f(sum_transactions(db, user.id, "expense", month_start, today)),
        "month_income_logged": f(sum_transactions(db, user.id, "income", month_start, today)),
        "monthly_income": f(profile.monthly_income),
        "monthly_fixed_expenses": f(fixed_expenses_total(db, user)),
        "emi_total": f(emi_total(db, user)),
        "total_savings": f(savings_total(db, user)),
        "upcoming_expenses": [{**i, "amount": f(i["amount"]), "due_date": i["due_date"].isoformat()}
                              for i in upcoming],
        "upcoming_total": f(upcoming_total),
        "safe_daily_spending": safe,
        "forecast": forecast,
        "emergency_fund": emergency_status(db, user),
        "spending_breakdown": analytics.category_breakdown(db, user.id, month_start, today),
        "financial_health": health,
        "disclaimer": "Status labels are simple indicators based only on the numbers you entered. "
                      "They are not an official financial score.",
        "butler_message": _butler_message(health["status"], safe["safe_daily_amount"] if safe else None),
    }