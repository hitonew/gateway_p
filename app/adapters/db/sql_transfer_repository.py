from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.payments.types import (
    PaymentData,
    TransferBody,
    TransferParty,
    TransferPartyOwner,
)
from app.db.models import PaymentRecord, TransferEventRecord, TransferRecord
from app.domain.models import PaymentStatus
from app.ports.transfer_repository import TransferRepository


class SqlAlchemyTransferRepository(TransferRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, data: PaymentData) -> PaymentData:
        payment_record = await self._ensure_payment_record(data)
        record = await self._get_transfer_by_payment_id(data.payment_id)

        transfer_body = data.transfer_body
        if transfer_body is None:
            raise ValueError("Transfer body is required to persist transfer data")
        if data.source is None or data.destination is None:
            raise ValueError("Transfer source and destination are required")

        metadata_copy = deepcopy(data.metadata or {})
        connector_response = deepcopy(metadata_copy.get("connector_response", {}))

        if record is None:
            record = TransferRecord(
                payment=payment_record,
                payment_id=payment_record.id,
                origin_id=data.origin_id,
                status=data.status,
                amount=Decimal(str(data.amount)),
                currency=data.currency,
                concept=transfer_body.concept,
                description=data.description or transfer_body.description,
                connector_id=data.connector_id,
                source_address=data.source.address,
                source_address_type=data.source.address_type,
                source_owner_id_type=data.source.owner.person_id_type,
                source_owner_id=data.source.owner.person_id,
                source_owner_name=data.source.owner.person_name,
                destination_address=data.destination.address,
                destination_address_type=data.destination.address_type,
                destination_owner_id_type=data.destination.owner.person_id_type,
                destination_owner_id=data.destination.owner.person_id,
                destination_owner_name=data.destination.owner.person_name,
                metadata=metadata_copy,
                connector_response=connector_response,
            )
            self.session.add(record)
        else:
            record.status = data.status
            record.amount = Decimal(str(data.amount))
            record.currency = data.currency
            record.concept = transfer_body.concept
            record.description = data.description or transfer_body.description
            record.connector_id = data.connector_id
            record.source_address = data.source.address
            record.source_address_type = data.source.address_type
            record.source_owner_id_type = data.source.owner.person_id_type
            record.source_owner_id = data.source.owner.person_id
            record.source_owner_name = data.source.owner.person_name
            record.destination_address = data.destination.address
            record.destination_address_type = data.destination.address_type
            record.destination_owner_id_type = data.destination.owner.person_id_type
            record.destination_owner_id = data.destination.owner.person_id
            record.destination_owner_name = data.destination.owner.person_name
            record.metadata = metadata_copy
            record.connector_response = connector_response
            record.updated_at = datetime.now(timezone.utc)

        event = TransferEventRecord(
            transfer=record,
            status=data.status,
            message=metadata_copy.get("error_message"),
            payload={
                "status": data.status.value,
                "metadata": metadata_copy,
                "connector_response": connector_response,
            },
        )
        self.session.add(event)

        await self.session.flush()
        # Reload to ensure relationships are present and defaults applied
        record = await self._get_transfer_by_payment_id(data.payment_id)
        if record is None:
            raise RuntimeError("Failed to persist transfer data")

        return self._to_payment_data(record)

    async def get_by_origin_id(self, origin_id: str) -> Optional[PaymentData]:
        record = await self._get_transfer_by_origin(origin_id)
        if record is None:
            return None
        return self._to_payment_data(record)

    async def get_by_payment_id(self, payment_id: UUID) -> Optional[PaymentData]:
        record = await self._get_transfer_by_payment_id(payment_id)
        if record is None:
            return None
        return self._to_payment_data(record)

    async def _ensure_payment_record(self, data: PaymentData) -> PaymentRecord:
        payment_record = await self.session.get(PaymentRecord, data.payment_id)
        if payment_record is None:
            payment_record = PaymentRecord(
                id=data.payment_id,
                amount=Decimal(str(data.amount)),
                currency=data.currency,
                status=PaymentStatus.PENDING,
                description=data.description,
                metadata=deepcopy(data.metadata or {}),
            )
            self.session.add(payment_record)
            await self.session.flush()
            await self.session.refresh(payment_record)
        return payment_record

    async def _get_transfer_by_origin(self, origin_id: str) -> Optional[TransferRecord]:
        stmt = (
            select(TransferRecord)
            .options(selectinload(TransferRecord.payment))
            .where(TransferRecord.origin_id == origin_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_transfer_by_payment_id(self, payment_id: UUID) -> Optional[TransferRecord]:
        stmt = (
            select(TransferRecord)
            .options(selectinload(TransferRecord.payment))
            .where(TransferRecord.payment_id == payment_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _to_payment_data(self, record: TransferRecord) -> PaymentData:
        payment_record = record.payment
        if payment_record is None:
            raise ValueError("Transfer record is missing related payment")

        source_owner = TransferPartyOwner(
            personIdType=record.source_owner_id_type,
            personId=record.source_owner_id,
            personName=record.source_owner_name,
        )
        destination_owner = TransferPartyOwner(
            personIdType=record.destination_owner_id_type,
            personId=record.destination_owner_id,
            personName=record.destination_owner_name,
        )

        source = TransferParty(
            addressType=record.source_address_type,
            address=record.source_address,
            owner=source_owner,
        )
        destination = TransferParty(
            addressType=record.destination_address_type,
            address=record.destination_address,
            owner=destination_owner,
        )

        body = TransferBody(
            amount=Decimal(record.amount),
            currency=record.currency,
            description=record.description,
            concept=record.concept,
        )

        metadata_copy = deepcopy(record.metadata or {})
        metadata_copy["connector_response"] = deepcopy(record.connector_response or {})

        return PaymentData(
            payment_id=payment_record.id,
            origin_id=record.origin_id,
            amount=Decimal(record.amount),
            currency=record.currency,
            description=payment_record.description or record.description,
            status=record.status,
            connector_id=record.connector_id,
            metadata=metadata_copy,
            source=source,
            destination=destination,
            body=body,
            created_at=record.created_at,
        )
