# -*- coding: utf-8 -*-
"""M5 用户端：我的订阅 / 通知中心。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import distinct, func, select

from app.db import SessionLocal
from app.deps import get_current_user
from app.models import Notification, Sample, Site, Subscription, User

router = APIRouter(prefix="/api/v1")


# ---------------------------------------------------------------------------
# 可订阅的河流列表（有审核通过数据的河流，去重）
# ---------------------------------------------------------------------------
@router.get("/rivers")
def list_known_rivers(user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.execute(
            select(Site.river, func.count(distinct(Sample.id)))
            .join(Sample, Sample.site_id == Site.id)
            .where(Sample.review_status == "approved", Site.river != "")
            .group_by(Site.river)
            .order_by(Site.river)
        ).all()
        subscribed = {
            (s.target_type, s.target_key)
            for s in db.scalars(select(Subscription).where(
                Subscription.user_id == user.id)).all()
        }
        return [
            {
                "river": river,
                "sample_count": count,
                "subscribed": ("river", river) in subscribed,
            }
            for river, count in rows
        ]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 订阅管理
# ---------------------------------------------------------------------------
class SubscribeRequest(BaseModel):
    target_type: str = Field(pattern="^(river|site)$")
    target_key: str = Field(min_length=1, max_length=64)
    target_label: str = Field(default="", max_length=64)
    alert_grade_from: int = Field(default=4, ge=1, le=6)


@router.get("/subscriptions")
def list_my_subscriptions(user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .order_by(Subscription.created_at.desc())
        ).all()
        return [
            {
                "id": s.id,
                "target_type": s.target_type,
                "target_key": s.target_key,
                "target_label": s.target_label,
                "alert_grade_from": s.alert_grade_from,
                "created_at": s.created_at.isoformat(),
            }
            for s in rows
        ]
    finally:
        db.close()


@router.post("/subscriptions", status_code=201)
def subscribe(req: SubscribeRequest, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        existing = db.scalar(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.target_type == req.target_type,
                Subscription.target_key == req.target_key))
        if existing is not None:
            raise HTTPException(status_code=400, detail="已经订阅过了")

        label = req.target_label
        if not label:
            if req.target_type == "river":
                label = req.target_key
            else:
                site = db.get(Site, int(req.target_key))
                label = site.name if site else req.target_key

        s = Subscription(
            user_id=user.id,
            target_type=req.target_type,
            target_key=req.target_key,
            target_label=label,
            alert_grade_from=req.alert_grade_from,
        )
        db.add(s)
        db.commit()
        return {"id": s.id, "message": "订阅成功，有新数据或水质预警会通知你"}
    except ValueError:
        raise HTTPException(status_code=400, detail="点位 id 无效")
    finally:
        db.close()


@router.delete("/subscriptions/{sub_id}")
def unsubscribe(sub_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        s = db.get(Subscription, sub_id)
        if s is None or s.user_id != user.id:
            raise HTTPException(status_code=404, detail="订阅不存在")
        db.delete(s)
        db.commit()
        return {"id": sub_id, "deleted": True}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 通知
# ---------------------------------------------------------------------------
@router.get("/notifications")
def list_notifications(limit: int = Query(default=50, ge=1, le=200),
                       user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        ).all()
        unread = db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id,
                Notification.is_read.is_(False)))
        return {
            "unread": unread,
            "items": [
                {
                    "id": n.id,
                    "kind": n.kind,
                    "title": n.title,
                    "body": n.body,
                    "link": n.link,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in rows
            ],
        }
    finally:
        db.close()


@router.get("/notifications/unread-count")
def unread_count(user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        count = db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id,
                Notification.is_read.is_(False)))
        return {"unread": count}
    finally:
        db.close()


class ReadRequest(BaseModel):
    ids: Optional[list[int]] = None  # 空/不传 = 全部已读


@router.post("/notifications/read")
def mark_read(req: ReadRequest, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        stmt = select(Notification).where(
            Notification.user_id == user.id,
            Notification.is_read.is_(False))
        if req.ids:
            stmt = stmt.where(Notification.id.in_(req.ids))
        rows = db.scalars(stmt).all()
        for n in rows:
            n.is_read = True
        db.commit()
        return {"updated": len(rows)}
    finally:
        db.close()
