from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.ledger.core.mx_transaction.types import (
    MxTransactionType,
    MxScheduledLedgerIntervalType,
)


class CreateMxTransactionRequest(BaseModel):
    payment_account_id: str
    target_type: MxTransactionType
    amount: str
    currency: str
    idempotency_key: str
    routing_key: datetime
    interval_type: MxScheduledLedgerIntervalType
    target_id: Optional[str]
    context: Optional[str]
    metadata: Optional[str]
    legacy_transaction_id: Optional[str]


# https://pydantic-docs.helpmanual.io/#self-referencing-models
CreateMxTransactionRequest.update_forward_refs()