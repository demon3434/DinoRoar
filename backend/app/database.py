import os
import shutil
import logging
from pathlib import Path
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

logger = logging.getLogger("DinoRoar.database")

def check_and_migrate_db_filepath():
    """
    If legacy uploads/dinoroar.db exists and data/dinoroar.db does not exist,
    move the database file and WAL/SHM logs to data/dinoroar.db.
    """
    old_db = Path("./uploads/dinoroar.db")
    new_db = Path("./data/dinoroar.db")

    if old_db.exists() and not new_db.exists():
        logger.info("Migrating database file from ./uploads/dinoroar.db to ./data/dinoroar.db ...")
        new_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_db), str(new_db))

        # Move WAL/SHM files if present
        for ext in ["-wal", "-shm"]:
            old_extra = Path(f"./uploads/dinoroar.db{ext}")
            new_extra = Path(f"./data/dinoroar.db{ext}")
            if old_extra.exists() and not new_extra.exists():
                shutil.move(str(old_extra), str(new_extra))

check_and_migrate_db_filepath()

# SQLite checks_same_thread needs to be disabled only for sqlite
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False
)

# Enforce UTF-8 encoding on every SQLite connection
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_utf8(dbapi_connection, connection_record):
        dbapi_connection.execute("PRAGMA encoding='UTF-8'")
        dbapi_connection.execute("PRAGMA journal_mode=WAL")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

