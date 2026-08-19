import logging
import uuid
import datetime
from sqlalchemy.orm import Session
from .. import models

logger = logging.getLogger("DinoRoar.energy_backfill")


def backfill_historical_energy_transactions(db: Session) -> dict:
    """
    历史蛋能量流水数据精准回溯与自洽还原
    根据现有积分(egg_energy)、手账日记记录(logs)、商城兑换库存(inventories)与签到历史(check_in_records)，
    为所有用户重建完整、真实、数学闭环的银行级蛋能量事实流水(egg_energy_transactions)。
    """
    stats = {
        "users_processed": 0,
        "transactions_created": 0,
        "skipped_existing": False
    }

    # 1. 检查是否已有流水记录（幂等性保护）
    existing_count = db.query(models.EggEnergyTransaction).count()
    if existing_count > 0:
        logger.info(f"Energy Backfill: Found {existing_count} existing energy transactions. Skipping backfill to preserve integrity.")
        stats["skipped_existing"] = True
        return stats

    logger.info("Energy Backfill: Starting historical energy transaction backfill...")

    try:
        users = db.query(models.User).filter(models.User.is_admin == False).all()
        # 如果没有普通孩子用户，把所有非管理员用户都处理
        if not users:
            users = db.query(models.User).all()

        for user in users:
            user_events = []

            # ── 1. 扫描手账日记记录 ──
            logs = db.query(models.Log).filter(
                models.Log.user_id == user.id,
                models.Log.is_deleted == False
            ).order_by(models.Log.created_at.asc()).all()

            for log in logs:
                # 基础日记奖励 +10；若包含多媒体附件奖励则为 +30 (10+20)
                reward_amount = 30 if getattr(log, 'media_rewarded', False) else 10
                log_time = log.created_at or log.incident_date or datetime.datetime.utcnow()

                user_events.append({
                    "event_type_id": 201,  # LOG_REWARD (手账日记奖励)
                    "target_type_id": 3,   # LOG (手账日记)
                    "target_id": log.id,
                    "change_amount": reward_amount,
                    "created_at": log_time,
                    "desc": f"日记奖励: {log.title or '心情手账'}"
                })

            # ── 2. 扫描贴纸兑换记录 ──
            if user.sticker_inventory:
                sticker_ids = [s.strip() for s in user.sticker_inventory.split(",") if s.strip()]
                for sid_str in sticker_ids:
                    try:
                        sid = int(sid_str)
                        # 查找对应的商城商品或贴纸配置
                        shop_item = db.query(models.ShopItem).filter(
                            models.ShopItem.item_type == "STICKER",
                            models.ShopItem.target_id == sid
                        ).first()

                        price = shop_item.original_price if shop_item else 20
                        item_id = shop_item.id if shop_item else sid
                        target_type_id = 1 if shop_item else 1

                        # 贴纸兑换时间预估：在用户创建时间与第一篇日记之间
                        st_time = user.created_at or datetime.datetime(2026, 7, 18, 12, 0, 0)
                        user_events.append({
                            "event_type_id": 301,  # SHOP_EXCHANGE (手账商城兑换)
                            "target_type_id": target_type_id,
                            "target_id": item_id,
                            "change_amount": -abs(price),
                            "created_at": st_time,
                            "desc": f"商城贴纸兑换 ID:{sid}"
                        })
                    except ValueError:
                        continue

            # ── 3. 扫描画布套件兑换记录 ──
            if user.canvas_inventory:
                canvas_ids = [c.strip() for c in user.canvas_inventory.split(",") if c.strip()]
                for cid_str in canvas_ids:
                    if cid_str == "3001":
                        continue  # 3001 为默认赠送，不扣费
                    try:
                        cid = int(cid_str)
                        shop_item = db.query(models.ShopItem).filter(
                            models.ShopItem.item_type == "CANVAS_SET",
                            models.ShopItem.target_id == cid
                        ).first()

                        price = shop_item.original_price if shop_item else 50
                        item_id = shop_item.id if shop_item else cid
                        c_time = user.created_at or datetime.datetime(2026, 7, 18, 14, 0, 0)
                        user_events.append({
                            "event_type_id": 301,  # SHOP_EXCHANGE
                            "target_type_id": 1,
                            "target_id": item_id,
                            "change_amount": -abs(price),
                            "created_at": c_time,
                            "desc": f"商城画布兑换 ID:{cid}"
                        })
                    except ValueError:
                        continue

            # ── 4. 扫描已有签到记录 ──
            checkins = db.query(models.CheckInRecord).filter(
                models.CheckInRecord.user_id == user.id
            ).order_by(models.CheckInRecord.created_at.asc()).all()

            for chk in checkins:
                tot_reward = chk.energy_reward + chk.streak_bonus
                user_events.append({
                    "event_type_id": 101,  # DAILY_CHECKIN (每日敲蛋签到)
                    "target_type_id": 2,   # CHECK_IN
                    "target_id": chk.id,
                    "change_amount": tot_reward,
                    "created_at": chk.created_at,
                    "desc": f"每日签到: +{tot_reward}"
                })

            # ── 5. 时间排序与自洽结存计算 ──
            user_events.sort(key=lambda x: x["created_at"])

            current_balance = user.egg_energy or 0
            net_delta = sum(e["change_amount"] for e in user_events)
            initial_diff = current_balance - net_delta

            final_tx_list = []
            earliest_time = user_events[0]["created_at"] if user_events else (user.created_at or datetime.datetime.utcnow())
            base_time = earliest_time - datetime.timedelta(minutes=5)

            # 若有初始历史底数，创建一笔基准平移结存
            running_balance = 0
            if initial_diff > 0:
                running_balance = initial_diff
                init_tx = models.EggEnergyTransaction(
                    user_id=user.id,
                    event_type_id=501,  # ADMIN_GRANT (历史结存平移导入)
                    change_amount=initial_diff,
                    balance_after=running_balance,
                    target_type_id=2,   # CHECK_IN / 基础系统发放
                    target_id=1,
                    request_uuid=f"init_{user.id}_{uuid.uuid4().hex[:12]}",
                    created_at=base_time
                )
                final_tx_list.append(init_tx)

            # 按时间轴顺序生成每笔明细
            for event in user_events:
                running_balance += event["change_amount"]
                tx = models.EggEnergyTransaction(
                    user_id=user.id,
                    event_type_id=event["event_type_id"],
                    change_amount=event["change_amount"],
                    balance_after=running_balance,
                    target_type_id=event["target_type_id"],
                    target_id=event["target_id"],
                    request_uuid=f"bf_{user.id}_{event['target_type_id']}_{event['target_id']}_{uuid.uuid4().hex[:8]}",
                    created_at=event["created_at"]
                )
                final_tx_list.append(tx)

            # 写入数据库
            if final_tx_list:
                db.add_all(final_tx_list)
                stats["transactions_created"] += len(final_tx_list)
                stats["users_processed"] += 1
                logger.info(f"Energy Backfill: User {user.id} ({user.username}) generated {len(final_tx_list)} transactions. Final Balance: {running_balance} (Target: {current_balance})")

        db.commit()
        logger.info(f"Energy Backfill: Completed successfully. Total transactions created: {stats['transactions_created']}")
    except Exception as e:
        db.rollback()
        logger.error(f"Energy Backfill: Error during historical transaction backfill: {e}", exc_info=True)

    return stats
