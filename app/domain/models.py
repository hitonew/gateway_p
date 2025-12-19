from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class Payment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    amount: float
    currency: str
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
