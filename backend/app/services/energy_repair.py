import datetime
import logging
from sqlalchemy.orm import Session
from .. import models

logger = logging.getLogger("DinoRoar.energy_repair")


def repair_missing_media_reward_transactions(db: Session, dry_run: bool = False) -> dict:
    """
    扫描所有 media_rewarded=True 的日记，检查是否缺失配图加成流水事实记录并自愈对齐
    """
    stats = {
        "scanned_logs": 0,
        "missing_rewards_found": 0,
        "transactions_created": 0,
        "users_affected": set()
    }

    try:
        users = db.query(models.User).filter(models.User.is_admin == False).all()
        if not users:
            users = db.query(models.User).all()

        for user in users:
            user_txs = db.query(models.EggEnergyTransaction).filter(
                models.EggEnergyTransaction.user_id == user.id
            ).order_by(models.EggEnergyTransaction.id.asc()).all()

            total_tx_amount = sum(t.change_amount for t in user_txs)
            current_user_balance = user.egg_energy or 0

            media_logs = db.query(models.Log).filter(
                models.Log.user_id == user.id,
                models.Log.is_deleted == False,
                models.Log.media_rewarded == True
            ).all()

            for log in media_logs:
                stats["scanned_logs"] += 1

                has_media_reward_tx = db.query(models.EggEnergyTransaction).filter(
                    models.EggEnergyTransaction.user_id == user.id,
                    models.EggEnergyTransaction.target_type_id == 3,
                    models.EggEnergyTransaction.target_id == log.id,
                    models.EggEnergyTransaction.request_uuid == f"log_media_reward_{log.uuid}"
                ).first()

                has_single_30_tx = db.query(models.EggEnergyTransaction).filter(
                    models.EggEnergyTransaction.user_id == user.id,
                    models.EggEnergyTransaction.target_type_id == 3,
                    models.EggEnergyTransaction.target_id == log.id,
                    models.EggEnergyTransaction.change_amount == 30
                ).first()

                if not has_media_reward_tx and not has_single_30_tx:
                    stats["missing_rewards_found"] += 1
                    stats["users_affected"].add(user.username)

                    att = db.query(models.Attachment).filter(
                        models.Attachment.log_uuid == log.uuid
                    ).order_by(models.Attachment.created_at.asc()).first()

                    tx_time = att.created_at if (att and att.created_at) else (log.updated_at or log.created_at or datetime.datetime.utcnow())

                    logger.info(f"Energy Repair: Missing media reward tx found: User={user.username} (ID={user.id}), Log={log.title} (UUID={log.uuid}, LogID={log.id})")

                    if not dry_run:
                        diff = current_user_balance - total_tx_amount
                        needs_balance_add = diff < 20

                        if needs_balance_add:
                            user.egg_energy = current_user_balance + 20
                            db.add(user)
                            new_balance = user.egg_energy
                            current_user_balance = new_balance
                        else:
                            new_balance = current_user_balance

                        new_tx = models.EggEnergyTransaction(
                            user_id=user.id,
                            event_type_id=201, # LOG_REWARD
                            change_amount=20,
                            balance_after=new_balance,
                            target_type_id=3,  # LOG
                            target_id=log.id,
                            request_uuid=f"log_media_reward_{log.uuid}",
                            created_at=tx_time
                        )
                        db.add(new_tx)
                        db.commit()
                        total_tx_amount += 20

                        stats["transactions_created"] += 1
                        logger.info(f"Energy Repair: Created backfill tx: LogID={log.id}, Amount=+20, BalanceAfter={new_balance}, UUID=log_media_reward_{log.uuid}")

        stats["users_affected"] = list(stats["users_affected"])
    except Exception as e:
        logger.error(f"Energy Repair: Error during execution: {e}")

    return stats


def fix_timezone_of_historical_transactions(db: Session) -> dict:
    """
    历史流水 UTC 时区时差自愈修复：
    将因之前使用 utcnow 导致比北京时间慢 8 小时的日记与签到流水校正为北京时间
    """
    fixed_count = 0
    try:
        # 1. 修复日记基础奖励流水：对齐到日记的 incident_date (发生时间)
        log_txs = db.query(models.EggEnergyTransaction).filter(
            models.EggEnergyTransaction.target_type_id == 3,
            models.EggEnergyTransaction.request_uuid.like("log_reward_%")
        ).all()

        for tx in log_txs:
            log = db.query(models.Log).filter(models.Log.id == tx.target_id).first()
            if log and log.incident_date:
                # 如果流水时间比 incident_date 早约 8 小时（7 到 9 小时之间）
                time_diff = (log.incident_date - tx.created_at).total_seconds()
                if 25000 <= time_diff <= 29000:  # 约 7 ~ 8.05 小时
                    old_time = tx.created_at
                    tx.created_at = log.incident_date
                    fixed_count += 1
                    logger.info(f"Timezone Repair: Fixed log reward tx={tx.id} from {old_time} to {tx.created_at}")

        # 2. 修复同一时期跟随产生的签到流水
        checkin_txs = db.query(models.EggEnergyTransaction).filter(
            models.EggEnergyTransaction.target_type_id == 2
        ).all()

        for ctx in checkin_txs:
            # 如果创建时间小时数在 0 ~ 15 之间，且对应 checkin_date 是当天
            checkin = db.query(models.CheckInRecord).filter(models.CheckInRecord.id == ctx.target_id).first()
            if checkin:
                # 检查是否存在同时段被修正的日记流水 (5 分钟内)
                # 或者如果 checkin.created_at 包含 8 小时偏差
                # 通过检查与当前小时数推断：若时间是凌晨 01:00~07:00，但打卡日期是今天
                if ctx.created_at.hour < 8 and ctx.created_at.strftime("%Y-%m-%d") == checkin.check_in_date:
                    # 检查是否已有修正标记或通过加 8 小时校正
                    ctx.created_at = ctx.created_at + datetime.timedelta(hours=8)
                    checkin.created_at = ctx.created_at
                    fixed_count += 1
                    logger.info(f"Timezone Repair: Fixed checkin tx={ctx.id} to {ctx.created_at}")

        if fixed_count > 0:
            db.commit()
            logger.info(f"Timezone Repair: Total {fixed_count} transactions aligned to Beijing Time.")
    except Exception as e:
        logger.error(f"Timezone Repair: Error during execution: {e}")

    return {"fixed_count": fixed_count}
