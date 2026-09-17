// Modal triggers
function openAddCategoryModal() {
    document.getElementById('categoryModalTitle').textContent = "新建分类";
    document.getElementById('categoryModalUuid').value = "";
    document.getElementById('categoryModalName').value = "";
    document.getElementById('categoryModal').style.display = "flex";
}

function openEditCategoryModal(uuid, name) {
    document.getElementById('categoryModalTitle').textContent = "修改分类";
    document.getElementById('categoryModalUuid').value = uuid;
    document.getElementById('categoryModalName').value = name;
    document.getElementById('categoryModal').style.display = "flex";
}

function closeCategoryModal() {
    document.getElementById('categoryModal').style.display = "none";
}

async function saveCategoryModal() {
    const uuid = document.getElementById('categoryModalUuid').value;
    const name = document.getElementById('categoryModalName').value.trim();
    if (!name) {
        alert("分类名称不能为空哦！");
        return;
    }

    const catObj = {
        uuid: uuid || 'cat-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now().toString(36),
        name: name,
        sort_order: uuid ? (globalCategories.find(c => c.uuid === uuid)?.sort_order || 0) : globalCategories.length
    };

    try {
        const res = await fetch('/api/categories/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ categories: [catObj], deleted_uuids: [] })
        });
        if (res.ok) {
            closeCategoryModal();
            await fetchCategories();
            renderPersonBoard();
        }
    } catch (e) {
        console.error("Failed to save category", e);
    }
}

async function deleteCategory(uuid) {
    const ok = await showCustomConfirm(
        "确认停用该分类？",
        "确定要停用这个分类吗？停用后该分类在日记选择和首页看板中将不再显示，但下属人物的状态本身不受影响，以往的历史数据依然完整保留。\n\n您随时可以从‘已停用列表’中重新启用此分类。",
        "确认停用"
    );
    if (!ok) return;
    try {
        const res = await fetch('/api/categories/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ categories: [], deleted_uuids: [uuid] })
        });
        if (res.ok) {
            await fetchCategories();
            await fetchPersons();
        }
    } catch (e) {
        console.error("Failed to delete category", e);
    }
}

// Person Modals
function openAddPersonModal() {
    document.getElementById('personModalTitle').textContent = "新增关系人";
    document.getElementById('personModalUuid').value = "";
    document.getElementById('personModalName').value = "";
    document.getElementById('personModalAbbr').value = "";
    document.getElementById('personModalRel').value = "";
    
    const select = document.getElementById('personModalCategory');
    select.innerHTML = '';
    globalCategories.filter(c => !c.is_deleted).forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.uuid;
        opt.textContent = c.name;
        select.appendChild(opt);
    });

    document.getElementById('personModalDeleteBtn').style.display = "none";
    document.getElementById('personModalDeleteBtn').textContent = "停用人物";
    document.getElementById('personModalDeleteBtn').onclick = deletePersonFromModal;
    document.querySelector('input[name="personModalColor"][value="red"]').checked = true;
    document.getElementById('personModal').style.display = "flex";
}

function openEditPersonModal(person) {
    document.getElementById('personModalTitle').textContent = person.is_temporary ? "🌟 临时人物转正 🌟" : "编辑人物属性";
    document.getElementById('personModalUuid').value = person.uuid;
    document.getElementById('personModalName').value = person.name;
    document.getElementById('personModalAbbr').value = person.abbreviation;
    document.getElementById('personModalRel').value = person.relationship;

    const select = document.getElementById('personModalCategory');
    select.innerHTML = '';
    
    const activeCategories = globalCategories.filter(c => !c.is_deleted);
    activeCategories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.uuid;
        opt.textContent = c.name;
        select.appendChild(opt);
    });

    if (person.category_uuid) {
        const existingCat = globalCategories.find(c => c.uuid === person.category_uuid);
        if (existingCat && existingCat.is_deleted) {
            const opt = document.createElement('option');
            opt.value = existingCat.uuid;
            opt.textContent = existingCat.name + ' (已停用)';
            select.appendChild(opt);
        }
        select.value = person.category_uuid;
    } else {
        if (activeCategories.length > 0) {
            select.value = activeCategories[0].uuid;
        } else {
            select.value = '';
        }
    }

    const colorVal = person.color_tag || 'red';
    const radio = document.querySelector(`input[name="personModalColor"][value="${colorVal}"]`);
    if (radio) {
        radio.checked = true;
    } else {
        const fallbackRadio = document.querySelector(`input[name="personModalColor"][value="red"]`);
        if (fallbackRadio) fallbackRadio.checked = true;
    }

    const deleteBtn = document.getElementById('personModalDeleteBtn');
    deleteBtn.style.display = "block";
    if (person.is_deleted) {
        deleteBtn.textContent = "启用人物";
        deleteBtn.className = "modal-btn-save";
        deleteBtn.onclick = function() {
            enablePerson(person.uuid);
            closePersonModal();
        };
    } else {
        deleteBtn.textContent = "停用人物";
        deleteBtn.className = "modal-btn-delete";
        deleteBtn.onclick = deletePersonFromModal;
    }
    document.getElementById('personModal').style.display = "flex";
}

function closePersonModal() {
    document.getElementById('personModal').style.display = "none";
}

async function savePersonModal() {
    const uuid = document.getElementById('personModalUuid').value;
    const name = document.getElementById('personModalName').value.trim();
    const abbr = document.getElementById('personModalAbbr').value.trim();
    const rel = document.getElementById('personModalRel').value.trim();
    const catSelectVal = document.getElementById('personModalCategory').value;
    const colorVal = document.querySelector('input[name="personModalColor"]:checked').value;

    if (!name || !abbr) {
        alert("人物姓名和拼音缩写不能为空！");
        return;
    }

    const activeCategories = globalCategories.filter(c => !c.is_deleted);
    const isEditingWithDisabledCat = uuid && globalPersons.find(p => p.uuid === uuid)?.category_uuid === catSelectVal;
    if (activeCategories.length === 0 && !isEditingWithDisabledCat) {
        alert("请先新建分类！所有正式关系人必须落座分类。");
        return;
    }

    if (!catSelectVal || catSelectVal === 'unclassified') {
        alert("请选择一个有效的分类！");
        return;
    }

    const existing = globalPersons.find(p => p.uuid === uuid);

    const personObj = {
        uuid: uuid || 'p-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now().toString(36),
        name: name,
        abbreviation: abbr.toUpperCase(),
        relationship: rel || '朋友',
        category_uuid: catSelectVal,
        color_tag: colorVal,
        sort_order: existing ? (existing.sort_order || 0) : 99,
        is_temporary: false
    };

    try {
        const res = await fetch('/api/persons/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ persons: [personObj], deleted_uuids: [] })
        });
        if (res.ok) {
            closePersonModal();
            await fetchPersons();
        }
    } catch (e) {
        console.error("Failed to save person", e);
    }
}

async function deletePersonFromModal() {
    const uuid = document.getElementById('personModalUuid').value;
    if (!uuid) return;
    const ok = await showCustomConfirm(
        "确认停用该关系人？",
        "确定要停用这个人物关系吗？停用后，他们将不再出现在选择名单和分类看板中。您以前日记中的人物名字和彩色标签依然会完整挂载，且您随时可以重新启用他们。",
        "确认停用"
    );
    if (!ok) return;
    try {
        const res = await fetch('/api/persons/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ persons: [], deleted_uuids: [uuid] })
        });
        if (res.ok) {
            closePersonModal();
            await fetchPersons();
        }
    } catch (e) {
        console.error("Failed to delete person", e);
    }
}

async function enableCategory(uuid) {
    const cat = globalCategories.find(c => c.uuid === uuid);
    if (!cat) return;
    const ok = await showCustomConfirm(
        "确认恢复启用分类？",
        `确定要恢复启用分类 "${cat.name}" 吗？启用后，它将重新显示在写日记和首页看板的分类列表中，其以往的历史数据均保持完整。`,
        "确认启用"
    );
    if (!ok) return;
    try {
        const activeCategories = globalCategories.filter(c => !c.is_deleted);
        const maxSort = activeCategories.length > 0 ? Math.max(...activeCategories.map(c => c.sort_order || 0)) : -1;
        
        const res = await fetch('/api/categories/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                categories: [{
                    uuid: cat.uuid,
                    name: cat.name,
                    sort_order: maxSort + 1,
                    is_deleted: false
                }],
                deleted_uuids: []
            })
        });
        if (res.ok) {
            await fetchCategories();
            await fetchPersons();
            showToast(`分类 "${cat.name}" 已恢复启用！`);
        }
    } catch (e) {
        console.error("Failed to enable category", e);
    }
}

async function enablePerson(uuid) {
    const person = globalPersons.find(p => p.uuid === uuid);
    if (!person) return;
    try {
        const activePersonsInCat = globalPersons.filter(p => p.category_uuid === person.category_uuid && !p.is_deleted);
        const maxSort = activePersonsInCat.length > 0 ? Math.max(...activePersonsInCat.map(p => p.sort_order || 0)) : -1;

        const res = await fetch('/api/persons/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                persons: [{
                    uuid: person.uuid,
                    name: person.name,
                    abbreviation: person.abbreviation,
                    relationship: person.relationship,
                    category_uuid: person.category_uuid,
                    sort_order: maxSort + 1,
                    color_tag: person.color_tag,
                    is_temporary: person.is_temporary,
                    is_deleted: false,
                    created_at: person.created_at
                }],
                deleted_uuids: []
            })
        });
        if (res.ok) {
            await fetchPersons();
            showToast(`关系人 "${person.name}" 已恢复启用！`);
        }
    } catch (e) {
        console.error("Failed to enable person", e);
    }
}

async function enablePersonDirect(uuid, event) {
    if (event) event.stopPropagation();
    const person = globalPersons.find(p => p.uuid === uuid);
    if (!person) return;
    const ok = await showCustomConfirm(
        "确认恢复启用关系人？",
        `确定要恢复启用关系人 "${person.name}" 吗？启用后，他们将重新显示在写日记和分类看板的人物列表中，并在其原有的分类中可见。`,
        "确认启用"
    );
    if (!ok) return;
    await enablePerson(uuid);
}

async function deletePersonDirect(uuid, event) {
    if (event) event.stopPropagation();
    const person = globalPersons.find(p => p.uuid === uuid);
    if (!person) return;
    const ok = await showCustomConfirm(
        "确认停用该关系人？",
        `确定要停用关系人 "${person.name}" 吗？停用后，他们将不再出现在选择名单和分类看板中。以前日记中的记录依然完整保留，且您随时可以从下方的已停用列表中恢复启用。`,
        "确认停用"
    );
    if (!ok) return;
    try {
        const res = await fetch('/api/persons/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                persons: [{
                    uuid: person.uuid,
                    name: person.name,
                    abbreviation: person.abbreviation,
                    relationship: person.relationship,
                    category_uuid: person.category_uuid,
                    sort_order: person.sort_order,
                    color_tag: person.color_tag,
                    is_temporary: person.is_temporary,
                    is_deleted: true,
                    created_at: person.created_at
                }],
                deleted_uuids: []
            })
        });
        if (res.ok) {
            await fetchPersons();
        }
    } catch (e) {
        console.error("Failed to delete person direct", e);
    }
}
