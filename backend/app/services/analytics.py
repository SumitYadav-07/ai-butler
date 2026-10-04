from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import Transaction, User
from app.services.common import D, ZERO, days_in_month, f, month_bounds, sum_transactions
from app.utils.formatting import inr


def category_breakdown(db: Session, user_id: int, start: date, end: date) -> list[dict]:
    total_expr = func.sum(Transaction.amount)
    rows = db.execute(
        select(Transaction.category, total_expr)
        .where(Transaction.user_id == user_id, Transaction.type == "expense",
               Transaction.txn_date >= start, Transaction.txn_date <= end)
        .group_by(Transaction.category).order_by(desc(total_expr))
    ).all()
    grand = sum((Decimal(t) for _, t in rows), ZERO)
    return [
        {"category": c, "total": f(t), "percent": round(float(Decimal(t) / grand * 100), 1) if grand else 0}
        for c, t in rows
    ]


def _first_of_month_back(today: date, back: int) -> date:
    year, month = today.year, today.month - back
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def daily_series(db: Session, user_id: int, today: date, days: int = 30) -> list[dict]:
    start = today - timedelta(days=days - 1)
    rows = db.execute(
        select(Transaction.txn_date, func.sum(Transaction.amount))
        .where(Transaction.user_id == user_id, Transaction.type == "expense",
               Transaction.txn_date >= start, Transaction.txn_date <= today)
        .group_by(Transaction.txn_date)
    ).all()
    by_day = {d: Decimal(t) for d, t in rows}
    return [{"date": (start + timedelta(days=i)).isoformat(),
             "spent": f(by_day.get(start + timedelta(days=i), ZERO))} for i in range(days)]


def weekly_series(db: Session, user_id: int, today: date, weeks: int = 8) -> list[dict]:
    monday = today - timedelta(days=today.weekday())
    series = []
    for i in range(weeks - 1, -1, -1):
        start = monday - timedelta(days=7 * i)
        end = min(start + timedelta(days=6), today)
        series.append({"week_start": start.isoformat(),
                       "spent": f(sum_transactions(db, user_id, "expense", start, end))})
    return series


def monthly_series(db: Session, user_id: int, today: date, months: int = 6) -> list[dict]:
    series = []
    for back in range(months - 1, -1, -1):
        start = _first_of_month_back(today, back)
        end = start.replace(day=days_in_month(start))
        series.append({
            "month": start.strftime("%Y-%m"),
            "spent": f(sum_transactions(db, user_id, "expense", start, end)),
            "income": f(sum_transactions(db, user_id, "income", start, end)),
        })
    return series


def compare_with_previous_month(db: Session, user_id: int, today: date) -> dict:
    """This month so far vs the same number of days last month."""
    this_start, _ = month_bounds(today)
    prev_start = _first_of_month_back(today, 1)
    prev_end = prev_start.replace(day=min(today.day, days_in_month(prev_start)))
    current = {r["category"]: D(r["total"]) for r in category_breakdown(db, user_id, this_start, today)}
    previous = {r["category"]: D(r["total"]) for r in category_breakdown(db, user_id, prev_start, prev_end)}
    categories = sorted(set(current) | set(previous))
    rows = [{"category": c, "this_month": f(current.get(c, ZERO)), "last_month": f(previous.get(c, ZERO)),
             "change": f(current.get(c, ZERO) - previous.get(c, ZERO))} for c in categories]
    return {
        "rows": rows,
        "this_month_total": f(sum(current.values(), ZERO)),
        "last_month_total": f(sum(previous.values(), ZERO)),
        "has_previous_data": bool(previous),
    }


def build_insights(breakdown: list[dict], comparison: dict) -> list[str]:
    insights = []
    if breakdown:
        top = breakdown[0]
        insights.append(f"Your biggest expense category this month is {top['category']} "
                        f"({inr(top['total'])}, {top['percent']}% of your spending).")
    else:
        insights.append("You haven't recorded any expenses this month yet.")
        return insights
    if not comparison["has_previous_data"]:
        insights.append("I don't have entries from last month yet, so I can't compare periods.")
        return insights
    diff = comparison["this_month_total"] - comparison["last_month_total"]
    if diff > 0:
        insights.append(f"You've spent {inr(diff)} more than at this point last month.")
        risers = sorted((r for r in comparison["rows"] if r["change"] > 0), key=lambda r: -r["change"])[:2]
        for r in risers:
            insights.append(f"{r['category']} is up by {inr(r['change'])}. If you want to save more, "
                            f"this is one area you could look at.")
    else:
        insights.append(f"You've spent {inr(abs(diff))} less than at this point last month.")
    return insights


def get_analytics(db: Session, user: User, today: date) -> dict:
    start, end = month_bounds(today)
    breakdown = category_breakdown(db, user.id, start, end)
    comparison = compare_with_previous_month(db, user.id, today)
    return {
        "category_breakdown": breakdown,
        "highest_category": breakdown[0] if breakdown else None,
        "daily": daily_series(db, user.id, today),
        "weekly": weekly_series(db, user.id, today),
        "monthly": monthly_series(db, user.id, today),
        "comparison": comparison,
        "insights": build_insights(breakdown, comparison),
    }