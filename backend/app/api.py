"""API：实时解码、检测分享提交、众包数据、指标百科、同汾泾案例。"""
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.content import GRADE_STATUS, GRADE_SUMMARY
from app.core.grading import grade_section
from app.db import SessionLocal
from app.deps import get_current_user
from app.models import Indicator, Measurement, Sample, Site, User

router = APIRouter(prefix="/api/v1")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class DecodeRequest(BaseModel):
    values: Dict[str, float] = Field(default_factory=dict)


class SaveSampleRequest(BaseModel):
    river: str = ""
    site_name: str = Field(min_length=1, max_length=64)
    lng: Optional[float] = None
    lat: Optional[float] = None
    sampled_at: datetime
    method_level: int = 2
    method_note: str = ""
    fuzzy_location: bool = False  # 模糊坐标（约 1 km 网格，保护私宅点位）
    values: Dict[str, float] = Field(default_factory=dict)


def _fuzzy_coord(v: float) -> float:
    """约 1 km 网格模糊化（上海纬度 0.01°≈1.1km）。"""
    return round(v, 2)


# ---------------------------------------------------------------------------
# 序列化
# ---------------------------------------------------------------------------
def _serialize_grade(result):
    return {
        "overall_grade": result.overall_grade,
        "overall_label": result.overall_label,
        "grade_status": GRADE_STATUS.get(result.overall_grade) if result.overall_grade else None,
        "summary": GRADE_SUMMARY.get(result.overall_grade) if result.overall_grade else None,
        "deciding_factors": result.deciding_factors,
        "unknown_indicators": result.unknown_indicators,
        "boundary_non_compliant": result.non_compliant_boundary,
        "error": result.error,
        "items": {
            code: {
                "code": it.code,
                "name": it.name,
                "value": it.value,
                "unit": it.unit,
                "grade": it.grade,
                "grade_status": GRADE_STATUS.get(it.grade) if it.grade else None,
                "compliant": it.compliant,
                "limit_value": it.limit_value,
                "exceed_ratio": it.exceed_ratio,
            }
            for code, it in result.items.items()
        },
    }


# ---------------------------------------------------------------------------
# 解码
# ---------------------------------------------------------------------------
@router.post("/decode")
def decode(req: DecodeRequest):
    result = grade_section(req.values)
    return _serialize_grade(result)


# ---------------------------------------------------------------------------
# 提交检测分享（M2：需登录，先审后发）
# ---------------------------------------------------------------------------
@router.post("/samples", status_code=201)
def save_sample(req: SaveSampleRequest, user: User = Depends(get_current_user)):
    result = grade_section(req.values)
    if result.error == "no_data":
        raise HTTPException(status_code=400, detail="没有可评价的指标数据")

    lng = req.lng
    lat = req.lat
    if lng is not None and lat is not None and req.fuzzy_location:
        lng, lat = _fuzzy_coord(lng), _fuzzy_coord(lat)

    db = SessionLocal()
    try:
        stmt = select(Site).where(Site.name == req.site_name)
        if req.river:
            stmt = stmt.where(Site.river == req.river)
        site = db.scalar(stmt)
        if site is None:
            if lng is None or lat is None:
                raise HTTPException(status_code=400,
                                    detail="新点位需要提供经纬度坐标")
            site = Site(name=req.site_name, river=req.river, lng=lng, lat=lat)
            db.add(site)
            db.flush()

        sample = Sample(
            user_id=user.id,
            site_id=site.id,
            sampled_at=req.sampled_at,
            method_level=req.method_level,
            method_note=req.method_note,
            overall_grade=result.overall_grade,
            deciding_factors=result.deciding_factors,
            review_status="pending",
        )
        db.add(sample)
        db.flush()
        for code, value in req.values.items():
            item = result.items.get(code)
            db.add(Measurement(sample_id=sample.id, indicator_code=code, value=value,
                               grade=item.grade if item else None))
        db.commit()
        return {"id": sample.id, "review_status": "pending",
                "message": "已提交，审核通过后将出现在河流地图",
                **_serialize_grade(result)}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 众包数据（公开地图：仅 approved；我的提交：全部状态）
# ---------------------------------------------------------------------------
def _serialize_sample(s: Sample, include_review: bool = False) -> dict:
    data = {
        "id": s.id,
        "sampled_at": s.sampled_at.isoformat(),
        "method_level": s.method_level,
        "method_note": s.method_note,
        "overall_grade": s.overall_grade,
        "deciding_factors": s.deciding_factors,
        "contributor": s.user.display_name if s.user else None,
        "site": {
            "id": s.site.id,
            "name": s.site.name,
            "river": s.site.river,
            "lng": float(s.site.lng),
            "lat": float(s.site.lat),
        },
        "measurements": [
            {"code": m.indicator_code, "value": float(m.value), "grade": m.grade}
            for m in s.measurements
        ],
    }
    if include_review:
        data["review_status"] = s.review_status
        data["review_note"] = s.review_note
    return data


@router.get("/samples")
def list_public_samples(
    grade: Optional[int] = Query(None, ge=1, le=6),
    method_level: Optional[int] = Query(None, ge=1, le=4),
    river: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = Query(500, ge=1, le=1000),
):
    """地图数据源：仅审核通过的公开数据。"""
    db = SessionLocal()
    try:
        stmt = (
            select(Sample)
            .where(Sample.review_status == "approved")
            .options(selectinload(Sample.site), selectinload(Sample.measurements),
                     selectinload(Sample.user))
            .order_by(Sample.sampled_at.desc())
            .limit(limit)
        )
        if grade is not None:
            stmt = stmt.where(Sample.overall_grade == grade)
        if method_level is not None:
            stmt = stmt.where(Sample.method_level == method_level)
        if river:
            stmt = stmt.join(Site).where(Site.river.ilike(f"%{river}%"))
        if since is not None:
            stmt = stmt.where(Sample.sampled_at >= since)
        rows = db.scalars(stmt).unique().all()
        return [_serialize_sample(s) for s in rows]
    finally:
        db.close()


@router.get("/samples/mine")
def list_my_samples(user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        stmt = (
            select(Sample)
            .where(Sample.user_id == user.id)
            .options(selectinload(Sample.site), selectinload(Sample.measurements),
                     selectinload(Sample.user))
            .order_by(Sample.created_at.desc())
        )
        rows = db.scalars(stmt).unique().all()
        return [_serialize_sample(s, include_review=True) for s in rows]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 指标百科
# ---------------------------------------------------------------------------
@router.get("/indicators")
def list_indicators():
    db = SessionLocal()
    try:
        rows = db.scalars(select(Indicator).order_by(Indicator.code)).all()
        return [{"code": r.code, "name": r.name, "unit": r.unit,
                 "direction": r.direction} for r in rows]
    finally:
        db.close()


@router.get("/indicators/{code}")
def get_indicator(code: str):
    db = SessionLocal()
    try:
        obj = db.get(Indicator, code)
        if obj is None:
            raise HTTPException(status_code=404, detail="indicator not found")
        limits = {}
        from app.models import StandardLimit
        rows = db.scalars(
            select(StandardLimit).where(StandardLimit.indicator_code == code)
            .order_by(StandardLimit.grade)
        ).all()
        limits = [{"grade": r.grade, "limit_value": float(r.limit_value)} for r in rows]
        return {"code": obj.code, "name": obj.name, "unit": obj.unit,
                "direction": obj.direction, "wiki": obj.wiki, "limits": limits}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 同汾泾案例
# ---------------------------------------------------------------------------
CASE_NARRATIVE = {
    "title": "同汾泾：一条 2 公里小河的自白",
    "river": "同汾泾（川杨河支流，全长 2.07 公里，上海浦东浦三路附近）",
    "authors": "胡同学、程同学（公民科学参与者）",
    "intro": (
        "夏天家门口的小河为什么会浑浊、发绿、有味道？两位青少年公民科学参与者，"
        "在河道上、中、下游三个断面开展现场监测，并将水样送到专业实验室分析，"
        "用数据给小河照了一张「CT」。"
    ),
    "mechanisms": [
        {
            "name": "夜晚为什么会变浑？",
            "text": "白天表层水被太阳晒热，和底层水形成热分层；入夜后表层降温，"
                    "分层被破坏，上下水体混合，底层的悬浮物和污染物被带到水面——"
                    "清晨的河水就变浑了。",
        },
        {
            "name": "河水为什么会发绿、发臭？",
            "text": "上游总磷平均超标约 1.1 倍、总氮平均超标约 1.9 倍。氮磷是藻类的"
                    "「养料」，富营养化使藻类暴发，河水发绿；藻类死亡后沉入水底腐烂，"
                    "消耗氧气并产生异味，河底长期处于厌氧状态。",
        },
        {
            "name": "小河如何自己「洗干净」？",
            "text": "上游来水在 Ⅴ 类甚至劣 Ⅴ 类，但经过约 2 公里的流动、沉降与生物"
                    "净化，下游在两次监测中都稳定达到 Ⅲ 类——小微水体虽脆弱，也具备"
                    "可观的自净能力。",
        },
    ],
}


@router.get("/cases/tongfenjing")
def tongfenjing_case():
    db = SessionLocal()
    try:
        stmt = (
            select(Sample)
            .join(Site, Site.id == Sample.site_id)
            .where(Site.river.in_(["同汾泾", "三林塘港"]))
            .options(selectinload(Sample.site), selectinload(Sample.measurements))
            .order_by(Sample.sampled_at)
        )
        samples = db.scalars(stmt).unique().all()

        data = []
        for s in samples:
            data.append({
                "sample_id": s.id,
                "sampled_at": s.sampled_at.isoformat(),
                "site_name": s.site.name,
                "method_level": s.method_level,
                "overall_grade": s.overall_grade,
                "deciding_factors": s.deciding_factors,
                "measurements": [
                    {"code": m.indicator_code, "value": float(m.value), "grade": m.grade}
                    for m in s.measurements
                ],
            })
        return {"narrative": CASE_NARRATIVE, "samples": data}
    finally:
        db.close()
