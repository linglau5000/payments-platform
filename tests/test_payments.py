"""
Payments API tests — use SQLite in-memory DB for isolation (no live Postgres needed).
The DB-backed router is tested end-to-end via a real SQLAlchemy session.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLITE_URL = "sqlite:///./test.db"

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

PAYMENT_PAYLOAD = {
    "amount": "100.00",
    "currency": "USD",
    "idempotency_key": "test-key-001",
    "description": "Test payment",
    "debit_account": "ACC-DEBIT-001",
    "credit_account": "ACC-CREDIT-001",
}


def test_health_check():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_payment():
    r = client.post("/payments", json=PAYMENT_PAYLOAD)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending"
    assert float(data["amount"]) == 100.0
    assert data["currency"] == "USD"
    assert data["idempotency_key"] == "test-key-001"


def test_idempotency_returns_same_payment():
    r1 = client.post("/payments", json=PAYMENT_PAYLOAD)
    r2 = client.post("/payments", json=PAYMENT_PAYLOAD)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


def test_get_payment():
    create = client.post("/payments", json=PAYMENT_PAYLOAD)
    payment_id = create.json()["id"]

    r = client.get(f"/payments/{payment_id}")
    assert r.status_code == 200
    assert r.json()["id"] == payment_id


def test_get_payment_not_found():
    r = client.get("/payments/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_settle_payment():
    create = client.post("/payments", json=PAYMENT_PAYLOAD)
    payment_id = create.json()["id"]

    r = client.post(f"/payments/{payment_id}/settle")
    assert r.status_code == 200
    data = r.json()
    assert data["payment"]["status"] == "settled"
    assert data["ledger_entry"]["payment_id"] == payment_id
    assert float(data["ledger_entry"]["amount"]) == 100.0


def test_settle_already_settled():
    create = client.post("/payments", json=PAYMENT_PAYLOAD)
    payment_id = create.json()["id"]
    client.post(f"/payments/{payment_id}/settle")

    r = client.post(f"/payments/{payment_id}/settle")
    assert r.status_code == 400
    assert "already settled" in r.json()["detail"]


def test_settle_not_found():
    r = client.post("/payments/00000000-0000-0000-0000-000000000000/settle")
    assert r.status_code == 400
