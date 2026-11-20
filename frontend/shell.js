// shell.js - shared header, footer and icon set for every Forvyn page.
(function () {
    'use strict';

    var ICONS = {
        'arrow-right': '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
        'arrow-left': '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
        'search': '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
        'draft': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
        'explain': '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
        'mapping': '<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>',
        'gavel': '<path d="m14.5 12.5-8 8a2.119 2.119 0 1 1-3-3l8-8"/><path d="m16 16 6-6"/><path d="m8 8 6-6"/><path d="m9 7 8 8"/><path d="m21 11-8-8"/>',
        'risk': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
        'folder': '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
        'card': '<rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/>',
        'user': '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
        'users': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        'idea': '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
        'message': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        'x': '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
        'send': '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
        'upload': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
        'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
        'check': '<path d="M20 6 9 17l-5-5"/>',
        'globe': '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
        'pen': '<path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>',
        'trash': '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
        'refresh': '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
        'file': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/>',
        'zap': '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
        'lock': '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
    };

    function icon(name, size) {
        var s = size || 18;
        return '<svg class="icon" width="' + s + '" height="' + s + '" viewBox="0 0 24 24" fill="none" ' +
            'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
            (ICONS[name] || '') + '</svg>';
    }
    window.ForvynIcon = icon;

    var SEAL = '<img class="brand-seal" src="/static/assets/emblem.svg" alt="" width="48" height="40">';

    var NAV = [
        { key: 'tools', href: '/tools', label: 'Tools' },
        { key: 'draft', href: '/draft', label: 'Draft' },
        { key: 'sources', href: '/sources', label: 'Sources' },
        { key: 'billing', href: '/billing', label: 'Plans' }
    ];

    function buildHeader(active) {
        var links = NAV.map(function (n) {
            return '<a href="' + n.href + '"' + (n.key === active ? ' class="is-active" aria-current="page"' : '') + '>' + n.label + '</a>';
        }).join('');
        return '' +
            '<div class="wrap site-header-bar">' +
            '<a class="brand" href="/" aria-label="Forvyn home">' +
            SEAL +
            '<span class="brand-name">Forvyn</span>' +
            '</a>' +
            '<nav class="site-nav" aria-label="Primary">' + links + '</nav>' +
            '<a class="site-account' + (active === 'workspace' ? ' is-active' : '') + '" href="/workspace">' +
            icon('user', 16) + '<span>Workspace</span></a>' +
            '</div>';
    }

    function buildFooter() {
        return '' +
            '<div class="wrap site-footer-grid">' +
            '<div>' +
            '<a class="brand" href="/">' + SEAL + '<span class="brand-name">Forvyn</span></a>' +
            '<p class="site-footer-note">Forvyn drafts from retrieved clause templates and statutory text. ' +
            'Output is a starting point for professional review and is not legal advice.</p>' +
            '</div>' +
            '<div class="site-footer-links">' +
            '<span class="eyebrow">Tools</span>' +
            '<a href="/draft">Draft a document</a>' +
            '<a href="/analyze-risks">Analyze risks</a>' +
            '<a href="/explain">Explain a provision</a>' +
            '<a href="/mapping">IPC to BNS</a>' +
            '</div>' +
            '<div class="site-footer-links">' +
            '<span class="eyebrow">Library</span>' +
            '<a href="/summarize">Summarize a judgment</a>' +
            '<a href="/sources">Legal sources</a>' +
            '<a href="/billing">Plans &amp; billing</a>' +
            '<a href="/workspace">Workspace</a>' +
            '</div>' +
            '</div>';
    }

    function mount() {
        var page = document.body.getAttribute('data-page') || '';

        var header = document.querySelector('[data-shell="header"]');
        if (header) {
            header.className = 'site-header';
            header.innerHTML = buildHeader(page);
        }

        var footer = document.querySelector('[data-shell="footer"]');
        if (footer) {
            footer.className = 'site-footer';
            footer.innerHTML = buildFooter();
        }

        document.querySelectorAll('[data-icon]').forEach(function (el) {
            el.innerHTML = icon(el.getAttribute('data-icon'), parseInt(el.getAttribute('data-size'), 10) || 18);
            el.classList.add('icon-slot');
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mount);
    } else {
        mount();
    }
})();
