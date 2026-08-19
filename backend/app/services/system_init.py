import os
import shutil
import logging
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import engine, Base
from ..config import settings
from .. import models

logger = logging.getLogger("DinoRoar.system_init")


def seed_initial_dino_configs(db: Session):
    """
    初始化默认心情恐龙配置
    """
    dino_exists = db.query(models.DinoConfig).first()
    if not dino_exists:
        logger.info("Database: Seeding initial dinosaur configs...")
        initial_dinos = [
            models.DinoConfig(id=1, legacy_key="Triceratops", name="快乐三角龙", mood_label="😊 开心", mood_tip="快乐是会传染的，今天也要开心哦！", image_url="mood_triceratops.png", mood_score=10, sort_order=1, is_active=True),
            models.DinoConfig(id=2, legacy_key="Pterodactyl_happy", name="冲天翼手龙", mood_label="🤩 兴奋", mood_tip="把快乐写进日记，让它飞得更高吧！", image_url="mood_pterodactyl_happy.png", mood_score=9, sort_order=2, is_active=True),
            models.DinoConfig(id=3, legacy_key="T-Rex_proud", name="挺胸霸王龙", mood_label="😎 得意", mood_tip="你太棒了！今天也是值得自豪的一天！", image_url="mood_t_rex_proud.png", mood_score=8, sort_order=3, is_active=True),
            models.DinoConfig(id=4, legacy_key="Brachiosaurus", name="大眼睛雷龙", mood_label="🌟 期待", mood_tip="未来闪闪发光，让我们一起期待明天吧！", image_url="mood_brachiosaurus.png", mood_score=7, sort_order=4, is_active=True),
            models.DinoConfig(id=5, legacy_key="Stegosaurus", name="呆呆剑龙", mood_label="😮 惊讶", mood_tip="哇，今天发生了意想不到的奇妙事情呢！", image_url="mood_stegosaurus.png", mood_score=6, sort_order=5, is_active=True),
            models.DinoConfig(id=6, legacy_key="Velociraptor", name="佛系迅猛龙", mood_label="😐 一般", mood_tip="平静的一天也很美好，休息一下吧！", image_url="mood_velociraptor.png", mood_score=5, sort_order=6, is_active=True),
            models.DinoConfig(id=7, legacy_key="Ankylosaurus_scared", name="缩壳甲龙", mood_label="😰 紧张", mood_tip="别怕，缩进壳里也是保护自己的好办法，你很安全！", image_url="mood_ankylosaurus_scared.png", mood_score=4, sort_order=7, is_active=True),
            models.DinoConfig(id=8, legacy_key="Pachycephalosaurus", name="叹气肿头龙", mood_label="🍃 遗憾", mood_tip="没关系，每一次小小的遗憾都是成长的足迹。", image_url="mood_pachycephalosaurus.png", mood_score=3, sort_order=8, is_active=True),
            models.DinoConfig(id=9, legacy_key="Parasaurolophus_regret", name="耷拉角副栉龙", mood_label="😣 后悔", mood_tip="别太自责，过去的事就让它过去，下次会更好！", image_url="mood_parasaurolophus_regret.png", mood_score=2, sort_order=9, is_active=True),
            models.DinoConfig(id=10, legacy_key="Spinosaurus", name="细雨棘龙", mood_label="😭 伤心", mood_tip="伤心的时候可以哭出来，雨过天晴总会放晴的。", image_url="mood_spinosaurus.png", mood_score=2, sort_order=10, is_active=True),
            models.DinoConfig(id=11, legacy_key="Dilophosaurus", name="怒火双脊龙", mood_label="😡 愤怒", mood_tip="深呼吸，把怒火倾诉给恐龙，它会默默倾听你的委屈。", image_url="mood_dilophosaurus.png", mood_score=1, sort_order=11, is_active=True),
        ]
        db.add_all(initial_dinos)
        db.commit()
        logger.info("Database: Seeding initial dinosaur configs completed.")


def run_database_migrations_and_indexes(db: Session):
    """
    检查并补充缺失的数据库表字段与索引
    """
    # 补齐 columns
    columns_to_check = [
        ("users", "nickname", "VARCHAR"),
        ("users", "theme", "VARCHAR DEFAULT 'dark-neon'"),
        ("users", "is_active", "BOOLEAN DEFAULT 1"),
        ("users", "sticker_inventory", "VARCHAR DEFAULT ''"),
        ("users", "egg_energy", "INTEGER DEFAULT 0"),
        ("users", "canvas_inventory", "VARCHAR DEFAULT ''"),
        ("sticker_configs", "series_id", "INTEGER DEFAULT 1"),
        ("sticker_configs", "sort_order", "INTEGER DEFAULT 0"),
        ("sticker_configs", "exchange_price", "INTEGER DEFAULT 20"),
        ("sticker_configs", "created_at", "DATETIME DEFAULT '2026-07-17 00:00:00'"),
        ("sticker_configs", "is_deleted", "BOOLEAN DEFAULT 0"),
        ("sticker_series", "created_at", "DATETIME DEFAULT '2026-07-17 00:00:00'"),
        ("sticker_series", "is_deleted", "BOOLEAN DEFAULT 0"),
        ("logs", "updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("logs", "version", "INTEGER DEFAULT 1"),
        ("logs", "title", "VARCHAR"),
        ("logs", "media_rewarded", "BOOLEAN DEFAULT 0"),
        ("attachments", "md5", "VARCHAR"),
        ("attachments", "title", "VARCHAR"),
        ("persons", "category_uuid", "VARCHAR"),
        ("persons", "sort_order", "INTEGER DEFAULT 0"),
        ("persons", "color_tag", "VARCHAR DEFAULT 'red'"),
        ("persons", "is_temporary", "BOOLEAN DEFAULT 0"),
    ]

    for table, col, col_def in columns_to_check:
        try:
            db.execute(text(f"SELECT {col} FROM {table} LIMIT 1"))
        except Exception:
            db.rollback()
            try:
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}"))
                db.commit()
                logger.info(f"Database Migration: Added missing column '{col}' to '{table}'.")
            except Exception as alt_err:
                db.rollback()
                logger.warning(f"Database Migration: Could not add column '{col}' to '{table}': {alt_err}")

    # 索引保障
    try:
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_logs_user_deleted_incident ON logs(user_id, is_deleted, incident_date)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_persons_user_deleted ON persons(user_id, is_deleted)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_categories_user_deleted ON person_categories(user_id, is_deleted)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_attachments_log_id ON attachments(log_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_attachments_md5 ON attachments (md5)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_log_person_association_person_uuid ON log_person_association(person_uuid)"))
        db.commit()
        logger.info("Database Migration: Indexes verified/created successfully.")
    except Exception as idx_err:
        db.rollback()
        logger.error(f"Database Migration: Failed to create indexes: {idx_err}")


def auto_heal_media_rewards(db: Session):
    """
    历史数据自愈与补齐：为含有效附件的历史日志补发 20 蛋能量
    """
    try:
        unrewarded_logs_with_media = db.execute(text("""
            SELECT DISTINCT l.id, l.user_id, l.uuid 
            FROM logs l 
            JOIN attachments a ON l.uuid = a.log_uuid 
            WHERE (l.media_rewarded = 0 OR l.media_rewarded IS NULL)
        """)).fetchall()
        for row in unrewarded_logs_with_media:
            log_id, user_id, log_uuid = row[0], row[1], row[2]
            db.execute(text("UPDATE users SET egg_energy = egg_energy + 20 WHERE id = :uid"), {"uid": user_id})
            db.execute(text("UPDATE logs SET media_rewarded = 1 WHERE id = :lid"), {"lid": log_id})
            logger.info(f"Sticker Economy Migration: User {user_id} rewarded +20 bonus energy for historical media log {log_uuid}")
        db.commit()
    except Exception as heal_err:
        db.rollback()
        logger.warning(f"Failed to auto-heal historical media rewards: {heal_err}")


def seed_default_stickers(db: Session):
    """
    播种与自愈默认贴纸资产
    """
    try:
        default_series = db.query(models.StickerSeries).filter(models.StickerSeries.name == "3D恐龙", models.StickerSeries.is_deleted == False).first()
        if not default_series:
            logger.info("Database: Seeding default sticker series '3D恐龙'...")
            default_series = models.StickerSeries(name="3D恐龙", sort_order=1, is_active=True)
            db.add(default_series)
            db.commit()
            db.refresh(default_series)
            logger.info(f"Database: Default sticker series seeded with ID {default_series.id}.")

        base_static = Path(__file__).resolve().parent.parent / "static"
        series_id = default_series.id if default_series else 1
        upload_root = Path(settings.upload_dir)
        stickers_dir = upload_root / "stickers" / f"series_{series_id}"
        builtin_clean_dir = base_static / "images" / "default_stickers"
        stickers_dir.mkdir(parents=True, exist_ok=True)

        dino_asset_mapping = [
            ("三角龙", "sticker_3d_triceratops.png"),
            ("翼手龙", "sticker_3d_pterodactyl.png"),
            ("霸王龙", "sticker_3d_t_rex.png"),
            ("雷龙", "sticker_3d_brachiosaurus.png"),
            ("剑龙", "sticker_3d_stegosaurus.png"),
            ("迅猛龙", "sticker_3d_velociraptor.png"),
            ("甲龙", "sticker_3d_ankylosaurus.png"),
            ("肿头龙", "sticker_3d_pachycephalosaurus.png"),
            ("副栉龙", "sticker_3d_parasaurolophus.png"),
            ("棘龙", "sticker_3d_spinosaurus.png"),
            ("双脊龙", "sticker_3d_dilophosaurus.png")
        ]

        for s_name, target_name in dino_asset_mapping:
            target_file = stickers_dir / target_name
            src_file = builtin_clean_dir / target_name
            if src_file.exists():
                shutil.copy2(src_file, target_file)

        default_stickers = [
            {"name": "三角龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_triceratops.png", "description": "快乐是会传染的，今天也要开心哦！", "sort_order": 1, "exchange_price": 20},
            {"name": "翼手龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_pterodactyl.png", "description": "把快乐写进日记，让它飞得更高吧！", "sort_order": 2, "exchange_price": 20},
            {"name": "霸王龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_t_rex.png", "description": "你太棒了！今天也是值得自豪的一天！", "sort_order": 3, "exchange_price": 20},
            {"name": "雷龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_brachiosaurus.png", "description": "未来闪闪发光，让我们一起期待明天吧！", "sort_order": 4, "exchange_price": 20},
            {"name": "剑龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_stegosaurus.png", "description": "哇，今天发生了意想不到的奇妙事情呢！", "sort_order": 5, "exchange_price": 20},
            {"name": "迅猛龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_velociraptor.png", "description": "平静的一天也很美好，休息一下吧！", "sort_order": 6, "exchange_price": 20},
            {"name": "甲龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_ankylosaurus.png", "description": "别怕，缩进壳里也是保护自己的好办法，你很安全！", "sort_order": 7, "exchange_price": 20},
            {"name": "肿头龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_pachycephalosaurus.png", "description": "没关系，每一次小小的遗憾都是成长的足迹。", "sort_order": 8, "exchange_price": 20},
            {"name": "副栉龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_parasaurolophus.png", "description": "别太自责，过去的事就让它过去，下次会更好！", "sort_order": 9, "exchange_price": 20},
            {"name": "棘龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_spinosaurus.png", "description": "伤心的时候可以哭出来，雨过天晴总会放晴的。", "sort_order": 10, "exchange_price": 20},
            {"name": "双脊龙", "image_url": f"/static/uploads/stickers/series_{series_id}/sticker_3d_dilophosaurus.png", "description": "深呼吸，把怒火倾诉给恐龙，它会默默倾听你的委屈。", "sort_order": 11, "exchange_price": 20}
        ]
        
        modified = False
        for st in default_stickers:
            cfg = db.query(models.StickerConfig).filter(models.StickerConfig.name == st["name"], models.StickerConfig.is_deleted == False).first()
            if not cfg:
                new_cfg = models.StickerConfig(
                    series_id=series_id,
                    name=st["name"],
                    image_url=st["image_url"],
                    description=st["description"],
                    sort_order=st["sort_order"],
                    exchange_price=st["exchange_price"],
                    is_active=True
                )
                db.add(new_cfg)
                modified = True
            else:
                cfg_modified = False
                if series_id and cfg.series_id != series_id:
                    cfg.series_id = series_id
                    cfg_modified = True
                if cfg.image_url != st["image_url"]:
                    cfg.image_url = st["image_url"]
                    cfg_modified = True
                if cfg.sort_order != st["sort_order"]:
                    cfg.sort_order = st["sort_order"]
                    cfg_modified = True
                if cfg.exchange_price != st["exchange_price"]:
                    cfg.exchange_price = st["exchange_price"]
                    cfg_modified = True
                if cfg_modified:
                    db.add(cfg)
                    modified = True
        
        if modified:
            db.commit()
            logger.info("Database: Seeding/Self-healing of default sticker configs completed and committed.")
        else:
            logger.info("Database: All default sticker configs are up-to-date and clean.")

        from .stickers import migrate_legacy_sticker_files
        migration_res = migrate_legacy_sticker_files(db)
        if migration_res.get("migrated_count", 0) > 0:
            logger.info(f"Database Migration: Successfully migrated {migration_res['migrated_count']} legacy sticker files to series subfolders.")
    except Exception as seed_err:
        logger.error(f"Database: Failed to seed or self-heal sticker configs: {seed_err}")


def seed_default_canvases(db: Session):
    """
    播种与自愈默认画布资产 (系列: 恐龙世界, 套件: 森林家园 ID 3001)
    """
    try:
        base_static = Path(__file__).resolve().parent.parent / "static"
        upload_root = Path(settings.upload_dir)

        # 1. 确保分类 "恐龙世界" 存在
        series = db.query(models.CanvasSeries).filter(models.CanvasSeries.name == "恐龙世界", models.CanvasSeries.is_deleted == False).first()
        if not series:
            series = models.CanvasSeries(name="恐龙世界", sort_order=1, is_active=True, is_deleted=False)
            db.add(series)
            db.commit()
            db.refresh(series)

        series_id = series.id

        # 2. 确保套件 "森林家园" 存在（主键固定为 3001）
        canvas_set = db.query(models.CanvasSet).filter(models.CanvasSet.id == 3001).first()
        if not canvas_set:
            canvas_set = models.CanvasSet(
                id=3001,
                series_id=series_id,
                name="森林家园",
                description="远古绿野与清凉湖泊的森林家园",
                sort_order=1,
                exchange_price=50,
                is_active=True,
                is_deleted=False
            )
            db.add(canvas_set)
            db.commit()
            db.refresh(canvas_set)

        # 3. 复制图片到 uploads 对应目录
        canvases_dir = upload_root / "canvases" / f"series_{series_id}"
        canvases_dir.mkdir(parents=True, exist_ok=True)

        canvas_ratios = [
            ("16:9", "canvas_fallback_16_9.jpg", "canvas_3001_16_9.jpg", 1440, 810, 4001),
            ("4:3", "canvas_fallback_4_3.jpg", "canvas_3001_4_3.jpg", 1440, 1080, 4002),
            ("1:1", "canvas_fallback_1_1.jpg", "canvas_3001_1_1.jpg", 1440, 1440, 4003),
            ("2:1", "canvas_fallback_2_1.jpg", "canvas_3001_2_1.jpg", 1440, 720, 4004)
        ]

        for ratio, src_name, dest_name, w, h, inst_id in canvas_ratios:
            src_file = base_static / "images" / "canvases" / src_name
            dest_file = canvases_dir / dest_name
            if src_file.exists():
                shutil.copy2(src_file, dest_file)

            instance = db.query(models.CanvasInstance).filter(models.CanvasInstance.id == inst_id).first()
            rel_url = f"/static/uploads/canvases/series_{series_id}/{dest_name}"
            if not instance:
                instance = models.CanvasInstance(
                    id=inst_id,
                    canvas_set_id=3001,
                    aspect_ratio=ratio,
                    image_url=rel_url,
                    width=w,
                    height=h,
                    is_active=True,
                    is_deleted=False
                )
                db.add(instance)
            else:
                instance.canvas_set_id = 3001
                instance.aspect_ratio = ratio
                instance.image_url = rel_url
                instance.width = w
                instance.height = h
                instance.is_deleted = False
                db.add(instance)
        db.commit()

        # 4. 直接赠送这套画布给所有已存在的用户
        for u in db.query(models.User).all():
            inv = u.canvas_inventory or ""
            parts = [p.strip() for p in inv.split(",") if p.strip()]
            if "3001" not in parts:
                parts.append("3001")
                u.canvas_inventory = ",".join(parts)
                db.add(u)
        db.commit()
        logger.info("Database: Seeding of default canvas configs completed successfully.")
    except Exception as canvas_seed_err:
        db.rollback()
        logger.error(f"Database: Failed to seed default canvas configs: {canvas_seed_err}")


def init_system_data(db: Session):
    """
    全量启动初始化调度入口
    """
    # 1. 确保基础表结构与迁移索引
    run_database_migrations_and_indexes(db)

    # 2. 播种恐龙配置
    seed_initial_dino_configs(db)

    # 3. 历史数据自愈
    auto_heal_media_rewards(db)

    # 4. 播种默认贴纸与画布
    seed_default_stickers(db)
    seed_default_canvases(db)

    # 5. 默认管理员账号初始化
    admin_exists = db.query(models.User).filter(models.User.username == settings.default_admin_username).first()
    if not admin_exists:
        from ..auth import get_password_hash
        hashed = get_password_hash(settings.default_admin_password)
        new_admin = models.User(
            username=settings.default_admin_username,
            hashed_password=hashed,
            is_admin=True
        )
        db.add(new_admin)
        db.commit()
        logger.info(f"Database: Default admin user '{settings.default_admin_username}' seeded successfully.")

    # 6. 附件目录与商城迁移
    try:
        from .migrate_attachments import perform_attachment_migration
        perform_attachment_migration(db)
    except Exception as mig_err:
        logger.error(f"Attachment Migration: Error: {mig_err}")

    try:
        from .shop import migrate_shop_items
        migrate_shop_items(db)
    except Exception as shop_mig_err:
        logger.error(f"Shop Migration: Error: {shop_mig_err}")

    # 7. 播种蛋能量维度表与签到默认配置
    seed_energy_and_checkin_defaults(db)

    # 8. 历史蛋能量流水自愈与自洽还原
    try:
        from .energy_backfill import backfill_historical_energy_transactions
        backfill_historical_energy_transactions(db)
    except Exception as bf_err:
        logger.error(f"Energy Backfill: Error during backfill: {bf_err}")


def seed_energy_and_checkin_defaults(db: Session):
    """
    初始化蛋能量元数据维度表与签到默认参数
    """
    try:
        # 1. 实体维度表
        target_types = [
            (1, "SHOP_ITEM", "shop_items", "id", "name", "image_url", "手账商品"),
            (2, "CHECK_IN", "check_in_records", "id", "check_in_date", None, "每日签到"),
            (3, "LOG", "logs", "id", "incident_date", None, "手账日记"),
            (4, "PRIZE", "prizes", "id", "name", "image_url", "宝箱奖品"),
        ]
        for tid, code, tbl, pk, title, img, badge in target_types:
            existing = db.query(models.EggEnergyTargetType).filter(models.EggEnergyTargetType.target_type_id == tid).first()
            if not existing:
                db.add(models.EggEnergyTargetType(
                    target_type_id=tid,
                    target_code=code,
                    table_name=tbl,
                    pk_column=pk,
                    title_column=title,
                    image_column=img,
                    badge_label=badge
                ))
        db.commit()

        # 2. 事件维度表
        event_types = [
            (101, "DAILY_CHECKIN", 2, "EARN", "每日敲蛋签到", "ic_checkin"),
            (201, "LOG_REWARD", 3, "EARN", "手账日记奖励", "ic_diary"),
            (301, "SHOP_EXCHANGE", 1, "SPEND", "手账商城兑换", "ic_shop"),
            (401, "PRIZE_CHEST", 4, "EARN", "宝箱奖品开启", "ic_chest"),
            (501, "ADMIN_GRANT", 2, "EARN", "管理员补发", "ic_admin"),
            (502, "ADMIN_REVOKE", 2, "SPEND", "管理员核减", "ic_admin"),
        ]
        for eid, ecode, tid, direction, name, icon in event_types:
            existing = db.query(models.EggEnergyEventType).filter(models.EggEnergyEventType.event_type_id == eid).first()
            if not existing:
                db.add(models.EggEnergyEventType(
                    event_type_id=eid,
                    event_code=ecode,
                    target_type_id=tid,
                    direction=direction,
                    display_name=name,
                    icon_key=icon
                ))
        db.commit()

        # 3. 默认签到配置
        config_exists = db.query(models.CheckInConfig).first()
        if not config_exists:
            db.add(models.CheckInConfig(
                id=1,
                base_min=5,
                base_max=15,
                crit_rate=0.15,
                crit_min=30,
                crit_max=66,
                streak_enabled=True,
                streak_rules_json='{"3": 5, "7": 20}'
            ))
            db.commit()
            logger.info("Database: Default check-in configuration seeded successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Database: Failed to seed energy and check-in defaults: {e}")

