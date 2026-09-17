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
    globalPersons.forEach(p => {
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
        const col = createColumnDOM(cat, colPersons, index, globalCategories.length);
        container.appendChild(col);
    });




    // 4. Render Disabled Archive area (Separated Columns Container)
    const disabledCategories = globalCategories.filter(c => c.is_deleted);
    
    if (disabledCategories.length > 0) {
        let archiveContainer = document.getElementById('archiveContainer');
        if (!archiveContainer) {
            archiveContainer = document.createElement('div');
            archiveContainer.id = 'archiveContainer';
            archiveContainer.style.cssText = 'margin-top: 40px; border-top: 1px dashed rgba(128,128,128,0.2); padding-top: 20px;';
            container.parentNode.appendChild(archiveContainer);
        }
        
        archiveContainer.innerHTML = `
            <div style="font-size: 1.05rem; font-weight: 700; color: var(--text-muted); margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
                📁 已停用的分类 (${disabledCategories.length})
            </div>
            <div class="kanban-board" style="min-height: auto; padding-bottom: 10px;">
            </div>
        `;
        
        const archiveBoard = archiveContainer.querySelector('.kanban-board');
        
        // Render each disabled category
        disabledCategories.forEach(cat => {
            const colPersons = groups[cat.uuid] || [];
            const col = createDisabledColumnDOM(cat, colPersons);
            archiveBoard.appendChild(col);
        });
    } else {
        const archiveContainer = document.getElementById('archiveContainer');
        if (archiveContainer) {
            archiveContainer.remove();
        }
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
        const isFirst = index === 0;
        const isLast = index === totalCols - 1;
        
        const upBtn = `<span onclick="moveCategoryUp(${index})" style="cursor:${isFirst ? 'default' : 'pointer'}; opacity:${isFirst ? 0.3 : 1}; font-size:0.75rem;" title="上移分类"><svg viewBox="0 0 24 24" width="14" height="14" style="fill:none; stroke:var(--text-muted); stroke-width:3; stroke-linecap:round; stroke-linejoin:round; display:inline-block; vertical-align:middle;"><path d="m18 15-6-6-6 6"/></svg></span>`;
        const downBtn = `<span onclick="moveCategoryDown(${index})" style="cursor:${isLast ? 'default' : 'pointer'}; opacity:${isLast ? 0.3 : 1}; font-size:0.75rem;" title="下移分类"><svg viewBox="0 0 24 24" width="14" height="14" style="fill:none; stroke:var(--text-muted); stroke-width:3; stroke-linecap:round; stroke-linejoin:round; display:inline-block; vertical-align:middle;"><path d="m6 9 6 6 6-6"/></svg></span>`;
        
        actionHtml = `
            <div style="display:flex; gap:8px; align-items:center;">
                ${upBtn}
                ${downBtn}
                <span onclick="openEditCategoryModal('${cat.uuid}', '${cat.name}')" style="cursor:pointer; font-size:0.75rem;" title="修改分类名称">✏️</span>
                <span onclick="deleteCategory('${cat.uuid}')" style="cursor:pointer; font-size:0.75rem;" title="停用该分类">🚫</span>
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

        if (p.is_deleted) {
            card.style.opacity = '0.55';
            card.style.filter = 'grayscale(50%)';
            card.style.border = '1px dashed rgba(128, 128, 128, 0.4)';
        }

        const relLabel = p.relationship ? `<span style="font-size:0.7rem; font-weight:600; opacity:0.8; margin-left:6px;">(${p.relationship})</span>` : '';
        const abbrLabel = p.abbreviation ? `<div style="font-size:0.75rem; opacity:0.7; margin-top:4px; font-family:monospace;">缩写: ${p.abbreviation}</div>` : '';
        const tempTag = p.is_temporary ? `<span style="font-size:0.65rem; background:rgba(0,0,0,0.25); padding:1px 4px; border-radius:4px; margin-left:6px; color:#f8fafc;">路人</span>` : '';
        const disabledTag = p.is_deleted ? `<span style="font-size:0.65rem; background:rgba(128,128,128,0.3); padding:1px 4px; border-radius:4px; margin-left:6px; color:var(--text-muted);">已停用</span>` : '';
        
        const colorDot = p.is_temporary ? '' : `<span class="dino-color-dot dot-${p.color_tag || 'red'}" style="margin-left:6px; display:inline-block; vertical-align:middle;"></span>`;
        
        let actionBtn = '';
        if (!p.is_temporary) {
            if (p.is_deleted) {
                actionBtn = `<span onclick="enablePersonDirect('${p.uuid}', event)" style="cursor:pointer; padding: 2px 6px; display:inline-flex; align-items:center;" title="恢复启用该人物"><svg viewBox="0 0 24 24" width="14" height="14" style="fill:none; stroke:#10b981; stroke-width:3; stroke-linecap:round; stroke-linejoin:round;"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l.73-2.79"/></svg></span>`;
            } else {
                actionBtn = `<span onclick="deletePersonDirect('${p.uuid}', event)" style="cursor:pointer; font-size:0.85rem; padding: 2px 6px; color: #ef4444;" title="停用该人物">🚫</span>`;
            }
        }

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                <div style="flex:1;">
                    <div style="font-weight:700; font-size:0.85rem; display:flex; align-items:center;">
                        <span>${p.name}${relLabel}${colorDot}${tempTag}${disabledTag}</span>
                    </div>
                    ${abbrLabel}
                </div>
                ${actionBtn}
            </div>
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
function createDisabledColumnDOM(cat, persons) {
    const col = document.createElement('div');
    col.className = 'kanban-column';
    col.style.background = 'rgba(128, 128, 128, 0.05)';
    col.style.border = '1px dashed rgba(128, 128, 128, 0.3)';
    col.style.opacity = '0.85';
    
    const header = document.createElement('div');
    header.className = 'kanban-column-header';
    header.style.borderBottom = '2px solid rgba(128, 128, 128, 0.2)';
    header.innerHTML = `
        <div class="kanban-column-title" style="color: var(--text-muted); font-weight: bold;">
            <span style="color: var(--text-muted);">📂 ${cat.name}</span>
            <span style="font-size:0.75rem; color:var(--text-muted);">(${persons.length})</span>
        </div>
        <span onclick="enableCategory('${cat.uuid}')" style="cursor:pointer; padding: 4px; display:inline-flex; align-items:center;" title="恢复启用该分类"><svg viewBox="0 0 24 24" width="15" height="15" style="fill:none; stroke:#10b981; stroke-width:3; stroke-linecap:round; stroke-linejoin:round;"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l.73-2.79"/></svg></span>
    `;
    col.appendChild(header);
    
    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'kanban-cards-container';
    
    persons.forEach(p => {
        const card = document.createElement('div');
        card.className = `kanban-card person-card color-chip-${p.color_tag || 'red'}`;
        card.style.cursor = 'default';
        if (p.is_deleted) {
            card.style.opacity = '0.55';
            card.style.filter = 'grayscale(50%)';
        }
        const colorDot = p.is_temporary ? '' : `<span class="dino-color-dot dot-${p.color_tag || 'red'}" style="margin-left:6px; display:inline-block; vertical-align:middle;"></span>`;
        const disabledTag = p.is_deleted ? `<span style="font-size:0.65rem; background:rgba(128,128,128,0.3); padding:1px 4px; border-radius:4px; margin-left:6px; color:var(--text-muted);">已停用</span>` : '';
        card.innerHTML = `
            <div style="font-weight:700; font-size:0.85rem;">
                <span>${p.name} ${p.relationship ? `<span style="font-size:0.7rem; opacity:0.8;">(${p.relationship})</span>` : ''}${colorDot}${disabledTag}</span>
            </div>
        `;
        cardsContainer.appendChild(card);
    });
    
    if (persons.length === 0) {
        const placeholder = document.createElement('div');
        placeholder.style = "border: 1px dashed rgba(128,128,128,0.15); border-radius:10px; padding:15px; text-align:center; font-size:0.75rem; color:var(--text-muted);";
        placeholder.textContent = "无活跃成员";
        cardsContainer.appendChild(placeholder);
    }
    
    col.appendChild(cardsContainer);
    return col;
}

async function moveCategoryUp(index) {
    if (index <= 0) return;
    const activeCategories = globalCategories.filter(c => !c.is_deleted);
    const currentCat = activeCategories[index];
    const prevCat = activeCategories[index - 1];
    
    const idx1 = globalCategories.findIndex(c => c.uuid === currentCat.uuid);
    const idx2 = globalCategories.findIndex(c => c.uuid === prevCat.uuid);
    if (idx1 >= 0 && idx2 >= 0) {
        const temp = globalCategories[idx1].sort_order;
        globalCategories[idx1].sort_order = globalCategories[idx2].sort_order;
        globalCategories[idx2].sort_order = temp;
        
        globalCategories.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
        globalCategories.filter(c => !c.is_deleted).forEach((c, idx) => {
            c.sort_order = idx;
        });
        await syncCategoriesOrder();
    }
}

async function moveCategoryDown(index) {
    const activeCategories = globalCategories.filter(c => !c.is_deleted);
    if (index >= activeCategories.length - 1) return;
    const currentCat = activeCategories[index];
    const nextCat = activeCategories[index + 1];
    
    const idx1 = globalCategories.findIndex(c => c.uuid === currentCat.uuid);
    const idx2 = globalCategories.findIndex(c => c.uuid === nextCat.uuid);
    if (idx1 >= 0 && idx2 >= 0) {
        const temp = globalCategories[idx1].sort_order;
        globalCategories[idx1].sort_order = globalCategories[idx2].sort_order;
        globalCategories[idx2].sort_order = temp;
        
        globalCategories.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
        globalCategories.filter(c => !c.is_deleted).forEach((c, idx) => {
            c.sort_order = idx;
        });
        await syncCategoriesOrder();
    }
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

// 修复「鼠标在层内按下、拖拽到层外松开」误触关闭 Bug
// mousedown 发生在遮罩本身时才允许 click 关闭，防止文本框拖拽选词时误关弹窗
['categoryModal', 'personModal'].forEach(id => {
    const modal = document.getElementById(id);
    if (!modal) return;
    let mouseDownOnBackdrop = false;
    modal.addEventListener('mousedown', (e) => {
        mouseDownOnBackdrop = (e.target === modal);
    });
    modal.addEventListener('click', (e) => {
        if (e.target === modal && mouseDownOnBackdrop) {
            if (id === 'categoryModal') closeCategoryModal();
            else if (id === 'personModal') closePersonModal();
        }
        mouseDownOnBackdrop = false;
    });
});

// Start Initialization
initPersonsPage();
