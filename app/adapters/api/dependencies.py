from typing import Optional

from app.adapters.db.memory_transfer_repository import InMemoryTransferRepository
from app.core.connectors.banco_comercio import BancoComercioConnector
from app.core.connectors.interface import ConnectorIntegration
from app.core.connectors.mock_banco_comercio import MockBancoComercioConnector
from app.core.payments.operation import PaymentOperation
from app.services.payment_service import PaymentService
from config.settings import settings

# Stub for dependency injection. 
# This will be overridden in main.py but serves as the dependency token.
async def get_payment_service() -> PaymentService:
    raise NotImplementedError("Dependency not explicitly overridden")


_transfer_repository = InMemoryTransferRepository()


def get_payment_operation() -> PaymentOperation:
    return PaymentOperation(transfer_repository=_transfer_repository)

_connector_instance: Optional[ConnectorIntegration] = None


def _build_connector() -> ConnectorIntegration:
    mode = settings.transfer_connector_mode.lower()
    if mode == "mock":
        return MockBancoComercioConnector()
    if mode in {"banco_comercio", "live", "prod"}:
        return BancoComercioConnector()
    raise ValueError(f"Unsupported transfer connector mode: {settings.transfer_connector_mode}")


def get_transfer_connector() -> ConnectorIntegration:
    global _connector_instance
    if _connector_instance is None:
        _connector_instance = _build_connector()
    return _connector_instance


def get_banco_comercio_connector() -> ConnectorIntegration:
    return get_transfer_connector()
