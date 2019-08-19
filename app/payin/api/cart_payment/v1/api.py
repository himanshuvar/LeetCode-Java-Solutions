from fastapi import APIRouter

from app.commons.context.req_context import get_context_from_req
from app.commons.context.app_context import get_context_from_app
from app.commons.error.errors import PaymentError, PaymentException
from app.payin.api.cart_payment.v1.request import (
    CreateCartPaymentRequest,
    UpdateCartPaymentRequest,
)
from app.payin.core.exceptions import PayinErrorCode
from app.payin.core.cart_payment.processor import submit_payment, update_payment
from app.payin.core.cart_payment.model import (
    CartPayment,
    CartMetadata,
    CartType,
    SplitPayment,
    LegacyPayment,
)
from app.payin.repository.cart_payment_repo import CartPaymentRepository
from app.payin.repository.payer_repo import PayerRepository
from app.payin.repository.payment_method_repo import PaymentMethodRepository

from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from starlette.requests import Request
from typing import Optional
from uuid import UUID


def create_cart_payments_router(
    cart_payment_repo: CartPaymentRepository,
    payer_repo: PayerRepository,
    payment_method_repo: PaymentMethodRepository,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/cart_payments", status_code=HTTP_201_CREATED)
    async def create_cart_payment(
        cart_payment_request: CreateCartPaymentRequest, request: Request
    ):
        req_context = get_context_from_req(request)
        app_context = get_context_from_app(request.app)
        req_context.log.debug(
            f"Creating cart_payment for payer {cart_payment_request.payer_id}"
        )

        try:
            cart_payment = await submit_payment(
                app_context=app_context,
                req_context=req_context,
                payment_repo=cart_payment_repo,
                payer_repo=payer_repo,
                payment_method_repo=payment_method_repo,
                request_cart_payment=request_to_model(cart_payment_request),
                idempotency_key=cart_payment_request.idempotency_key,
                country=cart_payment_request.country,
                currency=cart_payment_request.currency,
                client_description=cart_payment_request.client_description,
                payer_id_type=cart_payment_request.payer_id_type,
                payment_method_id_type=cart_payment_request.payment_method_id_type,
            )

            req_context.log.info(
                f"Created cart_payment {cart_payment.id} of type {cart_payment.cart_metadata.type} for payer {cart_payment.payer_id}"
            )
            return cart_payment
        except PaymentError as payment_error:
            http_status_code = HTTP_500_INTERNAL_SERVER_ERROR
            if payment_error.error_code == PayinErrorCode.PAYMENT_METHOD_GET_NOT_FOUND:
                http_status_code = HTTP_400_BAD_REQUEST
            elif (
                payment_error.error_code
                == PayinErrorCode.PAYMENT_METHOD_GET_PAYER_PAYMENT_METHOD_MISMATCH
            ):
                http_status_code = HTTP_403_FORBIDDEN

            raise PaymentException(
                http_status_code=http_status_code,
                error_code=payment_error.error_code,
                error_message=payment_error.error_message,
                retryable=payment_error.retryable,
            )

    @router.post(
        "/api/v1/cart_payments/{cart_payment_id}/adjust", status_code=HTTP_200_OK
    )
    async def update_cart_payment(
        cart_payment_id: UUID,
        cart_payment_request: UpdateCartPaymentRequest,
        request: Request,
    ):
        req_context = get_context_from_req(request)
        app_context = get_context_from_app(request.app)
        req_context.log.info(f"Updating cart_payment {cart_payment_id}")

        cart_payment: CartPayment = await update_payment(
            app_context=app_context,
            req_context=req_context,
            payment_repo=cart_payment_repo,
            payer_repo=payer_repo,
            payment_method_repo=payment_method_repo,
            idempotency_key=cart_payment_request.idempotency_key,
            cart_payment_id=cart_payment_id,
            payer_id=cart_payment_request.payer_id,
            amount=cart_payment_request.amount,
            legacy_payment=get_legacy_payment_model(cart_payment_request),
            client_description=cart_payment_request.client_description,
            payer_statement_description=cart_payment_request.payer_statement_description,
            metadata=get_cart_payment_metadata_model(cart_payment_request),
        )
        req_context.log.info(
            f"Updated cart_payment {cart_payment.id} for payer {cart_payment.payer_id}"
        )
        return cart_payment

    return router


def request_to_model(cart_payment_request: CreateCartPaymentRequest) -> CartPayment:
    return CartPayment(
        id=None,
        payer_id=cart_payment_request.payer_id,
        amount=cart_payment_request.amount,
        payment_method_id=cart_payment_request.payment_method_id,
        capture_method=cart_payment_request.capture_method,
        cart_metadata=CartMetadata(
            reference_id=cart_payment_request.metadata.reference_id,
            ct_reference_id=cart_payment_request.metadata.ct_reference_id,
            type=CartType(cart_payment_request.metadata.type),
        ),
        client_description=cart_payment_request.client_description,
        payer_statement_description=cart_payment_request.payer_statement_description,
        legacy_payment=LegacyPayment(
            consumer_id=getattr(
                cart_payment_request.legacy_payment, "consumer_id", None
            ),
            charge_id=getattr(cart_payment_request.legacy_payment, "charge_id", None),
            stripe_customer_id=getattr(
                cart_payment_request.legacy_payment, "stripe_customer_id", None
            ),
        ),
        split_payment=SplitPayment(
            payout_account_id=getattr(
                cart_payment_request.split_payment, "payout_account_id", None
            ),
            application_fee_amount=getattr(
                cart_payment_request.split_payment, "appication_fee_amount", None
            ),
        ),
        created_at=None,
        updated_at=None,
    )


def get_legacy_payment_model(
    cart_payment_request: UpdateCartPaymentRequest
) -> Optional[LegacyPayment]:
    if not cart_payment_request.legacy_payment:
        return None

    return LegacyPayment(
        consumer_id=cart_payment_request.legacy_payment.consumer_id,
        stripe_customer_id=cart_payment_request.legacy_payment.stripe_customer_id,
        charge_id=cart_payment_request.legacy_payment.charge_id,
    )


def get_cart_payment_metadata_model(
    cart_payment_request: UpdateCartPaymentRequest
) -> Optional[CartMetadata]:
    if not cart_payment_request.metadata:
        return None

    return CartMetadata(
        reference_id=cart_payment_request.metadata.reference_id,
        ct_reference_id=cart_payment_request.metadata.ct_reference_id,
        type=cart_payment_request.metadata.type,
    )