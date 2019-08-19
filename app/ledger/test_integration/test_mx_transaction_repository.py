import uuid
from datetime import datetime

import pytest
from asyncpg import UniqueViolationError
from pytest_mock import MockFixture

from app.commons.context.app_context import AppContext
from app.commons.database.infra import DB
from app.commons.types import CurrencyType
from app.ledger.core.mx_transaction.data_types import (
    InsertMxTransactionWithLedgerInput,
    GetMxLedgerByIdInput,
    InsertMxScheduledLedgerInput,
    GetMxScheduledLedgerInput,
)
from app.ledger.core.mx_transaction.types import (
    MxTransactionType,
    MxLedgerType,
    MxLedgerStateType,
    MxScheduledLedgerIntervalType,
)
from app.ledger.repository.mx_ledger_repository import (
    MxLedgerRepository,
    InsertMxLedgerInput,
)
from app.ledger.repository.mx_scheduled_ledger_repository import (
    MxScheduledLedgerRepository,
)
from app.ledger.repository.mx_transaction_repository import (
    MxTransactionRepository,
    InsertMxTransactionInput,
)


class TestMxTransactionRepository:
    pytestmark = [pytest.mark.asyncio]

    async def test_insert_mx_transaction_success(
        self, ledger_app_context: AppContext, ledger_paymentdb: DB
    ):
        repo = MxTransactionRepository(context=ledger_app_context)
        ledger_repo = MxLedgerRepository(context=ledger_app_context)
        mx_ledger_id = uuid.uuid4()
        mx_transaction_id = uuid.uuid4()
        ide_key = str(uuid.uuid4())
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id="pay_act_test_id",
        )

        mx_transaction_to_insert = InsertMxTransactionInput(
            id=mx_transaction_id,
            payment_account_id="pay_act_test_id",
            amount=2000,
            currency=CurrencyType.USD.value,
            ledger_id=mx_ledger_id,
            idempotency_key=ide_key,
            target_type=MxTransactionType.MERCHANT_DELIVERY.value,
            routing_key=datetime.utcnow(),
        )
        await ledger_repo.insert_mx_ledger(mx_ledger_to_insert)
        mx_transaction = await repo.insert_mx_transaction(mx_transaction_to_insert)
        assert mx_transaction.id == mx_transaction_id
        assert mx_transaction.target_type == MxTransactionType.MERCHANT_DELIVERY
        assert mx_transaction.currency == CurrencyType.USD
        assert mx_transaction.ledger_id == mx_ledger_id
        assert mx_transaction.amount == 2000
        assert mx_transaction.payment_account_id == "pay_act_test_id"
        assert mx_transaction.idempotency_key == ide_key

    async def test_insert_mx_transaction_raise_exception(
        self, ledger_app_context: AppContext, ledger_paymentdb: DB
    ):
        repo = MxTransactionRepository(context=ledger_app_context)
        ledger_repo = MxLedgerRepository(context=ledger_app_context)
        mx_ledger_id = uuid.uuid4()
        mx_transaction_id = uuid.uuid4()
        ide_key = str(uuid.uuid4())
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id="pay_act_test_id",
        )

        mx_transaction_to_insert = InsertMxTransactionInput(
            id=mx_transaction_id,
            payment_account_id="pay_act_test_id",
            amount=2000,
            currency=CurrencyType.USD.value,
            ledger_id=mx_ledger_id,
            idempotency_key=ide_key,
            target_type=MxTransactionType.MERCHANT_DELIVERY.value,
            routing_key=datetime.utcnow(),
        )
        await ledger_repo.insert_mx_ledger(mx_ledger_to_insert)
        await repo.insert_mx_transaction(mx_transaction_to_insert)

        with pytest.raises(UniqueViolationError):
            await repo.insert_mx_transaction(mx_transaction_to_insert)

    async def test_create_ledger_and_insert_mx_transaction_success(
        self, mocker: MockFixture, ledger_app_context: AppContext, ledger_paymentdb: DB
    ):
        mx_txn_repo = MxTransactionRepository(context=ledger_app_context)
        ledger_repo = MxLedgerRepository(context=ledger_app_context)
        mx_scheduled_ledger_repo = MxScheduledLedgerRepository(
            context=ledger_app_context
        )

        payment_account_id = str(uuid.uuid4())
        routing_key = datetime(2019, 8, 1)
        request_input = InsertMxTransactionWithLedgerInput(
            currency=CurrencyType.USD,
            amount=2000,
            type=MxLedgerType.SCHEDULED,
            payment_account_id=payment_account_id,
            interval_type=MxScheduledLedgerIntervalType.WEEKLY,
            routing_key=routing_key,
            idempotency_key=str(uuid.uuid4()),
            target_type=MxTransactionType.MERCHANT_DELIVERY,
        )

        mx_transaction = await mx_txn_repo.create_ledger_and_insert_mx_transaction(
            request_input, mx_scheduled_ledger_repo, req_context=mocker.Mock()
        )
        assert mx_transaction is not None
        assert mx_transaction.currency == CurrencyType.USD
        assert mx_transaction.amount == 2000
        assert mx_transaction.payment_account_id == payment_account_id
        assert mx_transaction.routing_key == datetime(2019, 8, 1)
        assert mx_transaction.target_type == MxTransactionType.MERCHANT_DELIVERY

        get_scheduled_ledger_request = GetMxScheduledLedgerInput(
            payment_account_id=payment_account_id,
            routing_key=routing_key,
            interval_type=MxScheduledLedgerIntervalType.WEEKLY,
        )
        mx_scheduled_ledger = await mx_scheduled_ledger_repo.get_open_mx_scheduled_ledger_for_period(
            get_scheduled_ledger_request
        )
        assert mx_scheduled_ledger is not None
        assert mx_scheduled_ledger.ledger_id == mx_transaction.ledger_id

        get_mx_ledger_request = GetMxLedgerByIdInput(id=mx_transaction.ledger_id)
        mx_ledger = await ledger_repo.get_ledger_by_id(get_mx_ledger_request)
        assert mx_ledger is not None
        assert mx_ledger.balance == 2000

    async def test_create_ledger_and_insert_mx_transaction_raise_exception(
        self, mocker: MockFixture, ledger_app_context: AppContext, ledger_paymentdb: DB
    ):
        mx_txn_repo = MxTransactionRepository(context=ledger_app_context)
        ledger_repo = MxLedgerRepository(context=ledger_app_context)
        mx_scheduled_ledger_repo = MxScheduledLedgerRepository(
            context=ledger_app_context
        )

        # test roll back created_mx_ledger if insert mx_scheduled_ledger failed due to duplicate [payment_account_id, start_time, end_time]
        payment_account_id = str(uuid.uuid4())
        routing_key = datetime(2019, 8, 1)
        interval_type = MxScheduledLedgerIntervalType.WEEKLY

        ledger_request = InsertMxLedgerInput(
            id=uuid.uuid4(),
            payment_account_id=payment_account_id,
            currency=CurrencyType.USD,
            type=MxLedgerType.SCHEDULED,
            balance=2000,
            state=MxLedgerStateType.OPEN,
        )
        mx_ledger = await ledger_repo.insert_mx_ledger(ledger_request)

        scheduled_ledger_request = InsertMxScheduledLedgerInput(
            id=uuid.uuid4(),
            payment_account_id=payment_account_id,
            ledger_id=mx_ledger.id,
            interval_type=interval_type,
            start_time=mx_scheduled_ledger_repo.pacific_start_time_for_current_interval(
                routing_key, interval_type
            ),
            end_time=mx_scheduled_ledger_repo.pacific_end_time_for_current_interval(
                routing_key, interval_type
            ),
        )
        await mx_scheduled_ledger_repo.insert_mx_scheduled_ledger(
            scheduled_ledger_request
        )

        request_input = InsertMxTransactionWithLedgerInput(
            currency=CurrencyType.USD,
            amount=2000,
            type=MxLedgerType.SCHEDULED,
            payment_account_id=payment_account_id,
            interval_type=MxScheduledLedgerIntervalType.WEEKLY,
            routing_key=datetime(2019, 8, 1),
            idempotency_key=str(uuid.uuid4()),
            target_type=MxTransactionType.MERCHANT_DELIVERY,
        )

        with pytest.raises(Exception):
            await mx_txn_repo.create_ledger_and_insert_mx_transaction(
                request_input, mx_scheduled_ledger_repo, req_context=mocker.Mock()
            )
            # the mx_ledger created before should be rolled back
            get_ledger_request = GetMxLedgerByIdInput(id=mx_ledger.id)
            mx_ledger_retrieved = await ledger_repo.get_ledger_by_id(get_ledger_request)
            assert mx_ledger_retrieved is None

    async def test_insert_mx_transaction_and_update_ledger_success(
        self, mocker: MockFixture, ledger_app_context: AppContext, ledger_paymentdb: DB
    ):
        mx_txn_repo = MxTransactionRepository(context=ledger_app_context)
        ledger_repo = MxLedgerRepository(context=ledger_app_context)

        # create a new mx_ledger which needs to be updated later
        payment_account_id = str(uuid.uuid4())
        ledger_request = InsertMxLedgerInput(
            id=uuid.uuid4(),
            payment_account_id=payment_account_id,
            currency=CurrencyType.USD,
            type=MxLedgerType.SCHEDULED,
            balance=2000,
            state=MxLedgerStateType.OPEN,
        )
        mx_ledger = await ledger_repo.insert_mx_ledger(ledger_request)

        request_input = InsertMxTransactionWithLedgerInput(
            currency=CurrencyType.USD,
            amount=2000,
            type=MxLedgerType.SCHEDULED,
            payment_account_id=payment_account_id,
            interval_type=MxScheduledLedgerIntervalType.WEEKLY,
            routing_key=datetime(2019, 8, 1),
            idempotency_key=str(uuid.uuid4()),
            target_type=MxTransactionType.MERCHANT_DELIVERY,
        )

        mx_transaction = await mx_txn_repo.insert_mx_transaction_and_update_ledger(
            request_input, ledger_repo, mx_ledger.id, req_context=mocker.Mock()
        )
        assert mx_transaction is not None
        assert mx_transaction.currency == CurrencyType.USD
        assert mx_transaction.amount == 2000
        assert mx_transaction.payment_account_id == payment_account_id
        assert mx_transaction.routing_key == datetime(2019, 8, 1)
        assert mx_transaction.target_type == MxTransactionType.MERCHANT_DELIVERY

        get_mx_ledger_request = GetMxLedgerByIdInput(id=mx_transaction.ledger_id)
        mx_ledger_retrieved = await ledger_repo.get_ledger_by_id(get_mx_ledger_request)
        assert mx_ledger_retrieved is not None
        assert mx_ledger_retrieved.balance == 4000

    async def test_insert_mx_transaction_and_update_ledger_raise_exception(
        self, mocker: MockFixture, ledger_app_context: AppContext, ledger_paymentdb: DB
    ):
        mx_txn_repo = MxTransactionRepository(context=ledger_app_context)
        ledger_repo = MxLedgerRepository(context=ledger_app_context)

        # test roll back created_mx_ledger if insert mx_txn failed due to duplicate [payment_account_id, idempotency_key]
        payment_account_id = str(uuid.uuid4())
        idempotency_key = str(uuid.uuid4())
        mx_ledger_id = uuid.uuid4()
        ledger_request = InsertMxLedgerInput(
            id=mx_ledger_id,
            payment_account_id=payment_account_id,
            currency=CurrencyType.USD,
            type=MxLedgerType.SCHEDULED,
            balance=2000,
            state=MxLedgerStateType.OPEN,
        )
        await ledger_repo.insert_mx_ledger(ledger_request)

        insert_txn_request = InsertMxTransactionInput(
            id=uuid.uuid4(),
            payment_account_id=payment_account_id,
            amount=2000,
            currency=CurrencyType.USD,
            ledger_id=mx_ledger_id,
            idempotency_key=idempotency_key,
            target_type=MxTransactionType.MERCHANT_DELIVERY,
            routing_key=datetime(2019, 8, 1),
        )
        await mx_txn_repo.insert_mx_transaction(insert_txn_request)

        request_input = InsertMxTransactionWithLedgerInput(
            currency=CurrencyType.USD,
            amount=2000,
            type=MxLedgerType.SCHEDULED,
            payment_account_id=payment_account_id,
            interval_type=MxScheduledLedgerIntervalType.WEEKLY,
            routing_key=datetime(2019, 8, 1),
            idempotency_key=str(uuid.uuid4()),
            target_type=MxTransactionType.MERCHANT_DELIVERY,
        )
        with pytest.raises(Exception):
            await mx_txn_repo.insert_mx_transaction_and_update_ledger(
                request_input, ledger_repo, mx_ledger_id, req_context=mocker.Mock()
            )
            # the mx_ledger that needs to be updated should not be updated
            get_ledger_request = GetMxLedgerByIdInput(id=mx_ledger_id)
            mx_ledger_retrieved = await ledger_repo.get_ledger_by_id(get_ledger_request)
            assert mx_ledger_retrieved is not None
            assert mx_ledger_retrieved.balance == 2000