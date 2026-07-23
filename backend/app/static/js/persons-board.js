// Global Variables for Kanban
let globalCategories = [];
let globalPersons = [];
let globalPersonsMap = {};

async function initPersonsPage() {
    try {
        await fetchCategories();
        await fetchPersons();
    } catch (e) {
        console.error("Failed to initialize Kanban page", e);
    }
}

// Sync and load categories
async function fetchCategories() {
    try {
        const res = await fetch('/api/categories/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ categories: [], deleted_uuids: [] })
        });
        if (res.ok) {
            globalCategories = await res.json();
            globalCategories.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
        }
    } catch (e) {
        console.error("Failed to load categories", e);
    }
}

// Sync and load persons
async function fetchPersons() {
    try {
        const res = await fetch('/api/persons/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ persons: [], deleted_uuids: [] })
        });
        if (res.ok) {
            globalPersons = await res.json();
            globalPersonsMap = {};
            
            // Build map
            globalPersons.forEach(p => {
                globalPersonsMap[p.uuid] = p;
            });
            
            renderPersonBoard();
        }
    } catch (e) {
        console.error("Failed to load persons", e);
    }
}

// Kanban Board Render
function renderPersonBoard() {
    const container = document.getElementById('kanbanBoard');
    if (!container) return;
    container.innerHTML = '';

    // Group persons by category_uuid
    const groups = {};
    globalPersons.filter(p => !p.is_deleted).forEach(p => {
        const key = p.category_uuid || 'unclassified';
        if (!groups[key]) groups[key] = [];
        groups[key].push(p);
    });

    // Sort persons in each group by sort_order
    for (const key in groups) {
        groups[key].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
    }

    // 1. Render custom categories
    globalCategories.filter(cat => !cat.is_deleted).forEach((cat, index) => {
        const colPersons = groups[cat.uuid] || [];
        const col = createColumnDOM(cat, colPersons.filter(p => !p.is_temporary), index, globalCategories.length);
        container.appendChild(col);
    });

    // 2. Render Unclassified column (Static)
    const unclassifiedPersons = groups['unclassified'] || [];
    const unclassifiedCol = createColumnDOM({ uuid: 'unclassified', name: '未分类' }, unclassifiedPersons.filter(p => !p.is_temporary), -1, 0);
    container.appendChild(unclassifiedCol);

    // 3. Render Temporary Persons column (Static)
    const temporaryPersons = globalPersons.filter(p => p.is_temporary && !p.is_deleted);
    if (temporaryPersons.length > 0) {
        const tempCol = createColumnDOM({ uuid: 'temporary', name: '一次性临时路人' }, temporaryPersons, -2, 0);
        container.appendChild(tempCol);
    }

    // 4. Render Disabled Archive column (Static)
    const disabledPersons = globalPersons.filter(p => p.is_deleted);
    const disabledCategories = globalCategories.filter(c => c.is_deleted);
    if (disabledPersons.length > 0 || disabledCategories.length > 0) {
        const archiveCol = createArchiveColumnDOM(disabledCategories, disabledPersons);
        container.appendChild(archiveCol);
    }

    // Setup HTML5 Drag and Drop events
    setupPersonsDragAndDrop();
}

function createColumnDOM(cat, persons, index, totalCols) {
    const isCustom = index >= 0;
    const isTemp = cat.uuid === 'temporary';
    const col = document.createElement('div');
    col.className = 'kanban-column';
    col.id = `col-${cat.uuid}`;
    col.setAttribute('data-uuid', cat.uuid);
    
    // Custom categories can be dragged horizontally
    if (isCustom) {
        col.setAttribute('draggable', 'true');
    }

    // Header
    const header = document.createElement('div');
    header.className = 'kanban-column-header';
    
    let actionHtml = '';
    if (isCustom) {
        actionHtml = `
            <div style="display:flex; gap:6px;">
                <span onclick="openEditCategoryModal('${cat.uuid}', '${cat.name}')" style="cursor:pointer; font-size:0.75rem;">✏️</span>
                <span onclick="deleteCategory('${cat.uuid}')" style="cursor:pointer; font-size:0.75rem;">🗑️</span>
            </div>
        `;
    }

    const numPrefix = isCustom ? `${index + 1}. ` : '';
    header.innerHTML = `
        <div class="kanban-column-title">
            <span>${isTemp ? '📁' : '📂'} ${numPrefix}${cat.name}</span>
            <span style="font-size:0.75rem; color:var(--text-muted);">(${persons.length})</span>
        </div>
        ${actionHtml}
    `;
    col.appendChild(header);

    // Cards Container
    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'kanban-cards-container';
    cardsContainer.id = `cards-${cat.uuid}`;
    cardsContainer.setAttribute('data-uuid', cat.uuid);

    persons.forEach(p => {
        const card = document.createElement('div');
        card.className = `kanban-card person-card color-chip-${p.color_tag || 'red'}`;
        if (p.is_temporary) {
            card.className = `kanban-card person-card color-chip-gray`;
        }
        card.setAttribute('draggable', 'true');
        card.setAttribute('data-uuid', p.uuid);
        
        card.onclick = (e) => {
            if (card.classList.contains('dragging')) return;
            openEditPersonModal(p);
        };

        const relLabel = p.relationship ? `<span style="font-size:0.7rem; font-weight:600; opacity:0.8; margin-left:6px;">(${p.relationship})</span>` : '';
        const abbrLabel = p.abbreviation ? `<div style="font-size:0.75rem; opacity:0.7; margin-top:4px; font-family:monospace;">缩写: ${p.abbreviation}</div>` : '';
        const tempTag = p.is_temporary ? `<span style="font-size:0.65rem; background:rgba(0,0,0,0.25); padding:1px 4px; border-radius:4px; margin-left:6px; color:#f8fafc;">路人</span>` : '';
        
        const colorDot = p.is_temporary ? '' : `<span class="dino-color-dot dot-${p.color_tag || 'red'}" style="margin-left:6px; display:inline-block; vertical-align:middle;"></span>`;
        card.innerHTML = `
            <div style="font-weight:700; font-size:0.85rem; display:flex; align-items:center; justify-content:space-between;">
                <span>${p.name}${relLabel}${colorDot}${tempTag}</span>
            </div>
            ${abbrLabel}
        `;
        cardsContainer.appendChild(card);
    });

    if (persons.length === 0) {
        const placeholder = document.createElement('div');
        placeholder.style = "border: 1px dashed rgba(128,128,128,0.2); border-radius:10px; padding:15px; text-align:center; font-size:0.75rem; color:var(--text-muted);";
        placeholder.textContent = "空空如也，拖拽人物到这里吧";
        cardsContainer.appendChild(placeholder);
    }

    col.appendChild(cardsContainer);
    return col;
}



async function syncCategoriesOrder() {
    try {
        const res = await fetch('/api/categories/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ categories: globalCategories, deleted_uuids: [] })
        });
        if (res.ok) {
            globalCategories = await res.json();
            renderPersonBoard();
        }
    } catch (e) {
        console.error("Failed to sync category order", e);
    }
}

async function syncPersonsBatch(personsList) {
    try {
        const res = await fetch('/api/persons/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ persons: personsList, deleted_uuids: [] })
        });
        if (res.ok) {
            await fetchPersons();
        }
    } catch (e) {
        console.error("Failed to sync persons order", e);
    }
}

// Modal triggers
function createArchiveColumnDOM(categories, persons) {
    const col = document.createElement('div');
    col.className = 'kanban-column';
    col.style.background = 'rgba(239, 68, 68, 0.05)';
    col.style.border = '1px dashed rgba(239, 68, 68, 0.2)';
    
    col.innerHTML = `
        <div class="kanban-column-header" style="border-bottom: 2px solid rgba(239, 68, 68, 0.2);">
            <div style="font-weight: bold; color: #ef4444;">📁 已停用的归档区 (${categories.length + persons.length})</div>
        </div>
        <div class="kanban-cards-container" style="display:flex; flex-direction:column; gap:8px; padding: 12px 4px; overflow-y:auto; max-height:480px;">
        </div>
    `;
    
    const cardsContainer = col.querySelector('.kanban-cards-container');
    
    if (categories.length > 0) {
        const catTitle = document.createElement('div');
        catTitle.style.cssText = 'font-size:0.75rem; color:var(--text-muted); font-weight:bold; margin-top:4px;';
        catTitle.textContent = '停用的分类：';
        cardsContainer.appendChild(catTitle);
        
        categories.forEach(cat => {
            const card = document.createElement('div');
            card.className = 'kanban-card';
            card.style.cssText = 'padding:10px; display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.7);';
            card.innerHTML = `
                <div style="font-weight:500; font-size:0.85rem;">📂 ${cat.name}</div>
                <button onclick="enableCategory('${cat.uuid}')" class="btn-primary-purple" style="padding:4px 8px; font-size:0.7rem; border-radius:6px; cursor:pointer;">启用</button>
            `;
            cardsContainer.appendChild(card);
        });
    }
    
    if (persons.length > 0) {
        const personTitle = document.createElement('div');
        personTitle.style.cssText = 'font-size:0.75rem; color:var(--text-muted); font-weight:bold; margin-top:8px;';
        personTitle.textContent = '停用的关系人：';
        cardsContainer.appendChild(personTitle);
        
        persons.forEach(p => {
            const card = document.createElement('div');
            card.className = 'kanban-card';
            card.style.cssText = 'padding:10px; display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.7); cursor:pointer;';
            card.onclick = function(e) {
                if (e.target.tagName !== 'BUTTON') {
                    openEditPersonModal(p);
                }
            };
            
            const colorClass = p.color_tag || 'red';
            card.innerHTML = `
                <div style="display:flex; align-items:center; gap:6px;">
                    <div class="dino-color-dot dino-color-dot-${colorClass}"></div>
                    <div style="font-weight:bold; font-size:0.85rem;">${p.name}</div>
                    ${p.relationship ? `<div style="font-size:0.7rem; color:var(--text-muted);">(${p.relationship})</div>` : ''}
                </div>
                <button onclick="enablePerson('${p.uuid}')" class="btn-primary-green" style="padding:4px 8px; font-size:0.7rem; border-radius:6px; cursor:pointer;">启用</button>
            `;
            cardsContainer.appendChild(card);
        });
    }
    
    return col;
}

function showToast(msg) {
    let toast = document.getElementById('dino-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'dino-toast';
        toast.style.cssText = 'position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.85); color:white; padding:10px 24px; border-radius:20px; font-size:0.85rem; z-index:9999; transition:opacity 0.3s; opacity:0; box-shadow:0 4px 12px rgba(0,0,0,0.15);';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = '1';
    setTimeout(() => {
        toast.style.opacity = '0';
    }, 2000);
}

// Close Modal when click outside
window.addEventListener('click', function(e) {
    const catModal = document.getElementById('categoryModal');
    const pModal = document.getElementById('personModal');
    if (e.target === catModal) closeCategoryModal();
    if (e.target === pModal) closePersonModal();
});

// Start Initialization
initPersonsPage();
