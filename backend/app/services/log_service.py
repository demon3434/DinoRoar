import os
import re
import datetime
import logging
from typing import List, Optional
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm import Session, selectinload
from ..models import Log, Attachment, User, Person, PersonCategory
from ..schemas import LogSyncPayload
from .analytics_service import extract_high_frequency_words

logger = logging.getLogger("DinoRoar.logs")

def sync_logs_service(db: Session, current_user: User, payload: LogSyncPayload) -> List[Log]:
    # 1. Process client deletions (Hard Delete)
    if payload.deleted_uuids:
        to_delete = db.query(Log).filter(
            Log.uuid.in_(payload.deleted_uuids),
            Log.user_id == current_user.id
        ).all()
        
        for log in to_delete:
            for attachment in log.attachments:
                if os.path.exists(attachment.file_path):
                    try:
                        os.remove(attachment.file_path)
                    except Exception:
                        pass
            db.delete(log)
        db.commit()

    # 2. Process client additions/updates
    for log_data in payload.logs:
        existing_log = db.query(Log).filter(
            Log.uuid == log_data.uuid,
            Log.user_id == current_user.id
        ).first()

        associated_persons = []
        if log_data.person_uuids:
            associated_persons = db.query(Person).filter(
                Person.uuid.in_(log_data.person_uuids),
                Person.user_id == current_user.id
            ).all()

        if existing_log:
            if existing_log.version > log_data.version:
                logger.warning(f"Sync conflict: Server version ({existing_log.version}) is higher than client base version ({log_data.version}) for UUID {log_data.uuid}. Skipping client update.")
                continue

            client_updated_at = log_data.updated_at
            if client_updated_at and client_updated_at.tzinfo is not None:
                client_updated_at = client_updated_at.replace(tzinfo=None)
                
            db_updated_at = existing_log.updated_at
            if db_updated_at and db_updated_at.tzinfo is not None:
                db_updated_at = db_updated_at.replace(tzinfo=None)

            if db_updated_at and client_updated_at and db_updated_at > client_updated_at:
                logger.info(f"Sync logs LWW: Skipped stale client update for UUID {log_data.uuid}")
                continue

            existing_log.incident_date = log_data.incident_date.replace(tzinfo=None) if log_data.incident_date.tzinfo is not None else log_data.incident_date
            existing_log.mood_dino_id = log_data.mood_dino_id
            existing_log.content = log_data.content
            existing_log.own_thoughts = log_data.own_thoughts
            existing_log.title = log_data.title[:10] if log_data.title else None
            existing_log.updated_at = client_updated_at or datetime.datetime.utcnow()
            existing_log.version = max(existing_log.version, log_data.version) + 1
            
            existing_log.persons = associated_persons
        else:
            client_updated_at = log_data.updated_at
            if client_updated_at and client_updated_at.tzinfo is not None:
                client_updated_at = client_updated_at.replace(tzinfo=None)
                
            new_log = Log(
                user_id=current_user.id,
                uuid=log_data.uuid,
                title=log_data.title[:10] if log_data.title else None,
                incident_date=log_data.incident_date.replace(tzinfo=None) if log_data.incident_date.tzinfo is not None else log_data.incident_date,
                mood_dino_id=log_data.mood_dino_id,
                content=log_data.content,
                own_thoughts=log_data.own_thoughts,
                updated_at=client_updated_at or datetime.datetime.utcnow(),
                version=log_data.version or 1
            )
            new_log.persons = associated_persons
            db.add(new_log)
            
            earned_energy = 10
            has_media = db.query(Attachment).filter(Attachment.log_uuid == log_data.uuid).first() is not None
            if has_media:
                earned_energy += 20
                
            current_user.egg_energy += earned_energy
            logger.info(f"Sticker Economy: User {current_user.id} earned {earned_energy} energy for new log {log_data.uuid}")

            stickers_in_log = re.findall(r'\[sticker:([^:]+):[0-9.-]+,[0-9.-]+\]', log_data.content)
            if stickers_in_log:
                stickers_to_deduct = {}
                for st in stickers_in_log:
                    try:
                        s_id = int(st.strip())
                        stickers_to_deduct[s_id] = stickers_to_deduct.get(s_id, 0) + 1
                    except ValueError:
                        continue
                
                if stickers_to_deduct:
                    inventory = {}
                    inv_str = current_user.sticker_inventory or ""
                    for item in inv_str.split(','):
                        parts = item.split(':')
                        if len(parts) == 2:
                            try:
                                inventory[int(parts[0])] = int(parts[1])
                            except ValueError:
                                pass
                    for s_id, count in stickers_to_deduct.items():
                        if s_id in inventory:
                            inventory[s_id] = max(0, inventory[s_id] - count)
                      
                    current_user.sticker_inventory = ",".join(f"{k}:{v}" for k, v in inventory.items())
                    logger.info(f"Sticker Economy: User {current_user.id} sticker inventory updated after sync: {current_user.sticker_inventory}")

    db.commit()

    active_logs = db.query(Log).filter(
        Log.user_id == current_user.id,
        Log.is_deleted == False
    ).all()
    
    log_uuids = [log.uuid for log in active_logs]
    orphans = db.query(Attachment).filter(
        Attachment.log_uuid.in_(log_uuids),
        Attachment.log_id.is_(None)
    ).all()
    
    if orphans:
        log_map = {log.uuid: log.id for log in active_logs}
        for attachment in orphans:
            attachment.log_id = log_map.get(attachment.log_uuid)
        db.commit()

    active_logs_loaded = db.query(Log).filter(
        Log.user_id == current_user.id,
        Log.is_deleted == False
    ).options(selectinload(Log.attachments), selectinload(Log.persons)).all()

    return active_logs_loaded


def get_logs_stats_overview_service(db: Session, current_user: User) -> dict:
    happy_mood_ids = {1, 2, 3, 4}
    sad_mood_ids = {7, 8, 9, 10, 11}
    
    all_logs = db.query(Log).filter(
        Log.user_id == current_user.id,
        Log.is_deleted == False
    ).order_by(desc(Log.incident_date))\
     .options(selectinload(Log.persons), selectinload(Log.attachments), selectinload(Log.dino_config)).all()
     
    date_mood_map = {}
    for log in reversed(all_logs):
        try:
            day_str = log.incident_date.strftime("%Y-%m-%d")
            date_mood_map[day_str] = log.mood_dino_id
        except Exception:
            pass
            
    sorted_days = sorted(date_mood_map.keys(), reverse=True)[:30]
    mood_heatmap = [{"date": day, "mood": date_mood_map[day]} for day in reversed(sorted_days)]
    
    # ---- 1. 蛋能量四宫格增量 & 余额计算 ----
    today_dt = datetime.date.today()
    start_of_this_week = today_dt - datetime.timedelta(days=today_dt.weekday())
    end_of_this_week = start_of_this_week + datetime.timedelta(days=6)
    start_of_last_week = start_of_this_week - datetime.timedelta(days=7)
    end_of_last_week = start_of_this_week - datetime.timedelta(days=1)
    start_of_this_month = today_dt.replace(day=1)

    def calc_log_energy(log_item):
        has_media = any(att.mime_type.startswith("image/") or att.mime_type.startswith("audio/") or att.mime_type.startswith("video/") for att in log_item.attachments)
        return 30 if has_media else 10

    total_accumulated_energy = 0
    energy_today = 0
    energy_this_week = 0
    energy_last_week = 0
    energy_this_month = 0

    for log in all_logs:
        if not log.incident_date:
            continue
        log_date = log.incident_date.date() if isinstance(log.incident_date, datetime.datetime) else log.incident_date
        e = calc_log_energy(log)
        total_accumulated_energy += e
        if log_date == today_dt:
            energy_today += e
        if start_of_this_week <= log_date <= end_of_this_week:
            energy_this_week += e
        if start_of_last_week <= log_date <= end_of_last_week:
            energy_last_week += e
        if log_date >= start_of_this_month:
            energy_this_month += e

    user_balance = getattr(current_user, "egg_energy", 0)
    if user_balance == 0 and total_accumulated_energy > 0:
        user_balance = total_accumulated_energy

    egg_energy_data = {
        "balance": user_balance,
        "today": energy_today,
        "this_week": energy_this_week,
        "last_week": energy_last_week,
        "this_month": energy_this_month
    }

    # ---- 2. 时光机自然周期回顾 ----
    next_month = start_of_this_month.replace(day=28) + datetime.timedelta(days=4)
    end_of_this_month = next_month - datetime.timedelta(days=next_month.day)

    if start_of_this_month.month == 1:
        start_of_last_month = start_of_this_month.replace(year=start_of_this_month.year - 1, month=12, day=1)
    else:
        start_of_last_month = start_of_this_month.replace(month=start_of_this_month.month - 1, day=1)
    end_of_last_month = start_of_this_month - datetime.timedelta(days=1)

    if start_of_last_month.month == 1:
        start_of_two_months_ago = start_of_last_month.replace(year=start_of_last_month.year - 1, month=12, day=1)
    else:
        start_of_two_months_ago = start_of_last_month.replace(month=start_of_last_month.month - 1, day=1)
    end_of_two_months_ago = start_of_last_month - datetime.timedelta(days=1)

    start_of_this_year = today_dt.replace(month=1, day=1)
    end_of_this_year = today_dt.replace(month=12, day=31)
    start_of_last_year = start_of_this_year.replace(year=start_of_this_year.year - 1)
    end_of_last_year = start_of_this_year - datetime.timedelta(days=1)

    def filter_logs_in_period(s_date, e_date):
        return [l for l in all_logs if l.incident_date and (s_date <= (l.incident_date.date() if isinstance(l.incident_date, datetime.datetime) else l.incident_date) <= e_date)]

    this_week_logs = filter_logs_in_period(start_of_this_week, end_of_this_week)
    last_week_logs = filter_logs_in_period(start_of_last_week, end_of_last_week)

    this_month_logs = filter_logs_in_period(start_of_this_month, today_dt)
    last_month_logs = filter_logs_in_period(start_of_last_month, end_of_last_month)
    two_months_ago_logs = filter_logs_in_period(start_of_two_months_ago, end_of_two_months_ago)

    this_year_logs = filter_logs_in_period(start_of_this_year, today_dt)
    last_year_logs = filter_logs_in_period(start_of_last_year, end_of_last_year)

    def build_period_item(logs_in_p, prev_logs_count, s_date, e_date):
        c = len(logs_in_p)
        diff = c - prev_logs_count
        high_c = 0
        mid_c = 0
        low_c = 0
        p_person_counts = {}
        for l in logs_in_p:
            score = l.dino_config.mood_score if l.dino_config and l.dino_config.mood_score is not None else 5
            if score >= 7 or l.mood_dino_id in happy_mood_ids:
                high_c += 1
            elif score <= 3 or l.mood_dino_id in sad_mood_ids:
                low_c += 1
            else:
                mid_c += 1
            for p in l.persons:
                p_person_counts[p.uuid] = p_person_counts.get(p.uuid, 0) + 1
        
        total_m = float(c)
        if c == 0:
            pcts = [0, 0, 0]
        else:
            pcts = [round(high_c / total_m * 100), round(mid_c / total_m * 100), round(low_c / total_m * 100)]
        
        all_p_objs = {p.uuid: p for l in logs_in_p for p in l.persons}
        top_p_list = []
        sorted_p_uuids = sorted(p_person_counts.keys(), key=lambda x: p_person_counts[x], reverse=True)[:3]
        for p_uuid in sorted_p_uuids:
            p_obj = all_p_objs.get(p_uuid)
            if p_obj:
                top_p_list.append({
                    "uuid": p_uuid,
                    "name": p_obj.name,
                    "count": p_person_counts[p_uuid]
                })

        return {
            "date_range_str": f"{s_date.strftime('%Y.%m.%d')} - {e_date.strftime('%Y.%m.%d')}",
            "count": c,
            "diff": diff,
            "mood_percentages": pcts,
            "top_persons": top_p_list
        }

    period_reviews = {
        "week": build_period_item(this_week_logs, len(last_week_logs), start_of_this_week, end_of_this_week),
        "month": build_period_item(this_month_logs, len(last_month_logs), start_of_this_month, end_of_this_month),
        "last_month": build_period_item(last_month_logs, len(two_months_ago_logs), start_of_last_month, end_of_last_month),
        "year": build_period_item(this_year_logs, len(last_year_logs), start_of_this_year, end_of_this_year)
    }

    # ---- 3. 关系人分类晴雨表 ----
    categories = db.query(PersonCategory).filter(
        PersonCategory.user_id == current_user.id,
        PersonCategory.is_deleted == False
    ).order_by(PersonCategory.sort_order).all()

    all_persons_db = db.query(Person).filter(
        Person.user_id == current_user.id,
        Person.is_deleted == False
    ).all()

    person_stats = {}
    for p in all_persons_db:
        p_logs = [l for l in all_logs if p.uuid in [lp.uuid for lp in l.persons]]
        happy_cnt = 0
        calm_cnt = 0
        sad_cnt = 0
        for l in p_logs:
            score = l.dino_config.mood_score if l.dino_config and l.dino_config.mood_score is not None else 5
            if score >= 7 or l.mood_dino_id in happy_mood_ids:
                happy_cnt += 1
            elif score <= 3 or l.mood_dino_id in sad_mood_ids:
                sad_cnt += 1
            else:
                calm_cnt += 1
        person_stats[p.uuid] = {
            "uuid": p.uuid,
            "name": p.name,
            "relationship": p.relationship or "朋友",
            "category_uuid": p.category_uuid,
            "diary_count": len(p_logs),
            "happy_count": happy_cnt,
            "calm_count": calm_cnt,
            "sad_count": sad_cnt
        }

    category_summaries = []
    all_person_list = list(person_stats.values())

    if categories:
        cat_person_map = {}
        for p_stat in person_stats.values():
            c_uuid = p_stat["category_uuid"] or "uncategorized"
            if c_uuid not in cat_person_map:
                cat_person_map[c_uuid] = []
            cat_person_map[c_uuid].append(p_stat)

        for cat in categories:
            c_persons = cat_person_map.get(cat.uuid, [])
            category_summaries.append({
                "uuid": cat.uuid,
                "name": cat.name,
                "persons": c_persons
            })
        
        uncategorized_persons = cat_person_map.get("uncategorized", [])
        if uncategorized_persons:
            category_summaries.append({
                "uuid": "uncategorized",
                "name": "未分类",
                "persons": uncategorized_persons
            })
    else:
        if all_person_list:
            category_summaries.append({
                "uuid": "uncategorized",
                "name": "我的伙伴",
                "persons": all_person_list
            })

    person_scores = {}
    person_counts = {}
    person_last_date = {}
    
    for log in all_logs:
        mood_id = log.mood_dino_id
        score = 0
        if mood_id in happy_mood_ids:
            score = 1
        elif mood_id in sad_mood_ids:
            score = -1
            
        for person in log.persons:
            p_uuid = person.uuid
            if p_uuid not in person_scores:
                person_scores[p_uuid] = 0
                person_counts[p_uuid] = 0
                person_last_date[p_uuid] = log.incident_date
            else:
                if log.incident_date > person_last_date[p_uuid]:
                    person_last_date[p_uuid] = log.incident_date
            
            person_scores[p_uuid] += score
            person_counts[p_uuid] += 1

    person_map = {p.uuid: p for p in all_persons_db}
    
    nodes = [{"id": "child", "name": "我", "val": 15, "category": "me", "color_tag": "amber", "happy_count": 0, "sad_count": 0}]
    links = []
    
    for p_uuid, count in person_counts.items():
        p_obj = person_map.get(p_uuid)
        if p_obj:
            friend_logs = [log for log in all_logs if p_uuid in [p.uuid for p in log.persons]]
            f_happy = sum(1 for log in friend_logs if log.mood_dino_id in happy_mood_ids)
            f_sad = sum(1 for log in friend_logs if log.mood_dino_id in sad_mood_ids)
            
            nodes.append({
                "id": p_uuid,
                "name": p_obj.name,
                "val": min(12, 4 + count),
                "category": p_obj.relationship or "朋友",
                "color_tag": p_obj.color_tag or "red",
                "happy_count": f_happy,
                "sad_count": f_sad
            })
            links.append({
                "source": "child",
                "target": p_uuid,
                "weight": count
            })
            
    happy_buddies = []
    warm_hug_buddies = []
    
    for p_uuid, score in person_scores.items():
        p_obj = person_map.get(p_uuid)
        if p_obj:
            b_info = {
                "uuid": p_uuid,
                "name": p_obj.name,
                "relationship": p_obj.relationship or "朋友",
                "score": score,
                "color_tag": p_obj.color_tag or "red"
            }
            if score > 0:
                happy_buddies.append(b_info)
            elif score < 0:
                warm_hug_buddies.append(b_info)
                
    happy_buddies.sort(key=lambda x: x["score"], reverse=True)
    warm_hug_buddies.sort(key=lambda x: x["score"])
    
    happy_buddies = happy_buddies[:5]
    warm_hug_buddies = warm_hug_buddies[:5]
    
    text_contents = [log.content for log in all_logs[:30]] + [log.own_thoughts for log in all_logs[:30] if log.own_thoughts]
    words_list = extract_high_frequency_words(text_contents)
    
    recent_logs = all_logs[:5]
    avg_score = 3.0
    if recent_logs:
        scores = []
        for l in recent_logs:
            if l.mood_dino_id in happy_mood_ids:
                scores.append(5)
            elif l.mood_dino_id in sad_mood_ids:
                scores.append(1)
            else:
                scores.append(3)
        avg_score = sum(scores) / len(scores)
        
    tips = "你的小恐龙基地一片风和日丽 ☀️！你最近一定遇到了很多好玩的事情，小伙伴们也很喜欢和你一起玩！快去给乐园解锁更多的恐龙伙伴吧！🦖✨"
    if avg_score < 2.5:
        tips = "最近小恐龙的草地上有一点下小雨 🌧️ 呢。别担心，悄悄写下日记把它们装进秘密基地，或者找喜欢的人抱抱！只要你愿意说出来，天空很快就会放晴的！🦕☔"
    elif avg_score < 4.0:
        tips = "平静普通的一天，小恐龙也在惬意地打哈欠 ⛅。继续记录你的日常点滴吧，每一个小小的脚印都是珍贵的回忆哦！🍃"
        
    if words_list:
        top_keyword = words_list[0]["text"]
        tips += f" 悄悄告诉你，你最近提到了好几次“{top_keyword}”，这似乎是你的超级焦点呢！"
        
    cinema_logs = []
    for log in all_logs:
        if len(cinema_logs) >= 10:
            break
        if log.attachments:
            has_img = any(att.mime_type.startswith("image/") for att in log.attachments)
            has_aud = any(att.mime_type.startswith("audio/") for att in log.attachments)
            if has_img or has_aud:
                atts = []
                for att in log.attachments:
                    atts.append({
                        "uuid": att.uuid,
                        "mime_type": att.mime_type,
                        "url": f"/api/attachments/download/{att.uuid}"
                    })
                clean_content = re.sub(r'\[sticker:[^\]]+\]', '', log.content).strip()
                cinema_logs.append({
                    "uuid": log.uuid,
                    "title": log.title or "无标题",
                    "content": clean_content,
                    "incident_date": log.incident_date.strftime("%Y-%m-%d %H:%M") if isinstance(log.incident_date, datetime.datetime) else str(log.incident_date),
                    "attachments": atts,
                    "mood_dino_id": log.mood_dino_id
                })
    if not cinema_logs and all_logs:
        log = all_logs[0]
        atts = []
        for att in log.attachments:
            atts.append({
                "uuid": att.uuid,
                "mime_type": att.mime_type,
                "url": f"/api/attachments/download/{att.uuid}"
            })
        clean_content = re.sub(r'\[sticker:[^\]]+\]', '', log.content).strip()
        cinema_logs.append({
            "uuid": log.uuid,
            "title": log.title or "无标题",
            "content": clean_content,
            "incident_date": log.incident_date.strftime("%Y-%m-%d %H:%M") if isinstance(log.incident_date, datetime.datetime) else str(log.incident_date),
            "attachments": atts,
            "mood_dino_id": log.mood_dino_id
        })

    return {
        "egg_energy": egg_energy_data,
        "period_reviews": period_reviews,
        "category_summaries": category_summaries,
        "mood_heatmap": mood_heatmap,
        "relationship_galaxy": {
            "nodes": nodes,
            "links": links
        },
        "friend_mood_stats": {
            "happy_buddies": happy_buddies,
            "warm_hug_buddies": warm_hug_buddies
        },
        "ai_word_cloud_tips": {
            "words": words_list,
            "tips": tips
        },
        "cinema_logs": cinema_logs
    }
