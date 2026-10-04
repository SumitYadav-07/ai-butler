from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from app.schemas.types import PositiveMoney


class TransactionIn(BaseModel):
    type: Literal["income", "expense"]
    amount: PositiveMoney
    category: str
    description: str = Field("", max_length=255)
    txn_date: date
    payment_method: str | None = Field(None, max_length=30)

    @field_validator("txn_date")
    @classmethod
    def check_date(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("The date cannot be in the future.")
        if v < today - timedelta(days=366 * 5):
            raise ValueError("The date is too far in the past.")
        return v

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def category_matches_type(self):
        allowed = EXPENSE_CATEGORIES if self.type == "expense" else INCOME_CATEGORIES
        if self.category not in allowed:
            raise ValueError(f"Category '{self.category}' is not valid for {self.type}. Choose one of: {', '.join(allowed)}.")
        return self


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    amount: float
    category: str
    description: str
    txn_date: date
    payment_method: str | None