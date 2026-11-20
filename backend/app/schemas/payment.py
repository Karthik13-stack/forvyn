from pydantic import BaseModel, EmailStr, Field
from typing import List, Literal, Optional


BillingCycle = Literal['monthly', 'quarterly', 'annual']
PlanTier = Literal['lite', 'premium']
PaymentStatus = Literal['initiated', 'completed', 'failed', 'expired']


class PaymentCheckoutRequest(BaseModel):
    user_id: str = Field(..., min_length=3)
    full_name: str = Field(..., min_length=2)
    email: str
    plan_tier: PlanTier
    billing_cycle: BillingCycle


class PaymentConfirmRequest(BaseModel):
    user_id: str = Field(..., min_length=3)
    payment_id: str = Field(..., min_length=5)


class PaymentHistoryRecord(BaseModel):
    payment_id: str
    user_id: str
    full_name: str
    email: str
    plan_tier: PlanTier
    billing_cycle: BillingCycle
    amount_inr: int
    status: PaymentStatus
    merchant_upi_id: str
    upi_uri: str
    transaction_reference: str
    created_at: str
    updated_at: str


class PaymentPlan(BaseModel):
    plan_tier: PlanTier
    billing_cycle: BillingCycle
    amount_inr: int
    title: str
    tagline: str
    features: List[str]


class PaymentPlansResponse(BaseModel):
    merchant_name: str
    merchant_upi_id: str
    plans: List[PaymentPlan]


class PaymentCheckoutResponse(BaseModel):
    payment: PaymentHistoryRecord
    upi_uri: str
    instructions: List[str]


class PaymentHistoryResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    payments: List[PaymentHistoryRecord]
