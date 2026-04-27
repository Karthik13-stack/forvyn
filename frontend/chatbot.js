// chatbot.js - Self-contained chatbot widget for Forvyn AI
(function () {
    'use strict';

    const ROUTE_MAP = {
        'navigate:dashboard': { path: '/', label: 'Go to Dashboard' },
        'navigate:explain-provision': { path: '/explain', label: 'Open Explain Provision' },
        'navigate:ipc-bns-mapping': { path: '/mapping', label: 'Open IPC → BNS Mapping' },
        'navigate:draft-documents': { path: '/draft', label: 'Open Draft Documents' },
        'navigate:summarize-judgment': { path: '/summarize', label: 'Open Summarize Judgment' },
        'navigate:analyze-risks': { path: '/analyze-risks', label: 'Open Analyze Risks' },
        'navigate:billing': { path: '/billing', label: 'Open Billing & Subscriptions' },
        'navigate:sources': { path: '/sources', label: 'Open Legal Sources' }
    };

    const QUICK_ACTIONS = [
        { label: '📝 Draft a Document', action: 'navigate:draft-documents' },
        { label: '⚠️ Analyze Risks', action: 'navigate:analyze-risks' },
        { label: '💳 Billing & Plans', action: 'navigate:billing' },
        { label: '📁 Legal Sources', action: 'navigate:sources' },
        { label: '💡 Legal Basics', message: 'What are some basic legal concepts I should know?' }
    ];

    let conversationHistory = [];
    const MAX_HISTORY = 5;
    let isSending = false;

    // ---- Build DOM ----
    function buildWidget() {
        // Toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'chatbot-toggle';
        toggleBtn.id = 'chatbotToggle';
        toggleBtn.innerHTML = '💬';
        toggleBtn.setAttribute('aria-label', 'Open chatbot');

        // Chat window
        const chatWindow = document.createElement('div');
        chatWindow.className = 'chatbot-window';
        chatWindow.id = 'chatbotWindow';
        chatWindow.innerHTML = `
            <div class="chatbot-header">
                <div class="chatbot-header-avatar">⚖️</div>
                <div class="chatbot-header-info">
                    <div class="chatbot-header-title">Forvyn Assistant</div>
                    <div class="chatbot-header-status">Online</div>
                </div>
                <button class="chatbot-close-btn" id="chatbotCloseBtn" aria-label="Close chat">✕</button>
            </div>
            <div class="chatbot-quick-actions" id="chatbotQuickActions"></div>
            <div class="chatbot-messages" id="chatbotMessages"></div>
            <div class="chatbot-input-area">
                <input class="chatbot-input" id="chatbotInput" type="text"
                       placeholder="Ask me anything..." autocomplete="off" />
                <button class="chatbot-send-btn" id="chatbotSendBtn" aria-label="Send message">➤</button>
            </div>
        `;

        document.body.appendChild(chatWindow);
        document.body.appendChild(toggleBtn);

        renderQuickActions();
        addWelcomeMessage();
        bindEvents();
    }

    // ---- Quick Actions ----
    function renderQuickActions() {
        const container = document.getElementById('chatbotQuickActions');
        QUICK_ACTIONS.forEach(qa => {
            const btn = document.createElement('button');
            btn.className = 'chatbot-quick-btn';
            btn.textContent = qa.label;
            btn.addEventListener('click', () => {
                if (qa.action) {
                    const route = ROUTE_MAP[qa.action];
                    if (route) window.location.href = route.path;
                } else if (qa.message) {
                    document.getElementById('chatbotInput').value = qa.message;
                    sendMessage();
                }
            });
            container.appendChild(btn);
        });
    }

    // ---- Welcome Message ----
    function addWelcomeMessage() {
        const reply = "👋 Hi! I'm your Forvyn AI assistant. I can help you navigate the platform, answer legal questions, or point you to the right tool. How can I help?";
        appendBotMessage(reply);
    }

    // ---- Events ----
    function bindEvents() {
        const toggleBtn = document.getElementById('chatbotToggle');
        const closeBtn = document.getElementById('chatbotCloseBtn');
        const sendBtn = document.getElementById('chatbotSendBtn');
        const input = document.getElementById('chatbotInput');

        toggleBtn.addEventListener('click', toggleChat);
        closeBtn.addEventListener('click', toggleChat);
        sendBtn.addEventListener('click', sendMessage);

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // ---- Toggle ----
    function toggleChat() {
        const win = document.getElementById('chatbotWindow');
        const btn = document.getElementById('chatbotToggle');
        const isOpen = win.classList.contains('open');

        if (isOpen) {
            win.classList.remove('open');
            btn.classList.remove('active');
            btn.innerHTML = '💬';
        } else {
            win.classList.add('open');
            btn.classList.add('active');
            btn.innerHTML = '✕';
            setTimeout(() => {
                document.getElementById('chatbotInput').focus();
            }, 350);
        }
    }

    // ---- Send Message ----
    async function sendMessage() {
        if (isSending) return;

        const input = document.getElementById('chatbotInput');
        const message = input.value.trim();
        if (!message) return;

        input.value = '';
        isSending = true;
        document.getElementById('chatbotSendBtn').disabled = true;

        appendUserMessage(message);

        conversationHistory.push({ role: 'user', content: message });
        if (conversationHistory.length > MAX_HISTORY * 2) {
            conversationHistory = conversationHistory.slice(-MAX_HISTORY * 2);
        }

        const typingEl = showTypingIndicator();

        try {
            const contextStr = buildContext();
            const res = await fetch('/api/chatbot/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    context: contextStr
                })
            });

            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`);
            }

            const data = await res.json();

            removeTypingIndicator(typingEl);

            appendBotMessage(data.reply, data.action, data.intent);

            conversationHistory.push({ role: 'assistant', content: data.reply });

        } catch (err) {
            console.error('Chatbot error:', err);
            removeTypingIndicator(typingEl);
            appendBotMessage("Sorry, I'm having trouble connecting. Please try again in a moment.");
        }

        isSending = false;
        document.getElementById('chatbotSendBtn').disabled = false;
        document.getElementById('chatbotInput').focus();
    }

    // ---- Context Builder ----
    function buildContext() {
        const parts = [];
        parts.push('Current page: ' + window.location.pathname);

        if (conversationHistory.length > 0) {
            const recent = conversationHistory.slice(-MAX_HISTORY * 2);
            const historyStr = recent.map(h => `${h.role}: ${h.content}`).join('\n');
            parts.push('Recent conversation:\n' + historyStr);
        }

        return parts.join('\n\n');
    }

    // ---- Render Messages ----
    function appendUserMessage(text) {
        const container = document.getElementById('chatbotMessages');
        const msg = document.createElement('div');
        msg.className = 'chatbot-msg user';
        msg.innerHTML = `
            <div class="chatbot-msg-avatar">👤</div>
            <div class="chatbot-msg-bubble">${escapeHtml(text)}</div>
        `;
        container.appendChild(msg);
        scrollToBottom();
    }

    function appendBotMessage(text, action, intent) {
        const container = document.getElementById('chatbotMessages');
        const msg = document.createElement('div');
        msg.className = 'chatbot-msg bot';

        let bubbleContent = escapeHtml(text);

        if (action && ROUTE_MAP[action]) {
            const route = ROUTE_MAP[action];
            bubbleContent += `
                <div>
                    <a class="chatbot-action-link" href="${route.path}">
                        → ${route.label}
                    </a>
                </div>
            `;
        }

        if (intent === 'simple_legal' && !text.toLowerCase().includes('not legal advice')) {
            bubbleContent += `<div class="chatbot-disclaimer">⚠ This is general information, not legal advice.</div>`;
        }

        msg.innerHTML = `
            <div class="chatbot-msg-avatar">⚖️</div>
            <div class="chatbot-msg-bubble">${bubbleContent}</div>
        `;
        container.appendChild(msg);
        scrollToBottom();
    }

    // ---- Typing Indicator ----
    function showTypingIndicator() {
        const container = document.getElementById('chatbotMessages');
        const msg = document.createElement('div');
        msg.className = 'chatbot-msg bot';
        msg.id = 'chatbotTyping';
        msg.innerHTML = `
            <div class="chatbot-msg-avatar">⚖️</div>
            <div class="chatbot-msg-bubble">
                <div class="chatbot-typing">
                    <div class="chatbot-typing-dot"></div>
                    <div class="chatbot-typing-dot"></div>
                    <div class="chatbot-typing-dot"></div>
                </div>
            </div>
        `;
        container.appendChild(msg);
        scrollToBottom();
        return msg;
    }

    function removeTypingIndicator(el) {
        if (el && el.parentNode) {
            el.parentNode.removeChild(el);
        }
    }

    // ---- Helpers ----
    function scrollToBottom() {
        const container = document.getElementById('chatbotMessages');
        requestAnimationFrame(() => {
            container.scrollTop = container.scrollHeight;
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ---- Init ----
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', buildWidget);
    } else {
        buildWidget();
    }
})();
