from fastapi import APIRouter, Depends, HTTPException

from app.schemas.payment import (
    PaymentCheckoutRequest,
    PaymentCheckoutResponse,
    PaymentConfirmRequest,
    PaymentHistoryResponse,
    PaymentPlansResponse,
)
from app.services.payment_service import PaymentService, get_payment_service

router = APIRouter()


@router.get('/payments/plans', response_model=PaymentPlansResponse)
def get_plans(payment_service: PaymentService = Depends(get_payment_service)):
    return PaymentPlansResponse(
        merchant_name=payment_service.merchant_name,
        merchant_upi_id=payment_service.merchant_upi_id,
        plans=payment_service.list_plans(),
    )


@router.post('/payments/checkout', response_model=PaymentCheckoutResponse)
def checkout(payload: PaymentCheckoutRequest, payment_service: PaymentService = Depends(get_payment_service)):
    payment = payment_service.checkout(
        user_id=payload.user_id,
        full_name=payload.full_name,
        email=str(payload.email),
        plan_tier=payload.plan_tier,
        billing_cycle=payload.billing_cycle,
    )
    return PaymentCheckoutResponse(
        payment=payment,
        upi_uri=payment.upi_uri,
        instructions=[
            'Open the UPI link in your payment app.',
            'Complete the dummy payment flow for testing.',
            'Return here and confirm once you have finished.',
        ],
    )


@router.post('/payments/confirm', response_model=PaymentCheckoutResponse)
def confirm(payload: PaymentConfirmRequest, payment_service: PaymentService = Depends(get_payment_service)):
    payment = payment_service.confirm(payload.user_id, payload.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail='Payment not found for this user')
    return PaymentCheckoutResponse(
        payment=payment,
        upi_uri=payment.upi_uri,
        instructions=['Payment confirmed and stored in your history.'],
    )


@router.get('/payments/history/{user_id}', response_model=PaymentHistoryResponse)
def history(user_id: str, payment_service: PaymentService = Depends(get_payment_service)):
    profile = payment_service.user_profile(user_id)
    return PaymentHistoryResponse(
        user_id=user_id,
        email=profile.get('email'),
        full_name=profile.get('full_name'),
        payments=payment_service.list_history(user_id),
    )
