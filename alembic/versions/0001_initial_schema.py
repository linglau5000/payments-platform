"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-05-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("debit_account", sa.String(255), nullable=False),
        sa.Column("credit_account", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_payments_idempotency_key", "payments", ["idempotency_key"])

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "payment_id",
            sa.String(36),
            sa.ForeignKey("payments.id"),
            nullable=False,
        ),
        sa.Column("debit_account", sa.String(255), nullable=False),
        sa.Column("credit_account", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_ledger_entries_payment_id", "ledger_entries", ["payment_id"])


def downgrade() -> None:
    op.drop_table("ledger_entries")
    op.drop_table("payments")
