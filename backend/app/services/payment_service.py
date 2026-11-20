import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

from app.core.config import settings
from app.schemas.payment import BillingCycle, PaymentHistoryRecord, PaymentPlan, PlanTier

STORAGE_DIR = Path(__file__).resolve().parent / 'storage'
PAYMENTS_FILE = STORAGE_DIR / 'payment_history.json'


@dataclass(frozen=True)
class PlanPrice:
    amount_inr: int
    title: str
    tagline: str
    features: List[str]


PLAN_PRICE_MAP: Dict[PlanTier, Dict[BillingCycle, PlanPrice]] = {
    'lite': {
        'monthly': PlanPrice(
            amount_inr=199,
            title='Lite Monthly',
            tagline='For solo users who need quick legal drafts and basic support.',
            features=['Drafting access', 'Basic legal explanations', 'Email support'],
        ),
        'quarterly': PlanPrice(
            amount_inr=549,
            title='Lite Quarterly',
            tagline='Best value for frequent document work over three months.',
            features=['Drafting access', 'Basic legal explanations', 'Priority queue', 'Save payment history'],
        ),
        'annual': PlanPrice(
            amount_inr=1999,
            title='Lite Annual',
            tagline='Affordable annual access for steady use.',
            features=['Drafting access', 'Basic legal explanations', 'Priority queue', 'Annual record export'],
        ),
    },
    'premium': {
        'monthly': PlanPrice(
            amount_inr=499,
            title='Premium Monthly',
            tagline='For teams needing advanced review and concierge help.',
            features=['Everything in Lite', 'Risk checks', 'Concierge routing', 'Premium support'],
        ),
        'quarterly': PlanPrice(
            amount_inr=1299,
            title='Premium Quarterly',
            tagline='Best value for ongoing professional work.',
            features=['Everything in Lite', 'Risk checks', 'Concierge routing', 'Quarterly billing history'],
        ),
        'annual': PlanPrice(
            amount_inr=4499,
            title='Premium Annual',
            tagline='Full year access for legal operations and heavy use.',
            features=['Everything in Lite', 'Risk checks', 'Concierge routing', 'Annual savings'],
        ),
    },
}


class PaymentService:
    def __init__(self):
        self.merchant_name = 'Forvyn AI'
        self.merchant_upi_id = settings.MERCHANT_UPI_ID
        self.merchant_display = settings.MERCHANT_NAME
        self._store = self._load_store()

    def _load_store(self) -> dict:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        if PAYMENTS_FILE.exists():
            try:
                with open(PAYMENTS_FILE, 'r', encoding='utf-8') as handle:
                    data = json.load(handle)
                    if isinstance(data, dict):
                        data.setdefault('users', {})
                        data.setdefault('payments', {})
                        return data
            except Exception:
                pass
        return {'users': {}, 'payments': {}}

    def _save_store(self) -> None:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        with open(PAYMENTS_FILE, 'w', encoding='utf-8') as handle:
            json.dump(self._store, handle, indent=2, ensure_ascii=False)

    def list_plans(self) -> List[PaymentPlan]:
        plans: List[PaymentPlan] = []
        for tier, cycle_map in PLAN_PRICE_MAP.items():
            for cycle, price in cycle_map.items():
                plans.append(
                    PaymentPlan(
                        plan_tier=tier,
                        billing_cycle=cycle,
                        amount_inr=price.amount_inr,
                        title=price.title,
                        tagline=price.tagline,
                        features=price.features,
                    )
                )
        return plans

    def _get_plan_price(self, plan_tier: PlanTier, billing_cycle: BillingCycle) -> PlanPrice:
        return PLAN_PRICE_MAP[plan_tier][billing_cycle]

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_upi_uri(self, payment_id: str, full_name: str, amount_inr: int, plan_tier: PlanTier, billing_cycle: BillingCycle) -> str:
        note = f'{plan_tier.title()} {billing_cycle.title()} subscription for {full_name} ({payment_id})'
        params = {
            'pa': self.merchant_upi_id,
            'pn': self.merchant_display,
            'am': f'{amount_inr:.2f}',
            'cu': 'INR',
            'tn': note,
            'tr': payment_id,
        }
        encoded = '&'.join(f'{key}={quote(str(value))}' for key, value in params.items())
        return f'upi://pay?{encoded}'

    def _build_transaction_reference(self) -> str:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        token = secrets.token_hex(4).upper()
        return f'FVN-{stamp}-{token}'

    def checkout(self, user_id: str, full_name: str, email: str, plan_tier: PlanTier, billing_cycle: BillingCycle) -> PaymentHistoryRecord:
        price = self._get_plan_price(plan_tier, billing_cycle)
        payment_id = f'PAY-{secrets.token_hex(6).upper()}'
        now = self._now()
        upi_uri = self._build_upi_uri(payment_id, full_name, price.amount_inr, plan_tier, billing_cycle)
        record = PaymentHistoryRecord(
            payment_id=payment_id,
            user_id=user_id,
            full_name=full_name,
            email=email,
            plan_tier=plan_tier,
            billing_cycle=billing_cycle,
            amount_inr=price.amount_inr,
            status='initiated',
            merchant_upi_id=self.merchant_upi_id,
            upi_uri=upi_uri,
            transaction_reference=self._build_transaction_reference(),
            created_at=now,
            updated_at=now,
        )
        self._store['payments'][payment_id] = record.model_dump()
        self._store['users'].setdefault(user_id, {
            'user_id': user_id,
            'full_name': full_name,
            'email': email,
            'payments': [],
        })
        user_entry = self._store['users'][user_id]
        user_entry['full_name'] = full_name
        user_entry['email'] = email
        user_entry['payments'] = [record.model_dump()] + [p for p in user_entry.get('payments', []) if p.get('payment_id') != payment_id]
        self._save_store()
        return record

    def confirm(self, user_id: str, payment_id: str) -> Optional[PaymentHistoryRecord]:
        payment = self._store['payments'].get(payment_id)
        if not payment or payment.get('user_id') != user_id:
            return None
        payment['status'] = 'completed'
        payment['updated_at'] = self._now()
        self._store['payments'][payment_id] = payment
        user_entry = self._store['users'].get(user_id)
        if user_entry:
            user_entry['payments'] = [payment if p.get('payment_id') == payment_id else p for p in user_entry.get('payments', [])]
        self._save_store()
        return PaymentHistoryRecord(**payment)

    def list_history(self, user_id: str) -> List[PaymentHistoryRecord]:
        user_entry = self._store['users'].get(user_id, {})
        payments = user_entry.get('payments', [])
        parsed: List[PaymentHistoryRecord] = []
        for payment in payments:
            try:
                parsed.append(PaymentHistoryRecord(**payment))
            except Exception:
                continue
        parsed.sort(key=lambda item: item.created_at, reverse=True)
        return parsed

    def user_profile(self, user_id: str) -> dict:
        user_entry = self._store['users'].get(user_id, {})
        return {
            'user_id': user_id,
            'full_name': user_entry.get('full_name'),
            'email': user_entry.get('email'),
        }


payment_service = PaymentService()


def get_payment_service() -> PaymentService:
    return payment_service
