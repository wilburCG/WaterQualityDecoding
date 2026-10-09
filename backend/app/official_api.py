# -*- coding: utf-8 -*-
"""M5 官方监测数据 API：公开断面/对照 + 管理员批量导入。"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.official import (
    CandidateReading,
    CandidateSection,
    compare,
)
from app.db import SessionLocal
from app.deps import get_current_user, require_admin
from app.models import Indicator, OfficialReading, OfficialSection, User

public_router = APIRouter(prefix="/api/v1")
admin_router = APIRouter(prefix="/api/v1/admin/official",
                         dependencies=[Depends(require_admin)])


def _parse_dt(raw: str) -> datetime:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"时间格式无法解析：{raw}")


def _section_summary(s: OfficialSection, latest: Optional[OfficialReading]) -> dict:
    return {
        "id": s.id,
        "code": s.code,
        "name": s.name,
        "river": s.river,
        "lng": float(s.lng),
        "lat": float(s.lat),
        "level": s.level,
        "source_org": s.source_org,
        "latest": (
            {
                "observed_at": latest.observed_at.isoformat(),
                "overall_grade": latest.overall_grade,
                "source": latest.source,
                "note": latest.note,
            }
            if latest else None
        ),
    }


# ---------------------------------------------------------------------------
# 公开
# ---------------------------------------------------------------------------
@public_router.get("/official/sections")
def list_sections(river: Optional[str] = None):
    db = SessionLocal()
    try:
        stmt = select(OfficialSection).where(OfficialSection.is_active.is_(True))
        if river:
            stmt = stmt.where(OfficialSection.river.ilike(f"%{river}%"))
        sections = db.scalars(stmt).all()
        result = []
        for s in sections:
            latest = db.scalar(
                select(OfficialReading)
                .where(OfficialReading.section_id == s.id)
                .order_by(OfficialReading.observed_at.desc())
                .limit(1))
            result.append(_section_summary(s, latest))
        return result
    finally:
        db.close()


class CompareRequest(BaseModel):
    lng: float
    lat: float
    sampled_at: str  # ISO
    values: dict[str, float]
    radius_km: float = Field(default=8.0, ge=0.5, le=50)
    max_days: int = Field(default=21, ge=1, le=365)


@public_router.post("/compare")
def compare_official(req: CompareRequest):
    db = SessionLocal()
    try:
        sections = db.scalars(
            select(OfficialSection)
            .where(OfficialSection.is_active.is_(True))
            .options(selectinload(OfficialSection.readings))
        ).unique().all()

        candidates = [
            CandidateSection(
                code=s.code, name=s.name, river=s.river,
                lng=float(s.lng), lat=float(s.lat),
                level=s.level, source_org=s.source_org,
                readings=[
                    CandidateReading(
                        observed_at=r.observed_at,
                        values=r.values,
                        overall_grade=r.overall_grade,
                        source=r.source,
                        source_url=r.source_url,
                        note=r.note,
                    )
                    for r in s.readings
                ],
            )
            for s in sections
        ]
        indicator_meta = {
            i.code: {"name": i.name, "unit": i.unit}
            for i in db.scalars(select(Indicator)).all()
        }
        result = compare(
            lng=req.lng, lat=req.lat,
            sampled_at=_parse_dt(req.sampled_at),
            values=req.values,
            sections=candidates,
            indicator_meta=indicator_meta,
            radius_km=req.radius_km,
            max_days=req.max_days,
        )
        if not result["matches"]:
            result["empty_note"] = (
                "附近暂时没有可对照的官方断面数据（受距离与时间窗口限制），"
                "可在地图查看已收录的官方断面，或稍后再来。")
        return result
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 管理员：断面与读数导入
# ---------------------------------------------------------------------------
class SectionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    river: str = ""
    lng: float
    lat: float
    level: str = "市控"
    source_org: str = ""
    is_active: bool = True


@admin_router.get("/sections")
def admin_list_sections(user: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        rows = db.scalars(select(OfficialSection)).all()
        return [_section_summary(s, None) for s in rows]
    finally:
        db.close()


@admin_router.post("/sections")
def admin_create_section(req: SectionCreate, user: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        if db.scalar(select(OfficialSection).where(
                OfficialSection.code == req.code)):
            raise HTTPException(status_code=400, detail="断面编号已存在")
        s = OfficialSection(**req.model_dump())
        db.add(s)
        db.commit()
        return _section_summary(s, None)
    finally:
        db.close()


@admin_router.delete("/sections/{code}")
def admin_delete_section(code: str, user: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        s = db.scalar(select(OfficialSection).where(
            OfficialSection.code == code))
        if s is None:
            raise HTTPException(status_code=404, detail="断面不存在")
        db.delete(s)
        db.commit()
        return {"code": code, "deleted": True}
    finally:
        db.close()


class ReadingItem(BaseModel):
    observed_at: str
    values: dict[str, float]
    overall_grade: Optional[int] = Field(default=None, ge=1, le=6)
    source: str = ""
    source_url: str = ""
    note: str = ""


class ReadingBulk(BaseModel):
    section_code: str
    readings: list[ReadingItem] = Field(min_length=1, max_length=500)


@admin_router.post("/readings/bulk")
def admin_bulk_readings(req: ReadingBulk, user: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        section = db.scalar(select(OfficialSection).where(
            OfficialSection.code == req.section_code))
        if section is None:
            raise HTTPException(status_code=404, detail="断面不存在")

        inserted = 0
        for item in req.readings:
            observed_at = _parse_dt(item.observed_at)
            existing = db.scalar(
                select(OfficialReading).where(
                    OfficialReading.section_id == section.id,
                    OfficialReading.observed_at == observed_at))
            if existing is not None:
                # 同时间点读数：覆盖更新
                existing.values = item.values
                existing.overall_grade = item.overall_grade
                existing.source = item.source
                existing.source_url = item.source_url
                existing.note = item.note
            else:
                db.add(OfficialReading(
                    section_id=section.id,
                    observed_at=observed_at,
                    values=item.values,
                    overall_grade=item.overall_grade,
                    source=item.source,
                    source_url=item.source_url,
                    note=item.note,
                ))
                inserted += 1
        db.commit()
        return {"section_code": req.section_code,
                "inserted": inserted,
                "total_readings": len(section.readings)}
    finally:
        db.close()
