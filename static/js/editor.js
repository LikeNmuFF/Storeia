// ─── State ───────────────────────────────────────────────────────────────────
let currentNodeId = null;
let allNodes = [];

// ─── Init ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    await refreshNodes();

    document.getElementById('btn-add-node').addEventListener('click', addNode);
});

// ─── Node list ───────────────────────────────────────────────────────────────
async function refreshNodes() {
    const res = await fetch(`/api/story/${STORY_ID}/nodes`);
    allNodes = await res.json();
    renderNodeList();
    if (currentNodeId) {
        const node = allNodes.find(n => n.id === currentNodeId);
        if (node) renderNodeEditor(node);
    }
}

function renderNodeList() {
    const list = document.getElementById('node-list');
    list.innerHTML = '';
    allNodes.forEach(node => {
        const li = document.createElement('li');
        li.className = `node-item${node.is_start ? ' node-start' : ''}${node.is_ending ? ' node-ending' : ''}${node.id === currentNodeId ? ' active' : ''}`;
        li.dataset.id = node.id;
        li.onclick = () => selectNode(node.id);

        let html = `<span class="node-item-title">${escapeHtml(node.title)}</span>`;
        if (node.is_start) html += `<span class="node-tag start-tag">Start</span>`;
        if (node.is_ending) html += `<span class="node-tag end-tag">End</span>`;
        li.innerHTML = html;
        list.appendChild(li);
    });
}

function selectNode(nodeId) {
    currentNodeId = nodeId;
    const node = allNodes.find(n => n.id === nodeId);
    if (!node) return;

    document.querySelectorAll('.node-item').forEach(el => el.classList.remove('active'));
    const li = document.querySelector(`.node-item[data-id="${nodeId}"]`);
    if (li) li.classList.add('active');

    renderNodeEditor(node);
}

// ─── Node editor ─────────────────────────────────────────────────────────────
function renderNodeEditor(node) {
    const area = document.getElementById('node-editor-area');
    const template = document.getElementById('node-editor-template');
    area.innerHTML = '';
    area.appendChild(template.content.cloneNode(true));

    document.getElementById('node-title').value = node.title;
    document.getElementById('node-content').value = node.content;
    document.getElementById('node-is-ending').checked = node.is_ending;

    const saveBtn = document.getElementById('btn-save-node');
    saveBtn.addEventListener('click', () => saveNode(node.id));

    const deleteBtn = document.getElementById('btn-delete-node');
    if (node.is_start) {
        deleteBtn.disabled = true;
        deleteBtn.title = 'Cannot delete the starting scene';
        deleteBtn.style.opacity = '0.4';
    } else {
        deleteBtn.addEventListener('click', () => deleteNode(node.id));
    }

    document.getElementById('btn-add-choice').addEventListener('click', () => addChoice(node.id));

    // Word count live counter
    const contentArea = document.getElementById('node-content');
    updateWordCount(contentArea.value);
    contentArea.addEventListener('input', () => updateWordCount(contentArea.value));

    renderChoices(node.choices);
}

async function saveNode(nodeId) {
    const title = document.getElementById('node-title').value.trim();
    const content = document.getElementById('node-content').value;
    const isEnding = document.getElementById('node-is-ending').checked;

    if (!title) return showSaveIndicator('Title required.', false);

    const res = await fetch(`/api/node/${nodeId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content, is_ending: isEnding })
    });

    if (res.ok) {
        showSaveIndicator('Saved.', true);
        await refreshNodes();
    } else {
        showSaveIndicator('Save failed.', false);
    }
}

async function deleteNode(nodeId) {
    if (!confirm('Delete this scene? This cannot be undone.')) return;
    const res = await fetch(`/api/node/${nodeId}`, { method: 'DELETE' });
    if (res.ok) {
        currentNodeId = null;
        document.getElementById('node-editor-area').innerHTML =
            '<div class="node-editor-placeholder"><p>Select a scene from the sidebar to edit it.</p></div>';
        await refreshNodes();
    }
}

async function addNode() {
    const res = await fetch(`/api/story/${STORY_ID}/node`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Scene', content: '' })
    });
    if (res.ok) {
        const node = await res.json();
        await refreshNodes();
        selectNode(node.id);
    }
}

function showSaveIndicator(msg, success) {
    const el = document.getElementById('save-indicator');
    if (!el) return;
    el.textContent = msg;
    el.style.color = success ? 'var(--sage)' : 'var(--rust)';
    setTimeout(() => { el.textContent = ''; }, 3000);
}

// ─── Choices ─────────────────────────────────────────────────────────────────
function renderChoices(choices) {
    const list = document.getElementById('choices-list');
    list.innerHTML = '';
    choices.sort((a, b) => a.order - b.order).forEach(choice => {
        list.appendChild(buildChoiceRow(choice));
    });
}

function buildChoiceRow(choice) {
    const row = document.createElement('div');
    row.className = 'choice-row';
    row.dataset.id = choice.id;

    const labelInput = document.createElement('input');
    labelInput.className = 'field-input field-input-sm';
    labelInput.type = 'text';
    labelInput.value = choice.label;
    labelInput.placeholder = 'Choice text...';

    const targetSelect = document.createElement('select');
    targetSelect.innerHTML = `<option value="">-- leads nowhere --</option>`;
    allNodes.filter(n => n.id !== currentNodeId).forEach(n => {
        const opt = document.createElement('option');
        opt.value = n.id;
        opt.textContent = n.title;
        if (n.id === choice.to_node_id) opt.selected = true;
        targetSelect.appendChild(opt);
    });

    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-sm btn-outline';
    saveBtn.textContent = 'Save';
    saveBtn.onclick = async () => {
        await fetch(`/api/choice/${choice.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                label: labelInput.value.trim(),
                to_node_id: targetSelect.value ? parseInt(targetSelect.value) : null
            })
        });
        await refreshNodes();
        const node = allNodes.find(n => n.id === currentNodeId);
        if (node) renderChoices(node.choices);
        showSaveIndicator('Saved.', true);
    };

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn-icon';
    deleteBtn.innerHTML = '&#10005;';
    deleteBtn.onclick = async () => {
        await fetch(`/api/choice/${choice.id}`, { method: 'DELETE' });
        row.remove();
        await refreshNodes();
    };

    row.appendChild(labelInput);
    row.appendChild(targetSelect);
    const btnGroup = document.createElement('div');
    btnGroup.style.display = 'flex';
    btnGroup.style.gap = '6px';
    btnGroup.appendChild(saveBtn);
    btnGroup.appendChild(deleteBtn);
    row.appendChild(btnGroup);

    return row;
}

async function addChoice(nodeId) {
    const res = await fetch(`/api/node/${nodeId}/choice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: 'New Choice' })
    });
    if (res.ok) {
        const choice = await res.json();
        const list = document.getElementById('choices-list');
        if (list) list.appendChild(buildChoiceRow(choice));
        await refreshNodes();
    }
}

// ─── Collaborators ────────────────────────────────────────────────────────────
async function inviteCollaborator() {
    const input = document.getElementById('invite-username');
    const username = input.value.trim();
    if (!username) return;

    const res = await fetch(`/api/story/${STORY_ID}/invite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
    });

    const data = await res.json();
    if (res.ok) {
        input.value = '';
        const list = document.getElementById('collab-list');
        const li = document.createElement('li');
        li.className = 'collab-item';
        li.dataset.userId = data.user_id;
        li.innerHTML = `
            <span class="collab-avatar">${data.username[0].toUpperCase()}</span>
            <span>${escapeHtml(data.username)}</span>
            ${IS_OWNER ? `<button class="btn-icon remove-collab" onclick="removeCollaborator(${data.user_id})">&#10005;</button>` : ''}
        `;
        list.appendChild(li);
    } else {
        alert(data.error || 'Could not invite user.');
    }
}

async function removeCollaborator(userId) {
    if (!confirm('Remove this collaborator?')) return;
    const res = await fetch(`/api/story/${STORY_ID}/remove_collaborator`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    if (res.ok) {
        const li = document.querySelector(`.collab-item[data-user-id="${userId}"]`);
        if (li) li.remove();
    }
}

// ─── Word Count ───────────────────────────────────────────────────────────────
function updateWordCount(text) {
    const words = text.trim() === '' ? 0 : text.trim().split(/\s+/).length;
    const numEl = document.getElementById('wc-num');
    const fillEl = document.getElementById('wc-fill');
    const labelEl = document.getElementById('wc-label');
    if (!numEl) return;

    numEl.textContent = words;

    // Target: 300 words per scene feels complete
    const target = 300;
    const pct = Math.min((words / target) * 100, 100);
    fillEl.style.width = pct + '%';

    // Color stages
    fillEl.className = 'word-count-fill';
    if (pct >= 100) fillEl.classList.add('full');
    else if (pct >= 60) fillEl.classList.add('warm');

    // Labels
    const labels = [
        [0,   'just getting started'],
        [30,  'setting the scene'],
        [80,  'finding the rhythm'],
        [150, 'good momentum'],
        [200, 'getting somewhere'],
        [260, 'almost a full scene'],
        [300, 'solid scene'],
        [400, 'going deep'],
        [600, 'epic passage'],
    ];
    let label = labels[0][1];
    for (const [threshold, text] of labels) {
        if (words >= threshold) label = text;
    }
    labelEl.textContent = label;
}


function escapeHtml(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
}
