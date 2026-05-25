# Payments Platform

A bank-style payments platform built on AWS + Kubernetes.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client / API Gateway                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Payments API                          │
│  POST /payments   GET /payments/{id}   POST /payments/{id}/settle│
│                      GET /healthz                                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐
│  PostgreSQL DB  │  │ Settlement Worker │  │  Audit Logger  │
│  - payments     │  │  (async worker)  │  │  (AuditEvent)  │
│  - ledger_entries│  └──────────────────┘  └────────────────┘
└─────────────────┘

Infrastructure:
  AWS EKS (Kubernetes) ← Helm charts ← GitHub Actions CI/CD
  Terraform: VPC, EKS, ECR, IAM, Secrets Manager
  Monitoring: CloudWatch + Prometheus
```

## Payment Lifecycle

```
PENDING → AUTHORIZED → SETTLED
                  └──→ FAILED
```

## Idempotency

Every `POST /payments` requires a unique `idempotency_key`. Duplicate keys
return the existing payment — no double charges.

## Ledger

`ledger_entries` are **immutable** — never updated or deleted. Each settlement
writes a new debit/credit pair. This guarantees a complete financial audit trail.

## Project Structure

```
payments-platform/
├── .claude/
│   ├── instructions/   # Claude engineering standards
│   ├── skills/         # Claude reusable skill prompts
│   └── memory/         # Claude architecture context
├── app/
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic request/response schemas
│   ├── routers/        # FastAPI route handlers
│   └── repositories/  # Database access layer
├── charts/             # Helm charts
├── infra/              # Terraform (VPC, EKS, ECR, IAM)
├── k8s/                # Raw Kubernetes manifests
├── tests/              # Pytest test suite
└── .github/workflows/  # GitHub Actions CI/CD
```

## Tech Stack

| Area | Tool |
|------|------|
| AI Engineering | Claude Code |
| Backend | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy + Alembic |
| Containers | Docker |
| Kubernetes | EKS + Minikube |
| K8s Packaging | Helm |
| IaC | Terraform |
| Cloud | AWS |
| Registry | Amazon ECR |
| Secrets | AWS Secrets Manager |
| CI/CD | GitHub Actions |
| Monitoring | CloudWatch + Prometheus |

## Quick Start (Local)

```bash
# Start full stack
docker compose up

# API available at
http://localhost:8000

# Create a payment
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.00, "currency": "USD", "idempotency_key": "pay-001", "description": "Test payment"}'
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
