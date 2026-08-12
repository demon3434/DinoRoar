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
    if (overlay) overlay.style.display = "none";
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
