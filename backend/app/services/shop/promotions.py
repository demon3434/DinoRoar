"""
促销活动服务 (Promotion Service)
负责促销活动的生命周期管理、规则维护及生效活动快速检索
"""

import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...models import Promotion, PromotionTarget


PROMOTION_START_ID = 5001
PROMOTION_TARGET_START_ID = 6001

def get_next_promotion_id(db: Session) -> int:
    """获取下一个促销活动 ID（5001 起步）"""
    max_id = db.query(func.max(Promotion.id)).scalar()
    if max_id is None or max_id < PROMOTION_START_ID - 1:
        return PROMOTION_START_ID
    return max_id + 1

def get_next_promotion_target_id(db: Session) -> int:
    """获取下一个促销规则 ID（6001 起步）"""
    max_id = db.query(func.max(PromotionTarget.id)).scalar()
    if max_id is None or max_id < PROMOTION_TARGET_START_ID - 1:
        return PROMOTION_TARGET_START_ID
    return max_id + 1

def get_active_promotion_targets(db: Session) -> List[PromotionTarget]:
    """
    获取当前所有有效且处于生效时间窗口内的促销规则
    """
    now = datetime.datetime.utcnow()
    return db.query(PromotionTarget).join(Promotion).filter(
        Promotion.is_active == True,
        Promotion.is_deleted == False,
        Promotion.start_time <= now,
        Promotion.end_time >= now
    ).all()

def get_active_promotions_summary(db: Session) -> List[Dict[str, Any]]:
    """
    获取当前生效活动简报（包含活动下所有规则的结构化描述，用于客户端横幅及首页微徽标）
    """
    now = datetime.datetime.utcnow()
    promotions = db.query(Promotion).filter(
        Promotion.is_active == True,
        Promotion.is_deleted == False,
        Promotion.start_time <= now,
        Promotion.end_time >= now
    ).all()

    results = []
    for p in promotions:
        rules = []
        highlights = []
        for t in (p.targets or []):
            scope_name = "全场商品"
            if t.target_scope == "ITEM_TYPE":
                if t.target_type == "STICKER":
                    scope_name = "手账贴纸"
                elif t.target_type == "CANVAS_SET":
                    scope_name = "背景画布"
            elif t.target_scope == "SERIES":
                s_name = None
                if t.target_type == "STICKER":
                    from ...models import StickerSeries
                    ser = db.query(StickerSeries).filter(StickerSeries.id == t.target_id).first()
                    if ser:
                        s_name = f"{ser.name}贴纸"
                elif t.target_type == "CANVAS_SET":
                    from ...models import CanvasSeries
                    ser = db.query(CanvasSeries).filter(CanvasSeries.id == t.target_id).first()
                    if ser:
                        s_name = f"{ser.name}画布"
                scope_name = s_name or f"指定系列#{t.target_id}"

            if t.fixed_price is not None:
                r_desc = f"{scope_name} 一口价 {t.fixed_price} 个蛋能量"
                rules.append(r_desc)
                highlights.append(f"{scope_name}{t.fixed_price}能量")
            elif t.discount_rate is not None:
                rate_val = round(t.discount_rate * 10, 1)
                rate_str = str(int(rate_val)) if rate_val.is_integer() else str(rate_val)
                r_desc = f"{scope_name} 全场 {rate_str} 折"
                rules.append(r_desc)
                highlights.append(f"{scope_name}{rate_str}折")


        results.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "rules_summary": rules,
            "highlight_text": " · ".join(highlights) if highlights else "限时特惠进行中",
            "start_time": p.start_time.isoformat() if p.start_time else None,
            "end_time": p.end_time.isoformat() if p.end_time else None
        })

    return results


def list_all_promotions(
    db: Session,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """获取所有未被软删除的促销活动列表（按创建时间倒序），支持分页"""
    query = db.query(Promotion).filter(Promotion.is_deleted == False).order_by(Promotion.id.desc())
    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def get_promotion_by_id(db: Session, promotion_id: int) -> Optional[Promotion]:
    return db.query(Promotion).filter(Promotion.id == promotion_id, Promotion.is_deleted == False).first()

def create_promotion(
    db: Session,
    name: str,
    description: Optional[str],
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    is_active: bool = True,
    targets_data: Optional[List[Dict[str, Any]]] = None
) -> Promotion:
    """创建新促销活动及规则"""
    promo_id = get_next_promotion_id(db)
    promotion = Promotion(
        id=promo_id,
        name=name,
        description=description,
        start_time=start_time,
        end_time=end_time,
        is_active=is_active,
        is_deleted=False,
        created_at=datetime.datetime.utcnow()
    )
    db.add(promotion)
    db.flush()

    if targets_data:
        for t_data in targets_data:
            target = PromotionTarget(
                id=get_next_promotion_target_id(db),
                promotion_id=promotion.id,
                target_scope=t_data.get("target_scope", "ALL"),
                target_type=t_data.get("target_type"),
                target_id=t_data.get("target_id"),
                discount_rate=t_data.get("discount_rate"),
                fixed_price=t_data.get("fixed_price"),
                created_at=datetime.datetime.utcnow()
            )
            db.add(target)
            db.flush()

    db.commit()
    db.refresh(promotion)
    return promotion

def update_promotion(
    db: Session,
    promotion_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    is_active: Optional[bool] = None,
    targets_data: Optional[List[Dict[str, Any]]] = None
) -> Optional[Promotion]:
    """更新促销活动基本信息及重新配置规则"""
    promotion = get_promotion_by_id(db, promotion_id)
    if not promotion:
        return None

    if name is not None:
        promotion.name = name
    if description is not None:
        promotion.description = description
    if start_time is not None:
        promotion.start_time = start_time
    if end_time is not None:
        promotion.end_time = end_time
    if is_active is not None:
        promotion.is_active = is_active

    if targets_data is not None:
        # 清理旧规则
        db.query(PromotionTarget).filter(PromotionTarget.promotion_id == promotion.id).delete()
        db.flush()
        # 重新插入新规则
        for t_data in targets_data:
            target = PromotionTarget(
                id=get_next_promotion_target_id(db),
                promotion_id=promotion.id,
                target_scope=t_data.get("target_scope", "ALL"),
                target_type=t_data.get("target_type"),
                target_id=t_data.get("target_id"),
                discount_rate=t_data.get("discount_rate"),
                fixed_price=t_data.get("fixed_price"),
                created_at=datetime.datetime.utcnow()
            )
            db.add(target)
            db.flush()

    db.commit()
    db.refresh(promotion)
    return promotion

def toggle_promotion_active(db: Session, promotion_id: int, is_active: bool) -> Optional[Promotion]:
    """快捷切换活动启用/停用状态"""
    promotion = get_promotion_by_id(db, promotion_id)
    if not promotion:
        return None
    promotion.is_active = is_active
    db.commit()
    db.refresh(promotion)
    return promotion

def delete_promotion(db: Session, promotion_id: int) -> bool:
    """软删除促销活动"""
    promotion = get_promotion_by_id(db, promotion_id)
    if not promotion:
        return False
    promotion.is_deleted = True
    promotion.is_active = False
    db.commit()
    return True
