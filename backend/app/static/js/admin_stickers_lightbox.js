// ==================== 贴纸原图 Lightbox 预览逻辑 ====================
function openStickerImagePreview(imgSrc, name) {
    document.getElementById('lightboxStickerTitle').textContent = `🔍 ${name || '贴纸原图'}`;
    document.getElementById('lightboxStickerImage').src = imgSrc;
    document.getElementById('imageLightboxModal').style.display = 'flex';
}

function closeImageLightboxModal() {
    document.getElementById('imageLightboxModal').style.display = 'none';
}
