from pydantic import BaseModel, Field

from app.schemas.types import Money


class ProfileIn(BaseModel):
    """Partial update: only fields the client sends are changed."""
    name: str | None = Field(None, min_length=1, max_length=100)
    monthly_income: Money | None = None
    opening_balance: Money | None = None
    monthly_fixed_expenses: Money | None = None
    monthly_savings_target: Money | None = None
    emergency_fund_target: Money | None = None
    emergency_reserve: Money | None = None


class ProfileOut(BaseModel):
    name: str
    email: str
    monthly_income: float | None
    opening_balance: float | None
    monthly_fixed_expenses: float | None
    monthly_savings_target: float | None
    emergency_fund_target: float | None
    emergency_reserve: float
    setup_completed: bool