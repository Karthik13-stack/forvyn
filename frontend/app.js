document.addEventListener('DOMContentLoaded', () => {

    const domainSelect = document.getElementById('domainSelect');
    const documentSelect = document.getElementById('documentSelect');
    const docHint = document.getElementById('docHint');
    const roleSelectionView = document.getElementById('roleSelectionView');
    const mainContainer = document.getElementById('mainContainer');
    const fieldsContainer = document.getElementById('fieldsContainer');
    const dynamicFields = document.getElementById('dynamicFields');
    const generateBtn = document.getElementById('generateBtn');
    const editor = document.getElementById('editor');
    const status = document.getElementById('status');

    const exportPdfBtn = document.getElementById('exportPdfBtn');
    const exportDocxBtn = document.getElementById('exportDocxBtn');

    // Sources UI elements
    const sourceFileInput = document.getElementById('sourceFileInput');
    const uploadSourceBtn = document.getElementById('uploadSourceBtn');
    const refreshSourcesBtn = document.getElementById('refreshSourcesBtn');
    const sourcesList = document.getElementById('sourcesList');
    const sourcePreview = document.getElementById('sourcePreview');

    const btnRewrite = document.getElementById('btnRewrite');

    const rewriteModal = document.getElementById('rewriteModal');
    const btnCancelRewrite = document.getElementById('btnCancelRewrite');
    const btnConfirmRewrite = document.getElementById('btnConfirmRewrite');
    const selectedClausePreview = document.getElementById('selectedClausePreview');
    const rewriteIntent = document.getElementById('rewriteIntent');

    // --- Stepper Navigation ---
    window.goToStep = function(step) {
        document.querySelectorAll('.step-section').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.step-item').forEach(s => s.classList.remove('active', 'completed'));

        const targetSection = document.getElementById('section' + step);
        if (targetSection) targetSection.classList.add('active');

        for(let i=1; i<=3; i++) {
            const tab = document.getElementById('step' + i + '-tab');
            if (tab) {
                if (i < step) tab.classList.add('completed');
                if (i === step) tab.classList.add('active');
            }
        }
    };

    const btnNextStep1 = document.getElementById('btnNextStep1');
    if (btnNextStep1) {
        btnNextStep1.addEventListener('click', () => {
            if (domainSelect.value && documentSelect.value) {
                window.goToStep(2);
            }
        });
    }

    // Load Domains
    console.log('Loading domains from /api/meta/domains...');
    fetch('/api/meta/domains')
        .then(res => {
            console.log('Response status:', res.status, res.statusText);
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then(domains => {
            console.log('Received domains:', domains);
            if (!Array.isArray(domains)) {
                console.error('Expected array but got:', domains);
                status.textContent = 'Error: Invalid response from server';
                status.style.color = '#ef4444';
                return;
            }
            if (domains.length === 0) {
                console.warn('No domains returned from API');
                status.textContent = 'No domains available. Check server logs.';
                status.style.color = '#f59e0b';
                return;
            }
            console.log(`Adding ${domains.length} domains to dropdown`);
            domains.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d;
                opt.textContent = d;
                domainSelect.appendChild(opt);
            });
            status.textContent = `Loaded ${domains.length} domain(s)`;
            status.style.color = '#10b981';
        })
        .catch(error => {
            console.error('Error loading domains:', error);
            status.textContent = `Error loading domains: ${error.message}`;
            status.style.color = '#ef4444';
        });

    // Load Documents
    domainSelect.addEventListener('change', async () => {
        if (!domainSelect.value) return;

        documentSelect.innerHTML = '<option disabled selected>Select Document...</option>';
        documentSelect.disabled = true;
        fieldsContainer.innerHTML = '';
        if (dynamicFields) dynamicFields.classList.add('hidden');
        if (generateBtn) generateBtn.disabled = true;
        status.textContent = `Loading documents for ${domainSelect.value}...`;
        status.style.color = '#2563eb';

        try {
            const res = await fetch(`/api/meta/${encodeURIComponent(domainSelect.value)}/documents`);
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
                throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
            }
            const docs = await res.json();

            if (!Array.isArray(docs)) {
                console.error('Expected array but got:', docs);
                status.textContent = 'Error: Invalid response format';
                status.style.color = '#ef4444';
                return;
            }

            if (docs.length === 0) {
                status.textContent = `No documents found for ${domainSelect.value}`;
                status.style.color = '#f59e0b';
                return;
            }

            docs.forEach(doc => {
                const opt = document.createElement('option');
                opt.value = doc;
                opt.textContent = doc;
                documentSelect.appendChild(opt);
            });

            documentSelect.disabled = false;
            if (docHint) docHint.classList.add('hidden');
            status.textContent = `Loaded ${docs.length} document type(s)`;
            status.style.color = '#10b981';
        } catch (error) {
            console.error('Error loading documents:', error);
            status.textContent = `Error: ${error.message}`;
            status.style.color = '#ef4444';
        }
    });

    // Load Schema
    documentSelect.addEventListener('change', async () => {
        if (!domainSelect.value || !documentSelect.value) return;

        status.textContent = 'Loading form fields...';
        status.style.color = '#2563eb';

        try {
            const res = await fetch(`/api/meta/${encodeURIComponent(domainSelect.value)}/${encodeURIComponent(documentSelect.value)}/schema`);
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
                throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
            }
            const schema = await res.json();

            if (!Array.isArray(schema)) {
                console.error('Expected array but got:', schema);
                status.textContent = 'Error: Invalid schema format';
                status.style.color = '#ef4444';
                return;
            }

            renderForm(schema);
            if (dynamicFields) dynamicFields.classList.remove('hidden');
            if (docHint) docHint.classList.add('hidden');
            if (btnNextStep1) btnNextStep1.disabled = false;
            if (generateBtn) generateBtn.disabled = false;

            if (schema.length === 0) {
                status.textContent = 'No form fields required for this document type';
                status.style.color = '#f59e0b';
            } else {
                status.textContent = `Ready to generate (${schema.length} field(s))`;
                status.style.color = '#10b981';
            }
        } catch (error) {
            console.error('Error loading schema:', error);
            status.textContent = `Error: ${error.message}`;
            status.style.color = '#ef4444';
        }
    });

    function renderForm(schema) {
        fieldsContainer.innerHTML = '';

        schema.forEach(field => {
            const wrap = document.createElement('div');
            wrap.className = 'form-group';

            const label = document.createElement('label');
            label.textContent = field.label + (field.required ? ' *' : '');

            let input;
            if (field.type === 'textarea') {
                input = document.createElement('textarea');
                input.rows = 4;
            } else {
                input = document.createElement('input');

                // Set input type based on field type
                if (field.type === 'date') {
                    input.type = 'date';
                } else if (field.type === 'number') {
                    input.type = 'number';
                    input.step = 'any';
                } else if (field.type === 'email') {
                    input.type = 'email';
                } else {
                    input.type = 'text';
                }
            }

            input.name = field.key;
            input.required = field.required;
            input.placeholder = `Enter ${field.label}`;

            // SYSTEM AUTO-FILLS
            if (field.key === 'year') {
                input.value = new Date().getFullYear();
                input.readOnly = true;
                input.classList.add('system-field');
            }

            wrap.appendChild(label);
            wrap.appendChild(input);
            fieldsContainer.appendChild(wrap);
        });
    }

    // --- Sources management ---
    async function loadSources() {
        sourcesList.innerHTML = 'Loading sources...';
        try {
            const res = await fetch('/api/sources/');
            if (!res.ok) throw new Error('Failed to load sources');
            const list = await res.json();
            renderSources(list || []);
        } catch (e) {
            sourcesList.innerHTML = `<div class="error">${e.message}</div>`;
        }
    }

    function renderSources(list) {
        if (!list.length) {
            sourcesList.innerHTML = '<div class="hint">No uploaded sources.</div>';
            return;
        }
        const ul = document.createElement('ul');
        ul.className = 'source-items';
        list.forEach(name => {
            const li = document.createElement('li');
            li.className = 'source-item';
            const label = document.createElement('span');
            label.textContent = name;

            const dl = document.createElement('div');
            dl.className = 'source-actions';

            const a = document.createElement('a');
            a.href = `/api/sources/download/${encodeURIComponent(name)}`;
            a.textContent = 'Download';
            a.className = 'secondary-link';
            a.target = '_blank';

            const del = document.createElement('button');
            del.textContent = 'Delete';
            del.className = 'secondary-btn btn-sm';
            del.addEventListener('click', async () => {
                if (!confirm(`Delete ${name}?`)) return;
                try {
                    const res = await fetch(`/api/sources/${encodeURIComponent(name)}`, { method: 'DELETE' });
                    if (res.status === 204) {
                        loadSources();
                    } else {
                        const err = await res.json().catch(() => ({ detail: 'Delete failed' }));
                        alert(err.detail || 'Delete failed');
                    }
                } catch (err) {
                    alert('Delete error: ' + (err.message || err));
                }
            });

            dl.appendChild(a);
            dl.appendChild(del);

            li.appendChild(label);
            li.appendChild(dl);
            ul.appendChild(li);
        });
        sourcesList.innerHTML = '';
        sourcesList.appendChild(ul);
    }

    // Client-side validation and upload
    const MAX_BYTES = 10 * 1024 * 1024; // 10 MB
    const ALLOWED_TYPES = [
        'application/pdf',
        'text/plain',
        'image/png',
        'image/jpeg',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];

    sourceFileInput.addEventListener('change', () => {
        sourcePreview.innerHTML = '';
        const file = sourceFileInput.files && sourceFileInput.files[0];
        if (!file) return;
        const info = document.createElement('div');
        info.className = 'source-info';
        info.innerHTML = `<strong>${file.name}</strong> (${Math.round(file.size / 1024)} KB) — ${file.type || 'unknown'}`;
        sourcePreview.appendChild(info);

        if (file.size > MAX_BYTES) {
            const warn = document.createElement('div');
            warn.className = 'error';
            warn.textContent = 'File is larger than 10MB and may be rejected by the server.';
            sourcePreview.appendChild(warn);
        }

        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.style.maxWidth = '240px';
            img.style.display = 'block';
            img.onload = () => URL.revokeObjectURL(img.src);
            sourcePreview.appendChild(img);
        } else if (file.type === 'text/plain') {
            const reader = new FileReader();
            reader.onload = (ev) => {
                const pre = document.createElement('pre');
                pre.textContent = String(ev.target.result).slice(0, 2000);
                sourcePreview.appendChild(pre);
            };
            reader.readAsText(file);
        } else if (file.type === 'application/pdf') {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(file);
            link.target = '_blank';
            link.textContent = 'Open PDF preview';
            sourcePreview.appendChild(link);
        } else {
            const note = document.createElement('div');
            note.className = 'hint';
            note.textContent = 'No inline preview available for this file type.';
            sourcePreview.appendChild(note);
        }
    });

    uploadSourceBtn.addEventListener('click', async () => {
        const file = sourceFileInput.files && sourceFileInput.files[0];
        if (!file) {
            alert('Choose a file to upload');
            return;
        }

        if (file.size > MAX_BYTES) {
            alert('File too large (max 10MB)');
            return;
        }
        if (ALLOWED_TYPES.length && !ALLOWED_TYPES.includes(file.type) && !file.name.match(/\.docx$/i)) {
            // allow docx by extension when content-type may be empty
            alert('Unsupported file type. Allowed: PDF, TXT, PNG, JPEG, DOCX');
            return;
        }

        const form = new FormData();
        form.append('file', file);
        uploadSourceBtn.disabled = true;
        uploadSourceBtn.textContent = 'Uploading...';
        try {
            const res = await fetch('/api/sources/upload', { method: 'POST', body: form });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Upload failed');
            sourceFileInput.value = '';
            sourcePreview.innerHTML = '';
            await loadSources();
            alert('Uploaded: ' + (data.name || file.name));
        } catch (e) {
            alert('Upload error: ' + e.message);
        }
        uploadSourceBtn.disabled = false;
        uploadSourceBtn.textContent = 'Upload';
    });

    refreshSourcesBtn.addEventListener('click', loadSources);

    // Initial load
    loadSources();

    // Generate
    generateBtn.addEventListener('click', async () => {
        const inputs = fieldsContainer.querySelectorAll('input, textarea');
        const formData = {};
        let valid = true;

        inputs.forEach(i => {
            if (i.required && !i.value.trim()) {
                i.style.borderColor = '#ef4444';
                valid = false;
            } else {
                i.style.borderColor = '#e2e8f0';
                formData[i.name] = i.value;
            }
        });

        if (!valid) {
            status.textContent = "Missing required legal details.";
            status.style.color = '#ef4444';
            return;
        }

        generateBtn.disabled = true;
        status.textContent = "Drafting document...";
        status.style.color = '#2563eb';

        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domain: domainSelect.value,
                    doc_type: documentSelect.value,
                    form_data: formData
                })
            });

            const data = await res.json();
            if (!res.ok) {
                status.textContent = "Error: " + (data.detail || res.statusText || "Generation failed");
                status.style.color = '#ef4444';
                generateBtn.disabled = false;
                return;
            }
            const content = data && (data.content != null) ? String(data.content) : "";
            const errorMessage = data && data.error_message ? String(data.error_message) : null;
            editor.value = content;

            if (errorMessage) {
                status.textContent = "Placeholder shown (generation failed): " + errorMessage;
                status.style.color = '#f59e0b';
            } else {
                status.textContent = "Draft generated successfully.";
                status.style.color = '#10b981';
                window.goToStep(3);
            }
        } catch (err) {
            status.textContent = "Error: " + (err.message || "Request failed");
            status.style.color = '#ef4444';
        }
        generateBtn.disabled = false;
    });



    // --- Floating Rewrite & Diff Logic ---
    const rewritePopover = document.getElementById('rewritePopover');
    const diffPopover = document.getElementById('diffPopover');
    const rewriteLang = document.getElementById('rewriteLang');
    const btnEmphasize = document.getElementById('btnEmphasize');
    const btnRewriteClarity = document.getElementById('btnRewriteClarity');
    const btnTranslate = document.getElementById('btnTranslate');
    const diffOriginal = document.getElementById('diffOriginal');
    const diffNew = document.getElementById('diffNew');
    const btnDiffAccept = document.getElementById('btnDiffAccept');
    const btnDiffReject = document.getElementById('btnDiffReject');

    let currentSelection = { start: 0, end: 0, text: '' };
    let proposedText = '';

    // Handle Editor Selection
    if (editor) {
        editor.addEventListener('mouseup', (e) => {
            // Give brief moment for browser selection to settle
            setTimeout(() => {
                const text = editor.value.substring(editor.selectionStart, editor.selectionEnd);
                if (text.trim().length > 0) {
                    currentSelection = { start: editor.selectionStart, end: editor.selectionEnd, text: text };
                    
                    const rect = editor.getBoundingClientRect();
                    let x = e.clientX - rect.left;
                    let y = e.clientY - rect.top;
                    
                    if (x < 160) x = 160;
                    if (y > rect.height - 120) y = rect.height - 120;
    
                    if(rewritePopover) {
                        rewritePopover.style.left = `${x}px`;
                        rewritePopover.style.top = `${y - 15}px`;
                        rewritePopover.classList.add('visible');
                    }
                    if(diffPopover) diffPopover.classList.remove('visible'); // hide diff if showing
                } else {
                    if(rewritePopover) rewritePopover.classList.remove('visible');
                }
            }, 50);
        });
    }

    // Hide popover when clicking elsewhere (but not inside popover)
    document.addEventListener('mousedown', (e) => {
        if (rewritePopover && !rewritePopover.contains(e.target) && e.target !== editor && diffPopover && !diffPopover.contains(e.target)) {
            rewritePopover.classList.remove('visible');
        }
    });

    async function handleRewriteAction(actionType) {
        if(rewritePopover) rewritePopover.classList.remove('visible');
        status.textContent = `Applying ${actionType}...`;
        status.style.color = '#2563eb';
        
        try {
            const res = await fetch('/api/rewrite-clause', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    selected_text: currentSelection.text, 
                    action_type: actionType,
                    target_language: rewriteLang.value
                })
            });

            if (!res.ok) throw new Error('Rewrite API failed');
            const data = await res.json();
            proposedText = data.rewritten_text;

            // Show diff
            if (diffOriginal) diffOriginal.textContent = currentSelection.text;
            if (diffNew) diffNew.textContent = proposedText;
            
            // Re-trigger placement roughly in top-center of editor
            if (diffPopover && editor) {
                const rect = editor.getBoundingClientRect();
                diffPopover.style.left = `${rect.width / 2}px`;
                diffPopover.style.top = `60px`; 
                diffPopover.classList.add('visible');
            }
            
            status.textContent = "Review proposed changes.";
            status.style.color = '#f59e0b';
            
        } catch (err) {
            status.textContent = "Error: " + err.message;
            status.style.color = '#ef4444';
        }
    }

    if (btnEmphasize) btnEmphasize.onclick = () => handleRewriteAction('emphasize');
    if (btnRewriteClarity) btnRewriteClarity.onclick = () => handleRewriteAction('rewrite');
    if (btnTranslate) btnTranslate.onclick = () => handleRewriteAction('translate');

    if (btnDiffAccept) {
        btnDiffAccept.onclick = () => {
            editor.setRangeText(proposedText, currentSelection.start, currentSelection.end, 'select');
            if(diffPopover) diffPopover.classList.remove('visible');
            status.textContent = "Changes applied.";
            status.style.color = '#10b981';
        };
    }
    
    if (btnDiffReject) {
        btnDiffReject.onclick = () => {
            if(diffPopover) diffPopover.classList.remove('visible');
            status.textContent = "Changes discarded.";
            status.style.color = '#64748b';
        };
    }

    // --- Export Logic ---
    async function handleExport(format) {
        const content = editor.value.trim();
        if (!content) {
            alert('Draft editor is empty. Generate a document first.');
            return;
        }

        const filename = (documentSelect.value || 'legal_document').replace(/\s+/g, '_');
        const endpoint = `/api/export/${format}`;

        status.textContent = `Exporting ${format.toUpperCase()}...`;
        status.style.color = '#2563eb';

        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content, filename })
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(data.detail || 'Export failed');
            }

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}.${format === 'docx' ? 'docx' : 'pdf'}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            status.textContent = `${format.toUpperCase()} exported successfully.`;
            status.style.color = '#10b981';
        } catch (err) {
            console.error(`Export ${format} error:`, err);
            status.textContent = `Export failed: ${err.message}`;
            status.style.color = '#ef4444';
        }
    }

    exportPdfBtn.addEventListener('click', () => handleExport('pdf'));
    exportDocxBtn.addEventListener('click', () => handleExport('docx'));

});
