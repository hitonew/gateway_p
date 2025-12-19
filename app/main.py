from fastapi import FastAPI, Depends
from app.adapters.api.routes import router as payment_router
from app.services.payment_service import PaymentService
from app.adapters.db.memory_repository import InMemoryPaymentRepository
from app.adapters.payment.mock_gateway import MockPaymentGateway

app = FastAPI(
    title="Pagoflex Middleware",
    description="Payment Gateway API",
    version="0.1.0",
)

from app.adapters.api.dependencies import get_payment_service

# Dependency Injection Setup
# In a real app, use a DI container or proper FastAPI Depends patterns with state
# Singleton instances for simplicity
repository = InMemoryPaymentRepository()
gateway = MockPaymentGateway()

def get_payment_service_impl():
    return PaymentService(repository, gateway)

# Override the dependency in the router
app.dependency_overrides[get_payment_service] = get_payment_service_impl

app.include_router(payment_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
