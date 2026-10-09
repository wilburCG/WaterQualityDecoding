# -*- coding: utf-8 -*-
"""M5 订阅通知：匹配订阅者 / 构建通知 / 审核通过时 fanout。"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Notification, Sample, Subscription

GRADE_NAMES = {1: "Ⅰ类", 2: "Ⅱ类", 3: "Ⅲ类", 4: "Ⅳ类", 5: "Ⅴ类", 6: "劣Ⅴ类"}


def match_subscriptions(subs: list[Subscription], river: str,
                        site_id: int) -> list[Subscription]:
    """纯逻辑：订阅该河流或该点位的订阅者。"""
    out = []
    for s in subs:
        if s.target_type == "river" and s.target_key == river:
            out.append(s)
        elif s.target_type == "site" and s.target_key == str(site_id):
            out.append(s)
    return out


def build_notification(sub: Subscription, sample: Sample) -> Notification:
    river = sample.site.river or "未知河流"
    site_name = sample.site.name
    grade = sample.overall_grade
    grade_text = GRADE_NAMES.get(grade, "未评级")
    link = f"/map?sample={sample.id}"

    is_alert = grade is not None and grade >= sub.alert_grade_from
    if is_alert:
        kind = "grade_alert"
        title = f"⚠️ {river} 水质预警：{grade_text}"
        body = f"{site_name} 新发布的检测综合水质为{grade_text}，请注意相关风险（科普参考，非官方结论）。"
    else:
        kind = "new_data"
        title = f"🌊 {river} 有新的检测数据"
        body = f"{site_name} 新发布了一份检测数据，综合水质 {grade_text}，来看看吧。"
    return Notification(user_id=sub.user_id, kind=kind, title=title,
                        body=body, link=link, is_read=False)


def fanout_for_sample(db, sample: Sample) -> int:
    """审核通过后调用：给匹配订阅者生成通知。返回生成条数。"""
    subs = db.scalars(select(Subscription)).all()
    matched = match_subscriptions(subs, sample.site.river, sample.site_id)

    created = 0
    for sub in matched:
        db.add(build_notification(sub, sample))
        created += 1
    return created
