// ==================== 1. 主页分类文件夹（Folders）拖拽 ====================
let draggedFolder = null;

function handleFolderDragStart(e) {
    draggedFolder = this;
    e.dataTransfer.effectAllowed = "move";
    this.style.opacity = "0.4";
}

function handleFolderDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    return false;
}

function handleFolderDragEnter() {
    this.classList.add("over");
}

function handleFolderDragLeave() {
    this.classList.remove("over");
}

function handleFolderDrop(e) {
    e.stopPropagation();
    if (draggedFolder !== this) {
        const container = document.getElementById("seriesContainer");
        const children = [...container.children];
        const from = children.indexOf(draggedFolder);
        const to = children.indexOf(this);
        if (from < to) {
            container.insertBefore(draggedFolder, this.nextSibling);
        } else {
            container.insertBefore(draggedFolder, this);
        }
        saveNewFolderOrder();
    }
    return false;
}

function handleFolderDragEnd() {
    this.style.opacity = "1";
    document.querySelectorAll(".folder-card").forEach(f => f.classList.remove("over"));
}

async function saveNewFolderOrder() {
    const ids = [...document.getElementById("seriesContainer").children]
        .map(c => parseInt(c.getAttribute("data-id")))
        .filter(id => !isNaN(id));

    try {
        await canvasesApi.sortSeries(ids);
        showToast("分类排序保存成功！", "success");
        loadConfig();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// ==================== 2. 画布详情弹窗套件（Sets）拖拽 ====================
let draggedSet = null;

function handleSetDragStart(e) {
    draggedSet = this;
    e.dataTransfer.effectAllowed = "move";
    this.style.opacity = "0.4";
}

// Disable dragging when interacting with renamed inputs or sliders
function setDraggableState(draggable) {
    document.querySelectorAll(".folder-card").forEach(f => f.setAttribute("draggable", draggable ? "true" : "false"));
}

function handleSetDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    return false;
}

function handleSetDragEnter() {
    this.classList.add("over");
}

function handleSetDragLeave() {
    this.classList.remove("over");
}

function handleSetDrop(e) {
    e.stopPropagation();
    if (draggedSet !== this) {
        const container = document.getElementById("setsDetailGrid");
        const children = [...container.children];
        const from = children.indexOf(draggedSet);
        const to = children.indexOf(this);
        if (from < to) {
            container.insertBefore(draggedSet, this.nextSibling);
        } else {
            container.insertBefore(draggedSet, this);
        }
        saveNewSetsOrder();
    }
    return false;
}

function handleSetDragEnd() {
    this.style.opacity = "1";
    document.querySelectorAll(".set-detail-card").forEach(c => c.classList.remove("over"));
}

async function saveNewSetsOrder() {
    const ids = [...document.getElementById("setsDetailGrid").children]
        .map(c => parseInt(c.getAttribute("data-id")))
        .filter(id => !isNaN(id));

    try {
        await canvasesApi.sortSets(ids);
        showToast("画布排序保存成功！", "success");
        loadConfig();
    } catch (err) {
        showToast(err.message, "error");
    }
}
