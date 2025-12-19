from fastapi import Depends
from app.services.payment_service import PaymentService

# Stub for dependency injection. 
# This will be overridden in main.py but serves as the dependency token.
async def get_payment_service() -> PaymentService:
    raise NotImplementedError("Dependency not explicitly overridden")
