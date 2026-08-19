import json
import random
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .. import models
from .energy_service import EnergyEngineService

logger = logging.getLogger("DinoRoar.checkin_service")


class CheckInService:
    """
    每日敲蛋签到业务服务
    """

    @staticmethod
    def get_today_str(target_date: Optional[date] = None) -> str:
        d = target_date or datetime.now().date()
        return d.strftime("%Y-%m-%d")

    @staticmethod
    def get_config(db: Session) -> models.CheckInConfig:
        config = db.query(models.CheckInConfig).first()
        if not config:
            config = models.CheckInConfig(
                id=1,
                base_min=5,
                base_max=15,
                crit_rate=0.15,
                crit_min=30,
                crit_max=66,
                streak_enabled=True,
                streak_rules_json='{"3": 5, "7": 20}'
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        return config

    @staticmethod
    def calculate_streak_days(db: Session, user_id: int, today_str: str) -> int:
        """
        推算用户截止今日的连续签到天数
        """
        today_date = datetime.strptime(today_str, "%Y-%m-%d").date()
        yesterday_str = (today_date - timedelta(days=1)).strftime("%Y-%m-%d")

        yesterday_record = db.query(models.CheckInRecord).filter(
            models.CheckInRecord.user_id == user_id,
            models.CheckInRecord.check_in_date == yesterday_str
        ).first()

        if yesterday_record:
            return yesterday_record.streak_days + 1
        return 1

    @staticmethod
    def roll_checkin_energy(config: models.CheckInConfig, streak_days: int) -> Tuple[int, int, bool, int]:
        """
        根据配置掷骰生成签到随机蛋能量与暴击结果
        :return: (total_reward, base_reward, is_crit, streak_bonus)
        """
        # 1. 暴击判断
        is_crit = random.random() < config.crit_rate
        if is_crit:
            base_min = min(config.crit_min, config.crit_max)
            base_max = max(config.crit_min, config.crit_max)
            base_reward = random.randint(base_min, base_max)
        else:
            base_min = min(config.base_min, config.base_max)
            base_max = max(config.base_min, config.base_max)
            base_reward = random.randint(base_min, base_max)

        # 2. 连续签到阶梯奖励
        streak_bonus = 0
        if config.streak_enabled and config.streak_rules_json:
            try:
                rules = json.loads(config.streak_rules_json)
                streak_bonus = int(rules.get(str(streak_days), 0))
            except Exception as e:
                logger.warning(f"Failed to parse streak_rules_json: {e}")

        total_reward = base_reward + streak_bonus
        return total_reward, base_reward, is_crit, streak_bonus

    @staticmethod
    def get_user_checkin_status(db: Session, user_id: int, target_date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        查询用户今日签到状态与最近 7 天签到历史
        """
        today_str = target_date_str or CheckInService.get_today_str()
        today_date = datetime.strptime(today_str, "%Y-%m-%d").date()

        # 今日签到记录
        today_record = db.query(models.CheckInRecord).filter(
            models.CheckInRecord.user_id == user_id,
            models.CheckInRecord.check_in_date == today_str
        ).first()

        has_checked_in = today_record is not None
        streak_days = today_record.streak_days if today_record else CheckInService.calculate_streak_days(db, user_id, today_str)

        # 最近 7 天足迹 (从 6 天前到今天)
        history = []
        for i in range(6, -1, -1):
            past_date = today_date - timedelta(days=i)
            past_date_str = past_date.strftime("%Y-%m-%d")
            record = db.query(models.CheckInRecord).filter(
                models.CheckInRecord.user_id == user_id,
                models.CheckInRecord.check_in_date == past_date_str
            ).first()

            history.append({
                "date": past_date_str,
                "day_of_week": past_date.weekday() + 1,  # 1=周一, 7=周日
                "checked_in": record is not None,
                "energy_reward": record.energy_reward if record else 0,
                "streak_bonus": record.streak_bonus if record else 0,
                "is_crit": record.is_crit if record else False
            })

        user = db.query(models.User).filter(models.User.id == user_id).first()
        current_energy = user.egg_energy if user else 0

        return {
            "has_checked_in_today": has_checked_in,
            "today_date": today_str,
            "streak_days": streak_days,
            "current_egg_energy": current_energy,
            "today_record": {
                "id": today_record.id,
                "energy_reward": today_record.energy_reward,
                "streak_bonus": today_record.streak_bonus,
                "is_crit": today_record.is_crit,
                "streak_days": today_record.streak_days,
                "created_at": today_record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } if today_record else None,
            "weekly_history": history
        }

    @staticmethod
    def perform_user_checkin(
        db: Session,
        user_id: int,
        request_uuid: str,
        target_date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行用户敲蛋签到
        """
        today_str = target_date_str or CheckInService.get_today_str()

        # 1. 检查今日是否已签到 (防止重复签到)
        existing_record = db.query(models.CheckInRecord).filter(
            models.CheckInRecord.user_id == user_id,
            models.CheckInRecord.check_in_date == today_str
        ).first()

        if existing_record:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            return {
                "success": True,
                "already_checked_in": True,
                "checkin_id": existing_record.id,
                "total_reward": existing_record.energy_reward + existing_record.streak_bonus,
                "base_reward": existing_record.energy_reward,
                "streak_bonus": existing_record.streak_bonus,
                "is_crit": existing_record.is_crit,
                "streak_days": existing_record.streak_days,
                "total_egg_energy": user.egg_energy if user else 0,
                "message": "今日已经完成敲蛋签到啦！"
            }

        # 2. 计算连续天数与随机奖励
        config = CheckInService.get_config(db)
        streak_days = CheckInService.calculate_streak_days(db, user_id, today_str)
        total_reward, base_reward, is_crit, streak_bonus = CheckInService.roll_checkin_energy(config, streak_days)

        # 3. 写入签到记录表
        checkin_record = models.CheckInRecord(
            user_id=user_id,
            check_in_date=today_str,
            energy_reward=base_reward,
            streak_bonus=streak_bonus,
            is_crit=is_crit,
            streak_days=streak_days
        )
        db.add(checkin_record)
        db.flush()  # 生成 checkin_record.id 用于 target_id 强整型关联

        # 4. 调用权威蛋能量引擎入库流水
        tx = EnergyEngineService.apply_transaction(
            db=db,
            user_id=user_id,
            event_type_id=101,  # 每日敲蛋签到
            change_amount=total_reward,
            target_type_id=2,    # CHECK_IN 实体
            target_id=checkin_record.id,  # 严格强类型整型主键
            request_uuid=request_uuid,
            commit=False
        )

        db.commit()
        db.refresh(checkin_record)

        msg = "💥 欧皇降临！触发大暴击！" if is_crit else "🎉 敲蛋成功！"
        if streak_bonus > 0:
            msg += f" 连续签到第 {streak_days} 天，额外获赠 {streak_bonus} 蛋能量！"

        return {
            "success": True,
            "already_checked_in": False,
            "checkin_id": checkin_record.id,
            "total_reward": total_reward,
            "base_reward": base_reward,
            "streak_bonus": streak_bonus,
            "is_crit": is_crit,
            "streak_days": streak_days,
            "total_egg_energy": tx.balance_after,
            "message": msg
        }
