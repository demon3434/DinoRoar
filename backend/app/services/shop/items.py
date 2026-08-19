"""
统一商品服务 (Shop Item Service)
负责统一商城商品检索、促销计价集成、资产库存发放与统一结算
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ...models import (
    User, ShopItem, StickerConfig, StickerSeries,
    CanvasSet, CanvasSeries, CanvasInstance
)

from .pricing import calculate_item_price
from .promotions import get_active_promotion_targets
from .migration import get_next_shop_item_id

logger = logging.getLogger(__name__)


def sync_asset_shop_item(
    db: Session,
    item_type: str,
    target_id: int,
    original_price: int,
    sort_order: int = 0,
    is_active: bool = True
) -> ShopItem:
    """
    当领域资产（贴纸或画布套）被创建或编辑时，联动同步更新统一商品销售表
    """
    item = db.query(ShopItem).filter(
        ShopItem.item_type == item_type,
        ShopItem.target_id == target_id
    ).first()

    if not item:
        item = ShopItem(
            id=get_next_shop_item_id(db),
            item_type=item_type,
            target_id=target_id,
            original_price=original_price,
            sort_order=sort_order,
            is_active=is_active,
            is_deleted=False
        )
        db.add(item)
    else:
        item.original_price = original_price
        item.sort_order = sort_order
        item.is_active = is_active
        item.is_deleted = False

    db.flush()
    return item


def list_shop_items(
    db: Session,
    item_type: Optional[str] = None,
    series_id: Optional[int] = None,
    user: Optional[User] = None,
    admin_view: bool = False
) -> List[Dict[str, Any]]:
    """
    查询统一商品列表（结合促销计价引擎计算实付价并附带资产详情与拥有状态）
    """
    active_targets = get_active_promotion_targets(db)

    query = db.query(ShopItem).filter(ShopItem.is_deleted == False)
    if not admin_view:
        query = query.filter(ShopItem.is_active == True)
    if item_type:
        query = query.filter(ShopItem.item_type == item_type)

    items = query.order_by(ShopItem.sort_order.asc(), ShopItem.id.asc()).all()

    # 解析当前用户的贴纸与画布库存
    owned_sticker_counts: Dict[int, int] = {}
    owned_canvas_set_ids = set()

    if user:
        if user.sticker_inventory:
            for seg in user.sticker_inventory.split(','):
                if ':' in seg:
                    sid, cnt = seg.split(':', 1)
                    try:
                        owned_sticker_counts[int(sid)] = int(cnt)
                    except ValueError:
                        pass
        if user.canvas_inventory:
            for cid in user.canvas_inventory.split(','):
                try:
                    owned_canvas_set_ids.add(int(cid.strip()))
                except ValueError:
                    pass

    result = []
    for item in items:
        asset_info: Dict[str, Any] = {}
        s_id: Optional[int] = None
        s_name = ""
        is_owned = False
        owned_count = 0

        if item.item_type == "STICKER":
            sticker = db.query(StickerConfig).filter(
                StickerConfig.id == item.target_id,
                StickerConfig.is_deleted == False
            ).first()
            if not sticker:
                continue
            s_id = sticker.series_id
            if s_id:
                series = db.query(StickerSeries).filter(StickerSeries.id == s_id).first()
                s_name = series.name if series else ""

            asset_info = {
                "name": sticker.name,
                "image_url": sticker.image_url,
                "description": sticker.description or "",
                "series_id": s_id,
                "series_name": s_name
            }
            owned_count = owned_sticker_counts.get(sticker.id, 0)
            is_owned = owned_count > 0

        elif item.item_type == "CANVAS_SET":
            canvas = db.query(CanvasSet).filter(
                CanvasSet.id == item.target_id,
                CanvasSet.is_deleted == False
            ).first()
            if not canvas:
                continue
            s_id = canvas.series_id
            if s_id:
                cseries = db.query(CanvasSeries).filter(CanvasSeries.id == s_id).first()
                s_name = cseries.name if cseries else ""

            # 获取该画布套下的全部比例实例
            instances = db.query(CanvasInstance).filter(
                CanvasInstance.canvas_set_id == canvas.id,
                CanvasInstance.is_deleted == False,
                CanvasInstance.is_active == True
            ).all()

            asset_info = {
                "name": canvas.name,
                "description": canvas.description or "",
                "series_id": s_id,
                "series_name": s_name,
                "instances": [
                    {
                        "id": inst.id,
                        "aspect_ratio": inst.aspect_ratio,
                        "image_url": inst.image_url,
                        "width": inst.width,
                        "height": inst.height
                    }
                    for inst in instances
                ]
            }
            is_owned = canvas.id in owned_canvas_set_ids

        # 筛选指定系列
        if series_id is not None and s_id != series_id:
            continue

        # 计算当前促销价格
        current_price, is_on_sale = calculate_item_price(
            original_price=item.original_price,
            item_type=item.item_type,
            shop_item_id=item.id,
            series_id=s_id,
            active_targets=active_targets
        )

        result.append({
            "shop_item_id": item.id,
            "item_type": item.item_type,
            "target_id": item.target_id,
            "original_price": item.original_price,
            "current_price": current_price,
            "is_on_sale": is_on_sale,
            "is_active": item.is_active,
            "sort_order": item.sort_order,
            "is_owned": is_owned,
            "owned_count": owned_count,
            "asset": asset_info
        })

    return result


def exchange_shop_items(
    db: Session,
    user_id: int,
    shop_item_ids: List[int]
) -> Dict[str, Any]:
    """
    统一兑换结算服务：在单个事务内校验余额、扣减蛋能量并按类型分发资产到背包
    """
    if not shop_item_ids:
        raise HTTPException(status_code=400, detail="未选择任何待兑换商品")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    active_targets = get_active_promotion_targets(db)
    total_cost = 0
    total_original_cost = 0
    purchased_items = []

    # 解析现有贴纸库存与画布库存
    sticker_inv: Dict[int, int] = {}
    if user.sticker_inventory:
        for seg in user.sticker_inventory.split(','):
            if ':' in seg:
                sid, cnt = seg.split(':', 1)
                try:
                    sticker_inv[int(sid)] = int(cnt)
                except ValueError:
                    pass

    canvas_inv = set()
    if user.canvas_inventory:
        for cid in user.canvas_inventory.split(','):
            try:
                canvas_inv.add(int(cid.strip()))
            except ValueError:
                pass

    for item_id in shop_item_ids:
        item = db.query(ShopItem).filter(
            ShopItem.id == item_id,
            ShopItem.is_deleted == False,
            ShopItem.is_active == True
        ).first()

        if not item:
            raise HTTPException(status_code=404, detail=f"商品 (ID: {item_id}) 不存在或已下架")

        # 查找系列 ID 辅助计价
        s_id = None
        if item.item_type == "STICKER":
            st = db.query(StickerConfig).filter(StickerConfig.id == item.target_id).first()
            if st:
                s_id = st.series_id
        elif item.item_type == "CANVAS_SET":
            cs = db.query(CanvasSet).filter(CanvasSet.id == item.target_id).first()
            if cs:
                s_id = cs.series_id

        current_price, _ = calculate_item_price(
            original_price=item.original_price,
            item_type=item.item_type,
            shop_item_id=item.id,
            series_id=s_id,
            active_targets=active_targets
        )

        total_cost += current_price
        total_original_cost += item.original_price

        # 分发资产到内存数据中
        if item.item_type == "STICKER":
            sticker_inv[item.target_id] = sticker_inv.get(item.target_id, 0) + 1
        elif item.item_type == "CANVAS_SET":
            canvas_inv.add(item.target_id)

        purchased_items.append({
            "shop_item_id": item.id,
            "item_type": item.item_type,
            "target_id": item.target_id,
            "original_price": item.original_price,
            "current_price": current_price
        })

    # 通过统一能量引擎逐项扣减蛋能量并写入流水
    import uuid
    from ..energy_service import EnergyEngineService
    for p_item in purchased_items:
        if p_item["current_price"] > 0:
            EnergyEngineService.apply_transaction(
                db=db,
                user_id=user_id,
                event_type_id=301,  # SHOP_EXCHANGE
                change_amount=-p_item["current_price"],
                target_type_id=1,   # SHOP_ITEM
                target_id=p_item["shop_item_id"],
                request_uuid=str(uuid.uuid4()),
                commit=False
            )

    # 序列化贴纸背包 "1001:2,1002:1"
    user.sticker_inventory = ",".join([f"{sid}:{cnt}" for sid, cnt in sorted(sticker_inv.items())])
    # 序列化画布背包 "3001,3002"
    user.canvas_inventory = ",".join([str(cid) for cid in sorted(canvas_inv)])

    db.commit()
    db.refresh(user)

    return {
        "success": True,

        "total_original_cost": total_original_cost,
        "total_cost": total_cost,
        "saved_energy": max(0, total_original_cost - total_cost),
        "remaining_energy": user.egg_energy,
        "purchased_count": len(purchased_items),
        "items": purchased_items
    }
