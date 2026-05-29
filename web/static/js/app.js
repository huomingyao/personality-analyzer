/**
 * Psyche KB - Personality Analysis System
 * Light Theme Frontend Application
 */

// ==================== STATE ====================
const AppState = {
    currentSection: 'analyze',
    selectedFrameworks: ['liangebodwo-mirror'],
    selectedKb: null,
    isAnalyzing: false
};

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initFrameworkCards();
    loadKbList();
    loadSrcKbSelect();
    loadSessions();
});

// ==================== NAVIGATION ====================
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            switchSection(section);

            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function switchSection(name) {
    AppState.currentSection = name;
    document.querySelectorAll('.section-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(`section-${name}`)?.classList.add('active');

    if (name === 'knowledge') loadKbList();
    if (name === 'sessions') loadSessions();
}

// ==================== FRAMEWORK CARDS ====================
function initFrameworkCards() {
    document.querySelectorAll('.fw-card').forEach(card => {
        card.addEventListener('click', (e) => {
            const fw = card.dataset.framework;

            if (card.classList.contains('active')) {
                // Already selected: only deselect if multi-selecting (Ctrl+Click)
                if (e.ctrlKey || e.metaKey) {
                    card.classList.remove('active');
                    AppState.selectedFrameworks = AppState.selectedFrameworks.filter(f => f !== fw);
                }
                // Without Ctrl, keep selected (no-op for single click on active card)
            } else {
                if (e.ctrlKey || e.metaKey) {
                    // Ctrl+Click: add to selection
                    card.classList.add('active');
                    if (!AppState.selectedFrameworks.includes(fw)) {
                        AppState.selectedFrameworks.push(fw);
                    }
                } else {
                    // Normal click: single-select, deselect all others first
                    document.querySelectorAll('.fw-card').forEach(c => c.classList.remove('active'));
                    card.classList.add('active');
                    AppState.selectedFrameworks = [fw];
                }
            }
            updateFwCount();
        });
    });
}

function updateFwCount() {
    const el = document.getElementById('selectedFwCount');
    if (el) el.textContent = `已选 ${AppState.selectedFrameworks.length} 个框架`;
}

// ==================== ANALYZE ====================
async function doAnalyze() {
    if (AppState.isAnalyzing) return;

    const target = document.getElementById('targetKb').value.trim();
    const kbName = document.getElementById('srcKbName').value;
    const fileName = document.getElementById('srcFileName').value;
    const kbSearch = document.getElementById('srcSearch').value.trim();

    if (!kbName) { showToast('请选择档案库', 'error'); return; }
    if (!target) { showToast('请提供分析对象名称', 'error'); return; }
    if (AppState.selectedFrameworks.length === 0) { showToast('请选择至少一个分析框架', 'error'); return; }

    const enableCritic = document.getElementById('enableCritic').checked;

    const payload = { target, kb_name: kbName, critic: enableCritic };
    if (fileName) {
        payload.kb_filename = fileName;
    } else if (kbSearch) {
        payload.kb_search = kbSearch;
    }

    const multi = AppState.selectedFrameworks.length > 1;
    if (multi) {
        payload.frameworks = AppState.selectedFrameworks;
    } else {
        payload.framework = AppState.selectedFrameworks[0] || 'liangebodwo-mirror';
    }

    AppState.isAnalyzing = true;
    const overlay = document.getElementById('loadingOverlay');
    const btn = document.getElementById('btnAnalyze');
    const stepEl = document.getElementById('loadingStep');
    const stepsEl = document.getElementById('loadingSteps');

    overlay.style.display = 'flex';
    btn.disabled = true;
    stepEl.textContent = '正在准备...';
    stepsEl.innerHTML = '';

    try {
        const endpoint = multi ? '/api/analyze/multi' : '/api/analyze/stream';
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (multi) {
            // Multi-framework: regular JSON response
            const data = await res.json();
            const card = document.getElementById('resultCard');
            const content = document.getElementById('resultContent');
            card.style.display = 'block';
            if (data.success) {
                content.innerHTML = formatResult(data.data.result);
                document.getElementById('resultTime').textContent = new Date().toLocaleTimeString('zh-CN');
                card.scrollIntoView({ behavior: 'smooth', block: 'start' });
                showToast('分析完成', 'success');
            } else {
                content.innerHTML = `<div style="color: var(--accent-error)">${escapeHtml(data.message)}</div>`;
                showToast(data.message, 'error');
            }
        } else {
            // Single framework: streaming NDJSON (one JSON per line)
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let finalResult = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed || trimmed === ' ') continue;

                    try {
                        const event = JSON.parse(trimmed);
                        switch (event.type) {
                            case 'init':
                                stepEl.textContent = `分析对象: ${event.target}`;
                                if (event.kb_name) {
                                    const d = document.createElement('div');
                                    d.className = 'loading-step-item done';
                                    d.textContent = `知识库: ${event.kb_name}`;
                                    stepsEl.appendChild(d);
                                }
                                break;
                            case 'progress':
                                stepEl.textContent = event.message;
                                const prev = stepsEl.lastElementChild;
                                if (prev) prev.className = 'loading-step-item done';
                                const d = document.createElement('div');
                                d.className = 'loading-step-item loading';
                                d.textContent = event.message;
                                stepsEl.appendChild(d);
                                stepsEl.scrollTop = stepsEl.scrollHeight;
                                break;
                            case 'complete':
                                finalResult = event.result;
                                const last = stepsEl.lastElementChild;
                                if (last) last.className = 'loading-step-item done';
                                break;
                            case 'error':
                                finalResult = { error: event.message };
                                break;
                        }
                    } catch (e) {
                        // skip malformed lines
                    }
                }
            }

            const card = document.getElementById('resultCard');
            const content = document.getElementById('resultContent');
            card.style.display = 'block';

            if (finalResult && !finalResult.error) {
                content.innerHTML = formatResult(finalResult);
                document.getElementById('resultTime').textContent = new Date().toLocaleTimeString('zh-CN');
                card.scrollIntoView({ behavior: 'smooth', block: 'start' });
                showToast('分析完成', 'success');
            } else {
                const errMsg = finalResult?.error || '分析失败';
                content.innerHTML = `<div style="color: var(--accent-error)">${escapeHtml(errMsg)}</div>`;
                showToast(errMsg, 'error');
            }
        }
    } catch (e) {
        const card = document.getElementById('resultCard');
        const content = document.getElementById('resultContent');
        card.style.display = 'block';
        content.innerHTML = `<div style="color: var(--accent-error)">请求失败: ${escapeHtml(e.message)}</div>`;
        showToast('请求失败: ' + e.message, 'error');
    } finally {
        AppState.isAnalyzing = false;
        overlay.style.display = 'none';
        btn.disabled = false;
    }
}

function formatResult(text) {
    if (!text) return '';
    let html = escapeHtml(text);

    html = html.replace(/^#{1,6}\s+(.+)$/gm, (m, t) => {
        const l = m.match(/^#+/)[0].length;
        return `<h${l}>${t}</h${l}>`;
    });
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');
    html = html.replace(/^>\s*(.+)$/gm, '<blockquote>$1</blockquote>');
    html = html.replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*?<\/li>\n?)+/g, m => `<ul>${m}</ul>`);
    html = html.replace(/\n/g, '<br>');

    return html;
}

function escapeHtml(t) {
    const d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
}

function copyResult() {
    const text = document.getElementById('resultContent').innerText;
    navigator.clipboard.writeText(text).then(() => showToast('已复制', 'success'))
        .catch(() => showToast('复制失败', 'error'));
}

async function saveSession() {
    const target = document.getElementById('targetKb').value.trim();
    const kbName = document.getElementById('srcKbName').value;
    const framework = AppState.selectedFrameworks[0];

    if (!target) { showToast('请先进行分析', 'error'); return; }

    try {
        const res = await fetch('/api/session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target, kb_name: kbName, framework })
        });
        const data = await res.json();
        if (data.success) {
            showToast('会话已保存', 'success');
            loadSessions();
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('保存失败', 'error');
    }
}

// ==================== KNOWLEDGE BASE ====================
async function loadKbList() {
    try {
        const res = await fetch('/api/kb/list');
        const data = await res.json();
        const grid = document.getElementById('kbGrid');

        if (data.success && data.data.length > 0) {
            grid.innerHTML = data.data.map(kb => `
                <div class="kb-card ${AppState.selectedKb === kb.name ? 'selected' : ''}"
                     onclick="selectKb('${escapeHtml(kb.name)}')">
                    <div class="kb-name">${escapeHtml(kb.name)}</div>
                    <div class="kb-info">${kb.file_count} 个文件</div>
                    <button class="kb-delete-btn" onclick="event.stopPropagation(); deleteKb('${escapeHtml(kb.name)}')" title="删除档案库">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            `).join('');
            fillSelect('uploadKb', data.data);
        } else {
            grid.innerHTML = `
                <div class="kb-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                    </svg>
                    <p>暂无档案库</p>
                </div>`;
        }
    } catch (e) {
        document.getElementById('kbGrid').innerHTML = '<div class="kb-empty"><p>加载失败</p></div>';
    }
}

async function deleteKb(name) {
    if (!confirm(`确定删除档案库「${name}」吗？\n\n此操作将永久删除所有文件和索引，不可恢复。`)) return;

    try {
        const res = await fetch('/api/kb/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            if (AppState.selectedKb === name) AppState.selectedKb = null;
            loadKbList();
            loadSrcKbSelect();
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

async function loadSrcKbSelect() {
    try {
        const res = await fetch('/api/kb/list');
        const data = await res.json();
        if (data.success) fillSelect('srcKbName', data.data);
    } catch (e) {}
}

function fillSelect(id, list) {
    const sel = document.getElementById(id);
    if (!sel) return;
    const val = sel.value;
    sel.innerHTML = '<option value="">-- 请选择 --</option>' +
        list.map(kb => `<option value="${escapeHtml(kb.name)}">${escapeHtml(kb.name)} (${kb.file_count}个文件)</option>`).join('');
    if (val) sel.value = val;
}

function selectKb(name) {
    AppState.selectedKb = name;
    document.querySelectorAll('.kb-card').forEach(c => c.classList.remove('selected'));
    document.querySelectorAll('.kb-card').forEach(c => {
        if (c.querySelector('.kb-name')?.textContent === name) c.classList.add('selected');
    });
    const uploadKb = document.getElementById('uploadKb');
    if (uploadKb) uploadKb.value = name;
    onUploadKbChange();
    loadKnowledgeTree(name);
}

async function onUploadKbChange() {
    const name = document.getElementById('uploadKb').value;
    document.getElementById('uploadArea').style.display = name ? 'block' : 'none';
    clearSelectedFile();
    if (name) { await loadFiles(name); loadKnowledgeTree(name); }
}

async function onSrcKbChange() {
    const name = document.getElementById('srcKbName').value;
    const sel = document.getElementById('srcFileName');
    if (!name) { sel.innerHTML = '<option value="">-- 请先选档案库 --</option>'; return; }

    try {
        const res = await fetch('/api/kb/files?name=' + encodeURIComponent(name));
        const data = await res.json();
        if (data.success && data.data.length > 0) {
            sel.innerHTML = '<option value="">-- 自动浏览全部 --</option>' +
                data.data.map(f => `<option value="${escapeHtml(f.name)}">${escapeHtml(f.name)}</option>`).join('');
        } else {
            sel.innerHTML = '<option value="">-- 自动浏览全部（无文件）--</option>';
        }
    } catch (e) {
        sel.innerHTML = '<option value="">-- 加载失败 --</option>';
    }
}

async function loadFiles(kbName) {
    try {
        const res = await fetch('/api/kb/files?name=' + encodeURIComponent(kbName));
        const data = await res.json();
        const el = document.getElementById('fileList');

        if (data.success && data.data.length > 0) {
            el.innerHTML = data.data.map(f => `
                <div class="file-item">
                    <div class="file-name">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                        </svg>
                        ${escapeHtml(f.name)}
                    </div>
                    <span class="file-size">${formatBytes(f.size)}</span>
                </div>
            `).join('');
        } else {
            el.innerHTML = '<div class="files-empty">暂无文件</div>';
        }
    } catch (e) {
        document.getElementById('fileList').innerHTML = '<div class="files-empty">加载失败</div>';
    }
}

async function loadKnowledgeTree(kbName) {
    try {
        const res = await fetch('/api/kb/tree?name=' + encodeURIComponent(kbName));
        const data = await res.json();
        if (data.success && data.data.index_md) {
            document.getElementById('treeCard').style.display = 'block';
            document.getElementById('knowledgeTree').textContent = data.data.index_md;
        } else {
            document.getElementById('treeCard').style.display = 'none';
        }
    } catch (e) {
        document.getElementById('treeCard').style.display = 'none';
    }
}

// ==================== CRUD ====================
function toggleCreateForm() {
    const form = document.getElementById('createForm');
    form.style.display = form.style.display === 'none' ? 'flex' : 'none';
    if (form.style.display === 'flex') document.getElementById('newKbName').focus();
}

async function createKb() {
    const name = document.getElementById('newKbName').value.trim();
    if (!name) { showToast('请输入名称', 'error'); return; }

    try {
        const res = await fetch('/api/kb/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById('newKbName').value = '';
            toggleCreateForm();
            loadKbList();
            showToast('档案库创建成功', 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('创建失败', 'error');
    }
}

async function uploadFile() {
    const kbName = document.getElementById('uploadKb').value;
    const fileInput = document.getElementById('fileInput');

    if (!kbName) { showToast('请选择档案库', 'error'); return; }
    if (!fileInput.files[0]) { showToast('请选择文件', 'error'); return; }

    const fd = new FormData();
    fd.append('file', fileInput.files[0]);
    fd.append('kb_name', kbName);

    try {
        const res = await fetch('/api/kb/upload', { method: 'POST', body: fd });
        const data = await res.json();
        const el = document.getElementById('uploadMsg');

        if (data.success) {
            const info = data.pipeline ? ` (分块: ${data.pipeline.chunk_count})` : '';
            el.innerHTML = `<div class="upload-msg success">${data.message}${info}</div>`;
            fileInput.value = '';
            clearSelectedFile();
            loadFiles(kbName);
            loadKnowledgeTree(kbName);
            loadKbList();
            showToast('上传成功', 'success');
        } else {
            el.innerHTML = `<div class="upload-msg error">${data.message}</div>`;
            showToast(data.message, 'error');
        }
    } catch (e) {
        document.getElementById('uploadMsg').innerHTML = '<div class="upload-msg error">上传失败</div>';
        showToast('上传失败', 'error');
    }
}

// ==================== SESSIONS ====================
async function loadSessions() {
    try {
        const res = await fetch('/api/session');
        const data = await res.json();
        const container = document.getElementById('sessionsList');
        const countEl = document.getElementById('sessionCount');

        if (data.success && data.data && data.data.length > 0) {
            if (countEl) countEl.textContent = `${data.data.length} 条`;
            container.innerHTML = data.data.map(s => `
                <div class="session-item">
                    <div class="session-info">
                        <div class="session-target">${escapeHtml(s.target || '未命名')}</div>
                        <div class="session-meta">
                            ${escapeHtml(s.framework || '默认')} · ${new Date(s.created_at).toLocaleString('zh-CN')}
                        </div>
                    </div>
                    <div class="session-actions">
                        <button class="btn-ghost btn-sm" onclick="loadSession('${s.id}')">加载</button>
                        <button class="btn-ghost btn-sm" onclick="deleteSession('${s.id}')">删除</button>
                    </div>
                </div>
            `).join('');
        } else {
            if (countEl) countEl.textContent = '0 条';
            container.innerHTML = `
                <div class="sessions-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    <p>暂无会话记录</p>
                </div>`;
        }
    } catch (e) {
        console.error('Load sessions failed:', e);
    }
}

async function loadSession(id) {
    try {
        const res = await fetch(`/api/session?id=${encodeURIComponent(id)}`);
        const data = await res.json();
        if (data.success && data.data) {
            document.getElementById('targetKb').value = data.data.target || '';
            if (data.data.kb_name) {
                document.getElementById('srcKbName').value = data.data.kb_name;
                onSrcKbChange();
            }
            switchSection('analyze');
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            document.querySelector('[data-section="analyze"]')?.classList.add('active');
            showToast('会话已加载', 'success');
        }
    } catch (e) {
        showToast('加载失败', 'error');
    }
}

async function deleteSession(id) {
    if (!confirm('确定删除此会话？')) return;
    try {
        const res = await fetch(`/api/session?id=${encodeURIComponent(id)}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            loadSessions();
            showToast('已删除', 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

// ==================== UTILITIES ====================
function formatBytes(b) {
    if (b === 0) return '0 B';
    const k = 1024, s = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(b) / Math.log(k));
    return parseFloat((b / Math.pow(k, i)).toFixed(1)) + ' ' + s[i];
}

function showToast(msg, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = `<span style="font-weight:700">${icon}</span><span>${escapeHtml(msg)}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.classList.add('toast-out'); setTimeout(() => toast.remove(), 300); }, 3000);
}

// ==================== DRAG & DROP & FILE SELECT ====================
function showSelectedFile(name) {
    const label = document.getElementById('selectedFileLabel');
    if (label) {
        label.textContent = '已选择: ' + name;
        label.style.display = 'block';
    }
}
function clearSelectedFile() {
    const label = document.getElementById('selectedFileLabel');
    if (label) { label.style.display = 'none'; label.textContent = ''; }
}

document.addEventListener('DOMContentLoaded', () => {
    const dz = document.getElementById('dropzone');
    const fi = document.getElementById('fileInput');
    if (fi) {
        fi.addEventListener('change', () => {
            if (fi.files.length > 0) showSelectedFile(fi.files[0].name);
        });
    }
    if (dz) {
        dz.addEventListener('dragover', e => { e.preventDefault(); dz.style.borderColor = 'var(--blue-300)'; dz.style.background = 'var(--blue-50)'; });
        dz.addEventListener('dragleave', () => { dz.style.borderColor = ''; dz.style.background = ''; });
        dz.addEventListener('drop', e => {
            e.preventDefault();
            dz.style.borderColor = ''; dz.style.background = '';
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('fileInput').files = files;
                showSelectedFile(files[0].name);
            }
        });
    }
});

// ==================== KEYBOARD ====================
document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && AppState.currentSection === 'analyze') {
        doAnalyze();
    }
});
