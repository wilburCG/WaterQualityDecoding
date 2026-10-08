"""种子数据：7 指标字典 + GB 3838-2002 河流限值 + 同汾泾案例。

运行：python -m app.seeds.seed
幂等：重复执行不会产生重复数据。
"""
from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.content import INDICATOR_WIKI
from app.core.grading import GB3838_RIVER
from app.core.grading import grade_section
from app.db import Base, SessionLocal, engine
from app.models import Indicator, Measurement, Sample, Site, StandardLimit

INDICATORS = [
    # code, name, unit, direction
    ("ph", "pH", "", "range"),
    ("wt", "水温", "℃", "info"),
    ("do", "溶解氧", "mg/L", "ge"),
    ("codmn", "高锰酸盐指数", "mg/L", "le"),
    ("nh3n", "氨氮", "mg/L", "le"),
    ("tp", "总磷", "mg/L", "le"),
    ("tn", "总氮", "mg/L", "le"),
]

# 点位坐标为浦三路附近近似值（M1 示意，M2 上图前用实测 GPS 校正）
SITES = [
    # name, river, lng, lat
    ("同汾泾-上游", "同汾泾", 121.5180, 31.1430),
    ("同汾泾-中游", "同汾泾", 121.5200, 31.1520),
    ("同汾泾-下游", "同汾泾", 121.5230, 31.1610),
    ("三林塘港（同汾泾上游来水）", "三林塘港", 121.5130, 31.1380),
]

# (site index, sampled_at, {indicator: value}, method_note)
SAMPLES = [
    (0, datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
     {"tp": 0.25, "tn": 1.73, "nh3n": 0.47, "codmn": 4.61},
     "黑灯实验室全自动分析仪（上海市环境监测中心）"),
    (1, datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
     {"tp": 0.16, "tn": 1.21, "nh3n": 0.18, "codmn": 4.56},
     "黑灯实验室全自动分析仪（上海市环境监测中心）"),
    (2, datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
     {"tp": 0.08, "tn": 0.90, "nh3n": 0.28, "codmn": 4.14},
     "黑灯实验室全自动分析仪（上海市环境监测中心）"),
    (3, datetime(2026, 8, 5, 16, 30, tzinfo=timezone.utc),
     {"tp": 0.20, "tn": 1.84, "codmn": 5.84},
     "黑灯实验室全自动分析仪（上海市环境监测中心）"),
    (0, datetime(2026, 8, 5, 16, 30, tzinfo=timezone.utc),
     {"tp": 0.20, "tn": 2.09, "codmn": 6.17},
     "黑灯实验室全自动分析仪（上海市环境监测中心）"),
    (1, datetime(2026, 8, 5, 16, 30, tzinfo=timezone.utc),
     {"tp": 0.13, "tn": 0.78, "codmn": 5.04},
     "黑灯实验室全自动分析仪（上海市环境监测中心）"),
    (2, datetime(2026, 8, 5, 16, 30, tzinfo=timezone.utc),
     {"tp": 0.09, "tn": 0.85, "codmn": 4.63},
     "黑灯实验室全自动分析仪（上海市环境监测中心）"),
]


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 指标
        for code, name, unit, direction in INDICATORS:
            obj = db.get(Indicator, code)
            if obj is None:
                db.add(Indicator(code=code, name=name, unit=unit, direction=direction,
                                 wiki=INDICATOR_WIKI.get(code, {})))
            else:
                obj.name, obj.unit, obj.direction = name, unit, direction
                obj.wiki = INDICATOR_WIKI.get(code, {})
        db.flush()

        # 限值：GB 3838 河流
        db.execute(delete(StandardLimit).where(StandardLimit.standard_no == "GB 3838-2002"))
        for code, spec in GB3838_RIVER.items():
            if spec["direction"] == "range":
                db.add(StandardLimit(indicator_code=code, grade=0,
                                     limit_value=spec["limits"][1]))
            else:
                for grade, value in spec["limits"].items():
                    db.add(StandardLimit(indicator_code=code, grade=grade, limit_value=value))
        db.flush()

        # 点位
        site_ids = {}
        for idx, (name, river, lng, lat) in enumerate(SITES):
            existing = db.scalar(select(Site).where(Site.name == name))
            if existing is None:
                existing = Site(name=name, river=river, lng=lng, lat=lat)
                db.add(existing)
                db.flush()
            site_ids[idx] = existing.id

        # 检测分享：删除旧的案例数据后重建
        old_samples = db.scalars(select(Sample).where(Sample.site_id.in_(site_ids.values()))).all()
        for s in old_samples:
            db.delete(s)
        db.flush()

        for site_idx, sampled_at, values, note in SAMPLES:
            result = grade_section(values)
            sample = Sample(
                site_id=site_ids[site_idx],
                sampled_at=sampled_at,
                method_level=1,
                method_note=note,
                overall_grade=result.overall_grade,
                deciding_factors=result.deciding_factors,
                review_status="approved",
            )
            db.add(sample)
            db.flush()
            for code, value in values.items():
                item = result.items.get(code)
                db.add(Measurement(sample_id=sample.id, indicator_code=code, value=value,
                                   grade=item.grade if item else None))
        db.commit()
        print("seed done:",
              f"{len(INDICATORS)} indicators,",
              f"{len(SITES)} sites,",
              f"{len(SAMPLES)} samples")
    finally:
        db.close()


if __name__ == "__main__":
    run()
