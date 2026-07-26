"""
Zip export and import services for sticker series packs.
"""

import io
import json
import os
import zipfile
import uuid
import shutil
import re
import datetime
import base64
from pathlib import Path
from sqlalchemy.orm import Session
from ...models import StickerSeries, StickerConfig
from .storage import STATIC_DIR, STICKERS_UPLOAD_DIR, TEMP_IMPORT_DIR, get_series_upload_dir


def export_sticker_series_zip(db: Session, series_ids: list) -> io.BytesIO:
    """
    打包导出指定的贴纸系列为符合统一规范标准的 Zip 内存文件流
    """
    series_list = db.query(StickerSeries).filter(
        StickerSeries.id.in_(series_ids),
        StickerSeries.is_deleted == False
    ).order_by(StickerSeries.sort_order.asc(), StickerSeries.id.asc()).all()

    if not series_list:
        raise ValueError("未查找到指定的贴纸系列")

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        series_info_list = []
        for s in series_list:
            safe_name = re.sub(r'[^\w\u4e00-\u9fa5]', '_', s.name)
            dir_name = f"series_{s.id}_{safe_name}"
            series_info_list.append({
                "series_name": s.name,
                "dir_name": dir_name,
                "sort_order": s.sort_order
            })

            stickers = db.query(StickerConfig).filter(
                StickerConfig.series_id == s.id,
                StickerConfig.is_deleted == False
            ).order_by(StickerConfig.sort_order.asc(), StickerConfig.id.asc()).all()

            stickers_data = []
            for st in stickers:
                img_name = os.path.basename(st.image_url) if st.image_url else ""
                real_img_path = None

                if st.image_url and st.image_url.startswith("/static/"):
                    rel_path = st.image_url.replace("/static/", "", 1)
                    target_p = STATIC_DIR / rel_path
                    if target_p.exists():
                        real_img_path = target_p

                if not real_img_path or not real_img_path.exists():
                    p1 = STICKERS_UPLOAD_DIR / f"series_{s.id}" / img_name
                    p2 = STICKERS_UPLOAD_DIR / img_name
                    if p1.exists():
                        real_img_path = p1
                    elif p2.exists():
                        real_img_path = p2

                if img_name and real_img_path and real_img_path.exists():
                    zf.write(real_img_path, f"{dir_name}/{img_name}")

                stickers_data.append({
                    "name": st.name,
                    "image_file": img_name,
                    "sort_order": st.sort_order,
                    "exchange_price": st.exchange_price,
                    "description": st.description
                })

            series_json_data = {
                "series_name": s.name,
                "sort_order": s.sort_order,
                "description": "",
                "stickers": stickers_data
            }
            zf.writestr(f"{dir_name}/series.json", json.dumps(series_json_data, ensure_ascii=False, indent=2))

        pack_info = {
            "spec_version": "1.0",
            "app": "DinoRoar",
            "exported_at": datetime.datetime.utcnow().isoformat() + "Z",
            "series_count": len(series_info_list),
            "series_list": series_info_list
        }
        zf.writestr("pack_info.json", json.dumps(pack_info, ensure_ascii=False, indent=2))

    memory_file.seek(0)
    return memory_file


def preview_import_zip(zip_bytes: bytes, db: Session) -> dict:
    """
    解压并安全校验上传的贴纸包，解析元数据并准备前端预览数据
    """
    if len(zip_bytes) > 50 * 1024 * 1024:
        raise ValueError("上传的贴纸包不能超过 50MB")

    temp_token = uuid.uuid4().hex
    target_dir = TEMP_IMPORT_DIR / temp_token
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            target_dir_canonical = os.path.realpath(target_dir)
            for member in zf.infolist():
                extracted_path = os.path.realpath(target_dir / member.filename)
                if not extracted_path.startswith(target_dir_canonical):
                    raise ValueError("极高风险：检测到贴纸包中包含路径穿越越权文件")
            zf.extractall(target_dir)
    except Exception as e:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ValueError(f"贴纸包格式非法或解析解压失败: {str(e)}")

    pack_info_path = target_dir / "pack_info.json"
    if not pack_info_path.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ValueError("解压失败：缺失标准 pack_info.json 规范描述文件")

    try:
        with open(pack_info_path, "r", encoding="utf-8") as f:
            pack_info = json.load(f)
    except Exception as e:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ValueError(f"pack_info.json 解析失败: {str(e)}")

    existing_series_names = {
        s.name for s in db.query(StickerSeries).filter(StickerSeries.is_deleted == False).all()
    }

    raw_series_map = {}
    for root, dirs, files in os.walk(target_dir):
        if "series.json" in files:
            series_json_file = Path(root) / "series.json"
            try:
                with open(series_json_file, "r", encoding="utf-8") as sf:
                    s_data = json.load(sf)
            except Exception:
                continue

            s_name = s_data.get("series_name", "未命名系列")
            stickers_raw = s_data.get("stickers", [])
            stickers_preview = []

            for st in stickers_raw:
                img_file = st.get("image_file", "")
                img_path = Path(root) / img_file
                img_b64 = ""
                if img_file and img_path.exists():
                    try:
                        with open(img_path, "rb") as imf:
                            ext = img_path.suffix.lstrip(".").lower() or "png"
                            img_b64 = f"data:image/{ext};base64," + base64.b64encode(imf.read()).decode("utf-8")
                    except Exception:
                        pass

                stickers_preview.append({
                    "name": st.get("name", ""),
                    "image_b64": img_b64,
                    "exchange_price": st.get("exchange_price", 20),
                    "sort_order": st.get("sort_order", 0)
                })

            dir_basename = os.path.basename(root)
            raw_series_map[dir_basename] = {
                "series_name": s_name,
                "dir_name": dir_basename,
                "sort_order": s_data.get("sort_order", 0),
                "is_name_conflict": s_name in existing_series_names,
                "sticker_count": len(stickers_preview),
                "stickers": stickers_preview
            }

    parsed_series_list = []
    pack_series_info = pack_info.get("series_list", [])
    if pack_series_info and isinstance(pack_series_info, list):
        for s_info in pack_series_info:
            d_name = s_info.get("dir_name") if isinstance(s_info, dict) else s_info
            if d_name in raw_series_map:
                parsed_series_list.append(raw_series_map.pop(d_name))

    remaining = list(raw_series_map.values())
    remaining.sort(key=lambda x: x.get("sort_order", 0))
    parsed_series_list.extend(remaining)

    if not parsed_series_list:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ValueError("解压贴纸包未识别到任何有效的 series.json 系列描述文件")

    return {
        "temp_token": temp_token,
        "spec_version": pack_info.get("spec_version", "1.0"),
        "series_list": parsed_series_list
    }


def confirm_import_stickers(
    temp_token: str,
    selected_series_names: list,
    conflict_resolution: str,
    db: Session
) -> dict:
    """
    读取解压缓存中的贴纸包，根据管理员的选择以及冲突策略将贴纸系列落库，
    并将贴纸图片落盘写入层级目录 backend/app/static/uploads/stickers/series_{series_id}/
    """
    import logging
    logger = logging.getLogger("DinoRoar")
    logger.info(f"confirm_import_stickers triggered: temp_token={temp_token}, selected_series_names={selected_series_names}, conflict_resolution={conflict_resolution}")

    target_dir = TEMP_IMPORT_DIR / temp_token
    if not target_dir.exists():
        logger.error(f"confirm_import_stickers failed: target_dir={target_dir} not exists")
        raise ValueError("导入缓存已过期或不存在，请重新上传贴纸包")

    try:
        existing_series_map = {
            s.name: s.id for s in db.query(StickerSeries).filter(StickerSeries.is_deleted == False).all()
        }
        logger.info(f"confirm_import_stickers: existing_series_map={existing_series_map}")

        imported_count = 0

        for root, dirs, files in os.walk(target_dir):
            if "series.json" in files:
                series_json_file = Path(root) / "series.json"
                try:
                    with open(series_json_file, "r", encoding="utf-8") as sf:
                        s_data = json.load(sf)
                except Exception as e:
                    logger.error(f"confirm_import_stickers: failed to parse series.json: {str(e)}")
                    continue

                raw_name = s_data.get("series_name", "未命名系列")
                logger.info(f"confirm_import_stickers: found series in pack raw_name='{raw_name}'")
                if raw_name not in selected_series_names:
                    logger.info(f"confirm_import_stickers: raw_name='{raw_name}' not in selected_series_names, skipping")
                    continue

                final_series_name = raw_name
                series_id = None

                if raw_name in existing_series_map:
                    if conflict_resolution == "skip":
                        logger.info(f"confirm_import_stickers: raw_name='{raw_name}' exists and conflict_resolution='skip', skipping whole series")
                        continue
                    elif conflict_resolution == "merge":
                        series_id = existing_series_map[raw_name]
                        logger.info(f"confirm_import_stickers: raw_name='{raw_name}' exists and conflict_resolution='merge', merging into series_id={series_id}")
                    elif conflict_resolution == "rename":
                        idx = 1
                        while f"{raw_name}_{idx}" in existing_series_map:
                            idx += 1
                        final_series_name = f"{raw_name}_{idx}"
                        logger.info(f"confirm_import_stickers: raw_name='{raw_name}' exists and conflict_resolution='rename', renaming to '{final_series_name}'")

                if series_id is None:
                    new_series = StickerSeries(
                        name=final_series_name,
                        sort_order=s_data.get("sort_order", 0),
                        is_active=True
                    )
                    db.add(new_series)
                    db.flush()
                    series_id = new_series.id

                dest_dir = get_series_upload_dir(series_id)

                stickers_raw = s_data.get("stickers", [])
                for st in stickers_raw:
                    st_name = st.get("name", "贴纸")[:6]
                    
                    # 查找该系列下是否已存在同名且非软删除的贴纸
                    existing_sticker = db.query(StickerConfig).filter(
                        StickerConfig.series_id == series_id,
                        StickerConfig.name == st_name,
                        StickerConfig.is_deleted == False
                    ).first()

                    img_file = st.get("image_file", "")
                    src_img_path = Path(root) / img_file

                    final_image_url = ""
                    if img_file and src_img_path.exists():
                        ext = src_img_path.suffix or ".png"
                        dest_file_name = f"{uuid.uuid4().hex}{ext}"
                        dest_path = dest_dir / dest_file_name
                        shutil.copy(src_img_path, dest_path)
                        final_image_url = f"/static/uploads/stickers/series_{series_id}/{dest_file_name}"

                    if existing_sticker:
                        # 覆盖替换已有贴纸配置
                        logger.info(f"confirm_import_stickers: sticker name='{st_name}' exists (ID={existing_sticker.id}), updating...")
                        if final_image_url:
                            # 物理删除原贴纸绑定的图片，避免磁盘空间残留
                            if existing_sticker.image_url:
                                filename = os.path.basename(existing_sticker.image_url)
                                # 优先尝试从本系列上传子目录下定位
                                old_img_path = get_series_upload_dir(existing_sticker.series_id) / filename
                                if not old_img_path.exists():
                                    # 兼容兜底：平铺根目录
                                    old_img_path = STICKERS_UPLOAD_DIR / filename
                                
                                if old_img_path.exists():
                                    try:
                                        os.remove(old_img_path)
                                        logger.info(f"confirm_import_stickers: old physical image deleted: {old_img_path}")
                                    except Exception as ex:
                                        logger.error(f"confirm_import_stickers: failed to delete old physical image {old_img_path}: {str(ex)}")
                            existing_sticker.image_url = final_image_url
                            logger.info(f"confirm_import_stickers: updated image_url to {final_image_url}")
                        
                        if st.get("description") is not None:
                            existing_sticker.description = st.get("description")
                        # 🚨 排序（sort_order）不再被导入覆盖更新，保留本系列下原有的展示排序值，避免冲突
                        if st.get("exchange_price") is not None:
                            existing_sticker.exchange_price = st.get("exchange_price", 20)
                        db.flush()
                    else:
                        # 创建全新贴纸配置
                        logger.info(f"confirm_import_stickers: sticker name='{st_name}' is new, inserting...")
                        sticker_cfg = StickerConfig(
                            series_id=series_id,
                            name=st_name,
                            image_url=final_image_url,
                            description=st.get("description"),
                            sort_order=st.get("sort_order", 0),
                            exchange_price=st.get("exchange_price", 20),
                            is_active=True
                        )
                        db.add(sticker_cfg)
                        db.flush()
                        logger.info(f"confirm_import_stickers: inserted new sticker id={sticker_cfg.id}")

                imported_count += 1

        db.commit()
        return {"imported_series_count": imported_count}
    finally:
        shutil.rmtree(target_dir, ignore_errors=True)
