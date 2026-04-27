(function () {
    'use strict';

    const profileForm = document.getElementById('billingProfileForm');
    const fullNameInput = document.getElementById('fullName');
    const emailInput = document.getElementById('email');
    const planGrid = document.getElementById('planGrid');
    const historyList = document.getElementById('historyList');
    const historyEmpty = document.getElementById('historyEmpty');
    const checkoutState = document.getElementById('checkoutState');
    const checkoutCard = document.getElementById('checkoutCard');
    const selectedPlanLabel = document.getElementById('selectedPlanLabel');
    const selectedAmount = document.getElementById('selectedAmount');
    const selectedPaymentId = document.getElementById('selectedPaymentId');
    const upiHint = document.getElementById('upiHint');
    const openUpiBtn = document.getElementById('openUpiBtn');
    const copyUpiBtn = document.getElementById('copyUpiBtn');
    const confirmPaymentBtn = document.getElementById('confirmPaymentBtn');
    const merchantNamePill = document.getElementById('merchantNamePill');
    const merchantUpiPill = document.getElementById('merchantUpiPill');

    const STORAGE_KEY = 'forvyn_billing_profile';
    let plansByKey = new Map();
    let currentCheckout = null;

    function loadProfile() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed.fullName) fullNameInput.value = parsed.fullName;
                if (parsed.email) emailInput.value = parsed.email;
            }
        } catch (err) {
            console.warn('Could not load billing profile', err);
        }
    }

    function saveProfile() {
        const profile = {
            fullName: fullNameInput.value.trim(),
            email: emailInput.value.trim().toLowerCase(),
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
        return profile;
    }

    function getProfile() {
        const profile = saveProfile();
        if (!profile.fullName || !profile.email) {
            throw new Error('Enter your full name and email before starting checkout.');
        }
        return profile;
    }

    function groupPlans(plans) {
        const grouped = new Map();
        plans.forEach((plan) => {
            if (!grouped.has(plan.plan_tier)) {
                grouped.set(plan.plan_tier, []);
            }
            grouped.get(plan.plan_tier).push(plan);
            plansByKey.set(`${plan.plan_tier}:${plan.billing_cycle}`, plan);
        });
        return grouped;
    }

    function renderPlans(plans) {
        planGrid.innerHTML = '';
        const grouped = groupPlans(plans);

        const order = ['lite', 'premium'];
        order.forEach((tier) => {
            const cyclePlans = grouped.get(tier) || [];
            const card = document.createElement('div');
            card.className = `plan-card ${tier === 'premium' ? 'featured' : ''}`;

            const title = tier === 'lite' ? 'Lite' : 'Premium';
            const cycleButtons = cyclePlans
                .sort((a, b) => ['monthly', 'quarterly', 'annual'].indexOf(a.billing_cycle) - ['monthly', 'quarterly', 'annual'].indexOf(b.billing_cycle))
                .map((plan) => {
                    return `
                        <button type="button" class="cycle-btn" data-plan-tier="${plan.plan_tier}" data-billing-cycle="${plan.billing_cycle}">
                            <strong>₹${plan.amount_inr} / ${plan.billing_cycle}</strong>
                            <span>Open dummy UPI checkout</span>
                        </button>
                    `;
                })
                .join('');

            const featureList = (cyclePlans[0] && cyclePlans[0].features) ? cyclePlans[0].features : [];
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom: 6px;">
                    <div>
                        <h3>${title}</h3>
                        <p class="plan-tagline">${cyclePlans[0] ? cyclePlans[0].tagline : 'Select a billing cycle to continue.'}</p>
                    </div>
                    <span class="pill">${title} Plan</span>
                </div>
                <div style="display:grid; gap:14px; margin-bottom: 16px;">
                    ${featureList.length ? `<div class="muted-note"><strong>What’s included:</strong><br>${featureList.map((feature) => `• ${feature}`).join('<br>')}</div>` : ''}
                </div>
                <div class="cycle-grid">${cycleButtons}</div>
            `;

            planGrid.appendChild(card);
        });

        planGrid.querySelectorAll('.cycle-btn').forEach((button) => {
            button.addEventListener('click', () => {
                const planTier = button.dataset.planTier;
                const billingCycle = button.dataset.billingCycle;
                startCheckout(planTier, billingCycle).catch((error) => {
                    alert(error.message || 'Could not start checkout.');
                });
            });
        });
    }

    function renderHistory(payments) {
        historyList.innerHTML = '';
        if (!payments || payments.length === 0) {
            historyEmpty.classList.remove('hidden');
            return;
        }
        historyEmpty.classList.add('hidden');

        payments.forEach((payment) => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div class="history-item-header">
                    <div>
                        <strong>${payment.plan_tier.toUpperCase()} / ${payment.billing_cycle.toUpperCase()}</strong>
                        <div class="muted-note">${payment.full_name} · ${payment.email}</div>
                    </div>
                    <span class="status-badge ${payment.status}">${payment.status}</span>
                </div>
                <div class="muted-note">
                    Amount: ₹${payment.amount_inr}<br>
                    Reference: ${payment.transaction_reference}<br>
                    Created: ${new Date(payment.created_at).toLocaleString()}<br>
                    Updated: ${new Date(payment.updated_at).toLocaleString()}
                </div>
            `;
            historyList.appendChild(item);
        });
    }

    function setCheckoutState(payment, upiUri, instructions) {
        currentCheckout = { payment, upiUri };
        checkoutCard.classList.remove('hidden');
        checkoutState.textContent = 'Dummy checkout is ready. Open your UPI app, then mark paid to save the record.';
        selectedPlanLabel.textContent = `${payment.plan_tier.toUpperCase()} · ${payment.billing_cycle.toUpperCase()}`;
        selectedAmount.textContent = payment.amount_inr;
        selectedPaymentId.textContent = payment.payment_id;
        upiHint.textContent = instructions.join(' ');

        openUpiBtn.onclick = () => {
            window.location.href = upiUri;
        };

        copyUpiBtn.onclick = async () => {
            try {
                await navigator.clipboard.writeText(upiUri);
                copyUpiBtn.textContent = 'Copied';
                setTimeout(() => {
                    copyUpiBtn.textContent = 'Copy UPI Link';
                }, 1200);
            } catch (err) {
                alert('Could not copy the UPI link.');
            }
        };

        confirmPaymentBtn.onclick = async () => {
            await confirmCheckout(payment.payment_id);
        };
    }

    async function fetchJson(url, options = {}) {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload.detail || 'Request failed');
        }
        return payload;
    }

    async function loadPlansAndHistory() {
        const profile = saveProfile();
        const data = await fetchJson('/api/payments/plans');
        merchantNamePill.textContent = `Merchant: ${data.merchant_name}`;
        merchantUpiPill.textContent = `UPI: ${data.merchant_upi_id}`;
        renderPlans(data.plans);

        if (profile.email) {
            const history = await fetchJson(`/api/payments/history/${encodeURIComponent(profile.email)}`);
            renderHistory(history.payments);
        }
    }

    async function startCheckout(planTier, billingCycle) {
        const profile = getProfile();
        checkoutState.textContent = 'Creating dummy payment session...';
        const payload = {
            user_id: profile.email,
            full_name: profile.fullName,
            email: profile.email,
            plan_tier: planTier,
            billing_cycle: billingCycle,
        };
        const result = await fetchJson('/api/payments/checkout', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        setCheckoutState(result.payment, result.upi_uri, result.instructions || []);
        const history = await fetchJson(`/api/payments/history/${encodeURIComponent(profile.email)}`);
        renderHistory(history.payments);
    }

    async function confirmCheckout(paymentId) {
        const profile = getProfile();
        const result = await fetchJson('/api/payments/confirm', {
            method: 'POST',
            body: JSON.stringify({
                user_id: profile.email,
                payment_id: paymentId,
            }),
        });
        setCheckoutState(result.payment, result.upi_uri, result.instructions || []);
        const history = await fetchJson(`/api/payments/history/${encodeURIComponent(profile.email)}`);
        renderHistory(history.payments);
        checkoutState.textContent = 'Payment stored in history. This was a dummy UPI checkout for testing.';
    }

    profileForm.addEventListener('submit', (event) => {
        event.preventDefault();
        saveProfile();
        loadPlansAndHistory().catch((error) => {
            checkoutState.textContent = error.message || 'Could not refresh payment data.';
        });
    });

    [fullNameInput, emailInput].forEach((input) => {
        input.addEventListener('change', saveProfile);
        input.addEventListener('blur', saveProfile);
    });

    loadProfile();
    loadPlansAndHistory().catch((error) => {
        checkoutState.textContent = error.message || 'Could not load billing data.';
    });
})();
