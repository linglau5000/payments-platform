from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PaymentStatus(str, Enum):
    pending = "pending"
    authorized = "authorized"
    settled = "settled"
    failed = "failed"


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Payment amount, must be positive")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    idempotency_key: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    debit_account: str = Field(..., description="Account to debit")
    credit_account: str = Field(..., description="Account to credit")

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("amount")
    @classmethod
    def amount_two_decimals(cls, v: Decimal) -> Decimal:
        return round(v, 2)


class PaymentResponse(BaseModel):
    id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    idempotency_key: str
    description: Optional[str]
    debit_account: str
    credit_account: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LedgerEntryResponse(BaseModel):
    id: UUID
    payment_id: UUID
    debit_account: str
    credit_account: str
    amount: Decimal
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SettleResponse(BaseModel):
    payment: PaymentResponse
    ledger_entry: LedgerEntryResponse
