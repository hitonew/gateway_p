from fastapi import Depends, FastAPI

from app.adapters.api.dependencies import (
    get_payment_operation,
    get_payment_service,
)
from app.adapters.api.routes import router as payment_router
from app.adapters.db.memory_repository import InMemoryPaymentRepository
from app.adapters.db.memory_transfer_repository import InMemoryTransferRepository
from app.adapters.db.sql_payment_repository import SqlAlchemyPaymentRepository
from app.adapters.db.sql_transfer_repository import SqlAlchemyTransferRepository
from app.adapters.payment.mock_gateway import MockPaymentGateway
from app.core.payments.operation import PaymentOperation
from app.db.session import get_db_session
from app.services.payment_service import PaymentService
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings

app = FastAPI(
    title="Pagoflex Middleware",
    description="Payment Gateway API",
    version="0.1.0",
)

gateway = MockPaymentGateway()


if settings.persistence_backend.lower() == "memory":
    # Fallback mode for tests or local development without Postgres
    _payment_repository = InMemoryPaymentRepository()
    _transfer_repository = InMemoryTransferRepository()

    def get_payment_service_impl() -> PaymentService:
        return PaymentService(_payment_repository, gateway)

    def get_payment_operation_impl() -> PaymentOperation:
        return PaymentOperation(transfer_repository=_transfer_repository)

else:

    async def get_payment_service_impl(
        session: AsyncSession = Depends(get_db_session),
    ) -> PaymentService:
        repository = SqlAlchemyPaymentRepository(session)
        return PaymentService(repository, gateway)

    async def get_payment_operation_impl(
        session: AsyncSession = Depends(get_db_session),
    ) -> PaymentOperation:
        repository = SqlAlchemyTransferRepository(session)
        return PaymentOperation(transfer_repository=repository)

# Override dependency tokens
app.dependency_overrides[get_payment_service] = get_payment_service_impl
app.dependency_overrides[get_payment_operation] = get_payment_operation_impl

app.include_router(payment_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
