"""
手账商城数据平滑迁移服务
负责在系统启动时自动检测并将贴纸、画布等领域资产的售价与上架状态
无损同步注册至统一商品销售表 (shop_items) 中，确保向后兼容与平滑演进。
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...models import StickerConfig, CanvasSet, ShopItem


logger = logging.getLogger(__name__)

SHOP_ITEM_START_ID = 7001

def get_next_shop_item_id(db: Session) -> int:
    """获取下一个可用的统一商品 ID（7001 起步）"""
    max_id = db.query(func.max(ShopItem.id)).scalar()
    if max_id is None or max_id < SHOP_ITEM_START_ID - 1:
        return SHOP_ITEM_START_ID
    return max_id + 1

def migrate_shop_items(db: Session) -> int:
    """
    无损平滑迁移现有资产至统一商品表 shop_items
    返回新增同步的商品数量
    """
    synced_count = 0

    # 1. 迁移贴纸资产 (STICKER)
    stickers = db.query(StickerConfig).filter(StickerConfig.is_deleted == False).all()
    for sticker in stickers:
        existing_item = db.query(ShopItem).filter(
            ShopItem.item_type == "STICKER",
            ShopItem.target_id == sticker.id
        ).first()

        if not existing_item:
            price = getattr(sticker, "exchange_price", None) or 20
            new_item = ShopItem(
                id=get_next_shop_item_id(db),
                item_type="STICKER",
                target_id=sticker.id,
                original_price=price,
                sort_order=sticker.sort_order or 0,
                is_active=sticker.is_active if sticker.is_active is not None else True,
                is_deleted=sticker.is_deleted if sticker.is_deleted is not None else False
            )
            db.add(new_item)
            db.flush()
            synced_count += 1

    # 2. 迁移画布套件资产 (CANVAS_SET)
    canvases = db.query(CanvasSet).filter(CanvasSet.is_deleted == False).all()
    for canvas in canvases:
        existing_item = db.query(ShopItem).filter(
            ShopItem.item_type == "CANVAS_SET",
            ShopItem.target_id == canvas.id
        ).first()

        if not existing_item:
            price = getattr(canvas, "exchange_price", None) or 50
            new_item = ShopItem(
                id=get_next_shop_item_id(db),
                item_type="CANVAS_SET",
                target_id=canvas.id,
                original_price=price,
                sort_order=canvas.sort_order or 0,
                is_active=canvas.is_active if canvas.is_active is not None else True,
                is_deleted=canvas.is_deleted if canvas.is_deleted is not None else False
            )
            db.add(new_item)
            db.flush()
            synced_count += 1

    if synced_count > 0:
        db.commit()
        logger.info(f"[ShopMigration] 成功自动无损同步 {synced_count} 个存量资产到 shop_items 统一商品表")

    return synced_count
