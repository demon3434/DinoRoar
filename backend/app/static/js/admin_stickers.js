let activeCropper = null, editCropper = null, loadedSeriesData = [], activeFolderId = null, activeStickerObj = null;
let selectedExportSeriesIds = new Set();
let isExportMode = false;

function openCustomConfirm(message, onConfirm) {
    document.getElementById('confirmMessage').textContent = message;
    const modal = document.getElementById('customConfirmModal'); modal.style.display = 'flex';
    const okBtn = document.getElementById('btnConfirmOK'), cancelBtn = document.getElementById('btnConfirmCancel');
    okBtn.onclick = () => { modal.style.display = 'none'; if (onConfirm) onConfirm(); };
    cancelBtn.onclick = () => { modal.style.display = 'none'; };
}

async function loadStickerManagementData() {
    const seriesContainer = document.getElementById('seriesContainer');
    try {
        loadedSeriesData = await stickersApi.fetchConfig();
        renderFolders(loadedSeriesData);
        if (activeFolderId !== null) {
            const folder = loadedSeriesData.find(s => s.id === activeFolderId);
            if (folder) {
                updateFolderDetailTitle(folder);
                renderStickerList(folder);
            } else {
                closeFolderDetailModal();
            }
        }
    } catch(err) {
        showToast("拉取贴纸库失败：" + err.message, "error");
        seriesContainer.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--dino-red);">拉取贴纸配置失败！</div>`;
    }
}

function updateFolderDetailTitle(series) {
    const titleEl = document.getElementById('detailModalTitle');
    if (!titleEl || !series) return;
    const count = series.stickers ? series.stickers.length : 0;
    titleEl.innerHTML = `📁 ${series.name} - 贴纸列表 <span style="font-size: 0.85rem; font-weight: normal; color: var(--text-muted); margin-left: 8px;">(${count} 个贴纸)</span>`;
}

function renderFolders(data) {
    const container = document.getElementById('seriesContainer'); container.innerHTML = '';
    if (!data || data.length === 0) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">暂无任何系列分类，请点击上方创建</div>`;
        return;
    }
    data.forEach(s => {
        let tianziHtml = '';
        for (let i = 0; i < 4; i++) {
            if (s.stickers && s.stickers[i]) {
                let img = s.stickers[i].image_url;
                if (img && !img.startsWith('/static/')) img = '/static/images/dinosaurs/' + img;
                tianziHtml += `<div class="tianzi-cell"><img src="${img}" onerror="this.src='/static/images/ic_launcher.png'" /></div>`;
            } else tianziHtml += `<div class="tianzi-cell"></div>`;
        }
        const isSelected = selectedExportSeriesIds.has(s.id);
        const card = document.createElement('div');
        card.className = `folder-card ${s.is_active ? '' : 'grayscale-active'} ${isExportMode ? 'export-mode-active' : ''} ${isSelected ? 'export-selected' : ''}`;
        card.setAttribute('data-id', s.id);

        if (isExportMode) {
            card.onclick = () => toggleSeriesExportSelect(s.id);
        } else {
            card.onclick = () => openFolderDetail(s.id);
            card.setAttribute('draggable', 'true');
            card.addEventListener('dragstart', handleFolderDragStart); card.addEventListener('dragover', handleFolderDragOver);
            card.addEventListener('dragenter', handleFolderDragEnter); card.addEventListener('dragleave', handleFolderDragLeave);
            card.addEventListener('drop', handleFolderDrop); card.addEventListener('dragend', handleFolderDragEnd);
        }

        const activeBtnClass = s.is_active ? 'active-toggle-btn' : 'active-toggle-btn btn-enable';
        const activeBtnText = s.is_active ? '🚫 停用' : '▶ 启用';

        const topRightAction = isExportMode
            ? `<input type="checkbox" class="card-export-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleSeriesExportSelect(${s.id})" />`
            : `<div class="rename-trigger" onclick="startRename(event, ${s.id}, '${s.name}')" title="重命名">✏️</div>`;

        card.innerHTML = `
            ${!s.is_active ? `<div class="inactive-badge">🛑 已停用</div>` : ''}
            ${topRightAction}
            <div class="folder-title-box">
                <div class="folder-name-text" id="nameDisplay-${s.id}">
                    <span>${s.name}</span>
                </div>
                <div id="nameEdit-${s.id}" style="display: none; width: 85%;" onclick="event.stopPropagation()">
                    <input type="text" class="form-control" id="nameInput-${s.id}" value="${s.name}" style="height: 28px; font-size: 0.8rem; text-align: center;" onblur="finishRename(${s.id})" onkeydown="handleRenameKey(event, ${s.id})">
                </div>
            </div>
            <div class="folder-icon-wrapper"><div class="tianzi-grid">${tianziHtml}</div></div>
            <div class="folder-btn-bar" onclick="event.stopPropagation()">
                <button class="small-action-btn ${activeBtnClass}" ${isExportMode ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''} onclick="toggleSeriesActive(${s.id}, ${s.is_active})">${activeBtnText}</button>
                <button class="small-action-btn del-btn" ${isExportMode ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''} onclick="deleteSeries(${s.id})">🗑 删除</button>
            </div>
        `;
        container.appendChild(card);
    });
}

function handleSearch() {
    const query = document.getElementById('searchSeriesInput').value.trim().toLowerCase();
    document.querySelectorAll('.folder-card').forEach(card => {
        const id = parseInt(card.getAttribute('data-id')); if (isNaN(id)) return;
        const series = loadedSeriesData.find(s => s.id === id); if (!series) { card.style.display = 'none'; return; }
        const seriesMatch = series.name.toLowerCase().includes(query);
        const stickerMatch = series.stickers && series.stickers.some(st => st.name.toLowerCase().includes(query));
        card.style.display = (seriesMatch || stickerMatch) ? 'flex' : 'none';
    });
}

function startRename(e, seriesId, currentName) {
    e.stopPropagation();
    const card = document.querySelector(`.folder-card[data-id="${seriesId}"]`);
    if (card) card.setAttribute('draggable', 'false');
    document.getElementById(`nameDisplay-${seriesId}`).style.display = 'none';
    const editBox = document.getElementById(`nameEdit-${seriesId}`); editBox.style.display = 'block';
    const input = document.getElementById(`nameInput-${seriesId}`); input.focus(); input.select();
}

function handleRenameKey(e, seriesId) { if (e.key === 'Enter') finishRename(seriesId); }

async function finishRename(seriesId) {
    const card = document.querySelector(`.folder-card[data-id="${seriesId}"]`);
    if (card && !isExportMode) card.setAttribute('draggable', 'true');
    const input = document.getElementById(`nameInput-${seriesId}`), newName = input.value.trim();
    const oldBox = document.getElementById(`nameDisplay-${seriesId}`), editBox = document.getElementById(`nameEdit-${seriesId}`);
    editBox.style.display = 'none'; oldBox.style.display = 'inline-flex';
    if (!newName || newName === oldBox.querySelector('span').textContent) return;
    try {
        await stickersApi.updateSeries(seriesId, newName);
        showToast("分类重命名成功！", "success"); loadStickerManagementData();
    } catch(err) { showToast(err.message, "error"); }
}

function openAddSeriesModal() {
    document.getElementById('seriesName').value = '';
    let maxSort = 0; loadedSeriesData.forEach(s => { if (s.sort_order > maxSort) maxSort = s.sort_order; });
    document.getElementById('seriesSort').value = maxSort + 1;
    document.getElementById('addSeriesModal').style.display = 'flex';
}

const closeAddSeriesModal = () => document.getElementById('addSeriesModal').style.display = 'none';

async function handleAddSeries() {
    const name = document.getElementById('seriesName').value.trim();
    const sort = parseInt(document.getElementById('seriesSort').value) || 0;
    if (!name) { showToast("请输入系列名称", "error"); return; }
    try {
        await stickersApi.createSeries(name, sort);
        showToast("系列创建成功！", "success"); closeAddSeriesModal(); loadStickerManagementData();
    } catch(err) { showToast(err.message, "error"); }
}

async function toggleSeriesActive(seriesId, currentActive) {
    try {
        await stickersApi.toggleSeriesActive(seriesId, !currentActive);
        showToast(!currentActive ? "分类已启用！" : "分类已停用！", "success"); loadStickerManagementData();
    } catch(err) { showToast(err.message, "error"); }
}

function deleteSeries(seriesId) {
    const series = loadedSeriesData.find(s => s.id === seriesId); if (!series) return;
    const stickerCount = series.stickers ? series.stickers.length : 0;
    
    if (stickerCount > 0) {
        openCustomConfirm(`⚠️ 警告：贴纸系列【${series.name}】下包含 ${stickerCount} 张贴纸。删除系列将同时物理清空并删除其下的所有贴纸图片！是否确定继续？`, () => {
            openCustomConfirm(`🚨 终极操作确认：此操作不可逆！该系列下的 ${stickerCount} 张贴纸图片及关联记录将被彻底物理删除。请再次确认！`, async () => {
                try {
                    await stickersApi.deleteSeriesCascade(seriesId);
                    showToast("✨ 贴纸系列及其关联贴纸已成功彻底删除！", "success");
                    loadStickerManagementData();
                } catch(err) { showToast(err.message, "error"); }
            });
        });
    } else {
        openCustomConfirm(`确定要删除空系列【${series.name}】吗？`, async () => {
            try {
                await stickersApi.deleteSeries(seriesId);
                showToast("分类删除成功！", "success"); loadStickerManagementData();
            } catch(err) { showToast(err.message, "error"); }
        });
    }
}

let isStickerBatchDeleteMode = false;
let selectedStickerIds = new Set();

function openFolderDetail(seriesId) {
    activeFolderId = seriesId; const series = loadedSeriesData.find(s => s.id === seriesId); if (!series) return;
    exitStickerBatchDeleteMode();
    renderStickerList(series);
    updateFolderDetailTitle(series);
    const addBtn = document.getElementById('btnAddStickerTrigger');
    if (!series.is_active) { addBtn.style.display = 'none'; }
    else { addBtn.style.display = 'block'; }
    document.getElementById('folderDetailModal').style.display = 'flex';
}

const closeFolderDetailModal = () => { 
    exitStickerBatchDeleteMode();
    activeFolderId = null; 
    document.getElementById('folderDetailModal').style.display = 'none'; 
};

function enterStickerBatchDeleteMode() {
    isStickerBatchDeleteMode = true;
    selectedStickerIds.clear();
    document.getElementById('normalDetailActions').style.display = 'none';
    document.getElementById('batchDeleteDetailActions').style.display = 'flex';
    document.getElementById('selectAllDetailStickersBox').checked = false;
    updateBatchStickerDeleteButtonText();
    const series = loadedSeriesData.find(s => s.id === activeFolderId);
    if (series) renderStickerList(series);
}

function exitStickerBatchDeleteMode() {
    isStickerBatchDeleteMode = false;
    selectedStickerIds.clear();
    const normalActions = document.getElementById('normalDetailActions');
    const batchActions = document.getElementById('batchDeleteDetailActions');
    if (normalActions) normalActions.style.display = 'flex';
    if (batchActions) batchActions.style.display = 'none';
    const series = loadedSeriesData.find(s => s.id === activeFolderId);
    if (series) renderStickerList(series);
}

function toggleStickerSelect(stId) {
    if (selectedStickerIds.has(stId)) {
        selectedStickerIds.delete(stId);
    } else {
        selectedStickerIds.add(stId);
    }
    const item = document.querySelector(`.sticker-item[data-id="${stId}"]`);
    if (item) {
        const isSelected = selectedStickerIds.has(stId);
        const cb = item.querySelector('.sticker-batch-checkbox');
        if (cb) cb.checked = isSelected;
        if (isSelected) item.classList.add('batch-delete-selected');
        else item.classList.remove('batch-delete-selected');
    }
    const series = loadedSeriesData.find(s => s.id === activeFolderId);
    const allCount = (series && series.stickers) ? series.stickers.length : 0;
    document.getElementById('selectAllDetailStickersBox').checked = (allCount > 0 && selectedStickerIds.size === allCount);
    updateBatchStickerDeleteButtonText();
}

function toggleSelectAllDetailStickers(e) {
    const isChecked = e.target.checked;
    selectedStickerIds.clear();
    const series = loadedSeriesData.find(s => s.id === activeFolderId);
    if (isChecked && series && series.stickers) {
        series.stickers.forEach(st => selectedStickerIds.add(st.id));
    }
    if (series) renderStickerList(series);
    updateBatchStickerDeleteButtonText();
}

function updateBatchStickerDeleteButtonText() {
    const count = selectedStickerIds.size;
    const btn = document.getElementById('btnConfirmBatchDeleteStickers');
    if (btn) {
        btn.textContent = `🔥 确认删除 (${count})`;
        btn.disabled = count === 0;
        btn.style.opacity = count === 0 ? '0.5' : '1';
        btn.style.cursor = count === 0 ? 'not-allowed' : 'pointer';
    }
}

async function handleConfirmBatchDeleteStickersSubmit() {
    if (selectedStickerIds.size === 0) {
        showToast("请至少勾选 1 张要删除的贴纸！", "error");
        return;
    }
    const count = selectedStickerIds.size;
    openCustomConfirm(`⚠️ 确定要批量物理清理并删除选中的 ${count} 张贴纸吗？删除后对应图片文件将被彻底清理！`, async () => {
        const btn = document.getElementById('btnConfirmBatchDeleteStickers');
        btn.disabled = true; btn.textContent = "⏳ 删除中...";
        try {
            await stickersApi.batchDeleteStickers(Array.from(selectedStickerIds));
            showToast(`✨ 成功彻底删除 ${count} 张贴纸！`, "success");
            exitStickerBatchDeleteMode();
            loadStickerManagementData();
        } catch (err) {
            showToast(err.message, "error");
            updateBatchStickerDeleteButtonText();
        }
    });
}

function renderStickerList(series) {
    const grid = document.getElementById('stickerDetailGrid'); grid.innerHTML = '';
    if (!series.stickers || series.stickers.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 20px; color: var(--text-muted); font-size: 0.8rem;">无贴纸，请导入新贴纸</div>`;
        return;
    }
    series.stickers.forEach(st => {
        let img = st.image_url;
        if (img && !img.startsWith('/static/')) img = '/static/images/dinosaurs/' + img;
        const isSelected = selectedStickerIds.has(st.id);
        const item = document.createElement('div');
        item.className = `sticker-item ${isStickerBatchDeleteMode ? 'batch-delete-active' : ''} ${isSelected ? 'batch-delete-selected' : ''}`;
        item.setAttribute('data-id', st.id);

        if (isStickerBatchDeleteMode) {
            item.onclick = () => toggleStickerSelect(st.id);
        } else {
            item.onclick = () => { if (series.is_active) openEditStickerModal(st); };
            if (series.is_active) {
                item.setAttribute('draggable', 'true');
                item.addEventListener('dragstart', handleDragStart); item.addEventListener('dragover', handleDragOver);
                item.addEventListener('dragenter', handleDragEnter); item.addEventListener('dragleave', handleDragLeave);
                item.addEventListener('drop', handleDrop); item.addEventListener('dragend', handleDragEnd);
            }
        }

        const topRightIcon = isStickerBatchDeleteMode
            ? `<input type="checkbox" class="sticker-batch-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleStickerSelect(${st.id})" />`
            : (series.is_active ? `<div class="sticker-delete-trigger" onclick="deleteSticker(event, ${st.id}, '${st.name}')">🗑</div>` : '');

        item.innerHTML = `
            ${topRightIcon}
            <img src="${img}" onerror="this.src='/static/images/ic_launcher.png'" />
            <div class="sticker-item-name" title="${st.name}">${st.name}</div>
            <div class="sticker-item-price">💸 ${st.exchange_price}</div>
        `;
        grid.appendChild(item);
    });
}

function deleteSticker(e, stickerId, stickerName) {
    e.stopPropagation();
    openCustomConfirm(`确定要软删除贴纸【${stickerName}】吗？`, async () => {
        try {
            await stickersApi.deleteSticker(stickerId);
            showToast("贴纸删除成功！", "success"); loadStickerManagementData();
        } catch(err) { showToast(err.message, "error"); }
    });
}

function openAddStickerModal() {
    if (activeFolderId === null) return;
    document.getElementById('targetFolderSeriesId').value = activeFolderId;
    document.getElementById('stickerName').value = ''; document.getElementById('stickerPrice').value = '10';
    document.getElementById('stickerDesc').value = '';
    document.getElementById('stickerFile').value = '';
    
    // 重置裁剪预览占位状态
    document.getElementById('cropImage').src = '';
    document.getElementById('cropImage').style.display = 'none';
    const placeholder = document.getElementById('stickerCropPlaceholder');
    if (placeholder) placeholder.style.display = 'flex';
    
    let maxSort = 0;
    const series = loadedSeriesData.find(s => s.id === activeFolderId);
    if (series && series.stickers) {
        series.stickers.forEach(st => {
            if (st.sort_order > maxSort) maxSort = st.sort_order;
        });
    }
    document.getElementById('stickerSort').value = maxSort + 1;
    
    if (activeCropper) { activeCropper.destroy(); activeCropper = null; }
    document.getElementById('addStickerModal').style.display = 'flex';
}

function closeAddStickerModal() { if (activeCropper) { activeCropper.destroy(); activeCropper = null; } document.getElementById('addStickerModal').style.display = 'none'; }

function handleFileSelect(e) {
    const file = e.target.files[0]; if (!file) return;
    loadBlobToStickerCropper(file);
}

function loadBlobToStickerCropper(blob) {
    const reader = new FileReader();
    reader.onload = function(event) {
        const cropImage = document.getElementById('cropImage');
        cropImage.src = event.target.result;
        cropImage.style.display = 'block';
        
        const placeholder = document.getElementById('stickerCropPlaceholder');
        if (placeholder) placeholder.style.display = 'none';
        
        if (activeCropper) activeCropper.destroy();
        activeCropper = new Cropper(cropImage, {
            aspectRatio: 1,
            viewMode: 0,
            dragMode: 'move',
            background: true,
            autoCropArea: 1.0,
            responsive: true,
            restore: false,
            checkCrossOrigin: false,
            toggleDragModeOnDblclick: false
        });
    };
    reader.readAsDataURL(blob);
}

function initStickerPasteAndDragEvent() {
    document.addEventListener("paste", (e) => {
        const addStickerModal = document.getElementById("addStickerModal");
        if (addStickerModal && (addStickerModal.style.display === "flex" || addStickerModal.style.display === "block")) {
            const items = e.clipboardData || e.originalEvent?.clipboardData;
            if (!items) return;
            for (const item of items.items) {
                if (item.type.indexOf("image") !== -1) {
                    const blob = item.getAsFile();
                    loadBlobToStickerCropper(blob);
                    e.preventDefault();
                    break;
                }
            }
        }
    });
    
    const wrapper = document.getElementById("stickerCropWrapper");
    if (wrapper) {
        wrapper.addEventListener("dragover", (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = "copy";
            wrapper.style.borderColor = "#7c3aed";
            wrapper.style.background = "rgba(124, 58, 237, 0.05)";
        });
        
        wrapper.addEventListener("dragleave", (e) => {
            e.preventDefault();
            wrapper.style.borderColor = "rgba(255, 255, 255, 0.08)";
            wrapper.style.background = "rgba(255, 255, 255, 0.01)";
        });
        
        wrapper.addEventListener("drop", (e) => {
            e.preventDefault();
            wrapper.style.borderColor = "rgba(255, 255, 255, 0.08)";
            wrapper.style.background = "rgba(255, 255, 255, 0.01)";
            
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                const file = files[0];
                if (file.type.startsWith("image/")) {
                    loadBlobToStickerCropper(file);
                }
            }
        });
    }
}

function handleUploadSticker() {
    const name = document.getElementById('stickerName').value.trim(), seriesId = document.getElementById('targetFolderSeriesId').value;
    const price = document.getElementById('stickerPrice').value, sort = document.getElementById('stickerSort').value, desc = document.getElementById('stickerDesc').value.trim();
    if (!name) { showToast("请输入贴纸名称", "error"); return; }
    if (name.length > 6) { showToast("贴纸名称最多限制 6 个汉字/字符", "error"); return; }
    if (!activeCropper) { showToast("请先选择贴纸原始图片", "error"); return; }
    const btn = document.getElementById('btnConfirmUpload'); btn.disabled = true; btn.textContent = "上传中...";
    const canvas = activeCropper.getCroppedCanvas({ width: 256, height: 256, imageSmoothingEnabled: true, imageSmoothingQuality: 'high' });
    canvas.toBlob(async function(blob) {
        if (!blob) { showToast("裁剪失败", "error"); btn.disabled = false; btn.textContent = "确认上传并保存"; return; }
        const formData = new FormData(); formData.append('file', blob, 'sticker_cropped.png');
        formData.append('series_id', seriesId); formData.append('name', name);
        formData.append('description', desc); formData.append('sort_order', sort); formData.append('exchange_price', price);
        try {
            await stickersApi.uploadSticker(formData);
            showToast("贴纸上传成功！", "success"); closeAddStickerModal(); loadStickerManagementData();
        } catch(err) { showToast(err.message, "error"); } finally { btn.disabled = false; btn.textContent = "确认上传并保存"; }
    }, 'image/png');
}

function openEditStickerModal(st) {
    activeStickerObj = st;
    document.getElementById('editStickerId').value = st.id;
    document.getElementById('editStickerName').value = st.name;
    document.getElementById('editStickerPrice').value = st.exchange_price;
    document.getElementById('editStickerSort').value = st.sort_order;
    document.getElementById('editStickerDesc').value = st.description || '';
    document.getElementById('editStickerFile').value = '';
    
    let imgUrl = st.image_url;
    if (imgUrl && !imgUrl.startsWith('/static/')) imgUrl = '/static/images/dinosaurs/' + imgUrl;
    document.getElementById('editStickerCurrentImg').src = imgUrl;
    document.getElementById('editStickerCurrentImgWrapper').style.display = 'block';
    document.getElementById('editCropContainer').style.display = 'none';
    
    if (editCropper) { editCropper.destroy(); editCropper = null; }
    document.getElementById('editStickerModal').style.display = 'flex';
}

function closeEditStickerModal() { if (editCropper) { editCropper.destroy(); editCropper = null; } document.getElementById('editStickerModal').style.display = 'none'; }

function handleEditFileSelect(e) {
    const file = e.target.files[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = function(event) {
        document.getElementById('editStickerCurrentImgWrapper').style.display = 'none';
        const cropImage = document.getElementById('editCropImage'); cropImage.src = event.target.result;
        document.getElementById('editCropContainer').style.display = 'block';
        if (editCropper) editCropper.destroy();
        editCropper = new Cropper(cropImage, {
            aspectRatio: 1,
            viewMode: 0,
            dragMode: 'move',
            background: true,
            autoCropArea: 1.0,
            responsive: true,
            restore: false,
            checkCrossOrigin: false,
            toggleDragModeOnDblclick: false
        });
    };
    reader.readAsDataURL(file);
}

function handleUpdateSticker() {
    const id = document.getElementById('editStickerId').value, name = document.getElementById('editStickerName').value.trim();
    const price = document.getElementById('editStickerPrice').value, sort = document.getElementById('editStickerSort').value, desc = document.getElementById('editStickerDesc').value.trim();
    if (!name) { showToast("请输入贴纸名称", "error"); return; }
    if (name.length > 6) { showToast("贴纸名称最多限制 6 个汉字/字符", "error"); return; }
    const btn = document.getElementById('btnConfirmEdit'); btn.disabled = true; btn.textContent = "保存中...";
    const doUpdate = async (blob) => {
        const formData = new FormData(); formData.append('name', name); formData.append('exchange_price', price);
        formData.append('sort_order', sort); formData.append('description', desc);
        if (blob) formData.append('file', blob, 'sticker_edited.png');
        try {
            await stickersApi.updateSticker(id, formData);
            showToast("贴纸修改保存成功！", "success"); closeEditStickerModal(); loadStickerManagementData();
        } catch(err) { showToast(err.message, "error"); } finally { btn.disabled = false; btn.textContent = "确认保存修改"; }
    };
    if (editCropper) {
        const canvas = editCropper.getCroppedCanvas({ width: 256, height: 256, imageSmoothingEnabled: true, imageSmoothingQuality: 'high' });
        canvas.toBlob(doUpdate, 'image/png');
    } else doUpdate(null);
}

function enterExportMode() {
    isExportMode = true;
    selectedExportSeriesIds.clear();
    document.getElementById('normalHeaderActions').style.display = 'none';
    document.getElementById('exportHeaderActions').style.display = 'flex';
    document.getElementById('selectAllPageCheckbox').checked = false;
    updateExportModeButtonText();
    renderFolders(loadedSeriesData);
}

function exitExportMode() {
    isExportMode = false;
    selectedExportSeriesIds.clear();
    document.getElementById('exportHeaderActions').style.display = 'none';
    document.getElementById('normalHeaderActions').style.display = 'flex';
    renderFolders(loadedSeriesData);
}

function toggleSeriesExportSelect(seriesId) {
    if (selectedExportSeriesIds.has(seriesId)) {
        selectedExportSeriesIds.delete(seriesId);
    } else {
        selectedExportSeriesIds.add(seriesId);
    }
    
    const card = document.querySelector(`.folder-card[data-id="${seriesId}"]`);
    if (card) {
        const isSelected = selectedExportSeriesIds.has(seriesId);
        const cb = card.querySelector('.card-export-checkbox');
        if (cb) cb.checked = isSelected;
        if (isSelected) card.classList.add('export-selected');
        else card.classList.remove('export-selected');
    }
    
    const allCount = loadedSeriesData ? loadedSeriesData.length : 0;
    document.getElementById('selectAllPageCheckbox').checked = (allCount > 0 && selectedExportSeriesIds.size === allCount);
    updateExportModeButtonText();
}

function toggleSelectAllPage(e) {
    const isChecked = e.target.checked;
    selectedExportSeriesIds.clear();
    if (isChecked && loadedSeriesData) {
        loadedSeriesData.forEach(s => selectedExportSeriesIds.add(s.id));
    }
    renderFolders(loadedSeriesData);
    updateExportModeButtonText();
}

function updateExportModeButtonText() {
    const count = selectedExportSeriesIds.size;
    const btn = document.getElementById('btnConfirmExportMode');
    if (btn) {
        btn.textContent = `🚀 确认导出 (${count})`;
        btn.disabled = count === 0;
        btn.style.opacity = count === 0 ? '0.5' : '1';
        btn.style.cursor = count === 0 ? 'not-allowed' : 'pointer';
    }
}

async function handleConfirmExportModeSubmit() {
    if (selectedExportSeriesIds.size === 0) {
        showToast("请至少勾选 1 个要导出的贴纸系列", "error");
        return;
    }
    const ids = Array.from(selectedExportSeriesIds).join(',');
    const btn = document.getElementById('btnConfirmExportMode');
    btn.disabled = true; btn.textContent = "⏳ 正在打包中...";
    try {
        const res = await stickersApi.exportStickers(ids);
        const blob = await res.blob();
        let fileName = `dinoroar_stickers_export_${new Date().getTime()}.zip`;
        const contentDisposition = res.headers.get('Content-Disposition');
        if (contentDisposition && contentDisposition.includes('filename=')) {
            fileName = contentDisposition.split('filename=')[1].replace(/"/g, '');
        }
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = fileName;
        document.body.appendChild(a); a.click(); a.remove();
        window.URL.revokeObjectURL(url);
        showToast("✨ 贴纸包打包导出成功，已自动下载！", "success");
        exitExportMode();
    } catch (err) {
        showToast(err.message, "error");
        updateExportModeButtonText();
    }
}

function triggerImportStickerPack() {
    const fileInput = document.getElementById('importZipFileInput');
    fileInput.value = '';
    fileInput.click();
}

async function handleImportZipSelected(event) {
    const file = event.target.files[0];
    if (!file) return;
    document.getElementById('importZipFileName').textContent = file.name;
    
    const formData = new FormData();
    formData.append('file', file);
    
    showToast("正在读取解析贴纸包...", "info");
    try {
        const data = await stickersApi.importPreview(formData);
        renderImportPreviewModal(data);
    } catch(err) {
        showToast(err.message, "error");
    }
}

function renderImportPreviewModal(data) {
    document.getElementById('importTempToken').value = data.temp_token;
    const container = document.getElementById('importSeriesPreviewContainer');
    container.innerHTML = '';
    
    if (!data.series_list || data.series_list.length === 0) {
        container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">未扫描到任何有效的贴纸系列</div>`;
        return;
    }
    
    data.series_list.forEach((s, idx) => {
        let thumbsHtml = '';
        if (s.stickers && s.stickers.length > 0) {
            s.stickers.forEach(st => {
                const imgSrc = st.image_b64 || '/static/images/ic_launcher.png';
                thumbsHtml += `<div class="import-thumb-box" title="点击查看大图: ${st.name}" onclick="openStickerImagePreview('${imgSrc}', '${st.name}')" style="cursor: pointer;"><img src="${imgSrc}" onerror="this.src='/static/images/ic_launcher.png'" /></div>`;
            });
        }
        
        const item = document.createElement('div');
        item.className = 'import-series-item';
        item.innerHTML = `
            <div class="import-series-header">
                <div class="import-series-title">
                    <input type="checkbox" class="import-series-checkbox" value="${s.series_name}" checked style="width: 16px; height: 16px; accent-color: #7c3aed; cursor: pointer;" />
                    <span>📁 ${s.series_name}</span>
                    ${s.is_name_conflict ? `<span class="import-conflict-badge">⚠️ 本地已存在同名系列</span>` : ''}
                </div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">共 ${s.sticker_count} 张贴纸</div>
            </div>
            <div class="import-thumbnails-strip">${thumbsHtml}</div>
        `;
        container.appendChild(item);
    });
    
    document.getElementById('importPreviewModal').style.display = 'flex';
}

function closeImportPreviewModal() {
    document.getElementById('importPreviewModal').style.display = 'none';
}

async function handleConfirmImportSubmit() {
    const tempToken = document.getElementById('importTempToken').value;
    const selectedBoxes = [...document.querySelectorAll('.import-series-checkbox:checked')];
    if (selectedBoxes.length === 0) {
        showToast("请至少勾选 1 个需要导入的贴纸系列！", "error");
        return;
    }
    const selectedSeriesNames = selectedBoxes.map(b => b.value);
    const radioVal = document.querySelector('input[name="conflictResolution"]:checked')?.value || 'rename';
    
    const btn = document.getElementById('btnConfirmImport');
    btn.disabled = true; btn.textContent = "⏳ 正在写入落库...";
    try {
        const result = await stickersApi.importConfirm(tempToken, selectedSeriesNames, radioVal);
        showToast(`🎉 成功导入 ${result.imported_series_count || 0} 个贴纸系列！`, "success");
        closeImportPreviewModal();
        loadStickerManagementData();
    } catch(err) {
        showToast(err.message, "error");
    } finally {
        btn.disabled = false; btn.textContent = "🚀 确认导入已选系列";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const modals = document.querySelectorAll(".modal");
    modals.forEach(modal => {
        let isMouseDownOnModalContent = false;
        const content = modal.querySelector(".modal-content");
        if (content) {
            content.addEventListener("mousedown", (e) => {
                isMouseDownOnModalContent = true;
            });
        }
        modal.addEventListener("mousedown", (e) => {
            if (e.target === modal) {
                isMouseDownOnModalContent = false;
            }
        });
        modal.addEventListener("click", (e) => {
            if (e.target === modal && !isMouseDownOnModalContent) {
                if (modal.id === 'folderDetailModal') closeFolderDetailModal();
                else if (modal.id === 'addSeriesModal') closeAddSeriesModal();
                else if (modal.id === 'addStickerModal') closeAddStickerModal();
                else if (modal.id === 'editStickerModal') closeEditStickerModal();
                else if (modal.id === 'customConfirmModal') { modal.style.display = 'none'; }
                else if (modal.id === 'importPreviewModal') closeImportPreviewModal();
                else if (modal.id === 'imageLightboxModal') closeImageLightboxModal();
            }
            isMouseDownOnModalContent = false;
        });
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            const visibleModals = [...document.querySelectorAll(".modal")].filter(m => m.style.display === "flex" || m.style.display === "block");
            if (visibleModals.length > 0) {
                const modal = visibleModals[visibleModals.length - 1];
                if (modal.id === 'folderDetailModal') closeFolderDetailModal();
                else if (modal.id === 'addSeriesModal') closeAddSeriesModal();
                else if (modal.id === 'addStickerModal') closeAddStickerModal();
                else if (modal.id === 'editStickerModal') closeEditStickerModal();
                else if (modal.id === 'customConfirmModal') { modal.style.display = 'none'; }
                else if (modal.id === 'importPreviewModal') closeImportPreviewModal();
                else if (modal.id === 'imageLightboxModal') closeImageLightboxModal();
            }
        }
    });
    loadStickerManagementData();
    initStickerPasteAndDragEvent();
});
