"""create payments and transfer tables

Revision ID: 20260102_01
Revises: 
Create Date: 2026-01-02 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260102_01"
down_revision = None
branch_labels = None
depends_on = None


payment_status_enum = sa.Enum(
    "PENDING",
    "COMPLETED",
    "FAILED",
    "REFUNDED",
    name="payment_status",
)

transfer_status_enum = sa.Enum(
    "CREATED",
    "REQUIRES_PM",
    "REQUIRES_KYC",
    "AUTHORIZED",
    "CAPTURED",
    "FAILED",
    "CANCELLED",
    name="transfer_status",
)

transfer_event_status_enum = sa.Enum(
    "CREATED",
    "REQUIRES_PM",
    "REQUIRES_KYC",
    "AUTHORIZED",
    "CAPTURED",
    "FAILED",
    "CANCELLED",
    name="transfer_event_status",
)


def upgrade() -> None:
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    transfer_status_enum.create(op.get_bind(), checkfirst=True)
    transfer_event_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", payment_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
    )

    op.create_table(
        "transfers",
        sa.Column("id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("origin_id", sa.String(length=64), nullable=False),
        sa.Column("status", transfer_status_enum, nullable=False, server_default="CREATED"),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("concept", sa.String(length=32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("connector_id", sa.String(length=64), nullable=True),
        sa.Column("source_address", sa.String(length=64), nullable=False),
        sa.Column("source_address_type", sa.String(length=32), nullable=False),
        sa.Column("source_owner_id_type", sa.String(length=16), nullable=False),
        sa.Column("source_owner_id", sa.String(length=32), nullable=False),
        sa.Column("source_owner_name", sa.String(length=128), nullable=True),
        sa.Column("destination_address", sa.String(length=64), nullable=False),
        sa.Column("destination_address_type", sa.String(length=32), nullable=False),
        sa.Column("destination_owner_id_type", sa.String(length=16), nullable=False),
        sa.Column("destination_owner_id", sa.String(length=32), nullable=False),
        sa.Column("destination_owner_name", sa.String(length=128), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("connector_response", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
    )
    op.create_index("ix_transfers_origin_id", "transfers", ["origin_id"], unique=True)

    op.create_table(
        "transfer_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("transfer_id", sa.BigInteger(), sa.ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", transfer_event_status_enum, nullable=False),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
    )
    op.create_index("ix_transfer_events_transfer_id_created", "transfer_events", ["transfer_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transfer_events_transfer_id_created", table_name="transfer_events")
    op.drop_table("transfer_events")

    op.drop_index("ix_transfers_origin_id", table_name="transfers")
    op.drop_table("transfers")

    op.drop_table("payments")

    transfer_event_status_enum.drop(op.get_bind(), checkfirst=True)
    transfer_status_enum.drop(op.get_bind(), checkfirst=True)
    payment_status_enum.drop(op.get_bind(), checkfirst=True)
