from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routes.deps import get_current_user
from app.schemas.transaction import TransactionIn, TransactionOut
from app.services import transactions as svc
from app.services.common import f
from app.services.financial import calculated_balance
from app.utils.errors import MissingFinancialData
from app.utils.formatting import inr

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("", status_code=201)
def add_transaction(payload: TransactionIn, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    txn = svc.create_transaction(db, user, payload)
    balance, warning = None, None
    try:
        balance = calculated_balance(db, user)
        if balance < 0:
            warning = (f"This puts your recorded balance at {inr(balance)}, below zero. "
                       "Please check your entries if that doesn't look right.")
    except MissingFinancialData:
        warning = "Enter your current balance in Settings so I can keep your balance up to date."
    return {"transaction": TransactionOut.model_validate(txn), "balance": f(balance), "warning": warning}


@router.get("")
def list_all(type: Literal["income", "expense"] | None = None, category: str | None = None,
             start_date: date | None = None, end_date: date | None = None,
             limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items, total = svc.list_transactions(db, user, type, category, start_date, end_date, limit, offset)
    return {"items": [TransactionOut.model_validate(t) for t in items], "total": total}


@router.delete("/{txn_id}")
def remove(txn_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    svc.delete_transaction(db, user, txn_id)
    return {"message": "Transaction deleted."}