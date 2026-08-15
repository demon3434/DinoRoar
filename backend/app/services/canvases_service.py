import os
import io
from PIL import Image
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import CanvasSeries, CanvasSet, CanvasInstance
from ..config import settings

def get_canvases_config(db: Session, only_active: bool = True, apply_promo: bool = True) -> List[dict]:
    """
    获取画布系列分类及其嵌套的商品套、图片列表
    apply_promo: True 则 exchange_price 为当前促销实付价；False 则为基础原价（供 Admin 端使用）
    """
    from .shop.pricing import calculate_item_price
    from .shop.promotions import get_active_promotion_targets
    from ..models import ShopItem

    active_targets = get_active_promotion_targets(db) if apply_promo else []

    query = db.query(CanvasSeries).filter(CanvasSeries.is_deleted == False)
    if only_active:
        query = query.filter(CanvasSeries.is_active == True)
    series_list = query.order_by(CanvasSeries.sort_order.asc(), CanvasSeries.id.asc()).all()

    result = []
    ratio_order = {"16:9": 0, "4:3": 1, "1:1": 2, "2:1": 3}

    for series in series_list:
        set_query = db.query(CanvasSet).filter(CanvasSet.series_id == series.id, CanvasSet.is_deleted == False)
        if only_active:
            set_query = set_query.filter(CanvasSet.is_active == True)
        sets = set_query.order_by(CanvasSet.sort_order.asc(), CanvasSet.id.asc()).all()

        sets_response = []
        for cset in sets:
            inst_query = db.query(CanvasInstance).filter(
                CanvasInstance.canvas_set_id == cset.id,
                CanvasInstance.is_deleted == False
            )
            if only_active:
                inst_query = inst_query.filter(CanvasInstance.is_active == True)
            instances = inst_query.all()
            sorted_instances = sorted(instances, key=lambda inst: ratio_order.get(inst.aspect_ratio, 99))
            
            # 计算促销折后价
            shop_item = db.query(ShopItem).filter(
                ShopItem.item_type == "CANVAS_SET",
                ShopItem.target_id == cset.id
            ).first()
            orig = shop_item.original_price if shop_item else (cset.exchange_price or 50)
            item_id = shop_item.id if shop_item else 7000 + cset.id
            price, is_sale = calculate_item_price(
                original_price=orig,
                item_type="CANVAS_SET",
                shop_item_id=item_id,
                series_id=series.id,
                active_targets=active_targets
            )

            sets_response.append({
                "id": cset.id,
                "series_id": cset.series_id,
                "name": cset.name,
                "description": cset.description,
                "sort_order": cset.sort_order,
                "exchange_price": price if apply_promo else orig,
                "original_price": orig,
                "is_on_sale": is_sale,
                "is_active": cset.is_active,
                "is_deleted": cset.is_deleted,
                "created_at": cset.created_at,
                "instances": sorted_instances
            })



        result.append({
            "id": series.id,
            "name": series.name,
            "sort_order": series.sort_order,
            "is_active": series.is_active,
            "is_deleted": series.is_deleted,
            "created_at": series.created_at,
            "sets": sets_response
        })
    return result

def create_canvas_series(db: Session, name: str, sort_order: int = 0) -> CanvasSeries:
    """
    新建画布分类系列
    """
    max_id = db.query(CanvasSeries.id).order_by(CanvasSeries.id.desc()).first()
    next_id = 1
    if max_id:
        next_id = max_id[0] + 1

    series = CanvasSeries(
        id=next_id,
        name=name,
        sort_order=sort_order,
        is_active=True
    )
    db.add(series)
    db.commit()
    db.refresh(series)
    series.sets = []
    return series

def update_canvas_series(db: Session, series_id: int, name: str, sort_order: int) -> CanvasSeries:
    """
    更新画布分类系列基本信息
    """
    series = db.query(CanvasSeries).filter(CanvasSeries.id == series_id, CanvasSeries.is_deleted == False).first()
    if not series:
        raise HTTPException(status_code=404, detail="画布分类系列不存在")
    series.name = name
    series.sort_order = sort_order
    db.commit()
    db.refresh(series)
    return series

def toggle_canvas_series_active(db: Session, series_id: int) -> CanvasSeries:
    """
    切换系列启用/停用状态
    """
    series = db.query(CanvasSeries).filter(CanvasSeries.id == series_id, CanvasSeries.is_deleted == False).first()
    if not series:
        raise HTTPException(status_code=404, detail="画布分类系列不存在")
    series.is_active = not series.is_active
    db.commit()
    db.refresh(series)
    return series

def delete_canvas_series_cascade(db: Session, series_id: int):
    """
    级联软删除分类系列及所有下属画布和图片
    """
    series = db.query(CanvasSeries).filter(CanvasSeries.id == series_id, CanvasSeries.is_deleted == False).first()
    if not series:
        raise HTTPException(status_code=404, detail="画布分类系列不存在")
    series.is_deleted = True
    
    sets = db.query(CanvasSet).filter(CanvasSet.series_id == series_id).all()
    for cset in sets:
        cset.is_deleted = True
        db.query(CanvasInstance).filter(CanvasInstance.canvas_set_id == cset.id).update({"is_deleted": True})
    db.commit()

def sort_canvas_series(db: Session, series_ids: List[int]):
    """
    更新画布分类系列排序顺序
    """
    for index, series_id in enumerate(series_ids, start=1):
        db.query(CanvasSeries).filter(CanvasSeries.id == series_id).update({"sort_order": index})
    db.commit()

def reorder_sets_in_series(db: Session, target_series_id: int, current_set_id: int, desired_sort_order: int, old_series_id: Optional[int] = None):
    """
    顺位插入重排逻辑：
    1. 如果跨系列移动，先紧凑重排旧系列剩余项 (1..N)。
    2. 在目标系列中，将除 current_set_id 之外的画布按原顺序取出。
    3. 根据 desired_sort_order (1-based) 将 current_set_id 插入到对应位置 (例如序号 1 插在开头，序号 20 插在第 20 位)。
    4. 统一将目标系列中所有画布顺延赋值为连续序号 1, 2, 3...
    """
    # 1. 跨系列移出时，重排旧系列
    if old_series_id and old_series_id != target_series_id:
        old_sets = db.query(CanvasSet).filter(
            CanvasSet.series_id == old_series_id,
            CanvasSet.id != current_set_id,
            CanvasSet.is_deleted == False
        ).order_by(CanvasSet.sort_order.asc(), CanvasSet.id.asc()).all()
        for idx, s in enumerate(old_sets, start=1):
            s.sort_order = idx

    # 2. 目标系列已有其他画布
    target_sets = db.query(CanvasSet).filter(
        CanvasSet.series_id == target_series_id,
        CanvasSet.id != current_set_id,
        CanvasSet.is_deleted == False
    ).order_by(CanvasSet.sort_order.asc(), CanvasSet.id.asc()).all()

    current_set = db.query(CanvasSet).filter(CanvasSet.id == current_set_id).first()
    if not current_set:
        return

    # 3. 计算插入索引 (0-based)
    # 若 desired_sort_order <= 1，插在索引 0；若大于当前总数，插在末尾
    insert_idx = max(0, min(desired_sort_order - 1, len(target_sets)))
    target_sets.insert(insert_idx, current_set)

    # 4. 连续重排 (1, 2, 3...)
    for idx, s in enumerate(target_sets, start=1):
        s.sort_order = idx

def create_canvas_set(db: Session, series_id: int, name: str, description: Optional[str] = None, exchange_price: int = 50, sort_order: int = 1) -> CanvasSet:
    """
    新建画布商品套（支持顺位插入重排）
    """
    series = db.query(CanvasSeries).filter(CanvasSeries.id == series_id).first()
    if not series:
        raise HTTPException(status_code=400, detail="对应的画布分类系列不存在")

    max_id = db.query(CanvasSet.id).filter(CanvasSet.id >= 3001).order_by(CanvasSet.id.desc()).first()
    next_id = 3001
    if max_id:
        next_id = max_id[0] + 1

    cset = CanvasSet(
        id=next_id,
        series_id=series_id,
        name=name,
        description=description,
        sort_order=sort_order,
        exchange_price=exchange_price,
        is_active=True
    )
    db.add(cset)
    db.flush()

    # 执行顺位插入重排
    reorder_sets_in_series(db, target_series_id=series_id, current_set_id=next_id, desired_sort_order=sort_order)
    db.commit()
    db.refresh(cset)
    cset.instances = []
    return cset

def update_canvas_set(db: Session, set_id: int, series_id: int, name: str, description: Optional[str], exchange_price: int, sort_order: int) -> CanvasSet:
    """
    修改画布商品套基本信息（支持顺位插入重排）
    """
    cset = db.query(CanvasSet).filter(CanvasSet.id == set_id, CanvasSet.is_deleted == False).first()
    if not cset:
        raise HTTPException(status_code=404, detail="商品套件不存在")
    series = db.query(CanvasSeries).filter(CanvasSeries.id == series_id).first()
    if not series:
        raise HTTPException(status_code=400, detail="指定的分类系列不存在")

    old_series_id = cset.series_id
    cset.series_id = series_id
    cset.name = name
    cset.description = description
    cset.exchange_price = exchange_price

    # 执行顺位插入重排
    reorder_sets_in_series(db, target_series_id=series_id, current_set_id=set_id, desired_sort_order=sort_order, old_series_id=old_series_id)
    db.commit()
    db.refresh(cset)
    return cset

def toggle_canvas_set_active(db: Session, set_id: int) -> CanvasSet:
    """
    切换画布商品套启用/停用状态
    """
    cset = db.query(CanvasSet).filter(CanvasSet.id == set_id, CanvasSet.is_deleted == False).first()
    if not cset:
        raise HTTPException(status_code=404, detail="商品套件不存在")
    cset.is_active = not cset.is_active
    db.commit()
    db.refresh(cset)
    return cset

def delete_canvas_set(db: Session, set_id: int):
    """
    软删除画布商品套件并紧凑重排系列内其余画布
    """
    if set_id == 3001:
        raise HTTPException(status_code=400, detail="内置的画布（森林家园）为系统预设底图，不允许删除")
    cset = db.query(CanvasSet).filter(CanvasSet.id == set_id, CanvasSet.is_deleted == False).first()
    if not cset:
        raise HTTPException(status_code=404, detail="商品套件不存在")
    cset.is_deleted = True
    db.query(CanvasInstance).filter(CanvasInstance.canvas_set_id == set_id).update({"is_deleted": True})
    
    # 紧凑重排该系列内剩余画布
    remaining_sets = db.query(CanvasSet).filter(
        CanvasSet.series_id == cset.series_id,
        CanvasSet.id != set_id,
        CanvasSet.is_deleted == False
    ).order_by(CanvasSet.sort_order.asc(), CanvasSet.id.asc()).all()
    for idx, s in enumerate(remaining_sets, start=1):
        s.sort_order = idx

    db.commit()

def sort_canvas_sets(db: Session, set_ids: List[int]):
    """
    更新商品套排序顺序 (1..N)
    """
    for index, set_id in enumerate(set_ids, start=1):
        db.query(CanvasSet).filter(CanvasSet.id == set_id).update({"sort_order": index})
    db.commit()

async def process_and_save_canvas_instance(db: Session, canvas_set_id: int, aspect_ratio: str, file: UploadFile) -> CanvasInstance:
    """
    处理上传的画布图片物理裁剪和重采样，并保存为 JPEG（quality=90）文件，然后记录入库
    """
    cset = db.query(CanvasSet).filter(CanvasSet.id == canvas_set_id, CanvasSet.is_deleted == False).first()
    if not cset:
        raise HTTPException(status_code=404, detail="画布套件不存在")

    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        ratio_map = {"16:9": 16 / 9, "4:3": 4 / 3, "1:1": 1.0, "2:1": 2.0}
        r_val = ratio_map[aspect_ratio]
        
        target_width = 1440
        target_height = int(target_width / r_val)
        resized_img = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        # JPEG 不支持透明通道，强制转换为 RGB 模式
        resized_img = resized_img.convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片读取或缩放处理失败: {str(e)}")

    ratio_suffix = aspect_ratio.replace(":", "_")
    relative_dir = f"canvases/series_{cset.series_id}"
    physical_dir = os.path.join(settings.upload_dir, relative_dir)
    os.makedirs(physical_dir, exist_ok=True)
    
    file_name = f"canvas_{cset.id}_{ratio_suffix}.jpg"
    physical_path = os.path.join(physical_dir, file_name)
    resized_img.save(physical_path, format="JPEG", quality=90)
    
    image_url = f"/static/uploads/{relative_dir}/{file_name}"

    instance = db.query(CanvasInstance).filter(
        CanvasInstance.canvas_set_id == cset.id,
        CanvasInstance.aspect_ratio == aspect_ratio
    ).first()
    
    if not instance:
        max_id = db.query(CanvasInstance.id).filter(CanvasInstance.id >= 4001).order_by(CanvasInstance.id.desc()).first()
        next_id = 4001
        if max_id:
            next_id = max_id[0] + 1
            
        instance = CanvasInstance(
            id=next_id,
            canvas_set_id=cset.id,
            aspect_ratio=aspect_ratio,
            image_url=image_url,
            width=target_width,
            height=target_height,
            is_active=True
        )
        db.add(instance)
    else:
        instance.image_url = image_url
        instance.width = target_width
        instance.height = target_height
        instance.is_deleted = False

    db.commit()
    db.refresh(instance)
    return instance

def toggle_canvas_instance_active(db: Session, instance_id: int) -> CanvasInstance:
    """
    切换单个图片实例的启用/停用状态
    """
    instance = db.query(CanvasInstance).filter(CanvasInstance.id == instance_id, CanvasInstance.is_deleted == False).first()
    if not instance:
        raise HTTPException(status_code=404, detail="画布图片实例不存在")
    instance.is_active = not instance.is_active
    db.commit()
    db.refresh(instance)
    return instance

def delete_canvas_instance(db: Session, instance_id: int):
    """
    软删除单个画布图片实例
    """
    instance = db.query(CanvasInstance).filter(CanvasInstance.id == instance_id, CanvasInstance.is_deleted == False).first()
    if not instance:
        raise HTTPException(status_code=404, detail="画布图片实例不存在")
    instance.is_deleted = True
    db.commit()
