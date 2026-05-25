from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.payment import Payment
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import (
    LedgerEntryResponse,
    PaymentCreate,
    PaymentResponse,
    SettleResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])


def _payment_to_response(p: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=p.id,
        amount=p.amount,
        currency=p.currency,
        status=p.status,
        idempotency_key=p.idempotency_key,
        description=p.description,
        debit_account=p.debit_account,
        credit_account=p.credit_account,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payment intent",
)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> PaymentResponse:
    """
    Creates a new payment in PENDING status.
    Idempotency: the same idempotency_key always returns the original payment.
    """
    repo = PaymentRepository(db)
    payment = Payment(
        amount=float(payload.amount),
        currency=payload.currency,
        idempotency_key=payload.idempotency_key,
        debit_account=payload.debit_account,
        credit_account=payload.credit_account,
        description=payload.description,
    )
    saved = repo.create(payment)
    return _payment_to_response(saved)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Retrieve a payment by ID",
)
def get_payment(payment_id: UUID, db: Session = Depends(get_db)) -> PaymentResponse:
    repo = PaymentRepository(db)
    payment = repo.get(str(payment_id))
    if not payment:
        raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")
    return _payment_to_response(payment)


@router.post(
    "/{payment_id}/settle",
    response_model=SettleResponse,
    summary="Settle a payment and write a ledger entry",
)
def settle_payment(payment_id: UUID, db: Session = Depends(get_db)) -> SettleResponse:
    """
    Transitions payment PENDING/AUTHORIZED → SETTLED.
    Writes an immutable ledger entry in the same transaction.
    """
    repo = PaymentRepository(db)
    try:
        payment, entry = repo.settle(str(payment_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SettleResponse(
        payment=_payment_to_response(payment),
        ledger_entry=LedgerEntryResponse(
            id=entry.id,
            payment_id=entry.payment_id,
            debit_account=entry.debit_account,
            credit_account=entry.credit_account,
            amount=entry.amount,
            currency=entry.currency,
            created_at=entry.created_at,
        ),
    )
