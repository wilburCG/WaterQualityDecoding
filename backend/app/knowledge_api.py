"""M3 知识库管理 API（管理员）：文档增删改 + 分块嵌入。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.rag import ingest_doc
from app.db import SessionLocal
from app.deps import require_admin
from app.models import KnowledgeDoc, User

router = APIRouter(prefix="/api/v1/admin/knowledge",
                   dependencies=[Depends(require_admin)])


class DocCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    source: str = Field(default="", max_length=128)
    source_url: str = Field(default="", max_length=512)
    category: str = Field(default="science", pattern="^(standard|science|guide)$")
    is_published: bool = True
    content: str = Field(min_length=1)


class DocUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=128)
    source: Optional[str] = Field(default=None, max_length=128)
    source_url: Optional[str] = Field(default=None, max_length=512)
    category: Optional[str] = Field(default=None,
                                    pattern="^(standard|science|guide)$")
    is_published: Optional[bool] = None
    content: Optional[str] = None  # 提供则重新分块嵌入


def _serialize(doc: KnowledgeDoc) -> dict:
    return {
        "id": doc.id,
        "title": doc.title,
        "source": doc.source,
        "source_url": doc.source_url,
        "category": doc.category,
        "is_published": doc.is_published,
        "chunk_count": doc.chunk_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.get("/docs")
def list_docs(admin: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(KnowledgeDoc).order_by(KnowledgeDoc.created_at.desc())).all()
        return [_serialize(d) for d in rows]
    finally:
        db.close()


@router.post("/docs")
def create_doc(req: DocCreate, admin: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        doc = KnowledgeDoc(
            title=req.title, source=req.source, source_url=req.source_url,
            category=req.category, is_published=req.is_published,
        )
        db.add(doc)
        db.flush()
        count = ingest_doc(db, doc, req.content)
        db.commit()
        return {**_serialize(doc), "chunk_count": count}
    finally:
        db.close()


@router.patch("/docs/{doc_id}")
def update_doc(doc_id: int, req: DocUpdate, admin: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        doc = db.get(KnowledgeDoc, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        for field in ("title", "source", "source_url", "category", "is_published"):
            value = getattr(req, field)
            if value is not None:
                setattr(doc, field, value)
        if req.content is not None:
            ingest_doc(db, doc, req.content)
        db.commit()
        return _serialize(doc)
    finally:
        db.close()


@router.delete("/docs/{doc_id}")
def delete_doc(doc_id: int, admin: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        doc = db.get(KnowledgeDoc, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        db.delete(doc)
        db.commit()
        return {"id": doc_id, "deleted": True}
    finally:
        db.close()
