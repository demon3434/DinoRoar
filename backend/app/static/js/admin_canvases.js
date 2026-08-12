let allConfig = [];
let activeFolderId = null;
let cropperInstance = null;
let currentActiveRatios = {}; // 记录每个商品套当前选中的分辨率预览，例如：{ 3001: "16:9" }

const ratioMap = {
    "16:9": 16 / 9,
    "4:3": 4 / 3,
    "1:1": 1.0,
    "2:1": 2.0
};

document.addEventListener("DOMContentLoaded", () => {
    loadConfig();
    initLightboxEvents();
    bindModalOverlayEvents();
    initPasteImageEvent();
    initDragDropImageEvent();
});

async function loadConfig() {
    try {
        allConfig = await canvasesApi.fetchConfig();
        renderFolders(allConfig);
        
        // 如果详情窗口开着，同步渲染
        if (activeFolderId !== null) {
            const activeSeries = allConfig.find(s => s.id === activeFolderId);
            if (activeSeries) {
                renderSetsGrid(activeSeries);
            } else {
                closeFolderDetailModal();
            }
        }
        populateSeriesDropdown();
    } catch (e) {
        console.error("加载后台配置失败", e);
    }
}

// ==================== 1. 主页分类文件夹（Folders）渲染 ====================
function renderFolders(data) {
    const container = document.getElementById("seriesContainer");
    container.innerHTML = "";
    
    if (!data || data.length === 0) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">暂无任何分类系列，请点击上方新建</div>`;
        return;
    }
    
    data.forEach(s => {
        // 田字格预览图拼装
        let tianziHtml = "";
        for (let i = 0; i < 4; i++) {
            if (s.sets && s.sets[i]) {
                const cset = s.sets[i];
                // 找 16:9 -> 4:3 -> 1:1 -> 2:1 中任意一个作为首图
                const ratios = ["16:9", "4:3", "1:1", "2:1"];
                let imgUrl = "";
                for (const r of ratios) {
                    const inst = cset.instances.find(inst => inst.aspect_ratio === r && !inst.is_deleted);
                    if (inst && inst.image_url) {
                        imgUrl = inst.image_url;
                        break;
                    }
                }
                if (imgUrl) {
                    tianziHtml += `<div class="tianzi-cell"><img src="${imgUrl}?v=202608110023" onerror="this.src='/static/images/ic_launcher.png'" /></div>`;
                } else {
                    tianziHtml += `<div class="tianzi-cell"></div>`;
                }
            } else {
                tianziHtml += `<div class="tianzi-cell"></div>`;
            }
        }
        
        const isSelected = exportSelectedIds.has(s.id);
        const card = document.createElement("div");
        card.className = `folder-card ${s.is_active ? '' : 'grayscale-active'} ${exportModeActive ? 'export-mode-active' : ''} ${isSelected ? 'export-selected' : ''}`;
        card.setAttribute("data-id", s.id);

        if (exportModeActive) {
            // 导出模式：点击整卡切换选中，禁止拖拽
            card.onclick = () => toggleSeriesExportSelect(s.id);
        } else {
            // 正常模式：点击打开详情，允许拖拽
            card.onclick = () => openFolderDetail(s.id);
            card.setAttribute("draggable", "true");
            card.addEventListener("dragstart", handleFolderDragStart);
            card.addEventListener("dragover", handleFolderDragOver);
            card.addEventListener("dragenter", handleFolderDragEnter);
            card.addEventListener("dragleave", handleFolderDragLeave);
            card.addEventListener("drop", handleFolderDrop);
            card.addEventListener("dragend", handleFolderDragEnd);
        }
        
        const activeBtnClass = s.is_active ? "active-toggle-btn" : "active-toggle-btn btn-enable";
        const activeBtnText = s.is_active ? "🚫 停用" : "🟢 启用";
        
        // 右上角：导出模式显示 checkbox，否则显示重命名触发器
        const topRightAction = exportModeActive
            ? `<input type="checkbox" class="card-export-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleSeriesExportSelect(${s.id})" />`
            : `<div class="rename-trigger" onclick="startRename(event, ${s.id}, '${s.name}')" title="重命名分类">✏️</div>`;

        card.innerHTML = `
            ${!s.is_active ? `<div class="inactive-badge">🛑 已停用</div>` : ""}
            ${topRightAction}
            <div class="folder-title-box">
                <div class="folder-name-text" id="nameDisplay-${s.id}">
                    <span>${s.name}</span>
                </div>
                <div id="nameEdit-${s.id}" style="display: none; width: 85%;" onclick="event.stopPropagation()">
                    <input type="text" class="form-control" id="nameInput-${s.id}" value="${s.name}" style="height: 28px; font-size: 0.8rem; text-align: center;" onblur="finishRename(${s.id})" onkeydown="handleRenameKey(event, ${s.id})">
                </div>
            </div>
            <div class="folder-icon-wrapper">
                <div class="tianzi-grid">${tianziHtml}</div>
            </div>
            <div class="folder-btn-bar" onclick="event.stopPropagation()">
                <button class="small-action-btn ${activeBtnClass}" ${exportModeActive ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''} onclick="toggleSeriesActive(${s.id}, ${s.is_active})">${activeBtnText}</button>
                <button class="small-action-btn del-btn" ${exportModeActive ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''} onclick="deleteSeries(${s.id})">🗑 删除</button>
            </div>
        `;
        container.appendChild(card);
    });
}


function startRename(e, seriesId, currentName) {
    e.stopPropagation();
    setDraggableState(false);
    document.getElementById(`nameDisplay-${seriesId}`).style.display = "none";
    const editBox = document.getElementById(`nameEdit-${seriesId}`);
    editBox.style.display = "block";
    const input = document.getElementById(`nameInput-${seriesId}`);
    input.focus();
    input.select();
}

function handleRenameKey(e, seriesId) {
    if (e.key === "Enter") {
        finishRename(seriesId);
    }
}

async function finishRename(seriesId) {
    setDraggableState(true);
    const input = document.getElementById(`nameInput-${seriesId}`);
    const newName = input.value.trim();
    const oldBox = document.getElementById(`nameDisplay-${seriesId}`);
    const editBox = document.getElementById(`nameEdit-${seriesId}`);
    
    editBox.style.display = "none";
    oldBox.style.display = "inline-flex";
    
    if (!newName || newName === oldBox.querySelector("span").textContent) return;
    
    try {
        await canvasesApi.updateSeries(seriesId, newName, 0);
        showToast("重命名分类成功！", "success");
        loadConfig();
    } catch (e) {
        showToast(e.message, "error");
    }
}

async function toggleSeriesActive(seriesId, currentActive) {
    const verb = currentActive ? "停用" : "启用";
    openCustomConfirm(`确定要${verb}该分类系列吗？`, async () => {
        try {
            await canvasesApi.toggleSeriesActive(seriesId);
            showToast(`已成功${verb}分类系列`, "success");
            loadConfig();
        } catch (e) {
            showToast(e.message, "error");
        }
    });
}

async function deleteSeries(seriesId) {
    openCustomConfirm("❗ 确定要级联删除此系列分类吗？删除后，该分类下所有背景画布和图片都会被级联删除！", async () => {
        try {
            await canvasesApi.deleteSeriesCascade(seriesId);
            showToast("分类已成功级联删除！", "success");
            loadConfig();
        } catch (e) {
            showToast(e.message, "error");
        }
    });
}

function openSeriesModal(seriesId = null) {
    const modal = document.getElementById("seriesModal");
    const title = document.getElementById("seriesModalTitle");
    const nameInput = document.getElementById("seriesName");
    const sortInput = document.getElementById("seriesSort");
    
    nameInput.value = "";
    sortInput.value = 0;
    
    if (seriesId) {
        title.textContent = "✏️ 编辑分类系列";
        const series = allConfig.find(s => s.id === seriesId);
        if (series) {
            nameInput.value = series.name;
            sortInput.value = series.sort_order;
            modal.setAttribute("data-edit-id", seriesId);
        }
    } else {
        title.textContent = "✨ 新建分类系列";
        modal.removeAttribute("data-edit-id");
    }
    modal.style.display = "flex";
}

function closeSeriesModal() {
    const modal = document.getElementById("seriesModal");
    modal.removeAttribute("data-edit-id");
    modal.style.display = "none";
}

async function saveSeries() {
    const modal = document.getElementById("seriesModal");
    const editId = modal.getAttribute("data-edit-id");
    const name = document.getElementById("seriesName").value.trim();
    const sortOrder = parseInt(document.getElementById("seriesSort").value) || 0;
    
    if (!name) {
        showToast("请输入分类名称", "error");
        return;
    }
    
    try {
        if (editId) {
            await canvasesApi.updateSeries(editId, name, sortOrder);
            showToast("编辑分类成功！", "success");
        } else {
            await canvasesApi.createSeries(name, sortOrder);
            showToast("创建分类成功！", "success");
        }
        closeSeriesModal();
        loadConfig();
    } catch (e) {
        showToast(e.message, "error");
    }
}

// ==================== 2. 画布详情弹窗/商品套渲染 ====================
function openFolderDetail(seriesId) {
    activeFolderId = seriesId;
    const series = allConfig.find(s => s.id === seriesId);
    if (series) {
        document.getElementById("detailModalTitle").textContent = `${series.name} - 画布列表`;
        renderSetsGrid(series);
    }
    document.getElementById("folderDetailModal").style.display = "flex";
}

function closeFolderDetailModal() {
    activeFolderId = null;
    document.getElementById("folderDetailModal").style.display = "none";
}

function populateSeriesDropdown() {
    const select = document.getElementById("setSeriesId");
    if (!select) return;
    select.innerHTML = "";
    allConfig.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.name;
        select.appendChild(opt);
    });
}

function renderSetsGrid(series) {
    const container = document.getElementById("setsDetailGrid");
    container.innerHTML = "";
    
    if (!series.sets || series.sets.length === 0) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">该系列分类下暂无画布背景</div>`;
        return;
    }
    
    series.sets.forEach(cset => {
        let activeRatio = currentActiveRatios[cset.id];
        if (!activeRatio) {
            activeRatio = "16:9";
            currentActiveRatios[cset.id] = activeRatio;
        }
        
        const inst = cset.instances.find(i => i.aspect_ratio === activeRatio && !i.is_deleted);
        
        const card = document.createElement("div");
        card.className = `set-detail-card ${cset.is_active ? '' : 'grayscale-active'}`;
        card.setAttribute("data-id", cset.id);
        card.setAttribute("draggable", "true");
        card.addEventListener("dragstart", handleSetDragStart);
        card.addEventListener("dragover", handleSetDragOver);
        card.addEventListener("dragenter", handleSetDragEnter);
        card.addEventListener("dragleave", handleSetDragLeave);
        card.addEventListener("drop", handleSetDrop);
        card.addEventListener("dragend", handleSetDragEnd);
        
        let imgHtml = "";
        if (inst && inst.image_url) {
            const aspectStyle = activeRatio.replace(":", "/");
            imgHtml = `<img class="set-card-preview-img" style="aspect-ratio: ${aspectStyle};" src="${inst.image_url}" onclick="openLightbox('${inst.image_url}', '${cset.name} - ${activeRatio}')" />`;
        } else {
            imgHtml = `<div style="display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--text-muted);">
                <span style="font-size: 1.8rem; opacity: 0.6;">🖼️</span>
                <span style="font-size: 0.72rem; font-weight: 500; letter-spacing: 0.5px; color: #a78bfa;">待上传 ${activeRatio} 比例底图</span>
            </div>`;
        }
        
        const badgeHtml = cset.is_active ? "" : `<div class="inactive-badge">🛑 已停用</div>`;
        
        let switcherHtml = "";
        ["16:9", "4:3", "1:1", "2:1"].forEach(r => {
            const hasImg = cset.instances.some(i => i.aspect_ratio === r && !i.is_deleted);
            const isActive = (r === activeRatio) ? "active" : "";
            switcherHtml += `<button class="btn-ratio-switch ${isActive}" onclick="changeSetRatio(${cset.id}, '${r}')">
                ${r}${hasImg ? '<span class="has-img-dot"></span>' : ''}
            </button>`;
        });
        
        const statusBtnClass = cset.is_active ? "btn-status-toggle" : "btn-status-toggle btn-enable";
        const statusBtnIcon = cset.is_active ? "🚫" : "🟢";
        const statusBtnTitle = cset.is_active ? "停用画布" : "启用画布";
        
        const delBtnHtml = cset.id === 3001
            ? `<button class="btn-icon del-btn disabled" disabled title="内置预设底图不可删除" style="opacity: 0.3; cursor: not-allowed;">🗑</button>`
            : `<button class="btn-icon del-btn" onclick="deleteSet(${cset.id})" title="删除画布">🗑</button>`;
        
        card.innerHTML = `
            <div class="set-card-preview-box">
                ${badgeHtml}
                ${imgHtml}
                <div class="set-card-title-banner">
                    <div class="set-card-name-banner" title="${cset.name}">${cset.name}</div>
                    <div class="set-card-price-banner">💸 ${cset.exchange_price}</div>
                </div>
            </div>
            <div class="ratio-switcher-row">${switcherHtml}</div>
            <div class="set-card-btn-bar">
                <button class="btn-icon edit-btn" onclick="openSetModal(${cset.id})" title="编辑基本属性">✏️</button>
                <button class="btn-icon upload-btn" onclick="openUploadModal(${cset.id}, '${activeRatio}')" title="上传/裁剪该比例图片">📤</button>
                <button class="btn-icon ${statusBtnClass}" onclick="toggleSetActive(${cset.id}, ${cset.is_active})" title="${statusBtnTitle}">${statusBtnIcon}</button>
                ${delBtnHtml}
            </div>
        `;
        container.appendChild(card);
    });
}

function changeSetRatio(setId, ratio) {
    currentActiveRatios[setId] = ratio;
    if (activeFolderId) {
        const series = allConfig.find(s => s.id === activeFolderId);
        if (series) renderSetsGrid(series);
    }
}

async function toggleSetActive(setId, currentActive) {
    const verb = currentActive ? "停用" : "启用";
    openCustomConfirm(`确定要${verb}该背景画布吗？`, async () => {
        try {
            await canvasesApi.toggleSetActive(setId);
            showToast(`已成功${verb}背景画布`, "success");
            loadConfig();
        } catch (e) {
            showToast(e.message, "error");
        }
    });
}

async function deleteSet(setId) {
    if (setId === 3001) {
        showToast("系统预设底图不可删除！", "error");
        return;
    }
    openCustomConfirm("❗ 确定要删除该背景画布吗？删除后下属所有比例图片都将被级联删除！", async () => {
        try {
            await canvasesApi.deleteSet(setId);
            showToast("背景画布已成功删除！", "success");
            loadConfig();
        } catch (e) {
            showToast(e.message, "error");
        }
    });
}

function openSetModal(setId = null) {
    const modal = document.getElementById("setModal");
    const title = document.getElementById("setModalTitle");
    const nameInput = document.getElementById("setName");
    const descInput = document.getElementById("setDesc");
    const priceInput = document.getElementById("setPrice");
    const sortInput = document.getElementById("setSort");
    const seriesSelect = document.getElementById("setSeriesId");
    
    nameInput.value = "";
    descInput.value = "";
    priceInput.value = 50;
    sortInput.value = 0;
    
    if (activeFolderId) {
        seriesSelect.value = activeFolderId;
    }
    
    if (setId) {
        title.textContent = "✏️ 编辑画布基本信息";
        let foundSet = null;
        allConfig.forEach(s => {
            const found = s.sets.find(st => st.id === setId);
            if (found) foundSet = found;
        });
        if (foundSet) {
            nameInput.value = foundSet.name;
            descInput.value = foundSet.description || "";
            priceInput.value = foundSet.exchange_price;
            sortInput.value = foundSet.sort_order;
            seriesSelect.value = foundSet.series_id;
            modal.setAttribute("data-edit-id", setId);
        }
    } else {
        title.textContent = "✨ 新增背景画布";
        modal.removeAttribute("data-edit-id");
    }
    modal.style.display = "flex";
}

function closeSetModal() {
    const modal = document.getElementById("setModal");
    modal.removeAttribute("data-edit-id");
    modal.style.display = "none";
}

async function saveSet() {
    const modal = document.getElementById("setModal");
    const editId = modal.getAttribute("data-edit-id");
    
    const seriesId = parseInt(document.getElementById("setSeriesId").value);
    const name = document.getElementById("setName").value.trim();
    const description = document.getElementById("setDesc").value.trim();
    const exchangePrice = parseInt(document.getElementById("setPrice").value) || 50;
    const sortOrder = parseInt(document.getElementById("setSort").value) || 0;
    
    if (!name) {
        showToast("请输入画布名称", "error");
        return;
    }
    
    try {
        if (editId) {
            await canvasesApi.updateSet(editId, seriesId, name, description, exchangePrice, sortOrder);
            showToast("编辑画布成功！", "success");
        } else {
            await canvasesApi.createSet(seriesId, name, description, exchangePrice, sortOrder);
            showToast("新增画布成功！", "success");
        }
        closeSetModal();
        loadConfig();
    } catch (e) {
        showToast(e.message, "error");
    }
}

// ==================== 3. 物理图片裁剪上传 ====================
function openUploadModal(setId, ratio) {
    document.getElementById("uploadSetId").value = setId;
    document.getElementById("uploadRatioSelect").value = ratio;
    document.getElementById("fileInput").value = "";
    
    document.getElementById("cropperImage").src = "";
    document.getElementById("cropperImage").style.display = "none";
    const placeholder = document.getElementById("cropperPlaceholder");
    if (placeholder) placeholder.style.display = "flex";
    
    const saveBtn = document.getElementById("saveUploadBtn");
    saveBtn.disabled = true;
    saveBtn.textContent = "裁剪并上传";
    
    if (cropperInstance) {
        cropperInstance.destroy();
        cropperInstance = null;
    }
    
    document.getElementById("uploadModal").style.display = "flex";
}

function closeUploadModal() {
    if (cropperInstance) {
        cropperInstance.destroy();
        cropperInstance = null;
    }
    document.getElementById("uploadModal").style.display = "none";
}

function handleUploadFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    loadBlobToCropper(file);
}

function loadBlobToCropper(blob) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = document.getElementById("cropperImage");
        img.src = e.target.result;
        img.style.display = "block";
        
        const placeholder = document.getElementById("cropperPlaceholder");
        if (placeholder) placeholder.style.display = "none";

        document.getElementById("saveUploadBtn").disabled = false;

        if (cropperInstance) {
            cropperInstance.destroy();
        }

        const selectedRatio = document.getElementById("uploadRatioSelect").value;
        const aspectVal = ratioMap[selectedRatio];

        cropperInstance = new Cropper(img, {
            aspectRatio: aspectVal,
            viewMode: 1,
            dragMode: 'move',
            autoCropArea: 1,
            restore: false,
            guides: true,
            center: true,
            highlight: false,
            cropBoxMovable: true,
            cropBoxResizable: true,
            toggleDragModeOnDblclick: false
        });
    };
    reader.readAsDataURL(blob);
}

function changeCropRatio() {
    if (!cropperInstance) return;
    const selectedRatio = document.getElementById("uploadRatioSelect").value;
    const aspectVal = ratioMap[selectedRatio];
    cropperInstance.setAspectRatio(aspectVal);
}

function saveCroppedImage() {
    if (!cropperInstance) {
        alert("请先选择并裁剪图片");
        return;
    }

    const setId = document.getElementById("uploadSetId").value;
    const selectedRatio = document.getElementById("uploadRatioSelect").value;

    const r_val = ratioMap[selectedRatio];
    const targetWidth = 1440;
    const targetHeight = Math.round(targetWidth / r_val);

    const croppedCanvas = cropperInstance.getCroppedCanvas({
        width: targetWidth,
        height: targetHeight,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high'
    });

    const saveBtn = document.getElementById("saveUploadBtn");
    saveBtn.disabled = true;
    saveBtn.textContent = "正在上传...";

    croppedCanvas.toBlob(async (blob) => {
        if (!blob) {
            alert("裁剪处理失败");
            saveBtn.disabled = false;
            saveBtn.textContent = "裁剪并上传";
            return;
        }

        const token = localStorage.getItem("token");
        const formData = new FormData();
        formData.append("canvas_set_id", setId);
        formData.append("aspect_ratio", selectedRatio);
        formData.append("file", blob, "canvas_crop.png");

        try {
            const response = await fetch("/api/canvases/admin/upload", {
                method: "POST",
                headers: { "Authorization": "Bearer " + token },
                body: formData
            });

            if (response.ok) {
                closeUploadModal();
                loadConfig();
            } else {
                const err = await response.json();
                alert(`❌ 上传失败: ${err.detail || "服务器错误"}`);
                saveBtn.disabled = false;
                saveBtn.textContent = "裁剪并上传";
            }
        } catch (e) {
            console.error("上传出错", e);
            alert("❌ 网络上传请求失败！");
            saveBtn.disabled = false;
            saveBtn.textContent = "裁剪并上传";
        }
    }, "image/png");
}

function initPasteImageEvent() {
    document.addEventListener("paste", (e) => {
        const uploadModal = document.getElementById("uploadModal");
        if (uploadModal && (uploadModal.style.display === "flex" || uploadModal.style.display === "block")) {
            const items = e.clipboardData || e.originalEvent?.clipboardData;
            if (!items) return;
            for (const item of items.items) {
                if (item.type.indexOf("image") !== -1) {
                    const blob = item.getAsFile();
                    loadBlobToCropper(blob);
                    e.preventDefault();
                    break;
                }
            }
        }
    });
}

function initDragDropImageEvent() {
    const wrapper = document.getElementById("cropperWrapper");
    if (!wrapper) return;
    
    wrapper.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "copy";
        wrapper.style.borderColor = "#8b5cf6";
        wrapper.style.background = "rgba(139, 92, 246, 0.05)";
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
                loadBlobToCropper(file);
            }
        }
    });
}

function openCustomConfirm(message, onConfirm) {
    document.getElementById("confirmMessage").textContent = message;
    const modal = document.getElementById("customConfirmModal");
    modal.style.display = "flex";
    
    const okBtn = document.getElementById("btnConfirmOK");
    const cancelBtn = document.getElementById("btnConfirmCancel");
    
    okBtn.onclick = () => {
        modal.style.display = "none";
        if (onConfirm) onConfirm();
    };
    cancelBtn.onclick = () => {
        modal.style.display = "none";
    };
}

function bindModalOverlayEvents() {
    const modals = document.querySelectorAll(".admin-modal");
    modals.forEach(modal => {
        let isMouseDownOnModalContent = false;
        const content = modal.querySelector(".modal-content");
        if (content) {
            content.addEventListener("mousedown", () => {
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
                if (modal.id === "seriesModal") closeSeriesModal();
                else if (modal.id === "folderDetailModal") closeFolderDetailModal();
                else if (modal.id === "setModal") closeSetModal();
                else if (modal.id === "uploadModal") closeUploadModal();
                else if (modal.id === "customConfirmModal") { modal.style.display = 'none'; }
            }
            isMouseDownOnModalContent = false;
        });
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            const lightbox = document.getElementById("lightboxOverlay");
            if (lightbox && lightbox.style.display === "flex") {
                closeLightbox();
                e.stopPropagation();
                return;
            }
            const visibleModals = [...document.querySelectorAll(".admin-modal")].filter(m => m.style.display === "flex" || m.style.display === "block");
            if (visibleModals.length > 0) {
                const modal = visibleModals[visibleModals.length - 1];
                if (modal.id === "seriesModal") closeSeriesModal();
                else if (modal.id === "folderDetailModal") closeFolderDetailModal();
                else if (modal.id === "setModal") closeSetModal();
                else if (modal.id === "uploadModal") closeUploadModal();
                else if (modal.id === "importPreviewModal") closeImportPreviewModal();
                else if (modal.id === "customConfirmModal") { modal.style.display = 'none'; }
            }
        }
    });
}

// ==================== 导入导出控制器 ====================

let exportModeActive = false;
let exportSelectedIds = new Set();
let importPreviewData = null;

function enterExportMode() {
    exportModeActive = true;
    exportSelectedIds = new Set();
    document.getElementById("normalHeaderBtns").style.display = "none";
    document.getElementById("exportHeaderBtns").style.display = "flex";
    const allChk = document.getElementById("selectAllCanvasCheckbox");
    if (allChk) allChk.checked = false;
    // 重新渲染 folders 以切换至导出模式样式（inline render-time branching，与贴纸管理一致）
    renderFolders(allConfig);
    setDraggableState(false);
    updateExportBtn();
}

function exitExportMode() {
    exportModeActive = false;
    exportSelectedIds = new Set();
    document.getElementById("normalHeaderBtns").style.display = "flex";
    document.getElementById("exportHeaderBtns").style.display = "none";
    const allChk = document.getElementById("selectAllCanvasCheckbox");
    if (allChk) allChk.checked = false;
    // 重新渲染恢复正常模式
    renderFolders(allConfig);
    setDraggableState(true);
}

function toggleSeriesExportSelect(id) {
    if (exportSelectedIds.has(id)) {
        exportSelectedIds.delete(id);
    } else {
        exportSelectedIds.add(id);
    }
    // 同步 DOM：更新对应卡片的 class 和 checkbox，无需整体重渲染
    const card = document.querySelector(`.folder-card[data-id="${id}"]`);
    if (card) {
        card.classList.toggle("export-selected", exportSelectedIds.has(id));
        const chk = card.querySelector(".card-export-checkbox");
        if (chk) chk.checked = exportSelectedIds.has(id);
    }
    updateExportBtn();
    // 同步全选框状态
    const allChk = document.getElementById("selectAllCanvasCheckbox");
    if (allChk) {
        const total = document.querySelectorAll(".folder-card[data-id]").length;
        allChk.checked = exportSelectedIds.size === total && total > 0;
    }
}

function toggleSelectAllCanvas(event) {
    const checked = event.target.checked;
    document.querySelectorAll(".folder-card[data-id]").forEach(card => {
        const id = parseInt(card.getAttribute("data-id"));
        if (checked) {
            exportSelectedIds.add(id);
            card.classList.add("export-selected");
        } else {
            exportSelectedIds.delete(id);
            card.classList.remove("export-selected");
        }
        const chk = card.querySelector(".card-export-checkbox");
        if (chk) chk.checked = checked;
    });
    updateExportBtn();
}

function updateExportBtn() {
    const btn = document.getElementById("confirmExportBtn");
    if (btn) btn.textContent = `🚀 确认导出 (${exportSelectedIds.size})`;
}

async function performExport() {
    if (exportSelectedIds.size === 0) {
        showToast("请先勾选至少一个系列", "error");
        return;
    }
    const btn = document.getElementById("confirmExportBtn");
    btn.disabled = true;
    btn.textContent = "⏳ 正在打包中...";
    try {
        const ids = [...exportSelectedIds];
        const token = localStorage.getItem("token");
        const idsParam = ids.join(",");
        const res = await fetch(`/api/canvases/admin/export?series_ids=${idsParam}`, {
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "导出失败");
        }
        const blob = await res.blob();
        // 优先从 Content-Disposition 读取文件名，否则用时间戳
        let fileName = `dinoroar_canvases_export_${new Date().getTime()}.zip`;
        const contentDisposition = res.headers.get("Content-Disposition");
        if (contentDisposition && contentDisposition.includes("filename=")) {
            fileName = contentDisposition.split("filename=")[1].replace(/"/g, "");
        }
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        showToast("✨ 画布包打包导出成功，已自动下载！", "success");
        exitExportMode();
    } catch (e) {
        showToast(e.message || "导出失败", "error");
        btn.disabled = false;
        updateExportBtn();
    }
}

function triggerImportCanvasPack() {
    document.getElementById("importZipFileInput").value = "";
    document.getElementById("importZipFileInput").click();
}

async function handleImportZipSelected(event) {
    const file = event.target.files[0];
    if (!file) return;
    showToast("正在上传并解析画布包...", "info");
    try {
        const data = await canvasesApi.importPreview(file);
        importPreviewData = data;
        renderImportPreviewModal(data);
    } catch (e) {
        showToast(e.message || "上传解析失败", "error");
    }
}

function renderImportPreviewModal(data) {
    const list = document.getElementById("importSeriesPreviewList");
    list.innerHTML = "";
    data.series_list.forEach((series, idx) => {
        const conflictBadge = series.is_name_conflict
            ? `<span style="background:#f59e0b;color:#000;font-size:0.72rem;padding:2px 7px;border-radius:6px;font-weight:700;margin-left:8px;">⚠️ 同名已存在</span>`
            : "";

        // 取第一个商品套的第一张图作为预览缩略图
        let thumbHtml = "";
        if (series.canvas_sets && series.canvas_sets.length > 0) {
            const firstSet = series.canvas_sets[0];
            if (firstSet.instances && firstSet.instances.length > 0) {
                const inst = firstSet.instances[0];
                if (inst.image_b64) {
                    thumbHtml = `<img src="${inst.image_b64}" style="width:80px;height:52px;object-fit:cover;border-radius:6px;flex-shrink:0;border:1px solid var(--card-border);">`;
                }
            }
        }

        const setsHtml = series.canvas_sets.map(cs => {
            const instBadges = cs.instances.map(inst =>
                `<span style="font-size:0.72rem;padding:1px 6px;border-radius:4px;background:rgba(139,92,246,0.15);color:#a78bfa;">${inst.aspect_ratio}</span>`
            ).join(" ");
            return `<div style="font-size:0.82rem;color:var(--text-muted);display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                <span style="color:var(--text-main);font-weight:600;">${cs.name}</span>
                <span style="color:var(--text-muted);">¥${cs.exchange_price}🥚</span>
                ${instBadges}
            </div>`;
        }).join("");

        const card = document.createElement("div");
        card.style.cssText = "background:rgba(255,255,255,0.02);border:1.5px solid var(--card-border);border-radius:12px;padding:12px 16px;display:flex;align-items:flex-start;gap:14px;cursor:pointer;transition:border-color 0.2s;";
        card.setAttribute("data-series-name", series.series_name);
        card.id = `importSeriesCard-${idx}`;
        card.innerHTML = `
            <input type="checkbox" class="import-series-chk" data-name="${series.series_name}" style="width:18px;height:18px;flex-shrink:0;margin-top:2px;cursor:pointer;" checked onchange="updateImportHint()">
            ${thumbHtml}
            <div style="flex:1;min-width:0;">
                <div style="font-weight:700;font-size:0.92rem;display:flex;align-items:center;flex-wrap:wrap;">
                    ${series.series_name}${conflictBadge}
                    <span style="margin-left:auto;font-size:0.78rem;color:var(--text-muted);">${series.set_count} 个画布套</span>
                </div>
                <div style="display:flex;flex-direction:column;gap:5px;margin-top:8px;">${setsHtml}</div>
            </div>
        `;
        card.addEventListener("click", (e) => {
            if (e.target.tagName !== "INPUT") {
                const chk = card.querySelector(".import-series-chk");
                chk.checked = !chk.checked;
                updateImportHint();
            }
        });
        list.appendChild(card);
    });
    updateImportHint();
    document.getElementById("importPreviewModal").style.display = "flex";
}

function updateImportHint() {
    const checked = document.querySelectorAll(".import-series-chk:checked").length;
    document.getElementById("importSelectHint").textContent = `已选 ${checked} 个系列`;
}

function closeImportPreviewModal() {
    document.getElementById("importPreviewModal").style.display = "none";
    importPreviewData = null;
}

async function handleConfirmImportSubmit() {
    const checkedNames = [...document.querySelectorAll(".import-series-chk:checked")].map(c => c.getAttribute("data-name"));
    if (checkedNames.length === 0) {
        showToast("请至少勾选一个系列进行导入", "error");
        return;
    }
    const conflictRes = document.querySelector("input[name='conflictRes']:checked")?.value || "rename";
    const btn = document.getElementById("confirmImportBtn");
    btn.disabled = true;
    btn.textContent = "导入中...";
    try {
        const res = await canvasesApi.importConfirm(importPreviewData.temp_token, checkedNames, conflictRes);
        closeImportPreviewModal();
        showToast(`✅ 成功导入 ${res.imported_series_count} 个系列！`, "success");
        loadConfig();
    } catch (e) {
        showToast(e.message || "导入失败", "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "✅ 确认导入";
    }
}

