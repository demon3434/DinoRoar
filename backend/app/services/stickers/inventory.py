"""
User sticker inventory and egg energy exchange services.
"""

from sqlalchemy.orm import Session
from ...models import User, StickerConfig
from ...schemas import StickerSyncPayload


def get_user_inventory(db: Session, user_id: int) -> User:
    """
    获取指定用户的贴纸库存与蛋能量 (包含空字段自愈兜底)
    规则：只为新建账号/空资产账号发放基础默认系列 (Series 1 / 3D恐龙) 的初始贴纸 (每款 1 张)，
    任何自定义导入/扩展贴纸系列初始库存均为 0，需要通过蛋能量在商城自主兑换。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    # 查询基础系列 (1 或 101) 的贴纸 ID 集合
    base_sticker_ids = set()
    base_stickers = db.query(StickerConfig.id).filter(
        (StickerConfig.series_id == 1) | (StickerConfig.series_id == 101),
        StickerConfig.is_active == True,
        StickerConfig.is_deleted == False
    ).order_by(StickerConfig.sort_order.asc()).all()

    if not base_stickers:
        from ...models import StickerSeries
        first_series = db.query(StickerSeries.id).filter(
            StickerSeries.is_active == True,
            StickerSeries.is_deleted == False
        ).order_by(StickerSeries.sort_order.asc()).first()
        if first_series:
            base_stickers = db.query(StickerConfig.id).filter(
                StickerConfig.series_id == first_series.id,
                StickerConfig.is_active == True,
                StickerConfig.is_deleted == False
            ).order_by(StickerConfig.sort_order.asc()).all()

    if base_stickers:
        base_sticker_ids = {st.id for st in base_stickers}

    if not user.sticker_inventory or len(user.sticker_inventory.strip()) == 0:
        if user.egg_energy == 0:
            user.egg_energy = 100
        if base_sticker_ids:
            user.sticker_inventory = ",".join([f"{sid}:1" for sid in sorted(base_sticker_ids)])
        else:
            user.sticker_inventory = ""
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # 清理旧逻辑错误给自定义非基础系列填充的 999 假数据
        raw_inv = user.sticker_inventory.strip()
        parts = raw_inv.split(',')
        cleaned_parts = []
        changed = False

        for item in parts:
            if ':' in item:
                try:
                    sid_str, count_str = item.split(':')
                    sid = int(sid_str)
                    count = int(count_str)
                    # 如果不是基础系列的贴纸，但数量却是旧 bug 赋予的 999，将其清理掉（恢复为未兑换 0 库存）
                    if sid not in base_sticker_ids and count == 999:
                        changed = True
                        continue
                    cleaned_parts.append(f"{sid}:{count}")
                except ValueError:
                    continue

        if changed:
            user.sticker_inventory = ",".join(cleaned_parts)
            db.add(user)
            db.commit()
            db.refresh(user)

    return user


def update_user_inventory(db: Session, user_id: int, payload: StickerSyncPayload) -> User:
    """
    覆写更新用户的贴纸库存与蛋能量数据
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    user.sticker_inventory = payload.sticker_inventory
    user.egg_energy = payload.egg_energy

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def exchange_sticker_transaction(db: Session, user_id: int, sticker_id: int) -> User:
    """
    服务端事务：强校验用户蛋能量并执行贴纸扣除和入库
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户未找到")

    sticker = db.query(StickerConfig).filter(
        StickerConfig.id == sticker_id,
        StickerConfig.is_active == True
    ).first()
    if not sticker:
        raise ValueError("贴纸未找到或已停用")

    if user.egg_energy < sticker.exchange_price:
        raise ValueError("蛋能量不足，兑换失败")

    # 扣减蛋能量
    user.egg_energy -= sticker.exchange_price

    # 累加贴纸库存
    inventory_dict = {}
    if user.sticker_inventory and len(user.sticker_inventory.strip()) > 0:
        for item in user.sticker_inventory.split(','):
            if ':' in item:
                parts = item.split(':')
                try:
                    inventory_dict[int(parts[0])] = int(parts[1])
                except ValueError:
                    continue

    inventory_dict[sticker_id] = inventory_dict.get(sticker_id, 0) + 1

    serialized = ",".join([f"{k}:{v}" for k, v in inventory_dict.items()])
    user.sticker_inventory = serialized

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_sticker_inventory(db: Session, user_id: int, new_inventory: str) -> User:
    """
    更新用户的贴纸持有量（支持手账装扮后的进销存扣减与资产存盘）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户未找到")
    user.sticker_inventory = new_inventory
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
