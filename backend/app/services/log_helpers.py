import datetime
from typing import List, Dict, Any
from sqlalchemy import or_, desc
from sqlalchemy.orm import Session
from ..models import Log, Attachment, User, Person, PersonCategory, DinoConfig, log_person_association


def get_logs_stats_overview_service(db: Session, current_user: User) -> dict:
    """
    计算日志全量统计、热力图、蛋能量四象限、关系星系图与 AI 关怀分析
    """
    happy_mood_ids = {1, 2, 3, 4}
    sad_mood_ids = {7, 8, 9, 10, 11}
    
    # 1. 查询元数据
    logs_meta = db.query(
        Log.id,
        Log.uuid,
        Log.incident_date,
        Log.mood_dino_id,
        DinoConfig.mood_score
    ).outerjoin(
        DinoConfig, Log.mood_dino_id == DinoConfig.id
    ).filter(
        Log.user_id == current_user.id,
        Log.is_deleted == False
    ).order_by(desc(Log.incident_date)).all()

    # 2. 获取包含多媒体附件的日志 ID
    media_log_ids = set(
        r[0] for r in db.query(Attachment.log_id).filter(
            Attachment.log_id.isnot(None),
            or_(
                Attachment.mime_type.like("image/%"),
                Attachment.mime_type.like("audio/%"),
                Attachment.mime_type.like("video/%")
            )
        ).all()
    )

    # 3. 热力图生成
    date_mood_map = {}
    for log_id, log_uuid, incident_date, mood_dino_id, mood_score in reversed(logs_meta):
        try:
            day_str = incident_date.strftime("%Y-%m-%d")
            date_mood_map[day_str] = mood_dino_id
        except Exception:
            pass
            
    sorted_days = sorted(date_mood_map.keys(), reverse=True)[:30]
    mood_heatmap = [{"date": day, "mood": date_mood_map[day]} for day in reversed(sorted_days)]

    # 4. 蛋能量四象限增量与结余计算
    today_dt = datetime.date.today()
    start_of_this_week = today_dt - datetime.timedelta(days=today_dt.weekday())
    end_of_this_week = start_of_this_week + datetime.timedelta(days=6)
    start_of_last_week = start_of_this_week - datetime.timedelta(days=7)
    end_of_last_week = start_of_this_week - datetime.timedelta(days=1)
    start_of_this_month = today_dt.replace(day=1)
    if today_dt.month == 12:
        next_month_start = today_dt.replace(year=today_dt.year + 1, month=1, day=1)
    else:
        next_month_start = today_dt.replace(month=today_dt.month + 1, day=1)
    end_of_this_month = next_month_start - datetime.timedelta(days=1)
    
    first_of_this_month = start_of_this_month
    last_day_of_last_month = first_of_this_month - datetime.timedelta(days=1)
    start_of_last_month = last_day_of_last_month.replace(day=1)
    end_of_last_month = last_day_of_last_month

    first_of_last_month = start_of_last_month
    last_day_of_two_months_ago = first_of_last_month - datetime.timedelta(days=1)
    start_of_two_months_ago = last_day_of_two_months_ago.replace(day=1)
    end_of_two_months_ago = last_day_of_two_months_ago

    start_of_this_year = today_dt.replace(month=1, day=1)
    end_of_this_year = today_dt.replace(month=12, day=31)
    start_of_last_year = start_of_this_year.replace(year=today_dt.year - 1)
    end_of_last_year = start_of_this_year - datetime.timedelta(days=1)

    def calc_energy_in_period(s_date, e_date):
        base_e = 0
        bonus_e = 0
        for log_id, log_uuid, incident_date, mood_dino_id, mood_score in logs_meta:
            if incident_date:
                dt_val = incident_date.date() if isinstance(incident_date, datetime.datetime) else incident_date
                if s_date <= dt_val <= e_date:
                    base_e += 10
                    if log_id in media_log_ids:
                        bonus_e += 20
        return base_e, bonus_e

    t_base, t_bonus = calc_energy_in_period(today_dt, today_dt)
    w_base, w_bonus = calc_energy_in_period(start_of_this_week, end_of_this_week)
    lw_base, lw_bonus = calc_energy_in_period(start_of_last_week, end_of_last_week)
    m_base, m_bonus = calc_energy_in_period(start_of_this_month, today_dt)
    lm_base, lm_bonus = calc_energy_in_period(start_of_last_month, end_of_last_month)
    y_base, y_bonus = calc_energy_in_period(start_of_this_year, today_dt)
    ly_base, ly_bonus = calc_energy_in_period(start_of_last_year, end_of_last_year)

    today_total = t_base + t_bonus
    this_week_total = w_base + w_bonus
    last_week_total = lw_base + lw_bonus
    this_month_total = m_base + m_bonus

    egg_energy_data = {
        "balance": current_user.egg_energy or 0,
        "today": today_total,
        "this_week": this_week_total,
        "last_week": last_week_total,
        "this_month": this_month_total,
        "week": {
            "base_energy": w_base,
            "bonus_energy": w_bonus,
            "total": this_week_total,
            "prev_total": last_week_total
        },
        "month": {
            "base_energy": m_base,
            "bonus_energy": m_bonus,
            "total": this_month_total,
            "prev_total": lm_base + lm_bonus
        },
        "year": {
            "base_energy": y_base,
            "bonus_energy": y_bonus,
            "total": y_base + y_bonus,
            "prev_total": ly_base + ly_bonus
        }
    }

    # 5. 人物映射与关联（基于 log_uuid 和 person_uuid）
    persons_list = db.query(Person).filter(
        Person.user_id == current_user.id,
        Person.is_deleted == False
    ).all()
    person_map = {p.uuid: p for p in persons_list}

    user_log_uuids = [l[1] for l in logs_meta if l[1]]
    log_uuid_to_id_map = {l[1]: l[0] for l in logs_meta if l[1]}
    log_id_to_uuid_map = {l[0]: l[1] for l in logs_meta if l[1]}

    associations = []
    if user_log_uuids:
        associations = db.query(
            log_person_association.c.person_uuid,
            log_person_association.c.log_uuid
        ).filter(
            log_person_association.c.log_uuid.in_(user_log_uuids)
        ).all()

    log_persons = {}
    for p_uuid, log_uuid in associations:
        log_id = log_uuid_to_id_map.get(log_uuid)
        if log_id is not None:
            if log_id not in log_persons:
                log_persons[log_id] = []
            log_persons[log_id].append(p_uuid)

    # 6. Period Reviews
    def filter_logs_in_period(s_date, e_date):
        return [
            (log_id, log_uuid, incident_date, mood_dino_id, mood_score)
            for log_id, log_uuid, incident_date, mood_dino_id, mood_score in logs_meta
            if incident_date and s_date <= (incident_date.date() if isinstance(incident_date, datetime.datetime) else incident_date) <= e_date
        ]

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
        for log_id, log_uuid, incident_date, mood_dino_id, mood_score in logs_in_p:
            score = mood_score if mood_score is not None else 5
            if score >= 7 or mood_dino_id in happy_mood_ids:
                high_c += 1
            elif score <= 3 or mood_dino_id in sad_mood_ids:
                low_c += 1
            else:
                mid_c += 1
            
            p_uuids = log_persons.get(log_id, [])
            for p_uuid in p_uuids:
                p_person_counts[p_uuid] = p_person_counts.get(p_uuid, 0) + 1
        
        total_m = float(c)
        if c == 0:
            pcts = [0, 0, 0]
        else:
            pcts = [round(high_c / total_m * 100), round(mid_c / total_m * 100), round(low_c / total_m * 100)]
        
        top_p_list = []
        sorted_p_uuids = sorted(p_person_counts.keys(), key=lambda x: p_person_counts[x], reverse=True)[:3]
        for p_uuid in sorted_p_uuids:
            p_obj = person_map.get(p_uuid)
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

    # 7. 人物分类与星系图
    person_stats = {}
    for p in persons_list:
        person_stats[p.uuid] = {
            "uuid": p.uuid,
            "name": p.name,
            "relationship": p.relationship or "朋友",
            "category_uuid": p.category_uuid,
            "diary_count": 0,
            "happy_count": 0,
            "calm_count": 0,
            "sad_count": 0
        }

    log_details_map = {log_id: (mood_dino_id, mood_score, incident_date) for log_id, log_uuid, incident_date, mood_dino_id, mood_score in logs_meta}

    person_scores = {}
    person_counts = {}
    person_last_date = {}
    
    for person_uuid, log_uuid in associations:
        log_id = log_uuid_to_id_map.get(log_uuid)
        if log_id in log_details_map:
            mood_dino_id, mood_score, incident_date = log_details_map[log_id]
            
            if person_uuid in person_stats:
                stats = person_stats[person_uuid]
                stats["diary_count"] += 1
                score = mood_score if mood_score is not None else 5
                if score >= 7 or mood_dino_id in happy_mood_ids:
                    stats["happy_count"] += 1
                elif score <= 3 or mood_dino_id in sad_mood_ids:
                    stats["sad_count"] += 1
                else:
                    stats["calm_count"] += 1
            
            score_val = 0
            if mood_dino_id in happy_mood_ids:
                score_val = 1
            elif mood_dino_id in sad_mood_ids:
                score_val = -1
                
            if person_uuid not in person_scores:
                person_scores[person_uuid] = 0
                person_counts[person_uuid] = 0
                person_last_date[person_uuid] = incident_date
            else:
                if incident_date and person_last_date[person_uuid] and incident_date > person_last_date[person_uuid]:
                    person_last_date[person_uuid] = incident_date
            
            person_scores[person_uuid] += score_val
            person_counts[person_uuid] += 1

    categories = db.query(PersonCategory).filter(
        PersonCategory.user_id == current_user.id,
        PersonCategory.is_deleted == False
    ).order_by(PersonCategory.sort_order).all()

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
                "name": "其他",
                "persons": uncategorized_persons
            })
    else:
        if all_person_list:
            category_summaries.append({
                "uuid": "uncategorized",
                "name": "我的伙伴",
                "persons": all_person_list
            })

    # 星系图
    nodes = [{"id": "child", "name": "我", "val": 15, "category": "me", "color_tag": "amber", "happy_count": 0, "sad_count": 0}]
    links = []
    
    for p_uuid, count in person_counts.items():
        p_obj = person_map.get(p_uuid)
        if p_obj:
            stats = person_stats.get(p_uuid, {})
            nodes.append({
                "id": p_uuid,
                "name": p_obj.name,
                "val": min(12, 4 + count),
                "category": p_obj.relationship or "朋友",
                "color_tag": p_obj.color_tag or "red",
                "happy_count": stats.get("happy_count", 0),
                "sad_count": stats.get("sad_count", 0)
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
    
    # 8. AI 关怀提示
    recent_scores = []
    for log_id, log_uuid, incident_date, mood_dino_id, mood_score in logs_meta[:5]:
        if mood_dino_id in happy_mood_ids:
            recent_scores.append(5)
        elif mood_dino_id in sad_mood_ids:
            recent_scores.append(1)
        else:
            recent_scores.append(3)
            
    avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else 3.0
    
    tips = "你的小恐龙基地一片风和日丽 ☀️！你最近一定遇到了很多好玩的事情，小伙伴们也很喜欢和你一起玩！快去给乐园解锁更多的恐龙伙伴吧！🦖✨"
    if avg_score < 2.5:
        tips = "最近小恐龙的草地有一点下小雨 🌧️ 呢。别担心，悄悄写下日记把它们装进秘密基地，或者找喜欢的人抱抱！只要你愿意说出来，天空很快就会放晴的！🦕☔"
    elif avg_score < 4.0:
        tips = "平静普通的一天，小恐龙也在惬意地打哈欠 ⛅。继续记录你的日常点滴吧，每一个小小的脚印都是珍贵的回忆哦！🍃"
        
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
            "words": [],
            "tips": tips
        },
        "cinema_logs": []
    }
