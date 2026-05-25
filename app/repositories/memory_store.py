"""
In-memory persistence for Day 2. Replaced by PostgreSQL in Day 3.

All data is stored in plain dicts keyed by UUID strings.
Idempotency is enforced by the idempotency_key index.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID, uuid4

from app.schemas.payment import PaymentStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PaymentRecord:
    def __init__(
        self,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        debit_account: str,
        credit_account: str,
        description: Optional[str] = None,
    ):
        self.id = uuid4()
        self.amount = amount
        self.currency = currency
        self.idempotency_key = idempotency_key
        self.debit_account = debit_account
        self.credit_account = credit_account
        self.description = description
        self.status = PaymentStatus.pending
        self.created_at = _now()
        self.updated_at = _now()


class LedgerEntry:
    def __init__(
        self,
        payment_id: UUID,
        debit_account: str,
        credit_account: str,
        amount: Decimal,
        currency: str,
    ):
        self.id = uuid4()
        self.payment_id = payment_id
        self.debit_account = debit_account
        self.credit_account = credit_account
        self.amount = amount
        self.currency = currency
        self.created_at = _now()


class InMemoryPaymentRepository:
    """Thread-unsafe in-memory store — suitable for single-process local dev only."""

    def __init__(self):
        self._payments: Dict[UUID, PaymentRecord] = {}
        self._idempotency_index: Dict[str, UUID] = {}
        self._ledger: Dict[UUID, LedgerEntry] = {}

    def create(self, record: PaymentRecord) -> PaymentRecord:
        existing_id = self._idempotency_index.get(record.idempotency_key)
        if existing_id:
            # Idempotency: return the original payment unchanged
            return self._payments[existing_id]
        self._payments[record.id] = record
        self._idempotency_index[record.idempotency_key] = record.id
        return record

    def get(self, payment_id: UUID) -> Optional[PaymentRecord]:
        return self._payments.get(payment_id)

    def settle(self, payment_id: UUID) -> tuple[PaymentRecord, LedgerEntry]:
        payment = self._payments.get(payment_id)
        if payment is None:
            raise ValueError(f"Payment {payment_id} not found")
        if payment.status == PaymentStatus.settled:
            raise ValueError(f"Payment {payment_id} is already settled")
        if payment.status == PaymentStatus.failed:
            raise ValueError(f"Payment {payment_id} has failed and cannot be settled")

        payment.status = PaymentStatus.settled
        payment.updated_at = _now()

        entry = LedgerEntry(
            payment_id=payment.id,
            debit_account=payment.debit_account,
            credit_account=payment.credit_account,
            amount=payment.amount,
            currency=payment.currency,
        )
        self._ledger[entry.id] = entry
        return payment, entry


# Module-level singleton — replaced by DB session in Day 3
payment_repo = InMemoryPaymentRepository()
