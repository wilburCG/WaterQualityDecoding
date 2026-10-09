# -*- coding: utf-8 -*-
"""M5 官方监测断面演示种子（幂等）。

⚠️ 所有读数均为**演示数据**，非官方真实发布值；真实对照请以发布机构原始公报为准。
运行：python -m app.seeds.official_seed
"""
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import OfficialReading, OfficialSection

DEMO_NOTE = (
    "演示数据：非官方真实发布值，仅用于功能演示；真实对照请以发布机构公报为准。"
)

SECTIONS = [
    {
        "code": "DEMO-TFJ-01",
        "name": "同汾泾入河口（演示断面）",
        "river": "同汾泾",
        "lng": 121.5260,
        "lat": 31.1680,
        "level": "市控",
        "source_org": "（演示）市生态环境局",
    },
    {
        "code": "DEMO-SLT-01",
        "name": "三林塘港闸内（演示断面）",
        "river": "三林塘港",
        "lng": 121.5105,
        "lat": 31.1345,
        "level": "市控",
        "source_org": "（演示）市生态环境局",
    },
]

READINGS = [
    ("DEMO-TFJ-01", datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
     {"tp": 0.09, "tn": 0.95, "nh3n": 0.30, "codmn": 4.30, "do": 5.4, "ph": 7.2}, 3),
    ("DEMO-TFJ-01", datetime(2026, 8, 6, 10, 0, tzinfo=timezone.utc),
     {"tp": 0.10, "tn": 0.88, "nh3n": 0.26, "codmn": 4.20, "do": 5.1, "ph": 7.3}, 3),
    ("DEMO-SLT-01", datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
     {"tp": 0.22, "tn": 1.90, "nh3n": 1.60, "codmn": 5.90, "do": 3.2, "ph": 7.1}, 5),
    ("DEMO-SLT-01", datetime(2026, 8, 6, 10, 0, tzinfo=timezone.utc),
     {"tp": 0.19, "tn": 1.75, "nh3n": 1.40, "codmn": 5.60, "do": 3.6, "ph": 7.2}, 4),
]


def run() -> None:
    db = SessionLocal()
    try:
        section_map = {}
        for item in SECTIONS:
            s = db.scalar(select(OfficialSection).where(
                OfficialSection.code == item["code"]))
            if s is None:
                s = OfficialSection(**item, is_active=True)
                db.add(s)
                db.flush()
            section_map[item["code"]] = s

        for code, observed_at, values, grade in READINGS:
            s = section_map[code]
            reading = db.scalar(
                select(OfficialReading).where(
                    OfficialReading.section_id == s.id,
                    OfficialReading.observed_at == observed_at))
            if reading is None:
                reading = OfficialReading(section_id=s.id, observed_at=observed_at)
                db.add(reading)
            reading.values = values
            reading.overall_grade = grade
            reading.source = "演示公报（非真实发布）"
            reading.note = DEMO_NOTE
        db.commit()
        print(f"official seed done: {len(SECTIONS)} sections, {len(READINGS)} readings (DEMO)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
