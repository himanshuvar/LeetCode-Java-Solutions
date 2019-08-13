import uuid

import pytest
import pytest_mock
from asyncpg import UniqueViolationError

from app.commons.context.app_context import AppContext
from app.commons.database.infra import DB
from app.commons.types import CurrencyType
from app.ledger.core.mx_transaction.types import (
    MxLedgerType,
    MxLedgerStateType,
    MxTransactionType,
)
from app.ledger.repository.mx_ledger_repository import (
    MxLedgerRepository,
    InsertMxLedgerInput,
    UpdateMxLedgerSetInput,
    UpdateMxLedgerWhereInput,
    GetMxLedgerByIdInput,
    GetMxLedgerByAccountInput,
)


class TestMxLedgerRepository:
    pytestmark = [pytest.mark.asyncio]

    async def test_insert_mx_ledger_success(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id="pay_act_test_id",
        )

        mx_ledger = await repo.insert_mx_ledger(mx_ledger_to_insert)
        assert mx_ledger.id == mx_ledger_id
        assert mx_ledger.type == MxLedgerType.MANUAL
        assert mx_ledger.currency == CurrencyType.USD
        assert mx_ledger.state == MxLedgerStateType.OPEN
        assert mx_ledger.balance == 2000
        assert mx_ledger.payment_account_id == "pay_act_test_id"

    async def test_insert_mx_ledger_raise_exception(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id="pay_act_test_id",
        )
        await repo.insert_mx_ledger(mx_ledger_to_insert)

        with pytest.raises(UniqueViolationError):
            await repo.insert_mx_ledger(mx_ledger_to_insert)

    async def test_update_mx_ledger_balance_success(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id="pay_act_test_id",
        )
        mx_ledger = await repo.insert_mx_ledger(mx_ledger_to_insert)

        assert mx_ledger.balance == 2000

        mx_ledger_set_input = UpdateMxLedgerSetInput(balance=3000)
        mx_ledger_where_input = UpdateMxLedgerWhereInput(id=mx_ledger.id)
        updated_mx_ledger = await repo.update_mx_ledger_balance(
            mx_ledger_set_input, mx_ledger_where_input
        )
        assert mx_ledger.id == updated_mx_ledger.id
        assert updated_mx_ledger.balance == 3000

    async def test_get_ledger_by_id_success(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id="pay_act_test_id",
        )
        mx_ledger = await repo.insert_mx_ledger(mx_ledger_to_insert)
        mx_ledger_request = GetMxLedgerByIdInput(id=mx_ledger.id)
        retrieved_mx_ledger = await repo.get_ledger_by_id(mx_ledger_request)

        assert retrieved_mx_ledger is not None
        assert retrieved_mx_ledger.id == mx_ledger.id
        assert retrieved_mx_ledger.type == mx_ledger.type
        assert retrieved_mx_ledger.currency == mx_ledger.currency
        assert retrieved_mx_ledger.state == mx_ledger.state
        assert retrieved_mx_ledger.balance == mx_ledger.balance
        assert retrieved_mx_ledger.payment_account_id == mx_ledger.payment_account_id

    async def test_get_ledger_by_id_not_exist_success(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id="pay_act_test_id",
        )
        await repo.insert_mx_ledger(mx_ledger_to_insert)
        mx_ledger_request = GetMxLedgerByIdInput(id=uuid.uuid4())
        retrieved_mx_ledger = await repo.get_ledger_by_id(mx_ledger_request)

        assert retrieved_mx_ledger is None

    async def test_get_open_ledger_for_payment_account_success(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        payment_account_id = str(uuid.uuid4())
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id=payment_account_id,
        )
        mx_ledger = await repo.insert_mx_ledger(mx_ledger_to_insert)
        mx_ledger_request = GetMxLedgerByAccountInput(
            payment_account_id=payment_account_id
        )
        retrieved_mx_ledger = await repo.get_open_ledger_for_payment_account(
            mx_ledger_request
        )

        assert retrieved_mx_ledger is not None
        assert retrieved_mx_ledger.id == mx_ledger.id
        assert retrieved_mx_ledger.type == mx_ledger.type
        assert retrieved_mx_ledger.currency == mx_ledger.currency
        assert retrieved_mx_ledger.state == mx_ledger.state
        assert retrieved_mx_ledger.balance == mx_ledger.balance
        assert retrieved_mx_ledger.payment_account_id == mx_ledger.payment_account_id

    async def test_get_open_ledger_for_payment_account_no_open_ledger(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        payment_account_id = str(uuid.uuid4())
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.PAID.value,
            balance=2000,
            payment_account_id=payment_account_id,
        )
        await repo.insert_mx_ledger(mx_ledger_to_insert)
        mx_ledger_request = GetMxLedgerByAccountInput(
            payment_account_id=payment_account_id
        )
        retrieved_mx_ledger = await repo.get_open_ledger_for_payment_account(
            mx_ledger_request
        )

        assert retrieved_mx_ledger is None

    async def test_get_open_ledger_for_payment_account_no_account(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        mx_ledger_to_insert = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.PAID.value,
            balance=2000,
            payment_account_id=str(uuid.uuid4()),
        )
        await repo.insert_mx_ledger(mx_ledger_to_insert)
        mx_ledger_request = GetMxLedgerByAccountInput(
            payment_account_id=str(uuid.uuid4())
        )
        retrieved_mx_ledger = await repo.get_open_ledger_for_payment_account(
            mx_ledger_request
        )

        assert retrieved_mx_ledger is None

    async def test_create_one_off_mx_ledger(
        self, mocker: pytest_mock.MockFixture, ledger_paymentdb: DB
    ):
        app_context: AppContext = AppContext(
            log=mocker.Mock(),
            payout_bankdb=mocker.Mock(),
            payin_maindb=mocker.Mock(),
            payin_paymentdb=mocker.Mock(),
            payout_maindb=mocker.Mock(),
            ledger_maindb=mocker.Mock(),
            ledger_paymentdb=ledger_paymentdb,
            stripe=mocker.Mock(),
            dsj_client=mocker.Mock(),
        )
        repo = MxLedgerRepository(context=app_context)
        mx_ledger_id = uuid.uuid4()
        mx_ledger_to_create = InsertMxLedgerInput(
            id=mx_ledger_id,
            type=MxLedgerType.MANUAL.value,
            currency=CurrencyType.USD.value,
            state=MxLedgerStateType.OPEN.value,
            balance=2000,
            payment_account_id="pay_act_test_id",
        )
        one_off_mx_ledger, mx_transaction = await repo.create_one_off_mx_ledger(
            mx_ledger_to_create
        )

        assert one_off_mx_ledger.id == mx_ledger_id
        assert one_off_mx_ledger.type == MxLedgerType.MANUAL
        assert one_off_mx_ledger.currency == CurrencyType.USD
        assert one_off_mx_ledger.state == MxLedgerStateType.OPEN
        assert one_off_mx_ledger.balance == 2000
        assert one_off_mx_ledger.payment_account_id == "pay_act_test_id"

        assert mx_transaction.ledger_id == mx_ledger_id
        assert mx_transaction.amount == 2000
        assert mx_transaction.currency == CurrencyType.USD
        assert mx_transaction.payment_account_id == "pay_act_test_id"
        assert mx_transaction.target_type == MxTransactionType.MICRO_DEPOSIT
