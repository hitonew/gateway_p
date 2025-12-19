from fastapi import FastAPI
from app.api_server.routers import payments, kyc
from config.settings import settings

app = FastAPI(title="Pagoflex Modular Platform", version="2.0.0")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api_server"}

# Include Routers
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(kyc.router, prefix="/kyc", tags=["kyc"])
