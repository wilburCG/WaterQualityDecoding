"""M2 后台审核 API（先审后发）。"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api import _serialize_sample
from app.db import SessionLocal
from app.deps import require_admin
from app.models import Sample, User

router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(require_admin)])


class RejectRequest(BaseModel):
    note: str = Field(min_length=1, max_length=256)


@router.get("/samples")
def list_review_queue(
    status: Optional[str] = Query("pending", pattern="^(pending|approved|rejected)$"),
    limit: int = Query(100, ge=1, le=500),
):
    db = SessionLocal()
    try:
        stmt = (
            select(Sample)
            .options(selectinload(Sample.site), selectinload(Sample.measurements),
                     selectinload(Sample.user))
            .order_by(Sample.created_at.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Sample.review_status == status)
        rows = db.scalars(stmt).unique().all()
        result = []
        for s in rows:
            d = _serialize_sample(s, include_review=True)
            d["reviewed_at"] = s.reviewed_at.isoformat() if s.reviewed_at else None
            d["submitted_at"] = s.created_at.isoformat()
            result.append(d)
        return result
    finally:
        db.close()


def _get_sample(db, sample_id: int) -> Sample:
    s = db.get(Sample, sample_id)
    if s is None:
        raise HTTPException(status_code=404, detail="提交不存在")
    return s


@router.post("/samples/{sample_id}/approve")
def approve(sample_id: int, admin: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        s = _get_sample(db, sample_id)
        s.review_status = "approved"
        s.review_note = ""
        s.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        return {"id": s.id, "review_status": "approved"}
    finally:
        db.close()


@router.post("/samples/{sample_id}/reject")
def reject(sample_id: int, req: RejectRequest,
           admin: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        s = _get_sample(db, sample_id)
        s.review_status = "rejected"
        s.review_note = req.note
        s.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        return {"id": s.id, "review_status": "rejected", "review_note": req.note}
    finally:
        db.close()
