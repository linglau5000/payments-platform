from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routers import payments

app = FastAPI(
    title="Payments Platform",
    description="Bank-style payments API with idempotency, immutable ledger, and settlement lifecycle.",
    version="0.1.0",
)

app.include_router(payments.router)


@app.get("/healthz", tags=["ops"], summary="Health check")
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})
