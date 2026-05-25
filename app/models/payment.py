import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    idempotency_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    debit_account: Mapped[str] = mapped_column(String(255), nullable=False)
    credit_account: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    ledger_entries: Mapped[List["LedgerEntry"]] = relationship(
        "LedgerEntry", back_populates="payment"
    )


class LedgerEntry(Base):
    """
    Immutable record of a debit/credit pair. Never updated or deleted —
    financial audit trail depends on this invariant.
    """

    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    payment_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("payments.id"), nullable=False, index=True
    )
    debit_account: Mapped[str] = mapped_column(String(255), nullable=False)
    credit_account: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    payment: Mapped["Payment"] = relationship("Payment", back_populates="ledger_entries")
