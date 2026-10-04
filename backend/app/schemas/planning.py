from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import EXPENSE_CATEGORIES
from app.schemas.types import Money, PositiveMoney


class RecurringExpenseIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = "Bills"
    amount: PositiveMoney
    due_day: int = Field(ge=1, le=31)
    is_active: bool = True

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        if v not in EXPENSE_CATEGORIES:
            raise ValueError("Unknown category.")
        return v


class RecurringExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category: str
    amount: float
    due_day: int
    is_active: bool


class RecurringIncomeIn(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    amount: PositiveMoney
    pay_day: int = Field(ge=1, le=31)
    is_active: bool = True


class RecurringIncomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    amount: float
    pay_day: int
    is_active: bool


class EmiIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    monthly_amount: PositiveMoney
    due_day: int = Field(ge=1, le=31)
    remaining_months: int | None = Field(None, ge=0, le=600)
    is_active: bool = True


class EmiOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    monthly_amount: float
    due_day: int
    remaining_months: int | None
    is_active: bool


class SavingIn(BaseModel):
    amount: PositiveMoney
    saved_on: date
    note: str = Field("", max_length=255)


class SavingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: float
    saved_on: date
    note: str


class EmergencyIn(BaseModel):
    current_amount: Money | None = None
    monthly_essential_expenses: Money | None = None
    target_months: int | None = Field(None, ge=1, le=60)


class GoalIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount: PositiveMoney
    saved_amount: Money = 0
    target_date: date

    @field_validator("target_date")
    @classmethod
    def future_date(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Please pick a target date that is today or later.")
        return v


class EmiCalcIn(BaseModel):
    new_emi: PositiveMoney
    loan_months: int = Field(ge=1, le=600)
    existing_emi: Money | None = None
    monthly_income: PositiveMoney | None = None
    fixed_expenses: Money | None = None
    current_savings: Money | None = None


class DailyBalanceIn(BaseModel):
    reported_balance: Money
    balance_date: date | None = None
    note: str = Field("", max_length=255)

    @field_validator("balance_date")
    @classmethod
    def not_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("The date cannot be in the future.")
        return v