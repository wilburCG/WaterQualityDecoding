"""M1 数据模型：指标字典 / 限值 / 点位 / 检测分享 / 测量值。"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
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
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"))
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    method_level: Mapped[int] = mapped_column(Integer, default=1)  # 1机构 2便携 3试剂 4描述
    method_note: Mapped[str] = mapped_column(String(128), default="")
    overall_grade: Mapped[int] = mapped_column(Integer, nullable=True)
    deciding_factors: Mapped[list] = mapped_column(JSON, default=list)
    review_status: Mapped[str] = mapped_column(String(16), default="approved")  # M2: pending
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())

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
