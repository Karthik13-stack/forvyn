(function () {
    'use strict';

    const uploadForm = document.getElementById('sourceUploadForm');
    const sourceFile = document.getElementById('sourceFile');
    const sourceType = document.getElementById('sourceType');
    const sourceCategory = document.getElementById('sourceCategory');
    const sourceNotes = document.getElementById('sourceNotes');
    const sourceList = document.getElementById('sourceList');
    const sourceListEmpty = document.getElementById('sourceListEmpty');
    const sourceSearch = document.getElementById('sourceSearch');
    const sourceCountPill = document.getElementById('sourceCountPill');
    const detailEmpty = document.getElementById('sourceDetailEmpty');
    const detailView = document.getElementById('sourceDetailView');
    const detailName = document.getElementById('detailName');
    const detailMeta = document.getElementById('detailMeta');
    const detailTags = document.getElementById('detailTags');
    const detailPreview = document.getElementById('detailPreview');
    const detailNotes = document.getElementById('detailNotes');
    const saveNotesBtn = document.getElementById('saveNotesBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const deleteBtn = document.getElementById('deleteBtn');

    let sources = [];
    let selectedSource = null;

    function formatBytes(bytes) {
        if (!bytes && bytes !== 0) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB'];
        let value = bytes;
        let idx = 0;
        while (value >= 1024 && idx < units.length - 1) {
            value /= 1024;
            idx += 1;
        }
        return `${value.toFixed(value >= 10 || idx === 0 ? 0 : 1)} ${units[idx]}`;
    }

    async function fetchJson(url, options = {}) {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (response.status === 204) {
            return null;
        }
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }
        return data;
    }

    function renderLibrary() {
        const query = sourceSearch.value.trim().toLowerCase();
        const filtered = query
            ? sources.filter((item) => {
                return [item.original_name, item.stored_name, item.category, item.notes, item.source_type]
                    .join(' ')
                    .toLowerCase()
                    .includes(query);
            })
            : sources;

        sourceCountPill.textContent = `${sources.length} sources`;
        sourceList.innerHTML = '';

        if (!filtered.length) {
            sourceListEmpty.classList.remove('hidden');
            sourceListEmpty.textContent = query ? 'No sources match your search.' : 'No sources uploaded yet.';
            return;
        }

        sourceListEmpty.classList.add('hidden');

        filtered.forEach((item) => {
            const card = document.createElement('button');
            card.type = 'button';
            card.className = `source-item ${selectedSource && selectedSource.stored_name === item.stored_name ? 'active' : ''}`;
            card.innerHTML = `
                <div class="source-item-title">${escapeHtml(item.original_name || item.stored_name)}</div>
                <div class="source-item-meta">${escapeHtml(item.category || 'Uncategorized')} · ${escapeHtml(item.source_type || 'General')}
                </div>
                <div class="source-item-foot">${formatBytes(item.size_bytes || 0)} · ${new Date(item.created_at || Date.now()).toLocaleDateString()}</div>
            `;
            card.addEventListener('click', () => selectSource(item.stored_name));
            sourceList.appendChild(card);
        });
    }

    async function loadSources() {
        sources = await fetchJson('/api/sources');
        if (!Array.isArray(sources)) {
            sources = [];
        }
        if (selectedSource) {
            const refreshed = sources.find((item) => item.stored_name === selectedSource.stored_name);
            if (refreshed) {
                selectedSource = refreshed;
            } else {
                selectedSource = null;
            }
        }
        renderLibrary();
        if (selectedSource) {
            renderDetail(selectedSource);
        }
    }

    function renderDetail(item) {
        detailEmpty.classList.add('hidden');
        detailView.classList.remove('hidden');
        detailName.textContent = item.original_name || item.stored_name;
        detailMeta.textContent = `${formatBytes(item.size_bytes || 0)} · Uploaded ${new Date(item.created_at || Date.now()).toLocaleString()}`;
        detailTags.innerHTML = `
            <span class="pill">${escapeHtml(item.category || 'Uncategorized')}</span>
            <span class="pill">${escapeHtml(item.source_type || 'General')}</span>
        `;
        detailNotes.value = item.notes || '';
        downloadBtn.href = `/api/sources/download/${encodeURIComponent(item.stored_name)}`;
        detailPreview.textContent = 'Loading preview...';
        fetchJson(`/api/sources/${encodeURIComponent(item.stored_name)}/preview`)
            .then((preview) => {
                detailPreview.textContent = preview.preview || 'No preview available.';
            })
            .catch(() => {
                detailPreview.textContent = 'Preview unavailable for this file type.';
            });
        deleteBtn.onclick = async () => {
            if (!confirm(`Delete ${item.original_name || item.stored_name}?`)) return;
            await fetchJson(`/api/sources/${encodeURIComponent(item.stored_name)}`, { method: 'DELETE' });
            selectedSource = null;
            detailEmpty.classList.remove('hidden');
            detailView.classList.add('hidden');
            await loadSources();
        };
        saveNotesBtn.onclick = async () => {
            const updated = await fetchJson(`/api/sources/${encodeURIComponent(item.stored_name)}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    notes: detailNotes.value,
                    category: item.category || '',
                    source_type: item.source_type || '',
                }),
            });
            selectedSource = updated;
            await loadSources();
        };
    }

    async function selectSource(name) {
        const item = await fetchJson(`/api/sources/${encodeURIComponent(name)}`);
        selectedSource = item;
        renderLibrary();
        renderDetail(item);
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const file = sourceFile.files[0];
        if (!file) {
            alert('Choose a file first.');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('category', sourceCategory.value.trim());
            formData.append('notes', sourceNotes.value.trim());
            formData.append('source_type', sourceType.value.trim());

            const response = await fetch('/api/sources/upload', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Upload failed');
            }
            uploadForm.reset();
            await loadSources();
            await selectSource(data.stored_name);
        } catch (error) {
            alert(error.message || 'Upload failed');
        }
    });

    sourceSearch.addEventListener('input', renderLibrary);

    loadSources().catch((error) => {
        sourceListEmpty.textContent = error.message || 'Could not load sources.';
    });
})();
