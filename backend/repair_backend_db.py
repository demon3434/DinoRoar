import sys
import os
import datetime

sys.path.append(os.path.abspath('e:\\home\\lyc\\Documents\\code\\DinoRoar\\backend'))

from app.database import SessionLocal
from app.models import Log

db = SessionLocal()
try:
    # Query all logs ordered by incident_date
    logs = db.query(Log).order_by(Log.incident_date).all()
    idx = 1
    updated_count = 0
    for log in logs:
        if not log.title or log.title.strip() == "":
            log.title = f"写作业{idx}"
            log.version = (log.version or 1) + 1
            log.updated_at = datetime.datetime.utcnow()
            idx += 1
            updated_count += 1
    db.commit()
    print(f"Successfully repaired {updated_count} logs in backend database.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
