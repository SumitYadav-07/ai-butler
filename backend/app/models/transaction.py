from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

EXPENSE_CATEGORIES = [
    "Food", "Transport", "Shopping", "Entertainment", "Bills", "Education",
    "Healthcare", "Rent", "EMI", "Travel", "Investments", "Other",
]
INCOME_CATEGORIES = ["Salary", "Allowance", "Other Income"]


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_txn_user_date", "user_id", "txn_date"),
        Index("idx_txn_user_category", "user_id", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    category: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(255), default="")
    txn_date: Mapped[date] = mapped_column(Date)
    payment_method: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())