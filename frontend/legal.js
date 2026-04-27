// legal.js - Handles frontend logic for Forvyn Legal Tools

// 1. IPC to BNS Mapping
async function convertSection() {
    const input = document.getElementById('sectionInput');
    const loading = document.getElementById('loadingState');
    const error = document.getElementById('errorState');
    const result = document.getElementById('resultContainer');
    
    if (!input || !input.value.trim()) return;

    // Reset states
    error.classList.add('hidden');
    result.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        const response = await fetch('/api/ipc-to-bns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ipc_section: input.value.trim() })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to fetch mapping');
        }

        // Populate results
        document.getElementById('ipcNum').textContent = data.ipc_section || 'N/A';
        document.getElementById('ipcTitle').textContent = data.ipc_title || 'Unknown';
        
        document.getElementById('bnsNum').textContent = data.bns_section || 'N/A';
        document.getElementById('bnsTitle').textContent = data.bns_title || 'Repealed/Unknown';
        
        document.getElementById('changesSummary').textContent = data.changes_summary || data.notes || '';

        // Status Badge
        const badge = document.getElementById('statusBadge');
        badge.textContent = data.status.replace('_', ' ').toUpperCase();
        badge.className = '';
        if (data.status === 'direct_mapping') badge.classList.add('status-direct');
        else if (data.status === 'repealed') badge.classList.add('status-repealed');
        else badge.classList.add('status-partial');

        result.classList.remove('hidden');
    } catch (err) {
        document.getElementById('errorText').textContent = err.message;
        error.classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
    }
}

// 2. Summarize Judgment
async function summarizeJudgment() {
    const textInput = document.getElementById('judgmentInput');
    const typeInput = document.getElementById('summaryType');
    
    if (!textInput || !textInput.value.trim()) {
        alert("Please paste the judgment text.");
        return;
    }

    const btn = document.getElementById('summarizeBtn');
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const resultContent = document.getElementById('resultContent');

    btn.disabled = true;
    emptyState.classList.add('hidden');
    errorState.classList.add('hidden');
    resultContent.classList.add('hidden');
    loadingState.classList.remove('hidden');

    try {
        const response = await fetch('/api/summarize-judgment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                judgement_text: textInput.value.trim(),
                summary_type: typeInput.value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to summarize judgment');
        }

        // Populate Top Metadata
        document.getElementById('caseTitle').textContent = data.metadata?.case_title || 'Unknown Case';
        document.getElementById('caseCourt').textContent = data.metadata?.court || 'Unknown Court';
        document.getElementById('caseDate').textContent = data.metadata?.date || 'Unknown Date';
        document.getElementById('caseJudges').textContent = (data.metadata?.judges || []).join(', ') || 'Unknown';

        // Populate Sections dynamically
        const sectionsContainer = document.getElementById('summarySections');
        sectionsContainer.innerHTML = '';

        const createSection = (title, content) => {
            if (!content || (Array.isArray(content) && content.length === 0)) return;
            
            const div = document.createElement('div');
            div.className = 'summary-section';
            
            const h4 = document.createElement('h4');
            h4.textContent = title;
            div.appendChild(h4);

            if (Array.isArray(content)) {
                const ul = document.createElement('ul');
                content.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = item;
                    ul.appendChild(li);
                });
                div.appendChild(ul);
            } else {
                const p = document.createElement('p');
                p.textContent = content;
                div.appendChild(p);
            }

            sectionsContainer.appendChild(div);
        };

        if (data.summary) {
            createSection('Brief Summary', data.summary.brief);
            createSection('Facts of the Case', data.summary.facts);
            createSection('Issues Framed', data.summary.issues);
            
            if (data.summary.arguments) {
                createSection('Petitioner Arguments', data.summary.arguments.petitioner);
                createSection('Respondent Arguments', data.summary.arguments.respondent);
            }
            
            createSection('Court Observations', data.summary.observations);
            createSection('Ratio Decidendi', data.summary.ratio);
            createSection('The Holding / Order', data.summary.holding);
        }

        if (data.analysis) {
            createSection('Key Takeaways', data.analysis.key_takeaways);
            createSection('Practical Implications', data.analysis.implications);
        }

        resultContent.classList.remove('hidden');
    } catch (err) {
        document.getElementById('errorText').textContent = err.message;
        errorState.classList.remove('hidden');
    } finally {
        loadingState.classList.add('hidden');
        btn.disabled = false;
    }
}

// 3. Explain Legal Provision
async function explainProvision() {
    const textInput = document.getElementById('provisionInput');
    
    if (!textInput || !textInput.value.trim()) {
        alert("Please paste the provision text.");
        return;
    }

    const btn = document.getElementById('explainBtn');
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const resultContent = document.getElementById('resultContent');

    btn.disabled = true;
    emptyState.classList.add('hidden');
    errorState.classList.add('hidden');
    resultContent.classList.add('hidden');
    loadingState.classList.remove('hidden');

    try {
        const response = await fetch('/api/explain-provision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provision_text: textInput.value.trim() })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to explain provision');
        }

        document.getElementById('explainSummary').textContent = data.summary || 'Summary unavailable.';
        
        const ptList = document.getElementById('explainPoints');
        ptList.innerHTML = '';
        (data.key_points || []).forEach(pt => {
            const li = document.createElement('li');
            li.textContent = pt;
            ptList.appendChild(li);
        });

        const exList = document.getElementById('explainExamples');
        exList.innerHTML = '';
        (data.examples || []).forEach(ex => {
            const li = document.createElement('li');
            li.textContent = ex;
            exList.appendChild(li);
        });

        resultContent.classList.remove('hidden');
    } catch (err) {
        document.getElementById('errorText').textContent = err.message;
        errorState.classList.remove('hidden');
    } finally {
        loadingState.classList.add('hidden');
        btn.disabled = false;
    }
}

// 4. Analyze Legal Risks
function initRiskUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const documentInput = document.getElementById('documentInput');

    if (!dropZone || !fileInput || !documentInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) readRiskFile(file);
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) readRiskFile(file);
    });
}

function readRiskFile(file) {
    if (!file.name.match(/\.(txt|text)$/i)) {
        alert('Please upload a .txt file.');
        return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
        const documentInput = document.getElementById('documentInput');
        const dropZone = document.getElementById('dropZone');
        documentInput.value = ev.target.result;
        dropZone.querySelector('p').innerHTML = `<strong>${file.name}</strong> loaded (${Math.round(file.size / 1024)} KB)`;
    };
    reader.readAsText(file);
}

async function analyzeRisks() {
    const documentInput = document.getElementById('documentInput');
    const content = documentInput.value.trim();
    if (!content) {
        alert('Please paste or upload a legal document first.');
        return;
    }

    const btn = document.getElementById('analyzeBtn');
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const resultContent = document.getElementById('resultContent');

    btn.disabled = true;
    emptyState.classList.add('hidden');
    errorState.classList.add('hidden');
    resultContent.classList.add('hidden');
    loadingState.classList.remove('hidden');

    try {
        const response = await fetch('/api/analyze-risks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Risk analysis failed');
        }

        const risks = (data.risks || []).sort((a, b) => {
            if (a.risk_level !== b.risk_level) {
                return a.risk_level === 'high' ? -1 : 1;
            }
            return a.start_index - b.start_index;
        });

        renderRiskResults(risks);
        resultContent.classList.remove('hidden');
    } catch (err) {
        document.getElementById('errorText').textContent = err.message;
        errorState.classList.remove('hidden');
    } finally {
        loadingState.classList.add('hidden');
        btn.disabled = false;
    }
}

function renderRiskResults(risks) {
    const highCount = risks.filter(r => r.risk_level === 'high').length;
    const mediumCount = risks.filter(r => r.risk_level === 'medium').length;

    const summaryHtml = `
        <div class="risk-stat total">
            <div class="stat-value">${risks.length}</div>
            <div class="stat-label">Total Risks</div>
        </div>
        <div class="risk-stat high">
            <div class="stat-value">${highCount}</div>
            <div class="stat-label">Needs Review</div>
        </div>
        <div class="risk-stat medium">
            <div class="stat-value">${mediumCount}</div>
            <div class="stat-label">Medium Risk</div>
        </div>
    `;
    document.getElementById('riskSummary').innerHTML = summaryHtml;

    const listEl = document.getElementById('risksList');
    if (risks.length === 0) {
        listEl.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--success);">
                <div style="font-size: 32px; margin-bottom: 12px;">✅</div>
                <p style="font-size: 16px; font-weight: 500;">No risks detected</p>
                <p style="font-size: 14px; color: var(--text-muted);">The document appears to have no flagged clauses.</p>
            </div>
        `;
        return;
    }

    listEl.innerHTML = risks.map((risk) => `
        <div class="risk-item ${risk.risk_level}">
            <span class="risk-badge ${risk.risk_level}">
                ${risk.risk_level === 'high' ? '🔴 Needs Human Review' : '🟠 Medium Risk'}
            </span>
            <div class="risk-snippet">"${escapeRiskHtml(risk.snippet || '')}"</div>
            <div class="risk-reason">${escapeRiskHtml(risk.reason || 'Potential risk identified')}</div>
        </div>
    `).join('');
}

function escapeRiskHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Generic file upload initializer for any drop zone → textarea pair
function initGenericUpload(dropZoneId, fileInputId, textareaId) {
    const dropZone = document.getElementById(dropZoneId);
    const fileInput = document.getElementById(fileInputId);
    const textarea = document.getElementById(textareaId);

    if (!dropZone || !fileInput || !textarea) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) readFileIntoTextarea(file, textarea, dropZone);
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) readFileIntoTextarea(file, textarea, dropZone);
    });
}

function readFileIntoTextarea(file, textarea, dropZone) {
    const name = file.name.toLowerCase();

    if (name.endsWith('.txt') || name.endsWith('.text')) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            textarea.value = ev.target.result;
            dropZone.querySelector('p').innerHTML =
                `<strong>${file.name}</strong> loaded (${Math.round(file.size / 1024)} KB)`;
        };
        reader.readAsText(file);
        return;
    }

    if (name.endsWith('.pdf')) {
        const reader = new FileReader();
        reader.onload = async (ev) => {
            dropZone.querySelector('p').innerHTML =
                `<strong>${file.name}</strong> — extracting text...`;
            try {
                // Try server-side extraction via sources upload
                const form = new FormData();
                form.append('file', file);
                const res = await fetch('/api/sources/upload', { method: 'POST', body: form });
                if (res.ok) {
                    const data = await res.json();
                    if (data.extracted_text) {
                        textarea.value = data.extracted_text;
                        dropZone.querySelector('p').innerHTML =
                            `<strong>${file.name}</strong> loaded (${Math.round(file.size / 1024)} KB)`;
                        return;
                    }
                }
            } catch (e) { /* fallback below */ }
            // Fallback: inform user to paste manually
            dropZone.querySelector('p').innerHTML =
                `<strong>${file.name}</strong> — PDF text extraction not available. Please paste text manually.`;
        };
        reader.readAsArrayBuffer(file);
        return;
    }

    if (name.endsWith('.docx')) {
        const reader = new FileReader();
        reader.onload = async (ev) => {
            dropZone.querySelector('p').innerHTML =
                `<strong>${file.name}</strong> — extracting text...`;
            try {
                const form = new FormData();
                form.append('file', file);
                const res = await fetch('/api/sources/upload', { method: 'POST', body: form });
                if (res.ok) {
                    const data = await res.json();
                    if (data.extracted_text) {
                        textarea.value = data.extracted_text;
                        dropZone.querySelector('p').innerHTML =
                            `<strong>${file.name}</strong> loaded (${Math.round(file.size / 1024)} KB)`;
                        return;
                    }
                }
            } catch (e) { /* fallback below */ }
            dropZone.querySelector('p').innerHTML =
                `<strong>${file.name}</strong> — DOCX text extraction not available. Please paste text manually.`;
        };
        reader.readAsArrayBuffer(file);
        return;
    }

    alert('Unsupported file type. Please upload a .txt, .pdf, or .docx file.');
}

// Auto-init all file uploads when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Analyze Risks page
    initRiskUpload();
    // Explain Legal Provision page
    initGenericUpload('explainDropZone', 'explainFileInput', 'provisionInput');
    // Summarize Judgment page
    initGenericUpload('summarizeDropZone', 'summarizeFileInput', 'judgmentInput');
});
