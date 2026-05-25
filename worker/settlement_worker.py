"""
Settlement worker — polls for AUTHORIZED payments and settles them.

In production this would be triggered by a message queue (SQS, Kafka).
For local/demo purposes it polls the DB on a fixed interval.
"""

import logging
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.payment import Payment
from app.repositories.payment_repository import PaymentRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("settlement-worker")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/payments")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)


def process_authorized_payments() -> int:
    settled = 0
    with Session() as db:
        repo = PaymentRepository(db)
        authorized = (
            db.query(Payment).filter(Payment.status == "authorized").all()
        )
        for payment in authorized:
            try:
                repo.settle(payment.id)
                log.info("settled payment %s amount=%s %s", payment.id, payment.amount, payment.currency)
                settled += 1
            except Exception as exc:
                log.error("failed to settle payment %s: %s", payment.id, exc)
    return settled


def run():
    log.info("settlement worker started, polling every %ds", POLL_INTERVAL)
    while True:
        try:
            count = process_authorized_payments()
            if count:
                log.info("processed %d payment(s)", count)
        except Exception as exc:
            log.error("worker loop error: %s", exc)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
