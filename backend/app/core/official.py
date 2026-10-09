# -*- coding: utf-8 -*-
"""M5 官方数据对照引擎（纯函数，DB 无关）。"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from app.core.geo import haversine_km

COMPARE_CAVEAT = (
    "对照结果仅供科普参考：众包点位与官方断面的位置、采样时间、检测方法和仪器可能不同，"
    "数值差异不代表任一方数据有误；官方数据以发布机构原始公告为准。"
)


@dataclass
class CandidateSection:
    code: str
    name: str
    river: str
    lng: float
    lat: float
    level: str
    source_org: str
    readings: list["CandidateReading"] = field(default_factory=list)


@dataclass
class CandidateReading:
    observed_at: datetime
    values: dict
    overall_grade: Optional[int]
    source: str
    source_url: str
    note: str


def _nearest_reading(c: CandidateSection, when: datetime,
                     max_days: int) -> Optional[tuple[CandidateReading, float]]:
    best: Optional[tuple[CandidateReading, float]] = None
    for r in c.readings:
        gap = abs((r.observed_at - when).total_seconds()) / 86400.0
        if gap <= max_days and (best is None or gap < best[1]):
            best = (r, gap)
    return best


def compare(
    lng: float,
    lat: float,
    sampled_at: datetime,
    values: dict,
    sections: list[CandidateSection],
    indicator_meta: dict,
    radius_km: float = 8.0,
    max_days: int = 21,
) -> dict:
    """返回附近官方断面对照结果，按距离升序。"""
    matches = []
    for sec in sections:
        dist = haversine_km(lng, lat, sec.lng, sec.lat)
        if dist > radius_km:
            continue
        picked = _nearest_reading(sec, sampled_at, max_days)
        if picked is None:
            continue
        reading, days_gap = picked

        items = []
        for code, citizen_val in values.items():
            if code not in reading.values:
                continue
            try:
                official_val = float(reading.values[code])
                cv = float(citizen_val)
            except (TypeError, ValueError):
                continue
            diff = cv - official_val
            base = abs(official_val)
            rel = (abs(diff) / base * 100.0) if base > 1e-9 else None
            meta = indicator_meta.get(code, {})
            items.append({
                "code": code,
                "label": meta.get("name", code),
                "unit": meta.get("unit", ""),
                "citizen": cv,
                "official": official_val,
                "diff": round(diff, 3),
                "rel_diff_pct": round(rel, 1) if rel is not None else None,
            })

        matches.append({
            "section": {
                "code": sec.code,
                "name": sec.name,
                "river": sec.river,
                "level": sec.level,
                "source_org": sec.source_org,
                "lng": sec.lng,
                "lat": sec.lat,
            },
            "reading": {
                "observed_at": reading.observed_at.isoformat(),
                "source": reading.source,
                "source_url": reading.source_url,
                "note": reading.note,
                "overall_grade": reading.overall_grade,
            },
            "distance_km": round(dist, 2),
            "days_gap": round(days_gap, 1),
            "shared_indicator_count": len(items),
            "items": items,
        })

    matches.sort(key=lambda m: (m["distance_km"], m["days_gap"]))
    return {
        "matches": matches,
        "radius_km": radius_km,
        "max_days": max_days,
        "caveat": COMPARE_CAVEAT,
    }
