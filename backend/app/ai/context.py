import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.ai.intents import detect_intent, extract_amount, extract_category
from app.models import Transaction, User
from app.schemas.planning import EmiCalcIn
from app.services import analytics, calculators, financial
from app.services.common import get_profile, month_bounds
from app.utils.errors import MissingFinancialData
from app.utils.formatting import inr


@dataclass
class Env:
    db: Session
    user: User
    today: date
    dash: dict
    amount: float | None
    category: str | None


def _result(lines=None, data=None, missing=None, needs_amount=False) -> dict:
    return {"lines": lines or [], "data": data or {}, "missing": missing or [],
            "needs_amount": needs_amount}


def _affordability(env: Env) -> dict:
    safe = env.dash["safe_daily_spending"]
    if safe is None:
        return _result(missing=["current balance"])
    if env.amount is None:
        return _result(needs_amount=True)
    amount, balance, usable, days = env.amount, safe["current_balance"], safe["usable_money"], safe["days_remaining"]
    balance_after, usable_after = balance - amount, usable - amount
    lines = [
        f"Current balance: {inr(balance)}",
        f"Set aside this month: upcoming bills and EMIs {inr(safe['upcoming_total'])}, "
        f"emergency reserve {inr(safe['emergency_reserve'])}, savings target {inr(safe['savings_target'])}",
        f"Usable money before this purchase: {inr(usable)}",
        f"Purchase amount: {inr(amount)}",
        f"Balance after purchase: {inr(balance_after)}",
        f"Usable money after purchase: {inr(usable_after)}",
    ]
    if usable_after >= 0:
        lines.append(f"Safe daily spending after the purchase would be about "
                     f"{inr(usable_after / days)} for the remaining {days} days.")
    else:
        lines.append("This purchase would use money set aside for bills, reserve or savings.")
    return _result(lines, {"purchase_amount": amount, "balance_after": round(balance_after, 2),
                           "usable_after": round(usable_after, 2),
                           "fits_within_usable": usable_after >= 0,
                           "fits_within_balance": balance_after >= 0})


def _daily(env: Env) -> dict:
    safe = env.dash["safe_daily_spending"]
    if safe is None:
        return _result(missing=["current balance"])
    return _result([safe["explanation"], *safe["assumptions"]], {"safe_daily_amount": safe["safe_daily_amount"]})


def _category(env: Env) -> dict:
    breakdown, total = env.dash["spending_breakdown"], env.dash["month_spending"]
    if env.category:
        row = next((r for r in breakdown if r["category"] == env.category), None)
        if row:
            line = (f"{env.category} spending this month so far: {inr(row['total'])} "
                    f"({row['percent']}% of your {inr(total)} total spending)")
        else:
            line = f"No {env.category} expenses have been entered this month."
        return _result([line], {"category": env.category, "spent": row["total"] if row else 0.0})
    lines = [f"{r['category']}: {inr(r['total'])} ({r['percent']}%)" for r in breakdown]
    return _result(lines or ["No expenses have been entered this month yet."], {"total": total})


def _overspending(env: Env) -> dict:
    d = env.dash
    if d["monthly_income"] is None:
        return _result(missing=["monthly income"])
    spent, income = d["month_spending"], d["monthly_income"]
    lines = [f"Spent so far this month: {inr(spent)}", f"Monthly income you entered: {inr(income)}"]
    if income > 0:
        lines.append(f"That is {spent / income * 100:.0f}% of your income so far.")
    fc = d["forecast"]
    if fc and fc.get("available"):
        lines.append(fc["message"])
    health = d["financial_health"]
    lines.append(f"Status: {health['status']}. {health['reason']}")
    comp = analytics.compare_with_previous_month(env.db, env.user.id, env.today)
    if comp["has_previous_data"]:
        lines.append(f"At this point last month you had spent {inr(comp['last_month_total'])}.")
    else:
        lines.append("There is no entered data from last month to compare with.")
    return _result(lines, {"status": health["status"]})


def _emi(env: Env) -> dict:
    d = env.dash
    missing = []
    if d["monthly_income"] is None:
        missing.append("monthly income")
    if d["monthly_fixed_expenses"] is None:
        missing.append("monthly fixed expenses")
    if missing:
        return _result(missing=missing)
    if env.amount is None:
        return _result(needs_amount=True)
    try:
        res = calculators.calculate_emi_affordability(
            env.db, env.user,
            EmiCalcIn(new_emi=Decimal(str(round(env.amount, 2))), loan_months=12))
    except MissingFinancialData as exc:
        return _result(missing=[exc.message])
    lines = [
        f"The new EMI is {inr(env.amount)} (loan duration was not given; it does not change this category)."
        if line.startswith("The new EMI is") else line
        for line in res["explanation"]
    ]
    lines.append(f"Category: {res['category']}")
    return _result(lines, {"category": res["category"], "remaining_monthly_amount": res["remaining_monthly_amount"]})


def _save(env: Env) -> dict:
    d, profile = env.dash, get_profile(env.db, env.user)
    missing = []
    if d["monthly_income"] is None:
        missing.append("monthly income")
    if d["monthly_fixed_expenses"] is None:
        missing.append("monthly fixed expenses")
    if missing:
        return _result(missing=missing)
    income, fixed, emi = d["monthly_income"], d["monthly_fixed_expenses"], d["emi_total"]
    left = income - fixed - emi
    lines = [f"Monthly income: {inr(income)}", f"Fixed expenses: {inr(fixed)}", f"EMIs: {inr(emi)}",
             f"Left after fixed expenses and EMIs: {inr(left)}"]
    if profile.monthly_savings_target is None:
        lines.append("You haven't entered a monthly savings target yet.")
    else:
        target = float(profile.monthly_savings_target)
        lines.append(f"Your monthly savings target: {inr(target)}")
        lines.append("Your target fits within what is left." if target <= left
                     else f"Your target is {inr(target - left)} more than what is left after commitments.")
    return _result(lines, {"left_after_commitments": round(left, 2)})


def _emergency(env: Env) -> dict:
    e = env.dash["emergency_fund"]
    if e["target"] is None:
        return _result(missing=["monthly essential expenses and the number of months you want your emergency fund to cover"])
    lines = [e["message"], f"Remaining to reach the target: {inr(e['remaining'])}",
             f"Target worked out as: {e['target_source']}"]
    safe = env.dash["safe_daily_spending"]
    if safe:
        lines.append(f"Emergency reserve currently held back in safe spending: {inr(safe['emergency_reserve'])}")
    return _result(lines, {"progress_percent": e["progress_percent"]})


def _why(env: Env) -> dict:
    start, _ = month_bounds(env.today)
    comp = analytics.compare_with_previous_month(env.db, env.user.id, env.today)
    breakdown = env.dash["spending_breakdown"]
    lines = [f"Spent this month so far: {inr(comp['this_month_total'])}",
             f"Spent in the same period last month: {inr(comp['last_month_total'])}"]
    lines += analytics.build_insights(breakdown, comp)
    return _result(lines, {"has_previous_data": comp["has_previous_data"]})


def _biggest(env: Env) -> dict:
    breakdown = env.dash["spending_breakdown"]
    if not breakdown:
        return _result(["No expenses have been entered this month yet."])
    start, _ = month_bounds(env.today)
    top = env.db.scalars(
        select(Transaction).where(Transaction.user_id == env.user.id, Transaction.type == "expense",
                                  Transaction.txn_date >= start, Transaction.txn_date <= env.today)
        .order_by(desc(Transaction.amount)).limit(3)).all()
    lines = [f"{r['category']}: {inr(r['total'])} ({r['percent']}%)" for r in breakdown[:5]]
    for t in top:
        note = re.sub(r"\s+", " ", t.description)[:40]
        lines.append(f"Largest single expense: {inr(t.amount)} on {t.category}" + (f" ({note})" if note else ""))
    return _result(lines)


def _invest(env: Env) -> dict:
    return _result(data={"topic": "investing_education_only"})


def _general(env: Env) -> dict:
    d, lines = env.dash, []
    if d["current_balance"] is not None:
        lines.append(f"Current balance: {inr(d['current_balance'])}")
    if d["monthly_income"] is not None:
        lines.append(f"Monthly income: {inr(d['monthly_income'])}")
    lines.append(f"Spent this month so far: {inr(d['month_spending'])}")
    lines.append(f"Status: {d['financial_health']['status']}. {d['financial_health']['reason']}")
    return _result(lines)


HANDLERS = {
    "affordability": _affordability, "daily_spend": _daily, "category_spend": _category,
    "overspending": _overspending, "emi": _emi, "save": _save, "emergency": _emergency,
    "why_increase": _why, "biggest": _biggest, "invest": _invest, "general": _general,
}


def build_context(db: Session, user: User, message: str, today: date) -> dict:
    intent = detect_intent(message)
    env = Env(db=db, user=user, today=today, dash=financial.build_dashboard(db, user, today),
              amount=extract_amount(message), category=extract_category(message))
    return {"intent": intent, "today": today.isoformat(), "currency": "INR",
            "not_entered_yet": env.dash["missing_fields"], **HANDLERS[intent](env)}