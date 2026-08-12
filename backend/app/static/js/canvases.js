let allConfig = [];
let userInventory = { canvas_inventory: "", egg_energy: 0 };
let activeSeriesId = null;

document.addEventListener("DOMContentLoaded", () => {
    initPage();
    initLightboxEvents();
});

async function initPage() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
        // 1. 并发获取基础配置和用户资产
        const [configRes, inventoryRes] = await Promise.all([
            fetch("/api/canvases/config", {
                headers: { "Authorization": "Bearer " + token }
            }),
            fetch("/api/canvases/inventory", {
                headers: { "Authorization": "Bearer " + token }
            })
        ]);

        if (configRes.ok) allConfig = await configRes.json();
        if (inventoryRes.ok) userInventory = await inventoryRes.json();

        // 更新全局蛋能量显示
        updateEggEnergyDisplay(userInventory.egg_energy);

        // 2. 渲染左侧系列导航栏
        renderSeriesSidebar();

        // 3. 默认选中第一个系列
        if (allConfig.length > 0) {
            selectSeries(allConfig[0].id);
        } else {
            renderEmptyState();
        }

    } catch (e) {
        console.error("初始化商城数据失败", e);
    }
}

function updateEggEnergyDisplay(energy) {
    const navEnergyEl = document.getElementById("navEggEnergy");
    if (navEnergyEl) navEnergyEl.textContent = energy;
}

function renderSeriesSidebar() {
    const sidebarList = document.getElementById("seriesNavList");
    if (!sidebarList) return;

    sidebarList.innerHTML = "";
    allConfig.forEach(series => {
        const item = document.createElement("div");
        item.className = "series-nav-item";
        item.id = `series-nav-${series.id}`;
        item.onclick = () => selectSeries(series.id);

        const nameSpan = document.createElement("span");
        nameSpan.textContent = `🦕 ${series.name}`;

        const badge = document.createElement("span");
        badge.className = "series-badge";
        badge.textContent = series.sets.length;

        item.appendChild(nameSpan);
        item.appendChild(badge);
        sidebarList.appendChild(item);
    });
}

function selectSeries(seriesId) {
    activeSeriesId = seriesId;

    // 清空并重新高亮左侧页签
    const allItems = document.querySelectorAll(".series-nav-item");
    allItems.forEach(item => item.classList.remove("active"));
    const activeItem = document.getElementById(`series-nav-${seriesId}`);
    if (activeItem) activeItem.classList.add("active");

    // 渲染右侧面板
    renderCanvasesGrid();
}

function renderCanvasesGrid() {
    const grid = document.getElementById("canvasesGrid");
    if (!grid) return;

    grid.innerHTML = "";
    const activeSeries = allConfig.find(s => s.id === activeSeriesId);
    if (!activeSeries || activeSeries.sets.length === 0) {
        renderEmptyState();
        return;
    }

    const ownedSetIds = userInventory.canvas_inventory
        .split(",")
        .map(id => id.trim())
        .filter(id => id.length > 0);

    activeSeries.sets.forEach(cset => {
        const card = document.createElement("div");
        card.className = "canvas-card";

        // 取出该套画布下的所有图片实例，默认第一张为首图
        const instances = cset.instances || [];
        const isOwned = ownedSetIds.includes(String(cset.id));
        const defaultInstance = instances.find(inst => inst.aspect_ratio === "16:9") || instances[0];
        const CACHE_VERSION = "202608111051";
        const defaultImgUrl = defaultInstance ? `${defaultInstance.image_url}?v=${CACHE_VERSION}` : "/static/images/default_canvases/default_canvas_16_9.png";

        // 1. 预览盒
        const previewBox = document.createElement("div");
        previewBox.className = "canvas-preview-box";

        const img = document.createElement("img");
        img.className = "canvas-preview-img";
        img.src = defaultImgUrl;
        img.alt = cset.name;
        img.id = `canvas-img-${cset.id}`;
        img.style.cursor = "zoom-in";
        img.onclick = () => {
            let activeRatio = "16:9";
            if (instances.length > 0) {
                const activeTab = switcher.querySelector(".ratio-btn.active");
                if (activeTab) {
                    activeRatio = activeTab.textContent;
                } else if (defaultInstance) {
                    activeRatio = defaultInstance.aspect_ratio;
                }
            }
            openLightbox(img.src, `${cset.name} - ${activeRatio}`);
        };
        previewBox.appendChild(img);
        card.appendChild(previewBox);

        // 2. 比例切换器 (放置在图片之下，大字体更易点)
        const switcher = document.createElement("div");
        switcher.className = "ratio-switcher";

        if (instances.length > 0) {
            instances.forEach((inst, index) => {
                const tab = document.createElement("span");
                tab.className = `ratio-btn ${inst.aspect_ratio === "16:9" || (index === 0 && !instances.some(i => i.aspect_ratio === "16:9")) ? "active" : ""}`;
                tab.textContent = inst.aspect_ratio;
                tab.onclick = () => {
                    // 清空同辈的高亮
                    switcher.querySelectorAll(".ratio-btn").forEach(t => t.classList.remove("active"));
                    tab.classList.add("active");
                    // 切换图片预览并加上版本缓存失效标识
                    img.src = `${inst.image_url}?v=${CACHE_VERSION}`;
                };
                switcher.appendChild(tab);
            });
        } else {
            const tab = document.createElement("span");
            tab.className = "ratio-btn active";
            tab.textContent = "16:9";
            switcher.appendChild(tab);
        }
        card.appendChild(switcher);

        // 3. 画布详情
        const infoDiv = document.createElement("div");
        infoDiv.className = "canvas-info";

        const name = document.createElement("h4");
        name.className = "canvas-name";
        name.textContent = cset.name;
        infoDiv.appendChild(name);

        const descText = cset.description || "极其精美的手账背景，给日记排版增添童趣。";
        const desc = document.createElement("p");
        desc.className = "canvas-desc";
        desc.textContent = descText;
        desc.title = descText; // 气泡悬浮提示全部文字
        infoDiv.appendChild(desc);

        // 4. 动作操作区
        const actionArea = document.createElement("div");
        actionArea.className = "canvas-action-area";

        const priceSpan = document.createElement("span");
        priceSpan.className = "canvas-price";
        priceSpan.innerHTML = `🥚 ${cset.exchange_price} 能量`;
        actionArea.appendChild(priceSpan);

        const btn = document.createElement("button");
        if (isOwned) {
            btn.className = "canvas-btn owned";
            btn.textContent = "已拥有";
            btn.disabled = true;
        } else {
            const hasEnoughEnergy = userInventory.egg_energy >= cset.exchange_price;
            if (hasEnoughEnergy) {
                btn.className = "canvas-btn exchange";
                btn.textContent = "兑换";
                btn.onclick = () => performExchange(cset.id, cset.name, cset.exchange_price);
            } else {
                btn.className = "canvas-btn locked";
                btn.textContent = "能量不足";
                btn.disabled = true;
            }
        }
        actionArea.appendChild(btn);
        infoDiv.appendChild(actionArea);

        card.appendChild(infoDiv);
        grid.appendChild(card);
    });
}

function renderEmptyState() {
    const grid = document.getElementById("canvasesGrid");
    if (grid) {
        grid.innerHTML = `<div style="grid-column: 1/-1; padding: 50px; text-align: center; color: var(--text-muted); font-size: 0.9rem; font-weight: 700;">
            🍃 该系列暂无背景画布上架，敬请期待！
        </div>`;
    }
}

async function performExchange(setId, setName, price) {
    // 弹窗确认
    const confirmed = await showConfirm(`确认使用 🥚${price} 蛋能量兑换解锁画布套《${setName}》吗？\n解锁后双端将即刻生效！`);
    if (!confirmed) return;

    const token = localStorage.getItem("token");
    if (!token) return;

    try {
        const response = await fetch("/api/canvases/exchange", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({ canvas_set_id: setId })
        });

        if (response.ok) {
            userInventory = await response.json();
            updateEggEnergyDisplay(userInventory.egg_energy);
            // 重新刷新网格
            renderCanvasesGrid();
            showCustomAlert(`🎉 恭喜！兑换画布《${setName}》成功！`);
        } else {
            const errData = await response.json();
            showCustomAlert(`❌ 兑换失败: ${errData.detail || "服务器错误"}`);
        }
    } catch (e) {
        console.error("兑换画布请求失败", e);
        showCustomAlert("❌ 兑换请求发送失败，请检查网络！");
    }
}

// 辅助弹出式提示与确认对话框（对齐 DinoRoar 原有的 Confirm/Alert）
function showConfirm(message) {
    return new Promise(resolve => {
        const modal = document.getElementById("confirmModal");
        if (!modal) {
            resolve(confirm(message));
            return;
        }

        document.getElementById("confirmModalMessage").textContent = message;
        document.getElementById("confirmModalTitle").textContent = "确认兑换";
        
        modal.style.display = "flex";

        const handleOk = () => {
            modal.style.display = "none";
            cleanup();
            resolve(true);
        };
        const handleCancel = () => {
            modal.style.display = "none";
            cleanup();
            resolve(false);
        };

        const okBtn = document.getElementById("confirmModalConfirmBtn");
        const cancelBtn = document.getElementById("confirmModalCancelBtn");

        okBtn.addEventListener("click", handleOk);
        cancelBtn.addEventListener("click", handleCancel);

        function cleanup() {
            okBtn.removeEventListener("click", handleOk);
            cancelBtn.removeEventListener("click", handleCancel);
        }
    });
}

function showCustomAlert(message) {
    alert(message);
}

// ==================== 画布大图 Lightbox 预览逻辑 ====================
let lightboxScale = 1;
let lightboxTranslateX = 0;
let lightboxTranslateY = 0;
let lightboxIsDragging = false;
let lightboxStartX = 0;
let lightboxStartY = 0;

function openLightbox(imageUrl, title) {
    const overlay = document.getElementById("lightboxOverlay");
    const img = document.getElementById("lightboxImage");
    const titleEl = document.getElementById("lightboxTitle");
    
    img.src = imageUrl;
    titleEl.textContent = title || "画布预览";
    
    resetLightboxZoom();
    overlay.style.display = "flex";
}

function closeLightbox() {
    const overlay = document.getElementById("lightboxOverlay");
    overlay.style.display = "none";
}

function zoomIn() {
    lightboxScale = Math.min(lightboxScale + 0.25, 4.0);
    updateLightboxTransform();
}

function zoomOut() {
    lightboxScale = Math.max(lightboxScale - 0.25, 0.5);
    updateLightboxTransform();
}

function resetLightboxZoom() {
    lightboxScale = 1;
    lightboxTranslateX = 0;
    lightboxTranslateY = 0;
    updateLightboxTransform();
}

function updateLightboxTransform() {
    const img = document.getElementById("lightboxImage");
    const zoomLevelEl = document.getElementById("lightboxZoomLevel");
    if (!img) return;
    
    img.style.transform = `translate(${lightboxTranslateX}px, ${lightboxTranslateY}px) scale(${lightboxScale})`;
    img.style.cursor = lightboxIsDragging ? "grabbing" : "grab";
    if (zoomLevelEl) {
        zoomLevelEl.textContent = `${Math.round(lightboxScale * 100)}%`;
    }
}

function initLightboxEvents() {
    const overlay = document.getElementById("lightboxOverlay");
    const content = document.getElementById("lightboxContent");
    const img = document.getElementById("lightboxImage");
    if (!overlay || !content || !img) return;
    
    // 关闭按钮
    const closeBtn = document.getElementById("lightboxCloseBtn");
    if (closeBtn) closeBtn.onclick = closeLightbox;
    
    // 点击背景关闭
    overlay.onclick = (e) => {
        if (e.target === overlay || e.target === content) {
            closeLightbox();
        }
    };
    
    // ESC 键关闭
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && overlay.style.display === "flex") {
            closeLightbox();
        }
    });
    
    // 缩放控制按钮
    const zoomInBtn = document.getElementById("lightboxZoomIn");
    const zoomOutBtn = document.getElementById("lightboxZoomOut");
    const resetBtn = document.getElementById("lightboxResetZoom");
    
    if (zoomInBtn) zoomInBtn.onclick = zoomIn;
    if (zoomOutBtn) zoomOutBtn.onclick = zoomOut;
    if (resetBtn) resetBtn.onclick = resetLightboxZoom;
    
    // 滚轮缩放
    content.addEventListener("wheel", (e) => {
        e.preventDefault();
        if (e.deltaY < 0) {
            zoomIn();
        } else {
            zoomOut();
        }
    }, { passive: false });
    
    // 拖拽平移
    content.addEventListener("mousedown", (e) => {
        e.preventDefault();
        lightboxIsDragging = true;
        lightboxStartX = e.clientX - lightboxTranslateX;
        lightboxStartY = e.clientY - lightboxTranslateY;
        updateLightboxTransform();
    });
    
    document.addEventListener("mousemove", (e) => {
        if (!lightboxIsDragging) return;
        lightboxTranslateX = e.clientX - lightboxStartX;
        lightboxTranslateY = e.clientY - lightboxStartY;
        updateLightboxTransform();
    });
    
    document.addEventListener("mouseup", () => {
        if (lightboxIsDragging) {
            lightboxIsDragging = false;
            updateLightboxTransform();
        }
    });
}
