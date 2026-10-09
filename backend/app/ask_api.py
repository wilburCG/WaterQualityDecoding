"""M3 知识问答 API：检索 → 生成 → 强制引用，含免费额度控制。"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.llm import chat_completion
from app.core.rag import (
    SYSTEM_PROMPT,
    build_user_prompt,
    citations_payload,
    retrieve,
)
from app.db import SessionLocal
from app.deps import get_optional_user
from app.models import AskQuery, User
from app.config import get_settings

router = APIRouter(prefix="/api/v1")

SUGGESTED_QUESTIONS = [
    "水质的Ⅰ-Ⅴ类是怎么划分的？",
    "溶解氧低说明什么？",
    "河水发绿、有异味是什么原因？",
    "自来水烧开有水垢正常吗？",
]

NO_EVIDENCE = "抱歉，现有知识库中没有找到能回答这个问题的可靠依据。你可以换个说法，或试试下面的问题。"


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    client_id: str = Field(default="", max_length=64)  # 未登录时的匿名标识


def _today_range() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    return start, now


@router.post("/ask")
async def ask(req: AskRequest, user: Optional[User] = Depends(get_optional_user)):
    settings = get_settings()
    db = SessionLocal()
    try:
        # 额度统计
        start, now = _today_range()
        if user is not None:
            quota = settings.ask_user_daily
            count_stmt = select(func.count(AskQuery.id)).where(
                AskQuery.user_id == user.id, AskQuery.created_at >= start)
        else:
            quota = settings.ask_anonymous_daily
            cid = req.client_id.strip()
            if not cid:
                raise HTTPException(status_code=400, detail="缺少 client_id")
            count_stmt = select(func.count(AskQuery.id)).where(
                AskQuery.user_id.is_(None), AskQuery.client_id == cid,
                AskQuery.created_at >= start)
        used = db.scalar(count_stmt) or 0
        if used >= quota:
            raise HTTPException(
                status_code=429,
                detail=f"今日免费提问已达上限（{quota} 次），登录后额度更高，明天再来试试～",
            )

        refs = retrieve(db, req.question)
        if not refs:
            answer = NO_EVIDENCE
            citations: list[dict] = []
        else:
            answer = await chat_completion(
                SYSTEM_PROMPT, build_user_prompt(req.question, refs))
            citations = citations_payload(refs)

        record = AskQuery(
            user_id=user.id if user else None,
            client_id="" if user else req.client_id.strip(),
            question=req.question,
            answer=answer,
            citations=citations,
        )
        db.add(record)
        db.commit()

        return {
            "answer": answer,
            "citations": citations,
            "suggested_questions": SUGGESTED_QUESTIONS if not refs else None,
            "quota": {"used": used + 1, "limit": quota,
                      "remaining": max(0, quota - used - 1)},
        }
    finally:
        db.close()
