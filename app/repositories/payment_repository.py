"""
PostgreSQL-backed payment repository.
Replaces InMemoryPaymentRepository from Day 2.
All writes use explicit transactions — rollback on any exception.
"""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment import LedgerEntry, Payment


class PaymentRepository:
    def __init__(self, db: Session):
        self._db = db

    def create(self, payment: Payment) -> Payment:
        """
        Inserts a new payment. If idempotency_key already exists (IntegrityError),
        fetches and returns the existing record — no duplicate write.
        """
        try:
            self._db.add(payment)
            self._db.commit()
            self._db.refresh(payment)
            return payment
        except IntegrityError:
            self._db.rollback()
            existing = (
                self._db.query(Payment)
                .filter(Payment.idempotency_key == payment.idempotency_key)
                .one()
            )
            return existing

    def get(self, payment_id: str) -> Optional[Payment]:
        return self._db.query(Payment).filter(Payment.id == payment_id).first()

    def settle(self, payment_id: str) -> tuple[Payment, LedgerEntry]:
        """
        Atomically:
          1. Validates the payment can be settled.
          2. Updates status → settled.
          3. Inserts an immutable ledger entry.

        Both writes happen in a single transaction — either both commit or both roll back.
        """
        payment = self._db.query(Payment).filter(Payment.id == payment_id).first()
        if payment is None:
            raise ValueError(f"Payment {payment_id} not found")
        if payment.status == "settled":
            raise ValueError(f"Payment {payment_id} is already settled")
        if payment.status == "failed":
            raise ValueError(f"Payment {payment_id} has failed and cannot be settled")

        payment.status = "settled"

        entry = LedgerEntry(
            payment_id=payment.id,
            debit_account=payment.debit_account,
            credit_account=payment.credit_account,
            amount=payment.amount,
            currency=payment.currency,
        )
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(payment)
        self._db.refresh(entry)
        return payment, entry
