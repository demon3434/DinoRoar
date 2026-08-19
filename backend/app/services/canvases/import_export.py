"""
Zip export and import services for canvases series packs.
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
from typing import Optional, List, Dict
from pathlib import Path
from sqlalchemy.orm import Session
from ...models import CanvasSeries, CanvasSet, CanvasInstance
from ...config import settings

STATIC_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static")))
CANVASES_UPLOAD_DIR = Path(settings.upload_dir) / "canvases"
TEMP_IMPORT_DIR = Path(settings.upload_dir) / "temp" / "canvases"

def get_series_upload_dir(series_id: int) -> Path:
    d = CANVASES_UPLOAD_DIR / f"series_{series_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d

def export_canvas_series_zip(db: Session, series_ids: list) -> io.BytesIO:
    """
    打包导出指定的画布系列为符合统一规范标准的 Zip 内存文件流
    """
    series_list = db.query(CanvasSeries).filter(
        CanvasSeries.id.in_(series_ids),
        CanvasSeries.is_deleted == False
    ).order_by(CanvasSeries.sort_order.asc(), CanvasSeries.id.asc()).all()

    if not series_list:
        raise ValueError("未查找到指定的画布系列")

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

            sets = db.query(CanvasSet).filter(
                CanvasSet.series_id == s.id,
                CanvasSet.is_deleted == False
            ).order_by(CanvasSet.sort_order.asc(), CanvasSet.id.asc()).all()

            sets_data = []
            for cset in sets:
                instances = db.query(CanvasInstance).filter(
                    CanvasInstance.canvas_set_id == cset.id,
                    CanvasInstance.is_deleted == False
                ).all()

                instances_data = []
                for inst in instances:
                    url_clean = inst.image_url.split("?")[0]
                    img_name = os.path.basename(url_clean) if inst.image_url else ""
                    real_img_path = None

                    # 如果是在 static 下的内置图片
                    if inst.image_url and inst.image_url.startswith("/static/"):
                        if not inst.image_url.startswith("/static/uploads/"):
                            rel_path = inst.image_url.replace("/static/", "", 1)
                            target_p = STATIC_DIR / rel_path
                            if target_p.exists():
                                real_img_path = target_p

                    # 如果在 uploads 目录下
                    if not real_img_path or not real_img_path.exists():
                        p = CANVASES_UPLOAD_DIR / f"series_{s.id}" / img_name
                        if p.exists():
                            real_img_path = p

                    if img_name and real_img_path and real_img_path.exists():
                        zf.write(real_img_path, f"{dir_name}/{img_name}")

                    instances_data.append({
                        "aspect_ratio": inst.aspect_ratio,
                        "image_file": img_name,
                        "width": inst.width,
                        "height": inst.height
                    })

                sets_data.append({
                    "name": cset.name,
                    "description": cset.description,
                    "sort_order": cset.sort_order,
                    "exchange_price": cset.exchange_price,
                    "instances": instances_data
                })

            series_json_data = {
                "series_name": s.name,
                "sort_order": s.sort_order,
                "description": "",
                "canvas_sets": sets_data
            }
            zf.writestr(f"{dir_name}/series.json", json.dumps(series_json_data, ensure_ascii=False, indent=2))

        pack_info = {
            "spec_version": "1.0",
            "app": "DinoRoar",
            "type": "canvases",
            "exported_at": datetime.datetime.utcnow().isoformat() + "Z",
            "series_count": len(series_info_list),
            "series_list": series_info_list
        }
        zf.writestr("pack_info.json", json.dumps(pack_info, ensure_ascii=False, indent=2))

    memory_file.seek(0)
    return memory_file


def clean_stale_temp_imports(max_age_seconds: int = 1800):
    """
    清理临时导入目录中超过 30 分钟未处理的陈旧临时文件夹
    """
    if not TEMP_IMPORT_DIR.exists():
        return
    now = datetime.datetime.now().timestamp()
    for item in TEMP_IMPORT_DIR.iterdir():
        if item.is_dir():
            try:
                mtime = item.stat().st_mtime
                if now - mtime > max_age_seconds:
                    shutil.rmtree(item, ignore_errors=True)
            except Exception:
                pass


def cancel_import_temp(temp_token: str):
    """
    取消画布包导入并立即清理对应的临时解压目录
    """
    if not temp_token:
        return
    safe_token = os.path.basename(temp_token.strip())
    target_dir = TEMP_IMPORT_DIR / safe_token
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)


from PIL import Image

def generate_canvas_thumbnail_b64(img_path: Path, max_width: int = 240) -> str:
    """
    为前端卡片网格生成轻量级缩略图 Base64 (240px)，大幅缩减 JSON 大小，避免前端百兆内存阻塞与卡顿
    """
    try:
        with Image.open(img_path) as im:
            w, h = im.size
            if w > max_width:
                new_h = max(1, int(h * (max_width / w)))
                im = im.resize((max_width, new_h), Image.Resampling.BILINEAR)
            buf = io.BytesIO()
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                im.save(buf, format="PNG", optimize=True)
                ext = "png"
            else:
                if im.mode != "RGB":
                    im = im.convert("RGB")
                im.save(buf, format="JPEG", quality=70, optimize=True)
                ext = "jpeg"
            return f"data:image/{ext};base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        try:
            with open(img_path, "rb") as imf:
                ext = img_path.suffix.lstrip(".").lower() or "jpg"
                return f"data:image/{ext};base64," + base64.b64encode(imf.read()).decode("utf-8")
        except Exception:
            return ""


def preview_import_canvas_zip(zip_bytes: bytes, db: Session) -> dict:
    """
    解压并安全校验上传的画布包，解析元数据并准备前端轻量级预览数据
    """
    clean_stale_temp_imports()

    if len(zip_bytes) > 500 * 1024 * 1024:
        raise ValueError("上传的画布包不能超过 500MB")

    temp_token = uuid.uuid4().hex
    target_dir = TEMP_IMPORT_DIR / temp_token
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            target_dir_canonical = os.path.realpath(target_dir)
            for member in zf.infolist():
                extracted_path = os.path.realpath(target_dir / member.filename)
                if not extracted_path.startswith(target_dir_canonical):
                    raise ValueError("极高风险：检测到画布包中包含路径穿越越权文件")
            zf.extractall(target_dir)
    except Exception as e:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ValueError(f"画布包格式非法或解析解压失败: {str(e)}")

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

    if pack_info.get("type") != "canvases":
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ValueError("格式错误：上传的文件非画布包")

    existing_series_names = {
        s.name for s in db.query(CanvasSeries).filter(CanvasSeries.is_deleted == False).all()
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
            canvas_sets_raw = s_data.get("canvas_sets", [])
            canvas_sets_preview = []

            for cset in canvas_sets_raw:
                instances_preview = []
                for inst in cset.get("instances", []):
                    img_file = inst.get("image_file", "")
                    img_path = Path(root) / img_file
                    img_b64 = ""
                    rel_file_path = ""
                    if img_file and img_path.exists():
                        img_b64 = generate_canvas_thumbnail_b64(img_path, max_width=240)
                        try:
                            rel_file_path = str(img_path.relative_to(target_dir)).replace("\\", "/")
                        except Exception:
                            rel_file_path = img_file

                    instances_preview.append({
                        "aspect_ratio": inst.get("aspect_ratio", "16:9"),
                        "image_b64": img_b64,
                        "file_path": rel_file_path,
                        "width": inst.get("width", 1440),
                        "height": inst.get("height", 810)
                    })

                canvas_sets_preview.append({
                    "name": cset.get("name", ""),
                    "description": cset.get("description", ""),
                    "exchange_price": cset.get("exchange_price", 50),
                    "sort_order": cset.get("sort_order", 0),
                    "instances": instances_preview
                })

            dir_basename = os.path.basename(root)
            raw_series_map[dir_basename] = {
                "series_name": s_name,
                "dir_name": dir_basename,
                "sort_order": s_data.get("sort_order", 0),
                "is_name_conflict": s_name in existing_series_names,
                "set_count": len(canvas_sets_preview),
                "canvas_sets": canvas_sets_preview
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


def confirm_import_canvases(
    temp_token: str,
    selected_series_names: list,
    conflict_resolution: str,
    selected_sets_map: Optional[dict] = None,
    db: Session = None
) -> dict:
    """
    读取解压缓存中的画布包，根据策略将画布及商品套和实例落库，
    并将图片文件拷贝落盘写入相对路径 canvases/series_{series_id}/
    """
    target_dir = TEMP_IMPORT_DIR / temp_token
    if not target_dir.exists():
        raise ValueError("导入缓存已过期或不存在，请重新上传画布包")

    try:
        existing_series_map = {
            s.name: s.id for s in db.query(CanvasSeries).filter(CanvasSeries.is_deleted == False).all()
        }

        imported_series_count = 0
        imported_sets_count = 0
        copied_files = []

        for root, dirs, files in os.walk(target_dir):
            if "series.json" in files:
                series_json_file = Path(root) / "series.json"
                try:
                    with open(series_json_file, "r", encoding="utf-8") as sf:
                        s_data = json.load(sf)
                except Exception:
                    continue

                raw_name = s_data.get("series_name", "未命名系列")
                if raw_name not in selected_series_names:
                    continue

                canvas_sets_raw = s_data.get("canvas_sets", [])
                # 如果传入了按系列指定的套件名单，则按套件名称进行精确过滤
                if selected_sets_map is not None and raw_name in selected_sets_map:
                    target_set_names = set(selected_sets_map[raw_name])
                    canvas_sets_raw = [cs for cs in canvas_sets_raw if cs.get("name") in target_set_names]

                if not canvas_sets_raw:
                    # 该系列没有需要导入的画布套件，跳过
                    continue

                final_series_name = raw_name
                series_id = None

                if raw_name in existing_series_map:
                    if conflict_resolution == "skip":
                        continue
                    elif conflict_resolution == "merge":
                        series_id = existing_series_map[raw_name]
                    elif conflict_resolution == "rename":
                        idx = 1
                        while f"{raw_name}_{idx}" in existing_series_map:
                            idx += 1
                        final_series_name = f"{raw_name}_{idx}"

                if series_id is None:
                    new_series = CanvasSeries(
                        name=final_series_name,
                        sort_order=s_data.get("sort_order", 0),
                        is_active=True
                    )
                    db.add(new_series)
                    db.flush()
                    series_id = new_series.id

                dest_dir = get_series_upload_dir(series_id)

                for cset_raw in canvas_sets_raw:
                    cset_name = cset_raw.get("name", "画布")
                    
                    existing_set = db.query(CanvasSet).filter(
                        CanvasSet.series_id == series_id,
                        CanvasSet.name == cset_name,
                        CanvasSet.is_deleted == False
                    ).first()

                    if existing_set:
                        cset_id = existing_set.id
                        existing_set.description = cset_raw.get("description", existing_set.description)
                        existing_set.exchange_price = cset_raw.get("exchange_price", existing_set.exchange_price)
                        existing_set.sort_order = cset_raw.get("sort_order", existing_set.sort_order)
                    else:
                        max_set_id = db.query(CanvasSet.id).filter(CanvasSet.id >= 3001).order_by(CanvasSet.id.desc()).first()
                        next_set_id = 3001 if not max_set_id else max_set_id[0] + 1
                        new_set = CanvasSet(
                            id=next_set_id,
                            series_id=series_id,
                            name=cset_name,
                            description=cset_raw.get("description", ""),
                            exchange_price=cset_raw.get("exchange_price", 50),
                            sort_order=cset_raw.get("sort_order", 0),
                            is_active=True
                        )
                        db.add(new_set)
                        db.flush()
                        cset_id = new_set.id

                    for inst_raw in cset_raw.get("instances", []):
                        ratio = inst_raw.get("aspect_ratio", "16:9")
                        img_file = inst_raw.get("image_file", "")
                        src_img_path = Path(root) / img_file

                        if img_file and src_img_path.exists():
                            ratio_suffix = ratio.replace(":", "_")
                            # 保留原图的实际后缀（.jpg 或 .png），不执行二次压缩
                            src_ext = src_img_path.suffix.lower()
                            dest_file_name = f"canvas_{cset_id}_{ratio_suffix}{src_ext}"
                            dest_path = dest_dir / dest_file_name

                            # 直接拷贝原图，保留设计师原始质量，避免 JPEG 二次有损压缩
                            shutil.copy(src_img_path, dest_path)

                            copied_files.append(dest_path)

                            final_image_url = f"/static/uploads/canvases/series_{series_id}/{dest_file_name}"

                            existing_inst = db.query(CanvasInstance).filter(
                                CanvasInstance.canvas_set_id == cset_id,
                                CanvasInstance.aspect_ratio == ratio
                            ).first()

                            if existing_inst:
                                existing_inst.image_url = final_image_url
                                existing_inst.width = inst_raw.get("width", 1440)
                                existing_inst.height = inst_raw.get("height", 810)
                                existing_inst.is_deleted = False
                                db.flush()
                            else:
                                max_inst_id = db.query(CanvasInstance.id).filter(CanvasInstance.id >= 4001).order_by(CanvasInstance.id.desc()).first()
                                next_inst_id = 4001 if not max_inst_id else max_inst_id[0] + 1
                                new_inst = CanvasInstance(
                                    id=next_inst_id,
                                    canvas_set_id=cset_id,
                                    aspect_ratio=ratio,
                                    image_url=final_image_url,
                                    width=inst_raw.get("width", 1440),
                                    height=inst_raw.get("height", 810),
                                    is_active=True
                                )
                                db.add(new_inst)
                                db.flush()

                    # 同步写入商城统一商品表
                    from ..shop.items import sync_asset_shop_item
                    sync_asset_shop_item(
                        db=db,
                        item_type="CANVAS_SET",
                        target_id=cset_id,
                        original_price=cset_raw.get("exchange_price", 50),
                        sort_order=cset_raw.get("sort_order", 0),
                        is_active=True
                    )

                    imported_sets_count += 1

                imported_series_count += 1

        db.commit()
        return {
            "imported_series_count": imported_series_count,
            "imported_sets_count": imported_sets_count,
            "imported_count": imported_series_count,
            "message": f"已成功导入 {imported_series_count} 个系列（共 {imported_sets_count} 套画布）"
        }
    except Exception as e:
        db.rollback()
        for f in copied_files:
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                pass
        raise ValueError(f"正式导入确认落库失败: {str(e)}")
    finally:
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
        except Exception:
            pass
