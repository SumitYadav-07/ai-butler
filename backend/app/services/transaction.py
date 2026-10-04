from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Transaction, User
from app.schemas.transaction import TransactionIn
from app.utils.errors import AppError


def create_transaction(db: Session, user: User, data: TransactionIn) -> Transaction:
    txn = Transaction(user_id=user.id, **data.model_dump())
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def list_transactions(db: Session, user: User, txn_type: str | None = None, category: str | None = None,
                      start: date | None = None, end: date | None = None,
                      limit: int = 50, offset: int = 0) -> tuple[list[Transaction], int]:
    if start and end and start > end:
        raise AppError("The start date must be before the end date.", 422, "invalid_date_range")
    filters = [Transaction.user_id == user.id]
    if txn_type:
        filters.append(Transaction.type == txn_type)
    if category:
        filters.append(Transaction.category == category)
    if start:
        filters.append(Transaction.txn_date >= start)
    if end:
        filters.append(Transaction.txn_date <= end)
    total = db.scalar(select(func.count()).select_from(Transaction).where(*filters)) or 0
    items = db.scalars(
        select(Transaction).where(*filters)
        .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
        .limit(limit).offset(offset)
    ).all()
    return list(items), total


def delete_transaction(db: Session, user: User, txn_id: int) -> None:
    txn = db.scalar(select(Transaction).where(Transaction.id == txn_id, Transaction.user_id == user.id))
    if txn is None:
        raise AppError("That transaction was not found.", 404, "not_found")
    db.delete(txn)
    db.commit()