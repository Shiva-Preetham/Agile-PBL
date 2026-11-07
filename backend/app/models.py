"""Database tables."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    tenure_months: Mapped[int] = mapped_column(Integer)
    contract_type: Mapped[str] = mapped_column(String(20), index=True)
    monthly_charges: Mapped[float] = mapped_column(Float)
    total_charges: Mapped[float] = mapped_column(Float)
    internet_service: Mapped[str] = mapped_column(String(20))
    tech_support: Mapped[str] = mapped_column(String(5))
    payment_method: Mapped[str] = mapped_column(String(30))
    support_tickets: Mapped[int] = mapped_column(Integer)
    monthly_usage_gb: Mapped[float] = mapped_column(Float)
    days_since_last_login: Mapped[int] = mapped_column(Integer)

    churn_probability: Mapped[float | None] = mapped_column(Float, index=True)
    risk_category: Mapped[str | None] = mapped_column(String(10), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    action: Mapped["RetentionAction | None"] = relationship(
        back_populates="customer", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )


class RetentionAction(Base):
    __tablename__ = "retention_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_pk: Mapped[int] = mapped_column(ForeignKey("customers.id"), unique=True)
    rule_id: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="Pending", index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    customer: Mapped[Customer] = relationship(back_populates="action")
