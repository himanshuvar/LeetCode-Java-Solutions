from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from gino import Gino, GinoConnection

from app.commons.utils.dataclass_extensions import no_init_field
from app.payin.core.payer.model import Payer, PaymentGatewayProviderCustomer
from app.payin.core.payer.types import PayerType
from app.payin.models.paymentdb.payer import PayerTable


@dataclass
class PayerRepository:
    _gino: Gino
    _table: PayerTable = no_init_field()

    def __post_init__(self):
        self._table = PayerTable(self._gino)

    async def insert_payer(
        self,
        payer_id: str,
        payer_type: str,
        legacy_stripe_customer_id: str,
        country: str,
        account_balance: Optional[int] = None,
        description: Optional[str] = None,
        dd_payer_id: Optional[str] = None,
    ) -> Payer:
        # FIXME: remove when payment db credential is setup
        if True:
            return self._to_mock_payer(
                payer_id=payer_id,
                payer_type=payer_type,
                dd_payer_id=dd_payer_id,
                legacy_stripe_customer_id=legacy_stripe_customer_id,
                country=country,
                account_balance=account_balance,
                description=description,
            )
        else:
            data = {
                self._table.id: payer_id,
                self._table.payer_type: payer_type,
                self._table.legacy_stripe_customer_id: legacy_stripe_customer_id,
                self._table.country: country,
            }
            if account_balance:
                data.update({self._table.account_balance: account_balance})
            if description:
                data.update({self._table.description: description})
            if dd_payer_id:
                data.update({self._table.dd_payer_id: dd_payer_id})
            stmt = (
                self._table.table.insert()
                .values(data)
                .returning(*self._table.table.columns.values())
            )

            async with self._gino.acquire() as connection:  # type: GinoConnection
                row = await connection.first(stmt)
            return self._to_payer(row)

    async def get_payer_by_id(self, payer_id: str) -> Optional[Payer]:
        stmt = self._table.table.select().where(self._table.id == payer_id)
        # FIXME: remove when payment db credential is setup
        if True:
            return self._to_mock_payer(
                payer_id=payer_id,
                payer_type="drive",
                dd_payer_id="1234",
                legacy_stripe_customer_id="mock_legacy_stripe_customer_id",
                country="mock_country",
                account_balance=0,
                description="mock_description",
            )
        else:
            async with self._gino.acquire() as connection:  # type: GinoConnection
                row = await connection.first(stmt)
            return self._to_payer(row) if row else None

    async def get_payer_by_stripe_customer_id(
        self, stripe_customer_id: str
    ) -> Optional[Payer]:
        stmt = self._table.table.select().where(
            self._table.legacy_stripe_customer_id == stripe_customer_id
        )
        # FIXME: remove when payment db credential is setup
        if True:
            return self._to_mock_payer(
                payer_id="mock_payer_id",
                payer_type="drive",
                dd_payer_id="1234",
                legacy_stripe_customer_id=stripe_customer_id,
                country="mock_US",
                account_balance=0,
                description="mock_description",
            )
        else:
            async with self._gino.acquire() as connection:  # type: GinoConnection
                row = await connection.first(stmt)
            return self._to_payer(row) if row else None

    def _to_payer(self, row: Any) -> Payer:
        return Payer(
            payer_id=row[self._table.id],
            payer_type=PayerType(row[self._table.payer_type]),
            dd_payer_id=row[self._table.dd_payer_id],
            payment_gateway_provider_customers=[
                PaymentGatewayProviderCustomer(
                    payment_provider="stripe",
                    payment_provider_customer_id=row[
                        self._table.legacy_stripe_customer_id
                    ],
                )
            ],
            country=row[self._table.country],
            # account_balance=row[self._table.account_balance],
            description=row[self._table.description],
            created_at=row[self._table.created_at],
            updated_at=row[self._table.updated_at],
        )

    # FIXME: remove when payment db credential is setup
    def _to_mock_payer(
        self,
        payer_id: str,
        payer_type: str,
        legacy_stripe_customer_id: str,
        country: str,
        dd_payer_id: Optional[str],
        account_balance: Optional[int],
        description: Optional[str],
    ):
        return Payer(
            payer_id=payer_id,
            payer_type=PayerType(payer_type),
            dd_payer_id=dd_payer_id,
            payment_gateway_provider_customers=[
                PaymentGatewayProviderCustomer(
                    payment_provider="stripe",
                    payment_provider_customer_id=legacy_stripe_customer_id,
                )
            ],
            country=country,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )