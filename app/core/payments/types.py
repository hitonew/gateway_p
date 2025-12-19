from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class PaymentState(str, Enum):
    CREATED = "CREATED"
    REQUIRES_PM = "REQUIRES_PM"
    REQUIRES_KYC = "REQUIRES_KYC"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaymentData(BaseModel):
    payment_id: UUID
    amount: int
    currency: str
    customer_id: Optional[str] = None
    description: Optional[str] = None
    status: PaymentState = PaymentState.CREATED
    connector_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ConnectorResponse(BaseModel):
    status: PaymentState
    provider_reference_id: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)
