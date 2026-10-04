from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Emi, RecurringExpense, RecurringIncome, Saving, User
from app.routes.deps import get_current_user
from app.schemas.planning import (EmiIn, EmiOut, RecurringExpenseIn, RecurringExpenseOut,
                                  RecurringIncomeIn, RecurringIncomeOut, SavingIn, SavingOut)
from app.utils.errors import AppError


def crud_router(path: str, Model, In, Out, order_by) -> APIRouter:
    router = APIRouter(prefix=f"/api/{path}", tags=[path])

    def fetch(db: Session, user: User, item_id: int):
        obj = db.scalar(select(Model).where(Model.id == item_id, Model.user_id == user.id))
        if obj is None:
            raise AppError("That item was not found.", 404, "not_found")
        return obj

    @router.get("", response_model=list[Out])
    def list_items(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        return db.scalars(select(Model).where(Model.user_id == user.id).order_by(order_by)).all()

    @router.post("", response_model=Out, status_code=201)
    def create_item(payload: In, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        obj = Model(user_id=user.id, **payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.put("/{item_id}", response_model=Out)
    def update_item(item_id: int, payload: In, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
        obj = fetch(db, user, item_id)
        for key, value in payload.model_dump().items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @router.delete("/{item_id}")
    def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        db.delete(fetch(db, user, item_id))
        db.commit()
        return {"message": "Deleted."}

    return router


routers = [
    crud_router("recurring-expenses", RecurringExpense, RecurringExpenseIn, RecurringExpenseOut, RecurringExpense.due_day),
    crud_router("recurring-income", RecurringIncome, RecurringIncomeIn, RecurringIncomeOut, RecurringIncome.pay_day),
    crud_router("emis", Emi, EmiIn, EmiOut, Emi.due_day),
    crud_router("savings", Saving, SavingIn, SavingOut, Saving.saved_on.desc()),
]