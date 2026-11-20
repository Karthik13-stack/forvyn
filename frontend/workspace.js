(function () {
    'use strict';

    var STORAGE_KEY = 'forvyn_billing_profile';

    function esc(value) {
        var div = document.createElement('div');
        div.textContent = value == null ? '' : String(value);
        return div.innerHTML;
    }

    function el(id) { return document.getElementById(id); }

    function loadProfile() {
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            return saved ? JSON.parse(saved) : {};
        } catch (err) {
            return {};
        }
    }

    function formatBytes(bytes) {
        if (!bytes) return '0 B';
        var units = ['B', 'KB', 'MB', 'GB'];
        var i = 0;
        while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
        return bytes.toFixed(bytes >= 10 || i === 0 ? 0 : 1) + ' ' + units[i];
    }

    function renderProfile(profile) {
        if (profile.fullName) {
            el('wsName').textContent = profile.fullName;
            el('wsGreeting').textContent = 'Welcome back, ' + profile.fullName.split(' ')[0];
            el('wsAvatar').textContent = profile.fullName.trim().charAt(0).toUpperCase();
        }
        if (profile.email) el('wsEmail').textContent = profile.email;
    }

    function renderSources(sources) {
        el('wsSources').textContent = sources.length;
        var list = el('wsSourceList');
        list.innerHTML = '';
        if (!sources.length) return;
        el('wsSourceEmpty').classList.add('hidden');

        sources
            .slice()
            .sort(function (a, b) { return new Date(b.created_at || 0) - new Date(a.created_at || 0); })
            .slice(0, 5)
            .forEach(function (item) {
                var a = document.createElement('a');
                a.className = 'source-item';
                a.href = '/sources';
                a.innerHTML =
                    '<div class="source-item-title">' + esc(item.original_name || item.stored_name) + '</div>' +
                    '<div class="source-item-meta">' + esc(item.category || 'Uncategorized') + ' &middot; ' + esc(item.source_type || 'General') + '</div>' +
                    '<div class="source-item-foot">' + formatBytes(item.size_bytes || 0) + ' &middot; ' +
                    new Date(item.created_at || Date.now()).toLocaleDateString() + '</div>';
                list.appendChild(a);
            });
    }

    function renderHistory(payments) {
        el('wsPayments').textContent = payments.length;
        var list = el('wsHistoryList');
        list.innerHTML = '';
        if (!payments.length) return;
        el('wsHistoryEmpty').classList.add('hidden');

        var completed = payments.filter(function (p) { return p.status === 'completed'; });
        var latest = (completed[0] || payments[0]);
        el('wsPlan').textContent = latest.plan_tier.charAt(0).toUpperCase() + latest.plan_tier.slice(1) +
            ' (' + latest.billing_cycle + ')' + (completed.length ? '' : ' - unpaid');

        payments.slice(0, 5).forEach(function (p) {
            var item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML =
                '<div class="history-item-header">' +
                '<div><strong>' + esc(p.plan_tier.toUpperCase()) + ' / ' + esc(p.billing_cycle.toUpperCase()) + '</strong>' +
                '<div class="muted-note">Rs. ' + esc(p.amount_inr) + ' &middot; ' + new Date(p.created_at).toLocaleDateString() + '</div></div>' +
                '<span class="status-badge ' + esc(p.status) + '">' + esc(p.status) + '</span>' +
                '</div>';
            list.appendChild(item);
        });
    }

    function getJson(url) {
        return fetch(url).then(function (res) {
            if (!res.ok) throw new Error('Request failed');
            return res.json();
        });
    }

    var profile = loadProfile();
    renderProfile(profile);

    getJson('/api/sources').then(renderSources).catch(function () {
        el('wsSourceEmpty').textContent = 'Could not load sources.';
    });

    if (profile.email) {
        getJson('/api/payments/history/' + encodeURIComponent(profile.email))
            .then(function (data) { renderHistory(data.payments || []); })
            .catch(function () { el('wsHistoryEmpty').textContent = 'Could not load payment history.'; });
    }
})();
