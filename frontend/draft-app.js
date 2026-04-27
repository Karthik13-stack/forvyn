/**
 * draft-app.js — 4-Step Legal Document Drafting Wizard
 * Powers the domain → category/document → AI questions → editor/signature flow.
 */
(function () {
    'use strict';

    const API = '/api';

    // ── State ────────────────────────────────────────────────────
    const state = {
        currentStep: 1,
        domain: null,
        category: null,
        document: null,
        questions: [],
        answers: {},
        content: null,
        originalContent: null,
        englishContent: null,
        selectedLanguage: 'English',
        signatureData: null,
    };

    // ── Signature canvas vars ────────────────────────────────────
    let canvas, ctx, isDrawing = false, lastX = 0, lastY = 0;

    // ── Boot ─────────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        initSignatureCanvas();
    });

    // ── Step Navigation ──────────────────────────────────────────
    window.goToStep = function (step) {
        document.querySelectorAll('.draft-section').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.step-item').forEach(s => s.classList.remove('active', 'completed'));

        const target = document.getElementById('section' + step);
        if (target) target.classList.add('active');

        for (let i = 1; i <= 4; i++) {
            const tab = document.getElementById('step' + i + '-tab');
            if (tab) {
                if (i < step) tab.classList.add('completed');
                if (i === step) tab.classList.add('active');
            }
        }
        state.currentStep = step;

        if (step === 4) setTimeout(initSignatureCanvas, 150);
    };

    window.navigateToStep = function (step) {
        if (step < state.currentStep) { goToStep(step); return; }
        if (step === 1) { goToStep(1); return; }
        if (step === 2 && state.domain) { goToStep(2); return; }
        if (step === 3 && state.questions.length > 0) { goToStep(3); return; }
        if (step === 4 && state.content) { goToStep(4); return; }
        const msgs = {
            2: 'Please select a legal domain first.',
            3: 'Please select category/document and generate questions.',
            4: 'Please answer questions and generate a document first.',
        };
        alert(msgs[step] || 'Complete previous steps first.');
    };

    // ── Step 1 — Domain selection ────────────────────────────────
    window.selectDomain = async function (domain, el) {
        document.querySelectorAll('.domain-card').forEach(c => c.classList.remove('selected'));
        if (el) el.classList.add('selected');
        state.domain = domain;

        try {
            const res = await fetch(`${API}/drafting/categories?domain=${encodeURIComponent(domain)}`);
            const data = await res.json();
            const sel = document.getElementById('categorySelect');
            sel.innerHTML = '<option value="">Select Category</option>';
            (data.categories || []).forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                sel.appendChild(opt);
            });
            document.getElementById('documentSelect').innerHTML = '<option value="">Select Document</option>';
            setTimeout(() => goToStep(2), 250);
        } catch (err) {
            alert('Error loading categories: ' + err.message);
        }
    };

    // ── Step 2 — Category / Document cascading ───────────────────
    window.loadDocuments = async function () {
        const category = document.getElementById('categorySelect').value;
        if (!state.domain || !category) return;
        state.category = category;

        try {
            const res = await fetch(
                `${API}/drafting/documents?domain=${encodeURIComponent(state.domain)}&category=${encodeURIComponent(category)}`
            );
            const data = await res.json();
            const sel = document.getElementById('documentSelect');
            sel.innerHTML = '<option value="">Select Document</option>';
            (data.documents || []).forEach(doc => {
                const opt = document.createElement('option');
                opt.value = doc;
                opt.textContent = doc;
                sel.appendChild(opt);
            });
        } catch (err) {
            alert('Error loading documents: ' + err.message);
        }
    };

    // ── Step 2 → 3 — Generate Questions ──────────────────────────
    window.generateQuestions = async function () {
        const category = document.getElementById('categorySelect').value;
        const documentType = document.getElementById('documentSelect').value;
        if (!category || !documentType) { alert('Please select both category and document.'); return; }
        if (!state.domain) { alert('Please select a domain first.'); return; }

        state.category = category;
        state.document = documentType;
        state.answers = {};

        const langSel = document.getElementById('languageSelect');
        state.selectedLanguage = langSel ? langSel.value : 'English';

        const container = document.getElementById('questionsContainer');
        const loadMsg = state.selectedLanguage !== 'English'
            ? `AI is generating questions in ${state.selectedLanguage}…`
            : 'AI is analyzing legal requirements…';
        container.innerHTML = `<div class="draft-loading"><div class="spinner"></div><p>${loadMsg}</p></div>`;
        goToStep(3);

        try {
            const res = await fetch(`${API}/drafting/questions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domain: state.domain,
                    category,
                    document: documentType,
                    language: state.selectedLanguage,
                }),
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
                throw new Error(errData.detail || 'Failed to generate questions');
            }

            const data = await res.json();
            if (!Array.isArray(data.questions) || data.questions.length === 0) throw new Error('No questions received.');

            state.questions = data.questions;
            renderQuestions(data.questions);
        } catch (err) {
            container.innerHTML = `<div class="draft-error">Error: ${err.message}</div>`;
        }
    };

    function renderQuestions(questions) {
        const container = document.getElementById('questionsContainer');
        container.innerHTML = '';
        questions.forEach((q, idx) => {
            const item = document.createElement('div');
            item.className = 'question-item';

            const label = document.createElement('label');
            label.textContent = `${idx + 1}. ${q}`;

            const row = document.createElement('div');
            row.className = 'input-row';

            const ta = document.createElement('textarea');
            ta.id = `q_ans_${idx}`;
            ta.placeholder = 'Type your answer…';
            ta.oninput = function () { state.answers[q] = this.value; };

            const voiceBtn = document.createElement('button');
            voiceBtn.className = 'voice-btn';
            voiceBtn.title = 'Voice Input';
            voiceBtn.innerHTML = micSVG;
            voiceBtn.onclick = () => toggleVoice(ta.id, voiceBtn);

            row.appendChild(ta);
            row.appendChild(voiceBtn);
            item.appendChild(label);
            item.appendChild(row);
            container.appendChild(item);
        });
    }

    // ── Step 3 → 4 — Generate Document ───────────────────────────
    window.generateDocument = async function () {
        const btn = document.getElementById('generateDocBtn');
        if (btn) { btn.disabled = true; btn.textContent = 'AI is Drafting Document…'; }

        const langSel = document.getElementById('languageSelect');
        state.selectedLanguage = langSel ? langSel.value : 'English';

        try {
            const res = await fetch(`${API}/drafting/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domain: state.domain,
                    category: state.category,
                    document: state.document,
                    answers: state.answers,
                    language: state.selectedLanguage,
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: 'Generation failed' }));
                throw new Error(err.detail || 'Generation failed');
            }

            const data = await res.json();
            const cleaned = cleanMarkdown(data.content);
            state.content = cleaned;
            state.originalContent = cleaned;
            state.englishContent = null;

            const editor = document.getElementById('documentEditor');
            if (editor) editor.value = cleaned;

            // Update language indicator
            const langInd = document.getElementById('currentLanguage');
            if (langInd) langInd.textContent = state.selectedLanguage;

            // Show/hide translate button
            const translateBtn = document.getElementById('translateBtn');
            if (translateBtn) {
                translateBtn.style.display = state.selectedLanguage !== 'English' ? 'inline-flex' : 'none';
                translateBtn.textContent = '🌐 Show English';
            }

            goToStep(4);
        } catch (err) {
            alert('Error: ' + err.message);
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = 'Generate Document'; }
        }
    };

    // ── Language switching ────────────────────────────────────────
    window.regenerateInLanguage = async function () {
        const langSel = document.getElementById('docOutputLanguage');
        const newLang = langSel ? langSel.value : 'English';
        if (newLang === state.selectedLanguage) return;
        if (!state.answers || Object.keys(state.answers).length === 0) {
            alert('No document data available.'); return;
        }

        const editor = document.getElementById('documentEditor');
        if (editor) { editor.value = `Regenerating in ${newLang}…`; editor.disabled = true; }

        try {
            const res = await fetch(`${API}/drafting/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domain: state.domain,
                    category: state.category,
                    document: state.document,
                    answers: state.answers,
                    language: newLang,
                }),
            });
            if (!res.ok) throw new Error('Regeneration failed');
            const data = await res.json();
            const cleaned = cleanMarkdown(data.content);
            state.selectedLanguage = newLang;
            state.originalContent = cleaned;
            state.englishContent = null;
            if (editor) { editor.value = cleaned; editor.disabled = false; }

            const langInd = document.getElementById('currentLanguage');
            if (langInd) langInd.textContent = newLang;
            const trBtn = document.getElementById('translateBtn');
            if (trBtn) {
                trBtn.style.display = newLang !== 'English' ? 'inline-flex' : 'none';
                trBtn.textContent = '🌐 Show English';
            }
        } catch (err) {
            alert('Regeneration error: ' + err.message);
            if (editor) { editor.value = state.originalContent || ''; editor.disabled = false; }
        }
    };

    window.translateToEnglish = async function () {
        const btn = document.getElementById('translateBtn');
        const editor = document.getElementById('documentEditor');
        if (!editor || !state.originalContent) return;

        if (state.englishContent && editor.value === state.englishContent) {
            editor.value = state.originalContent;
            btn.textContent = '🌐 Show English';
            return;
        }
        if (state.englishContent) {
            editor.value = state.englishContent;
            btn.textContent = `🌐 Show ${state.selectedLanguage}`;
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Translating…';
        try {
            const res = await fetch(`${API}/drafting/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: state.originalContent,
                    from_language: state.selectedLanguage,
                    to_language: 'English',
                }),
            });
            if (!res.ok) throw new Error('Translation failed');
            const data = await res.json();
            state.englishContent = data.translated_content;
            editor.value = state.englishContent;
            btn.textContent = `🌐 Show ${state.selectedLanguage}`;
        } catch (err) {
            alert('Translation error: ' + err.message);
            btn.textContent = '🌐 Show English';
        } finally {
            btn.disabled = false;
        }
    };

    // ── Downloads ────────────────────────────────────────────────
    window.downloadPDF = async function () {
        const content = document.getElementById('documentEditor').value;
        if (!content) { alert('No content to download.'); return; }
        await exportFile('pdf', content);
    };

    window.downloadDOCX = async function () {
        const content = document.getElementById('documentEditor').value;
        if (!content) { alert('No content to download.'); return; }
        await exportFile('docx', content);
    };

    async function exportFile(format, content) {
        const filename = (state.document || 'legal_document').replace(/\s+/g, '_');
        const mimeTypes = {
            pdf: 'application/pdf',
            docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        };
        try {
            const res = await fetch(`${API}/export/${format}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content, filename }),
            });
            if (!res.ok) throw new Error('Export failed');
            const arrayBuffer = await res.arrayBuffer();
            const blob = new Blob([arrayBuffer], { type: mimeTypes[format] || 'application/octet-stream' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}.${format}`;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            // Delay cleanup so the browser can start the download
            setTimeout(() => { a.remove(); URL.revokeObjectURL(url); }, 1000);
        } catch (err) {
            alert(`Export error: ${err.message}`);
        }
    }

    // ── Voice Recognition ────────────────────────────────────────
    let recognition = null;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SR();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
    }

    const micSVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>';
    const stopSVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';

    function toggleVoice(textareaId, btn) {
        if (!recognition) { alert('Speech Recognition not supported.'); return; }

        if (btn.classList.contains('recording')) {
            recognition.stop();
            btn.classList.remove('recording');
            btn.innerHTML = micSVG;
            return;
        }

        const ta = document.getElementById(textareaId);
        btn.classList.add('recording');
        btn.innerHTML = stopSVG;

        recognition.onresult = (e) => {
            let final = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
                if (e.results[i].isFinal) final += e.results[i][0].transcript;
            }
            if (final) { ta.value = (ta.value + ' ' + final).trim(); ta.dispatchEvent(new Event('input')); }
        };
        recognition.onerror = () => { recognition.stop(); btn.classList.remove('recording'); btn.innerHTML = micSVG; };
        recognition.onend = () => { btn.classList.remove('recording'); btn.innerHTML = micSVG; };
        recognition.start();
    }

    // ── E-Signature ──────────────────────────────────────────────
    function initSignatureCanvas() {
        canvas = document.getElementById('signatureCanvas');
        if (!canvas) return;
        ctx = canvas.getContext('2d');
        const container = canvas.parentElement;
        canvas.width = container.clientWidth - 20;
        canvas.height = 150;
        ctx.strokeStyle = '#60a5fa';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        canvas.addEventListener('mousedown', startDraw);
        canvas.addEventListener('mousemove', drawing);
        canvas.addEventListener('mouseup', stopDraw);
        canvas.addEventListener('mouseout', stopDraw);
        canvas.addEventListener('touchstart', touchStart);
        canvas.addEventListener('touchmove', touchMove);
        canvas.addEventListener('touchend', stopDraw);
    }
    window.initSignatureCanvas = initSignatureCanvas;

    function startDraw(e) { isDrawing = true; [lastX, lastY] = [e.offsetX, e.offsetY]; }
    function drawing(e) {
        if (!isDrawing) return;
        ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(e.offsetX, e.offsetY); ctx.stroke();
        [lastX, lastY] = [e.offsetX, e.offsetY];
    }
    function stopDraw() { isDrawing = false; }
    function touchStart(e) {
        e.preventDefault();
        const t = e.touches[0], r = canvas.getBoundingClientRect();
        isDrawing = true; lastX = t.clientX - r.left; lastY = t.clientY - r.top;
    }
    function touchMove(e) {
        e.preventDefault(); if (!isDrawing) return;
        const t = e.touches[0], r = canvas.getBoundingClientRect();
        const x = t.clientX - r.left, y = t.clientY - r.top;
        ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(x, y); ctx.stroke();
        lastX = x; lastY = y;
    }

    window.clearSignature = function () {
        if (!ctx || !canvas) { initSignatureCanvas(); return; }
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        state.signatureData = null;
        const preview = document.getElementById('signaturePreview');
        if (preview) preview.classList.remove('active');
    };

    window.saveSignature = function () {
        if (!canvas) { alert('Signature canvas not ready.'); return; }
        const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        let hasContent = false;
        for (let i = 3; i < imgData.data.length; i += 4) { if (imgData.data[i] > 0) { hasContent = true; break; } }
        if (!hasContent) { alert('Please draw your signature first.'); return; }

        state.signatureData = canvas.toDataURL('image/png');
        const preview = document.getElementById('signaturePreview');
        const img = document.getElementById('signatureImage');
        if (img) img.src = state.signatureData;
        if (preview) preview.classList.add('active');
    };

    // ── Helpers ───────────────────────────────────────────────────
    function cleanMarkdown(text) {
        if (!text) return text;
        text = text.replace(/^#{1,6}\s*/gm, '');
        text = text.replace(/\*\*(.*?)\*\*/g, '$1');
        text = text.replace(/__(.*?)__/g, '$1');
        text = text.replace(/\*(?!\*)(.*?)\*/g, '$1');
        text = text.replace(/_(?!_)(.*?)_/g, '$1');
        text = text.replace(/^[\*\-\+]\s+/gm, '• ');
        text = text.replace(/^\d+\.\s+/gm, '');
        text = text.replace(/^[\-\*_]{3,}$/gm, '─'.repeat(40));
        text = text.replace(/[ \t]+/g, ' ');
        text = text.replace(/\n{3,}/g, '\n\n');
        return text.trim();
    }

})();
