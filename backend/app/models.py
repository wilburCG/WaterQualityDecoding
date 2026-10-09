"""M1 数据模型：指标字典 / 限值 / 点位 / 检测分享 / 测量值。"""
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Float,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Indicator(Base):
    __tablename__ = "indicator"

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    unit: Mapped[str] = mapped_column(String(16), default="")
    direction: Mapped[str] = mapped_column(String(8))  # range / ge / le
    wiki: Mapped[dict] = mapped_column(JSON, default=dict)


class StandardLimit(Base):
    __tablename__ = "standard_limit"
    __table_args__ = (
        UniqueConstraint("indicator_code", "standard_no", "water_body_type", "grade",
                         name="uq_standard_limit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_code: Mapped[str] = mapped_column(ForeignKey("indicator.code"))
    standard_no: Mapped[str] = mapped_column(String(32), default="GB 3838-2002")
    water_body_type: Mapped[str] = mapped_column(String(16), default="river")
    grade: Mapped[int] = mapped_column(Integer)  # 1-5；range 指标用 0
    limit_value: Mapped[float] = mapped_column(Numeric(10, 4))


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(32))
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role: Mapped[str] = mapped_column(String(16), default="user")  # user / admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())

    samples: Mapped[list["Sample"]] = relationship(back_populates="user")


class Site(Base):
    __tablename__ = "site"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    river: Mapped[str] = mapped_column(String(64), default="")
    water_body_type: Mapped[str] = mapped_column(String(16), default="river")
    lng: Mapped[float] = mapped_column(Numeric(10, 6))
    lat: Mapped[float] = mapped_column(Numeric(10, 6))

    samples: Mapped[list["Sample"]] = relationship(back_populates="site")


class Sample(Base):
    __tablename__ = "sample"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"), nullable=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"))
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    method_level: Mapped[int] = mapped_column(Integer, default=1)  # 1机构 2便携 3试剂 4描述
    method_note: Mapped[str] = mapped_column(String(128), default="")
    overall_grade: Mapped[int] = mapped_column(Integer, nullable=True)
    deciding_factors: Mapped[list] = mapped_column(JSON, default=list)
    # pending / approved / rejected；M1 种子数据为 approved
    review_status: Mapped[str] = mapped_column(String(16), default="pending")
    review_note: Mapped[str] = mapped_column(String(256), default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
                                                         nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="samples")
    site: Mapped[Site] = relationship(back_populates="samples")
    measurements: Mapped[list["Measurement"]] = relationship(
        back_populates="sample", cascade="all, delete-orphan")


class Measurement(Base):
    __tablename__ = "measurement"
    __table_args__ = (
        UniqueConstraint("sample_id", "indicator_code", name="uq_measurement"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("sample.id"))
    indicator_code: Mapped[str] = mapped_column(ForeignKey("indicator.code"))
    value: Mapped[float] = mapped_column(Numeric(12, 4))
    grade: Mapped[int] = mapped_column(Integer, nullable=True)

    sample: Mapped[Sample] = relationship(back_populates="measurements")


# ---------------------------------------------------------------------------
# M3：知识库文档 / 分块（向量） / 问答记录
# ---------------------------------------------------------------------------
class KnowledgeDoc(Base):
    __tablename__ = "knowledge_doc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(128), default="")  # 如 GB 3838-2002
    source_url: Mapped[str] = mapped_column(String(512), default="")
    category: Mapped[str] = mapped_column(String(32), default="science")  # standard/science/guide
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="doc", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"
    __table_args__ = (
        UniqueConstraint("doc_id", "chunk_index", name="uq_knowledge_chunk"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("knowledge_doc.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float(precision=8)))

    doc: Mapped[KnowledgeDoc] = relationship(back_populates="chunks")


class AskQuery(Base):
    """问答流水：审计 + 额度统计。"""
    __tablename__ = "ask_query"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"), nullable=True)
    client_id: Mapped[str] = mapped_column(String(64), default="")
    question: Mapped[str] = mapped_column(String(512))
    answer: Mapped[str] = mapped_column(Text, default="")
    citations: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())
