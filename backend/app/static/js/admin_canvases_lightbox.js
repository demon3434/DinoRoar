// ==================== 画布大图 Lightbox 预览逻辑 ====================
let lightboxScale = 1;
let lightboxTranslateX = 0;
let lightboxTranslateY = 0;
let lightboxIsDragging = false;
let lightboxStartX = 0;
let lightboxStartY = 0;

let currentLightboxImages = [];
let currentLightboxIndex = 0;

function openLightbox(imageUrl, title, setId = null, currentRatio = null) {
    const overlay = document.getElementById("lightboxOverlay");
    currentLightboxImages = [];
    
    const ratioOrder = ["16:9", "4:3", "1:1", "2:1"];
    let setName = title ? title.split(" - ")[0] : "画布预览";

    if (typeof allConfig !== "undefined" && setId) {
        let foundSet = null;
        for (const s of allConfig) {
            if (s.sets) {
                const found = s.sets.find(st => st.id === setId);
                if (found) {
                    foundSet = found;
                    setName = found.name;
                    break;
                }
            }
        }
        if (foundSet && foundSet.instances) {
            ratioOrder.forEach(r => {
                const inst = foundSet.instances.find(i => i.aspect_ratio === r && !i.is_deleted && i.image_url);
                if (inst) {
                    currentLightboxImages.push({
                        ratio: r,
                        url: inst.image_url,
                        name: setName
                    });
                }
            });
        }
    }

    // 兜底单图
    if (currentLightboxImages.length === 0 && imageUrl) {
        currentLightboxImages.push({
            ratio: currentRatio || "",
            url: imageUrl,
            name: setName
        });
    }

    // 定位到当前点击的 ratio
    let foundIndex = currentLightboxImages.findIndex(img => (currentRatio && img.ratio === currentRatio) || img.url === imageUrl);
    currentLightboxIndex = foundIndex >= 0 ? foundIndex : 0;

    renderLightboxCurrent();
    overlay.style.display = "flex";
}

function renderLightboxCurrent() {
    if (currentLightboxImages.length === 0) return;
    const current = currentLightboxImages[currentLightboxIndex];
    const img = document.getElementById("lightboxImage");
    const titleEl = document.getElementById("lightboxTitle");
    const prevBtn = document.getElementById("lightboxPrevBtn");
    const nextBtn = document.getElementById("lightboxNextBtn");

    if (img) img.src = current.url;
    if (titleEl) {
        if (currentLightboxImages.length > 1) {
            titleEl.textContent = `${current.name} - ${current.ratio} (${currentLightboxIndex + 1}/${currentLightboxImages.length})`;
        } else if (current.ratio) {
            titleEl.textContent = `${current.name} - ${current.ratio}`;
        } else {
            titleEl.textContent = current.name;
        }
    }

    const showNav = currentLightboxImages.length > 1;
    if (prevBtn) prevBtn.style.display = showNav ? "flex" : "none";
    if (nextBtn) nextBtn.style.display = showNav ? "flex" : "none";

    resetLightboxZoom();
}

function lightboxPrev(e) {
    if (e) e.stopPropagation();
    if (currentLightboxImages.length <= 1) return;
    currentLightboxIndex = (currentLightboxIndex - 1 + currentLightboxImages.length) % currentLightboxImages.length;
    renderLightboxCurrent();
}

function lightboxNext(e) {
    if (e) e.stopPropagation();
    if (currentLightboxImages.length <= 1) return;
    currentLightboxIndex = (currentLightboxIndex + 1) % currentLightboxImages.length;
    renderLightboxCurrent();
}

function closeLightbox() {
    const overlay = document.getElementById("lightboxOverlay");
    if (overlay) overlay.style.display = "none";
    currentLightboxImages = [];
    currentLightboxIndex = 0;
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
    
    const closeBtn = document.getElementById("lightboxCloseBtn");
    if (closeBtn) closeBtn.onclick = closeLightbox;
    
    const prevBtn = document.getElementById("lightboxPrevBtn");
    if (prevBtn) prevBtn.onclick = lightboxPrev;
    
    const nextBtn = document.getElementById("lightboxNextBtn");
    if (nextBtn) nextBtn.onclick = lightboxNext;
    
    overlay.onclick = (e) => {
        if (e.target === overlay || e.target === content) {
            closeLightbox();
        }
    };
    
    const zoomInBtn = document.getElementById("lightboxZoomIn");
    const zoomOutBtn = document.getElementById("lightboxZoomOut");
    const resetBtn = document.getElementById("lightboxResetZoom");
    
    if (zoomInBtn) zoomInBtn.onclick = zoomIn;
    if (zoomOutBtn) zoomOutBtn.onclick = zoomOut;
    if (resetBtn) resetBtn.onclick = resetLightboxZoom;
    
    content.addEventListener("wheel", (e) => {
        e.preventDefault();
        if (e.deltaY < 0) {
            zoomIn();
        } else {
            zoomOut();
        }
    }, { passive: false });
    
    content.addEventListener("mousedown", (e) => {
        if (e.target.closest(".lightbox-nav-btn") || e.target.closest(".lightbox-toolbar")) return;
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

    document.addEventListener("keydown", (e) => {
        if (overlay && overlay.style.display === "flex") {
            if (e.key === "ArrowLeft") {
                lightboxPrev();
                e.stopPropagation();
            } else if (e.key === "ArrowRight") {
                lightboxNext();
                e.stopPropagation();
            }
        }
    });
}
