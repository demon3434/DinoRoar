"""
DinoRoar 历史日记多媒体附件补发流水对账与回填工具
用于扫描并修复因附件上传时未通过 EnergyEngineService 记账而缺失的 +20 蛋能量流水
"""

import sys
import os
import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal, engine
from app import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("repair_media_energy")


from app.services.energy_repair import repair_missing_media_reward_transactions

if __name__ == "__main__":
    db = SessionLocal()
    try:
        dry_run = "--dry-run" in sys.argv
        print(f"Running repair_missing_media_reward_transactions (dry_run={dry_run})...")
        res = repair_missing_media_reward_transactions(db, dry_run=dry_run)
        print("Repair Result:", res)
    finally:
        db.close()

