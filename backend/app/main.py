import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import Base, engine, SessionLocal, migrate_and_cleanup_legacy_settings
from .services.mdns_discovery import broadcaster, get_mdns_settings_and_start

# Configure Logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DinoRoar")

INITIAL_DINOS = [
    (1, "Triceratops", "快乐三角龙", "😊 开心", "快乐是会传染的，今天也要开心哦！", "mood_triceratops.png", 10, 1, 1),
    (2, "Pterodactyl_happy", "冲天翼手龙", "🤩 兴奋", "把快乐写进日记，让它飞得更高吧！", "mood_pterodactyl_happy.png", 9, 2, 1),
    (3, "T-Rex_proud", "挺胸霸王龙", "😎 得意", "你太棒了！今天也是值得自豪的一天！", "mood_t_rex_proud.png", 8, 3, 1),
    (4, "Brachiosaurus", "大眼睛雷龙", "🌟 期待", "未来闪闪发光，让我们一起期待明天吧！", "mood_brachiosaurus.png", 7, 4, 1),
    (5, "Stegosaurus", "呆呆剑龙", "😮 惊讶", "哇，今天发生了意想不到的奇妙事情呢！", "mood_stegosaurus.png", 6, 5, 1),
    (6, "Velociraptor", "佛系迅猛龙", "😐 一般", "平静的一天也很美好，休息一下吧！", "mood_velociraptor.png", 5, 6, 1),
    (7, "Ankylosaurus_scared", "缩壳甲龙", "😰 紧张", "别怕，缩进壳里也是保护自己的好办法，你很安全！", "mood_ankylosaurus_scared.png", 4, 7, 1),
    (8, "Pachycephalosaurus", "叹气肿头龙", "🍃 遗憾", "没关系，每一次小小的遗憾都是成长的足迹。", "mood_pachycephalosaurus.png", 3, 8, 1),
    (9, "Parasaurolophus_regret", "耷拉角副栉龙", "😣 后悔", "别太自责，过去的事就让它过去，下次会更好！", "mood_parasaurolophus_regret.png", 2, 9, 1),
    (10, "Spinosaurus", "细雨棘龙", "😭 伤心", "伤心的时候可以哭出来，雨过天晴总会放晴的。", "mood_spinosaurus.png", 2, 10, 1),
    (11, "Dilophosaurus", "怒火双脊龙", "😡 愤怒", "深呼吸，把怒火倾诉给恐龙，它会默默倾听你的委屈。", "mood_dilophosaurus.png", 1, 11, 1),
]

def seed_initial_dino_configs(db):
    try:
        from . import models
        count = db.query(models.DinoConfig).count()
        if count == 0:
            logger.info("Database: Seeding default 11 DinoConfigs...")
            for item in INITIAL_DINOS:
                dino = models.DinoConfig(
                    id=item[0],
                    legacy_key=item[1],
                    name=item[2],
                    mood_label=item[3],
                    mood_tip=item[4],
                    image_url=item[5],
                    mood_score=item[6],
                    sort_order=item[7],
                    is_active=bool(item[8])
                )
                db.add(dino)
            db.commit()
            logger.info("Database: Default DinoConfigs seeded successfully.")
    except Exception as e:
        logger.error(f"Database: Error seeding DinoConfigs: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Migrate legacy system_settings table if present
    try:
        migrate_and_cleanup_legacy_settings()
    except Exception as err:
        logger.error(f"Error during legacy settings migration: {err}")

    # Initialize DB tables
    try:
        from . import models
        Base.metadata.create_all(bind=engine)
        logger.info("Database: Tables verified/created successfully.")
        
        # Seed default admin user and run quick migrations
        db = SessionLocal()
        try:
            from sqlalchemy import text

            # 1. Migration check: Add nickname column if missing
            try:
                db.execute(text("SELECT nickname FROM users LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info("Database Migration: Adding missing 'nickname' column to 'users' table...")
                db.execute(text("ALTER TABLE users ADD COLUMN nickname VARCHAR"))
                db.commit()
                logger.info("Database Migration: 'nickname' column added successfully.")
            
            # 2. Migration check: Add theme column if missing
            try:
                db.execute(text("SELECT theme FROM users LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info("Database Migration: Adding missing 'theme' column to 'users' table...")
                db.execute(text("ALTER TABLE users ADD COLUMN theme VARCHAR DEFAULT 'dark-neon'"))
                db.commit()
                logger.info("Database Migration: 'theme' column added successfully.")

            # 3. Migration check: Add is_active column if missing
            try:
                db.execute(text("SELECT is_active FROM users LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info("Database Migration: Adding missing 'is_active' column to 'users' table...")
                db.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                db.commit()
                logger.info("Database Migration: 'is_active' column added successfully.")

            # 4. Migration check: Add sticker_inventory column to users if missing
            try:
                db.execute(text("SELECT sticker_inventory FROM users LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info("Database Migration: Adding missing 'sticker_inventory' column to 'users' table...")
                db.execute(text("ALTER TABLE users ADD COLUMN sticker_inventory VARCHAR DEFAULT ''"))
                db.commit()
                logger.info("Database Migration: 'sticker_inventory' column added successfully.")

            # 5. Migration check: Add egg_energy column to users if missing
            try:
                db.execute(text("SELECT egg_energy FROM users LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info("Database Migration: Adding missing 'egg_energy' column to 'users' table...")
                db.execute(text("ALTER TABLE users ADD COLUMN egg_energy INTEGER DEFAULT 0"))
                db.commit()
                logger.info("Database Migration: 'egg_energy' column added successfully.")

            # 6. Migration check: Add canvas_inventory column to users if missing
            try:
                db.execute(text("SELECT canvas_inventory FROM users LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info("Database Migration: Adding missing 'canvas_inventory' column to 'users' table...")
                db.execute(text("ALTER TABLE users ADD COLUMN canvas_inventory VARCHAR DEFAULT ''"))
                db.commit()
                logger.info("Database Migration: 'canvas_inventory' column added successfully.")

            # 7. Migration check: Add missing columns to sticker_configs if missing
            try:
                db.execute(text("SELECT series_id FROM sticker_configs LIMIT 1"))
            except Exception:
                db.rollback()
                db.execute(text("ALTER TABLE sticker_configs ADD COLUMN series_id INTEGER DEFAULT NULL"))
                db.commit()
                
            try:
                db.execute(text("SELECT sort_order FROM sticker_configs LIMIT 1"))
            except Exception:
                db.rollback()
                db.execute(text("ALTER TABLE sticker_configs ADD COLUMN sort_order INTEGER DEFAULT 0"))
                db.commit()
                
            try:
                db.execute(text("SELECT exchange_price FROM sticker_configs LIMIT 1"))
            except Exception:
                db.rollback()
                db.execute(text("ALTER TABLE sticker_configs ADD COLUMN exchange_price INTEGER DEFAULT 20"))
                db.commit()
                
            try:
                db.execute(text("SELECT created_at FROM sticker_configs LIMIT 1"))
            except Exception:
                db.rollback()
                db.execute(text("ALTER TABLE sticker_configs ADD COLUMN created_at DATETIME DEFAULT '2026-07-17 00:00:00'"))
                db.commit()
                
            try:
                db.execute(text("SELECT is_deleted FROM sticker_configs LIMIT 1"))
            except Exception:
                db.rollback()
                db.execute(text("ALTER TABLE sticker_configs ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
                db.commit()

            # 8. Migration check: Add missing columns to sticker_series if missing
            try:
                db.execute(text("SELECT created_at FROM sticker_series LIMIT 1"))
            except Exception:
                db.rollback()
                db.execute(text("ALTER TABLE sticker_series ADD COLUMN created_at DATETIME DEFAULT '2026-07-17 00:00:00'"))
                db.commit()

            # 9. Migration check: Create indexes if missing
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_logs_user_deleted_incident ON logs(user_id, is_deleted, incident_date)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_persons_user_deleted ON persons(user_id, is_deleted)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_categories_user_deleted ON person_categories(user_id, is_deleted)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_attachments_log_id ON attachments(log_id)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_log_person_association_person_uuid ON log_person_association(person_uuid)"))
                db.commit()
                logger.info("Database Migration: Indexes verified/created successfully.")
            except Exception as idx_err:
                db.rollback()
                logger.error(f"Database Migration: Failed to create indexes: {idx_err}")

            # 10. Seed DinoConfigs if empty
            seed_initial_dino_configs(db)
                
            try:
                db.execute(text("SELECT is_deleted FROM sticker_series LIMIT 1"))
            except Exception:
                db.rollback()
                db.execute(text("ALTER TABLE sticker_series ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
                db.commit()

            # Migration check: Add media_rewarded column to logs if missing
            try:
                db.execute(text("SELECT media_rewarded FROM logs LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info("Database Migration: Adding missing 'media_rewarded' column to 'logs' table...")
                db.execute(text("ALTER TABLE logs ADD COLUMN media_rewarded BOOLEAN DEFAULT 0"))
                db.commit()
                logger.info("Database Migration: 'media_rewarded' column added successfully.")

            # 历史数据自愈与补齐：如果日记已有有效附件但未标记 media_rewarded，为对应用户补发 20 蛋能量并标记已奖励
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

            # Seed default series '3D恐龙' if not exists
            try:
                default_series = db.query(models.StickerSeries).filter(models.StickerSeries.name == "3D恐龙", models.StickerSeries.is_deleted == False).first()
                if not default_series:
                    logger.info("Database: Seeding default sticker series '3D恐龙'...")
                    default_series = models.StickerSeries(name="3D恐龙", sort_order=1, is_active=True)
                    db.add(default_series)
                    db.commit()
                    db.refresh(default_series)
                    logger.info(f"Database: Default sticker series seeded with ID {default_series.id}.")
            except Exception as series_err:
                logger.error(f"Database: Failed to seed sticker series: {series_err}")
                default_series = db.query(models.StickerSeries).filter(models.StickerSeries.name == "3D恐龙").first()

            # Seed and self-heal default sticker configs individually
            try:
                logger.info("Database: Verifying and seeding default sticker configs...")

                from pathlib import Path
                import shutil
                base_static = Path(__file__).resolve().parent / "static"
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
                        logger.info(f"Database: Seeding missing default sticker ({st['name']})...")
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

                from app.services.stickers import migrate_legacy_sticker_files
                migration_res = migrate_legacy_sticker_files(db)
                if migration_res.get("migrated_count", 0) > 0:
                    logger.info(f"Database Migration: Successfully migrated {migration_res['migrated_count']} legacy sticker files to series subfolders.")
            except Exception as seed_err:
                logger.error(f"Database: Failed to seed or self-heal sticker configs: {seed_err}")

            # Seed and self-heal default canvas configs (Series: "恐龙世界", Set: "森林家园")
            try:
                logger.info("Database: Verifying and seeding default canvas configs...")
                from pathlib import Path
                import shutil
                base_static = Path(__file__).resolve().parent / "static"
                upload_root = Path(settings.upload_dir)

                # 1. 确保分类 "恐龙世界" 存在
                series = db.query(models.CanvasSeries).filter(models.CanvasSeries.name == "恐龙世界", models.CanvasSeries.is_deleted == False).first()
                if not series:
                    logger.info("Database: Seeding default canvas series '恐龙世界'...")
                    series = models.CanvasSeries(name="恐龙世界", sort_order=1, is_active=True, is_deleted=False)
                    db.add(series)
                    db.commit()
                    db.refresh(series)

                series_id = series.id

                # 2. 确保套件 "森林家园" 存在（主键固定为 3001）
                canvas_set = db.query(models.CanvasSet).filter(models.CanvasSet.id == 3001).first()
                if not canvas_set:
                    logger.info("Database: Seeding default canvas set '森林家园' with ID 3001...")
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

                # 3. 复制对应的图片文件到 uploads 对应目录下
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
                        logger.info(f"Database: Copied fallback asset {src_name} to uploads: {dest_name}")
                    else:
                        logger.warning(f"Database: Builtin canvas asset {src_name} not found!")

                    # 4. 插入或更新对应的实例数据 (4001 - 4004)
                    instance = db.query(models.CanvasInstance).filter(models.CanvasInstance.id == inst_id).first()
                    rel_url = f"/static/uploads/canvases/series_{series_id}/{dest_name}"
                    if not instance:
                        logger.info(f"Database: Seeding canvas instance for {ratio}...")
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

                # 5. 直接赠送这套画布给所有已存在的用户（防漏）
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

            # Migration check: Add updated_at column to logs if missing
            try:
                db.execute(text("SELECT updated_at FROM logs LIMIT 1"))
            except Exception:
                logger.info("Database Migration: Adding missing 'updated_at' column to 'logs' table...")
                db.execute(text("ALTER TABLE logs ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                db.commit()
                logger.info("Database Migration: 'updated_at' column added successfully.")

            # Migration check: Add version column to logs if missing
            try:
                db.execute(text("SELECT version FROM logs LIMIT 1"))
            except Exception:
                logger.info("Database Migration: Adding missing 'version' column to 'logs' table...")
                db.execute(text("ALTER TABLE logs ADD COLUMN version INTEGER DEFAULT 1"))
                db.commit()
                logger.info("Database Migration: 'version' column added successfully.")

            # Migration check: Add title column to logs if missing
            try:
                db.execute(text("SELECT title FROM logs LIMIT 1"))
            except Exception:
                logger.info("Database Migration: Adding missing 'title' column to 'logs' table...")
                db.execute(text("ALTER TABLE logs ADD COLUMN title VARCHAR"))
                db.commit()
                logger.info("Database Migration: 'title' column added successfully.")

            # Migration check: Add md5 column to attachments if missing
            try:
                db.execute(text("SELECT md5 FROM attachments LIMIT 1"))
            except Exception:
                logger.info("Database Migration: Adding missing 'md5' column to 'attachments' table...")
                db.execute(text("ALTER TABLE attachments ADD COLUMN md5 VARCHAR"))
                db.execute(text("CREATE INDEX IF NOT EXISTS ix_attachments_md5 ON attachments (md5)"))
                db.commit()
                logger.info("Database Migration: 'md5' column and index added successfully.")

            # Migration check: Add title column to attachments if missing
            try:
                db.execute(text("SELECT title FROM attachments LIMIT 1"))
            except Exception:
                db.rollback()
                logger.info("Database Migration: Adding missing 'title' column to 'attachments' table...")
                db.execute(text("ALTER TABLE attachments ADD COLUMN title VARCHAR"))
                db.commit()
                logger.info("Database Migration: 'title' column added to 'attachments' table successfully.")

            # Migration check: Add category_uuid to persons if missing
            try:
                db.execute(text("SELECT category_uuid FROM persons LIMIT 1"))
            except Exception:
                logger.info("Database Migration: Adding missing 'category_uuid' column to 'persons' table...")
                db.execute(text("ALTER TABLE persons ADD COLUMN category_uuid VARCHAR"))
                db.commit()

            # Migration check: Add sort_order to persons if missing
            try:
                db.execute(text("SELECT sort_order FROM persons LIMIT 1"))
            except Exception:
                logger.info("Database Migration: Adding missing 'sort_order' column to 'persons' table...")
                db.execute(text("ALTER TABLE persons ADD COLUMN sort_order INTEGER DEFAULT 0"))
                db.commit()



            # Migration check: Add color_tag to persons if missing
            try:
                db.execute(text("SELECT color_tag FROM persons LIMIT 1"))
            except Exception:
                logger.info("Database Migration: Adding missing 'color_tag' column to 'persons' table...")
                db.execute(text("ALTER TABLE persons ADD COLUMN color_tag VARCHAR DEFAULT 'red'"))
                db.commit()

            # Migration check: Add is_temporary to persons if missing
            try:
                db.execute(text("SELECT is_temporary FROM persons LIMIT 1"))
            except Exception:
                logger.info("Database Migration: Adding missing 'is_temporary' column to 'persons' table...")
                db.execute(text("ALTER TABLE persons ADD COLUMN is_temporary BOOLEAN DEFAULT 0"))
                db.commit()

            # Default admin creation checks (no auto-migration overrides)
            
            admin_exists = db.query(models.User).filter(models.User.username == settings.default_admin_username).first()


            if not admin_exists:
                from .auth import get_password_hash
                hashed = get_password_hash(settings.default_admin_password)
                new_admin = models.User(
                    username=settings.default_admin_username,
                    hashed_password=hashed,
                    is_admin=True
                )
                db.add(new_admin)
                db.commit()
                logger.info(f"Database: Default admin user '{settings.default_admin_username}' seeded successfully.")

            # Seed initial dinosaur configs if empty
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

            # Perform smooth migration of legacy attachment files into YYYY/MM subdirectories
            try:
                from .services.migrate_attachments import perform_attachment_migration
                res = perform_attachment_migration(db)
                if res.get("migrated_count", 0) > 0:
                    logger.info(f"Attachment Migration: Successfully migrated {res['migrated_count']} legacy files.")
            except Exception as mig_err:
                logger.error(f"Attachment Migration: Error during startup migration: {mig_err}")

            # Perform smooth migration and auto-sync of shop items
            try:
                from .services.shop import migrate_shop_items
                shop_mig_count = migrate_shop_items(db)
                if shop_mig_count > 0:
                    logger.info(f"Shop Migration: Successfully synced {shop_mig_count} items into shop_items.")
            except Exception as shop_mig_err:
                logger.error(f"Shop Migration: Error during startup migration: {shop_mig_err}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database: Failed to check/create tables or seed default admin: {e}")


    # Start mDNS Broadcaster in background thread to avoid blocking main event loop
    try:
        import asyncio
        await asyncio.to_thread(get_mdns_settings_and_start)
    except Exception as mdns_err:
        logger.error(f"Lifespan: Error starting mDNS broadcaster: {mdns_err}")

    # Start background task to compress historical uploads (lossless optimization)
    try:
        from .services.compress_historical import start_historical_compression
        start_historical_compression()
    except Exception as compress_err:
        logger.error(f"Error starting historical image compression: {compress_err}")
    
    yield
    
    # Shutdown: Stop mDNS Broadcaster
    logger.info("Lifespan: Stopping mDNS broadcaster...")
    try:
        import asyncio
        await asyncio.to_thread(broadcaster.stop)
    except Exception as mdns_stop_err:
        logger.error(f"Lifespan: Error stopping mDNS broadcaster: {mdns_stop_err}")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan
)

# Register Routers
from .routers import auth, logs, settings as settings_router, attachments, admin_users, pages, persons, categories, dino_config, stickers, stt, canvases, shop
app.include_router(auth.router)
app.include_router(logs.router)
app.include_router(settings_router.router)
app.include_router(attachments.router)
app.include_router(admin_users.router)
app.include_router(pages.router)
app.include_router(persons.router)
app.include_router(categories.router)
app.include_router(dino_config.router)
app.include_router(stickers.router)
app.include_router(stt.router)
app.include_router(canvases.router)
app.include_router(shop.router)



# Mount Static Files
from pathlib import Path
uploads_dir = Path(settings.upload_dir)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="static_uploads")

static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global UTF-8 charset enforcement middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

class Utf8CharsetMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/js/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        ct = response.headers.get("content-type", "")
        if ct and "charset" not in ct and (
            "text/" in ct or "application/json" in ct or "application/javascript" in ct
        ):
            response.headers["content-type"] = ct + "; charset=utf-8"
        return response

app.add_middleware(Utf8CharsetMiddleware)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "mdns_active": broadcaster.zc is not None,
        "advertised_address": f"{broadcaster.active_host}:{broadcaster.active_port}" if broadcaster.active_host else None
    }
