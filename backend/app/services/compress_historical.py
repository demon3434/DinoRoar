import os
import threading
import logging
import time
from pathlib import Path
from PIL import Image
from app.config import settings

logger = logging.getLogger("DinoRoar.compress_historical")

def _compress_uploads_worker():
    upload_dir = Path(settings.upload_dir)
    lock_file = upload_dir / ".historical_pngs_optimized"
    
    # 建立局部数据库会话，用于执行贴纸及画布的废弃孤立文件清洗
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        logger.info("Starting historical data cleansing process...")
        
        # 1. 清空无用的临时导入解压缓存目录 temp_import
        temp_import_dir = upload_dir / "temp_import"
        if temp_import_dir.exists():
            import shutil
            try:
                shutil.rmtree(temp_import_dir, ignore_errors=True)
                logger.info("Cleansing: Cleared temporary import cache directory.")
            except Exception as e:
                logger.error(f"Cleansing: Failed to clear temp_import directory: {e}")
        # 1b. 清理过期的临时缓存子目录（TTL=1h）
        if temp_import_dir.exists():
            now_ts = time.time()
            for child in temp_import_dir.iterdir():
                if child.is_dir():
                    mtime = child.stat().st_mtime
                    if now_ts - mtime > 3600:  # 超过 1 小时
                        try:
                            import shutil
                            shutil.rmtree(child, ignore_errors=True)
                            logger.info(f"Cleansing: Removed expired temp_import subdir {child.name}")
                        except Exception as e2:
                            logger.error(f"Cleansing: Failed to remove expired temp_import subdir {child.name}: {e2}")
                
        # 2. 执行贴纸孤立废弃图片清理 (在数据库中无记录的文件)
        try:
            from app.services.stickers import cleanup_sticker_orphans
            st_clean = cleanup_sticker_orphans(db)
            logger.info(f"Cleansing: Cleaned orphan stickers: {st_clean.get('cleaned_files_count', 0)} files, {st_clean.get('cleaned_dirs_count', 0)} dirs deleted.")
        except Exception as e:
            logger.error(f"Cleansing: Failed to cleanup sticker orphans: {e}")
            
        # 3. 执行画布孤立废弃图片清理 (在数据库中没有对应 CanvasInstance 记录或已软删除的文件)
        try:
            from app.models import CanvasInstance
            valid_instances = db.query(CanvasInstance.image_url).filter(CanvasInstance.is_deleted == False).all()
            valid_paths = set()
            for (url,) in valid_instances:
                if url and url.startswith("/static/uploads/"):
                    rel = url.replace("/static/uploads/", "", 1)
                    valid_paths.add(os.path.realpath(upload_dir / rel))
            
            canvases_upload_dir = upload_dir / "canvases"
            cleaned_canvases_count = 0
            cleaned_canvases_dirs = 0
            if canvases_upload_dir.exists():
                for root, dirs, files in os.walk(canvases_upload_dir, topdown=False):
                    for f in files:
                        full_p = Path(root) / f
                        real_p = os.path.realpath(full_p)
                        if real_p not in valid_paths:
                            try:
                                os.remove(full_p)
                                cleaned_canvases_count += 1
                            except Exception:
                                pass
                    # 清理空子文件夹
                    if root != str(canvases_upload_dir):
                        if not os.listdir(root):
                            try:
                                os.rmdir(root)
                                cleaned_canvases_dirs += 1
                            except Exception:
                                pass
            logger.info(f"Cleansing: Cleaned orphan canvases: {cleaned_canvases_count} files, {cleaned_canvases_dirs} dirs deleted.")
        except Exception as e:
            logger.error(f"Cleansing: Failed to cleanup canvas orphans: {e}")
            
    except Exception as cleanse_err:
        logger.error(f"Cleansing: Unexpected error during directory cleansing: {cleanse_err}")
    finally:
        db.close()
        
    # 4. 无损压缩优化阶段 (锁保护：如果已完成无损重编码优化，直接跳过此耗时阶段)
    if lock_file.exists():
        logger.info("Historical image compression: Lock file exists. Skipping image compression phase.")
        return
        
    logger.info("Historical image compression: Starting background optimization scan...")
    
    try:
        # 支持 canvases 和 stickers 下的所有有效 PNG 文件
        png_files = []
        for root, dirs, files in os.walk(upload_dir):
            # 避开临时目录防止扫描到正在导入的文件
            if "temp_import" in root:
                continue
            for file in files:
                if file.lower().endswith(".png"):
                    png_files.append(Path(root) / file)
                    
        total_count = len(png_files)
        logger.info(f"Historical image compression: Found {total_count} PNG files to compress in {upload_dir}")
        
        compressed_count = 0
        failed_count = 0
        
        for index, file_path in enumerate(png_files):
            try:
                orig_size = file_path.stat().st_size
                with Image.open(file_path) as img:
                    img.save(file_path, format=img.format, optimize=True)
                new_size = file_path.stat().st_size
                if new_size < orig_size:
                    compressed_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to compress historical file {file_path}: {e}")
                
        # 写入锁文件，表示已全部处理完毕
        with open(lock_file, "w", encoding="utf-8") as lf:
            lf.write("done")
            
        logger.info(f"Historical image compression complete. Scanned: {total_count}, Compressed: {compressed_count}, Failed: {failed_count}.")
        
    except Exception as scan_err:
        logger.error(f"Error during historical image scan: {scan_err}")

def start_historical_compression():
    """
    非阻塞式启动后台工作线程来优化存量图片
    """
    thread = threading.Thread(target=_compress_uploads_worker, name="DinoRoar-HistoricalCompressor", daemon=True)
    thread.start()
