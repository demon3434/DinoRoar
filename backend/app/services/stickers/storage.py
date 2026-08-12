"""
Hierarchical directory management, legacy flat file migration,
and recursive orphan cleanup for sticker assets.
"""

import os
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from ...models import StickerConfig

import os
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from ...models import StickerConfig
from ...config import settings

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
UPLOAD_ROOT_DIR = Path(settings.upload_dir)
STICKERS_UPLOAD_DIR = UPLOAD_ROOT_DIR / "stickers"
TEMP_IMPORT_DIR = UPLOAD_ROOT_DIR / "temp_import"
LEGACY_STATIC_STICKERS_DIR = STATIC_DIR / "uploads" / "stickers"


def get_series_upload_dir(series_id: int) -> Path:
    """
    获取或创建特定贴纸系列的物理存储子目录 UPLOAD_ROOT_DIR/stickers/series_{series_id}/
    """
    series_dir = STICKERS_UPLOAD_DIR / f"series_{series_id}"
    series_dir.mkdir(parents=True, exist_ok=True)
    return series_dir


def save_sticker_image_file(series_id: int, filename: str, content_bytes: bytes, remove_background: bool = False) -> str:
    """
    保存贴纸图片到特定系列子目录，若 remove_background=True，则自动调用去背景扣图算法处理。
    返回带子路径的相对 URL。
    """
    series_dir = get_series_upload_dir(series_id)
    file_path = series_dir / filename
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    if remove_background:
        from .image_processor import remove_background_and_shadow
        remove_background_and_shadow(file_path, file_path)
    else:
        # 如果不去除背景，也直接对其进行 PIL 优化保存以缩减体积
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                img.save(file_path, format=img.format, optimize=True)
        except Exception:
            pass

    return f"/static/uploads/stickers/series_{series_id}/{filename}"


def migrate_legacy_sticker_files(db: Session) -> dict:
    """
    平滑迁移脚本：将 uploads/stickers/ 或旧 static/uploads/stickers/ 根目录下的存量平铺图片归类移入对应的 series_{series_id}/ 子目录，
    并同步更新数据库中的 image_url 相对路径。
    """
    STICKERS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    migrated_count = 0
    errors = []

    stickers = db.query(StickerConfig).filter(StickerConfig.is_deleted == False).all()
    for st in stickers:
        if not st.image_url:
            continue

        filename = os.path.basename(st.image_url)
        target_dir = get_series_upload_dir(st.series_id)
        target_path = target_dir / filename

        # 检查是否位于新存储根目录下的根平铺文件
        flat_file_path = STICKERS_UPLOAD_DIR / filename
        # 检查是否位于旧静态源码目录中的文件
        legacy_file_path = LEGACY_STATIC_STICKERS_DIR / filename
        legacy_series_path = LEGACY_STATIC_STICKERS_DIR / f"series_{st.series_id}" / filename

        source_path = None
        if flat_file_path.is_file():
            source_path = flat_file_path
        elif legacy_file_path.is_file():
            source_path = legacy_file_path
        elif legacy_series_path.is_file():
            source_path = legacy_series_path

        if source_path and source_path.is_file() and source_path.resolve() != target_path.resolve():
            try:
                shutil.move(str(source_path), str(target_path))
                new_image_url = f"/static/uploads/stickers/series_{st.series_id}/{filename}"
                st.image_url = new_image_url
                migrated_count += 1
            except Exception as e:
                errors.append(f"迁移贴纸 ID {st.id} ({filename}) 失败: {str(e)}")
        elif "/series_" not in st.image_url:
            st.image_url = f"/static/uploads/stickers/series_{st.series_id}/{filename}"
            migrated_count += 1

    if migrated_count > 0:
        db.commit()

    return {"migrated_count": migrated_count, "errors": errors}


def cleanup_sticker_orphans(db: Session) -> dict:
    """
    递归清理服务：递归扫描 uploads/stickers/ 目录下的所有文件与子目录，
    清理在数据库中没有对应引用记录的孤立图片，并清理空目录。
    """
    if not STICKERS_UPLOAD_DIR.exists():
        return {"cleaned_files_count": 0, "cleaned_dirs_count": 0}

    stickers = db.query(StickerConfig.image_url).all()
    valid_paths = set()
    for (url,) in stickers:
        if url:
            if url.startswith("/static/uploads/"):
                rel_path = url.replace("/static/uploads/", "", 1)
                valid_paths.add(os.path.realpath(UPLOAD_ROOT_DIR / rel_path))
            elif url.startswith("/static/"):
                rel_path = url.replace("/static/", "", 1)
                valid_paths.add(os.path.realpath(STATIC_DIR / rel_path))

    deleted_files = []
    freed_bytes = 0

    for root, dirs, files in os.walk(STICKERS_UPLOAD_DIR, topdown=False):
        for f in files:
            full_p = Path(root) / f
            real_p = os.path.realpath(full_p)
            if real_p not in valid_paths:
                try:
                    file_size = os.path.getsize(full_p)
                    os.remove(full_p)
                    deleted_files.append(os.path.relpath(full_p, STICKERS_UPLOAD_DIR))
                    freed_bytes += file_size
                except Exception:
                    pass

        if root != str(STICKERS_UPLOAD_DIR):
            try:
                if not os.listdir(root):
                    os.rmdir(root)
                    # Directory removal does not affect freed_bytes
            except Exception:
                pass

    return {
        "deleted_files": deleted_files,
        "freed_bytes": freed_bytes
    }

