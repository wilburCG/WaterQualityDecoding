# -*- coding: utf-8 -*-
"""M3 知识种子入库：幂等（按标题匹配，存在则重建分块）。

运行：python -m app.seeds.knowledge_seed
"""
from sqlalchemy import select

from app.core.rag import ingest_doc
from app.db import SessionLocal
from app.models import KnowledgeDoc
from app.seeds.knowledge_data import KNOWLEDGE_SEED_DOCS


def run() -> None:
    db = SessionLocal()
    try:
        total_chunks = 0
        for item in KNOWLEDGE_SEED_DOCS:
            doc = db.scalar(select(KnowledgeDoc).where(
                KnowledgeDoc.title == item["title"]))
            if doc is None:
                doc = KnowledgeDoc(
                    title=item["title"],
                    source=item["source"],
                    source_url=item["source_url"],
                    category=item["category"],
                    is_published=True,
                )
                db.add(doc)
                db.flush()
            count = ingest_doc(db, doc, item["content"])
            total_chunks += count
        db.commit()
        print(f"knowledge seed done: {len(KNOWLEDGE_SEED_DOCS)} docs, "
              f"{total_chunks} chunks")
    finally:
        db.close()


if __name__ == "__main__":
    run()
