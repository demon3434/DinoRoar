"""
CRUD and management operations for sticker series and sticker configurations.
"""

from sqlalchemy.orm import Session
from ...models import StickerSeries, StickerConfig


def get_nested_stickers_config(db: Session):
    """
    拉取按系列分类的嵌套贴纸列表，过滤掉软删除记录，按 sort_order 升序排序
    """
    series_list = db.query(StickerSeries).filter(
        StickerSeries.is_deleted == False
    ).order_by(StickerSeries.sort_order.asc()).all()

    results = []
    for s in series_list:
        stickers = db.query(StickerConfig).filter(
            StickerConfig.series_id == s.id,
            StickerConfig.is_deleted == False
        ).order_by(StickerConfig.sort_order.asc()).all()
        s.stickers = stickers
        results.append(s)
    return results


def reorder_stickers_in_series(db: Session, series_id: int, current_sticker_id: int, desired_sort_order: int):
    """
    顺位插入重排逻辑：
    1. 取出该系列下除 current_sticker_id 以外所有未删除贴纸（按原顺序排序）。
    2. 根据 desired_sort_order (1-based) 计算插入位置 insert_idx。
    3. 插入当前贴纸。
    4. 统一将所有贴纸重新赋值为连续递增序号 1, 2, 3...
    """
    other_stickers = db.query(StickerConfig).filter(
        StickerConfig.series_id == series_id,
        StickerConfig.id != current_sticker_id,
        StickerConfig.is_deleted == False
    ).order_by(StickerConfig.sort_order.asc(), StickerConfig.id.asc()).all()

    current_sticker = db.query(StickerConfig).filter(StickerConfig.id == current_sticker_id).first()
    if not current_sticker:
        return

    insert_idx = max(0, min(desired_sort_order - 1, len(other_stickers)))
    other_stickers.insert(insert_idx, current_sticker)

    for idx, s in enumerate(other_stickers, start=1):
        s.sort_order = idx


def sort_stickers(db: Session, sticker_ids: list):
    """
    批量更新一系列贴纸的 sort_order 顺序 (1..N)
    """
    for index, s_id in enumerate(sticker_ids, start=1):
        db.query(StickerConfig).filter(
            StickerConfig.id == s_id
        ).update({StickerConfig.sort_order: index})
    db.commit()


def rename_sticker_series(db: Session, series_id: int, new_name: str):
    """
    重命名分类系列
    """
    series = db.query(StickerSeries).filter(
        StickerSeries.id == series_id,
        StickerSeries.is_deleted == False
    ).first()
    if not series:
        raise ValueError("指定分类系列不存在")
    series.name = new_name
    db.commit()
    return series


def toggle_sticker_series_active(db: Session, series_id: int, is_active: bool):
    """
    切换分类系列的停启用状态
    """
    series = db.query(StickerSeries).filter(
        StickerSeries.id == series_id,
        StickerSeries.is_deleted == False
    ).first()
    if not series:
        raise ValueError("指定分类系列不存在")
    series.is_active = is_active
    db.commit()
    return series


def soft_delete_sticker(db: Session, sticker_id: int):
    """
    逻辑软删除指定贴纸并紧凑重排该系列内剩余贴纸
    """
    sticker = db.query(StickerConfig).filter(
        StickerConfig.id == sticker_id,
        StickerConfig.is_deleted == False
    ).first()
    if not sticker:
        raise ValueError("指定贴纸不存在或已被删除")
    sticker.is_deleted = True

    # 紧凑重排剩余贴纸 (1..N)
    remaining = db.query(StickerConfig).filter(
        StickerConfig.series_id == sticker.series_id,
        StickerConfig.id != sticker_id,
        StickerConfig.is_deleted == False
    ).order_by(StickerConfig.sort_order.asc(), StickerConfig.id.asc()).all()
    for idx, s in enumerate(remaining, start=1):
        s.sort_order = idx

    db.commit()
    return sticker


def soft_delete_sticker_series(db: Session, series_id: int):
    """
    逻辑软删除分类系列，若有未删除贴纸则强拦截抛异常
    """
    series = db.query(StickerSeries).filter(
        StickerSeries.id == series_id,
        StickerSeries.is_deleted == False
    ).first()
    if not series:
        raise ValueError("指定分类系列不存在或已被删除")

    active_count = db.query(StickerConfig).filter(
        StickerConfig.series_id == series_id,
        StickerConfig.is_deleted == False
    ).count()
    if active_count > 0:
        raise ValueError("该系列下还有未删除的贴纸，请先删除该系列下的所有贴纸")

    series.is_deleted = True
    db.commit()
    return series


def sort_sticker_series(db: Session, series_ids: list):
    """
    批量更新系列分类文件夹之间的 sort_order 顺序 (1..N)
    """
    for index, s_id in enumerate(series_ids, start=1):
        db.query(StickerSeries).filter(
            StickerSeries.id == s_id
        ).update({StickerSeries.sort_order: index})
    db.commit()


def update_sticker(
    db: Session,
    sticker_id: int,
    name: str,
    exchange_price: int,
    sort_order: int,
    description: str = None,
    image_url: str = None
):
    """
    修改单个贴纸的配置参数与图片（支持顺位插入重排）
    """
    sticker = db.query(StickerConfig).filter(
        StickerConfig.id == sticker_id,
        StickerConfig.is_deleted == False
    ).first()
    if not sticker:
        raise ValueError("指定贴纸配置不存在或已被删除")
    sticker.name = name
    sticker.exchange_price = exchange_price
    if description is not None:
        sticker.description = description
    if image_url:
        sticker.image_url = image_url

    # 执行顺位重排
    reorder_stickers_in_series(db, sticker.series_id, sticker.id, sort_order)
    db.commit()
    db.refresh(sticker)
    return sticker


def cascade_delete_series(db: Session, series_id: int) -> bool:
    """
    级联删除贴纸系列及其下的所有贴纸
    """
    series = db.query(StickerSeries).filter(StickerSeries.id == series_id).first()
    if not series:
        return False
    series.is_deleted = True
    db.query(StickerConfig).filter(StickerConfig.series_id == series_id).update(
        {StickerConfig.is_deleted: True}
    )
    db.commit()
    return True


def batch_delete_stickers(db: Session, sticker_ids: list) -> int:
    """
    批量软删除贴纸项并紧凑重排涉及系列的剩余贴纸
    """
    stickers = db.query(StickerConfig).filter(
        StickerConfig.id.in_(sticker_ids),
        StickerConfig.is_deleted == False
    ).all()
    if not stickers:
        return 0

    affected_series_ids = set()
    deleted_count = 0
    for st in stickers:
        st.is_deleted = True
        affected_series_ids.add(st.series_id)
        deleted_count += 1

    # 对所有受影响的系列分别做紧凑重排
    for s_id in affected_series_ids:
        remaining = db.query(StickerConfig).filter(
            StickerConfig.series_id == s_id,
            StickerConfig.is_deleted == False
        ).order_by(StickerConfig.sort_order.asc(), StickerConfig.id.asc()).all()
        for idx, s in enumerate(remaining, start=1):
            s.sort_order = idx

    db.commit()
    return deleted_count
