from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.payments.types import PaymentState
from app.db.base import Base
from app.domain.models import PaymentStatus


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentRecord(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(String(255))
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    transfer: Mapped[Optional["TransferRecord"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
        uselist=False,
    )


class TransferRecord(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    origin_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[PaymentState] = mapped_column(
        Enum(PaymentState, name="transfer_status"),
        default=PaymentState.CREATED,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    concept: Mapped[Optional[str]] = mapped_column(String(32))
    description: Mapped[Optional[str]] = mapped_column(Text())
    connector_id: Mapped[Optional[str]] = mapped_column(String(64))
    source_address: Mapped[str] = mapped_column(String(64), nullable=False)
    source_address_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_owner_id_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_owner_id: Mapped[str] = mapped_column(String(32), nullable=False)
    source_owner_name: Mapped[Optional[str]] = mapped_column(String(128))
    destination_address: Mapped[str] = mapped_column(String(64), nullable=False)
    destination_address_type: Mapped[str] = mapped_column(String(32), nullable=False)
    destination_owner_id_type: Mapped[str] = mapped_column(String(16), nullable=False)
    destination_owner_id: Mapped[str] = mapped_column(String(32), nullable=False)
    destination_owner_name: Mapped[Optional[str]] = mapped_column(String(128))
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    connector_response: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    payment: Mapped[PaymentRecord] = relationship(back_populates="transfer")
    events: Mapped[list["TransferEventRecord"]] = relationship(
        back_populates="transfer",
        cascade="all, delete-orphan",
        order_by="TransferEventRecord.created_at",
    )


class TransferEventRecord(Base):
    __tablename__ = "transfer_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transfer_id: Mapped[int] = mapped_column(
        ForeignKey("transfers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[PaymentState] = mapped_column(
        Enum(PaymentState, name="transfer_event_status"),
        nullable=False,
    )
    message: Mapped[Optional[str]] = mapped_column(String(255))
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    transfer: Mapped[TransferRecord] = relationship(back_populates="events")
