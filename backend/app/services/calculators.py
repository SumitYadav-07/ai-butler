from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyBalance, FinancialGoal, User
from app.schemas.planning import DailyBalanceIn, EmiCalcIn
from app.services.common import (D, ZERO, emi_total, f, fixed_expenses_total, get_profile,
                                 savings_total)
from app.services.financial import calculated_balance
from app.services.transactions import list_transactions
from app.utils.errors import MissingFinancialData
from app.utils.formatting import inr

DISCLAIMER = ("This is a simple calculation based only on the numbers you entered. "
              "It is not professional financial advice.")


def calculate_emi_affordability(db: Session, user: User, data: EmiCalcIn) -> dict:
    profile = get_profile(db, user)
    income = data.monthly_income if data.monthly_income is not None else profile.monthly_income
    if income is None or Decimal(income) <= 0:
        raise MissingFinancialData("monthly income")
    fixed = data.fixed_expenses if data.fixed_expenses is not None else fixed_expenses_total(db, user)
    if fixed is None:
        raise MissingFinancialData("monthly fixed expenses")
    existing = data.existing_emi if data.existing_emi is not None else emi_total(db, user)
    savings = data.current_savings if data.current_savings is not None else savings_total(db, user)

    income, fixed, existing, savings = Decimal(income), Decimal(fixed), Decimal(existing), Decimal(savings)
    new_emi = Decimal(data.new_emi)
    remaining = income - fixed - existing - new_emi
    emi_ratio = (existing + new_emi) / income * 100
    remaining_pct = remaining / income * 100

    if emi_ratio <= 20 and remaining_pct >= 30:
        category = "Comfortable"
    elif emi_ratio <= 35 and remaining_pct >= 15:
        category = "Manageable"
    elif emi_ratio <= 50 and remaining >= 0:
        category = "Risky"
    else:
        category = "Not recommended based on current entered data"

    lines = [
        f"Your monthly income is {inr(income)}.",
        f"Existing fixed expenses are {inr(fixed)}.",
        f"Existing EMI is {inr(existing)}.",
        f"The new EMI is {inr(new_emi)} for {data.loan_months} months.",
        f"Based on the information you entered, your remaining monthly amount would be {inr(remaining)}.",
        f"Your total EMIs would be {emi_ratio:.0f}% of your income.",
    ]
    if remaining < 0:
        lines.append("Your entered expenses and EMIs would be more than your income each month.")
    if savings > 0:
        lines.append(f"Your entered savings of {inr(savings)} would cover about "
                     f"{float(savings / new_emi):.1f} months of the new EMI.")
    return {
        "category": category,
        "remaining_monthly_amount": f(remaining),
        "emi_percent_of_income": round(float(emi_ratio), 1),
        "total_payable": f(new_emi * data.loan_months),
        "explanation": lines,
        "rules_used": "Comfortable: EMIs ≤ 20% of income and ≥ 30% left over. Manageable: ≤ 35% and ≥ 15% left. "
                      "Risky: ≤ 50% and not below zero. Otherwise: not recommended based on current entered data.",
        "disclaimer": DISCLAIMER,
    }


def goal_view(goal: FinancialGoal, today: date) -> dict:
    target, saved = Decimal(goal.target_amount), Decimal(goal.saved_amount)
    remaining = max(target - saved, ZERO)
    days_left = (goal.target_date - today).days
    months_left = max(days_left / 30.44, 0)
    if remaining == 0:
        suggested, note = ZERO, "Goal reached."
    elif days_left <= 0:
        suggested, note = remaining, "The target date has passed; the full remaining amount is shown."
    else:
        months = max(months_left, 1)
        suggested, note = remaining / Decimal(str(months)), ""
    return {
        "id": goal.id, "name": goal.name, "target_amount": f(target), "saved_amount": f(saved),
        "target_date": goal.target_date.isoformat(), "remaining": f(remaining),
        "progress_percent": round(min(float(saved / target * 100), 100.0), 1),
        "months_left": round(months_left, 1), "suggested_monthly_saving": f(suggested), "note": note,
    }


def record_daily_balance(db: Session, user: User, data: DailyBalanceIn) -> dict:
    day = data.balance_date or date.today()
    calculated = calculated_balance(db, user, as_of=day)
    reported = Decimal(data.reported_balance)

    row = db.scalar(select(DailyBalance).where(DailyBalance.user_id == user.id,
                                               DailyBalance.balance_date == day))
    if row is None:
        row = DailyBalance(user_id=user.id, balance_date=day)
        db.add(row)
    row.calculated_balance, row.reported_balance, row.note = calculated, reported, data.note
    db.commit()

    diff = reported - calculated
    todays, _ = list_transactions(db, user, start=day, end=day, limit=200)
    if diff == 0:
        message = "Your recorded transactions match the balance you reported. Nicely done."
        hint = None
    else:
        message = (f"Your recorded transactions indicate {inr(calculated)}, but you reported "
                   f"{inr(reported)}. There is a {inr(abs(diff))} difference.")
        hint = {"type": "expense" if diff < 0 else "income", "amount": f(abs(diff)),
                "note": "I can't tell where this money went. You can review today's entries, or add a "
                        "transaction yourself if you remember something that's missing."}
    return {
        "date": day.isoformat(), "calculated_balance": f(calculated), "reported_balance": f(reported),
        "difference": f(diff), "matches": diff == 0, "message": message,
        "possible_missing_transaction": hint,
        "transactions_for_day": [{"id": t.id, "type": t.type, "amount": f(t.amount),
                                  "category": t.category, "description": t.description} for t in todays],
    }