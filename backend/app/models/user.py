from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped["FinancialProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    opening_balance: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    monthly_fixed_expenses: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    monthly_savings_target: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    emergency_fund_target: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    emergency_reserve: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    setup_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="profile")