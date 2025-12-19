from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID
from app.domain.models import Payment
from app.services.payment_service import PaymentService
from app.adapters.api.dependencies import get_payment_service

router = APIRouter()

class CreatePaymentRequest(BaseModel):
    amount: float
    currency: str

@router.post("/payments", response_model=Payment)
async def create_payment(
    request: CreatePaymentRequest,
    service: PaymentService = Depends(get_payment_service), 
):
    return await service.create_payment(request.amount, request.currency)

@router.post("/payments/{payment_id}/process", response_model=Payment)
async def process_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
):
    payment = await service.process_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.get("/payments/{payment_id}", response_model=Payment)
async def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
):
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
