// ==================== 1. 主页分类文件夹（Folders）拖拽 ====================
let draggedFolder = null;

function handleFolderDragStart(e) {
    draggedFolder = this;
    e.dataTransfer.effectAllowed = 'move';
    this.style.opacity = '0.4';
}

function handleFolderDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    return false;
}

function handleFolderDragEnter() {
    this.classList.add('over');
}

function handleFolderDragLeave() {
    this.classList.remove('over');
}

function handleFolderDrop(e) {
    e.stopPropagation();
    if (draggedFolder !== this) {
        const container = document.getElementById('seriesContainer');
        const children = [...container.children];
        const from = children.indexOf(draggedFolder);
        const to = children.indexOf(this);
        if (from < to) {
            container.insertBefore(draggedFolder, this.nextSibling);
        } else {
            container.insertBefore(draggedFolder, this);
        }
        saveNewSeriesOrder();
    }
    return false;
}

function handleFolderDragEnd() {
    this.style.opacity = '1';
    document.querySelectorAll('.folder-card').forEach(f => f.classList.remove('over'));
}

async function saveNewSeriesOrder() {
    const ids = [...document.getElementById('seriesContainer').children]
        .map(c => parseInt(c.getAttribute('data-id')))
        .filter(id => !isNaN(id));

    try {
        await stickersApi.sortSeries(ids);
        showToast("分类顺序已成功保存！", "success");
        loadStickerManagementData();
    } catch(err) {
        showToast(err.message, "error");
    }
}

// ==================== 2. 贴纸详情弹窗列表拖拽 ====================
let draggedElement = null;

function handleDragStart(e) {
    draggedElement = this;
    e.dataTransfer.effectAllowed = 'move';
    this.style.opacity = '0.4';
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter() {
    this.classList.add('over');
}

function handleDragLeave() {
    this.classList.remove('over');
}

function handleDrop(e) {
    e.stopPropagation();
    if (draggedElement !== this) {
        const list = document.getElementById('stickerDetailGrid');
        const children = [...list.children];
        const from = children.indexOf(draggedElement);
        const to = children.indexOf(this);
        if (from < to) {
            list.insertBefore(draggedElement, this.nextSibling);
        } else {
            list.insertBefore(draggedElement, this);
        }
        saveNewStickersOrder();
    }
    return false;
}

function handleDragEnd() {
    this.style.opacity = '1';
    document.querySelectorAll('.sticker-item').forEach(i => i.classList.remove('over'));
}

async function saveNewStickersOrder() {
    const ids = [...document.getElementById('stickerDetailGrid').children]
        .map(c => parseInt(c.getAttribute('data-id')))
        .filter(id => !isNaN(id));

    try {
        await stickersApi.sortStickers(ids);
        showToast("顺序已保存！", "success");
        loadStickerManagementData();
    } catch(err) {
        showToast(err.message, "error");
    }
}
