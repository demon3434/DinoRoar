import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "uploads", "dinoroar.db")

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

LEGACY_REDIRECT = {
    "Parasaurolophus": "Spinosaurus",
    "Pterodactyl": "Pachycephalosaurus",
    "Pterodactyl_Sigh": "Pachycephalosaurus",
    "T-Rex": "Dilophosaurus",
    "T-Rex_Angry": "Dilophosaurus",
    "Parasaurolophus_Regret": "Parasaurolophus_regret",
    "Ankylosaurus_Shell": "Ankylosaurus_scared",
    "Ankylosaurus": "Velociraptor"
}

def migrate():
    print(f"Connecting to database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database file not found. Skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Create dino_config table if not exists
        print("Step 1: Creating dino_config table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dino_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legacy_key VARCHAR(64) UNIQUE NOT NULL,
            name VARCHAR(64) NOT NULL,
            mood_label VARCHAR(32) NOT NULL,
            mood_tip VARCHAR(256),
            image_url VARCHAR(256) NOT NULL,
            mood_score INTEGER NOT NULL DEFAULT 5,
            sort_order INTEGER NOT NULL DEFAULT 99,
            is_active BOOLEAN NOT NULL DEFAULT 1
        )
        """)
        conn.commit()

        # 2. Insert initial dinosaurs
        print("Step 2: Seeding initial dinosaur configs...")
        for dino in INITIAL_DINOS:
            cursor.execute("""
            INSERT OR IGNORE INTO dino_config (id, legacy_key, name, mood_label, mood_tip, image_url, mood_score, sort_order, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, dino)
        conn.commit()

        # 3. Add new columns to logs if they don't exist
        print("Step 3: Checking and adding new columns to logs table...")
        
        # Helper to check if column exists
        cursor.execute("PRAGMA table_info(logs)")
        columns = [col[1] for col in cursor.fetchall()]

        if "mood_dino_legacy" not in columns:
            print("Adding column mood_dino_legacy to logs...")
            cursor.execute("ALTER TABLE logs ADD COLUMN mood_dino_legacy VARCHAR")
            conn.commit()

        if "mood_dino_id" not in columns:
            print("Adding column mood_dino_id to logs...")
            cursor.execute("ALTER TABLE logs ADD COLUMN mood_dino_id INTEGER")
            conn.commit()

        # 4. Copy mood_dino values to mood_dino_legacy if legacy is empty/null
        print("Step 4: Backing up mood_dino values to mood_dino_legacy...")
        if "mood_dino" in columns:
            cursor.execute("UPDATE logs SET mood_dino_legacy = mood_dino WHERE mood_dino_legacy IS NULL OR mood_dino_legacy = ''")
            conn.commit()

        # 5. Populate mood_dino_id based on legacy key with redirection
        print("Step 5: Performing mapping migration...")
        cursor.execute("SELECT id, legacy_key FROM dino_config")
        dino_map = {row[1]: row[0] for row in cursor.fetchall()}

        cursor.execute("SELECT id, mood_dino_legacy FROM logs WHERE mood_dino_id IS NULL")
        logs_to_migrate = cursor.fetchall()

        success_count = 0
        failed_count = 0

        for log_id, legacy_key in logs_to_migrate:
            if not legacy_key:
                failed_count += 1
                continue

            target_key = legacy_key
            # Redirect historical keys
            if legacy_key in LEGACY_REDIRECT:
                target_key = LEGACY_REDIRECT[legacy_key]

            if target_key in dino_map:
                dino_id = dino_map[target_key]
                cursor.execute("UPDATE logs SET mood_dino_id = ? WHERE id = ?", (dino_id, log_id))
                success_count += 1
            else:
                print(f"Warning: Could not map legacy key '{legacy_key}' (target: '{target_key}') for log ID {log_id}")
                failed_count += 1

        conn.commit()
        print(f"Migration progress: Successfully updated {success_count} records. Failed/Skipped: {failed_count}.")

        # 6. Drop old mood_dino column to normalize the schema
        print("Step 6: Dropping old mood_dino column...")
        cursor.execute("PRAGMA table_info(logs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "mood_dino" in columns:
            try:
                # SQLite 3.35+ supports DROP COLUMN
                cursor.execute("ALTER TABLE logs DROP COLUMN mood_dino")
                conn.commit()
                print("Successfully dropped 'mood_dino' column.")
            except Exception as e:
                print(f"Could not drop 'mood_dino' column using ALTER (old SQLite version): {e}")
                print("Leaving old column in place. Application models are updated to ignore it.")

        # 7. Force update Velociraptor config for ID 6 and ID 1006 (migrate from Ankylosaurus)
        print("Step 7: Enforcing Velociraptor update for ID 6 and ID 1006...")
        cursor.execute("""
        UPDATE dino_config 
        SET legacy_key = 'Velociraptor', name = '佛系迅猛龙', image_url = 'mood_velociraptor.png'
        WHERE id = 6
        """)
        
        # Check if sticker_configs table exists and update
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sticker_configs'")
        if cursor.fetchone():
            cursor.execute("""
            UPDATE sticker_configs
            SET name = '迅猛龙', image_url = 'mood_velociraptor.png'
            WHERE id = 1006
            """)
            cursor.execute("""
            UPDATE sticker_configs
            SET name = '甲龙'
            WHERE id = 1007
            """)
        conn.commit()

        print("Migration successfully completed.")

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
