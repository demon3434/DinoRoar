import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .. import models

logger = logging.getLogger("DinoRoar.energy_service")


class InsufficientEnergyException(HTTPException):
    def __init__(self, current_energy: int, required_energy: int):
        super().__init__(
            status_code=400,
            detail=f"蛋能量不足！当前余额: {current_energy}，需要: {required_energy}"
        )


class EnergyEngineService:
    """
    通用蛋能量核心领域服务与原子事务引擎
    所有蛋能量变动必须通过本服务执行，100% 服务端权威计算并入库
    """

    @staticmethod
    def apply_transaction(
        db: Session,
        user_id: int,
        event_type_id: int,
        change_amount: int,
        target_type_id: int,
        target_id: int,
        request_uuid: str,
        commit: bool = True
    ) -> models.EggEnergyTransaction:
        """
        原子执行一笔蛋能量变动事务
        :param db: SQLAlchemy Session
        :param user_id: 用户ID
        :param event_type_id: 行为事件类型ID (如 101 签到, 201 日记奖励, 301 商城兑换)
        :param change_amount: 变动数量 (正数获取，负数扣除)
        :param target_type_id: 目标实体类型ID (如 1 商品, 2 签到, 3 日记, 4 奖品)
        :param target_id: 目标业务表的整型自增 ID
        :param request_uuid: 客户端生成的幂等唯一键
        :param commit: 是否在本方法内直接 commit
        """
        # 1. 幂等性校验：如果已有相同 request_uuid 的流水，直接返回该流水（防止网络重试导致重复扣/送）
        existing_tx = db.query(models.EggEnergyTransaction).filter(
            models.EggEnergyTransaction.request_uuid == request_uuid
        ).first()
        if existing_tx:
            logger.info(f"EnergyEngine: Duplicate request_uuid={request_uuid} intercepted. Returning existing tx={existing_tx.id}.")
            return existing_tx

        # 2. 查询用户并校验余额
        user = db.query(models.User).filter(models.User.id == user_id).with_for_update().first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        current_energy = user.egg_energy or 0
        new_balance = current_energy + change_amount

        if change_amount < 0 and new_balance < 0:
            raise InsufficientEnergyException(
                current_energy=current_energy,
                required_energy=abs(change_amount)
            )

        # 3. 验证事件维度
        event_type = db.query(models.EggEnergyEventType).filter(
            models.EggEnergyEventType.event_type_id == event_type_id
        ).first()
        if not event_type:
            raise HTTPException(status_code=400, detail=f"未知的能量事件类型ID: {event_type_id}")

        # 4. 插入流水事实表
        tx = models.EggEnergyTransaction(
            user_id=user_id,
            event_type_id=event_type_id,
            change_amount=change_amount,
            balance_after=new_balance,
            target_type_id=target_type_id,
            target_id=target_id,
            request_uuid=request_uuid
        )
        db.add(tx)

        # 5. 更新用户快照余额
        user.egg_energy = new_balance
        db.add(user)

        if commit:
            db.commit()
            db.refresh(tx)
            logger.info(f"EnergyEngine: Applied tx={tx.id} for user={user_id}, amount={change_amount}, new_balance={new_balance}.")

        return tx

    @staticmethod
    def resolve_transaction_asset(db: Session, tx: models.EggEnergyTransaction) -> Dict[str, Any]:
        """
        动态物化解析器：依据 target_type_id 和 target_id 解析流水类型大类主干、附属业务明细与图片
        """
        target_type = db.query(models.EggEnergyTargetType).filter(
            models.EggEnergyTargetType.target_type_id == tx.target_type_id
        ).first()

        event_type = tx.event_type
        event_name = event_type.display_name if event_type else "能量变动"
        direction = event_type.direction if event_type else ("EARN" if tx.change_amount > 0 else "SPEND")

        badge_label = target_type.badge_label if target_type else "资产明细"
        title = event_name
        subtitle = ""
        type_icon = "/static/icons/ic_egg_cracked.png" if tx.change_amount > 0 else "/static/icons/ic_shop.png"
        image_url = None
        theme_color = "#10B981" if tx.change_amount > 0 else "#F59E0B"
        detail_info = {}

        if tx.target_type_id == 1:  # SHOP_ITEM
            title = "手账商城兑换"
            type_icon = "/static/icons/ic_shop.png"
            theme_color = "#F59E0B"
            direction = "SPEND"
            shop_item = db.query(models.ShopItem).filter(models.ShopItem.id == tx.target_id).first()
            if shop_item:
                if shop_item.item_type == "STICKER":
                    sticker = db.query(models.StickerConfig).filter(models.StickerConfig.id == shop_item.target_id).first()
                    if sticker:
                        series = db.query(models.StickerSeries).filter(models.StickerSeries.id == sticker.series_id).first() if sticker.series_id else None
                        series_name = series.name if series else "经典贴纸"
                        subtitle = f"🛒 兑换商品: 贴纸 · {series_name} · {sticker.name}"
                        image_url = sticker.image_url
                        badge_label = "贴纸商品"
                        detail_info = {
                            "item_type": "STICKER",
                            "series_name": series_name,
                            "name": sticker.name,
                            "image_url": sticker.image_url,
                            "original_price": shop_item.original_price,
                            "paid_price": abs(tx.change_amount),
                            "target_id": sticker.id
                        }
                elif shop_item.item_type == "CANVAS_SET":
                    cset = db.query(models.CanvasSet).filter(models.CanvasSet.id == shop_item.target_id).first()
                    if cset:
                        cseries = db.query(models.CanvasSeries).filter(models.CanvasSeries.id == cset.series_id).first() if cset.series_id else None
                        series_name = cseries.name if cseries else "背景画布"
                        subtitle = f"🎨 兑换商品: 画布 · {series_name} · {cset.name}"
                        badge_label = "画布商品"
                        theme_color = "#8B5CF6"
                        
                        instances = db.query(models.CanvasInstance).filter(
                            models.CanvasInstance.canvas_set_id == cset.id,
                            models.CanvasInstance.is_deleted == False
                        ).all()
                        inst_map = {inst.aspect_ratio: inst for inst in instances}
                        chosen_inst = None
                        for ratio in ["16:9", "4:3", "1:1", "2:1"]:
                            if ratio in inst_map:
                                chosen_inst = inst_map[ratio]
                                break
                        if not chosen_inst and instances:
                            chosen_inst = instances[0]

                        image_url = chosen_inst.image_url if chosen_inst else None
                        aspect_ratio = chosen_inst.aspect_ratio if chosen_inst else "16:9"
                        detail_info = {
                            "item_type": "CANVAS_SET",
                            "series_name": series_name,
                            "name": cset.name,
                            "image_url": image_url,
                            "aspect_ratio": aspect_ratio,
                            "original_price": shop_item.original_price,
                            "paid_price": abs(tx.change_amount),
                            "target_id": cset.id
                        }
            else:
                subtitle = f"🛒 兑换商品 (ID #{tx.target_id})"

        elif tx.target_type_id == 2:  # CHECK_IN
            title = "每日敲蛋签到"
            type_icon = None
            direction = "EARN"
            checkin = db.query(models.CheckInRecord).filter(models.CheckInRecord.id == tx.target_id).first()
            if checkin:
                crit_text = " (暴击! 💥)" if checkin.is_crit else ""
                subtitle = f"✨ 连续签到第 {checkin.streak_days} 天{crit_text} · 获得 {checkin.energy_reward} 能量"
                badge_label = "每日签到"
                image_url = None
                theme_color = "#EF4444" if checkin.is_crit else "#10B981"
                detail_info = {
                    "check_in_date": checkin.check_in_date,
                    "streak_days": checkin.streak_days,
                    "is_crit": checkin.is_crit,
                    "base_reward": checkin.energy_reward,
                    "streak_bonus": checkin.streak_bonus
                }
            else:
                subtitle = "✨ 每日签到获得蛋能量"

        elif tx.target_type_id == 3:  # LOG
            title = "手账日记奖励"
            type_icon = None
            direction = "EARN"
            theme_color = "#10B981"
            badge_label = "手账日记"
            log = db.query(models.Log).filter(models.Log.id == tx.target_id).first()
            if log:
                dino = db.query(models.DinoConfig).filter(models.DinoConfig.id == log.mood_dino_id).first()
                dino_name = dino.name if dino else "心情恐龙"
                diary_title = log.title.strip() if (log.title and log.title.strip()) else f"{log.incident_date.strftime('%Y-%m-%d') if log.incident_date else ''} 手账"
                subtitle = f"📖 关联日记: 《{diary_title}》 · {dino_name}"
                if dino and dino.image_url:
                    image_url = dino.image_url if dino.image_url.startswith("/") else f"/static/images/dinosaurs/{dino.image_url}"
                else:
                    image_url = None

                detail_info = {
                    "diary_uuid": log.uuid,
                    "mood_id": log.mood_dino_id,
                    "mood_name": dino_name,
                    "title": diary_title,
                    "incident_date": log.incident_date.strftime("%Y-%m-%d") if log.incident_date else "",
                    "media_count": len(log.attachments) if log.attachments else 0
                }
            else:
                subtitle = "📖 记录生活手账获得蛋能量"

        elif tx.target_type_id == 4:  # PRIZE
            title = "活动神秘宝箱"
            type_icon = None
            subtitle = f"🎉 获得活动奖励 #{tx.target_id}"
            badge_label = "活动奖品"
            image_url = None
            theme_color = "#EC4899"
            direction = "EARN"
            detail_info = {"prize_id": tx.target_id}

        return {
            "title": title,
            "subtitle": subtitle,
            "badge_label": badge_label,
            "type_icon": type_icon,
            "image_url": image_url,
            "theme_color": theme_color,
            "direction": direction,
            "detail_info": detail_info
        }


    @staticmethod
    def get_user_transactions(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        filter_type: str = "all",
        month: Optional[str] = None,
        time_range: Optional[str] = "all"
    ) -> Dict[str, Any]:
        """
        分页查询用户的蛋能量变动账本，包含今日/本周/本月/上月统计、多维时间段与收支过滤
        """
        import datetime
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_month_str = now.strftime("%Y-%m")
        current_year_str = now.strftime("%Y")
        # 计算本周一的日期字符串
        week_start_date = (now.date() - datetime.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        
        # 计算上个月的年月字符串 (如 2026-07)
        first_day_of_current_month = now.date().replace(day=1)
        last_day_of_prev_month = first_day_of_current_month - datetime.timedelta(days=1)
        last_month_str = last_day_of_prev_month.strftime("%Y-%m")

        user = db.query(models.User).filter(models.User.id == user_id).first()
        current_balance = user.egg_energy if user else 0

        # 全量统计汇总 (当前用户)
        all_user_txs = db.query(models.EggEnergyTransaction).filter(
            models.EggEnergyTransaction.user_id == user_id
        ).all()

        today_income = 0
        today_expense = 0
        week_income = 0
        week_expense = 0
        month_total_income = 0
        month_total_expense = 0
        last_month_income = 0
        last_month_expense = 0
        year_income = 0
        year_expense = 0

        for t in all_user_txs:
            if not t.created_at:
                continue
            c_date = t.created_at.strftime("%Y-%m-%d")
            c_month = t.created_at.strftime("%Y-%m")
            c_year = t.created_at.strftime("%Y")

            # 今日统计
            if c_date == today_str:
                if t.change_amount > 0:
                    today_income += t.change_amount
                else:
                    today_expense += abs(t.change_amount)

            # 本周统计
            if c_date >= week_start_date:
                if t.change_amount > 0:
                    week_income += t.change_amount
                else:
                    week_expense += abs(t.change_amount)

            # 本月/指定月份统计
            target_month = month if month else current_month_str
            if c_month == target_month:
                if t.change_amount > 0:
                    month_total_income += t.change_amount
                else:
                    month_total_expense += abs(t.change_amount)

            # 上月统计
            if c_month == last_month_str:
                if t.change_amount > 0:
                    last_month_income += t.change_amount
                else:
                    last_month_expense += abs(t.change_amount)

            # 本年统计
            if c_year == current_year_str:
                if t.change_amount > 0:
                    year_income += t.change_amount
                else:
                    year_expense += abs(t.change_amount)

        month_net = month_total_income - month_total_expense

        summary = {
            "current_balance": current_balance,
            "today_income": today_income,
            "today_expense": today_expense,
            "week_income": week_income,
            "week_expense": week_expense,
            "month_total_income": month_total_income,
            "month_total_expense": month_total_expense,
            "month_net": month_net,
            "last_month_income": last_month_income,
            "last_month_expense": last_month_expense,
            "year_income": year_income,
            "year_expense": year_expense
        }

        # 列表查询过滤
        query = db.query(models.EggEnergyTransaction).filter(
            models.EggEnergyTransaction.user_id == user_id
        )

        if filter_type == "income":
            query = query.filter(models.EggEnergyTransaction.change_amount > 0)
        elif filter_type == "expense":
            query = query.filter(models.EggEnergyTransaction.change_amount < 0)

        # 时间维度过滤
        if month:
            # 指定月份优先
            query = query.filter(models.EggEnergyTransaction.created_at.like(f"{month}%"))
        elif time_range == "today":
            query = query.filter(models.EggEnergyTransaction.created_at.like(f"{today_str}%"))
        elif time_range == "week":
            query = query.filter(models.EggEnergyTransaction.created_at >= f"{week_start_date} 00:00:00")
        elif time_range == "month":
            query = query.filter(models.EggEnergyTransaction.created_at.like(f"{current_month_str}%"))
        elif time_range == "last_month":
            query = query.filter(models.EggEnergyTransaction.created_at.like(f"{last_month_str}%"))
        elif time_range == "year":
            query = query.filter(models.EggEnergyTransaction.created_at.like(f"{current_year_str}%"))

        query = query.order_by(models.EggEnergyTransaction.created_at.desc(), models.EggEnergyTransaction.id.desc())

        total = query.count()
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        items = []
        for tx in records:
            event_type = tx.event_type
            event_name = event_type.display_name if event_type else "能量变动"
            asset_display = EnergyEngineService.resolve_transaction_asset(db, tx)
            created_str = tx.created_at.strftime("%Y-%m-%d %H:%M:%S") if tx.created_at else ""
            month_group = tx.created_at.strftime("%Y-%m") if tx.created_at else ""

            items.append({
                "id": tx.id,
                "event_type_id": tx.event_type_id,
                "event_name": event_name,
                "change_amount": tx.change_amount,
                "balance_after": tx.balance_after,
                "target_type_id": tx.target_type_id,
                "target_id": tx.target_id,
                "transaction_uuid": tx.request_uuid,
                "request_uuid": tx.request_uuid,
                "created_at": created_str,
                "month_group": month_group,
                "title": asset_display.get("title"),
                "subtitle": asset_display.get("subtitle", ""),
                "badge_label": asset_display.get("badge_label"),
                "type_icon": asset_display.get("type_icon", "default"),
                "image_url": asset_display.get("image_url"),
                "theme_color": asset_display.get("theme_color"),
                "direction": asset_display.get("direction", "EARN"),
                "detail_info": asset_display.get("detail_info"),
                "asset_display": asset_display
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": summary,
            "items": items
        }

    @staticmethod
    def get_admin_transactions(
        db: Session,
        user_id: Optional[int] = None,
        event_type_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        管理员全局对账审计流水查询
        """
        query = db.query(models.EggEnergyTransaction)

        if user_id:
            query = query.filter(models.EggEnergyTransaction.user_id == user_id)
        if event_type_id:
            query = query.filter(models.EggEnergyTransaction.event_type_id == event_type_id)
        if start_date:
            query = query.filter(models.EggEnergyTransaction.created_at >= f"{start_date} 00:00:00")
        if end_date:
            query = query.filter(models.EggEnergyTransaction.created_at <= f"{end_date} 23:59:59")

        # 统计汇总
        all_filtered = query.all()
        total_granted = sum(t.change_amount for t in all_filtered if t.change_amount > 0)
        total_consumed = sum(abs(t.change_amount) for t in all_filtered if t.change_amount < 0)
        net_circulation = total_granted - total_consumed

        total = query.count()
        offset = (page - 1) * page_size
        records = query.order_by(
            models.EggEnergyTransaction.created_at.desc(),
            models.EggEnergyTransaction.id.desc()
        ).offset(offset).limit(page_size).all()

        items = []
        for tx in records:
            event_type = tx.event_type
            event_name = event_type.display_name if event_type else "能量变动"
            asset_display = EnergyEngineService.resolve_transaction_asset(db, tx)
            user = tx.user
            username = user.username if user else f"User#{tx.user_id}"
            nickname = user.nickname if user else None

            created_str = tx.created_at.strftime("%Y-%m-%d %H:%M:%S") if tx.created_at else ""
            month_group = tx.created_at.strftime("%Y-%m") if tx.created_at else ""

            items.append({
                "id": tx.id,
                "user_id": tx.user_id,
                "username": username,
                "nickname": nickname,
                "event_type_id": tx.event_type_id,
                "event_name": event_name,
                "change_amount": tx.change_amount,
                "balance_after": tx.balance_after,
                "target_type_id": tx.target_type_id,
                "target_id": tx.target_id,
                "transaction_uuid": tx.request_uuid,
                "request_uuid": tx.request_uuid,
                "created_at": created_str,
                "month_group": month_group,
                "title": asset_display.get("title"),
                "subtitle": asset_display.get("subtitle", ""),
                "badge_label": asset_display.get("badge_label"),
                "type_icon": asset_display.get("type_icon", "default"),
                "image_url": asset_display.get("image_url"),
                "theme_color": asset_display.get("theme_color"),
                "direction": asset_display.get("direction", "EARN"),
                "detail_info": asset_display.get("detail_info"),
                "asset_display": asset_display
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_granted": total_granted,
            "total_consumed": total_consumed,
            "net_circulation": net_circulation,
            "items": items
        }


